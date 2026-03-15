from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh


ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets" / "components"


def _write_mesh(mesh: trimesh.Trimesh, relative_path: str) -> None:
    target = ASSET_ROOT / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(mesh.export(file_type="glb"))


def _band_classic() -> trimesh.Trimesh:
    return trimesh.creation.annulus(r_min=8.0, r_max=10.0, height=2.6, sections=128)


def _band_tapered() -> trimesh.Trimesh:
    outer = trimesh.creation.annulus(r_min=8.4, r_max=10.0, height=2.5, sections=128)
    crown = trimesh.creation.annulus(r_min=9.2, r_max=9.8, height=0.45, sections=96)
    crown.apply_translation((0.0, 0.0, 0.7))
    return trimesh.util.concatenate([outer, crown])


def _setting_solitaire() -> trimesh.Trimesh:
    basket = trimesh.creation.cylinder(radius=1.65, height=2.6, sections=40)
    basket.apply_translation((0.0, 0.0, 1.3))

    rail = trimesh.creation.cylinder(radius=1.05, height=0.35, sections=36)
    rail.apply_translation((0.0, 0.0, 0.8))

    return trimesh.util.concatenate([basket, rail])


def _setting_royal_crown() -> trimesh.Trimesh:
    basket = trimesh.creation.cylinder(radius=1.85, height=3.1, sections=44)
    basket.apply_translation((0.0, 0.0, 1.55))

    crown_nodes: list[trimesh.Trimesh] = [basket]
    for i in range(6):
        angle = (2.0 * np.pi * i) / 6.0
        node = trimesh.creation.icosphere(subdivisions=2, radius=0.23)
        node.apply_translation((np.cos(angle) * 1.9, np.sin(angle) * 1.9, 2.85))
        crown_nodes.append(node)

    return trimesh.util.concatenate(crown_nodes)


def _style_cathedral_arms() -> trimesh.Trimesh:
    parts: list[trimesh.Trimesh] = []
    for direction in (-1.0, 1.0):
        base = np.array([direction * 9.0, 4.7, 0.4])
        tip = np.array([direction * 2.0, 8.4, 2.2])
        vec = tip - base
        length = float(np.linalg.norm(vec))
        arm = trimesh.creation.cylinder(radius=0.22, height=length, sections=30)
        transform = trimesh.geometry.align_vectors([0.0, 0.0, 1.0], vec / length)
        if transform is not None:
            arm.apply_transform(transform)
        arm.apply_translation(((base + tip) / 2.0).tolist())
        parts.append(arm)
    return trimesh.util.concatenate(parts)


def _accent_solitaire_shoulders() -> trimesh.Trimesh:
    parts: list[trimesh.Trimesh] = []
    for direction in (-1.0, 1.0):
        for idx in range(4):
            t = (idx + 1) / 5.0
            stone = trimesh.creation.icosphere(subdivisions=2, radius=0.28)
            stone.apply_translation((direction * (5.3 + t * 1.0), 7.4 - t * 2.8, 0.9 - t * 0.25))
            parts.append(stone)
    return trimesh.util.concatenate(parts)


def main() -> None:
    _write_mesh(_band_classic(), "bands/classic_band_v1.glb")
    _write_mesh(_band_tapered(), "bands/tapered_band_v1.glb")
    _write_mesh(_setting_solitaire(), "settings/solitaire_head_v1.glb")
    _write_mesh(_setting_royal_crown(), "settings/royal_crown_head_v1.glb")
    _write_mesh(_style_cathedral_arms(), "styles/cathedral_arms_v1.glb")
    _write_mesh(_accent_solitaire_shoulders(), "accents/solitaire_shoulders_v1.glb")

    print("Wrote demo component assets under:")
    print(ASSET_ROOT)


if __name__ == "__main__":
    main()
