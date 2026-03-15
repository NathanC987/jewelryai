from fastapi.testclient import TestClient

from app.main import app


def test_create_and_update_ring() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/rings")
    assert create_response.status_code == 200
    created = create_response.json()

    ring_id = created["ring_id"]
    assert created["parameters"]["metal"] == "gold"
    assert created["graph_version"] == 1

    patch_response = client.patch(
        f"/api/v1/rings/{ring_id}",
        json={"metal": "rose_gold", "band_thickness_mm": 1.5},
    )
    assert patch_response.status_code == 200

    patched = patch_response.json()
    assert patched["parameters"]["metal"] == "rose_gold"
    assert patched["parameters"]["band_thickness_mm"] == 1.5
    assert patched["graph_version"] == 2
    assert patched["last_update_diff"]["changed_fields"] == [
        "metal",
        "band_thickness_mm",
    ]
    assert patched["last_update_diff"]["impacted_components"] == ["band", "prongs"]
    assert any(
        w["code"] == "BAND_THIN" for w in patched["manufacturability_warnings"]
    )


def test_ring_graph_endpoint() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/rings")
    ring_id = create_response.json()["ring_id"]

    graph_response = client.get(f"/api/v1/rings/{ring_id}/graph")
    assert graph_response.status_code == 200
    graph = graph_response.json()

    assert graph["version"] == 1
    node_ids = {node["node_id"] for node in graph["nodes"]}
    assert {"ring", "band", "center_stone", "side_stones", "prongs"}.issubset(node_ids)


def test_create_ring_from_prompt_halo_vintage() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/rings/from-prompt",
        json={"prompt": "A vintage oval halo ring in rose gold with ruby"},
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["interpretation"]["template_id"] == "halo_ring"
    assert payload["interpretation"]["style_tag"] == "vintage"
    assert "setting.halo" in payload["interpretation"]["selected_components"]
    assert "style.milgrain_bezel" in payload["interpretation"]["selected_components"]
    assert payload["interpretation"]["confidence"] >= 0.7
    assert payload["ring"]["parameters"]["template_id"] == "halo_ring"
    assert payload["ring"]["parameters"]["style_tag"] == "vintage"
    assert payload["ring"]["parameters"]["metal"] == "rose_gold"
    assert payload["ring"]["parameters"]["gemstone_type"] == "ruby"
    assert payload["ring"]["parameters"]["center_stone_shape"] == "oval"


def test_create_ring_from_prompt_defaults_to_solitaire() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/rings/from-prompt",
        json={"prompt": "elegant engagement ring"},
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["interpretation"]["template_id"] == "solitaire_ring"
    assert payload["interpretation"]["selected_components"]
    assert payload["ring"]["parameters"]["template_id"] == "solitaire_ring"


def test_create_ring_from_prompt_royal_solitaire_keeps_clean_shoulder_defaults() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/rings/from-prompt",
        json={"prompt": "elegant solitaire diamond ring, royal style, platinum"},
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["interpretation"]["template_id"] == "solitaire_ring"
    assert payload["interpretation"]["style_tag"] == "royal"
    assert "setting.royal_crown" in payload["interpretation"]["selected_components"]
    assert payload["ring"]["parameters"]["side_stone_count"] == 0


def test_change_prompt_endpoint_updates_component_recipe() -> None:
    client = TestClient(app)

    created = client.post(
        "/api/v1/rings/from-prompt",
        json={"prompt": "elegant solitaire diamond ring"},
    ).json()
    ring_id = created["ring"]["ring_id"]

    response = client.post(
        f"/api/v1/rings/{ring_id}/change-prompt",
        json={"prompt": "switch to marquise bezel open heart with cathedral shank 10"},
    )
    assert response.status_code == 200
    patched = response.json()

    assert patched["parameters"]["center_stone_shape"] == "marquise"
    assert patched["parameters"]["setting_family"] == "bezel"
    assert patched["parameters"]["setting_openheart"] is True
    assert patched["parameters"]["shank_family"] == "cathedral"
    assert patched["parameters"]["shank_variant"] == 10
