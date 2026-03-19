"""OCR → 翻訳パイプライン。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from grabtl.core.ocr.base import OCRResult  # noqa: TCH001

if TYPE_CHECKING:
    from grabtl.core.ocr.base import OCREngine
    from grabtl.core.translation.base import Translator


@dataclass
class TranslationResult:
    """パイプラインの実行結果。"""

    ocr_result: OCRResult
    translated_text: str


class Pipeline:
    """OCR → 翻訳を一連の処理として実行するパイプライン。"""

    def __init__(self, ocr_engine: OCREngine, translator: Translator) -> None:
        self._ocr_engine = ocr_engine
        self._translator = translator

    def run(
        self,
        image: bytes,
        source_lang: str = "en",
        target_lang: str = "ja",
    ) -> TranslationResult:
        """画像から OCR → 翻訳を実行する。

        Args:
            image: PNG 形式の画像バイト列。
            source_lang: ソース言語コード。
            target_lang: ターゲット言語コード。

        Returns:
            OCR 結果と翻訳テキストを含む結果。
        """
        ocr_result = self._ocr_engine.recognize(image, lang=source_lang)

        if not ocr_result.text.strip():
            return TranslationResult(ocr_result=ocr_result, translated_text="")

        translated = self._translator.translate(
            ocr_result.text, source=source_lang, target=target_lang
        )

        return TranslationResult(ocr_result=ocr_result, translated_text=translated)
