from io import BytesIO

import numpy as np
from PIL import Image

from app.domain.ring import RingParameters
from app.domain.sketch import ComponentDetection, FeatureConfidence
from app.services.sketch_analysis.base import SketchAnalysisDraft


class DeterministicSketchAnalyzer:
    def analyze(self, content: bytes) -> SketchAnalysisDraft:
        image = Image.open(BytesIO(content)).convert("L")
        image = image.resize((256, 256))
        pixels = np.asarray(image, dtype=np.float32) / 255.0

        darkness = float(1.0 - pixels.mean())
        contrast = float(pixels.std())
        gradient = np.abs(np.diff(pixels, axis=0)).mean() + np.abs(np.diff(pixels, axis=1)).mean()

        threshold = (pixels < 0.62).astype(np.float32)
        transitions = np.abs(np.diff(threshold, axis=0)).mean() + np.abs(np.diff(threshold, axis=1)).mean()

        gemstone_size_mm = _clamp(2.2 + darkness * 7.0 + gradient * 2.0, 1.0, 12.0)
        band_thickness_mm = _clamp(1.2 + contrast * 7.5 + gradient * 1.2, 1.2, 5.0)

        if gradient > 0.26:
            gemstone_type = "diamond"
        elif gradient > 0.19:
            gemstone_type = "sapphire"
        elif darkness > 0.56:
            gemstone_type = "ruby"
        else:
            gemstone_type = "emerald"

        if darkness < 0.30:
            metal = "silver"
        elif darkness < 0.45:
            metal = "platinum"
        elif darkness < 0.60:
            metal = "gold"
        else:
            metal = "rose_gold"

        center_stone_shape = _infer_center_shape(gradient=gradient, contrast=contrast, darkness=darkness)
        prong_count = _infer_prong_count(transitions=transitions, gradient=gradient)
        band_profile = _infer_band_profile(contrast=contrast, transitions=transitions)
        side_stone_count = _infer_side_stone_count(transitions=transitions, contrast=contrast)
        setting_height_mm = _clamp(1.1 + gradient * 4.8 + darkness * 1.1, 0.6, 5.0)

        extracted = RingParameters(
            metal=metal,
            gemstone_type=gemstone_type,
            center_stone_shape=center_stone_shape,
            prong_count=prong_count,
            band_profile=band_profile,
            side_stone_count=side_stone_count,
            setting_height_mm=round(setting_height_mm, 2),
            gemstone_size_mm=round(gemstone_size_mm, 2),
            band_thickness_mm=round(band_thickness_mm, 2),
        )

        center_stone_conf = _clamp(0.58 + gradient * 0.85, 0.45, 0.96)
        band_conf = _clamp(0.55 + contrast * 1.1, 0.45, 0.96)
        prong_conf = _clamp(0.52 + transitions * 1.2, 0.4, 0.95)
        side_stone_conf = _clamp(0.5 + transitions * 0.9 + contrast * 0.4, 0.4, 0.93)
        setting_conf = _clamp(0.53 + gradient * 0.72 + darkness * 0.25, 0.42, 0.94)

        components = [
            ComponentDetection(
                component_type="band",
                bbox_norm_xywh=[0.15, 0.46, 0.7, 0.4],
                confidence=round(band_conf, 3),
            ),
            ComponentDetection(
                component_type="center_stone",
                bbox_norm_xywh=[0.38, 0.18, 0.24, 0.26],
                confidence=round(center_stone_conf, 3),
            ),
            ComponentDetection(
                component_type="prongs",
                bbox_norm_xywh=[0.33, 0.16, 0.34, 0.33],
                confidence=round(prong_conf, 3),
            ),
            ComponentDetection(
                component_type="side_stones",
                bbox_norm_xywh=[0.17, 0.33, 0.66, 0.22],
                confidence=round(side_stone_conf, 3),
            ),
        ]

        feature_confidences = [
            FeatureConfidence(
                feature_name="center_stone_shape",
                value=extracted.center_stone_shape,
                confidence=round(center_stone_conf, 3),
            ),
            FeatureConfidence(
                feature_name="prong_count",
                value=extracted.prong_count,
                confidence=round(prong_conf, 3),
            ),
            FeatureConfidence(
                feature_name="band_profile",
                value=extracted.band_profile,
                confidence=round(band_conf, 3),
            ),
            FeatureConfidence(
                feature_name="side_stone_count",
                value=extracted.side_stone_count,
                confidence=round(side_stone_conf, 3),
            ),
            FeatureConfidence(
                feature_name="setting_height_mm",
                value=extracted.setting_height_mm,
                confidence=round(setting_conf, 3),
            ),
            FeatureConfidence(
                feature_name="gemstone_size_mm",
                value=extracted.gemstone_size_mm,
                confidence=round(_clamp(0.56 + darkness * 0.8, 0.45, 0.94), 3),
            ),
            FeatureConfidence(
                feature_name="band_thickness_mm",
                value=extracted.band_thickness_mm,
                confidence=round(_clamp(0.56 + contrast * 0.85, 0.45, 0.94), 3),
            ),
        ]

        requires_confirmation = any(item.confidence < 0.66 for item in feature_confidences)
        return SketchAnalysisDraft(
            extracted_parameters=extracted,
            components=components,
            feature_confidences=feature_confidences,
            requires_user_confirmation=requires_confirmation,
            extraction_note=(
                "Deterministic sketch preprocessing extracted initial ring parameters. "
                "AI concept-to-CAD extraction is a planned next phase."
            ),
        )


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _infer_center_shape(gradient: float, contrast: float, darkness: float) -> str:
    if contrast > 0.29 and gradient > 0.22:
        return "princess"
    if gradient > 0.25 and darkness > 0.46:
        return "marquise"
    if gradient > 0.21 and darkness < 0.40:
        return "oval"
    if contrast < 0.22 and darkness < 0.35:
        return "emerald_cut"
    if darkness > 0.58:
        return "pear"
    return "round"


def _infer_prong_count(transitions: float, gradient: float) -> int:
    signal = transitions * 10.0 + gradient * 8.0
    if signal > 2.95:
        return 8
    if signal > 2.35:
        return 6
    if signal > 1.75:
        return 5
    return 4


def _infer_band_profile(contrast: float, transitions: float) -> str:
    if contrast > 0.31 and transitions > 0.21:
        return "knife_edge"
    if contrast < 0.20:
        return "flat"
    if transitions > 0.24:
        return "tapered"
    return "classic"


def _infer_side_stone_count(transitions: float, contrast: float) -> int:
    richness = transitions * 16.0 + contrast * 7.0
    if richness > 6.2:
        return 14
    if richness > 5.3:
        return 10
    if richness > 4.2:
        return 6
    if richness > 3.3:
        return 2
    return 0
