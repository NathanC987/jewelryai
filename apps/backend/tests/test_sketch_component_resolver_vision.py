from app.domain.ring import RingParameters
from app.services.component_visual_index import ComponentVisualDescriptor, ComponentVisualIndex
from app.services.sketch_component_resolver_vision import VisionModelSketchComponentResolver


def _build_index() -> ComponentVisualIndex:
    return ComponentVisualIndex(
        [
            ComponentVisualDescriptor(
                component_type="shank",
                component_id="classic_10",
                family="classic",
                variant=10,
                shape=None,
                prong_count_hint=None,
                source_path="/tmp/classic_10.glb",
                width=1.0,
                height=1.0,
                depth=1.0,
            ),
            ComponentVisualDescriptor(
                component_type="setting",
                component_id="peghead_06_round",
                family="peghead",
                variant=6,
                shape="round",
                prong_count_hint=6,
                source_path="/tmp/peghead_06_round.glb",
                width=1.0,
                height=1.0,
                depth=1.0,
            ),
        ]
    )


def test_vision_resolver_returns_vision_mapping_when_confident() -> None:
    resolver = VisionModelSketchComponentResolver(index=_build_index(), min_confidence=0.3)

    resolved = resolver.resolve(
        "my_sketch.png",
        RingParameters(
            shank_family="classic",
            shank_variant=10,
            setting_family="peghead",
            setting_variant=6,
            center_stone_shape="round",
            prong_count=6,
        ),
    )

    assert resolved.component_mapping.source == "vision_model"
    assert resolved.component_mapping.shank_component_id == "classic_10"
    assert resolved.component_mapping.setting_component_id == "peghead_06_round"
    assert resolved.parameters.shank_family == "classic"
    assert resolved.parameters.setting_family == "peghead"


def test_vision_resolver_falls_back_when_confidence_below_threshold() -> None:
    resolver = VisionModelSketchComponentResolver(index=_build_index(), min_confidence=0.99)

    resolved = resolver.resolve(
        "my_sketch.png",
        RingParameters(
            shank_family="classic",
            shank_variant=10,
            setting_family="peghead",
            setting_variant=6,
            center_stone_shape="round",
            prong_count=6,
        ),
    )

    assert resolved.component_mapping.source == "deterministic_fallback"
    assert resolved.component_mapping.shank_component_id is None
    assert resolved.component_mapping.setting_component_id is None