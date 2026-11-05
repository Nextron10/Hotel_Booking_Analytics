from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
CLEANED = BASE / "data" / "cleaned"
OUTPUT = CLEANED / "validation"
CLEANED.mkdir(parents=True, exist_ok=True)
OUTPUT.mkdir(parents=True, exist_ok=True)
raw = pd.read_excel(
    BASE / "data" / "raw" / "hotel_bookings.xlsx", keep_default_na=False
)
df = raw.copy()
for column in [
    "booking_date",
    "checkin_date",
    "checkout_date",
    "customer_signup_date",
    "review_date",
]:
    df[column] = pd.to_datetime(df[column].replace("", pd.NA), errors="raise")
df["review_rating"] = pd.to_numeric(df["review_rating"].replace("", pd.NA))
assert df.booking_id.is_unique, "Duplicate booking IDs need investigation."


# Keep the original amounts and record each issue before excluding anything.


df["invalid_stay"] = df.checkout_date.le(df.checkin_date)
df["before_signup"] = df.booking_date.lt(df.customer_signup_date)
df["zero_rooms"] = df.num_rooms.le(0)
df["invalid_review"] = df.booking_status.eq("Cancelled") & df.review_rating.notna()
df["expected_amount"] = (df.adr * df.nights * df.num_rooms - df.discount_amount).round(
    2
)
df["amount_mismatch"] = (df.total_amount - df.expected_amount).abs().gt(0.02)
df["booking_eligible"] = ~(df.invalid_stay | df.before_signup | df.zero_rooms)
df["revenue_eligible"] = (
    df.booking_eligible & ~df.amount_mismatch & df.booking_status.eq("Completed")
)
df["lead_days"] = (df.checkin_date - df.booking_date).dt.days
df["checkin_month"] = df.checkin_date.dt.month
df["coupon_code"] = df.coupon_code.replace({"": "NONE"})
flags = [
    "invalid_stay",
    "before_signup",
    "zero_rooms",
    "invalid_review",
    "amount_mismatch",
]
df[flags].sum().rename("affected_rows").to_csv(OUTPUT / "quality_checks.csv")
df.loc[df[flags].any(axis=1), ["booking_id"] + flags].to_csv(
    OUTPUT / "flagged_bookings.csv", index=False
)


# Use original ratings to expose the different scales.


df.groupby("customer_segment").review_rating.agg(
    ["count", "min", "max", "mean"]
).to_csv(OUTPUT / "ratings_by_segment.csv")
luxury = df.loc[
    df.revenue_eligible & df.property_type.eq("Luxury"), "total_amount"
].sum()
(OUTPUT / "quality_results.txt").write_text(
    f"Invalid stays: {int(df.invalid_stay.sum())} invalid stays.\n"
    "Review scales: See ratings_by_segment.csv. Corporate ratings use a different scale.\n"
    f"Luxury revenue: Luxury realized revenue = INR {luxury:,.2f}.\n"
    "Rules: Completed only; exclude invalid stays, bookings before signup, nonpositive rooms and amount mismatches.\n"
    f"Pricing discrepancies: {int(df.amount_mismatch.sum())} amounts disagree with the stated formula by more than INR 0.02.\n"
    "Retain original amounts, flag discrepancies and exclude them from primary revenue until reconciled.\n"
    "This is a conservative cleaning choice; compare footnote-only revenue with the primary result.\n"
    f'Luxury revenue before excluding amount mismatches: INR {df.loc[df.booking_eligible & df.booking_status.eq("Completed") & df.property_type.eq("Luxury"), "total_amount"].sum():,.2f}.\n',
    encoding="utf-8",
)
df.to_csv(CLEANED / "bookings_prepared.csv", index=False)
customer_columns = [
    "customer_id",
    "customer_name",
    "customer_segment",
    "customer_signup_date",
    "customer_home_city",
    "customer_loyalty_tier",
]
property_columns = [
    "property_id",
    "property_name",
    "property_city",
    "property_star_rating",
    "property_type",
    "property_total_rooms",
]
for key, columns, name in [
    ("customer_id", customer_columns, "customers"),
    ("property_id", property_columns, "properties"),
]:
    assert (
        not df.groupby(key)[columns].nunique(dropna=False).gt(1).any().any()
    ), f"Conflicting {name} attributes"
    df[columns].drop_duplicates().to_csv(CLEANED / f"{name}.csv", index=False)
booking_columns = [
    "booking_id",
    "customer_id",
    "property_id",
    "booking_date",
    "checkin_date",
    "checkout_date",
    "room_type",
    "num_rooms",
    "nights",
    "booking_channel",
    "adr",
    "discount_amount",
    "coupon_code",
    "total_amount",
    "payment_method",
    "booking_status",
    "review_rating",
    "review_date",
    "amount_mismatch",
]
bookings = df.loc[df.booking_eligible, booking_columns].copy()
bookings.loc[
    bookings.booking_status.eq("Cancelled"), ["review_rating", "review_date"]
] = None
bookings.to_csv(CLEANED / "bookings.csv", index=False)
print((OUTPUT / "quality_results.txt").read_text())
print(f"Prepared {len(df):,} source rows and {len(bookings):,} eligible bookings.")
