from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Any

import trimesh


CATALOG_ROOT = Path(__file__).resolve().parents[2] / "assets" / "components"
DEFAULT_MANIFEST_PATH = CATALOG_ROOT / "manifest.json"


@dataclass(frozen=True)
class CatalogComponent:
    id: str
    category: str
    status: str
    source_type: str
    source_name: str
    license: str
    target_component_id: str | None = None
    source_url: str | None = None
    file: str | None = None
    tags: tuple[str, ...] = ()
    quality_score: float | None = None
    fit: dict[str, float] = field(default_factory=dict)


class ComponentCatalog:
    """Loads and validates curated component metadata for asset-backed ring assembly."""

    allowed_statuses = {"approved", "candidate", "disabled"}
    allowed_source_types = {"builtin", "file"}

    def __init__(self, manifest_path: Path | None = None) -> None:
        env_manifest = os.getenv("JEWELRYAI_COMPONENT_MANIFEST")
        self._manifest_path = Path(env_manifest) if env_manifest else (manifest_path or DEFAULT_MANIFEST_PATH)

        self._components_by_id: dict[str, CatalogComponent] = {}
        self._schema_version = 0
        self._catalog_name = ""

        self.reload()

    def reload(self) -> None:
        if not self._manifest_path.exists():
            self._components_by_id = {}
            self._schema_version = 0
            self._catalog_name = "missing"
            return

        payload = json.loads(self._manifest_path.read_text(encoding="utf-8"))
        components: dict[str, CatalogComponent] = {}
        for raw in payload.get("components", []):
            component = self._component_from_json(raw)
            components[component.id] = component

        self._components_by_id = components
        self._schema_version = int(payload.get("schema_version", 0))
        self._catalog_name = str(payload.get("catalog_name", "unnamed"))

    @property
    def manifest_path(self) -> Path:
        return self._manifest_path

    @property
    def schema_version(self) -> int:
        return self._schema_version

    @property
    def catalog_name(self) -> str:
        return self._catalog_name

    def _component_from_json(self, raw: dict[str, Any]) -> CatalogComponent:
        status = str(raw.get("status", "candidate"))
        source_type = str(raw.get("source_type", "file"))

        if status not in self.allowed_statuses:
            raise ValueError(f"Unsupported component status '{status}' for id={raw.get('id')}")
        if source_type not in self.allowed_source_types:
            raise ValueError(
                f"Unsupported source_type '{source_type}' for id={raw.get('id')}"
            )

        fit_raw = raw.get("fit") or {}
        fit: dict[str, float] = {}
        for key, value in fit_raw.items():
            fit[key] = float(value)

        return CatalogComponent(
            id=str(raw["id"]),
            category=str(raw.get("category", "unknown")),
            status=status,
            source_type=source_type,
            source_name=str(raw.get("source_name", "unknown")),
            license=str(raw.get("license", "unknown")),
            target_component_id=raw.get("target_component_id"),
            source_url=raw.get("source_url"),
            file=raw.get("file"),
            tags=tuple(str(t) for t in raw.get("tags", [])),
            quality_score=(float(raw["quality_score"]) if "quality_score" in raw else None),
            fit=fit,
        )

    def all_components(self) -> list[CatalogComponent]:
        return list(self._components_by_id.values())

    def get(self, component_id: str) -> CatalogComponent | None:
        return self._components_by_id.get(component_id)

    def select_override_for(self, target_component_id: str) -> CatalogComponent | None:
        """Return the highest-scoring approved file component that targets the given component id."""
        candidates = [
            c
            for c in self._components_by_id.values()
            if c.target_component_id == target_component_id and c.status == "approved" and c.source_type == "file"
        ]
        if not candidates:
            return None

        candidates.sort(key=lambda c: (c.quality_score or 0.0), reverse=True)
        return candidates[0]

    def load_component_mesh(self, component: CatalogComponent) -> trimesh.Trimesh | None:
        if component.source_type != "file" or not component.file:
            return None

        file_path = CATALOG_ROOT / component.file
        if not file_path.exists():
            return None

        mesh = trimesh.load_mesh(file_path, force="mesh")
        if isinstance(mesh, trimesh.Scene):
            scene_meshes = [
                geometry.copy()
                for geometry in mesh.geometry.values()
                if isinstance(geometry, trimesh.Trimesh)
            ]
            if not scene_meshes:
                return None
            mesh = trimesh.util.concatenate(scene_meshes)

        if not isinstance(mesh, trimesh.Trimesh):
            return None

        mesh = mesh.copy()
        mesh.merge_vertices()
        mesh.remove_unreferenced_vertices()
        return mesh

    def audit(self) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "manifest_path": str(self._manifest_path),
            "schema_version": self._schema_version,
            "catalog_name": self._catalog_name,
            "total_components": len(self._components_by_id),
            "status_counts": {},
            "source_type_counts": {},
            "missing_files": [],
            "license_tbd": 0,
        }

        for component in self._components_by_id.values():
            summary["status_counts"][component.status] = summary["status_counts"].get(component.status, 0) + 1
            summary["source_type_counts"][component.source_type] = (
                summary["source_type_counts"].get(component.source_type, 0) + 1
            )

            if component.license.upper() == "TBD":
                summary["license_tbd"] += 1

            if component.source_type == "file" and component.file:
                asset_path = CATALOG_ROOT / component.file
                if not asset_path.exists():
                    summary["missing_files"].append(component.file)

        return summary


component_catalog = ComponentCatalog()
