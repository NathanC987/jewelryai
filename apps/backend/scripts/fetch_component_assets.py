from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
from urllib.parse import urlparse
import urllib.request

import trimesh


BACKEND_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = BACKEND_ROOT / "assets" / "components" / "manifest.json"
ASSET_ROOT = BACKEND_ROOT / "assets" / "components"


def _suffix_to_file_type(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    if suffix in {"stl", "obj", "ply", "glb", "gltf"}:
        return suffix
    raise ValueError(f"Unsupported target extension: {path.suffix}")


def _source_type_from_url(url: str) -> str:
    raw_path = urlparse(url).path.lower()
    for ext in (".stl", ".obj", ".ply", ".glb", ".gltf"):
        if raw_path.endswith(ext):
            return ext.lstrip(".")
    raise ValueError(f"Unsupported source extension in url: {url}")


def _load_mesh_from_bytes(payload: bytes, file_type: str) -> trimesh.Trimesh:
    mesh = trimesh.load_mesh(file_obj=BytesIO(payload), file_type=file_type)
    if isinstance(mesh, trimesh.Scene):
        meshes = [m.copy() for m in mesh.geometry.values() if isinstance(m, trimesh.Trimesh)]
        if not meshes:
            raise ValueError("Downloaded scene contains no mesh geometry")
        mesh = trimesh.util.concatenate(meshes)

    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("Downloaded asset did not resolve to a mesh")

    mesh = mesh.copy()
    mesh.merge_vertices()
    mesh.remove_unreferenced_vertices()
    return mesh


def _download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "jewelryai-component-fetcher/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def main() -> None:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    components = payload.get("components", [])

    downloaded = 0
    skipped = 0
    failed = 0

    for component in components:
        if component.get("source_type") != "file":
            continue

        rel_file = component.get("file")
        download_url = component.get("download_url")
        if not rel_file or not download_url:
            skipped += 1
            continue

        target_path = ASSET_ROOT / rel_file
        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            raw = _download(download_url)
            source_type = _source_type_from_url(download_url)
            target_type = _suffix_to_file_type(target_path)

            if source_type == target_type:
                target_path.write_bytes(raw)
            else:
                mesh = _load_mesh_from_bytes(raw, source_type)
                exported = mesh.export(file_type=target_type)
                if isinstance(exported, str):
                    target_path.write_text(exported, encoding="utf-8")
                else:
                    target_path.write_bytes(exported)

            print(f"downloaded: {component['id']} -> {target_path}")
            downloaded += 1
        except Exception as exc:  # pragma: no cover - command-line utility path
            print(f"failed: {component.get('id')} ({exc})")
            failed += 1

    print("summary:")
    print(f"  downloaded={downloaded}")
    print(f"  skipped={skipped}")
    print(f"  failed={failed}")


if __name__ == "__main__":
    main()
