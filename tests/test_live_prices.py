# Tests for live EIA gas price fetching (network calls are mocked)

import json

import pandas as pd
import pytest
import requests

import live_prices
from live_prices import (
    fetch_live_gas_prices,
    get_eia_api_key,
    STATE_DUOAREA,
    PADD_TO_STATES,
)

ALL_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")

    def json(self):
        return self._payload


def make_payload(rows):
    return {"response": {"data": rows}}


def full_rows():
    """One current row per state series and PADD region."""
    rows = []
    for duoarea in STATE_DUOAREA.values():
        rows.append({"duoarea": duoarea, "value": 4.00, "period": "2026-08-24"})
    for padd in PADD_TO_STATES:
        rows.append({"duoarea": padd, "value": 3.00, "period": "2026-08-24"})
    return rows


class TestFetchLiveGasPrices:
    def test_covers_all_states(self, monkeypatch):
        monkeypatch.setattr(
            live_prices.requests, "get",
            lambda *a, **k: FakeResponse(make_payload(full_rows())),
        )
        df = fetch_live_gas_prices("test-key")
        assert df is not None
        assert set(df["state"]) == ALL_STATES

    def test_state_series_overrides_region(self, monkeypatch):
        monkeypatch.setattr(
            live_prices.requests, "get",
            lambda *a, **k: FakeResponse(make_payload(full_rows())),
        )
        df = fetch_live_gas_prices("test-key")
        # CA has its own series at $4.00; its region (West Coast) is $3.00
        ca = df[df["state"] == "CA"].iloc[0]
        assert ca["price_per_gallon"] == pytest.approx(4.00)
        assert ca["price_source"] == "state average"
        # OR has no direct series → West Coast regional average
        oregon = df[df["state"] == "OR"].iloc[0]
        assert oregon["price_per_gallon"] == pytest.approx(3.00)
        assert "avg" in oregon["price_source"]

    def test_keeps_most_recent_period(self, monkeypatch):
        rows = [
            {"duoarea": "SCA", "value": 4.50, "period": "2026-08-24"},
            {"duoarea": "SCA", "value": 4.10, "period": "2026-08-17"},
            {"duoarea": "R50", "value": 4.20, "period": "2026-08-24"},
        ]
        monkeypatch.setattr(
            live_prices.requests, "get",
            lambda *a, **k: FakeResponse(make_payload(rows)),
        )
        df = fetch_live_gas_prices("test-key")
        ca = df[df["state"] == "CA"].iloc[0]
        assert ca["price_per_gallon"] == pytest.approx(4.50)
        assert ca["period"] == "2026-08-24"

    def test_skips_bad_rows(self, monkeypatch):
        rows = [
            {"duoarea": "R50", "value": None, "period": "2026-08-24"},
            {"duoarea": "R50", "value": -1, "period": "2026-08-24"},
            {"duoarea": "R50", "value": "not-a-number", "period": "2026-08-24"},
            {"duoarea": "R50", "value": 4.20, "period": "2026-08-17"},
        ]
        monkeypatch.setattr(
            live_prices.requests, "get",
            lambda *a, **k: FakeResponse(make_payload(rows)),
        )
        df = fetch_live_gas_prices("test-key")
        assert df is not None
        wa = df[df["state"] == "WA"].iloc[0]
        assert wa["price_per_gallon"] == pytest.approx(4.20)

    def test_network_error_returns_none(self, monkeypatch):
        def boom(*a, **k):
            raise requests.ConnectionError("no network")
        monkeypatch.setattr(live_prices.requests, "get", boom)
        assert fetch_live_gas_prices("test-key") is None

    def test_http_error_returns_none(self, monkeypatch):
        monkeypatch.setattr(
            live_prices.requests, "get",
            lambda *a, **k: FakeResponse({}, status=403),
        )
        assert fetch_live_gas_prices("bad-key") is None

    def test_unexpected_shape_returns_none(self, monkeypatch):
        monkeypatch.setattr(
            live_prices.requests, "get",
            lambda *a, **k: FakeResponse({"unexpected": True}),
        )
        assert fetch_live_gas_prices("test-key") is None

    def test_empty_data_returns_none(self, monkeypatch):
        monkeypatch.setattr(
            live_prices.requests, "get",
            lambda *a, **k: FakeResponse(make_payload([])),
        )
        assert fetch_live_gas_prices("test-key") is None

    def test_result_schema_matches_static(self, monkeypatch):
        # The live frame must be a drop-in replacement for the static one
        monkeypatch.setattr(
            live_prices.requests, "get",
            lambda *a, **k: FakeResponse(make_payload(full_rows())),
        )
        df = fetch_live_gas_prices("test-key")
        assert {"state", "price_per_gallon"} <= set(df.columns)
        assert df["price_per_gallon"].dtype.kind == "f"


class TestPaddCoverage:
    def test_every_state_has_a_region(self):
        covered = {s for states in PADD_TO_STATES.values() for s in states}
        assert covered == ALL_STATES

    def test_no_state_in_two_regions(self):
        seen = []
        for states in PADD_TO_STATES.values():
            seen.extend(states)
        assert len(seen) == len(set(seen))


class TestGetEiaApiKey:
    def test_reads_env(self, monkeypatch):
        monkeypatch.setenv("EIA_API_KEY", "abc123")
        assert get_eia_api_key() == "abc123"

    def test_missing_or_blank(self, monkeypatch):
        monkeypatch.delenv("EIA_API_KEY", raising=False)
        assert get_eia_api_key() is None
        monkeypatch.setenv("EIA_API_KEY", "   ")
        assert get_eia_api_key() is None
