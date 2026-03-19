"""OCR Protocol と OCRResult のテスト。"""

from __future__ import annotations

from grabtl.core.ocr.base import OCREngine, OCRResult


class FakeOCREngine:
    """テスト用の OCR エンジン。"""

    def recognize(self, image: bytes, lang: str = "en") -> OCRResult:
        return OCRResult(text="Hello World", confidence=0.95, lang=lang)

    def available_languages(self) -> list[str]:
        return ["en", "ja"]

    @property
    def name(self) -> str:
        return "FakeOCR"


class TestOCRResult:
    def test_デフォルト値(self) -> None:
        result = OCRResult(text="test", confidence=0.9, lang="en")
        assert result.text == "test"
        assert result.confidence == 0.9
        assert result.lang == "en"
        assert result.bounding_boxes is None

    def test_バウンディングボックス付き(self) -> None:
        boxes = [{"x": 0, "y": 0, "width": 100, "height": 20}]
        result = OCRResult(text="test", confidence=0.9, lang="en", bounding_boxes=boxes)
        assert result.bounding_boxes is not None
        assert len(result.bounding_boxes) == 1


class TestOCREngine:
    def test_Protocolに準拠(self) -> None:
        engine = FakeOCREngine()
        assert isinstance(engine, OCREngine)

    def test_recognize(self) -> None:
        engine = FakeOCREngine()
        result = engine.recognize(b"dummy_image", lang="en")
        assert result.text == "Hello World"
        assert result.confidence == 0.95

    def test_available_languages(self) -> None:
        engine = FakeOCREngine()
        langs = engine.available_languages()
        assert "en" in langs
        assert "ja" in langs

    def test_name(self) -> None:
        engine = FakeOCREngine()
        assert engine.name == "FakeOCR"
