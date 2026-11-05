-- Normalized hotel booking model.
CREATE TABLE IF NOT EXISTS customers (
 customer_id INTEGER PRIMARY KEY,
 customer_name VARCHAR(150) NOT NULL,
 customer_segment VARCHAR(20) NOT NULL,
 customer_signup_date DATE NOT NULL,
 customer_home_city VARCHAR(60) NOT NULL,
 customer_loyalty_tier VARCHAR(20) NOT NULL
);
CREATE TABLE IF NOT EXISTS properties (
 property_id INTEGER PRIMARY KEY,
 property_name VARCHAR(150) NOT NULL,
 property_city VARCHAR(60) NOT NULL,
 property_star_rating INTEGER NOT NULL,
 property_type VARCHAR(30) NOT NULL,
 property_total_rooms INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS bookings (
 booking_id INTEGER PRIMARY KEY,
 customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
 property_id INTEGER NOT NULL REFERENCES properties(property_id),
 booking_date DATE NOT NULL,
 checkin_date DATE NOT NULL,
 checkout_date DATE NOT NULL,
 room_type VARCHAR(30) NOT NULL,
 num_rooms INTEGER NOT NULL CHECK (num_rooms > 0),
 nights INTEGER NOT NULL,
 booking_channel VARCHAR(30) NOT NULL,
 adr NUMERIC(14,2) NOT NULL,
 discount_amount NUMERIC(14,2) NOT NULL,
 coupon_code VARCHAR(30),
 total_amount NUMERIC(14,2) NOT NULL,
 payment_method VARCHAR(30) NOT NULL,
 booking_status VARCHAR(20) NOT NULL,
 review_rating NUMERIC(4,1),
 review_date DATE,
 amount_mismatch BOOLEAN NOT NULL,
 CHECK (checkout_date > checkin_date)
);
-- Supports customer lookup and grouping for the consecutive-booking query.
CREATE INDEX IF NOT EXISTS bookings_customer_idx ON bookings(customer_id);


