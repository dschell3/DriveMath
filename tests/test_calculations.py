# Tests for core cost calculation logic

import pytest

from calculations import (
    calculate_comparison,
    calculate_gas_annual_cost,
    calculate_ev_annual_cost,
    calculate_cumulative_costs,
    calculate_breakeven_years,
    calculate_emissions_comparison,
    mpg_to_miles_per_kwh,
    kwh_to_mpge,
    CO2_KG_PER_GALLON,
)


class TestGasAnnualCost:
    def test_basic(self):
        # 12,000 miles / 30 mpg = 400 gallons * $4.50 = $1,800
        assert calculate_gas_annual_cost(12000, 30, 4.50) == pytest.approx(1800)

    def test_zero_mpg_raises(self):
        with pytest.raises(ValueError):
            calculate_gas_annual_cost(12000, 0, 4.50)

    def test_negative_mpg_raises(self):
        with pytest.raises(ValueError):
            calculate_gas_annual_cost(12000, -5, 4.50)


class TestEvAnnualCost:
    def test_basic(self):
        # 12,000 mi / 100 * 31 kWh * $0.18 = $669.60
        assert calculate_ev_annual_cost(12000, 31, 0.18) == pytest.approx(669.60)

    def test_tou_multiplier_applied(self):
        base = calculate_ev_annual_cost(12000, 31, 0.18, tou_multiplier=1.0)
        home = calculate_ev_annual_cost(12000, 31, 0.18, tou_multiplier=0.80)
        assert home == pytest.approx(base * 0.80)

    def test_zero_efficiency_raises(self):
        with pytest.raises(ValueError):
            calculate_ev_annual_cost(12000, 0, 0.18)


class TestCalculateComparison:
    def test_readme_example(self):
        # The worked example from the README
        results = calculate_comparison(
            gas_mpg=30,
            ev_kwh_per_100=31,
            annual_miles=12000,
            gas_price=4.50,
            electricity_rate=0.18,
            tou_multiplier=0.80,
        )
        assert results["gas_annual_cost"] == pytest.approx(1800)
        assert results["ev_annual_cost"] == pytest.approx(535.68)
        assert results["annual_savings"] == pytest.approx(1264.32)
        assert results["monthly_savings"] == pytest.approx(1264.32 / 12)

    def test_cost_per_mile(self):
        results = calculate_comparison(
            gas_mpg=25,
            ev_kwh_per_100=30,
            annual_miles=10000,
            gas_price=3.00,
            electricity_rate=0.15,
        )
        assert results["gas_cost_per_mile"] == pytest.approx(3.00 / 25)
        assert results["ev_cost_per_mile"] == pytest.approx(0.30 * 0.15)

    def test_ev_can_cost_more(self):
        # Efficient hybrid vs pricey public charging
        results = calculate_comparison(
            gas_mpg=55,
            ev_kwh_per_100=48,
            annual_miles=12000,
            gas_price=2.60,
            electricity_rate=0.30,
            tou_multiplier=1.20,
        )
        assert results["annual_savings"] < 0

    def test_zero_miles_raises(self):
        with pytest.raises(ValueError):
            calculate_comparison(
                gas_mpg=30, ev_kwh_per_100=31, annual_miles=0,
                gas_price=4.50, electricity_rate=0.18,
            )


class TestCumulativeCosts:
    def test_no_escalation(self):
        assert calculate_cumulative_costs(1000, 3) == pytest.approx([1000, 2000, 3000])

    def test_with_escalation(self):
        # 10% annual increase: 1000, 1100, 1210 → cumulative 1000, 2100, 3310
        result = calculate_cumulative_costs(1000, 3, annual_increase=0.10)
        assert result == pytest.approx([1000, 2100, 3310])

    def test_zero_years(self):
        assert calculate_cumulative_costs(1000, 0) == []


class TestBreakeven:
    def test_basic(self):
        assert calculate_breakeven_years(10000, 2000) == pytest.approx(5.0)

    def test_no_savings_never_breaks_even(self):
        assert calculate_breakeven_years(10000, 0) == float("inf")
        assert calculate_breakeven_years(10000, -500) == float("inf")


class TestEmissions:
    def test_basic(self):
        result = calculate_emissions_comparison(
            gas_mpg=30, ev_kwh_per_100=31, annual_miles=12000
        )
        # 400 gallons * 8.887 kg
        assert result["gas_annual_co2_kg"] == pytest.approx(400 * CO2_KG_PER_GALLON)
        # 3720 kWh * grid intensity
        assert result["ev_annual_co2_kg"] == pytest.approx(3720 * 0.39)
        assert result["annual_co2_savings_kg"] == pytest.approx(
            result["gas_annual_co2_kg"] - result["ev_annual_co2_kg"]
        )
        assert 0 < result["co2_reduction_pct"] < 100

    def test_custom_grid_intensity(self):
        clean = calculate_emissions_comparison(
            gas_mpg=30, ev_kwh_per_100=31, annual_miles=12000,
            grid_co2_kg_per_kwh=0.05,
        )
        dirty = calculate_emissions_comparison(
            gas_mpg=30, ev_kwh_per_100=31, annual_miles=12000,
            grid_co2_kg_per_kwh=0.80,
        )
        assert clean["ev_annual_co2_kg"] < dirty["ev_annual_co2_kg"]


class TestConversions:
    def test_round_trip(self):
        # 30 kWh/100mi → MPGe → same energy content
        mpge = kwh_to_mpge(30)
        assert mpge == pytest.approx((100 / 30) * 33.7)

    def test_mpg_to_miles_per_kwh(self):
        assert mpg_to_miles_per_kwh(33.7) == pytest.approx(1.0)
