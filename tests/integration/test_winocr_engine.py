"""WinOCREngine の実機テスト。

Windows + 英語 OCR 言語パックが必要。
CI (Ubuntu) ではスキップされる。
"""

from __future__ import annotations

import io
import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows 専用テスト")

# PIL は Windows/Linux 両方で import 可能だが、テスト実行時のみ使う
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


class TestWinOCREngine:
    def test_英語テキストを認識できる(self) -> None:
        from grabtl.core.ocr.winocr_engine import WinOCREngine

        engine = WinOCREngine()
        image = _create_test_image("Hello World")
        result = engine.recognize(image, lang="en")

        assert "Hello" in result.text
        assert result.lang == "en"

    def test_空白画像は空テキストを返す(self) -> None:
        from grabtl.core.ocr.winocr_engine import WinOCREngine

        engine = WinOCREngine()
        # 真っ白な画像
        img = Image.new("RGB", (200, 50), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        result = engine.recognize(buf.getvalue(), lang="en")

        assert result.text.strip() == ""

    def test_OCRResultのフィールドが正しく設定される(self) -> None:
        from grabtl.core.ocr.winocr_engine import WinOCREngine

        engine = WinOCREngine()
        image = _create_test_image("Test 123")
        result = engine.recognize(image, lang="en")

        assert isinstance(result.text, str)
        assert isinstance(result.confidence, float)
        assert result.lang == "en"
        # bounding_boxes はテキストがあれば設定される
        if result.text.strip():
            assert result.bounding_boxes is not None
            assert len(result.bounding_boxes) > 0
            box = result.bounding_boxes[0]
            assert "x" in box
            assert "y" in box
            assert "width" in box
            assert "height" in box

    def test_エンジン名とプロパティ(self) -> None:
        from grabtl.core.ocr.winocr_engine import WinOCREngine

        engine = WinOCREngine()
        assert engine.name == "Windows OCR"
        assert "en" in engine.available_languages()

    def test_Protocolに準拠している(self) -> None:
        from grabtl.core.ocr.base import OCREngine
        from grabtl.core.ocr.winocr_engine import WinOCREngine

        engine = WinOCREngine()
        assert isinstance(engine, OCREngine)
