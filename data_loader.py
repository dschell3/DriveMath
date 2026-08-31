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
    
    # Sample gas vehicles - expanded to include older years
    gas_vehicles = pd.DataFrame({
        "year": [
            # 2024
            2024, 2024, 2024, 2024, 2024, 2024,
            # 2023
            2023, 2023, 2023, 2023, 2023, 2023,
            # 2022
            2022, 2022, 2022, 2022,
            # 2020
            2020, 2020, 2020, 2020,
            # 2018
            2018, 2018, 2018, 2018,
            # 2015
            2015, 2015, 2015, 2015,
            # 2013
            2013, 2013, 2013, 2013,
        ],
        "make": [
            # 2024
            "Toyota", "Toyota", "Honda", "Ford", "Honda", "Chevrolet",
            # 2023
            "Toyota", "Toyota", "Honda", "Ford", "Honda", "Chevrolet",
            # 2022
            "Toyota", "Honda", "Ford", "Chevrolet",
            # 2020
            "Toyota", "Honda", "Ford", "Chevrolet",
            # 2018
            "Toyota", "Honda", "Ford", "Chevrolet",
            # 2015
            "Toyota", "Honda", "Ford", "Chevrolet",
            # 2013
            "Toyota", "Honda", "Ford", "Chevrolet",
        ],
        "model": [
            # 2024
            "Camry", "Corolla", "Civic", "F-150", "Accord", "Silverado",
            # 2023
            "Camry", "Corolla", "Civic", "F-150", "Accord", "Silverado",
            # 2022
            "Camry", "Civic", "F-150", "Silverado",
            # 2020
            "Camry", "Civic", "F-150", "Silverado",
            # 2018
            "Camry", "Civic", "F-150", "Silverado",
            # 2015
            "Camry", "Civic", "F-150", "Silverado",
            # 2013
            "Camry", "Civic", "F-150", "Silverado",
        ],
        "fuel_type": ["gas"] * 32,
        "combined_mpg": [
            # 2024
            32, 35, 36, 22, 32, 21,
            # 2023
            31, 34, 35, 21, 31, 20,
            # 2022
            30, 34, 20, 19,
            # 2020
            29, 33, 20, 18,
            # 2018
            29, 32, 19, 18,
            # 2015
            28, 31, 18, 17,
            # 2013
            28, 30, 17, 16,
        ],
        "kwh_per_100mi": [None] * 32
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

def validate_zip(zip_code: str) -> str | None:
    """
    Sanitize and validate a user-entered zip code.

    Returns the cleaned 5-digit zip string, or None if invalid.
    """
    if not zip_code:
        return None
    cleaned = zip_code.strip()
    if len(cleaned) == 5 and cleaned.isdigit():
        return cleaned
    return None


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


NATIONAL_AVG_GAS_PRICE = 3.20


def get_state_for_zip(zip_code: str, electricity_df: pd.DataFrame | None = None) -> str | None:
    """
    Resolve a zip code to a state.

    Prefers the state recorded in the electricity rates dataset (exact,
    covers every zip in the data), then falls back to the 3-digit
    prefix mapping.
    """
    if electricity_df is not None and "state" in electricity_df.columns:
        matches = electricity_df.loc[electricity_df["zip"] == zip_code, "state"].dropna()
        if not matches.empty:
            return matches.iloc[0]
    return zip_to_state(zip_code)


def get_gas_price(
    zip_code: str,
    gas_prices_df: pd.DataFrame,
    electricity_df: pd.DataFrame | None = None,
) -> tuple[float, str | None]:
    """
    Get gas price for a zip code (via state lookup).
    Falls back to national average if state not found.

    Returns:
        (price_per_gallon, state) — state is None when the national
        average fallback was used.
    """
    state = get_state_for_zip(zip_code, electricity_df)

    if state:
        matches = gas_prices_df[gas_prices_df["state"] == state]
        if not matches.empty:
            return matches["price_per_gallon"].iloc[0], state

    return NATIONAL_AVG_GAS_PRICE, None


# USPS 3-digit zip prefix ranges → state. Ranges are inclusive.
# A handful of prefixes cross state lines in reality; this resolves each
# prefix to the state that holds the overwhelming majority of it.
_ZIP_PREFIX_RANGES: list[tuple[int, int, str]] = [
    (5, 5, "NY"), (6, 9, "PR"),
    (10, 27, "MA"), (28, 29, "RI"), (30, 38, "NH"), (39, 49, "ME"),
    (50, 54, "VT"), (55, 55, "MA"), (56, 59, "VT"),
    (60, 69, "CT"), (70, 89, "NJ"),
    (100, 149, "NY"), (150, 196, "PA"), (197, 199, "DE"),
    (200, 200, "DC"), (201, 201, "VA"), (202, 205, "DC"),
    (206, 219, "MD"), (220, 246, "VA"), (247, 268, "WV"),
    (270, 289, "NC"), (290, 299, "SC"),
    (300, 319, "GA"), (320, 339, "FL"), (341, 342, "FL"),
    (344, 344, "FL"), (346, 347, "FL"), (349, 349, "FL"),
    (350, 369, "AL"), (370, 385, "TN"), (386, 397, "MS"),
    (398, 399, "GA"),
    (400, 427, "KY"), (430, 459, "OH"), (460, 479, "IN"),
    (480, 499, "MI"),
    (500, 528, "IA"), (530, 549, "WI"), (550, 567, "MN"),
    (570, 577, "SD"), (580, 588, "ND"), (590, 599, "MT"),
    (600, 629, "IL"), (630, 658, "MO"), (660, 679, "KS"),
    (680, 693, "NE"),
    (700, 714, "LA"), (716, 729, "AR"), (730, 732, "OK"),
    (733, 733, "TX"), (734, 749, "OK"), (750, 799, "TX"),
    (800, 816, "CO"), (820, 831, "WY"), (832, 838, "ID"),
    (840, 847, "UT"), (850, 865, "AZ"), (870, 884, "NM"),
    (885, 885, "TX"), (889, 898, "NV"),
    (900, 961, "CA"), (967, 968, "HI"), (970, 979, "OR"),
    (980, 994, "WA"), (995, 999, "AK"),
]


def zip_to_state(zip_code: str) -> str | None:
    """
    Map a zip code to its state using USPS 3-digit prefix ranges.
    Covers all 50 states, DC, and Puerto Rico.
    """
    if not zip_code or len(zip_code) < 3 or not zip_code[:3].isdigit():
        return None

    prefix = int(zip_code[:3])

    for start, end, state in _ZIP_PREFIX_RANGES:
        if start <= prefix <= end:
            return state

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