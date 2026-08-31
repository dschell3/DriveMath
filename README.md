# DriveMath

An interactive Python/Streamlit application that compares the annual fuel costs of gas vehicles versus electric vehicles based on user location and driving habits.

## Features

- **Location-based pricing**: Uses your zip code to look up local electricity rates and state gas prices (all 50 states + DC)
- **Live gas prices** (optional): With a free [EIA API key](https://www.eia.gov/opendata/register.php), the app fetches current weekly retail gasoline prices instead of static averages
- **Data transparency**: A sidebar shows exactly where each dataset comes from and how fresh it is
- **Multi-utility support**: Handles zip codes served by multiple utilities (e.g., Sacramento area with both SMUD and PG&E) by letting users select their provider
- **Custom price overrides**: Enter your actual electricity rate and pump price when you know them — real numbers beat dataset averages
- **Vehicle database**: Includes EPA fuel economy data for thousands of gas and electric vehicles (2010-present), averaged across trims
- **Charging scenarios**: Adjusts EV costs based on home vs. public charging habits
- **Purchase price / breakeven analysis**: Optionally include vehicle prices to see how many years of fuel savings pay back the EV premium
- **Environmental impact**: Estimated annual CO₂ emissions comparison (gasoline combustion vs. US-average grid electricity)
- **Data quality warnings**: Alerts users when electricity rates seem unusually low
- **Input validation**: Zip codes are sanitized and validated before lookup
- **Interactive visualizations**:
  - Annual cost comparison bar chart
  - Cumulative savings projection over time, with optional fuel-price inflation
  - Sensitivity analysis ("What If" gas/electricity prices change)
  - CO₂ emissions comparison chart

## Changelog: Improvement Pass 2 (2026-08) — Real-time data & UI/UX

For transparency, the second automated improvement pass implemented:

**Real-time data**
- **Live EIA gas prices** (previously a v2 idea): new `live_prices.py`
  module fetches current weekly retail regular-gasoline prices from the
  EIA API. EIA publishes direct weekly series for 9 states (CA, CO, FL,
  MA, MN, NY, OH, TX, WA); every other state uses its PADD region's
  weekly average — still refreshed weekly, and labeled as a regional
  average in the UI. Cached for 6 hours; any failure falls back to the
  static file automatically. See **Live Gas Prices** below for setup.
- `download_data.py` also uses the EIA key when present, so the saved
  `gas_prices.csv` contains real current prices instead of hardcoded ones.
- **Data provenance sidebar**: shows the source and freshness of every
  dataset (live EIA week, file download dates, or "built-in sample data")
  so users know exactly what their numbers are based on.
- The gas price caption states whether the price is a live state series,
  a live regional average (and which week), or a static average.

**UI/UX**
- Streamlit theme (`.streamlit/config.toml`) matching the app's green
  EV accent, with usage-stats reporting disabled.
- Vehicle pickers are now bordered cards; the EV card shows MPGe
  alongside kWh/100mi so gas-minded shoppers can compare intuitively.
- Sidebar with an about blurb, data status, and EIA key instructions.
- Footer states which gas price data the results were computed from.

**Testing**
- 13 new tests for the live price module (mocked network): coverage of
  all 51 states, state-over-region precedence, latest-week selection,
  bad-row handling, and every failure mode falling back to None.
- All three app data paths (static, live, live-fetch-failed) smoke
  tested headlessly.

## Changelog: Improvement Pass 1 (2026-08)

For transparency, this automated improvement pass implemented the following.
Everything below was added or changed in this pass; features not listed
predate it.

**Accuracy**
- Zip→state mapping expanded from 10 states to all 50 states + DC + PR using
  USPS 3-digit prefix ranges (`data_loader.py`). Previously, gas prices for
  40 states silently fell back to a $3.20 national average.
- Gas price lookup now prefers the state recorded in the electricity-rates
  dataset for the entered zip (exact), falling back to prefix mapping.
- EPA download now **averages efficiency across trims** of the same
  year/make/model instead of keeping an arbitrary first trim
  (`download_data.py`); the app also averages if a data file still contains
  duplicates.
- Electricity rate download filters rates above $1.00/kWh as bad data
  (in addition to the existing <$0.01 filter).
- Core calculation functions now reject non-positive MPG, kWh/100mi, and
  annual miles instead of silently producing nonsense.

**Features**
- **Custom price overrides**: users can enter their actual electricity rate
  and gas price ("Know your actual prices?" expander).
- **Purchase price / breakeven analysis** (previously a v2 idea): optional
  vehicle prices in the Savings Over Time tab, with breakeven-year estimate.
- **Fuel price inflation**: the cumulative projection supports separate
  annual gas/electricity price escalation (0-10%/yr).
- **Environmental impact tab** (previously a v2 idea): annual CO₂ comparison
  using EPA's 8.887 kg CO₂/gallon and ~0.39 kg CO₂/kWh US-average grid
  intensity, with clear caveats about regional grids and upstream emissions.
- The gas price used (and which state average it came from) is now shown in
  the UI instead of being applied invisibly.

**Usability & correctness**
- Zip code input is validated (5 digits, whitespace stripped) with a clear
  error message instead of failing lookups silently.
- Removed dead code (a duplicate utility lookup before the zip input existed).
- Guarded against NaN efficiency values reaching the results section.
- Migrated deprecated `use_container_width` to the current Streamlit
  `width="stretch"` API (Streamlit minimum bumped to 1.46).

**Testing & robustness**
- Added a real test suite (`tests/`, 91 tests) covering the calculation
  functions (including the README's worked example), zip mapping for all
  50 states, lookups, validation, and sample-data integrity — the README
  previously advertised `pytest` with no tests in the repo.
- Download script: replaced bare `except:` clauses with specific exception
  types so real bugs aren't swallowed.

## Screenshots

The app flows through four sections:
1. **Your Location** — Enter zip code, select utility if multiple serve your area
2. **Select Vehicles** — Choose your current gas vehicle and an EV to compare
3. **Driving Habits** — Set annual miles and charging scenario
4. **Results** — View cost breakdown, savings, and interactive charts

## Project Structure

```
drivemath/
├── app.py                 # Main Streamlit application
├── data_loader.py         # Functions to load and look up data
├── calculations.py        # Core cost calculation logic
├── live_prices.py         # Live EIA gas price fetching (optional API key)
├── download_data.py       # Script to download real datasets
├── .streamlit/
│   └── config.toml        # App theme
├── requirements.txt       # Python dependencies
├── tests/                 # Pytest suite for calculations and data lookups
│   ├── test_calculations.py
│   ├── test_data_loader.py
│   └── test_live_prices.py
├── data/                  # Data files (created by download script)
│   ├── vehicles.csv       # EPA vehicle database
│   ├── electricity_rates.csv  # NREL electricity rates by zip
│   └── gas_prices.csv     # State-level gas prices
└── README.md
```

## Quick Start

### 1. Create Virtual Environment (Recommended)

```bash
cd drivemath
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Download Real Data

Download EPA vehicle data and NREL electricity rates:

```bash
python download_data.py
```

This downloads:
- ~47,000 gas vehicles and ~1,300 EVs from EPA (2010-present)
- ~30,000 zip codes with electricity rates from NREL
- State-level gas prices

### 4. Run the App

```bash
streamlit run app.py
```

This will open the app in your browser at `http://localhost:8501`.

> **Note**: The app includes built-in sample data for development, but for full vehicle/zip coverage you should run the download script first.

### 5. (Optional) Live Gas Prices

Register for a free EIA API key at [eia.gov/opendata](https://www.eia.gov/opendata/register.php), then either:

```bash
# Option A: environment variable
export EIA_API_KEY=your_key_here
streamlit run app.py
```

```toml
# Option B: .streamlit/secrets.toml (never commit this file)
EIA_API_KEY = "your_key_here"
```

With a key set, the app fetches current weekly retail gasoline prices
(refreshed every 6 hours) instead of static averages. Nine states have
their own weekly EIA series; the rest use their PADD region's weekly
average, and the UI labels which one you're seeing. If the fetch fails
for any reason the app quietly falls back to the static data.

## Data Sources

| Data | Source | Coverage |
|------|--------|----------|
| Vehicle MPG/kWh | [EPA FuelEconomy.gov](https://fueleconomy.gov/feg/download.shtml) | 2010-2026, ~48k vehicles |
| Electricity Rates | [NREL/EIA via OpenEI](https://data.openei.org/submissions/8563) | ~30k zip codes |
| Gas Prices | [EIA](https://www.eia.gov/petroleum/gasdiesel/) | 50 states + DC (live weekly with an EIA API key; static fallback) |

### Data Quality Notes

- **Electricity rates < $0.01/kWh** are filtered out during download (bad data)
- **Electricity rates < $0.06/kWh** trigger a warning in the UI (suspiciously low)
- Typical US residential rates range from $0.08-$0.40/kWh
- Gas prices are static averages; for live data, register for an [EIA API key](https://www.eia.gov/opendata/register.php)

## How Calculations Work

### Gas Vehicle Annual Cost
```
annual_cost = (annual_miles / mpg) × price_per_gallon
```

### Electric Vehicle Annual Cost
```
annual_cost = (annual_miles / 100) × kwh_per_100mi × electricity_rate × tou_multiplier
```

### Time-of-Use (TOU) Multipliers
| Scenario | Multiplier | Explanation |
|----------|------------|-------------|
| Home charging (overnight) | 0.80 | 20% discount for off-peak |
| Mixed charging | 0.95 | Slight discount |
| Public charging | 1.20 | 20% premium |

### Example Calculation

For a 30 MPG car vs 31 kWh/100mi EV, driving 12,000 miles/year:
- **Gas**: 12,000 / 30 × $4.50 = **$1,800/year**
- **EV (home)**: 12,000 / 100 × 31 × $0.18 × 0.80 = **$535/year**
- **Savings**: $1,265/year

### Breakeven Analysis (optional)

```
breakeven_years = (ev_price − gas_vehicle_price) / annual_fuel_savings
```

### CO₂ Emissions Estimate

```
gas_co2  = (annual_miles / mpg) × 8.887 kg/gallon        (EPA)
ev_co2   = (annual_miles / 100) × kwh_per_100mi × 0.39 kg/kWh  (US grid avg)
```

These cover combustion vs. grid generation only — not upstream fuel
production or vehicle manufacturing — and your regional grid may differ
significantly from the national average.

## Development

### Code Structure

- `app.py` - Streamlit UI and reactive logic
- `data_loader.py` - Data I/O, sample data fallback, lookup functions
- `calculations.py` - Pure functions for cost math (easy to test)
- `download_data.py` - Data fetching with error handling for EPA/NREL sources

### Running Tests

The `tests/` directory covers the calculation logic, zip→state mapping,
data lookups, input validation, and sample-data integrity:

```bash
pip install pytest
pytest
```

### Updating Data

Re-run the download script periodically to get updated vehicle data:

```bash
python download_data.py
```

The script automatically tries multiple years of NREL data (2024, 2023, 2022...) in case the current year isn't available yet.

## Deployment

### Streamlit Cloud (Free)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Deploy!

> **Note**: Include your `data/` folder in the repo, or modify `download_data.py` to run on startup.

### Other Options

- **Heroku**: Add a `Procfile` with `web: streamlit run app.py --server.port=$PORT`
- **Docker**: Create a Dockerfile based on `python:3.11-slim`
- **AWS/GCP/Azure**: Deploy as a container or on a VM

## Known Limitations

- Without an EIA API key, gas prices are static state averages — mitigated by the live EIA integration and the custom price override
- Live EIA prices are state-level for 9 states, PADD-region averages for the rest (labeled in the UI)
- Electricity rates are utility averages (not detailed TOU structures) — mitigated by the custom rate override
- Some zip codes may have multiple utilities; user must select manually
- Vehicle efficiency is averaged across trims of the same year/make/model (individual trims are not selectable)
- CO₂ estimates use the US-average grid intensity, not your regional grid
- Zip→state mapping uses 3-digit prefix ranges; a handful of prefixes that cross state lines resolve to the majority state

## Potential Enhancements (v2 Ideas)

- [x] Purchase price / breakeven analysis
- [x] Environmental impact (CO2 savings)
- [x] Custom electricity/gas price overrides
- [x] Real-time gas prices via EIA API
- [ ] Address-based utility auto-detection (geocode → service territory shapefiles via GeoPandas)
- [ ] Detailed TOU rate structures for major utilities
- [ ] Regional grid carbon intensity (EPA eGRID subregions) for CO₂ estimates
- [ ] Maintenance cost comparison
- [ ] Compare multiple EVs at once
- [ ] Trim-level vehicle selection
- [ ] Custom icons and improved UI styling

## License

MIT License - feel free to use, modify, and share.

## Acknowledgments

- EPA and Department of Energy for open vehicle data
- NREL for electricity rate datasets
- EIA for gas price data