from dataclasses import dataclass
from pathlib import Path

import numpy as np
import trimesh

@dataclass(frozen=True)
class AssemblyContext:
    template_id: str
    style_tag: str
    band_profile: str
    band_thickness_mm: float
    gemstone_size_mm: float
    gemstone_type: str
    center_stone_shape: str
    prong_count: int
    side_stone_count: int
    setting_family: str
    setting_variant: int
    setting_openheart: bool
    shank_family: str
    shank_variant: int
    setting_height_mm: float


class OpenComponentLibrary:
    """Internal/open reusable component catalog for ring assembly."""

    band_components = {
        "classic": "band.classic",
        "flat": "band.flat",
        "knife_edge": "band.knife_edge",
        "tapered": "band.tapered",
    }

    setting_components = {
        "solitaire_ring": "setting.solitaire",
        "halo_ring": "setting.halo",
        "pave_band_ring": "setting.pave",
        "split_shank_ring": "setting.split_shank",
        "three_stone_ring": "setting.three_stone",
    }

    accent_components = {
        "solitaire_ring": "accent.solitaire_shoulders",
        "halo_ring": "accent.halo_cluster",
        "pave_band_ring": "accent.pave_arc",
        "three_stone_ring": "accent.shoulder_pair",
    }

    style_components = {
        "modern": "style.streamlined_gallery",
        "vintage": "style.milgrain_bezel",
        "royal": "style.cathedral_arms",
        "minimalist": "style.clean_gallery",
    }

    local_components_root = Path(__file__).resolve().parents[4] / "components"

    def selected_components(self, context: AssemblyContext) -> list[str]:
        return self._resolve_component_ids(context)

    def assemble_ring(self, context: AssemblyContext) -> trimesh.Trimesh:
        scene = self.assemble_ring_scene(context)
        meshes = [geometry.copy() for geometry in scene.geometry.values()]
        mesh = trimesh.util.concatenate(meshes)
        mesh.merge_vertices()
        mesh.remove_unreferenced_vertices()
        return mesh

    def assemble_ring_scene(self, context: AssemblyContext) -> trimesh.Scene:
        component_ids = self._resolve_component_ids(context)

        scene = trimesh.Scene()
        meshes: list[trimesh.Trimesh] = []
        shank_mount_plane_y: float | None = None
        shank_top_z: float | None = None
        for component_id in component_ids:
            local_meshes = self._load_local_component_meshes(
                component_id,
                context,
                shank_mount_plane_y=shank_mount_plane_y,
                shank_top_z=shank_top_z,
            )
            if local_meshes:
                if component_id.startswith("band."):
                    shank_reference = trimesh.util.concatenate([mesh.copy() for mesh in local_meshes])
                    shank_bounds = shank_reference.bounds
                    shank_mount_plane_y = float(shank_bounds[1][1]) - context.band_thickness_mm * 0.16
                    shank_top_z = float(shank_bounds[1][2])

                for index, local_mesh in enumerate(local_meshes):
                    source_name = str(local_mesh.metadata.get("source_name", f"part_{index}"))
                    scene.add_geometry(
                        local_mesh,
                        node_name=f"{component_id}.{source_name}.{index}",
                        geom_name=f"{component_id}.{source_name}.{index}",
                    )
                meshes.extend(local_meshes)

        if not meshes:
            raise ValueError(
                "No local component meshes could be loaded from the repository components library"
            )
        return scene

    def _load_local_component_meshes(
        self,
        component_id: str,
        context: AssemblyContext,
        shank_mount_plane_y: float | None = None,
        shank_top_z: float | None = None,
    ) -> list[trimesh.Trimesh]:
        if not self.local_components_root.exists():
            return []

        if component_id.startswith("band."):
            shank_path = self._choose_shank_path(context)
            if not shank_path:
                return []
            meshes = self._load_mesh_file_parts(shank_path)
            if not meshes:
                return []
            return self._fit_local_shank_meshes(meshes, context)

        if component_id.startswith("setting."):
            setting_path = self._choose_setting_path(context)
            if not setting_path:
                return []
            meshes = self._load_mesh_file_parts(setting_path)
            if not meshes:
                return []
            return self._fit_local_setting_meshes(
                meshes,
                context,
                shank_mount_plane_y=shank_mount_plane_y,
                shank_top_z=shank_top_z,
            )

        return []

    def _load_mesh_file_parts(self, mesh_path: Path) -> list[trimesh.Trimesh]:
        if not mesh_path.exists():
            return []

        loaded = trimesh.load(mesh_path)
        if isinstance(loaded, trimesh.Scene):
            scene_meshes: list[trimesh.Trimesh] = []
            for dumped in loaded.dump(concatenate=False):
                if not isinstance(dumped, trimesh.Trimesh):
                    continue

                part = dumped.copy()
                source_name = str(part.metadata.get("name", "part"))
                part.metadata = {**part.metadata, "source_name": source_name}
                part.merge_vertices()
                part.remove_unreferenced_vertices()
                scene_meshes.append(part)
            return scene_meshes

        if not isinstance(loaded, trimesh.Trimesh):
            return []

        mesh = loaded.copy()
        mesh.merge_vertices()
        mesh.remove_unreferenced_vertices()
        return [mesh]

    def _shape_key(self, shape: str) -> str:
        shape_map = {
            "round": "round",
            "oval": "oval",
            "princess": "princess",
            "emerald_cut": "cushion",
            "marquise": "marquise",
            "pear": "oval",
        }
        return shape_map.get(shape, "round")

    def _choose_existing_file(self, candidates: list[Path]) -> Path | None:
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _choose_shank_path(self, context: AssemblyContext) -> Path | None:
        family = context.shank_family
        variant = max(1, min(20, context.shank_variant))

        if family == "advanced":
            root = self.local_components_root / "advanced_shanks"
            preferred = [root / f"advanced_{variant:02d}.glb"]
            fallback = sorted(root.glob("advanced_*.glb"))
            return self._choose_existing_file(preferred + fallback)

        if family == "cathedral":
            root = self.local_components_root / "cathedral_shanks"
            preferred = [root / f"cathedral_{variant:02d}.glb"]
            fallback = sorted(root.glob("cathedral_*.glb"))
            return self._choose_existing_file(preferred + fallback)

        root = self.local_components_root / "classic_shanks"
        preferred = [root / f"classic_{variant:02d}.glb"]
        fallback = sorted(root.glob("classic_*.glb"))
        return self._choose_existing_file(preferred + fallback)

    def _choose_setting_path(self, context: AssemblyContext) -> Path | None:
        shape = self._shape_key(context.center_stone_shape)
        family = context.setting_family

        if family == "bezel":
            root = self.local_components_root / "bezels"
            suffix = "_openheart" if context.setting_openheart else ""
            preferred = [root / f"bezel_{shape}{suffix}.glb"]
            fallback = sorted(root.glob(f"bezel_{shape}*.glb")) + sorted(root.glob("bezel_*.glb"))
            return self._choose_existing_file(preferred + fallback)

        if family == "halo":
            root = self.local_components_root / "halos"
            variant = max(1, min(99, context.setting_variant))
            preferred = [root / f"halo_{variant:02d}_{shape}.glb"]
            fallback = sorted(root.glob(f"halo_*_{shape}.glb")) + sorted(root.glob("halo_*.glb"))
            return self._choose_existing_file(preferred + fallback)

        if family == "cluster":
            root = self.local_components_root / "clusters"
            variant = max(1, min(99, context.setting_variant))
            preferred = [root / f"cluster_{variant:02d}_{shape}.glb"]
            fallback = sorted(root.glob(f"cluster_*_{shape}.glb")) + sorted(root.glob("cluster_*.glb"))
            return self._choose_existing_file(preferred + fallback)

        if family == "basket":
            root = self.local_components_root / "baskets"
            count = min((3, 4, 6), key=lambda c: abs(c - context.prong_count))
            preferred = [root / f"basket_{count:02d}_{shape}.glb"]
            fallback = sorted(root.glob(f"basket_*_{shape}.glb")) + sorted(root.glob("basket_*.glb"))
            return self._choose_existing_file(preferred + fallback)

        root = self.local_components_root / "pegheads"
        count = min((4, 6), key=lambda c: abs(c - context.prong_count))
        preferred = [root / f"peghead_{count:02d}_{shape}.glb"]
        fallback = sorted(root.glob(f"peghead_*_{shape}.glb")) + sorted(root.glob("peghead_*.glb"))
        return self._choose_existing_file(preferred + fallback)

    def _fit_local_shank_meshes(self, meshes: list[trimesh.Trimesh], context: AssemblyContext) -> list[trimesh.Trimesh]:
        reference = trimesh.util.concatenate([mesh.copy() for mesh in meshes])
        bounds = reference.bounds
        extents = bounds[1] - bounds[0]

        outer_radius, _, band_height = self._compute_ring_base(context)
        target_width = outer_radius * 2.0
        current_width = max(float(extents[0]), float(extents[1]), 1e-6)
        current_height = max(float(extents[2]), 1e-6)

        scale_xy = target_width / current_width
        scale_z = max(0.6, band_height / current_height)
        transform = np.eye(4)
        transform[:3, :3] = np.diag([scale_xy, scale_xy, scale_z])

        center = reference.bounding_box.centroid * np.array([scale_xy, scale_xy, scale_z])
        transform[:3, 3] = -center

        fitted_meshes: list[trimesh.Trimesh] = []
        for mesh in meshes:
            fitted = mesh.copy()
            fitted.apply_transform(transform)
            fitted.merge_vertices()
            fitted.remove_unreferenced_vertices()
            fitted_meshes.append(fitted)
        return fitted_meshes

    def _fit_local_setting_meshes(
        self,
        meshes: list[trimesh.Trimesh],
        context: AssemblyContext,
        shank_mount_plane_y: float | None = None,
        shank_top_z: float | None = None,
    ) -> list[trimesh.Trimesh]:
        reference = trimesh.util.concatenate([mesh.copy() for mesh in meshes])
        bounds = reference.bounds
        extents = bounds[1] - bounds[0]

        outer_radius, band_height, stone_radius, setting_center_y, _ = self._setting_frame(context)
        width = max(float(extents[0]), float(extents[1]), 1e-6)
        height = max(float(extents[2]), 1e-6)

        family_width_factor = {
            "peghead": 1.7,
            "basket": 1.85,
            "bezel": 1.95,
            "halo": 2.6,
            "cluster": 2.85,
        }.get(context.setting_family, 1.8)
        target_width = max(
            1.2,
            stone_radius * family_width_factor,
            context.band_thickness_mm * 2.25,
            outer_radius * 0.32,
        )
        target_height = max(0.8, context.setting_height_mm * 1.8)

        scale_xy = target_width / width
        scale_z = target_height / height
        scaled_reference = reference.copy()
        scaled_reference.apply_scale((scale_xy, scale_xy, scale_z))
        center = scaled_reference.bounding_box.centroid
        scaled_reference.apply_translation((-center[0], -center[1], -center[2]))

        # Snap setting base to shank top and align to ring top centerline.
        aligned_bounds = scaled_reference.bounds
        min_z = float(aligned_bounds[0][2])
        min_y = float(aligned_bounds[0][1])
        max_abs_x = max(abs(float(aligned_bounds[0][0])), abs(float(aligned_bounds[1][0])), 1e-6)

        target_base_z = (
            shank_top_z + context.band_thickness_mm * 0.04
            if shank_top_z is not None
            else band_height * 0.56
        )
        delta_z = target_base_z - min_z

        # Anchor the rear of the setting slightly behind the shank top arc.
        mount_plane_y = (
            shank_mount_plane_y - context.band_thickness_mm * 0.32
            if shank_mount_plane_y is not None
            else setting_center_y - context.band_thickness_mm * 0.62
        )
        delta_y = mount_plane_y - min_y

        transform = np.eye(4)
        transform[:3, :3] = np.diag([scale_xy, scale_xy, scale_z])
        transform[:3, 3] = np.array([-center[0], -center[1] + delta_y, -center[2] + delta_z])

        x_center = float(scaled_reference.bounding_box.centroid[0])
        if abs(x_center) > max_abs_x * 0.05:
            transform[0, 3] -= x_center

        fitted_meshes: list[trimesh.Trimesh] = []
        for mesh in meshes:
            fitted = mesh.copy()
            fitted.apply_transform(transform)
            fitted.merge_vertices()
            fitted.remove_unreferenced_vertices()
            fitted_meshes.append(fitted)

        return fitted_meshes

    def _normalize_local_shank_orientation(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        # Source GLBs are authored in the expected orientation.
        # Do not auto-remap axes, as this can rotate shanks incorrectly.
        return mesh.copy()

    def _normalize_local_setting_orientation(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        # Source GLBs are authored in the expected orientation.
        # Do not auto-remap axes, as this can rotate settings incorrectly.
        return mesh.copy()

    def _resolve_component_ids(self, context: AssemblyContext) -> list[str]:
        band_component = self.band_components.get(context.band_profile, "band.classic")
        setting_component = self.setting_components.get(context.template_id, "setting.solitaire")
        accent_component = self.accent_components.get(context.template_id)
        style_component = self.style_components.get(context.style_tag, "style.streamlined_gallery")

        # Keep recipe IDs stable for interpretation payloads.
        if context.style_tag == "royal" and setting_component in {"setting.solitaire", "setting.halo"}:
            setting_component = "setting.royal_crown"

        parts = [band_component, setting_component, style_component]
        parts.append(f"setting_family.{context.setting_family}")
        parts.append(f"shank_family.{context.shank_family}")
        if accent_component:
            parts.append(accent_component)
        return parts

    def _compute_ring_base(self, context: AssemblyContext) -> tuple[float, float, float]:
        stone_radius = max(context.gemstone_size_mm / 2.0, 0.5)
        outer_radius = 8.5 + stone_radius * 0.6

        if context.template_id == "split_shank_ring":
            outer_radius += 0.5
        elif context.template_id == "three_stone_ring":
            outer_radius += 0.35

        if context.style_tag == "minimalist":
            outer_radius -= 0.15
        elif context.style_tag == "royal":
            outer_radius += 0.2

        thickness_scale = 1.0 if context.band_profile != "tapered" else 0.78
        inner_radius = max(outer_radius - context.band_thickness_mm * thickness_scale, 1.0)

        band_height = 1.8 + context.band_thickness_mm * 0.45
        if context.band_profile == "flat":
            band_height *= 0.75
        elif context.band_profile == "knife_edge":
            band_height *= 0.9

        if context.style_tag == "minimalist":
            band_height *= 0.86
        elif context.style_tag == "royal":
            band_height *= 1.1

        if context.template_id == "halo_ring":
            band_height *= 0.95

        return outer_radius, inner_radius, band_height

    def _setting_frame(self, context: AssemblyContext) -> tuple[float, float, float, float, float]:
        outer_radius, _, band_height = self._compute_ring_base(context)
        stone_radius = max(context.gemstone_size_mm / 2.0, 0.5)
        setting_center_y = outer_radius - context.band_thickness_mm * 0.28
        setting_base_z = band_height * 0.5
        stone_center_z = setting_base_z + context.setting_height_mm + stone_radius * 0.62
        return outer_radius, band_height, stone_radius, setting_center_y, stone_center_z

    def _build_band_component(self, component_id: str, context: AssemblyContext) -> list[trimesh.Trimesh]:
        outer_radius, inner_radius, band_height = self._compute_ring_base(context)

        band = trimesh.creation.annulus(
            r_min=inner_radius,
            r_max=outer_radius,
            height=band_height,
            sections=128,
        )
        parts: list[trimesh.Trimesh] = [band]

        # Add a comfort inner sleeve and top crown for a richer silhouette on close inspection.
        comfort_inner = trimesh.creation.annulus(
            r_min=inner_radius + context.band_thickness_mm * 0.06,
            r_max=inner_radius + context.band_thickness_mm * 0.2,
            height=band_height * 0.62,
            sections=84,
        )
        comfort_inner.apply_translation((0.0, 0.0, -band_height * 0.08))
        parts.append(comfort_inner)

        crown = trimesh.creation.annulus(
            r_min=outer_radius - context.band_thickness_mm * 0.32,
            r_max=outer_radius - context.band_thickness_mm * 0.06,
            height=max(0.18, band_height * 0.26),
            sections=84,
        )
        crown.apply_translation((0.0, 0.0, band_height * 0.35))
        parts.append(crown)

        if component_id == "band.knife_edge":
            ridge = trimesh.creation.annulus(
                r_min=inner_radius + context.band_thickness_mm * 0.2,
                r_max=outer_radius - context.band_thickness_mm * 0.18,
                height=band_height * 0.32,
                sections=96,
            )
            ridge.apply_translation((0.0, 0.0, band_height * 0.32))
            parts.append(ridge)

        if context.template_id == "split_shank_ring":
            split_ridge = trimesh.creation.annulus(
                r_min=inner_radius + context.band_thickness_mm * 0.16,
                r_max=outer_radius - context.band_thickness_mm * 0.12,
                height=band_height * 0.22,
                sections=96,
            )
            split_ridge.apply_translation((0.0, 0.0, -band_height * 0.2))
            parts.append(split_ridge)

        return parts

    def _build_setting_component(self, component_id: str, context: AssemblyContext) -> list[trimesh.Trimesh]:
        outer_radius, band_height, stone_radius, setting_center_y, _ = self._setting_frame(context)
        setting_base_z = band_height * 0.5

        basket_radius = max(stone_radius * 0.58, 0.4)
        if component_id == "setting.halo":
            basket_radius *= 1.06
        elif component_id == "setting.split_shank":
            basket_radius *= 1.04
        elif component_id == "setting.royal_crown":
            basket_radius *= 1.12

        basket_height = context.setting_height_mm
        if component_id == "setting.royal_crown":
            basket_height = min(5.0, basket_height + 0.5)

        basket = trimesh.creation.cylinder(radius=basket_radius, height=basket_height, sections=36)
        basket.apply_translation((0.0, setting_center_y, setting_base_z + basket_height / 2.0))

        gallery_bridge = trimesh.creation.cylinder(
            radius=max(0.18, basket_radius * 0.62),
            height=max(0.2, basket_height * 0.18),
            sections=30,
        )
        gallery_bridge.apply_translation((0.0, setting_center_y, setting_base_z + basket_height * 0.26))

        center_stone = _build_center_stone(shape=context.center_stone_shape, radius=stone_radius)
        _apply_gemstone_material_shape_hint(center_stone, context.gemstone_type)

        stone_center = np.array(
            [
                0.0,
                setting_center_y,
                setting_base_z + basket_height + stone_radius * 0.62,
            ]
        )
        center_stone.apply_translation(tuple(stone_center))

        prongs = _build_prongs(
            prong_count=context.prong_count,
            band_thickness_mm=context.band_thickness_mm,
            basket_radius=basket_radius,
            stone_radius=stone_radius,
            setting_center_y=setting_center_y,
            setting_base_z=setting_base_z,
            setting_height_mm=basket_height,
            stone_center=stone_center,
        )

        return [basket, gallery_bridge, center_stone, *prongs]

    def _build_accent_component(self, component_id: str, context: AssemblyContext) -> list[trimesh.Trimesh]:
        outer_radius, band_height, stone_radius, setting_center_y, stone_center_z = self._setting_frame(context)

        if component_id == "accent.halo_cluster":
            count = max(10, context.side_stone_count or 12)
            halo_radius = max(stone_radius * 0.2, 0.22)
            parts: list[trimesh.Trimesh] = []
            for idx in range(count):
                angle = (2.0 * np.pi * idx) / count
                halo_stone = trimesh.creation.icosphere(subdivisions=2, radius=halo_radius)
                halo_stone.apply_translation(
                    (
                        np.cos(angle) * (stone_radius * 1.38),
                        setting_center_y + np.sin(angle) * (stone_radius * 1.38),
                        stone_center_z - stone_radius * 0.08,
                    )
                )
                parts.append(halo_stone)
            return parts

        if component_id == "accent.shoulder_pair":
            parts = []
            for direction in (-1.0, 1.0):
                side = _build_center_stone(shape=context.center_stone_shape, radius=stone_radius * 0.58)
                side.apply_translation(
                    (
                        direction * stone_radius * 1.62,
                        setting_center_y,
                        stone_center_z - stone_radius * 0.12,
                    )
                )
                parts.append(side)
            return parts

        if component_id == "accent.solitaire_shoulders":
            count = max(0, min(12, context.side_stone_count))
            if count == 0:
                return []

            shoulder_radius = max(0.1, stone_radius * 0.16)
            spread = stone_radius * 1.85
            parts = []
            for direction in (-1.0, 1.0):
                for idx in range(count):
                    t = (idx + 1) / (count + 1)
                    y = setting_center_y - stone_radius * 0.25 - t * stone_radius * 1.2
                    x = direction * (spread + t * stone_radius * 0.35)
                    z = band_height * (0.5 - t * 0.18)
                    shoulder = trimesh.creation.icosphere(subdivisions=2, radius=shoulder_radius)
                    shoulder.apply_translation((x, y, z))
                    parts.append(shoulder)
            return parts

        # accent.pave_arc
        count = max(0, context.side_stone_count)
        if count == 0:
            return []

        stone_radius_small = max(0.15, stone_radius * 0.22)
        arc_start = np.pi * 0.08
        arc_end = np.pi - np.pi * 0.08
        parts = []
        for idx in range(count):
            ratio = (idx + 0.5) / count
            angle = arc_start + (arc_end - arc_start) * ratio
            side = trimesh.creation.icosphere(subdivisions=2, radius=stone_radius_small)
            side.apply_translation(
                (
                    np.cos(angle) * (outer_radius + stone_radius_small * 0.45),
                    np.sin(angle) * (outer_radius + stone_radius_small * 0.45),
                    band_height * 0.42,
                )
            )
            parts.append(side)
        return parts

    def _build_style_component(self, component_id: str, context: AssemblyContext) -> list[trimesh.Trimesh]:
        outer_radius, band_height, stone_radius, setting_center_y, stone_center_z = self._setting_frame(context)
        setting_base_z = band_height * 0.5

        if component_id == "style.cathedral_arms":
            arm_radius = max(0.11, context.band_thickness_mm * 0.09)
            parts: list[trimesh.Trimesh] = []
            for direction in (-1.0, 1.0):
                base = np.array(
                    [
                        direction * (outer_radius - context.band_thickness_mm * 0.7),
                        outer_radius * 0.48,
                        band_height * 0.12,
                    ]
                )
                tip = np.array(
                    [
                        direction * stone_radius * 0.82,
                        setting_center_y - stone_radius * 0.52,
                        setting_base_z + context.setting_height_mm * 0.58,
                    ]
                )
                vec = tip - base
                length = float(np.linalg.norm(vec))
                if length <= 1e-6:
                    continue
                arm = trimesh.creation.cylinder(radius=arm_radius, height=length, sections=24)
                transform = trimesh.geometry.align_vectors([0.0, 0.0, 1.0], vec / length)
                if transform is not None:
                    arm.apply_transform(transform)
                arm.apply_translation(((base + tip) / 2.0).tolist())
                parts.append(arm)
            return parts

        if component_id == "style.milgrain_bezel":
            bead_radius = max(0.08, stone_radius * 0.09)
            bead_count = 28
            parts: list[trimesh.Trimesh] = []
            for idx in range(bead_count):
                angle = (2.0 * np.pi * idx) / bead_count
                bead = trimesh.creation.icosphere(subdivisions=2, radius=bead_radius)
                bead.apply_translation(
                    (
                        np.cos(angle) * (stone_radius * 1.08),
                        setting_center_y + np.sin(angle) * (stone_radius * 1.08),
                        stone_center_z - stone_radius * 0.02,
                    )
                )
                parts.append(bead)
            return parts

        if component_id == "style.clean_gallery":
            rail = trimesh.creation.cylinder(radius=max(stone_radius * 0.52, 0.35), height=max(0.18, context.setting_height_mm * 0.18), sections=18)
            rail.apply_translation((0.0, setting_center_y, setting_base_z + context.setting_height_mm * 0.2))
            return [rail]

        # style.streamlined_gallery
        rail = trimesh.creation.cylinder(radius=max(stone_radius * 0.56, 0.38), height=max(0.2, context.setting_height_mm * 0.2), sections=20)
        rail.apply_translation((0.0, setting_center_y, setting_base_z + context.setting_height_mm * 0.26))
        return [rail]


def _build_prongs(
    prong_count: int,
    band_thickness_mm: float,
    basket_radius: float,
    stone_radius: float,
    setting_center_y: float,
    setting_base_z: float,
    setting_height_mm: float,
    stone_center: np.ndarray,
) -> list[trimesh.Trimesh]:
    prong_radius = max(0.11, band_thickness_mm * 0.1)
    prongs: list[trimesh.Trimesh] = []

    for i in range(prong_count):
        angle = (2.0 * np.pi * i) / prong_count
        base_point = np.array(
            [
                np.cos(angle) * basket_radius * 1.02,
                setting_center_y + np.sin(angle) * basket_radius * 0.8,
                setting_base_z + setting_height_mm * 0.18,
            ]
        )
        tip_point = np.array(
            [
                np.cos(angle) * stone_radius * 0.42,
                setting_center_y + np.sin(angle) * stone_radius * 0.28,
                stone_center[2] + stone_radius * 0.4,
            ]
        )
        prong_vector = tip_point - base_point
        prong_height = float(np.linalg.norm(prong_vector))
        if prong_height <= 1e-6:
            continue

        prong = trimesh.creation.cylinder(radius=prong_radius, height=prong_height, sections=24)
        prong_direction = prong_vector / prong_height
        transform = trimesh.geometry.align_vectors([0.0, 0.0, 1.0], prong_direction)
        if transform is not None:
            prong.apply_transform(transform)
        prong.apply_translation(((base_point + tip_point) / 2.0).tolist())
        prongs.append(prong)

        # Add claw-style tip to improve visual realism and stone grip cues.
        tip = trimesh.creation.cone(
            radius=prong_radius * 0.75,
            height=max(0.12, stone_radius * 0.14),
            sections=20,
        )
        tip_transform = trimesh.geometry.align_vectors([0.0, 0.0, 1.0], prong_direction)
        if tip_transform is not None:
            tip.apply_transform(tip_transform)
        tip.apply_translation((tip_point + prong_direction * max(0.03, stone_radius * 0.04)).tolist())
        prongs.append(tip)

    return prongs


def _axis_remap_transform(order: tuple[int, int, int]) -> np.ndarray:
    transform = np.eye(4)
    transform[:3, :3] = 0.0
    for target_axis, source_axis in enumerate(order):
        transform[target_axis, source_axis] = 1.0
    return transform


def _apply_gemstone_material_shape_hint(stone: trimesh.Trimesh, gemstone_type: str) -> None:
    if gemstone_type == "emerald":
        stone.apply_scale((1.12, 0.92, 0.92))
    elif gemstone_type == "sapphire":
        stone.apply_scale((1.0, 1.06, 0.98))
    elif gemstone_type == "ruby":
        stone.apply_scale((1.04, 1.0, 0.95))


def _build_center_stone(shape: str, radius: float) -> trimesh.Trimesh:
    if shape == "round":
        return trimesh.creation.icosphere(subdivisions=3, radius=radius)

    if shape == "oval":
        stone = trimesh.creation.icosphere(subdivisions=3, radius=radius)
        stone.apply_scale((1.35, 1.0, 0.85))
        return stone

    if shape == "princess":
        stone = trimesh.creation.box(extents=(radius * 1.65, radius * 1.65, radius * 1.15))
        stone.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 4.0, [0, 0, 1]))
        return stone

    if shape == "emerald_cut":
        return trimesh.creation.box(extents=(radius * 1.9, radius * 1.45, radius * 0.95))

    if shape == "marquise":
        stone = trimesh.creation.cylinder(radius=radius * 0.7, height=radius * 2.3, sections=18)
        stone.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2.0, [1, 0, 0]))
        stone.apply_scale((1.3, 0.9, 0.85))
        return stone

    sphere = trimesh.creation.icosphere(subdivisions=2, radius=radius * 0.9)
    tip = trimesh.creation.cone(radius=radius * 0.6, height=radius * 1.25, sections=14)
    tip.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    tip.apply_translation((0.0, radius * 0.95, 0.0))
    return trimesh.util.concatenate([sphere, tip])


open_component_library = OpenComponentLibrary()
