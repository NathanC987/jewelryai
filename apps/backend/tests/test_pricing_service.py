from pathlib import Path

from fastapi.testclient import TestClient

from app.domain.ring import RingParameters
from app.main import app
from app.services.pricing_service import PricingService, _fetch_metal_rates


def test_fetch_metal_rates_parses_metals_live_payload(monkeypatch) -> None:
    def fake_fetch_json(url: str, timeout_seconds: float) -> object:
        assert url == "https://example.test/metals"
        assert timeout_seconds == 1.0
        return [
            {"gold": 3000.0},
            {"silver": 30.0},
            {"platinum": 1100.0},
        ]

    monkeypatch.setattr("app.services.pricing_service._fetch_json", fake_fetch_json)

    rates = _fetch_metal_rates("https://example.test/metals", 1.0)

    assert rates is not None
    assert rates["gold"] > rates["silver"]
    assert rates["rose_gold"] > rates["gold"]
    assert rates["platinum"] > 0


def test_pricing_service_baseline_has_source_and_line_items(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("app.services.pricing_service.settings.pricing_market_enabled", False)
    monkeypatch.setattr("app.services.pricing_service.settings.pricing_market_cache_path", str(tmp_path / "rates.json"))

    service = PricingService()
    estimate = service.estimate_cost(RingParameters())

    assert estimate.estimated_price_usd > 0
    assert estimate.pricing_source == "baseline"
    assert len(estimate.line_items) == 3
    assert estimate.rates_timestamp_utc is not None


def test_ring_endpoints_return_pricing_metadata_and_realtime_price_change(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr("app.services.pricing_service.settings.pricing_market_enabled", False)
    monkeypatch.setattr("app.services.pricing_service.settings.pricing_market_cache_path", str(tmp_path / "rates.json"))

    client = TestClient(app)

    create_response = client.post("/api/v1/rings")
    assert create_response.status_code == 200
    created = create_response.json()

    initial_price = created["cost_estimate"]["estimated_price_usd"]
    assert created["cost_estimate"]["pricing_source"] in {"baseline", "cached", "live"}
    assert isinstance(created["cost_estimate"]["line_items"], list)
    assert created["cost_estimate"]["rates_timestamp_utc"]

    ring_id = created["ring_id"]
    patch_response = client.patch(
        f"/api/v1/rings/{ring_id}",
        json={"band_thickness_mm": 4.5, "gemstone_size_mm": 8.0},
    )
    assert patch_response.status_code == 200
    patched = patch_response.json()

    patched_price = patched["cost_estimate"]["estimated_price_usd"]
    assert patched_price != initial_price
    assert patched["cost_estimate"]["metal_weight_g"] > created["cost_estimate"]["metal_weight_g"]
