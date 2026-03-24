"""CachedTranslator のテスト。"""

from __future__ import annotations

from grabtl.core.translation.cache import CachedTranslator


class _CountingTranslator:
    """翻訳呼び出し回数を記録するテスト用 Translator。"""

    def __init__(self) -> None:
        self.call_count = 0

    def translate(self, text: str, source: str, target: str) -> str:
        self.call_count += 1
        return f"[{target}]{text}"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def is_local(self) -> bool:
        return True

    @property
    def allowed_endpoints(self) -> list[str]:
        return []


class TestCachedTranslator:
    def test_Protocolに準拠(self) -> None:
        from grabtl.core.translation.base import Translator

        cached = CachedTranslator(_CountingTranslator())
        assert isinstance(cached, Translator)

    def test_同じテキストはキャッシュから返す(self) -> None:
        inner = _CountingTranslator()
        cached = CachedTranslator(inner)

        r1 = cached.translate("Hello", "en", "ja")
        r2 = cached.translate("Hello", "en", "ja")

        assert r1 == r2
        assert inner.call_count == 1  # 2回目はキャッシュヒット

    def test_異なるテキストは別々に翻訳(self) -> None:
        inner = _CountingTranslator()
        cached = CachedTranslator(inner)

        cached.translate("Hello", "en", "ja")
        cached.translate("World", "en", "ja")

        assert inner.call_count == 2

    def test_言語ペアが異なればキャッシュミス(self) -> None:
        inner = _CountingTranslator()
        cached = CachedTranslator(inner)

        cached.translate("Hello", "en", "ja")
        cached.translate("Hello", "en", "ko")

        assert inner.call_count == 2

    def test_LRUで古いエントリが破棄される(self) -> None:
        inner = _CountingTranslator()
        cached = CachedTranslator(inner, max_size=2)

        cached.translate("A", "en", "ja")
        cached.translate("B", "en", "ja")
        cached.translate("C", "en", "ja")  # A が破棄される

        assert cached.cache_size == 2

        # A は破棄されたので再翻訳
        cached.translate("A", "en", "ja")
        assert inner.call_count == 4

    def test_空テキストはキャッシュしない(self) -> None:
        inner = _CountingTranslator()
        cached = CachedTranslator(inner)

        cached.translate("", "en", "ja")
        cached.translate("   ", "en", "ja")

        assert cached.cache_size == 0
        assert inner.call_count == 0

    def test_clear_cacheでキャッシュをクリア(self) -> None:
        inner = _CountingTranslator()
        cached = CachedTranslator(inner)

        cached.translate("Hello", "en", "ja")
        assert cached.cache_size == 1

        cached.clear_cache()
        assert cached.cache_size == 0

    def test_プロパティが内部translatorに委譲される(self) -> None:
        cached = CachedTranslator(_CountingTranslator())
        assert cached.requires_api_key is False
        assert cached.is_local is True
        assert cached.allowed_endpoints == []
