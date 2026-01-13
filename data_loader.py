# DriveMath - Data Loading Functions
# Handles loading and looking up vehicle, electricity, and gas price data

import pandas as pd
from pathlib import Path

# =============================================================================
# Load Vehicle Data
# =============================================================================

def load_vehicle_data(path: str = "data/vehicles.csv") -> pd.DataFrame:
    """
    Load vehicle data from CSV file.
    Falls back to sample data if file doesn't exist.
    """
    if Path(path).exists():
        vehicles = pd.read_csv(path)
        return vehicles
    else:
        print(f"Vehicle data not found at {path}")
        print("Using sample data for development...")
        return create_sample_vehicle_data()


def create_sample_vehicle_data() -> pd.DataFrame:
    """Create sample vehicle data for development/testing."""
    
    # Sample gas vehicles
    gas_vehicles = pd.DataFrame({
        "year": [2024, 2024, 2024, 2024, 2024, 2024,
                 2023, 2023, 2023, 2023, 2023, 2023,
                 2022, 2022, 2022, 2022],
        "make": ["Toyota", "Toyota", "Honda", "Ford", "Honda", "Chevrolet",
                 "Toyota", "Toyota", "Honda", "Ford", "Honda", "Chevrolet",
                 "Toyota", "Honda", "Ford", "Chevrolet"],
        "model": ["Camry", "Corolla", "Civic", "F-150", "Accord", "Silverado",
                  "Camry", "Corolla", "Civic", "F-150", "Accord", "Silverado",
                  "Camry", "Civic", "F-150", "Silverado"],
        "fuel_type": ["gas"] * 16,
        "combined_mpg": [32, 35, 36, 22, 32, 21,
                        31, 34, 35, 21, 31, 20,
                        30, 34, 20, 19],
        "kwh_per_100mi": [None] * 16
    })
    
    # Sample EVs
    ev_vehicles = pd.DataFrame({
        "year": [2024, 2024, 2024, 2024, 2024, 2024,
                 2023, 2023, 2023, 2023, 2023,
                 2022, 2022, 2022],
        "make": ["Tesla", "Tesla", "Chevrolet", "Ford", "Hyundai", "Rivian",
                 "Tesla", "Tesla", "Chevrolet", "Ford", "Hyundai",
                 "Tesla", "Chevrolet", "Ford"],
        "model": ["Model 3", "Model Y", "Bolt EV", "Mustang Mach-E", "Ioniq 6", "R1T",
                  "Model 3", "Model Y", "Bolt EV", "Mustang Mach-E", "Ioniq 5",
                  "Model 3", "Bolt EV", "F-150 Lightning"],
        "fuel_type": ["electric"] * 14,
        "combined_mpg": [None] * 14,
        "kwh_per_100mi": [26, 28, 29, 33, 31, 48,
                         27, 29, 29, 34, 32,
                         28, 30, 51]
    })
    
    return pd.concat([gas_vehicles, ev_vehicles], ignore_index=True)


# =============================================================================
# Load Electricity Rates
# =============================================================================

def load_electricity_rates(path: str = "data/electricity_rates.csv") -> pd.DataFrame:
    """
    Load electricity rates from CSV file.
    Falls back to sample data if file doesn't exist.
    """
    if Path(path).exists():
        rates = pd.read_csv(path, dtype={"zip": str})
        return rates
    else:
        print(f"Electricity rates not found at {path}")
        print("Using sample data for development...")
        return create_sample_electricity_data()


def create_sample_electricity_data() -> pd.DataFrame:
    """
    Create sample electricity data for development/testing.
    Includes Sacramento area with both SMUD and PG&E to demonstrate
    multi-utility zip code handling.
    """
    return pd.DataFrame({
        "zip": [
            # Sacramento area - multiple utilities per zip
            "95822", "95822",  # South Sacramento
            "95814", "95814",  # Downtown Sacramento
            "95825", "95825",  # Arden-Arcade
            "95630", "95630",  # Folsom
            "95828", "95828",  # Florin
            "95823", "95823",  # South Sacramento
            # Single-utility zips
            "95363",  # Patterson - PG&E only
            "90210",  # Beverly Hills - SCE
            "10001",  # NYC - ConEd
            "60601",  # Chicago - ComEd
            "77001",  # Houston - CenterPoint
            "98101",  # Seattle - Seattle City Light
            "33101",  # Miami - FPL
        ],
        "state": [
            "CA", "CA", "CA", "CA", "CA", "CA",
            "CA", "CA", "CA", "CA", "CA", "CA",
            "CA", "CA", "NY", "IL", "TX", "WA", "FL"
        ],
        "utility_name": [
            # Sacramento - alternating SMUD and PG&E
            "SMUD", "PG&E",
            "SMUD", "PG&E",
            "SMUD", "PG&E",
            "SMUD", "PG&E",
            "SMUD", "PG&E",
            "SMUD", "PG&E",
            # Single utilities
            "PG&E", "SCE", "ConEd", "ComEd",
            "CenterPoint", "Seattle City Light", "FPL"
        ],
        "residential_rate": [
            # Sacramento - SMUD ~$0.128, PG&E ~$0.271
            0.128, 0.271,
            0.128, 0.271,
            0.128, 0.271,
            0.131, 0.268,  # Folsom slightly different
            0.128, 0.271,
            0.128, 0.271,
            # Single utilities
            0.265,  # Patterson PG&E
            0.240,  # SCE
            0.220,  # ConEd
            0.140,  # ComEd
            0.120,  # CenterPoint
            0.108,  # Seattle City Light
            0.130,  # FPL
        ]
    })


# =============================================================================
# Load Gas Prices
# =============================================================================

def load_gas_prices(path: str = "data/gas_prices.csv") -> pd.DataFrame:
    """
    Load gas prices from CSV file.
    Falls back to sample data if file doesn't exist.
    """
    if Path(path).exists():
        prices = pd.read_csv(path)
        return prices
    else:
        print(f"Gas prices not found at {path}")
        print("Using sample data for development...")
        return create_sample_gas_data()


def create_sample_gas_data() -> pd.DataFrame:
    """Create sample gas price data by state."""
    return pd.DataFrame({
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
        ]
    })


# =============================================================================
# Lookup Functions
# =============================================================================

def get_utilities_for_zip(zip_code: str, electricity_df: pd.DataFrame) -> pd.DataFrame:
    """
    Get all utilities serving a zip code.
    
    Returns:
        DataFrame with utility_name and residential_rate columns,
        sorted by rate (cheapest first).
    """
    utilities = electricity_df[electricity_df["zip"] == zip_code][
        ["utility_name", "residential_rate"]
    ].drop_duplicates().sort_values("residential_rate")
    
    return utilities


def get_gas_price(zip_code: str, gas_prices_df: pd.DataFrame) -> float:
    """
    Get gas price for a zip code (via state lookup).
    Falls back to national average if state not found.
    """
    state = zip_to_state(zip_code)
    
    if state:
        matches = gas_prices_df[gas_prices_df["state"] == state]
        if not matches.empty:
            return matches["price_per_gallon"].iloc[0]
    
    # Fallback to national average
    return 3.20


def zip_to_state(zip_code: str) -> str | None:
    """
    Simplified zip code to state mapping.
    In production, use a proper zip code database.
    """
    if not zip_code or len(zip_code) < 3:
        return None
    
    first_three = zip_code[:3]
    
    # California (900-961)
    if "900" <= first_three <= "961":
        return "CA"
    
    # New York (100-149)
    if "100" <= first_three <= "149":
        return "NY"
    
    # Texas (750-799)
    if "750" <= first_three <= "799":
        return "TX"
    
    # Illinois (600-629)
    if "600" <= first_three <= "629":
        return "IL"
    
    # Florida (320-349)
    if "320" <= first_three <= "349":
        return "FL"
    
    # Washington (980-994)
    if "980" <= first_three <= "994":
        return "WA"
    
    # Georgia (300-319)
    if "300" <= first_three <= "319":
        return "GA"
    
    # Pennsylvania (150-196)
    if "150" <= first_three <= "196":
        return "PA"
    
    # Ohio (430-459)
    if "430" <= first_three <= "459":
        return "OH"
    
    # Michigan (480-499)
    if "480" <= first_three <= "499":
        return "MI"
    
    return None


def get_tou_multiplier(charging_scenario: str) -> float:
    """
    Get time-of-use multiplier based on charging scenario.
    
    Args:
        charging_scenario: One of 'home', 'mixed', 'public'
        
    Returns:
        Multiplier to apply to electricity rate
    """
    multipliers = {
        "home": 0.80,    # Overnight charging typically 20% cheaper
        "mixed": 0.95,   # Slight discount from some home charging
        "public": 1.20,  # Public charging often more expensive
    }
    return multipliers.get(charging_scenario, 1.0)
