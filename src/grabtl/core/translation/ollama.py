"""Ollama REST API を使った LLM 翻訳エンジン実装。

Tier 1: API キー不要、ローカル LLM で高品質翻訳。
Ollama のインストールとモデルのダウンロードが必要。
デフォルトモデル: qwen2.5:3b（Apache 2.0、VRAM 2GB）
"""

from __future__ import annotations

from typing import Any

import requests

from grabtl.core.translation._http import create_session, get_json, post_json
from grabtl.core.translation._llm_utils import LANG_MAP, SYSTEM_PROMPT, clean_response
from grabtl.core.translation.exceptions import ConnectionFailedError

_PROVIDER = "Ollama"


class OllamaTranslator:
    """Ollama REST API による LLM 翻訳。

    Tier 1: API キー不要、Ollama インストールが必要。
    """

    def __init__(
        self,
        model: str = "qwen2.5:3b",
        host: str = "127.0.0.1",
        port: int = 11434,
        timeout: float = 60.0,
    ) -> None:
        if host not in ("127.0.0.1", "localhost", "::1"):
            msg = f"セキュリティ上、Ollama の接続先は localhost に限定されています: {host}"
            raise ValueError(msg)

        self._model = model
        self._base_url = f"http://{host}:{port}"
        self._timeout = timeout

        # localhost 通信はプロキシを使わない（trust_env=False）
        self._session = create_session(trust_env=False)

    def translate(self, text: str, source: str, target: str) -> str:
        """テキストを翻訳する。

        Raises:
            ConnectionFailedError: Ollama サーバーに接続できない場合。
            EngineNotReadyError: モデルが見つからない場合。
        """
        if not text.strip():
            return ""

        target_name = LANG_MAP.get(target, target)
        source_name = LANG_MAP.get(source, source)

        system = SYSTEM_PROMPT.format(target_name=target_name)
        user_msg = f"Translate from {source_name} to {target_name}:\n{text}"

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
            },
        }

        try:
            result = post_json(
                self._session,
                f"{self._base_url}/api/chat",
                payload,
                self._timeout,
                provider=_PROVIDER,
            )
        except requests.exceptions.ConnectionError as e:
            raise ConnectionFailedError(
                "Ollama が起動していません。'ollama serve' を実行してください。",
                provider=_PROVIDER,
            ) from e

        raw = result.get("message", {}).get("content", "")
        return clean_response(raw)

    def is_available(self) -> bool:
        """Ollama サーバーが起動しているかチェックする。"""
        try:
            get_json(
                self._session,
                f"{self._base_url}/api/tags",
                timeout=5.0,
                provider=_PROVIDER,
            )
        except Exception:
            return False
        return True

    def is_model_available(self) -> bool:
        """指定モデルがダウンロード済みかチェックする。"""
        try:
            tags = get_json(
                self._session,
                f"{self._base_url}/api/tags",
                timeout=5.0,
                provider=_PROVIDER,
            )
            models = [m["name"] for m in tags.get("models", [])]
            return any(
                m == self._model or m.startswith(self._model.split(":")[0] + ":")
                for m in models
            )
        except Exception:
            return False

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
        """通信先なし（localhost はカウントしない）。"""
        return []
