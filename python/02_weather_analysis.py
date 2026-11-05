from pathlib import Path
from datetime import datetime, timezone
import sys
import json

import pandas as pd
import requests

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / "data/cleaned/weather"
CACHE = BASE / "data/raw/weather"
URL = "https://archive-api.open-meteo.com/v1/archive"
CITIES = {"Goa": (15.4909, 73.8278), "Manali": (32.2396, 77.1887)}

cached = "--cached" in sys.argv
OUTPUT.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)
bookings = pd.read_csv(
    BASE / "data/cleaned/bookings_prepared.csv", keep_default_na=False
)
bookings["checkin_date"] = pd.to_datetime(bookings.checkin_date)
sample = bookings.loc[
    bookings.booking_eligible
    & bookings.property_city.isin(CITIES)
    & bookings.checkin_date.dt.year.eq(2024)
].copy()
weather_rows = []
calls = []
for city, (latitude, longitude) in CITIES.items():
    dates = sample.loc[sample.property_city.eq(city), "checkin_date"]
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": dates.min().strftime("%Y-%m-%d"),
        "end_date": dates.max().strftime("%Y-%m-%d"),
        "daily": "precipitation_sum,temperature_2m_max",
        "timezone": "Asia/Kolkata",
    }
    cache = CACHE / f"weather_{city.lower()}.json"
    try:
        if cached:
            payload = json.loads(cache.read_text(encoding="utf-8"))
        else:
            response = requests.get(URL, params=params, timeout=60)
            response.raise_for_status()
            payload = response.json()
        daily = payload["daily"]
        if not isinstance(daily, dict):
            raise ValueError("Daily weather is missing or invalid.")
        city_weather = pd.DataFrame(
            {
                "property_city": city,
                "checkin_date": pd.to_datetime(daily["time"]),
                "precipitation_mm": daily["precipitation_sum"],
                "maximum_temperature_c": daily["temperature_2m_max"],
            }
        )
        if not cached:
            cache.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        weather_rows.append(city_weather)
        calls.append(
            {
                "city": city,
                "parameters": params,
                "status": "cached" if cached else "live success",
            }
        )
    except (
        requests.RequestException,
        ValueError,
        KeyError,
        TypeError,
        OSError,
    ) as error:
        calls.append(
            {
                "city": city,
                "parameters": params,
                "status": "failed",
                "error": str(error),
            }
        )
        print(f"{city}: weather unavailable; {error}")
(CACHE / ("cached_run.json" if cached else "api_run.json")).write_text(
    json.dumps(
        {
            "endpoint": URL,
            "run_utc": datetime.now(timezone.utc).isoformat(),
            "calls": calls,
            "source": "Open-Meteo Historical Weather API",
        },
        indent=2,
    ),
    encoding="utf-8",
)
if not weather_rows:
    print(
        "No weather available. Check the connection and rerun; cached responses can be used with --cached."
    )
    raise SystemExit(1)
weather = pd.concat(weather_rows, ignore_index=True)
assert not weather.duplicated(["property_city", "checkin_date"]).any()
merged = sample.merge(
    weather, on=["property_city", "checkin_date"], how="left", validate="many_to_one"
)
assert len(merged) == len(sample)
usable = merged.dropna(subset=["precipitation_mm", "maximum_temperature_c"]).copy()
usable["cancelled"] = usable.booking_status.eq("Cancelled").astype(int)
usable["no_show"] = usable.booking_status.eq("No-Show").astype(int)
usable["failed_booking"] = usable.booking_status.isin(["Cancelled", "No-Show"]).astype(
    int
)


# Thresholds are fixed before comparing outcomes. Precipitation can include snow.


usable["heavy_precipitation"] = usable.precipitation_mm.ge(20)
usable["extreme_temperature"] = usable.maximum_temperature_c.le(
    0
) | usable.maximum_temperature_c.ge(35)
summaries = []
for condition in ["heavy_precipitation", "extreme_temperature"]:
    summary = (
        usable.groupby(["property_city", condition])
        .agg(
            bookings=("booking_id", "size"),
            checkin_dates=("checkin_date", "nunique"),
            cancellations=("cancelled", "sum"),
            no_shows=("no_show", "sum"),
            failed_bookings=("failed_booking", "sum"),
        )
        .reset_index()
        .rename(columns={condition: "condition_present"})
    )
    summary["condition"] = condition
    summary["cancellation_rate"] = summary.cancellations / summary.bookings
    summary["no_show_rate"] = summary.no_shows / summary.bookings
    summary["failed_booking_rate"] = summary.failed_bookings / summary.bookings
    summaries.append(summary)
result = pd.concat(summaries, ignore_index=True)
weather.to_csv(OUTPUT / "daily_weather.csv", index=False)
merged.to_csv(OUTPUT / "bookings_with_weather.csv", index=False)
result.to_csv(OUTPUT / "weather_comparison.csv", index=False)
sentences = [
    f"Weather data matched {len(usable)} of {len(sample)} valid Goa and Manali bookings with check-in dates in 2024; {len(sample)-len(usable)} bookings lacked complete weather."
]
for city in CITIES:
    rows = result.loc[
        result.property_city.eq(city) & result.condition.eq("heavy_precipitation")
    ].set_index("condition_present")
    if True in rows.index and False in rows.index:
        heavy, other = rows.loc[True], rows.loc[False]
        gap = (heavy.failed_booking_rate - other.failed_booking_rate) * 100
        sentences.append(
            f"In {city}, {int(heavy.failed_bookings)} of {int(heavy.bookings)} bookings ({heavy.failed_booking_rate:.1%}) on days with at least 20 mm precipitation were cancelled or no-shows, compared with {int(other.failed_bookings)} of {int(other.bookings)} ({other.failed_booking_rate:.1%}) on other days, a difference of {gap:+.2f} percentage points."
        )
sentences.append(
    "These figures show a relationship, not proof that weather caused cancellations: cancellation times are unavailable, weather is estimated for the city, precipitation can include snow, and several bookings share the same weather date."
)
insight = " ".join(sentences)
(OUTPUT / "insight.txt").write_text(insight + "\n", encoding="utf-8")
print(insight)
# The public dashboard uses only city-level weather groups.
rain = result.loc[result.condition.eq("heavy_precipitation")].copy()
rain["weather_group"] = rain.condition_present.map(
    {True: "Heavy precipitation", False: "Other days"}
)
(BASE / "data/cleaned/dashboard").mkdir(parents=True, exist_ok=True)
rain.to_csv(BASE / "data/cleaned/dashboard/weather.csv", index=False)
if len(usable) != len(sample) or any(c["status"] == "failed" for c in calls):
    raise SystemExit(1)
