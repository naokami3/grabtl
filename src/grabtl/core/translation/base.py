"""翻訳エンジンの Protocol 定義。"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Translator(Protocol):
    """翻訳エンジンが実装すべきインターフェース。"""

    def translate(self, text: str, source: str, target: str) -> str:
        """テキストを翻訳する。

        Args:
            text: 翻訳対象のテキスト。
            source: ソース言語コード（例: "en"）。
            target: ターゲット言語コード（例: "ja"）。

        Returns:
            翻訳されたテキスト。
        """
        ...

    @property
    def requires_api_key(self) -> bool:
        """API キーが必要かどうか。"""
        ...

    @property
    def is_local(self) -> bool:
        """ローカル実行かどうか。"""
        ...

    @property
    def allowed_endpoints(self) -> list[str]:
        """通信先ドメインの一覧。ローカルの場合は空リスト。"""
        ...
