"""Pipeline のテスト。"""

from __future__ import annotations

from grabtl.core.ocr.base import OCRResult
from grabtl.core.pipeline import Pipeline


class FakeOCREngine:
    """テスト用 OCR エンジン。"""

    def __init__(self, text: str = "Hello World", confidence: float = 0.95) -> None:
        self._text = text
        self._confidence = confidence

    def recognize(self, image: bytes, lang: str = "en") -> OCRResult:
        return OCRResult(text=self._text, confidence=self._confidence, lang=lang)

    def available_languages(self) -> list[str]:
        return ["en"]

    @property
    def name(self) -> str:
        return "FakeOCR"


class FakeTranslator:
    """テスト用翻訳エンジン。"""

    def translate(self, text: str, source: str, target: str) -> str:
        return f"翻訳済み: {text}"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def is_local(self) -> bool:
        return True

    @property
    def allowed_endpoints(self) -> list[str]:
        return []


class TestPipeline:
    def test_正常な翻訳パイプライン(self) -> None:
        ocr = FakeOCREngine()
        translator = FakeTranslator()
        pipeline = Pipeline(ocr_engine=ocr, translator=translator)

        result = pipeline.run(b"dummy_image", source_lang="en", target_lang="ja")

        assert result.ocr_result.text == "Hello World"
        assert result.translated_text == "翻訳済み: Hello World"

    def test_空テキストの場合は翻訳しない(self) -> None:
        ocr = FakeOCREngine(text="", confidence=0.0)
        translator = FakeTranslator()
        pipeline = Pipeline(ocr_engine=ocr, translator=translator)

        result = pipeline.run(b"dummy_image")

        assert result.ocr_result.text == ""
        assert result.translated_text == ""

    def test_空白のみのテキストは翻訳しない(self) -> None:
        ocr = FakeOCREngine(text="   ", confidence=0.1)
        translator = FakeTranslator()
        pipeline = Pipeline(ocr_engine=ocr, translator=translator)

        result = pipeline.run(b"dummy_image")

        assert result.translated_text == ""

    def test_OCR結果が保持される(self) -> None:
        ocr = FakeOCREngine(confidence=0.87)
        translator = FakeTranslator()
        pipeline = Pipeline(ocr_engine=ocr, translator=translator)

        result = pipeline.run(b"dummy_image")

        assert result.ocr_result.confidence == 0.87
        assert result.ocr_result.lang == "en"
