-- Run from the repository root with psql; replaces these three tables' rows.
BEGIN;
TRUNCATE bookings, customers, properties;
\copy customers FROM 'data/cleaned/customers.csv' WITH (FORMAT csv, HEADER true)
\copy properties FROM 'data/cleaned/properties.csv' WITH (FORMAT csv, HEADER true)
\copy bookings FROM 'data/cleaned/bookings.csv' WITH (FORMAT csv, HEADER true)
COMMIT;
