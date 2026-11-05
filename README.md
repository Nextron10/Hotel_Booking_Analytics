# Hotel Booking Analytics

An analysis of hotel revenue, cancellations and weather-related booking outcomes using Python, PostgreSQL and Power BI. The project starts with 12,000 booking records and uses 11,460 eligible bookings after data-quality checks.

The highest cancellation rate is concentrated in a small group: Goa in July has 20 cancellations from 38 bookings. A broader scenario targeting bookings made more than 30 days ahead has a larger estimated impact, but neither scenario supports a five-percentage-point reduction across the platform.

![Executive dashboard showing booking totals, revenue and cancellation rates](dashboards/previews/executive_overview.png)

## Explore the project

- [Dashboard PDF](docs/Dashboard.pdf): view all three report pages without Power BI.
- [Power BI report](dashboards/Hotel_Booking_Analytics.pbix): explore the interactive report in Power BI Desktop.
- [Case study](docs/Case_Study.docx): read the findings, calculations, recommendations and limitations.
- [Project requirements](docs/Project_Requirements.docx): review the analytical questions and technical scope.

## Key results

| Metric | Result |
|---|---:|
| Eligible bookings | 11,460 |
| Completed bookings | 8,848 |
| Cancelled bookings | 2,267 |
| No-shows | 345 |
| Cancellation rate | 19.78% |
| Realized revenue | INR 264,722,151.63 |
| Bookings matched to weather | 926 |

Bringing the cancellation rate of bookings made more than 30 days ahead down to the shorter-lead group's rate would prevent an estimated 154.72 cancellations, or 1.35 percentage points across the platform, at fixed booking volume. This is a scenario calculation; a deposit policy has not been tested.

On days with at least 20 mm of precipitation, the combined cancellation and no-show rate is higher by 17.47 percentage points in Goa and 7.41 points in Manali. Weather is matched to the scheduled check-in date, so these comparisons do not establish why a booking was cancelled.

## Repository structure

```text
Hotel_Booking_Analytics/
  README.md
  requirements.txt
  .vscode/extensions.json
  python/                     Data preparation, weather analysis and validation
  sql/                        Schema, loading, business queries and exports
  data/
    raw/                      Source workbook and API cache; excluded from Git
    cleaned/
      dashboard/              Four aggregate CSVs used by Power BI
  dashboards/
    Hotel_Booking_Analytics.pbix
    previews/executive_overview.png
  docs/
    Case_Study.docx
    Dashboard.pdf
    Project_Requirements.docx
```

The four dashboard inputs have different purposes:

| CSV | Contents |
|---|---|
| `bookings.csv` | 480 groups by city, check-in month and booking channel; supplies revenue charts, booking metrics and the cancellation matrix |
| `scenarios.csv` | Two estimates of cancellations prevented and their platform-wide impact |
| `seasonality.csv` | 36 monthly groups for Goa, Manali and Kochi |
| `weather.csv` | Four groups comparing heavy-precipitation days with other days in Goa and Manali |

## Methods and definitions

Python preserves the source workbook and flags date, room, review and pricing issues. The date and room checks exclude 540 unique bookings; some error counts overlap. Review fields on Cancelled bookings are cleared without dropping those bookings. The 35 pricing discrepancies are retained for reconciliation, and affected Completed amounts are excluded from primary revenue.

PostgreSQL separates customers, properties and bookings into three related tables. It enforces keys and stay/room constraints, calculates the cancellation scenarios, and uses RANK and LAG for the property-revenue and repeat-customer analyses. Power BI imports aggregate CSVs; it does not query PostgreSQL live.

Realized revenue includes only eligible Completed bookings with consistent amounts. Cancellation rate is Cancelled divided by all eligible bookings, including No-Show bookings in the denominator. The weather comparison uses a separate outcome combining Cancelled and No-Show. Rates are calculated from summed counts rather than averaged subgroup percentages. Month refers to the scheduled check-in month.

The literal loyalty value `None` is preserved, blank coupons and `NONE` are treated alike, and ratings are reported separately for customer segments with different scales. Properties are identified by `property_id` because names can repeat.

## Run locally

To view the results, open the dashboard PDF or PBIX. To refresh the PBIX after cloning, open **Home > Transform data > Manage Parameters**, set `DataFolder` to the absolute path of `data/cleaned/dashboard`, then select **Close & Apply**, **Refresh**, and **Save**. PostgreSQL is not required to view or refresh the published aggregate snapshot.

To rerun the full analysis, use Python 3.12+, PostgreSQL and the original workbook. The source workbook, detailed booking records and API cache are excluded from this repository. Place the workbook at `data/raw/hotel_bookings.xlsx` and run these commands from the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python python/01_prepare_data.py
```

Create a database named `hotel_booking_analytics`. With PostgreSQL's `psql` command on PATH, run the SQL files in order:

```powershell
psql -h localhost -U postgres -d hotel_booking_analytics -v ON_ERROR_STOP=1 -f sql/01_create_tables.sql -f sql/02_load_data.sql -f sql/03_business_queries.sql -f sql/04_cancellation_analysis.sql -f sql/05_dashboard_views.sql -f sql/06_export_results.sql -o data/cleaned/validation/sql_results.txt
python python/02_weather_analysis.py
python python/03_validate_outputs.py
```

Enter your own database password when prompted. The load script replaces the rows in the three project tables within one transaction. Run it through `psql`, which supports the client-side `\copy` commands. After regenerating the CSVs, refresh and save the Power BI report.

The validator can also run against the four published CSVs without the workbook, database or API. It checks expected snapshot totals and selected consistency rules; it is not a general validator for unrelated datasets.

### Weather tool

The weather script adds daily precipitation and maximum temperature to eligible Goa and Manali bookings. It makes one request per city for the required date range and joins the results on city and local check-in date, with a check that the join does not multiply booking rows.

```powershell
python python/02_weather_analysis.py
# After a successful live run, reuse the saved responses:
python python/02_weather_analysis.py --cached
```

Responses and request logs are saved locally in `data/raw/weather`; detailed results are in `data/cleaned/weather`. A failed request or incomplete weather coverage returns a nonzero exit status. City-level weather estimates, missing cancellation times and shared weather dates limit interpretation.

## Data source and scope

The analysis uses a historical practice dataset. This repository includes only aggregate dashboard inputs, with no customer names, customer IDs or booking IDs. Running the complete pipeline requires the original workbook. Local environments, credentials, detailed outputs, the private interview guide and archived versions are excluded through `.gitignore`.

Weather data comes from the [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api). The comparisons describe this dataset and should be tested with further data before a policy is adopted.

Prepared by Dhaerya Nauni
