"""Google Gemini API を使った翻訳エンジン実装。

Tier 2c: API キー必要（BYOK）。LLM ベースの高品質翻訳。
ヘッダー認証（x-goog-api-key）を使用し、URL にキーを露出しない。
"""

from __future__ import annotations

from typing import Any

import requests

from grabtl.core.translation._http import create_session, post_json
from grabtl.core.translation._llm_utils import LANG_MAP, SYSTEM_PROMPT, clean_response
from grabtl.core.translation.exceptions import (
    ConnectionFailedError,
    InvalidApiKeyError,
    TextTooLongError,
)

_PROVIDER = "Gemini"
_MAX_CHARS = 2000
_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiTranslator:
    """Google Gemini API による翻訳。

    Tier 2c: API キー必要、LLM ベースの高品質翻訳。
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        timeout: float = 30.0,
    ) -> None:
        if not api_key:
            msg = "Gemini API キーが設定されていません。設定画面で入力してください。"
            raise InvalidApiKeyError(msg, provider=_PROVIDER)
        self._model = model
        self._timeout = timeout
        # ヘッダー認証: URL にキーを含めない
        self._session = create_session(
            headers={"x-goog-api-key": api_key},
        )

    def translate(self, text: str, source: str, target: str) -> str:
        """テキストを翻訳する。"""
        if not text.strip():
            return ""
        if len(text) > _MAX_CHARS:
            msg = f"テキストが長すぎます（{len(text)} 文字）。上限は {_MAX_CHARS} 文字です。"
            raise TextTooLongError(msg, provider=_PROVIDER)

        target_name = LANG_MAP.get(target, target)
        source_name = LANG_MAP.get(source, source)
        system = SYSTEM_PROMPT.format(target_name=target_name)

        payload: dict[str, Any] = {
            "system_instruction": {
                "parts": [{"text": system}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": f"Translate from {source_name} to {target_name}:\n{text}",
                        },
                    ],
                },
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1000,
            },
        }

        try:
            result = post_json(
                self._session,
                f"{_API_BASE}/models/{self._model}:generateContent",
                payload,
                self._timeout,
                provider=_PROVIDER,
            )
        except requests.exceptions.ConnectionError as e:
            raise ConnectionFailedError(
                "Gemini に接続できません。インターネット接続を確認してください。",
                provider=_PROVIDER,
            ) from e

        candidates = result.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                raw = parts[0].get("text", "")
                return clean_response(raw)
        return ""

    @property
    def requires_api_key(self) -> bool:
        return True

    @property
    def is_local(self) -> bool:
        return False

    @property
    def allowed_endpoints(self) -> list[str]:
        return ["generativelanguage.googleapis.com"]
