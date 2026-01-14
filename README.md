# DriveMath

An interactive Python/Streamlit application that compares the annual fuel costs of gas vehicles versus electric vehicles based on user location and driving habits.

## Features

- **Location-based pricing**: Uses your zip code to look up local electricity rates and state gas prices
- **Multi-utility support**: Handles zip codes served by multiple utilities (e.g., Sacramento area with both SMUD and PG&E) by letting users select their provider
- **Vehicle database**: Includes EPA fuel economy data for thousands of gas and electric vehicles (2010-present)
- **Charging scenarios**: Adjusts EV costs based on home vs. public charging habits
- **Data quality warnings**: Alerts users when electricity rates seem unusually low
- **Interactive visualizations**:
  - Annual cost comparison bar chart
  - Cumulative savings projection over time
  - Sensitivity analysis ("What If" gas/electricity prices change)

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
├── download_data.py       # Script to download real datasets
├── requirements.txt       # Python dependencies
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

## Data Sources

| Data | Source | Coverage |
|------|--------|----------|
| Vehicle MPG/kWh | [EPA FuelEconomy.gov](https://fueleconomy.gov/feg/download.shtml) | 2010-2026, ~48k vehicles |
| Electricity Rates | [NREL/EIA via OpenEI](https://data.openei.org/submissions/8563) | ~30k zip codes |
| Gas Prices | [EIA](https://www.eia.gov/petroleum/gasdiesel/) | 51 states (static, update manually) |

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

## Development

### Code Structure

- `app.py` - Streamlit UI and reactive logic
- `data_loader.py` - Data I/O, sample data fallback, lookup functions
- `calculations.py` - Pure functions for cost math (easy to test)
- `download_data.py` - Data fetching with error handling for EPA/NREL sources

### Running Tests

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

- Gas prices are static state averages (not real-time)
- Electricity rates are utility averages (not detailed TOU structures)
- Some zip codes may have multiple utilities; user must select manually
- Vehicle data limited to what EPA tests (some trims/variants may be missing)

## Potential Enhancements (v2 Ideas)

- [ ] Address-based utility auto-detection (geocode → service territory shapefiles via GeoPandas)
- [ ] Real-time gas prices via EIA API
- [ ] Detailed TOU rate structures for major utilities
- [ ] Maintenance cost comparison
- [ ] Purchase price / breakeven analysis
- [ ] Environmental impact (CO2 savings)
- [ ] Compare multiple EVs at once
- [ ] Custom icons and improved UI styling

## License

MIT License - feel free to use, modify, and share.

## Acknowledgments

- EPA and Department of Energy for open vehicle data
- NREL for electricity rate datasets
- EIA for gas price data