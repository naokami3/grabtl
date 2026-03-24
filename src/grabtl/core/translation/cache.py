"""翻訳キャッシュデコレータ。

同一テキストの再翻訳を回避し、API コスト削減とレスポンス高速化を実現する。
LRU キャッシュで最大エントリ数を制限する。
"""

from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from grabtl.core.translation.base import Translator

_DEFAULT_MAX_SIZE = 500


class CachedTranslator:
    """Translator をキャッシュでラップするデコレータ。

    Translator Protocol を満たすため、Pipeline にそのまま渡せる。
    キャッシュキーは (text, source, target) のタプル。
    LRU 方式で古いエントリから破棄する。
    """

    def __init__(self, translator: Translator, max_size: int = _DEFAULT_MAX_SIZE) -> None:
        self._translator = translator
        self._max_size = max_size
        self._cache: OrderedDict[tuple[str, str, str], str] = OrderedDict()

    def translate(self, text: str, source: str, target: str) -> str:
        """キャッシュを参照し、ヒットすればキャッシュから返す。"""
        if not text.strip():
            return ""

        key = (text, source, target)

        # キャッシュヒット
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]

        # キャッシュミス → 翻訳実行
        result = self._translator.translate(text, source=source, target=target)

        # キャッシュに追加
        self._cache[key] = result
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

        return result

    @property
    def cache_size(self) -> int:
        """現在のキャッシュエントリ数。"""
        return len(self._cache)

    def clear_cache(self) -> None:
        """キャッシュをクリアする。"""
        self._cache.clear()

    @property
    def requires_api_key(self) -> bool:
        """内部 translator に委譲。"""
        return self._translator.requires_api_key

    @property
    def is_local(self) -> bool:
        """内部 translator に委譲。"""
        return self._translator.is_local

    @property
    def allowed_endpoints(self) -> list[str]:
        """内部 translator に委譲。"""
        return self._translator.allowed_endpoints
