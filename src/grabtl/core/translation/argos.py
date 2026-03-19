"""argostranslate を使ったオフライン翻訳エンジン実装。"""

from __future__ import annotations

from typing import Any


class ArgosTranslator:
    """argostranslate によるオフライン翻訳。

    Tier 0: API キー不要、ネットワーク通信なし。
    """

    def __init__(self) -> None:
        try:
            import argostranslate.translate as _translate  # type: ignore[import-not-found]
        except ImportError:
            msg = "argostranslate がインストールされていません: pip install argostranslate"
            raise ImportError(msg) from None  # noqa: B904
        self._translate: Any = _translate

    def translate(self, text: str, source: str, target: str) -> str:
        """テキストを翻訳する。

        Args:
            text: 翻訳対象のテキスト。
            source: ソース言語コード（例: "en"）。
            target: ターゲット言語コード（例: "ja"）。

        Returns:
            翻訳されたテキスト。

        Raises:
            RuntimeError: 対応する言語パッケージがインストールされていない場合。
        """
        if not text.strip():
            return ""

        installed_languages = self._translate.get_installed_languages()

        source_lang = None
        target_lang = None
        for lang in installed_languages:
            if lang.code == source:
                source_lang = lang
            if lang.code == target:
                target_lang = lang

        if source_lang is None or target_lang is None:
            missing = []
            if source_lang is None:
                missing.append(source)
            if target_lang is None:
                missing.append(target)
            msg = (
                f"言語パッケージが見つかりません: {', '.join(missing)}。"
                f"argospm でインストールしてください"
            )
            raise RuntimeError(msg)

        translation = source_lang.get_translation(target_lang)
        if translation is None:
            msg = f"翻訳ペア {source} → {target} が利用できません"
            raise RuntimeError(msg)

        result: str = translation.translate(text)
        return result

    @property
    def requires_api_key(self) -> bool:
        """API キーは不要。"""
        return False

    @property
    def is_local(self) -> bool:
        """ローカル実行。"""
        return True

    @property
    def allowed_endpoints(self) -> list[str]:
        """通信先なし。"""
        return []
