"""翻訳エンジン共通の HTTP クライアント。

requests ベースの Session 管理とエラーハンドリングを提供する。

責務の分離:
- _http.py: HTTP レベルのエラー（ステータスコード）を翻訳例外に変換
- 各エンジン: ネットワークレベルのエラー（接続失敗等）を自分の文脈で処理
"""

from __future__ import annotations

from typing import Any

import requests

from grabtl.core.translation.exceptions import (
    InvalidApiKeyError,
    QuotaExceededError,
    RateLimitError,
    ServerError,
    TranslationTimeoutError,
)


def create_session(
    headers: dict[str, str] | None = None,
    trust_env: bool = True,
) -> requests.Session:
    """設定済みの requests Session を返す。

    Args:
        headers: デフォルトヘッダー（Authorization 等）。
        trust_env: False にするとプロキシ環境変数を無視する（localhost 通信用）。
    """
    session = requests.Session()
    session.trust_env = trust_env
    if headers:
        session.headers.update(headers)
    return session


def post_json(
    session: requests.Session,
    url: str,
    payload: dict[str, Any],
    timeout: float,
    *,
    provider: str = "",
) -> dict[str, Any]:
    """JSON POST リクエストを送信し、レスポンスを dict で返す。

    HTTP ステータスエラーは翻訳例外に変換する。
    ネットワークエラー（ConnectionError）はそのまま raise する。
    各エンジンが自分の文脈で catch して適切なメッセージを付ける。

    Raises:
        requests.exceptions.ConnectionError: サーバーに接続できない（各エンジンで catch）
        TranslationTimeoutError: タイムアウト
        InvalidApiKeyError: 401/403
        RateLimitError: 429
        QuotaExceededError: 456 (DeepL)
        ServerError: 500+
    """
    try:
        resp = session.post(url, json=payload, timeout=timeout)
    except requests.exceptions.Timeout as e:
        raise TranslationTimeoutError(
            f"{provider} へのリクエストがタイムアウトしました。", provider=provider
        ) from e
    # ConnectionError はそのまま raise（各エンジンが文脈付きで処理）

    if resp.ok:
        return resp.json()  # type: ignore[no-any-return]

    _handle_http_error(resp, provider=provider)
    return {}  # unreachable but satisfies mypy


def get_json(
    session: requests.Session,
    url: str,
    timeout: float = 5.0,
    *,
    provider: str = "",
) -> dict[str, Any]:
    """JSON GET リクエストを送信し、レスポンスを dict で返す。"""
    try:
        resp = session.get(url, timeout=timeout)
    except requests.exceptions.Timeout as e:
        raise TranslationTimeoutError(
            f"{provider} へのリクエストがタイムアウトしました。", provider=provider
        ) from e

    if resp.ok:
        return resp.json()  # type: ignore[no-any-return]

    _handle_http_error(resp, provider=provider)
    return {}


def _handle_http_error(resp: requests.Response, *, provider: str) -> None:
    """HTTP ステータスエラーを翻訳例外に変換する。"""
    code = resp.status_code
    url = resp.url

    if code in (401, 403):
        raise InvalidApiKeyError(
            f"{provider} の API キーが無効です。設定を確認してください。（{url}）",
            provider=provider,
        )
    if code == 429:
        retry_after = resp.headers.get("Retry-After")
        raise RateLimitError(
            f"{provider} の利用制限に達しました。しばらく待ってから再試行してください。",
            provider=provider,
            retry_after=int(retry_after) if retry_after and retry_after.isdigit() else None,
        )
    if code == 456:
        raise QuotaExceededError(
            f"{provider} の翻訳文字数上限に達しました。", provider=provider
        )
    if code >= 500:
        raise ServerError(
            f"{provider} が一時的に利用できません。（HTTP {code}）",
            provider=provider,
            status_code=code,
        )
    raise ServerError(
        f"{provider} API エラー（HTTP {code}, {url}）",
        provider=provider,
        status_code=code,
    )


