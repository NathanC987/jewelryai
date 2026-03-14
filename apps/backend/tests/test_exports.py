from pathlib import Path
import time

from fastapi.testclient import TestClient
import trimesh

from app.main import app


def test_export_endpoints_for_existing_ring() -> None:
    client = TestClient(app)
    create_response = client.post("/api/v1/rings")
    ring_id = create_response.json()["ring_id"]

    backend_root = Path(__file__).resolve().parents[1]
    ring_dir = backend_root / "artifacts" / ring_id
    if ring_dir.exists():
        for child in ring_dir.iterdir():
            child.unlink()
        ring_dir.rmdir()

    glb = client.get(f"/api/v1/exports/{ring_id}/glb")
    stl = client.get(f"/api/v1/exports/{ring_id}/stl")

    assert glb.status_code == 200
    assert stl.status_code == 200
    assert glb.json()["format"] == "glb"
    assert stl.json()["format"] == "stl"

    glb_path = backend_root / "artifacts" / ring_id / "model.glb"
    stl_path = backend_root / "artifacts" / ring_id / "model.stl"
    assert glb_path.exists()
    assert stl_path.exists()
    assert glb_path.stat().st_size > 0
    assert stl_path.stat().st_size > 0

    glb_file = client.get(glb.json()["artifact_uri"])
    stl_file = client.get(stl.json()["artifact_uri"])
    assert glb_file.status_code == 200
    assert stl_file.status_code == 200


def test_export_regenerates_after_parameter_updates() -> None:
    client = TestClient(app)
    create_response = client.post("/api/v1/rings")
    ring_id = create_response.json()["ring_id"]

    backend_root = Path(__file__).resolve().parents[1]
    stl_path = backend_root / "artifacts" / ring_id / "model.stl"

    first_export = client.get(f"/api/v1/exports/{ring_id}/stl")
    assert first_export.status_code == 200
    first_mesh = trimesh.load_mesh(stl_path, file_type="stl")
    first_volume = float(first_mesh.volume)
    first_mtime = stl_path.stat().st_mtime

    # Ensure mtime resolution does not hide regeneration on fast filesystems.
    time.sleep(0.02)

    patch_response = client.patch(
        f"/api/v1/rings/{ring_id}",
        json={"gemstone_size_mm": 10.0, "band_thickness_mm": 4.2},
    )
    assert patch_response.status_code == 200

    second_export = client.get(f"/api/v1/exports/{ring_id}/stl")
    assert second_export.status_code == 200
    second_mesh = trimesh.load_mesh(stl_path, file_type="stl")
    second_volume = float(second_mesh.volume)
    second_mtime = stl_path.stat().st_mtime

    assert second_mtime >= first_mtime
    assert second_volume > first_volume
