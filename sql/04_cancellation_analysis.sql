CREATE OR REPLACE VIEW cancellation_base AS
SELECT b.*,p.property_city,EXTRACT(MONTH FROM b.checkin_date)::INTEGER AS checkin_month,
 b.checkin_date-b.booking_date AS lead_days,
 (b.booking_status='Cancelled')::INTEGER AS cancelled
FROM bookings b JOIN properties p ON p.property_id=b.property_id;

CREATE OR REPLACE VIEW cancellation_slices AS
SELECT property_city,checkin_month,COUNT(*) AS bookings,SUM(cancelled) AS cancellations,
 AVG(cancelled::NUMERIC) AS cancellation_rate
FROM cancellation_base GROUP BY property_city,checkin_month;

-- Export for the city/month matrix in Power BI.
SELECT * FROM cancellation_slices ORDER BY property_city,checkin_month;
-- Rate and count answer different prioritization questions.
SELECT * FROM cancellation_slices ORDER BY cancellation_rate DESC,bookings DESC,property_city,checkin_month LIMIT 3;
SELECT * FROM cancellation_slices ORDER BY cancellations DESC,property_city,checkin_month LIMIT 3;

CREATE OR REPLACE VIEW worst_slice AS
SELECT * FROM cancellation_slices
ORDER BY cancellation_rate DESC,bookings DESC,property_city,checkin_month LIMIT 1;


-- Test lead-time mix, then compare the same city in other months and other cities in the same month.


WITH groups AS (
 SELECT c.*,CASE WHEN c.property_city=w.property_city AND c.checkin_month=w.checkin_month
 THEN 'Worst slice' ELSE 'Rest of platform' END AS comparison_group
 FROM cancellation_base c CROSS JOIN worst_slice w
)
SELECT comparison_group,COUNT(*) AS bookings,AVG(lead_days) AS mean_lead_days,
 PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY lead_days) AS median_lead_days,
 AVG((lead_days>30)::INTEGER::NUMERIC) AS long_lead_share,
 AVG(cancelled::NUMERIC) AS cancellation_rate
FROM groups GROUP BY comparison_group;


-- Same city in other months and other cities in the same month.


SELECT s.* FROM cancellation_slices s CROSS JOIN worst_slice w
WHERE s.property_city=w.property_city OR s.checkin_month=w.checkin_month
ORDER BY s.property_city,s.checkin_month;


-- Fixed booking volume; these are separate scenarios with possible overlap.


CREATE OR REPLACE VIEW cancellation_scenarios AS
WITH platform AS (
 SELECT COUNT(*) AS n,AVG(cancelled::NUMERIC) AS rate FROM cancellation_base
), lead_groups AS (
 SELECT COUNT(*) FILTER(WHERE lead_days>30) AS n_long,
 AVG(cancelled::NUMERIC) FILTER(WHERE lead_days>30) AS long_rate,
 AVG(cancelled::NUMERIC) FILTER(WHERE lead_days<=30) AS short_rate
 FROM cancellation_base
), scenarios AS (
 SELECT 'Worst slice to platform average' AS scenario,
 w.bookings*(w.cancellation_rate-p.rate) AS prevented,p.n
 FROM worst_slice w CROSS JOIN platform p
 UNION ALL
 SELECT 'Long lead to short lead rate',l.n_long*(l.long_rate-l.short_rate),p.n
 FROM lead_groups l CROSS JOIN platform p
)
SELECT scenario,prevented,100.0*prevented/n AS platform_percentage_points FROM scenarios;

SELECT * FROM cancellation_scenarios;


-- Compare marginal rate dispersion, weighted by each group's booking count.


WITH rates AS (
 SELECT 'City' AS dimension,COUNT(*) AS n,AVG(cancelled::NUMERIC) AS rate FROM cancellation_base GROUP BY property_city
 UNION ALL
 SELECT 'Month',COUNT(*),AVG(cancelled::NUMERIC) FROM cancellation_base GROUP BY checkin_month
)
SELECT dimension,100*(MAX(rate)-MIN(rate)) AS rate_range_pp,
 100*SQRT(SUM(n*rate*rate)/SUM(n)-POWER(SUM(n*rate)/SUM(n),2)) AS weighted_rate_sd_pp
FROM rates GROUP BY dimension;
