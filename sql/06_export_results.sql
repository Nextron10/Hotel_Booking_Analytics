-- Run from the repository root after the schema, data load and analysis SQL.
\copy (SELECT * FROM dashboard_bookings ORDER BY property_city,checkin_month,booking_channel) TO 'data/cleaned/dashboard/bookings.csv' WITH (FORMAT csv, HEADER true)
\copy (SELECT * FROM cancellation_slices ORDER BY property_city,checkin_month) TO 'data/cleaned/validation/cancellation_landscape.csv' WITH (FORMAT csv, HEADER true)
\copy (SELECT * FROM cancellation_slices WHERE property_city IN ('Goa','Manali','Kochi') ORDER BY property_city,checkin_month) TO 'data/cleaned/dashboard/seasonality.csv' WITH (FORMAT csv, HEADER true)
\copy (SELECT scenario,CASE WHEN scenario LIKE 'Worst%' THEN 'Worst city-month' ELSE 'Long lead bookings' END AS intervention,prevented,platform_percentage_points,CASE WHEN scenario LIKE 'Worst%' THEN (SELECT bookings FROM worst_slice) ELSE (SELECT COUNT(*) FROM cancellation_base WHERE lead_days>30) END AS targeted_bookings FROM cancellation_scenarios) TO 'data/cleaned/dashboard/scenarios.csv' WITH (FORMAT csv, HEADER true)

