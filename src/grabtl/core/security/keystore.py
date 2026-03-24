"""API キーのセキュアな保存・取得。

Windows Credential Manager (DPAPI) を keyring 経由で使用する。
API キーを平文で設定ファイルやログに保存してはならない（CLAUDE.md ルール 7）。

全ての API キーアクセスはこのモジュールを経由する。
"""

from __future__ import annotations

import keyring

_SERVICE_NAME = "grabtl"


def save_api_key(engine: str, api_key: str) -> None:
    """API キーを keyring に保存する。

    Args:
        engine: エンジン名（EngineType の値: "deepl", "chatgpt", "gemini"）。
        api_key: 保存する API キー。
    """
    keyring.set_password(_SERVICE_NAME, engine, api_key)


def load_api_key(engine: str) -> str | None:
    """keyring から API キーを取得する。

    Args:
        engine: エンジン名（EngineType の値）。

    Returns:
        保存済みの API キー。未保存の場合は None。
    """
    return keyring.get_password(_SERVICE_NAME, engine)


def delete_api_key(engine: str) -> None:
    """keyring から API キーを削除する。

    Args:
        engine: エンジン名（EngineType の値）。
    """
    import contextlib

    with contextlib.suppress(keyring.errors.PasswordDeleteError):
        keyring.delete_password(_SERVICE_NAME, engine)


def mask_api_key(key: str) -> str:
    """API キーをマスク表示用に変換する。

    Args:
        key: API キー。

    Returns:
        マスク済み文字列（例: "sk-...xxxx"）。
    """
    if len(key) <= 8:
        return "****"
    return key[:4] + "..." + key[-4:]
