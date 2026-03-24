"""DeepLTranslator のテスト。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from grabtl.core.translation.deepl import DeepLTranslator
from grabtl.core.translation.exceptions import InvalidApiKeyError, TextTooLongError


class TestDeepLTranslator:
    def test_Protocolに準拠(self) -> None:
        from grabtl.core.translation.base import Translator

        translator = DeepLTranslator(api_key="test-key:fx")
        assert isinstance(translator, Translator)

    def test_プロパティ(self) -> None:
        translator = DeepLTranslator(api_key="test-key:fx")
        assert translator.requires_api_key is True
        assert translator.is_local is False
        assert "api-free.deepl.com" in translator.allowed_endpoints

    def test_Freeキーの判別(self) -> None:
        translator = DeepLTranslator(api_key="test-key:fx")
        assert translator._api_base == "https://api-free.deepl.com"

    def test_Proキーの判別(self) -> None:
        translator = DeepLTranslator(api_key="test-key-pro")
        assert translator._api_base == "https://api.deepl.com"

    def test_空キーでInvalidApiKeyError(self) -> None:
        with pytest.raises(InvalidApiKeyError):
            DeepLTranslator(api_key="")

    def test_空テキストは空文字列を返す(self) -> None:
        translator = DeepLTranslator(api_key="test-key:fx")
        assert translator.translate("", "en", "ja") == ""

    def test_長すぎるテキストでTextTooLongError(self) -> None:
        translator = DeepLTranslator(api_key="test-key:fx")
        with pytest.raises(TextTooLongError):
            translator.translate("x" * 2001, "en", "ja")

    def test_翻訳リクエストが正しく処理される(self) -> None:
        translator = DeepLTranslator(api_key="test-key:fx")
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "translations": [{"text": "こんにちは世界"}],
        }

        with patch.object(translator._session, "post", return_value=mock_response):
            result = translator.translate("Hello world", "en", "ja")

        assert result == "こんにちは世界"
