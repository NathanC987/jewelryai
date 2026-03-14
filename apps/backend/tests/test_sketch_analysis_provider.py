import pytest

from app.services.sketch_analysis import create_sketch_analyzer
from app.services.sketch_analysis.deterministic import DeterministicSketchAnalyzer
from app.services.sketch_analysis.grounded_sam import GroundedSamSketchAnalyzer
from app.services.sketch_analysis.grounded_sam import ModelProviderUnavailableError
from app.services.sketch_analysis.mock_model import MockModelSketchAnalyzer


def test_create_sketch_analyzer_deterministic() -> None:
    analyzer, backend = create_sketch_analyzer("deterministic")
    assert isinstance(analyzer, DeterministicSketchAnalyzer)
    assert backend == "deterministic"


def test_create_sketch_analyzer_mock_model() -> None:
    analyzer, backend = create_sketch_analyzer("mock_model")
    assert isinstance(analyzer, MockModelSketchAnalyzer)
    assert backend == "mock_model"


def test_create_sketch_analyzer_grounded_sam_falls_back() -> None:
    analyzer, backend = create_sketch_analyzer(
        "grounded_sam",
        fallback_backend="deterministic",
        allow_fallback=True,
    )
    assert isinstance(analyzer, DeterministicSketchAnalyzer)
    assert backend == "deterministic"


def test_create_sketch_analyzer_grounded_sam_real_mode_falls_back() -> None:
    analyzer, backend = create_sketch_analyzer(
        "grounded_sam",
        grounded_sam_mode="real",
        fallback_backend="deterministic",
        allow_fallback=True,
    )
    assert isinstance(analyzer, DeterministicSketchAnalyzer)
    assert backend == "deterministic"


def test_create_sketch_analyzer_grounded_sam_no_fallback() -> None:
    with pytest.raises(ModelProviderUnavailableError):
        create_sketch_analyzer(
            "grounded_sam",
            allow_fallback=False,
        )


def test_create_sketch_analyzer_grounded_sam_success(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(
        "app.services.sketch_analysis.grounded_sam.find_spec",
        lambda _name: object(),
    )
    dino = tmp_path / "dino.pt"
    sam2 = tmp_path / "sam2.pt"
    dino.write_bytes(b"x")
    sam2.write_bytes(b"x")

    analyzer, backend = create_sketch_analyzer(
        "grounded_sam",
        allow_fallback=False,
        grounding_dino_checkpoint_path=str(dino),
        sam2_checkpoint_path=str(sam2),
    )
    assert backend == "grounded_sam"
    assert isinstance(analyzer, GroundedSamSketchAnalyzer)


def test_create_sketch_analyzer_invalid_backend() -> None:
    with pytest.raises(ValueError):
        create_sketch_analyzer("unsupported")


def test_create_sketch_analyzer_grounded_sam_invalid_mode_no_fallback() -> None:
    with pytest.raises(ModelProviderUnavailableError):
        create_sketch_analyzer(
            "grounded_sam",
            grounded_sam_mode="invalid",
            allow_fallback=False,
        )
