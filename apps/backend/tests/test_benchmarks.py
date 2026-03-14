from fastapi.testclient import TestClient

from app.main import app


def test_edit_latency_benchmark_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/benchmarks/edits?iterations=8")
    assert response.status_code == 200
    payload = response.json()

    assert payload["iterations"] == 8
    assert payload["target_max_ms"] == 1000.0
    assert payload["overall_max_ms"] >= 0
    assert isinstance(payload["meets_target"], bool)

    metrics = {item["operation"]: item for item in payload["per_operation"]}
    assert set(metrics.keys()) == {
        "material_swap",
        "gemstone_type_swap",
        "gemstone_size_adjustment",
        "band_thickness_adjustment",
    }

    for item in metrics.values():
        assert item["samples"] == 8
        assert item["min_ms"] >= 0
        assert item["avg_ms"] >= 0
        assert item["max_ms"] >= item["min_ms"]
