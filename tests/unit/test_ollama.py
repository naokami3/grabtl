"""OllamaTranslator のテスト。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from grabtl.core.translation._llm_utils import clean_response
from grabtl.core.translation.exceptions import ConnectionFailedError
from grabtl.core.translation.ollama import OllamaTranslator


class TestOllamaTranslator:
    def test_Protocolに準拠(self) -> None:
        from grabtl.core.translation.base import Translator

        translator = OllamaTranslator()
        assert isinstance(translator, Translator)

    def test_プロパティ(self) -> None:
        translator = OllamaTranslator()
        assert translator.requires_api_key is False
        assert translator.is_local is True
        assert translator.allowed_endpoints == []

    def test_localhost以外はValueError(self) -> None:
        with pytest.raises(ValueError, match="localhost に限定"):
            OllamaTranslator(host="evil.com")

    def test_127_0_0_1は許可(self) -> None:
        t = OllamaTranslator(host="127.0.0.1")
        assert t._base_url == "http://127.0.0.1:11434"

    def test_localhostは許可(self) -> None:
        t = OllamaTranslator(host="localhost")
        assert t._base_url == "http://localhost:11434"

    def test_空テキストは空文字列を返す(self) -> None:
        translator = OllamaTranslator()
        assert translator.translate("", "en", "ja") == ""
        assert translator.translate("   ", "en", "ja") == ""


class TestOllamaTranslatorWithMock:
    def test_翻訳リクエストが正しく送信される(self) -> None:
        translator = OllamaTranslator()

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "message": {"role": "assistant", "content": "こんにちは世界"},
            "done": True,
        }

        with patch.object(translator._session, "post", return_value=mock_response):
            result = translator.translate("Hello world", "en", "ja")

        assert result == "こんにちは世界"

    def test_Ollama未起動時にConnectionFailedError(self) -> None:
        translator = OllamaTranslator()

        with (
            patch.object(
                translator._session,
                "post",
                side_effect=requests.exceptions.ConnectionError("Connection refused"),
            ),
            pytest.raises(ConnectionFailedError, match="起動していません"),
        ):
            translator.translate("Hello", "en", "ja")


class TestCleanResponse:
    def test_プレフィックス除去(self) -> None:
        assert clean_response("Translation: こんにちは") == "こんにちは"
        assert clean_response("翻訳: こんにちは") == "こんにちは"

    def test_大文字小文字を区別しない(self) -> None:
        assert clean_response("translation: こんにちは") == "こんにちは"

    def test_引用符除去(self) -> None:
        assert clean_response('"こんにちは"') == "こんにちは"
        assert clean_response("「こんにちは」") == "こんにちは"

    def test_Note行除去(self) -> None:
        text = "こんにちは\nNote: This is a greeting"
        assert clean_response(text) == "こんにちは"

    def test_複数行のNote除去(self) -> None:
        text = "こんにちは世界\nExplanation: hello means...\nOriginal: Hello world"
        assert clean_response(text) == "こんにちは世界"

    def test_正常なテキストはそのまま(self) -> None:
        assert clean_response("こんにちは世界") == "こんにちは世界"

    def test_空文字列は元テキストを返す(self) -> None:
        assert clean_response("  ") == ""
