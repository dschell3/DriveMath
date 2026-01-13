# DriveMath

An interactive Python/Streamlit application that compares the annual fuel costs of gas vehicles versus electric vehicles based on user location and driving habits.

## Features

- **Location-based pricing**: Uses your zip code to look up local electricity rates and state gas prices
- **Multi-utility support**: Handles zip codes served by multiple utilities (e.g., Sacramento area with both SMUD and PG&E) by letting users select their provider
- **Vehicle database**: Includes EPA fuel economy data for thousands of gas and electric vehicles
- **Charging scenarios**: Adjusts EV costs based on home vs. public charging habits
- **Interactive visualizations**:
  - Annual cost comparison bar chart
  - Cumulative savings projection over time
  - Sensitivity analysis (what if gas/electricity prices change?)

## Project Structure

```
drivemath/
├── app.py                 # Main Streamlit application
├── data_loader.py         # Functions to load and look up data
├── calculations.py        # Core cost calculation logic
├── download_data.py       # Script to download real datasets
├── requirements.txt       # Python dependencies
├── data/                  # Data files (created by download script)
│   ├── vehicles.csv
│   ├── electricity_rates.csv
│   └── gas_prices.csv
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

### 3. Run with Sample Data

The app includes built-in sample data, so you can run it immediately:

```bash
streamlit run app.py
```

This will open the app in your browser at `http://localhost:8501`.

### 4. Download Real Data (Optional)

To use real EPA vehicle data and electricity rates:

```bash
python download_data.py
```

Then restart the Streamlit app.

## Data Sources

| Data | Source | Update Frequency |
|------|--------|------------------|
| Vehicle MPG/kWh | [EPA FuelEconomy.gov](https://fueleconomy.gov/feg/download.shtml) | Annual |
| Electricity Rates | [NREL/EIA via Data.gov](https://catalog.data.gov/dataset/u-s-electric-utility-companies-and-rates-look-up-by-zip-code-2024) | Annual |
| Gas Prices | [EIA](https://www.eia.gov/petroleum/gasdiesel/) | Weekly (manual update) |

## How Calculations Work

### Gas Vehicle Annual Cost
```
annual_cost = (annual_miles / mpg) × price_per_gallon
```

### Electric Vehicle Annual Cost
```
annual_cost = (annual_miles / 100) × kwh_per_100mi × electricity_rate × tou_multiplier
```

### Time-of-Use Multipliers
| Scenario | Multiplier | Explanation |
|----------|------------|-------------|
| Home charging (overnight) | 0.80 | 20% discount for off-peak |
| Mixed charging | 0.95 | Slight discount |
| Public charging | 1.20 | 20% premium |

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest

# Run tests
pytest
```

### Code Structure

- `app.py` - Streamlit UI and reactive logic
- `data_loader.py` - Data I/O and lookup functions
- `calculations.py` - Pure functions for cost math (easy to test)
- `download_data.py` - One-time data fetching script

## Deployment

### Streamlit Cloud (Free)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Deploy!

### Other Options

- **Heroku**: Add a `Procfile` with `web: streamlit run app.py --server.port=$PORT`
- **Docker**: Create a Dockerfile based on `python:3.11-slim`
- **AWS/GCP/Azure**: Deploy as a container or on a VM

## Potential Enhancements (v2 Ideas)

- [ ] Address-based utility auto-detection (geocode address → check against service territory shapefiles using GeoPandas)
- [ ] Real-time gas prices via EIA API
- [ ] Time-of-use rate details for major utilities
- [ ] Maintenance cost comparison
- [ ] Purchase price / breakeven analysis
- [ ] Environmental impact (CO2 savings)
- [ ] Compare multiple EVs at once
- [ ] Mobile-optimized layout

## License

MIT License - feel free to use, modify, and share.

## Acknowledgments

- EPA and Department of Energy for open vehicle data
- NREL for electricity rate datasets
- EIA for gas price data
