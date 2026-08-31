#!/usr/bin/env python3
"""
DriveMath - Data Download Script

Run this script to download and prepare the real datasets.

Usage:
    python download_data.py
"""

import pandas as pd
import requests
import zipfile
import io
from pathlib import Path
from datetime import date


def create_data_dir():
    """Create data directory if it doesn't exist."""
    Path("data").mkdir(exist_ok=True)


def download_vehicle_data() -> pd.DataFrame | None:
    """
    Download EPA vehicle data from FuelEconomy.gov.
    
    Returns processed DataFrame or None if download fails.
    """
    print("Downloading EPA vehicle data...")
    
    url = "https://fueleconomy.gov/feg/epadata/vehicles.csv.zip"
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Extract CSV from zip
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            with z.open("vehicles.csv") as f:
                raw_data = pd.read_csv(f, low_memory=False)
        
        print(f"  Downloaded {len(raw_data):,} vehicle records")
        
        # Process and filter the data
        vehicles = raw_data[[
            "year", "make", "model", "fuelType", "fuelType1",
            "comb08", "combE", "city08", "highway08"
        ]].copy()
        
        # Debug: Show what fuel types exist in the data
        print(f"  Fuel types found: {raw_data['fuelType'].unique()[:20]}")
        
        # Determine fuel type category
        def categorize_fuel(row):
            fuel = str(row["fuelType"]).strip() if pd.notna(row["fuelType"]) else ""
            fuel1 = str(row["fuelType1"]).strip() if pd.notna(row["fuelType1"]) else ""
            
            # Electric vehicles
            if fuel == "Electricity" or fuel1 == "Electricity":
                return "electric"
            # Gas vehicles (EPA uses "Regular", "Premium", "Midgrade")
            elif fuel in ["Regular", "Premium", "Midgrade", "Gasoline or E85", "Premium or E85"]:
                return "gas"
            elif fuel == "Diesel":
                return "diesel"
            else:
                return "other"
        
        vehicles["fuel_type"] = vehicles.apply(categorize_fuel, axis=1)
        
        # Debug: Show fuel type distribution after categorization
        print(f"  Fuel type distribution: {vehicles['fuel_type'].value_counts().to_dict()}")
        
        # Calculate combined MPG for gas vehicles
        vehicles["combined_mpg"] = vehicles.apply(
            lambda row: row["comb08"] if row["fuel_type"] in ["gas", "diesel"] else None,
            axis=1
        )
        
        # For EVs, combE is ALREADY kWh/100mi (not MPGe) - use it directly
        vehicles["kwh_per_100mi"] = vehicles.apply(
            lambda row: round(row["combE"], 1) 
            if row["fuel_type"] == "electric" and pd.notna(row["combE"]) and row["combE"] > 0 
            else None,
            axis=1
        )
        
        # Filter to recent years and relevant fuel types
        # Include vehicles back to 2010 for older car comparisons
        vehicles = vehicles[
            (vehicles["year"] >= 2010) &
            (vehicles["fuel_type"].isin(["gas", "electric"]))
        ].copy()
        
        # EPA lists multiple entries per model (engine/trim variants).
        # Average efficiency across variants so the app shows a
        # representative number rather than an arbitrary trim.
        vehicles = vehicles[[
            "year", "make", "model", "fuel_type", "combined_mpg", "kwh_per_100mi"
        ]].groupby(
            ["year", "make", "model", "fuel_type"], as_index=False
        ).mean(numeric_only=True)
        vehicles["combined_mpg"] = vehicles["combined_mpg"].round(1)
        vehicles["kwh_per_100mi"] = vehicles["kwh_per_100mi"].round(1)
        vehicles = vehicles.sort_values(
            ["year", "make", "model"], ascending=[False, True, True]
        )
        
        print(f"  Processed to {len(vehicles):,} unique vehicles")
        
        # Save
        vehicles.to_csv("data/vehicles.csv", index=False)
        print("  Saved to data/vehicles.csv")
        
        return vehicles
        
    except Exception as e:
        print(f"  Failed to download EPA data: {e}")
        print("  Using sample data instead.")
        return None


def download_electricity_rates() -> pd.DataFrame | None:
    """
    Download electricity rates by zip code from NREL/Data.gov.
    
    Returns processed DataFrame or None if download fails.
    """
    print("Downloading electricity rates...")
    
    # NREL dataset - each year has a different submission ID
    # Found at: https://data.openei.org/
    submissions = {
        2024: "8563",
        2023: "6225",
        2022: "5828",
        2021: "5650",
        2020: "5650",
    }
    
    for year, submission_id in submissions.items():
        try:
            print(f"  Trying {year} data (submission {submission_id})...")
            base_url = f"https://data.openei.org/files/{submission_id}"
            
            # File naming varies by year
            iou_patterns = [
                f"iou_zipcodes_{year}.csv",
                f"IOU_zipcodes_{year}.csv",
                f"iou_zip_{year}.csv",
                f"IOU rates with zip codes {year}.csv",
                f"IOU rates with zip codes, {year}.csv",
                "iou_zipcodes.csv",
                "IOU rates with zip codes.csv",
            ]
            
            non_iou_patterns = [
                f"non_iou_zipcodes_{year}.csv",
                f"Non_IOU_zipcodes_{year}.csv",
                f"non_iou_zip_{year}.csv",
                f"Non-IOU rates with zip codes {year}.csv",
                f"Non-IOU rates with zip codes, {year}.csv",
                "non_iou_zipcodes.csv",
                "Non-IOU rates with zip codes.csv",
            ]
            
            iou_data = None
            non_iou_data = None
            
            # Try to download IOU data
            for pattern in iou_patterns:
                url = f"{base_url}/{pattern}"
                try:
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        iou_data = pd.read_csv(io.StringIO(response.text))
                        print(f"    Downloaded IOU rates: {len(iou_data):,} records")
                        break
                except (requests.RequestException, pd.errors.ParserError):
                    continue
            
            if iou_data is None:
                print(f"    Could not find IOU data for {year}")
                continue
            
            # Try to download Non-IOU data
            for pattern in non_iou_patterns:
                url = f"{base_url}/{pattern}"
                try:
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        non_iou_data = pd.read_csv(io.StringIO(response.text))
                        print(f"    Downloaded Non-IOU rates: {len(non_iou_data):,} records")
                        break
                except (requests.RequestException, pd.errors.ParserError):
                    continue
            
            # Combine datasets (Non-IOU is optional)
            if non_iou_data is not None:
                rates = pd.concat([iou_data, non_iou_data], ignore_index=True)
            else:
                rates = iou_data
                print("    Note: Only IOU data available")
            
            # Standardize column names (they vary between files/years)
            rates.columns = rates.columns.str.lower().str.strip()
            
            # Find the relevant columns
            zip_col = next((c for c in rates.columns if 'zip' in c), None)
            state_col = next((c for c in rates.columns if 'state' in c), None)
            utility_col = next((c for c in rates.columns if 'utility_name' in c or 'utility name' in c), None)
            rate_col = next((c for c in rates.columns if 'res_rate' in c or 'res rate' in c or 'residential' in c), None)
            
            if not all([zip_col, state_col, rate_col]):
                print(f"    Could not find required columns in {year} data")
                print(f"    Available columns: {list(rates.columns)}")
                continue
            
            # Use utility name if available, otherwise use eiaid
            if utility_col is None:
                utility_col = next((c for c in rates.columns if 'eiaid' in c), None)
            if utility_col is None:
                utility_col = next((c for c in rates.columns if 'name' in c), None)
            
            rename_map = {
                zip_col: "zip",
                state_col: "state",
                rate_col: "residential_rate"
            }
            if utility_col:
                rename_map[utility_col] = "utility_name"
            
            rates = rates.rename(columns=rename_map)
            
            # Select only needed columns
            cols_to_keep = ["zip", "state", "utility_name", "residential_rate"]
            rates = rates[[c for c in cols_to_keep if c in rates.columns]].copy()
            
            # Add placeholder utility name if missing
            if "utility_name" not in rates.columns:
                rates["utility_name"] = "Unknown"
            
            # Clean up
            rates["zip"] = rates["zip"].astype(str).str.zfill(5)
            rates["residential_rate"] = pd.to_numeric(rates["residential_rate"], errors="coerce")
            rates = rates.dropna(subset=["residential_rate"])
            
            # Filter out bad data: rates below $0.01 or above $1.00/kWh
            # are almost certainly errors (typical US range is $0.08-$0.40)
            bad_rates = len(rates[(rates["residential_rate"] < 0.01) | (rates["residential_rate"] > 1.00)])
            if bad_rates > 0:
                print(f"    Filtering out {bad_rates} records with rates outside $0.01-$1.00/kWh (bad data)")
                rates = rates[(rates["residential_rate"] >= 0.01) & (rates["residential_rate"] <= 1.00)]
            
            # Remove duplicates
            rates = rates.drop_duplicates(subset=["zip", "utility_name"])
            
            print(f"  Processed to {len(rates):,} zip code records")
            
            # Save
            rates.to_csv("data/electricity_rates.csv", index=False)
            print(f"  Saved to data/electricity_rates.csv (using {year} data)")
            
            return rates
            
        except Exception as e:
            print(f"    {year} failed: {e}")
            continue
    
    print("  All download attempts failed.")
    print("  Please download manually from:")
    print("  https://catalog.data.gov/dataset/u-s-electric-utility-companies-and-rates-look-up-by-zip-code-2024")
    return None


def download_gas_prices() -> pd.DataFrame:
    """
    Create gas prices by state.

    If an EIA_API_KEY is set (environment variable), fetches current
    weekly retail prices from the EIA API. Otherwise writes a static
    file with approximate prices.
    """
    print("Creating gas price data...")

    from live_prices import fetch_live_gas_prices, get_eia_api_key

    api_key = get_eia_api_key()
    if api_key:
        print("  EIA_API_KEY found — fetching live weekly prices...")
        live = fetch_live_gas_prices(api_key)
        if live is not None:
            live = live.copy()
            live["last_updated"] = str(date.today())
            live.to_csv("data/gas_prices.csv", index=False)
            print(f"  Saved live prices for {len(live)} states to data/gas_prices.csv")
            return live
        print("  Live fetch failed — falling back to static values.")

    # These are approximate values - should be updated periodically
    # For live data, register for an EIA API key at:
    # https://www.eia.gov/opendata/register.php

    gas_prices = pd.DataFrame({
        "state": [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"
        ],
        "price_per_gallon": [
            2.75, 3.45, 3.15, 2.70, 4.50, 3.00, 3.25, 2.95, 3.10, 2.85,
            4.25, 3.20, 3.25, 3.00, 2.90, 2.80, 2.85, 2.70, 3.10, 3.20,
            3.15, 3.05, 2.95, 2.65, 2.75, 3.10, 2.85, 3.50, 3.05, 3.20,
            2.95, 3.35, 2.95, 3.00, 2.95, 2.70, 3.60, 3.30, 3.20, 2.80,
            3.00, 2.75, 2.80, 3.25, 3.10, 2.95, 3.80, 3.00, 2.95, 3.20, 3.25
        ],
        "last_updated": [str(date.today())] * 51
    })
    
    print(f"  Created gas price data for {len(gas_prices)} states")
    print("  NOTE: These are approximate values. For live data, use EIA API.")
    
    # Save
    gas_prices.to_csv("data/gas_prices.csv", index=False)
    print("  Saved to data/gas_prices.csv")
    
    return gas_prices


def download_all_data():
    """Download all datasets."""
    print("\n" + "=" * 50)
    print("DriveMath - Data Download")
    print("=" * 50 + "\n")
    
    create_data_dir()
    
    download_vehicle_data()
    print()
    
    download_electricity_rates()
    print()
    
    download_gas_prices()
    print()
    
    print("=" * 50)
    print("Download complete!")
    print("=" * 50 + "\n")
    
    print("Next steps:")
    print("1. Review the data files in the data/ directory")
    print("2. Run the Streamlit app: streamlit run app.py")
    print("3. For live gas prices, register for an EIA API key at:")
    print("   https://www.eia.gov/opendata/register.php")


if __name__ == "__main__":
    download_all_data()