from fastapi.testclient import TestClient

from app.main import app


def test_generate_style_variations_for_ring() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/rings")
    assert create_response.status_code == 200
    ring_id = create_response.json()["ring_id"]

    variation_response = client.post(f"/api/v1/rings/{ring_id}/variations?count=5")
    assert variation_response.status_code == 200

    payload = variation_response.json()
    assert payload["source_ring_id"] == ring_id
    assert len(payload["suggestions"]) == 5

    style_names = {item["style_name"] for item in payload["suggestions"]}
    assert style_names == {"Minimalist", "Vintage", "Royal", "Modern", "Bold"}

    ring_ids = [item["ring"]["ring_id"] for item in payload["suggestions"]]
    assert len(set(ring_ids)) == 5


def test_generate_variations_missing_ring() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/rings/not-found/variations")
    assert response.status_code == 404
