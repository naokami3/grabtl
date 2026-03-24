"""DeepL API を使った翻訳エンジン実装。

Tier 2a: API キー必要（BYOK）、最高品質の翻訳。
Free プラン（月 50 万文字）と Pro プランを自動判別。
"""

from __future__ import annotations

import requests

from grabtl.core.translation._http import create_session, post_json
from grabtl.core.translation.exceptions import (
    ConnectionFailedError,
    InvalidApiKeyError,
    TextTooLongError,
)

_DEEPL_LANG_MAP: dict[str, str] = {
    "en": "EN",
    "ja": "JA",
    "zh": "ZH",
    "ko": "KO",
    "de": "DE",
    "fr": "FR",
    "es": "ES",
    "pt": "PT-BR",
    "ru": "RU",
}

_PROVIDER = "DeepL"
_MAX_CHARS = 2000


class DeepLTranslator:
    """DeepL API による翻訳。

    Tier 2a: API キー必要、最高品質。
    キー末尾が ':fx' なら Free プラン、それ以外は Pro プラン。
    """

    def __init__(self, api_key: str, timeout: float = 10.0) -> None:
        if not api_key:
            msg = "DeepL API キーが設定されていません。設定画面で入力してください。"
            raise InvalidApiKeyError(msg, provider=_PROVIDER)
        self._api_key = api_key
        self._timeout = timeout
        self._session = create_session(
            headers={"Authorization": f"DeepL-Auth-Key {api_key}"},
        )

    @property
    def _api_base(self) -> str:
        if self._api_key.endswith(":fx"):
            return "https://api-free.deepl.com"
        return "https://api.deepl.com"

    def translate(self, text: str, source: str, target: str) -> str:
        """テキストを翻訳する。"""
        if not text.strip():
            return ""
        if len(text) > _MAX_CHARS:
            msg = f"テキストが長すぎます（{len(text)} 文字）。上限は {_MAX_CHARS} 文字です。"
            raise TextTooLongError(msg, provider=_PROVIDER)

        source_lang = _DEEPL_LANG_MAP.get(source, source.upper())
        target_lang = _DEEPL_LANG_MAP.get(target, target.upper())

        try:
            result = post_json(
                self._session,
                f"{self._api_base}/v2/translate",
                {"text": [text], "source_lang": source_lang, "target_lang": target_lang},
                self._timeout,
                provider=_PROVIDER,
            )
        except requests.exceptions.ConnectionError as e:
            raise ConnectionFailedError(
                "DeepL に接続できません。インターネット接続を確認してください。",
                provider=_PROVIDER,
            ) from e

        translations = result.get("translations", [])
        if translations:
            return translations[0].get("text", "").strip()  # type: ignore[no-any-return]
        return ""

    @property
    def requires_api_key(self) -> bool:
        return True

    @property
    def is_local(self) -> bool:
        return False

    @property
    def allowed_endpoints(self) -> list[str]:
        return ["api-free.deepl.com", "api.deepl.com"]
