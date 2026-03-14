from app.services.sketch_analysis.base import SketchAnalysisDraft
from app.services.sketch_analysis.deterministic import DeterministicSketchAnalyzer


class MockModelSketchAnalyzer:
    """Model-backed placeholder used to validate runtime provider swapping without API changes."""

    def __init__(self) -> None:
        self._baseline = DeterministicSketchAnalyzer()

    def analyze(self, content: bytes) -> SketchAnalysisDraft:
        baseline = self._baseline.analyze(content)

        boosted_components = [
            component.model_copy(update={"confidence": min(0.99, round(component.confidence + 0.05, 3))})
            for component in baseline.components
        ]
        boosted_features = [
            feature.model_copy(update={"confidence": min(0.99, round(feature.confidence + 0.06, 3))})
            for feature in baseline.feature_confidences
        ]

        return SketchAnalysisDraft(
            extracted_parameters=baseline.extracted_parameters,
            components=boosted_components,
            feature_confidences=boosted_features,
            requires_user_confirmation=any(item.confidence < 0.66 for item in boosted_features),
            extraction_note=(
                "Mock model-backed sketch analysis applied. "
                "Swap to GroundingDINO/SAM2 provider when model service is connected."
            ),
        )
