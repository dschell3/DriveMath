# Tests for data loading and lookup functions

import pandas as pd
import pytest

from data_loader import (
    create_sample_vehicle_data,
    create_sample_electricity_data,
    create_sample_gas_data,
    get_utilities_for_zip,
    get_gas_price,
    get_state_for_zip,
    get_tou_multiplier,
    validate_zip,
    zip_to_state,
    NATIONAL_AVG_GAS_PRICE,
)


class TestValidateZip:
    def test_valid(self):
        assert validate_zip("95822") == "95822"

    def test_strips_whitespace(self):
        assert validate_zip(" 95822 ") == "95822"

    def test_rejects_short(self):
        assert validate_zip("9582") is None

    def test_rejects_letters(self):
        assert validate_zip("9582a") is None
        assert validate_zip("abcde") is None

    def test_rejects_empty(self):
        assert validate_zip("") is None
        assert validate_zip(None) is None


class TestZipToState:
    @pytest.mark.parametrize("zip_code,state", [
        ("95822", "CA"),  # Sacramento
        ("90210", "CA"),  # Beverly Hills
        ("10001", "NY"),  # NYC
        ("60601", "IL"),  # Chicago
        ("77001", "TX"),  # Houston
        ("98101", "WA"),  # Seattle
        ("33101", "FL"),  # Miami
        ("02134", "MA"),  # Boston
        ("80202", "CO"),  # Denver
        ("85001", "AZ"),  # Phoenix
        ("97201", "OR"),  # Portland
        ("55401", "MN"),  # Minneapolis
        ("37201", "TN"),  # Nashville
        ("70112", "LA"),  # New Orleans
        ("89101", "NV"),  # Las Vegas
        ("96813", "HI"),  # Honolulu
        ("99501", "AK"),  # Anchorage
        ("20001", "DC"),  # Washington DC
        ("23219", "VA"),  # Richmond
        ("43215", "OH"),  # Columbus
        ("48201", "MI"),  # Detroit
        ("53202", "WI"),  # Milwaukee
        ("64101", "MO"),  # Kansas City
        ("73101", "OK"),  # Oklahoma City
        ("84101", "UT"),  # Salt Lake City
        ("87101", "NM"),  # Albuquerque
        ("59601", "MT"),  # Helena
        ("58501", "ND"),  # Bismarck
        ("82001", "WY"),  # Cheyenne
        ("05601", "VT"),  # Montpelier
        ("03301", "NH"),  # Concord
        ("04330", "ME"),  # Augusta
        ("06103", "CT"),  # Hartford
        ("02903", "RI"),  # Providence
        ("07102", "NJ"),  # Newark
        ("19801", "DE"),  # Wilmington
        ("21201", "MD"),  # Baltimore
        ("25301", "WV"),  # Charleston
        ("27601", "NC"),  # Raleigh
        ("29201", "SC"),  # Columbia
        ("30301", "GA"),  # Atlanta
        ("35201", "AL"),  # Birmingham
        ("39201", "MS"),  # Jackson
        ("40202", "KY"),  # Louisville
        ("46204", "IN"),  # Indianapolis
        ("50309", "IA"),  # Des Moines
        ("57501", "SD"),  # Pierre
        ("66603", "KS"),  # Topeka
        ("68102", "NE"),  # Omaha
        ("72201", "AR"),  # Little Rock
        ("83702", "ID"),  # Boise
        ("15222", "PA"),  # Pittsburgh
    ])
    def test_major_cities(self, zip_code, state):
        assert zip_to_state(zip_code) == state

    def test_invalid_input(self):
        assert zip_to_state("") is None
        assert zip_to_state("ab") is None
        assert zip_to_state("abcde") is None

    def test_unassigned_prefix(self):
        # 000-004 are not assigned
        assert zip_to_state("00099") is None


class TestGetStateForZip:
    def test_prefers_dataset_state(self):
        electricity = pd.DataFrame({
            "zip": ["12345"],
            "state": ["XX"],
            "utility_name": ["Test"],
            "residential_rate": [0.15],
        })
        assert get_state_for_zip("12345", electricity) == "XX"

    def test_falls_back_to_prefix(self):
        electricity = create_sample_electricity_data()
        # Not in the sample data, but the prefix maps to CO
        assert get_state_for_zip("80202", electricity) == "CO"


class TestGetUtilitiesForZip:
    def test_multi_utility_zip(self):
        electricity = create_sample_electricity_data()
        utilities = get_utilities_for_zip("95822", electricity)
        assert len(utilities) == 2
        assert set(utilities["utility_name"]) == {"SMUD", "PG&E"}
        # Sorted cheapest first
        assert utilities.iloc[0]["residential_rate"] <= utilities.iloc[1]["residential_rate"]

    def test_single_utility_zip(self):
        electricity = create_sample_electricity_data()
        utilities = get_utilities_for_zip("90210", electricity)
        assert len(utilities) == 1
        assert utilities.iloc[0]["utility_name"] == "SCE"

    def test_unknown_zip(self):
        electricity = create_sample_electricity_data()
        assert len(get_utilities_for_zip("00000", electricity)) == 0


class TestGetGasPrice:
    def test_known_state(self):
        gas = create_sample_gas_data()
        price, state = get_gas_price("95822", gas)
        assert state == "CA"
        assert price == pytest.approx(4.50)

    def test_uses_electricity_data_state(self):
        gas = create_sample_gas_data()
        electricity = pd.DataFrame({
            "zip": ["00001"],
            "state": ["TX"],
            "utility_name": ["Test"],
            "residential_rate": [0.12],
        })
        price, state = get_gas_price("00001", gas, electricity)
        assert state == "TX"

    def test_unknown_zip_falls_back(self):
        gas = create_sample_gas_data()
        price, state = get_gas_price("00000", gas)
        assert state is None
        assert price == NATIONAL_AVG_GAS_PRICE


class TestTouMultiplier:
    def test_scenarios(self):
        assert get_tou_multiplier("home") == 0.80
        assert get_tou_multiplier("mixed") == 0.95
        assert get_tou_multiplier("public") == 1.20

    def test_unknown_scenario_is_neutral(self):
        assert get_tou_multiplier("bogus") == 1.0


class TestSampleData:
    def test_vehicle_data_shape(self):
        vehicles = create_sample_vehicle_data()
        assert {"year", "make", "model", "fuel_type", "combined_mpg", "kwh_per_100mi"} <= set(vehicles.columns)
        gas = vehicles[vehicles["fuel_type"] == "gas"]
        evs = vehicles[vehicles["fuel_type"] == "electric"]
        assert len(gas) > 0 and len(evs) > 0
        assert gas["combined_mpg"].notna().all()
        assert evs["kwh_per_100mi"].notna().all()

    def test_gas_data_covers_all_states(self):
        gas = create_sample_gas_data()
        assert len(gas) == 51  # 50 states + DC
        assert (gas["price_per_gallon"] > 0).all()

    def test_electricity_rates_plausible(self):
        electricity = create_sample_electricity_data()
        assert (electricity["residential_rate"] > 0.01).all()
        assert (electricity["residential_rate"] < 1.00).all()
