from app.services.component_library import AssemblyContext, open_component_library
import trimesh


def test_open_component_library_assembles_halo_ring() -> None:
    context = AssemblyContext(
        template_id="halo_ring",
        style_tag="vintage",
        band_profile="classic",
        band_thickness_mm=2.2,
        gemstone_size_mm=5.4,
        gemstone_type="ruby",
        center_stone_shape="oval",
        prong_count=6,
        side_stone_count=14,
        setting_family="halo",
        setting_variant=15,
        setting_openheart=False,
        shank_family="cathedral",
        shank_variant=3,
        setting_height_mm=2.2,
    )

    mesh = open_component_library.assemble_ring(context)
    assert mesh.vertices.shape[0] > 0
    assert mesh.faces.shape[0] > 0
    assert float(mesh.volume) > 0.0


def test_open_component_library_assembles_three_stone_ring() -> None:
    context = AssemblyContext(
        template_id="three_stone_ring",
        style_tag="modern",
        band_profile="tapered",
        band_thickness_mm=2.0,
        gemstone_size_mm=5.0,
        gemstone_type="diamond",
        center_stone_shape="round",
        prong_count=4,
        side_stone_count=2,
        setting_family="basket",
        setting_variant=4,
        setting_openheart=False,
        shank_family="classic",
        shank_variant=4,
        setting_height_mm=2.0,
    )

    mesh = open_component_library.assemble_ring(context)
    assert mesh.vertices.shape[0] > 0
    assert mesh.faces.shape[0] > 0
    assert float(mesh.volume) > 0.0


def test_open_component_library_selected_components_include_style_recipe() -> None:
    context = AssemblyContext(
        template_id="solitaire_ring",
        style_tag="royal",
        band_profile="tapered",
        band_thickness_mm=2.2,
        gemstone_size_mm=5.8,
        gemstone_type="diamond",
        center_stone_shape="round",
        prong_count=6,
        side_stone_count=0,
        setting_family="peghead",
        setting_variant=4,
        setting_openheart=False,
        shank_family="cathedral",
        shank_variant=10,
        setting_height_mm=2.4,
    )

    components = open_component_library.selected_components(context)
    assert "band.tapered" in components
    assert "setting.royal_crown" in components
    assert "style.cathedral_arms" in components


def test_solitaire_setting_height_changes_vertical_extent() -> None:
    base_context = AssemblyContext(
        template_id="solitaire_ring",
        style_tag="modern",
        band_profile="classic",
        band_thickness_mm=2.0,
        gemstone_size_mm=5.2,
        gemstone_type="diamond",
        center_stone_shape="round",
        prong_count=4,
        side_stone_count=0,
        setting_family="peghead",
        setting_variant=4,
        setting_openheart=False,
        shank_family="classic",
        shank_variant=1,
        setting_height_mm=1.2,
    )
    tall_context = AssemblyContext(
        template_id="solitaire_ring",
        style_tag="modern",
        band_profile="classic",
        band_thickness_mm=2.0,
        gemstone_size_mm=5.2,
        gemstone_type="diamond",
        center_stone_shape="round",
        prong_count=4,
        side_stone_count=0,
        setting_family="peghead",
        setting_variant=4,
        setting_openheart=False,
        shank_family="classic",
        shank_variant=1,
        setting_height_mm=3.2,
    )

    base_mesh = open_component_library.assemble_ring(base_context)
    tall_mesh = open_component_library.assemble_ring(tall_context)

    base_height = float(base_mesh.bounds[1][2] - base_mesh.bounds[0][2])
    tall_height = float(tall_mesh.bounds[1][2] - tall_mesh.bounds[0][2])
    assert tall_height > base_height


def test_solitaire_side_stones_do_not_add_nonlocal_geometry() -> None:
    clean_context = AssemblyContext(
        template_id="solitaire_ring",
        style_tag="modern",
        band_profile="classic",
        band_thickness_mm=2.0,
        gemstone_size_mm=5.0,
        gemstone_type="diamond",
        center_stone_shape="round",
        prong_count=4,
        side_stone_count=0,
        setting_family="peghead",
        setting_variant=4,
        setting_openheart=False,
        shank_family="classic",
        shank_variant=1,
        setting_height_mm=2.0,
    )
    detailed_context = AssemblyContext(
        template_id="solitaire_ring",
        style_tag="modern",
        band_profile="classic",
        band_thickness_mm=2.0,
        gemstone_size_mm=5.0,
        gemstone_type="diamond",
        center_stone_shape="round",
        prong_count=4,
        side_stone_count=6,
        setting_family="peghead",
        setting_variant=4,
        setting_openheart=False,
        shank_family="classic",
        shank_variant=1,
        setting_height_mm=2.0,
    )

    clean_mesh = open_component_library.assemble_ring(clean_context)
    detailed_mesh = open_component_library.assemble_ring(detailed_context)

    assert float(detailed_mesh.volume) == float(clean_mesh.volume)


def test_local_setting_seats_into_shank_depth_axis() -> None:
    context = AssemblyContext(
        template_id="solitaire_ring",
        style_tag="modern",
        band_profile="classic",
        band_thickness_mm=2.0,
        gemstone_size_mm=5.2,
        gemstone_type="diamond",
        center_stone_shape="round",
        prong_count=4,
        side_stone_count=0,
        setting_family="peghead",
        setting_variant=1,
        setting_openheart=False,
        shank_family="classic",
        shank_variant=1,
        setting_height_mm=2.2,
    )

    scene = open_component_library.assemble_ring_scene(context)
    band_meshes = [mesh.copy() for name, mesh in scene.geometry.items() if name.startswith("band.")]
    setting_meshes = [mesh.copy() for name, mesh in scene.geometry.items() if name.startswith("setting.")]

    assert band_meshes
    assert setting_meshes

    band_bounds = trimesh.util.concatenate(band_meshes).bounds
    setting_bounds = trimesh.util.concatenate(setting_meshes).bounds

    shank_top_z = float(band_bounds[1][2])
    setting_base_z = float(setting_bounds[0][2])

    assert setting_base_z <= shank_top_z
    assert setting_base_z >= (shank_top_z - context.band_thickness_mm * 2.0)


def test_shank_and_setting_have_y_axis_overlap() -> None:
    context = AssemblyContext(
        template_id="solitaire_ring",
        style_tag="modern",
        band_profile="classic",
        band_thickness_mm=2.0,
        gemstone_size_mm=5.2,
        gemstone_type="diamond",
        center_stone_shape="round",
        prong_count=4,
        side_stone_count=0,
        setting_family="peghead",
        setting_variant=1,
        setting_openheart=False,
        shank_family="classic",
        shank_variant=1,
        setting_height_mm=2.2,
    )

    scene = open_component_library.assemble_ring_scene(context)
    band_meshes = [mesh.copy() for name, mesh in scene.geometry.items() if name.startswith("band.")]
    setting_meshes = [mesh.copy() for name, mesh in scene.geometry.items() if name.startswith("setting.")]

    assert band_meshes
    assert setting_meshes

    band_bounds = trimesh.util.concatenate(band_meshes).bounds
    setting_bounds = trimesh.util.concatenate(setting_meshes).bounds

    overlap_start = max(float(band_bounds[0][1]), float(setting_bounds[0][1]))
    overlap_end = min(float(band_bounds[1][1]), float(setting_bounds[1][1]))

    assert overlap_end > overlap_start


def test_marquise_setting_keeps_authored_proportions() -> None:
    context = AssemblyContext(
        template_id="solitaire_ring",
        style_tag="modern",
        band_profile="classic",
        band_thickness_mm=2.0,
        gemstone_size_mm=5.6,
        gemstone_type="diamond",
        center_stone_shape="marquise",
        prong_count=4,
        side_stone_count=0,
        setting_family="peghead",
        setting_variant=1,
        setting_openheart=False,
        shank_family="classic",
        shank_variant=1,
        setting_height_mm=2.2,
    )

    setting_path = open_component_library._choose_setting_path(context)
    assert setting_path is not None
    raw_meshes = open_component_library._load_mesh_file_parts(setting_path)
    assert raw_meshes

    shank_path = open_component_library._choose_shank_path(context)
    assert shank_path is not None
    shank_raw = open_component_library._load_mesh_file_parts(shank_path)
    shank_fit = open_component_library._fit_local_shank_meshes(shank_raw, context)
    shank_bounds = trimesh.util.concatenate([mesh.copy() for mesh in shank_fit]).bounds
    shank_mount_plane_y = float(shank_bounds[1][1]) - context.band_thickness_mm * 0.16
    shank_top_z = float(shank_bounds[1][2])

    fitted_meshes = open_component_library._fit_local_setting_meshes(
        raw_meshes,
        context,
        shank_mount_plane_y=shank_mount_plane_y,
        shank_top_z=shank_top_z,
    )

    raw_extents = trimesh.util.concatenate([mesh.copy() for mesh in raw_meshes]).extents
    fitted_extents = trimesh.util.concatenate([mesh.copy() for mesh in fitted_meshes]).extents

    raw_ratio = float(max(raw_extents) / max(min(raw_extents), 1e-6))
    fitted_ratio = float(max(fitted_extents) / max(min(fitted_extents), 1e-6))

    assert fitted_ratio >= raw_ratio * 0.95
