from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
import re

import trimesh

from app.domain.ring import RingParameters


logger = logging.getLogger("service.component_visual_index")


@dataclass(frozen=True)
class ComponentVisualDescriptor:
    component_type: str  # shank | setting
    component_id: str
    family: str
    variant: int
    shape: str | None
    prong_count_hint: int | None
    source_path: str
    width: float
    height: float
    depth: float


class ComponentVisualIndex:
    """Searchable local index of component descriptors for vision retrieval.

    This is intentionally lightweight and offline-first. It gives the resolver
    a component-aware lookup table tied to actual files in /components and can
    be upgraded later with learned embeddings.
    """

    def __init__(self, descriptors: list[ComponentVisualDescriptor]) -> None:
        self._descriptors = descriptors
        self._shanks = [d for d in descriptors if d.component_type == "shank"]
        self._settings = [d for d in descriptors if d.component_type == "setting"]
        logger.info(
            {
                "operation": "component_visual_index_init",
                "descriptor_count": len(self._descriptors),
                "shank_count": len(self._shanks),
                "setting_count": len(self._settings),
            }
        )

    @property
    def descriptors(self) -> list[ComponentVisualDescriptor]:
        return self._descriptors

    @classmethod
    def from_components_root(cls, components_root: Path) -> "ComponentVisualIndex":
        logger.info(
            {
                "operation": "component_visual_index_scan_start",
                "components_root": str(components_root),
            }
        )
        descriptors: list[ComponentVisualDescriptor] = []

        descriptors.extend(_scan_shanks(components_root / "classic_shanks", "classic"))
        descriptors.extend(_scan_shanks(components_root / "cathedral_shanks", "cathedral"))
        descriptors.extend(_scan_shanks(components_root / "advanced_shanks", "advanced"))

        descriptors.extend(_scan_settings(components_root / "baskets", "basket"))
        descriptors.extend(_scan_settings(components_root / "pegheads", "peghead"))
        descriptors.extend(_scan_settings(components_root / "bezels", "bezel"))
        descriptors.extend(_scan_settings(components_root / "halos", "halo"))
        descriptors.extend(_scan_settings(components_root / "clusters", "cluster"))

        logger.info(
            {
                "operation": "component_visual_index_scan_complete",
                "components_root": str(components_root),
                "descriptor_count": len(descriptors),
            }
        )
        return cls(descriptors)

    @classmethod
    def load_or_build(
        cls,
        components_root: Path,
        cache_path: Path | None = None,
        auto_build: bool = True,
    ) -> "ComponentVisualIndex":
        cache_file = cache_path or (components_root / ".component_visual_index.json")
        if cache_file.exists():
            payload = json.loads(cache_file.read_text(encoding="utf-8"))
            descriptors = [ComponentVisualDescriptor(**item) for item in payload.get("descriptors", [])]
            if descriptors:
                logger.info(
                    {
                        "operation": "component_visual_index_load_cache",
                        "cache_file": str(cache_file),
                        "descriptor_count": len(descriptors),
                    }
                )
                return cls(descriptors)
            logger.warning(
                {
                    "operation": "component_visual_index_load_cache",
                    "cache_file": str(cache_file),
                    "descriptor_count": 0,
                    "reason": "empty_cache_payload",
                }
            )

        if not auto_build:
            logger.warning(
                {
                    "operation": "component_visual_index_autobuild_disabled",
                    "components_root": str(components_root),
                    "cache_file": str(cache_file),
                }
            )
            return cls([])

        built = cls.from_components_root(components_root)
        cache_file.write_text(
            json.dumps(
                {
                    "descriptors": [asdict(item) for item in built.descriptors],
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        logger.info(
            {
                "operation": "component_visual_index_write_cache",
                "cache_file": str(cache_file),
                "descriptor_count": len(built.descriptors),
            }
        )
        return built

    def best_shank(self, parameters: RingParameters) -> tuple[ComponentVisualDescriptor, float] | None:
        if not self._shanks:
            logger.warning(
                {
                    "operation": "component_visual_index_best_shank",
                    "result": "none",
                    "reason": "no_shank_descriptors",
                }
            )
            return None

        ranked = sorted(
            ((item, _score_shank(item, parameters)) for item in self._shanks),
            key=lambda pair: pair[1],
            reverse=True,
        )
        return ranked[0]

    def best_setting(self, parameters: RingParameters) -> tuple[ComponentVisualDescriptor, float] | None:
        if not self._settings:
            logger.warning(
                {
                    "operation": "component_visual_index_best_setting",
                    "result": "none",
                    "reason": "no_setting_descriptors",
                }
            )
            return None

        ranked = sorted(
            ((item, _score_setting(item, parameters)) for item in self._settings),
            key=lambda pair: pair[1],
            reverse=True,
        )
        return ranked[0]


def _mesh_dimensions(path: Path) -> tuple[float, float, float] | None:
    try:
        loaded = trimesh.load(path)
    except Exception:
        return None

    if isinstance(loaded, trimesh.Scene):
        meshes = [geometry for geometry in loaded.geometry.values() if isinstance(geometry, trimesh.Trimesh)]
        if not meshes:
            return None
        merged = trimesh.util.concatenate([mesh.copy() for mesh in meshes])
    elif isinstance(loaded, trimesh.Trimesh):
        merged = loaded.copy()
    else:
        return None

    bounds = merged.bounds
    extents = bounds[1] - bounds[0]
    return float(extents[0]), float(extents[1]), float(extents[2])


def _scan_shanks(folder: Path, family: str) -> list[ComponentVisualDescriptor]:
    if not folder.exists():
        return []

    descriptors: list[ComponentVisualDescriptor] = []
    pattern = re.compile(rf"^{family}_(\d+)$")
    for file_path in sorted(folder.glob("*.glb")):
        stem = file_path.stem
        match = pattern.match(stem)
        if not match:
            continue
        dims = _mesh_dimensions(file_path)
        if not dims:
            continue
        variant = int(match.group(1))
        descriptors.append(
            ComponentVisualDescriptor(
                component_type="shank",
                component_id=stem,
                family=family,
                variant=variant,
                shape=None,
                prong_count_hint=None,
                source_path=str(file_path),
                width=dims[0],
                height=dims[1],
                depth=dims[2],
            )
        )
    return descriptors


def _scan_settings(folder: Path, family: str) -> list[ComponentVisualDescriptor]:
    if not folder.exists():
        return []

    descriptors: list[ComponentVisualDescriptor] = []
    pattern = re.compile(rf"^{family}_(\d+)_([a-z_]+)$")
    for file_path in sorted(folder.glob("*.glb")):
        stem = file_path.stem
        match = pattern.match(stem)
        if not match:
            if family == "bezel":
                shape = _extract_bezel_shape(stem)
                if shape is None:
                    continue
                variant = 1
                prong_hint = None
            else:
                continue
        else:
            variant = int(match.group(1))
            shape = match.group(2)
            prong_hint = variant if family in {"peghead", "basket"} and variant in {3, 4, 6} else None

        dims = _mesh_dimensions(file_path)
        if not dims:
            continue

        descriptors.append(
            ComponentVisualDescriptor(
                component_type="setting",
                component_id=stem,
                family=family,
                variant=variant,
                shape=shape,
                prong_count_hint=prong_hint,
                source_path=str(file_path),
                width=dims[0],
                height=dims[1],
                depth=dims[2],
            )
        )
    return descriptors


def _extract_bezel_shape(stem: str) -> str | None:
    # Examples: bezel_round, bezel_round_openheart, bezel_cushion_openheart
    if not stem.startswith("bezel_"):
        return None
    remainder = stem.removeprefix("bezel_")
    return remainder.removesuffix("_openheart")


def _score_shank(item: ComponentVisualDescriptor, parameters: RingParameters) -> float:
    family_score = 0.55 if item.family == parameters.shank_family else 0.0
    variant_distance = abs(item.variant - parameters.shank_variant)
    variant_score = max(0.0, 0.35 - min(0.35, variant_distance * 0.05))
    return family_score + variant_score


def _score_setting(item: ComponentVisualDescriptor, parameters: RingParameters) -> float:
    family_score = 0.48 if item.family == parameters.setting_family else 0.0
    variant_distance = abs(item.variant - parameters.setting_variant)
    variant_score = max(0.0, 0.28 - min(0.28, variant_distance * 0.04))

    shape_score = 0.0
    if item.shape:
        normalized_shape = "cushion" if parameters.center_stone_shape == "emerald_cut" else parameters.center_stone_shape
        if item.shape == normalized_shape:
            shape_score = 0.2

    prong_score = 0.0
    if item.prong_count_hint is not None and abs(item.prong_count_hint - parameters.prong_count) <= 1:
        prong_score = 0.1

    return family_score + variant_score + shape_score + prong_score