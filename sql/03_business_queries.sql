-- Highest realized revenue per city; retain ties.
WITH revenue AS (
 SELECT p.property_city, p.property_id, p.property_name, SUM(b.total_amount) AS revenue
 FROM properties p JOIN bookings b ON b.property_id=p.property_id
 WHERE b.booking_status='Completed' AND NOT b.amount_mismatch
 GROUP BY p.property_city,p.property_id,p.property_name
), ranked AS (
 SELECT *, RANK() OVER (PARTITION BY property_city ORDER BY revenue DESC) AS revenue_rank
 FROM revenue
)
SELECT property_city,property_id,property_name,revenue FROM ranked
WHERE revenue_rank=1 ORDER BY property_city;

-- Repeat customers: A single booking has no gap and does not qualify.
WITH previous AS (
 SELECT customer_id,checkin_date,
 LAG(checkin_date) OVER (PARTITION BY customer_id ORDER BY checkin_date,booking_id) AS previous_checkin
 FROM bookings WHERE booking_status='Completed'
), frequent AS (
 SELECT customer_id FROM previous GROUP BY customer_id
 HAVING AVG(checkin_date-previous_checkin)<30
)
SELECT COUNT(*) AS customers_under_30_days FROM frequent;
