from pathlib import Path

import trimesh

from app.domain.export import ExportFormat, ExportResponse
from app.services.component_library import AssemblyContext, open_component_library
from app.services.ring_service import ring_service


ARTIFACTS_ROOT = Path(__file__).resolve().parents[2] / "artifacts"


class ExportService:
    def get_export(self, ring_id: str, fmt: ExportFormat) -> ExportResponse | None:
        ring = ring_service.get_ring(ring_id)
        if not ring:
            return None

        artifact_path = ARTIFACTS_ROOT / ring_id / f"model.{fmt}"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)

        scene = self._build_scene(
            template_id=ring.parameters.template_id,
            style_tag=ring.parameters.style_tag,
            band_thickness_mm=ring.parameters.band_thickness_mm,
            gemstone_size_mm=ring.parameters.gemstone_size_mm,
            gemstone_type=ring.parameters.gemstone_type,
            center_stone_shape=ring.parameters.center_stone_shape,
            prong_count=ring.parameters.prong_count,
            band_profile=ring.parameters.band_profile,
            side_stone_count=ring.parameters.side_stone_count,
            setting_family=ring.parameters.setting_family,
            setting_variant=ring.parameters.setting_variant,
            setting_openheart=ring.parameters.setting_openheart,
            shank_family=ring.parameters.shank_family,
            shank_variant=ring.parameters.shank_variant,
            setting_height_mm=ring.parameters.setting_height_mm,
        )

        if fmt == "glb":
            payload = scene.export(file_type=fmt)
        else:
            merged_mesh = trimesh.util.concatenate([geometry.copy() for geometry in scene.geometry.values()])
            merged_mesh.merge_vertices()
            merged_mesh.remove_unreferenced_vertices()
            payload = merged_mesh.export(file_type=fmt)

        if isinstance(payload, str):
            artifact_path.write_text(payload, encoding="utf-8")
        else:
            artifact_path.write_bytes(payload)

        return ExportResponse(
            ring_id=ring_id,
            format=fmt,
            artifact_uri=f"/artifacts/{ring_id}/model.{fmt}",
        )

    @staticmethod
    def _build_scene(
        template_id: str,
        style_tag: str,
        band_thickness_mm: float,
        gemstone_size_mm: float,
        gemstone_type: str,
        center_stone_shape: str,
        prong_count: int,
        band_profile: str,
        side_stone_count: int,
        setting_family: str,
        setting_variant: int,
        setting_openheart: bool,
        shank_family: str,
        shank_variant: int,
        setting_height_mm: float,
    ) -> trimesh.Scene:
        context = AssemblyContext(
            template_id=template_id,
            style_tag=style_tag,
            band_profile=band_profile,
            band_thickness_mm=band_thickness_mm,
            gemstone_size_mm=gemstone_size_mm,
            gemstone_type=gemstone_type,
            center_stone_shape=center_stone_shape,
            prong_count=prong_count,
            side_stone_count=side_stone_count,
            setting_family=setting_family,
            setting_variant=setting_variant,
            setting_openheart=setting_openheart,
            shank_family=shank_family,
            shank_variant=shank_variant,
            setting_height_mm=setting_height_mm,
        )
        return open_component_library.assemble_ring_scene(context)


export_service = ExportService()
