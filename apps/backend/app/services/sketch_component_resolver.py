from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Protocol

from app.domain.ring import RingParameters
from app.domain.sketch import SketchComponentMapping


@dataclass
class SketchComponentResolution:
    parameters: RingParameters
    component_mapping: SketchComponentMapping


class SketchComponentResolver(Protocol):
    def resolve(self, filename: str | None, extracted_parameters: RingParameters) -> SketchComponentResolution:
        ...


class FilenameSketchComponentResolver:
    """Deterministic filename-based resolver for known sketch assets.

    This strategy is intentionally simple and acts as the first pluggable
    implementation behind the resolver contract. A future vision resolver can
    implement the same interface and be selected via configuration.
    """

    _known_filename_map = {
        "ring_sketch_1.jpg": {
            "shank_family": "classic",
            "shank_variant": 1,
            "setting_family": "peghead",
            "setting_variant": 6,
            "center_stone_shape": "round",
            "prong_count": 6,
            "shank_component_id": "classic_01",
            "setting_component_id": "peghead_06_round",
        },
        "ring_sketch_2.png": {
            "shank_family": "classic",
            "shank_variant": 10,
            "setting_family": "peghead",
            "setting_variant": 6,
            "center_stone_shape": "round",
            "prong_count": 6,
            "shank_component_id": "classic_10",
            "setting_component_id": "peghead_06_round",
        },
        "ring_sketch_3.png": {
            "shank_family": "cathedral",
            "shank_variant": 1,
            "setting_family": "halo",
            "setting_variant": 15,
            "center_stone_shape": "round",
            "shank_component_id": "cathedral_01",
            "setting_component_id": "halo_15_round",
        },
        "ring_sketch_4.png": {
            "shank_family": "classic",
            "shank_variant": 10,
            "setting_family": "cluster",
            "setting_variant": 9,
            "center_stone_shape": "round",
            "shank_component_id": "classic_10",
            "setting_component_id": "cluster_09_round",
        },
    }

    def resolve(self, filename: str | None, extracted_parameters: RingParameters) -> SketchComponentResolution:
        logger = logging.getLogger("service.sketch_component_resolver.filename")
        normalized_filename = Path(filename or "").name.lower()
        mapping = self._known_filename_map.get(normalized_filename)

        if not mapping:
            logger.info(
                {
                    "operation": "filename_resolver_miss",
                    "filename": normalized_filename or None,
                    "known_filenames": sorted(self._known_filename_map.keys()),
                    "reason": "filename_not_in_known_map",
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

        logger.info(
            {
                "operation": "filename_resolver_hit",
                "filename": normalized_filename,
                "shank_component_id": mapping["shank_component_id"],
                "setting_component_id": mapping["setting_component_id"],
            }
        )

        updated_parameters = extracted_parameters.model_copy(
            update={
                "metal": "gold",
                "gemstone_type": "sapphire",
                "shank_family": mapping["shank_family"],
                "shank_variant": mapping["shank_variant"],
                "setting_family": mapping["setting_family"],
                "setting_variant": mapping["setting_variant"],
                "center_stone_shape": mapping["center_stone_shape"],
                **({"prong_count": mapping["prong_count"]} if "prong_count" in mapping else {}),
            }
        )

        return SketchComponentResolution(
            parameters=updated_parameters,
            component_mapping=SketchComponentMapping(
                source="known_filename",
                confidence=1.0,
                matched_filename=normalized_filename,
                shank_component_id=mapping["shank_component_id"],
                setting_component_id=mapping["setting_component_id"],
            ),
        )


class NoopSketchComponentResolver:
    """Pass-through resolver used as fallback for unknown strategies."""

    def resolve(self, filename: str | None, extracted_parameters: RingParameters) -> SketchComponentResolution:
        return SketchComponentResolution(
            parameters=extracted_parameters,
            component_mapping=SketchComponentMapping(
                source="deterministic_fallback",
                confidence=0.0,
                matched_filename=Path(filename or "").name.lower() or None,
                shank_component_id=None,
                setting_component_id=None,
            ),
        )


def create_sketch_component_resolver(strategy: str) -> SketchComponentResolver:
    logger = logging.getLogger("service.sketch_component_resolver")
    logger.info({"operation": "resolver_factory", "strategy": strategy})
    if strategy == "filename":
        logger.info({"operation": "resolver_factory", "selected": "FilenameSketchComponentResolver"})
        return FilenameSketchComponentResolver()
    if strategy == "vision_model":
        from app.services.sketch_component_resolver_vision import VisionModelSketchComponentResolver

        logger.info({"operation": "resolver_factory", "selected": "VisionModelSketchComponentResolver"})
        return VisionModelSketchComponentResolver.from_settings()
    logger.warning(
        {
            "operation": "resolver_factory",
            "selected": "NoopSketchComponentResolver",
            "reason": "unknown_strategy",
            "strategy": strategy,
        }
    )
    return NoopSketchComponentResolver()
