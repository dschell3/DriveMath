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
    get_data_freshness,
    validate_zip,
)
from live_prices import fetch_live_gas_prices, get_eia_api_key
from calculations import (
    calculate_comparison,
    calculate_cumulative_costs,
    calculate_breakeven_years,
    calculate_emissions_comparison,
    kwh_to_mpge,
)

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


# --- Live gas prices (EIA API, refreshed every 6 hours) ---

@st.cache_data(ttl=6 * 3600, show_spinner=False)
def load_live_gas_prices(api_key: str):
    return fetch_live_gas_prices(api_key)


def resolve_eia_api_key() -> str | None:
    """EIA key from Streamlit secrets or the environment."""
    try:
        key = str(st.secrets.get("EIA_API_KEY", "")).strip()
        if key:
            return key
    except Exception:
        pass
    return get_eia_api_key()


eia_api_key = resolve_eia_api_key()
live_gas_df = None
if eia_api_key:
    with st.spinner("Fetching live gas prices from EIA..."):
        live_gas_df = load_live_gas_prices(eia_api_key)

if live_gas_df is not None:
    gas_prices_df = live_gas_df
    gas_data_week = live_gas_df["period"].max()
    gas_data_note = f"Live EIA weekly prices (week of {gas_data_week})"
elif eia_api_key:
    gas_data_note = "Static state averages (live EIA fetch failed — check your key or connection)"
else:
    gas_data_note = "Static state averages (add an EIA API key for live weekly prices)"


# --- Sidebar: about + data provenance ---

with st.sidebar:
    st.header("ℹ️ About DriveMath")
    st.markdown(
        "Estimates what you'd spend fueling an EV vs. your current gas "
        "vehicle, using your local electricity rate and gas price."
    )
    st.subheader("📅 Data status")
    st.markdown(f"**Gas prices:** {gas_data_note}")
    for dataset, status in get_data_freshness().items():
        if dataset == "Gas prices" and live_gas_df is not None:
            continue
        st.markdown(f"**{dataset}:** {status}")
    if live_gas_df is None:
        st.caption(
            "For live weekly gas prices, get a free API key at "
            "[eia.gov/opendata](https://www.eia.gov/opendata/register.php) "
            "and set it as `EIA_API_KEY` (environment variable or in "
            "`.streamlit/secrets.toml`)."
        )
    st.caption(
        "Sources: EPA FuelEconomy.gov · NREL/OpenEI utility rates · "
        "EIA gasoline prices"
    )

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

col1, col2 = st.columns(2)

with col1:
    zip_input = st.text_input(
        "Zip Code",
        value="95822",
        max_chars=5,
        placeholder="e.g., 90210"
    )

zip_code = validate_zip(zip_input)
if zip_code is None:
    st.error("Please enter a valid 5-digit zip code.")
    zip_code = ""

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

# Gas price for this location (state average, with national fallback)
gas_price, gas_price_state = get_gas_price(zip_code, gas_prices_df, electricity_df)
if gas_price_state:
    if live_gas_df is not None:
        source_rows = live_gas_df[live_gas_df["state"] == gas_price_state]
        price_source = source_rows["price_source"].iloc[0] if not source_rows.empty else "state average"
        week = source_rows["period"].iloc[0] if not source_rows.empty else ""
        st.caption(
            f"⛽ Gas price for your area: **${gas_price:.2f}/gal** "
            f"({gas_price_state} — live EIA {price_source}, week of {week})"
        )
    else:
        st.caption(f"⛽ Gas price for your area: **${gas_price:.2f}/gal** ({gas_price_state} state average, static)")
else:
    st.caption(f"⛽ Gas price: **${gas_price:.2f}/gal** (national average — couldn't determine your state)")

# Let users override the looked-up prices with what they actually pay —
# a utility bill or local pump price beats any dataset average
with st.expander("⚙️ Know your actual prices? Override them here"):
    override_col1, override_col2 = st.columns(2)
    with override_col1:
        use_custom_elec = st.checkbox("Custom electricity rate", key="use_custom_elec")
        if use_custom_elec:
            electricity_rate = st.number_input(
                "Your rate ($/kWh)",
                min_value=0.01,
                max_value=1.00,
                value=float(electricity_rate),
                step=0.01,
                format="%.3f",
                help="Find this on your utility bill (total cost ÷ kWh used is most accurate)"
            )
            utility_name = "Custom rate"
    with override_col2:
        use_custom_gas = st.checkbox("Custom gas price", key="use_custom_gas")
        if use_custom_gas:
            gas_price = st.number_input(
                "Your gas price ($/gal)",
                min_value=0.50,
                max_value=10.00,
                value=float(gas_price),
                step=0.05,
                format="%.2f",
                help="What you typically pay at the pump"
            )

st.divider()

# =============================================================================
# Section 2: Vehicle Selection
# =============================================================================

st.header("🚘 Select Vehicles to Compare")

col_gas, col_ev = st.columns(2, border=True)

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
        # Average across trims if the data file has multiple entries
        gas_mpg = round(gas_vehicles[
            (gas_vehicles["year"] == gas_year) &
            (gas_vehicles["make"] == gas_make) &
            (gas_vehicles["model"] == gas_model)
        ]["combined_mpg"].mean(), 1)
        st.metric("Combined MPG", f"{gas_mpg:g}")
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
        # Average across trims if the data file has multiple entries
        ev_kwh = round(ev_vehicles[
            (ev_vehicles["year"] == ev_year) &
            (ev_vehicles["make"] == ev_make) &
            (ev_vehicles["model"] == ev_model)
        ]["kwh_per_100mi"].mean(), 1)
        st.metric("Efficiency", f"{ev_kwh:g} kWh/100mi")
        if pd.notna(ev_kwh) and ev_kwh > 0:
            st.caption(f"≈ {kwh_to_mpge(ev_kwh):.0f} MPGe (gas-equivalent efficiency)")
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
    gas_mpg is not None and pd.notna(gas_mpg) and gas_mpg > 0,
    ev_kwh is not None and pd.notna(ev_kwh) and ev_kwh > 0,
])

if not inputs_valid:
    st.info("👆 **Complete the selections above** to see your cost comparison.")
else:
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
    
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Annual Cost", "Savings Over Time", "What If...", "Environmental Impact"]
    )
    
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
        st.plotly_chart(fig, width="stretch")
    
    with tab2:
        # Cumulative savings over time
        years_to_project = st.slider("Years to project", 1, 15, 5, key="projection_slider")

        with st.expander("📈 Projection options (price inflation, purchase prices)"):
            esc_col1, esc_col2 = st.columns(2)
            with esc_col1:
                gas_escalation = st.slider(
                    "Annual gas price increase",
                    min_value=0, max_value=10, value=0, step=1,
                    format="%d%%", key="gas_escalation",
                    help="US gas prices have historically risen ~2-4% per year"
                )
            with esc_col2:
                elec_escalation = st.slider(
                    "Annual electricity price increase",
                    min_value=0, max_value=10, value=0, step=1,
                    format="%d%%", key="elec_escalation",
                    help="US residential electricity rates have historically risen ~2-3% per year"
                )

            include_purchase = st.checkbox(
                "Include purchase prices (breakeven analysis)",
                key="include_purchase"
            )
            gas_purchase_price = 0.0
            ev_purchase_price = 0.0
            if include_purchase:
                price_col1, price_col2 = st.columns(2)
                with price_col1:
                    gas_purchase_price = st.number_input(
                        "Gas vehicle price ($)",
                        min_value=0, max_value=200000, value=0, step=1000,
                        key="gas_purchase_price",
                        help="Use $0 if you already own it and are only weighing the switch"
                    )
                with price_col2:
                    ev_purchase_price = st.number_input(
                        "EV price ($)",
                        min_value=0, max_value=200000, value=45000, step=1000,
                        key="ev_purchase_price",
                        help="After any tax credits or incentives"
                    )

        gas_fuel_cumulative = calculate_cumulative_costs(
            results["gas_annual_cost"], years_to_project, gas_escalation / 100
        )
        ev_fuel_cumulative = calculate_cumulative_costs(
            results["ev_annual_cost"], years_to_project, elec_escalation / 100
        )

        years = list(range(years_to_project + 1))
        gas_cumulative = [gas_purchase_price] + [gas_purchase_price + c for c in gas_fuel_cumulative]
        ev_cumulative = [ev_purchase_price] + [ev_purchase_price + c for c in ev_fuel_cumulative]

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
        chart_title = f"Cumulative {'Total' if include_purchase else 'Fuel'} Costs Over {years_to_project} Years"
        fig.update_layout(
            title=chart_title,
            xaxis_title="Year",
            yaxis_title="Cumulative Cost ($)",
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, width="stretch")

        total_savings = gas_cumulative[-1] - ev_cumulative[-1]
        if total_savings > 0:
            st.success(f"**Total savings over {years_to_project} years:** ${total_savings:,.0f}")
        else:
            st.warning(f"**Additional cost over {years_to_project} years:** ${abs(total_savings):,.0f}")

        if include_purchase:
            ev_premium = ev_purchase_price - gas_purchase_price
            if ev_premium <= 0:
                st.info("The EV costs no more upfront, so any fuel savings are immediate.")
            else:
                breakeven = calculate_breakeven_years(ev_premium, results["annual_savings"])
                if breakeven == float("inf"):
                    st.info(
                        "At current prices the EV doesn't save on fuel, "
                        "so the purchase premium never breaks even."
                    )
                elif breakeven > years_to_project:
                    st.info(
                        f"**Breakeven: ~{breakeven:.1f} years** — the ${ev_premium:,.0f} EV premium "
                        f"pays back beyond your {years_to_project}-year projection window."
                    )
                else:
                    st.success(
                        f"**Breakeven: ~{breakeven:.1f} years** — after that, "
                        f"the ${ev_premium:,.0f} EV premium is paid back by fuel savings."
                    )
    
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

    with tab4:
        emissions = calculate_emissions_comparison(
            gas_mpg=gas_mpg,
            ev_kwh_per_100=ev_kwh,
            annual_miles=annual_miles,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "⛽ Gas Vehicle CO₂",
                f"{emissions['gas_annual_co2_kg']:,.0f} kg/yr"
            )
        with col2:
            st.metric(
                "🔋 EV CO₂ (grid)",
                f"{emissions['ev_annual_co2_kg']:,.0f} kg/yr"
            )
        with col3:
            st.metric(
                "CO₂ Reduction",
                f"{emissions['co2_reduction_pct']:.0f}%",
                delta=f"-{emissions['annual_co2_savings_kg']:,.0f} kg/yr",
                delta_color="inverse"
            )

        emissions_df = pd.DataFrame({
            "Vehicle": [results["gas_vehicle_name"], results["ev_vehicle_name"]],
            "Annual CO₂ (kg)": [
                emissions["gas_annual_co2_kg"],
                emissions["ev_annual_co2_kg"]
            ],
            "Type": ["Gas", "Electric"]
        })
        fig = px.bar(
            emissions_df,
            x="Vehicle",
            y="Annual CO₂ (kg)",
            color="Type",
            color_discrete_map={"Gas": "#ef4444", "Electric": "#22c55e"},
            text="Annual CO₂ (kg)"
        )
        fig.update_traces(texttemplate="%{text:,.0f} kg", textposition="outside")
        fig.update_layout(
            title="Estimated Annual CO₂ Emissions",
            xaxis_title="",
            yaxis_title="CO₂ (kg/year)",
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig, width="stretch")

        st.caption(
            "Estimates cover gasoline combustion vs. US-average grid electricity "
            "(~0.39 kg CO₂/kWh), not upstream fuel production or vehicle manufacturing. "
            "Your grid may be cleaner or dirtier than average — regions with more "
            "hydro, nuclear, wind, or solar power make EVs even cleaner."
        )

# =============================================================================
# Footer
# =============================================================================

st.divider()

st.caption(
    "**Data sources:** EPA FuelEconomy.gov, EIA gas prices, NREL electricity rates  \n"
    f"**Gas price data:** {gas_data_note}  \n"
    "**Note:** Calculations are estimates. Actual costs vary based on driving habits, "
    "local utility rate structures, and fuel price fluctuations."
)

# Instructions if using sample data
if len(vehicles_df) < 100:
    st.info(
        "💡 **You're currently using sample data.** To get the full vehicle database and zip code coverage, "
        "run `python download_data.py` in your terminal."
    )