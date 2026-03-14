from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.main import app


def test_sketch_upload_returns_extracted_parameters() -> None:
    client = TestClient(app)

    image = Image.new("RGB", (220, 220), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((20, 110, 200, 200), outline="black", width=10)
    draw.ellipse((80, 40, 140, 100), outline="black", width=6)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    response = client.post(
        "/api/v1/sketches/upload",
        files={"file": ("ring-sketch.png", buffer.getvalue(), "image/png")},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["sketch_id"]
    assert payload["artifact_uri"].startswith("/artifacts/sketches/")
    assert payload["artifact_uri"].endswith(".png")
    assert payload["analysis_uri"].startswith("/api/v1/sketches/")
    assert payload["analysis_backend"] in {"deterministic", "mock_model"}

    extracted = payload["extracted_parameters"]
    assert extracted["metal"] in {"gold", "rose_gold", "platinum", "silver"}
    assert extracted["gemstone_type"] in {"diamond", "ruby", "emerald", "sapphire"}
    assert extracted["center_stone_shape"] in {
        "round",
        "oval",
        "princess",
        "emerald_cut",
        "marquise",
        "pear",
    }
    assert extracted["band_profile"] in {"classic", "flat", "knife_edge", "tapered"}
    assert 0 <= extracted["side_stone_count"] <= 24
    assert 0.6 <= extracted["setting_height_mm"] <= 5.0
    assert 2 <= extracted["prong_count"] <= 8
    assert 1.0 <= extracted["gemstone_size_mm"] <= 12.0
    assert 1.2 <= extracted["band_thickness_mm"] <= 5.0

    analysis_response = client.get(payload["analysis_uri"])
    assert analysis_response.status_code == 200
    analysis = analysis_response.json()
    assert analysis["sketch_id"] == payload["sketch_id"]
    assert analysis["analysis_backend"] == payload["analysis_backend"]
    assert len(analysis["components"]) >= 3
    assert len(analysis["feature_confidences"]) >= 5
    assert isinstance(analysis["requires_user_confirmation"], bool)
