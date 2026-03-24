"""ChatGPTTranslator のテスト。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from grabtl.core.translation.chatgpt import ChatGPTTranslator
from grabtl.core.translation.exceptions import InvalidApiKeyError, TextTooLongError


class TestChatGPTTranslator:
    def test_Protocolに準拠(self) -> None:
        from grabtl.core.translation.base import Translator

        translator = ChatGPTTranslator(api_key="sk-test")
        assert isinstance(translator, Translator)

    def test_プロパティ(self) -> None:
        translator = ChatGPTTranslator(api_key="sk-test")
        assert translator.requires_api_key is True
        assert translator.is_local is False
        assert "api.openai.com" in translator.allowed_endpoints

    def test_空キーでInvalidApiKeyError(self) -> None:
        with pytest.raises(InvalidApiKeyError):
            ChatGPTTranslator(api_key="")

    def test_空テキストは空文字列を返す(self) -> None:
        translator = ChatGPTTranslator(api_key="sk-test")
        assert translator.translate("", "en", "ja") == ""

    def test_長すぎるテキストでTextTooLongError(self) -> None:
        translator = ChatGPTTranslator(api_key="sk-test")
        with pytest.raises(TextTooLongError):
            translator.translate("x" * 2001, "en", "ja")

    def test_翻訳リクエストが正しく処理される(self) -> None:
        translator = ChatGPTTranslator(api_key="sk-test")
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "こんにちは世界"}}],
        }

        with patch.object(translator._session, "post", return_value=mock_response):
            result = translator.translate("Hello world", "en", "ja")

        assert result == "こんにちは世界"

    def test_レスポンスクリーニングが適用される(self) -> None:
        translator = ChatGPTTranslator(api_key="sk-test")
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Translation: こんにちは世界"}}],
        }

        with patch.object(translator._session, "post", return_value=mock_response):
            result = translator.translate("Hello world", "en", "ja")

        assert result == "こんにちは世界"
