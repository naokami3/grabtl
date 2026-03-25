"""GeminiTranslator のテスト。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from grabtl.core.translation.exceptions import InvalidApiKeyError, TextTooLongError
from grabtl.core.translation.gemini import GeminiTranslator


class TestGeminiTranslator:
    def test_Protocolに準拠(self) -> None:
        from grabtl.core.translation.base import Translator

        translator = GeminiTranslator(api_key="AIzaSy-test")
        assert isinstance(translator, Translator)

    def test_プロパティ(self) -> None:
        translator = GeminiTranslator(api_key="AIzaSy-test")
        assert translator.requires_api_key is True
        assert translator.is_local is False
        assert "generativelanguage.googleapis.com" in translator.allowed_endpoints

    def test_空キーでInvalidApiKeyError(self) -> None:
        with pytest.raises(InvalidApiKeyError):
            GeminiTranslator(api_key="")

    def test_空テキストは空文字列を返す(self) -> None:
        translator = GeminiTranslator(api_key="AIzaSy-test")
        assert translator.translate("", "en", "ja") == ""

    def test_長すぎるテキストでTextTooLongError(self) -> None:
        translator = GeminiTranslator(api_key="AIzaSy-test")
        with pytest.raises(TextTooLongError):
            translator.translate("x" * 2001, "en", "ja")

    def test_翻訳リクエストが正しく処理される(self) -> None:
        translator = GeminiTranslator(api_key="AIzaSy-test")
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "こんにちは世界"}]}}],
        }

        with patch.object(translator._session, "post", return_value=mock_response):
            result = translator.translate("Hello world", "en", "ja")

        assert result == "こんにちは世界"

    def test_ヘッダー認証を使用しURLにキーを含めない(self) -> None:
        translator = GeminiTranslator(api_key="AIzaSy-test")
        # Session のヘッダーに API キーが設定されていること
        assert translator._session.headers.get("x-goog-api-key") == "AIzaSy-test"
