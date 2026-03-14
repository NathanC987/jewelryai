from dataclasses import dataclass

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

    def selected_components(self, context: AssemblyContext) -> list[str]:
        return self._resolve_component_ids(context)

    def assemble_ring(self, context: AssemblyContext) -> trimesh.Trimesh:
        component_ids = self._resolve_component_ids(context)

        meshes: list[trimesh.Trimesh] = []
        for component_id in component_ids:
            if component_id.startswith("band."):
                meshes.extend(self._build_band_component(component_id, context))
            elif component_id.startswith("setting."):
                meshes.extend(self._build_setting_component(component_id, context))
            elif component_id.startswith("accent."):
                meshes.extend(self._build_accent_component(component_id, context))
            elif component_id.startswith("style."):
                meshes.extend(self._build_style_component(component_id, context))

        mesh = trimesh.util.concatenate(meshes)
        mesh.merge_vertices()
        mesh.remove_unreferenced_vertices()
        return mesh

    def _resolve_component_ids(self, context: AssemblyContext) -> list[str]:
        band_component = self.band_components.get(context.band_profile, "band.classic")
        setting_component = self.setting_components.get(context.template_id, "setting.solitaire")
        accent_component = self.accent_components.get(context.template_id)
        style_component = self.style_components.get(context.style_tag, "style.streamlined_gallery")

        # Royal setting recipe biases the basket architecture toward taller crown-style settings.
        if context.style_tag == "royal" and setting_component in {"setting.solitaire", "setting.halo"}:
            setting_component = "setting.royal_crown"

        parts = [band_component, setting_component, style_component]
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
