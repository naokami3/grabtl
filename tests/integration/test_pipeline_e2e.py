"""パイプライン結合テスト（実機）。

Windows + 英語 OCR 言語パック + argostranslate en→ja モデルが必要。
CI (Ubuntu) ではスキップされる。
"""

from __future__ import annotations

import io
import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows 専用テスト")

PIL = pytest.importorskip("PIL", reason="Pillow が必要")
from PIL import Image, ImageDraw, ImageFont  # noqa: E402


def _create_test_image(text: str, width: int = 400, height: int = 80) -> bytes:
    """テスト用にテキストを描画した PNG 画像を生成する。"""
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except OSError:
        font = ImageFont.load_default(size=32)
    draw.text((10, 10), text, fill="black", font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestPipelineE2E:
    """OCR → 翻訳のフルパイプラインテスト。"""

    @pytest.fixture
    def pipeline(self):  # noqa: ANN201
        from grabtl.core.translation._dll_fix import preload_system_vcrt

        preload_system_vcrt()

        from grabtl.core.ocr.winocr_engine import WinOCREngine
        from grabtl.core.pipeline import Pipeline
        from grabtl.core.translation.argos import ArgosTranslator

        return Pipeline(ocr_engine=WinOCREngine(), translator=ArgosTranslator())

    def test_英語テキストを日本語に翻訳できる(self, pipeline) -> None:  # noqa: ANN001
        image = _create_test_image("Hello")
        result = pipeline.run(image, source_lang="en", target_lang="ja")

        assert result.ocr_result.text.strip() != ""
        assert result.translated_text.strip() != ""
        # 翻訳結果が元の英語テキストとは異なること（実際に翻訳された証拠）
        assert result.translated_text != result.ocr_result.text

    def test_空白画像は空の翻訳結果を返す(self, pipeline) -> None:  # noqa: ANN001
        img = Image.new("RGB", (200, 50), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        result = pipeline.run(buf.getvalue(), source_lang="en", target_lang="ja")

        assert result.translated_text == ""
