# DriveMath - Live Gas Price Fetching
# Pulls current weekly retail gasoline prices from the EIA API (v2).
#
# EIA publishes weekly state-level retail gasoline prices for nine states
# (CA, CO, FL, MA, MN, NY, OH, TX, WA). Every other state is approximated
# by its PADD region's weekly average — still far fresher than a static
# snapshot. Register for a free API key at:
# https://www.eia.gov/opendata/register.php

import os

import pandas as pd
import requests

EIA_API_URL = "https://api.eia.gov/v2/petroleum/pri/gnd/data/"

# States with their own weekly EIA retail gasoline series
STATE_DUOAREA = {
    "CA": "SCA", "CO": "SCO", "FL": "SFL", "MA": "SMA", "MN": "SMN",
    "NY": "SNY", "OH": "SOH", "TX": "STX", "WA": "SWA",
}

# PADD region duoarea code → states approximated by that region's average.
# States in STATE_DUOAREA also appear here as a fallback in case their
# direct series is missing from a response.
PADD_TO_STATES = {
    "R1X": ["CT", "ME", "MA", "NH", "RI", "VT"],              # New England
    "R1Y": ["DE", "DC", "MD", "NJ", "NY", "PA"],              # Central Atlantic
    "R1Z": ["FL", "GA", "NC", "SC", "VA", "WV"],              # Lower Atlantic
    "R20": ["IL", "IN", "IA", "KS", "KY", "MI", "MN", "MO",   # Midwest
            "NE", "ND", "OH", "OK", "SD", "TN", "WI"],
    "R30": ["AL", "AR", "LA", "MS", "NM", "TX"],              # Gulf Coast
    "R40": ["CO", "ID", "MT", "UT", "WY"],                    # Rocky Mountain
    "R50": ["AK", "AZ", "CA", "HI", "NV", "OR", "WA"],        # West Coast
}


def get_eia_api_key() -> str | None:
    """Read the EIA API key from the environment (or return None)."""
    key = os.environ.get("EIA_API_KEY", "").strip()
    return key or None


def fetch_live_gas_prices(api_key: str, timeout: int = 15) -> pd.DataFrame | None:
    """
    Fetch the latest weekly retail regular-gasoline prices from EIA.

    Returns a DataFrame with columns:
        state            two-letter state code (all 50 + DC)
        price_per_gallon latest weekly price
        period           the week the price is for (YYYY-MM-DD string)
        price_source     'state average' or PADD region name

    Returns None on any failure (network, auth, unexpected shape) so
    callers can fall back to static data.
    """
    duoareas = sorted(set(STATE_DUOAREA.values()) | set(PADD_TO_STATES.keys()))
    params = {
        "api_key": api_key,
        "frequency": "weekly",
        "data[0]": "value",
        "facets[product][]": "EPMR",   # regular gasoline
        "facets[duoarea][]": duoareas,
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 5000,
    }

    try:
        response = requests.get(EIA_API_URL, params=params, timeout=timeout)
        response.raise_for_status()
        rows = response.json()["response"]["data"]
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return None

    # Keep the most recent price per duoarea (rows are sorted newest first)
    latest: dict[str, dict] = {}
    for row in rows:
        try:
            duoarea = row["duoarea"]
            value = float(row["value"])
            period = str(row["period"])
        except (KeyError, TypeError, ValueError):
            continue
        if value <= 0:
            continue
        if duoarea not in latest:
            latest[duoarea] = {"value": value, "period": period}

    if not latest:
        return None

    region_names = {
        "R1X": "New England avg", "R1Y": "Central Atlantic avg",
        "R1Z": "Lower Atlantic avg", "R20": "Midwest avg",
        "R30": "Gulf Coast avg", "R40": "Rocky Mountain avg",
        "R50": "West Coast avg",
    }

    records = []
    # Region averages first, then direct state series override them
    for padd_code, states in PADD_TO_STATES.items():
        if padd_code in latest:
            for state in states:
                records.append({
                    "state": state,
                    "price_per_gallon": latest[padd_code]["value"],
                    "period": latest[padd_code]["period"],
                    "price_source": region_names.get(padd_code, padd_code),
                })
    prices = {r["state"]: r for r in records}
    for state, duoarea in STATE_DUOAREA.items():
        if duoarea in latest:
            prices[state] = {
                "state": state,
                "price_per_gallon": latest[duoarea]["value"],
                "period": latest[duoarea]["period"],
                "price_source": "state average",
            }

    if not prices:
        return None

    return pd.DataFrame(list(prices.values()))
