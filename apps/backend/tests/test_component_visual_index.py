from app.domain.ring import RingParameters
from app.services.component_visual_index import ComponentVisualDescriptor, ComponentVisualIndex


def test_best_shank_prefers_matching_family_and_variant() -> None:
    index = ComponentVisualIndex(
        [
            ComponentVisualDescriptor(
                component_type="shank",
                component_id="classic_01",
                family="classic",
                variant=1,
                shape=None,
                prong_count_hint=None,
                source_path="/tmp/classic_01.glb",
                width=1.0,
                height=1.0,
                depth=1.0,
            ),
            ComponentVisualDescriptor(
                component_type="shank",
                component_id="cathedral_01",
                family="cathedral",
                variant=1,
                shape=None,
                prong_count_hint=None,
                source_path="/tmp/cathedral_01.glb",
                width=1.0,
                height=1.0,
                depth=1.0,
            ),
        ]
    )

    best = index.best_shank(RingParameters(shank_family="cathedral", shank_variant=1))

    assert best is not None
    descriptor, score = best
    assert descriptor.component_id == "cathedral_01"
    assert score > 0.8


def test_best_setting_prefers_shape_and_prong_compatibility() -> None:
    index = ComponentVisualIndex(
        [
            ComponentVisualDescriptor(
                component_type="setting",
                component_id="peghead_04_round",
                family="peghead",
                variant=4,
                shape="round",
                prong_count_hint=4,
                source_path="/tmp/peghead_04_round.glb",
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

    best = index.best_setting(
        RingParameters(setting_family="peghead", setting_variant=6, center_stone_shape="round", prong_count=6)
    )

    assert best is not None
    descriptor, score = best
    assert descriptor.component_id == "peghead_06_round"
    assert score > 0.9