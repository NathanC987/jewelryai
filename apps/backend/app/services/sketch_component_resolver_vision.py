from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import settings
from app.domain.ring import RingParameters
from app.domain.sketch import SketchComponentMapping
from app.services.component_visual_index import ComponentVisualIndex
from app.services.sketch_component_resolver import SketchComponentResolution


class VisionModelSketchComponentResolver:
    """Component-aware resolver scaffold using local component visual index.

    This resolver is intentionally fallback-first. It uses index ranking against
    extracted sketch features and only applies a vision mapping when confidence
    clears a threshold.
    """

    def __init__(self, index: ComponentVisualIndex, min_confidence: float) -> None:
        self._logger = logging.getLogger("service.sketch_component_resolver.vision")
        self._index = index
        self._min_confidence = min_confidence
        descriptor_count = len(index.descriptors)
        self._logger.info(
            {
                "operation": "vision_resolver_init",
                "descriptor_count": descriptor_count,
                "min_confidence": min_confidence,
            }
        )

    @classmethod
    def from_settings(cls) -> "VisionModelSketchComponentResolver":
        components_root = Path(__file__).resolve().parents[4] / "components"
        cache_path = (
            Path(settings.sketch_component_visual_index_path)
            if settings.sketch_component_visual_index_path
            else None
        )
        index = ComponentVisualIndex.load_or_build(
            components_root=components_root,
            cache_path=cache_path,
            auto_build=settings.sketch_component_visual_index_autobuild,
        )
        logging.getLogger("service.sketch_component_resolver.vision").info(
            {
                "operation": "vision_resolver_build_from_settings",
                "components_root": str(components_root),
                "cache_path": str(cache_path) if cache_path else None,
                "autobuild": settings.sketch_component_visual_index_autobuild,
                "descriptor_count": len(index.descriptors),
                "threshold": settings.sketch_component_vision_min_confidence,
            }
        )
        return cls(index=index, min_confidence=settings.sketch_component_vision_min_confidence)

    def resolve(self, filename: str | None, extracted_parameters: RingParameters) -> SketchComponentResolution:
        shank = self._index.best_shank(extracted_parameters)
        setting = self._index.best_setting(extracted_parameters)

        self._logger.info(
            {
                "operation": "vision_resolve_start",
                "filename": Path(filename or "").name.lower() or None,
                "input_parameters": extracted_parameters.model_dump(),
            }
        )

        if not shank or not setting:
            return _fallback_resolution(
                extracted_parameters,
                reason="missing_shank_or_setting_candidate",
                logger=self._logger,
            )

        shank_desc, shank_score = shank
        setting_desc, setting_score = setting
        confidence = round((shank_score + setting_score) / 2.0, 3)

        self._logger.info(
            {
                "operation": "vision_resolve_candidates",
                "shank_candidate": shank_desc.component_id,
                "shank_family": shank_desc.family,
                "shank_variant": shank_desc.variant,
                "shank_score": round(shank_score, 3),
                "setting_candidate": setting_desc.component_id,
                "setting_family": setting_desc.family,
                "setting_variant": setting_desc.variant,
                "setting_shape": setting_desc.shape,
                "setting_prong_hint": setting_desc.prong_count_hint,
                "setting_score": round(setting_score, 3),
                "combined_confidence": confidence,
                "threshold": self._min_confidence,
            }
        )

        if confidence < self._min_confidence:
            return _fallback_resolution(
                extracted_parameters,
                reason="confidence_below_threshold",
                logger=self._logger,
            )

        updated = extracted_parameters.model_copy(
            update={
                "shank_family": shank_desc.family,
                "shank_variant": shank_desc.variant,
                "setting_family": setting_desc.family,
                "setting_variant": setting_desc.variant,
                **(
                    {"center_stone_shape": _shape_to_center_shape(setting_desc.shape)}
                    if setting_desc.shape
                    else {}
                ),
                **(
                    {"prong_count": setting_desc.prong_count_hint}
                    if setting_desc.prong_count_hint is not None
                    else {}
                ),
            }
        )

        return SketchComponentResolution(
            parameters=updated,
            component_mapping=SketchComponentMapping(
                source="vision_model",
                confidence=confidence,
                matched_filename=Path(filename or "").name.lower() or None,
                shank_component_id=shank_desc.component_id,
                setting_component_id=setting_desc.component_id,
            ),
        )


def _shape_to_center_shape(shape: str | None) -> str:
    if shape is None:
        return "round"
    if shape == "cushion":
        return "emerald_cut"
    return shape


def _fallback_resolution(
    extracted_parameters: RingParameters,
    reason: str,
    logger: logging.Logger,
) -> SketchComponentResolution:
    logger.info(
        {
            "operation": "vision_resolve_fallback",
            "reason": reason,
            "parameters": extracted_parameters.model_dump(),
        }
    )
    return SketchComponentResolution(
        parameters=extracted_parameters,
        component_mapping=SketchComponentMapping(
            source="deterministic_fallback",
            confidence=0.0,
            matched_filename=None,
            shank_component_id=None,
            setting_component_id=None,
        ),
    )