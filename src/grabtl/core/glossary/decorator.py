"""Translator を Glossary でラップするデコレータ。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from grabtl.core.glossary.manager import Glossary
    from grabtl.core.translation.base import Translator


class GlossaryTranslator:
    """Translator を Glossary で装飾するデコレータ。

    Translator Protocol を満たすため、Pipeline にそのまま渡せる。
    翻訳の前後に用語辞書の置換処理を適用する。
    """

    def __init__(self, translator: Translator, glossary: Glossary) -> None:
        self._translator = translator
        self._glossary = glossary

    def translate(self, text: str, source: str, target: str) -> str:
        """用語辞書を適用しながら翻訳する。"""
        text = self._glossary.pre_translate(text)
        result = self._translator.translate(text, source=source, target=target)
        return self._glossary.post_translate(result)

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
