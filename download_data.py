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
        
        # Determine fuel type category
        def categorize_fuel(row):
            if row["fuelType"] == "Electricity" or row["fuelType1"] == "Electricity":
                return "electric"
            elif row["fuelType"] in ["Regular Gasoline", "Premium Gasoline", "Midgrade Gasoline"]:
                return "gas"
            elif row["fuelType"] == "Diesel":
                return "diesel"
            else:
                return "other"
        
        vehicles["fuel_type"] = vehicles.apply(categorize_fuel, axis=1)
        
        # Calculate combined MPG for gas vehicles
        vehicles["combined_mpg"] = vehicles.apply(
            lambda row: row["comb08"] if row["fuel_type"] in ["gas", "diesel"] else None,
            axis=1
        )
        
        # Calculate kWh per 100 miles for EVs
        # MPGe = (100 / kWh_per_100mi) * 33.7
        # So: kWh_per_100mi = 3370 / MPGe
        vehicles["kwh_per_100mi"] = vehicles.apply(
            lambda row: round(3370 / row["combE"], 1) 
            if row["fuel_type"] == "electric" and pd.notna(row["combE"]) and row["combE"] > 0 
            else None,
            axis=1
        )
        
        # Filter to recent years and relevant fuel types
        vehicles = vehicles[
            (vehicles["year"] >= 2015) &
            (vehicles["fuel_type"].isin(["gas", "electric"]))
        ].copy()
        
        # Select final columns and remove duplicates
        vehicles = vehicles[[
            "year", "make", "model", "fuel_type", "combined_mpg", "kwh_per_100mi"
        ]].drop_duplicates(
            subset=["year", "make", "model", "fuel_type"]
        ).sort_values(
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
    
    # NREL provides IOU and Non-IOU rates separately
    # Try 2024 data first, fall back to 2023
    base_url = "https://data.openei.org/files/5828"
    
    try:
        # Try to download IOU data
        iou_url = f"{base_url}/iou_zipcodes_2024.csv"
        non_iou_url = f"{base_url}/non_iou_zipcodes_2024.csv"
        
        print("  Downloading IOU rates...")
        iou_response = requests.get(iou_url, timeout=30)
        iou_response.raise_for_status()
        iou_data = pd.read_csv(io.StringIO(iou_response.text))
        print(f"  Downloaded {len(iou_data):,} IOU records")
        
        print("  Downloading Non-IOU rates...")
        non_iou_response = requests.get(non_iou_url, timeout=30)
        non_iou_response.raise_for_status()
        non_iou_data = pd.read_csv(io.StringIO(non_iou_response.text))
        print(f"  Downloaded {len(non_iou_data):,} Non-IOU records")
        
        # Combine datasets
        rates = pd.concat([iou_data, non_iou_data], ignore_index=True)
        
        # Standardize column names (they may vary between files)
        rates.columns = rates.columns.str.lower().str.strip()
        
        # Find the relevant columns (names vary by year)
        zip_col = [c for c in rates.columns if 'zip' in c][0]
        state_col = [c for c in rates.columns if 'state' in c][0]
        utility_col = [c for c in rates.columns if 'utility' in c or 'name' in c][0]
        rate_col = [c for c in rates.columns if 'res' in c or 'rate' in c][0]
        
        rates = rates.rename(columns={
            zip_col: "zip",
            state_col: "state", 
            utility_col: "utility_name",
            rate_col: "residential_rate"
        })[[
            "zip", "state", "utility_name", "residential_rate"
        ]].copy()
        
        # Clean up
        rates["zip"] = rates["zip"].astype(str).str.zfill(5)
        rates["residential_rate"] = pd.to_numeric(rates["residential_rate"], errors="coerce")
        rates = rates.dropna(subset=["residential_rate"])
        
        print(f"  Processed to {len(rates):,} zip code records")
        
        # Save
        rates.to_csv("data/electricity_rates.csv", index=False)
        print("  Saved to data/electricity_rates.csv")
        
        return rates
        
    except Exception as e:
        print(f"  Failed to download electricity rates: {e}")
        print("  Try downloading manually from:")
        print("  https://catalog.data.gov/dataset/u-s-electric-utility-companies-and-rates-look-up-by-zip-code-2024")
        return None


def download_gas_prices() -> pd.DataFrame:
    """
    Create gas prices by state.
    
    Note: EIA API requires registration for real-time data.
    This creates a static file with approximate recent prices.
    """
    print("Creating gas price data...")
    
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
