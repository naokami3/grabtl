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


def _create_game_chat_image(messages: list[str]) -> bytes:
    """ゲームチャット風の画像を生成する。

    暗い背景に白文字で複数行のチャットメッセージを描画する。
    """
    line_height = 28
    padding = 10
    width = 500
    height = padding * 2 + line_height * len(messages)

    img = Image.new("RGB", (width, height), color=(20, 20, 30))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        font = ImageFont.load_default(size=18)

    for i, msg in enumerate(messages):
        y = padding + i * line_height
        draw.text((padding, y), msg, fill=(220, 220, 220), font=font)

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

    def test_ゲームチャット風画像からテキストを認識できる(self) -> None:
        from grabtl.core.ocr.winocr_engine import WinOCREngine

        engine = WinOCREngine()
        image = _create_game_chat_image([
            "Player1: Anyone want to raid?",
            "Player2: Sure, invite me",
            "Player3: Looking for healer",
        ])
        result = engine.recognize(image, lang="en")

        # チャットメッセージの主要な単語が認識されること
        text_lower = result.text.lower()
        assert "raid" in text_lower or "player" in text_lower or "invite" in text_lower

    def test_複数行チャットが複数行として認識される(self) -> None:
        from grabtl.core.ocr.winocr_engine import WinOCREngine

        engine = WinOCREngine()
        image = _create_game_chat_image([
            "Hello World",
            "Good Morning",
        ])
        result = engine.recognize(image, lang="en")

        # 複数行として認識されること（改行が含まれる）
        assert "\n" in result.text
