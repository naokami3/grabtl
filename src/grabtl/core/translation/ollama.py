"""Ollama REST API を使った LLM 翻訳エンジン実装。

Tier 1: API キー不要、ローカル LLM で高品質翻訳。
Ollama のインストールとモデルのダウンロードが必要。
デフォルトモデル: qwen2.5:3b（Apache 2.0、VRAM 2GB）
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class OllamaConnectionError(RuntimeError):
    """Ollama サーバーに接続できない。"""


class OllamaModelNotFoundError(RuntimeError):
    """指定されたモデルが見つからない。"""


_LANG_MAP: dict[str, str] = {
    "en": "English",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "pt": "Portuguese",
    "ru": "Russian",
}

_SYSTEM_PROMPT = (
    "You are a translator for a video game. "
    "Translate the following text into {target_name}. "
    "Output ONLY the translated text, nothing else. "
    "Do not add explanations, notes, or alternatives."
)

_PREFIXES_TO_STRIP = [
    "Translation:",
    "Translated text:",
    "Here is the translation:",
    "翻訳:",
    "翻訳結果:",
]


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

        # プロキシバイパス: localhost 通信がプロキシを経由しないようにする
        no_proxy_handler = urllib.request.ProxyHandler({})
        self._opener = urllib.request.build_opener(no_proxy_handler)

    def translate(self, text: str, source: str, target: str) -> str:
        """テキストを翻訳する。

        Args:
            text: 翻訳対象のテキスト。
            source: ソース言語コード（例: "en"）。
            target: ターゲット言語コード（例: "ja"）。

        Returns:
            翻訳されたテキスト。

        Raises:
            OllamaConnectionError: Ollama サーバーに接続できない場合。
            OllamaModelNotFoundError: 指定モデルが見つからない場合。
        """
        if not text.strip():
            return ""

        target_name = _LANG_MAP.get(target, target)
        source_name = _LANG_MAP.get(source, source)

        system = _SYSTEM_PROMPT.format(target_name=target_name)
        user_msg = f"Translate from {source_name} to {target_name}:\n{text}"

        payload = {
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

        result = self._post_json(f"{self._base_url}/api/chat", payload)
        raw = result.get("message", {}).get("content", "")
        return self._clean_response(raw)

    def is_available(self) -> bool:
        """Ollama サーバーが起動しているかチェックする。"""
        try:
            self._get_json(f"{self._base_url}/api/tags", timeout=5.0)
        except Exception:
            return False
        return True

    def is_model_available(self) -> bool:
        """指定モデルがダウンロード済みかチェックする。"""
        try:
            tags = self._get_json(f"{self._base_url}/api/tags", timeout=5.0)
            models = [m["name"] for m in tags.get("models", [])]
            return any(
                m == self._model or m.startswith(self._model.split(":")[0] + ":")
                for m in models
            )
        except Exception:
            return False

    def _post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        """JSON POST リクエストを送信する。"""
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(  # noqa: S310 -- URL は localhost に限定済み
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._opener.open(req, timeout=self._timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))  # type: ignore[no-any-return]
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise OllamaModelNotFoundError(
                    f"モデル '{self._model}' が見つかりません。"
                    f"'ollama pull {self._model}' を実行してください。"
                ) from e
            body = e.read().decode("utf-8", errors="replace")
            msg = f"Ollama API エラー {e.code}: {body}"
            raise RuntimeError(msg) from e
        except urllib.error.URLError as e:
            if isinstance(e.reason, ConnectionRefusedError):
                raise OllamaConnectionError(
                    "Ollama が起動していません。'ollama serve' を実行してください。"
                ) from e
            raise OllamaConnectionError(f"Ollama に接続できません: {e.reason}") from e

    def _get_json(self, url: str, timeout: float = 5.0) -> dict[str, Any]:
        """JSON GET リクエストを送信する。"""
        req = urllib.request.Request(url, method="GET")  # noqa: S310
        try:
            with self._opener.open(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))  # type: ignore[no-any-return]
        except urllib.error.URLError as e:
            if isinstance(e.reason, ConnectionRefusedError):
                raise OllamaConnectionError(
                    "Ollama が起動していません。'ollama serve' を実行してください。"
                ) from e
            raise

    @staticmethod
    def _clean_response(raw: str) -> str:
        """LLM レスポンスから翻訳テキストのみを抽出する。"""
        text = raw.strip()

        # よくあるプレフィックスを除去
        for prefix in _PREFIXES_TO_STRIP:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix) :].strip()

        # 引用符を除去
        if len(text) >= 2 and (
            (text[0] == '"' and text[-1] == '"')
            or (text[0] == "'" and text[-1] == "'")
            or (text[0] == "「" and text[-1] == "」")
        ):
            text = text[1:-1].strip()

        # "Note:" "Explanation:" 行を除去
        lines = text.split("\n")
        filtered = []
        for line in lines:
            lower = line.strip().lower()
            if lower.startswith(("note:", "explanation:", "original:", "(note")):
                continue
            filtered.append(line)
        text = "\n".join(filtered).strip()

        return text if text else raw.strip()

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
