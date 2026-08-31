# DriveMath - Calculation Functions
# Core logic for computing fuel costs and comparisons

from typing import TypedDict


class ComparisonResult(TypedDict):
    """Type definition for comparison results."""
    gas_vehicle_name: str
    ev_vehicle_name: str
    gas_mpg: float
    ev_kwh_per_100: float
    annual_miles: int
    gas_price: float
    electricity_rate: float
    tou_multiplier: float
    gas_annual_cost: float
    ev_annual_cost: float
    gas_cost_per_mile: float
    ev_cost_per_mile: float
    annual_savings: float
    monthly_savings: float


def calculate_comparison(
    gas_mpg: float,
    ev_kwh_per_100: float,
    annual_miles: int,
    gas_price: float,
    electricity_rate: float,
    tou_multiplier: float = 1.0,
    gas_vehicle_name: str = "Gas Vehicle",
    ev_vehicle_name: str = "Electric Vehicle"
) -> ComparisonResult:
    """
    Calculate full comparison between gas and electric vehicles.
    
    Args:
        gas_mpg: Miles per gallon for gas vehicle
        ev_kwh_per_100: kWh per 100 miles for EV
        annual_miles: Annual miles driven
        gas_price: Price per gallon of gas
        electricity_rate: Price per kWh
        tou_multiplier: Time-of-use adjustment (1.0 = no adjustment)
        gas_vehicle_name: Display name for gas vehicle
        ev_vehicle_name: Display name for EV
        
    Returns:
        Dictionary containing all comparison metrics
    """
    if annual_miles <= 0:
        raise ValueError(f"annual_miles must be positive, got {annual_miles}")

    # Calculate annual costs
    gas_annual_cost = calculate_gas_annual_cost(annual_miles, gas_mpg, gas_price)
    ev_annual_cost = calculate_ev_annual_cost(
        annual_miles, ev_kwh_per_100, electricity_rate, tou_multiplier
    )
    
    # Calculate per-mile costs
    gas_cost_per_mile = gas_annual_cost / annual_miles
    ev_cost_per_mile = ev_annual_cost / annual_miles
    
    # Calculate savings
    annual_savings = gas_annual_cost - ev_annual_cost
    monthly_savings = annual_savings / 12
    
    return {
        # Vehicle info
        "gas_vehicle_name": gas_vehicle_name,
        "ev_vehicle_name": ev_vehicle_name,
        
        # Input values (for sensitivity analysis)
        "gas_mpg": gas_mpg,
        "ev_kwh_per_100": ev_kwh_per_100,
        "annual_miles": annual_miles,
        "gas_price": gas_price,
        "electricity_rate": electricity_rate,
        "tou_multiplier": tou_multiplier,
        
        # Calculated costs
        "gas_annual_cost": gas_annual_cost,
        "ev_annual_cost": ev_annual_cost,
        "gas_cost_per_mile": gas_cost_per_mile,
        "ev_cost_per_mile": ev_cost_per_mile,
        
        # Savings
        "annual_savings": annual_savings,
        "monthly_savings": monthly_savings,
    }


def calculate_gas_annual_cost(
    annual_miles: int,
    mpg: float,
    gas_price: float
) -> float:
    """
    Calculate annual fuel cost for a gas vehicle.
    
    Args:
        annual_miles: Miles driven per year
        mpg: Vehicle fuel efficiency (miles per gallon)
        gas_price: Price per gallon
        
    Returns:
        Annual fuel cost in dollars
    """
    if mpg <= 0:
        raise ValueError(f"mpg must be positive, got {mpg}")
    gallons_used = annual_miles / mpg
    return gallons_used * gas_price


def calculate_ev_annual_cost(
    annual_miles: int,
    kwh_per_100mi: float,
    electricity_rate: float,
    tou_multiplier: float = 1.0
) -> float:
    """
    Calculate annual energy cost for an electric vehicle.
    
    Args:
        annual_miles: Miles driven per year
        kwh_per_100mi: Energy consumption (kWh per 100 miles)
        electricity_rate: Price per kWh
        tou_multiplier: Time-of-use adjustment factor
        
    Returns:
        Annual energy cost in dollars
    """
    if kwh_per_100mi <= 0:
        raise ValueError(f"kwh_per_100mi must be positive, got {kwh_per_100mi}")
    kwh_used = (annual_miles / 100) * kwh_per_100mi
    effective_rate = electricity_rate * tou_multiplier
    return kwh_used * effective_rate


def calculate_cumulative_costs(
    annual_cost: float,
    years: int,
    annual_increase: float = 0.0
) -> list[float]:
    """
    Calculate cumulative costs over multiple years.
    
    Args:
        annual_cost: Annual cost
        years: Number of years to project
        annual_increase: Annual percentage increase in costs (default 0)
        
    Returns:
        List of cumulative costs for each year
    """
    yearly_costs = []
    current_cost = annual_cost
    
    for _ in range(years):
        yearly_costs.append(current_cost)
        current_cost *= (1 + annual_increase)
    
    # Return cumulative sum
    cumulative = []
    total = 0
    for cost in yearly_costs:
        total += cost
        cumulative.append(total)
    
    return cumulative


def calculate_breakeven_years(
    ev_premium: float,
    annual_savings: float
) -> float:
    """
    Calculate years to break even on EV premium.
    
    Args:
        ev_premium: Additional upfront cost of EV over gas vehicle
        annual_savings: Annual fuel savings
        
    Returns:
        Years to break even (infinity if savings <= 0)
    """
    if annual_savings <= 0:
        return float('inf')
    
    return ev_premium / annual_savings


# EPA: burning one gallon of gasoline emits 8.887 kg of CO2
CO2_KG_PER_GALLON = 8.887

# EPA eGRID US national average grid carbon intensity (~0.39 kg CO2/kWh).
# Actual intensity varies widely by region and time of day.
CO2_KG_PER_KWH_GRID = 0.39


class EmissionsResult(TypedDict):
    """Type definition for emissions comparison results."""
    gas_annual_co2_kg: float
    ev_annual_co2_kg: float
    annual_co2_savings_kg: float
    co2_reduction_pct: float


def calculate_emissions_comparison(
    gas_mpg: float,
    ev_kwh_per_100: float,
    annual_miles: int,
    grid_co2_kg_per_kwh: float = CO2_KG_PER_KWH_GRID,
) -> EmissionsResult:
    """
    Estimate annual tailpipe/grid CO2 emissions for both vehicles.

    Covers gasoline combustion vs. grid electricity generation only
    (not upstream fuel production or vehicle manufacturing).

    Args:
        gas_mpg: Miles per gallon for gas vehicle
        ev_kwh_per_100: kWh per 100 miles for EV
        annual_miles: Annual miles driven
        grid_co2_kg_per_kwh: Grid carbon intensity (kg CO2 per kWh)

    Returns:
        Dictionary with annual CO2 (kg) for each vehicle and the savings
    """
    gas_annual_co2 = (annual_miles / gas_mpg) * CO2_KG_PER_GALLON
    ev_annual_co2 = (annual_miles / 100) * ev_kwh_per_100 * grid_co2_kg_per_kwh
    savings = gas_annual_co2 - ev_annual_co2
    reduction_pct = (savings / gas_annual_co2 * 100) if gas_annual_co2 > 0 else 0.0

    return {
        "gas_annual_co2_kg": gas_annual_co2,
        "ev_annual_co2_kg": ev_annual_co2,
        "annual_co2_savings_kg": savings,
        "co2_reduction_pct": reduction_pct,
    }


def mpg_to_miles_per_kwh(mpg: float) -> float:
    """
    Convert MPG to miles per kWh equivalent (for comparison).
    
    Note: 1 gallon of gas ≈ 33.7 kWh of energy
    """
    KWH_PER_GALLON = 33.7
    return mpg / KWH_PER_GALLON


def kwh_to_mpge(kwh_per_100mi: float) -> float:
    """
    Convert kWh/100mi to MPGe (miles per gallon equivalent).
    """
    KWH_PER_GALLON = 33.7
    return (100 / kwh_per_100mi) * KWH_PER_GALLON
