from app.services.component_library import AssemblyContext, open_component_library


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
