from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/cleaned/dashboard'
bookings = pd.read_csv(DATA / 'bookings.csv')
weather = pd.read_csv(DATA / 'weather.csv')
scenarios = pd.read_csv(DATA / 'scenarios.csv')

assert not bookings.duplicated(['property_city', 'checkin_month', 'booking_channel']).any()
assert (bookings.completed + bookings.cancellations + bookings.no_shows).eq(bookings.bookings).all()
assert bookings.bookings.sum() == 11460
assert bookings.cancellations.sum() == 2267
assert abs(bookings.realized_revenue.sum() - 264722151.63) < 0.01
assert weather.bookings.sum() == 926
assert not weather.duplicated(['property_city', 'weather_group']).any()
assert (weather.cancellations + weather.no_shows).eq(weather.failed_bookings).all()
assert len(scenarios) == 2 and scenarios.intervention.is_unique
assert abs(scenarios.prevented.max() / bookings.bookings.sum() * 100 - scenarios.platform_percentage_points.max()) < 1e-8
for file in DATA.glob('*.csv'):
    columns = set(pd.read_csv(file, nrows=0).columns)
    assert not columns.intersection({'customer_name', 'customer_id', 'booking_id', 'customer_signup_date'})
print('Aggregate snapshot checks passed: counts, revenue, rates, grain and public-field scope.')
