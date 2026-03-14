from dataclasses import dataclass
from typing import Protocol

from app.domain.ring import RingParameters
from app.domain.sketch import ComponentDetection, FeatureConfidence


@dataclass
class SketchAnalysisDraft:
    extracted_parameters: RingParameters
    components: list[ComponentDetection]
    feature_confidences: list[FeatureConfidence]
    requires_user_confirmation: bool
    extraction_note: str


class SketchAnalyzer(Protocol):
    def analyze(self, content: bytes) -> SketchAnalysisDraft:
        ...
