-- One row per city, check-in month and booking channel. No customer-level fields.
CREATE OR REPLACE VIEW dashboard_bookings AS
SELECT p.property_city,b.booking_channel,
 EXTRACT(MONTH FROM b.checkin_date)::INTEGER AS checkin_month,
 COUNT(*) AS bookings,
 COUNT(*) FILTER(WHERE b.booking_status='Completed') AS completed,
 COUNT(*) FILTER(WHERE b.booking_status='Cancelled') AS cancellations,
 COUNT(*) FILTER(WHERE b.booking_status='No-Show') AS no_shows,
 COALESCE(SUM(b.total_amount) FILTER(WHERE b.booking_status='Completed' AND NOT b.amount_mismatch),0) AS realized_revenue
FROM bookings b JOIN properties p USING(property_id)
GROUP BY p.property_city,b.booking_channel,EXTRACT(MONTH FROM b.checkin_date);
