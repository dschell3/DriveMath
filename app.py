# DriveMath
# EV vs Gas Cost Comparison Tool
# Built with Python + Streamlit

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data_loader import (
    load_vehicle_data,
    load_electricity_rates,
    load_gas_prices,
    get_utilities_for_zip,
    get_gas_price,
    get_tou_multiplier,
)
from calculations import calculate_comparison

# =============================================================================
# Page Config
# =============================================================================

st.set_page_config(
    page_title="DriveMath",
    page_icon="🚗",
    layout="centered",  # Changed from "wide" to "centered"
)

# =============================================================================
# Load Data (cached)
# =============================================================================

@st.cache_data
def load_all_data():
    vehicles = load_vehicle_data()
    electricity = load_electricity_rates()
    gas = load_gas_prices()
    return vehicles, electricity, gas

vehicles_df, electricity_df, gas_prices_df = load_all_data()

# =============================================================================
# Header
# =============================================================================

st.title("🚗 DriveMath")
st.markdown(
    "Compare the annual fuel costs of your current gas vehicle against an "
    "electric vehicle, based on your location and driving habits."
)

st.divider()

# =============================================================================
# Section 1: Your Location
# =============================================================================

st.header("📍 Your Location")

# Handle multi-utility zip codes (need to check before rendering columns)
utilities = get_utilities_for_zip(zip_code if 'zip_code' in dir() else "95822", electricity_df)

col1, col2 = st.columns(2)

with col1:
    zip_code = st.text_input(
        "Zip Code",
        value="95822",
        max_chars=5,
        placeholder="e.g., 90210"
    )

# Re-check utilities with actual zip_code value
utilities = get_utilities_for_zip(zip_code, electricity_df)

with col2:
    if len(utilities) == 0:
        electricity_rate = 0.15
        utility_name = "National Average"
        st.text_input(
            "Utility ⚠️",
            value="National Average — $0.150/kWh",
            disabled=True,
            help="Zip code not found. Using national average rate."
        )
    elif len(utilities) == 1:
        electricity_rate = utilities.iloc[0]["residential_rate"]
        utility_name = utilities.iloc[0]["utility_name"]
        st.text_input(
            "Utility",
            value=f"{utility_name} — ${electricity_rate:.3f}/kWh",
            disabled=True
        )
    else:
        utility_options = {
            f"{row['utility_name']} — ${row['residential_rate']:.3f}/kWh": row['utility_name']
            for _, row in utilities.iterrows()
        }
        selected_display = st.selectbox(
            "Utility ℹ️",
            options=list(utility_options.keys()),
            help="Multiple utilities serve this zip code. Select yours."
        )
        utility_name = utility_options[selected_display]
        electricity_rate = utilities[utilities["utility_name"] == utility_name]["residential_rate"].iloc[0]

# Warning for suspiciously low rates
if electricity_rate < 0.06:
    st.warning(
        f"⚠️ The electricity rate (${electricity_rate:.3f}/kWh) seems unusually low. "
        "This may be a data error. Typical US residential rates range from $0.08-$0.40/kWh. "
        "Consider verifying with your utility bill."
    )

st.divider()

# =============================================================================
# Section 2: Vehicle Selection
# =============================================================================

st.header("🚘 Select Vehicles to Compare")

col_gas, col_ev = st.columns(2)

# --- Gas Vehicle ---
with col_gas:
    st.subheader("Your Current Vehicle")
    
    gas_vehicles = vehicles_df[vehicles_df["fuel_type"] == "gas"]
    gas_years = sorted([int(y) for y in gas_vehicles["year"].unique()], reverse=True)
    
    gas_year = st.selectbox(
        "Year",
        options=[None] + gas_years,
        key="gas_year",
        format_func=lambda x: "Select year..." if x is None else str(x)
    )
    
    if gas_year:
        available_gas_makes = sorted(
            gas_vehicles[gas_vehicles["year"] == gas_year]["make"].unique().tolist()
        )
    else:
        available_gas_makes = []
    
    gas_make = st.selectbox(
        "Make",
        options=[None] + available_gas_makes,
        key="gas_make",
        format_func=lambda x: "Select make..." if x is None else x
    )
    
    if gas_year and gas_make:
        available_gas_models = sorted(
            gas_vehicles[
                (gas_vehicles["year"] == gas_year) & 
                (gas_vehicles["make"] == gas_make)
            ]["model"].unique().tolist()
        )
    else:
        available_gas_models = []
    
    gas_model = st.selectbox(
        "Model",
        options=[None] + available_gas_models,
        key="gas_model",
        format_func=lambda x: "Select model..." if x is None else x
    )
    
    if gas_year and gas_make and gas_model:
        gas_mpg = gas_vehicles[
            (gas_vehicles["year"] == gas_year) &
            (gas_vehicles["make"] == gas_make) &
            (gas_vehicles["model"] == gas_model)
        ]["combined_mpg"].iloc[0]
        st.metric("Combined MPG", f"{gas_mpg}")
    else:
        gas_mpg = None

# --- EV ---
with col_ev:
    st.subheader("EV You're Considering")
    
    ev_vehicles = vehicles_df[vehicles_df["fuel_type"] == "electric"]
    ev_years = sorted([int(y) for y in ev_vehicles["year"].unique()], reverse=True)
    
    ev_year = st.selectbox(
        "Year",
        options=[None] + ev_years,
        key="ev_year",
        format_func=lambda x: "Select year..." if x is None else str(x)
    )
    
    if ev_year:
        available_ev_makes = sorted(
            ev_vehicles[ev_vehicles["year"] == ev_year]["make"].unique().tolist()
        )
    else:
        available_ev_makes = []
    
    ev_make = st.selectbox(
        "Make",
        options=[None] + available_ev_makes,
        key="ev_make",
        format_func=lambda x: "Select make..." if x is None else x
    )
    
    if ev_year and ev_make:
        available_ev_models = sorted(
            ev_vehicles[
                (ev_vehicles["year"] == ev_year) & 
                (ev_vehicles["make"] == ev_make)
            ]["model"].unique().tolist()
        )
    else:
        available_ev_models = []
    
    ev_model = st.selectbox(
        "Model",
        options=[None] + available_ev_models,
        key="ev_model",
        format_func=lambda x: "Select model..." if x is None else x
    )
    
    if ev_year and ev_make and ev_model:
        ev_kwh = ev_vehicles[
            (ev_vehicles["year"] == ev_year) &
            (ev_vehicles["make"] == ev_make) &
            (ev_vehicles["model"] == ev_model)
        ]["kwh_per_100mi"].iloc[0]
        st.metric("Efficiency", f"{ev_kwh} kWh/100mi")
    else:
        ev_kwh = None

st.divider()

# =============================================================================
# Section 3: Driving Habits
# =============================================================================

st.header("🛣️ Your Driving Habits")

col1, col2 = st.columns(2)

with col1:
    annual_miles = st.number_input(
        "Annual Miles Driven",
        min_value=1000,
        max_value=100000,
        value=12000,
        step=1000,
        help="The average American drives about 12,000 miles per year"
    )

with col2:
    charging_scenario = st.selectbox(
        "EV Charging Scenario",
        options=["home", "mixed", "public"],
        format_func=lambda x: {
            "home": "🏠 Home charging (overnight) — cheapest",
            "mixed": "🔄 Mixed (home + public)",
            "public": "⚡ Mostly public charging — most expensive"
        }[x],
        help="Where you charge affects your electricity cost"
    )

st.divider()

# =============================================================================
# Section 4: Results
# =============================================================================

# Check if we have all required inputs
inputs_valid = all([
    gas_year, gas_make, gas_model,
    ev_year, ev_make, ev_model,
    gas_mpg is not None,
    ev_kwh is not None
])

if not inputs_valid:
    st.info("👆 **Complete the selections above** to see your cost comparison.")
else:
    # Get gas price for location
    gas_price = get_gas_price(zip_code, gas_prices_df)
    
    # Get TOU multiplier
    tou_multiplier = get_tou_multiplier(charging_scenario)
    
    # Calculate comparison
    results = calculate_comparison(
        gas_mpg=gas_mpg,
        ev_kwh_per_100=ev_kwh,
        annual_miles=annual_miles,
        gas_price=gas_price,
        electricity_rate=electricity_rate,
        tou_multiplier=tou_multiplier,
        gas_vehicle_name=f"{gas_year} {gas_make} {gas_model}",
        ev_vehicle_name=f"{ev_year} {ev_make} {ev_model}"
    )
    
    # --- Big Result ---
    st.header("💰 Results")
    
    if results["annual_savings"] > 0:
        st.success(
            f"### You could save ${results['annual_savings']:,.0f}/year\n"
            f"That's **${results['monthly_savings']:,.0f}/month** by switching from your "
            f"{results['gas_vehicle_name']} to a {results['ev_vehicle_name']}."
        )
    else:
        st.warning(
            f"### The EV would cost more to fuel\n"
            f"Based on your inputs, the {results['ev_vehicle_name']} would cost "
            f"**${abs(results['annual_savings']):,.0f} more per year** in energy costs "
            f"than your {results['gas_vehicle_name']}."
        )
    
    # --- Key Metrics ---
    st.subheader("Cost Breakdown")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label=f"⛽ {results['gas_vehicle_name']}",
            value=f"${results['gas_annual_cost']:,.0f}/yr",
            delta=None
        )
    
    with col2:
        st.metric(
            label=f"🔋 {results['ev_vehicle_name']}",
            value=f"${results['ev_annual_cost']:,.0f}/yr",
            delta=f"-${results['annual_savings']:,.0f}" if results['annual_savings'] > 0 else f"+${abs(results['annual_savings']):,.0f}",
            delta_color="normal" if results['annual_savings'] > 0 else "inverse"
        )
    
    with col3:
        st.metric(
            label="Cost per Mile",
            value=f"${results['ev_cost_per_mile']:.2f}",
            delta=f"vs ${results['gas_cost_per_mile']:.2f} gas"
        )
    
    # --- Comparison Table ---
    with st.expander("📊 Detailed Comparison Table"):
        comparison_df = pd.DataFrame({
            "Metric": ["Vehicle", "Fuel Efficiency", "Annual Fuel Cost", "Cost per Mile", "Monthly Cost"],
            "Your Gas Vehicle": [
                results["gas_vehicle_name"],
                f"{results['gas_mpg']} MPG",
                f"${results['gas_annual_cost']:,.0f}",
                f"${results['gas_cost_per_mile']:.3f}",
                f"${results['gas_annual_cost']/12:,.0f}"
            ],
            "EV Option": [
                results["ev_vehicle_name"],
                f"{results['ev_kwh_per_100']} kWh/100mi",
                f"${results['ev_annual_cost']:,.0f}",
                f"${results['ev_cost_per_mile']:.3f}",
                f"${results['ev_annual_cost']/12:,.0f}"
            ]
        })
        st.table(comparison_df.set_index("Metric"))
    
    st.divider()
    
    # --- Visualizations ---
    st.header("📈 Visualizations")
    
    tab1, tab2, tab3 = st.tabs(["Annual Cost", "Savings Over Time", "What If..."])
    
    with tab1:
        # Annual cost bar chart
        cost_df = pd.DataFrame({
            "Vehicle": [results["gas_vehicle_name"], results["ev_vehicle_name"]],
            "Annual Cost": [results["gas_annual_cost"], results["ev_annual_cost"]],
            "Type": ["Gas", "Electric"]
        })
        
        fig = px.bar(
            cost_df,
            x="Vehicle",
            y="Annual Cost",
            color="Type",
            color_discrete_map={"Gas": "#ef4444", "Electric": "#22c55e"},
            text="Annual Cost"
        )
        fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
        fig.update_layout(
            title="Annual Fuel Cost Comparison",
            xaxis_title="",
            yaxis_title="Annual Cost ($)",
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Cumulative savings over time
        years_to_project = st.slider("Years to project", 1, 15, 5, key="projection_slider")
        
        years = list(range(years_to_project + 1))
        gas_cumulative = [results["gas_annual_cost"] * y for y in years]
        ev_cumulative = [results["ev_annual_cost"] * y for y in years]
        
        cumulative_df = pd.DataFrame({
            "Year": years + years,
            "Cumulative Cost": gas_cumulative + ev_cumulative,
            "Vehicle": [results["gas_vehicle_name"]] * len(years) + [results["ev_vehicle_name"]] * len(years)
        })
        
        fig = px.line(
            cumulative_df,
            x="Year",
            y="Cumulative Cost",
            color="Vehicle",
            color_discrete_map={
                results["gas_vehicle_name"]: "#ef4444",
                results["ev_vehicle_name"]: "#22c55e"
            },
            markers=True
        )
        fig.update_layout(
            title=f"Cumulative Fuel Costs Over {years_to_project} Years",
            xaxis_title="Year",
            yaxis_title="Cumulative Cost ($)",
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        total_savings = results["annual_savings"] * years_to_project
        if total_savings > 0:
            st.success(f"**Total savings over {years_to_project} years:** ${total_savings:,.0f}")
        else:
            st.warning(f"**Additional cost over {years_to_project} years:** ${abs(total_savings):,.0f}")
    
    with tab3:
        # Sensitivity analysis
        st.markdown("**Adjust prices to see how costs change:**")
        
        col1, col2 = st.columns(2)
        with col1:
            gas_price_change = st.slider(
                "Gas price change",
                min_value=-30,
                max_value=50,
                value=0,
                step=5,
                format="%d%%",
                key="gas_slider"
            )
        with col2:
            elec_price_change = st.slider(
                "Electricity price change",
                min_value=-30,
                max_value=50,
                value=0,
                step=5,
                format="%d%%",
                key="elec_slider"
            )
        
        # Recalculate with adjusted prices
        adjusted_gas_price = gas_price * (1 + gas_price_change / 100)
        adjusted_elec_rate = electricity_rate * (1 + elec_price_change / 100)
        
        adjusted_gas_cost = (annual_miles / gas_mpg) * adjusted_gas_price
        adjusted_ev_cost = (annual_miles / 100) * ev_kwh * adjusted_elec_rate * tou_multiplier
        adjusted_savings = adjusted_gas_cost - adjusted_ev_cost
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Adjusted Gas Cost",
                f"${adjusted_gas_cost:,.0f}/yr",
                f"Gas at ${adjusted_gas_price:.2f}/gal"
            )
        with col2:
            st.metric(
                "Adjusted EV Cost",
                f"${adjusted_ev_cost:,.0f}/yr",
                f"Electricity at ${adjusted_elec_rate:.3f}/kWh"
            )
        
        if adjusted_savings > 0:
            st.success(f"**Adjusted annual savings:** ${adjusted_savings:,.0f}")
        else:
            st.warning(f"**Adjusted annual extra cost:** ${abs(adjusted_savings):,.0f}")

# =============================================================================
# Footer
# =============================================================================

st.divider()

st.caption(
    "**Data sources:** EPA FuelEconomy.gov, EIA gas prices, NREL electricity rates  \n"
    "**Note:** Calculations are estimates. Actual costs vary based on driving habits, "
    "local utility rate structures, and fuel price fluctuations."
)

# Instructions if using sample data
if len(vehicles_df) < 100:
    st.info(
        "💡 **You're currently using sample data.** To get the full vehicle database and zip code coverage, "
        "run `python download_data.py` in your terminal."
    )