"""Translator Protocol のテスト。"""

from __future__ import annotations

from grabtl.core.translation.base import Translator


class FakeTranslator:
    """テスト用の翻訳エンジン。"""

    def translate(self, text: str, source: str, target: str) -> str:
        return f"[{target}] {text}"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def is_local(self) -> bool:
        return True

    @property
    def allowed_endpoints(self) -> list[str]:
        return []


class TestTranslator:
    def test_Protocolに準拠(self) -> None:
        translator = FakeTranslator()
        assert isinstance(translator, Translator)

    def test_translate(self) -> None:
        translator = FakeTranslator()
        result = translator.translate("Hello", source="en", target="ja")
        assert result == "[ja] Hello"

    def test_requires_api_key(self) -> None:
        translator = FakeTranslator()
        assert translator.requires_api_key is False

    def test_is_local(self) -> None:
        translator = FakeTranslator()
        assert translator.is_local is True

    def test_allowed_endpoints(self) -> None:
        translator = FakeTranslator()
        assert translator.allowed_endpoints == []
