from io import BytesIO

import pytest
from PIL import Image, ImageDraw

from app.services.sketch_analysis.grounded_sam import GroundedSamSketchAnalyzer
from app.services.sketch_analysis.grounded_sam import ModelProviderUnavailableError


def test_grounded_sam_analyze_runs_adapter_pipeline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(
        "app.services.sketch_analysis.grounded_sam.find_spec",
        lambda _name: object(),
    )

    dino = tmp_path / "dino.pt"
    sam2 = tmp_path / "sam2.pt"
    dino.write_bytes(b"x")
    sam2.write_bytes(b"x")

    analyzer = GroundedSamSketchAnalyzer(
        device="cpu",
        grounding_dino_checkpoint_path=str(dino),
        sam2_checkpoint_path=str(sam2),
    )

    image = Image.new("RGB", (220, 220), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((20, 110, 200, 200), outline="black", width=10)
    draw.ellipse((80, 40, 140, 100), outline="black", width=6)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    content = buffer.getvalue()

    result = analyzer.analyze(content)
    assert result.components
    assert result.feature_confidences
    assert "Grounded-SAM scaffold adapters executed" in result.extraction_note


def test_grounded_sam_real_mode_raises_when_runtime_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(
        "app.services.sketch_analysis.grounded_sam.find_spec",
        lambda _name: object(),
    )

    dino = tmp_path / "dino.pt"
    sam2 = tmp_path / "sam2.pt"
    dino.write_bytes(b"x")
    sam2.write_bytes(b"x")

    with pytest.raises(ModelProviderUnavailableError):
        GroundedSamSketchAnalyzer(
            device="cpu",
            mode="real",
            grounding_dino_checkpoint_path=str(dino),
            sam2_checkpoint_path=str(sam2),
        )
