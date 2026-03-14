from app.services.sketch_analysis.grounded_sam_adapters import (
    _component_from_label,
    _normalize_xyxy_to_xywh_norm,
    _proposals_from_grounding_predictions,
)


def test_component_from_label_maps_ring_terms() -> None:
    assert _component_from_label("ring band") == "band"
    assert _component_from_label("center gemstone") == "center_stone"
    assert _component_from_label("prong setting") == "prongs"
    assert _component_from_label("side stones") == "side_stones"


def test_normalize_xyxy_to_xywh_norm_clamps_and_scales() -> None:
    assert _normalize_xyxy_to_xywh_norm([20.0, 10.0, 120.0, 60.0], 200, 100) == [0.1, 0.1, 0.5, 0.5]
    assert _normalize_xyxy_to_xywh_norm([-10.0, -5.0, 220.0, 120.0], 200, 100) == [0.0, 0.0, 1.0, 1.0]


def test_proposals_from_grounding_predictions_keeps_best_component_score() -> None:
    predictions = {
        "boxes": [
            [10.0, 10.0, 110.0, 60.0],
            [30.0, 20.0, 100.0, 70.0],
            [40.0, 15.0, 95.0, 65.0],
        ],
        "scores": [0.6, 0.91, 0.77],
        "labels": ["ring band", "ring band", "center stone"],
    }

    proposals = _proposals_from_grounding_predictions(predictions, image_width=200, image_height=100)
    by_type = {item.component_type: item for item in proposals}

    assert set(by_type) == {"band", "center_stone"}
    assert by_type["band"].confidence == 0.91
    assert by_type["center_stone"].confidence == 0.77
