from app.domain.ring import RingParameters
from app.services.sketch_component_resolver import FilenameSketchComponentResolver


def test_known_filename_ring_sketch_1_maps_components() -> None:
    resolver = FilenameSketchComponentResolver()
    base = RingParameters()

    resolved = resolver.resolve("ring_sketch_1.jpg", base)

    assert resolved.component_mapping.source == "known_filename"
    assert resolved.component_mapping.confidence == 1.0
    assert resolved.component_mapping.matched_filename == "ring_sketch_1.jpg"
    assert resolved.component_mapping.shank_component_id == "classic_01"
    assert resolved.component_mapping.setting_component_id == "peghead_06_round"
    assert resolved.parameters.shank_family == "classic"
    assert resolved.parameters.shank_variant == 1
    assert resolved.parameters.setting_family == "peghead"
    assert resolved.parameters.setting_variant == 6
    assert resolved.parameters.center_stone_shape == "round"
    assert resolved.parameters.prong_count == 6


def test_known_filename_ring_sketch_2_maps_components() -> None:
    resolver = FilenameSketchComponentResolver()
    base = RingParameters(shank_family="advanced", shank_variant=4)

    resolved = resolver.resolve("ring_sketch_2.png", base)

    assert resolved.component_mapping.source == "known_filename"
    assert resolved.component_mapping.shank_component_id == "classic_10"
    assert resolved.component_mapping.setting_component_id == "peghead_06_round"
    assert resolved.parameters.shank_family == "classic"
    assert resolved.parameters.shank_variant == 10
    assert resolved.parameters.setting_family == "peghead"
    assert resolved.parameters.setting_variant == 6


def test_known_filename_ring_sketch_3_maps_components() -> None:
    resolver = FilenameSketchComponentResolver()
    base = RingParameters(setting_family="bezel", setting_variant=2)

    resolved = resolver.resolve("ring_sketch_3.png", base)

    assert resolved.component_mapping.source == "known_filename"
    assert resolved.component_mapping.shank_component_id == "cathedral_01"
    assert resolved.component_mapping.setting_component_id == "halo_15_round"
    assert resolved.parameters.shank_family == "cathedral"
    assert resolved.parameters.shank_variant == 1
    assert resolved.parameters.setting_family == "halo"
    assert resolved.parameters.setting_variant == 15


def test_known_filename_ring_sketch_4_maps_components() -> None:
    resolver = FilenameSketchComponentResolver()
    base = RingParameters(setting_family="bezel", setting_variant=2)

    resolved = resolver.resolve("ring_sketch_4.png", base)

    assert resolved.component_mapping.source == "known_filename"
    assert resolved.component_mapping.shank_component_id == "classic_10"
    assert resolved.component_mapping.setting_component_id == "cluster_09_round"
    assert resolved.parameters.shank_family == "classic"
    assert resolved.parameters.shank_variant == 10
    assert resolved.parameters.setting_family == "cluster"
    assert resolved.parameters.setting_variant == 9


def test_unknown_filename_uses_fallback_and_keeps_parameters() -> None:
    resolver = FilenameSketchComponentResolver()
    base = RingParameters(
        shank_family="advanced",
        shank_variant=7,
        setting_family="bezel",
        setting_variant=5,
        center_stone_shape="oval",
        prong_count=4,
    )

    resolved = resolver.resolve("custom_uploaded_sketch.jpeg", base)

    assert resolved.component_mapping.source == "deterministic_fallback"
    assert resolved.component_mapping.confidence == 0.0
    assert resolved.component_mapping.matched_filename is None
    assert resolved.parameters == base


def test_known_filename_matching_is_case_insensitive() -> None:
    resolver = FilenameSketchComponentResolver()

    resolved = resolver.resolve("RING_SKETCH_3.PNG", RingParameters())

    assert resolved.component_mapping.source == "known_filename"
    assert resolved.component_mapping.matched_filename == "ring_sketch_3.png"
    assert resolved.parameters.setting_family == "halo"