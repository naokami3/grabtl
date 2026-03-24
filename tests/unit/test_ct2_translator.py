"""CT2Translator のテスト。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from grabtl.core.translation.ct2_translator import CT2Translator


class TestCT2Translator:
    def test_Protocolに準拠(self) -> None:
        from grabtl.core.translation.base import Translator

        translator = CT2Translator(model_dir="/dummy")
        assert isinstance(translator, Translator)

    def test_プロパティ(self) -> None:
        translator = CT2Translator(model_dir="/dummy")
        assert translator.requires_api_key is False
        assert translator.is_local is True
        assert translator.allowed_endpoints == []

    def test_空テキストは空文字列を返す(self) -> None:
        translator = CT2Translator(model_dir="/dummy")
        assert translator.translate("", "en", "ja") == ""
        assert translator.translate("   ", "en", "ja") == ""

    def test_モデル未インストール時にFileNotFoundError(self) -> None:
        translator = CT2Translator(model_dir="/nonexistent/path")
        with pytest.raises(FileNotFoundError, match="翻訳モデルが見つかりません"):
            translator.translate("Hello", "en", "ja")


class TestCT2TranslatorWithMock:
    def test_翻訳リクエストが正しく処理される(self) -> None:
        translator = CT2Translator(model_dir="/dummy")

        mock_ct2 = MagicMock()
        mock_result = MagicMock()
        mock_result.hypotheses = [["こんにちは", "世界"]]
        mock_ct2.translate_batch.return_value = [mock_result]

        mock_sp = MagicMock()
        mock_sp.encode.return_value = ["Hello", "world"]
        mock_sp.decode.return_value = "こんにちは世界"

        translator._translator = mock_ct2
        translator._sp = mock_sp
        translator._loaded = True

        result = translator.translate("Hello world", "en", "ja")
        assert result == "こんにちは世界"

    def test_複数文がバッチ翻訳される(self) -> None:
        translator = CT2Translator(model_dir="/dummy")

        mock_ct2 = MagicMock()
        mock_r1 = MagicMock()
        mock_r1.hypotheses = [["文1"]]
        mock_r2 = MagicMock()
        mock_r2.hypotheses = [["文2"]]
        mock_ct2.translate_batch.return_value = [mock_r1, mock_r2]

        mock_sp = MagicMock()
        mock_sp.encode.side_effect = [["Hello"], ["World"]]
        mock_sp.decode.side_effect = ["こんにちは", "世界"]

        translator._translator = mock_ct2
        translator._sp = mock_sp
        translator._loaded = True

        with patch(
            "grabtl.core.translation.ct2_translator.CT2Translator._split_sentences",
            return_value=["Hello.", "World."],
        ):
            result = translator.translate("Hello. World.", "en", "ja")

        assert "こんにちは" in result
        assert "世界" in result
        # translate_batch が2文を受け取ること
        mock_ct2.translate_batch.assert_called_once()
        args = mock_ct2.translate_batch.call_args[0][0]
        assert len(args) == 2


class TestSplitSentences:
    def test_単文は分割しない(self) -> None:
        result = CT2Translator(model_dir="/dummy")._split_sentences("Hello world")
        assert result == ["Hello world"]

    def test_複数文を分割する(self) -> None:
        result = CT2Translator(model_dir="/dummy")._split_sentences(
            "The dragon was spotted. Adventurers are needed."
        )
        assert len(result) == 2

    def test_略語で誤分割しない(self) -> None:
        result = CT2Translator(model_dir="/dummy")._split_sentences(
            "Dr. Smith found the artifact."
        )
        assert len(result) == 1
