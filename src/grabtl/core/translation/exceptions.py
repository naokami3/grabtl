"""翻訳エンジンの共通例外。

例外の分類は「ユーザーが何をすべきか」と「デバッグ時に何が分かるか」を基準にする。

ユーザーアクション別:
- 設定を確認して  → InvalidApiKeyError, EngineNotReadyError
- しばらく待って   → RateLimitError, QuotaExceededError
- 選択し直して    → TextTooLongError
- 接続を確認して  → ConnectionFailedError
- 何もできない    → ServerError（サービス側の問題）

デバッグ情報:
- 全例外に provider（エンジン名）と url（リクエスト先）を含む
- HTTP エラーには status_code を含む
"""

from __future__ import annotations


class TranslationError(RuntimeError):
    """翻訳処理の基底エラー。全ての翻訳例外はこれを継承する。

    Attributes:
        provider: エラーが発生した翻訳エンジン名（例: "DeepL", "Ollama"）。
    """

    def __init__(self, message: str, *, provider: str = "") -> None:
        self.provider = provider
        super().__init__(message)


# --- ユーザーアクション: 設定を確認して ---


class InvalidApiKeyError(TranslationError):
    """API キーが無効または未設定。

    ユーザーへ: 「設定画面で API キーを確認してください。」
    """


class EngineNotReadyError(TranslationError):
    """翻訳エンジンが利用可能な状態にない。

    ユーザーへ: Ollama 未起動、モデル未ダウンロード等。
    エンジンごとに具体的なメッセージを設定する。
    """


# --- ユーザーアクション: しばらく待って ---


class RateLimitError(TranslationError):
    """API レート制限に達した。

    ユーザーへ: 「しばらく待ってから再試行してください。」
    """

    def __init__(
        self, message: str, *, provider: str = "", retry_after: int | None = None
    ) -> None:
        super().__init__(message, provider=provider)
        self.retry_after = retry_after


class QuotaExceededError(TranslationError):
    """API の利用枠を超過した。

    ユーザーへ: 「翻訳の無料枠を使い切りました。」
    """


# --- ユーザーアクション: 選択し直して ---


class TextTooLongError(TranslationError):
    """入力テキストが長すぎる。

    ユーザーへ: 「テキストが長すぎます。より小さい領域を選択してください。」
    """


# --- ユーザーアクション: 接続を確認して ---


class ConnectionFailedError(TranslationError):
    """翻訳サーバーへの接続に失敗した。

    ユーザーへ: Ollama → "Ollama を起動してください"
               API → "インターネット接続を確認してください"
    """


# --- ユーザーアクション: 何もできない（サービス側の問題） ---


class ServerError(TranslationError):
    """翻訳サービス側のエラー（HTTP 500 等）。

    ユーザーへ: 「翻訳サービスが一時的に利用できません。」
    デバッグ: status_code と url を含む。
    """

    def __init__(
        self, message: str, *, provider: str = "", status_code: int = 0
    ) -> None:
        super().__init__(message, provider=provider)
        self.status_code = status_code


# --- リクエストのタイムアウト ---


class TranslationTimeoutError(TranslationError):
    """リクエストがタイムアウトした。

    ユーザーへ: Ollama → "CPU で実行中の場合は時間がかかります"
               API → "ネットワークが不安定な可能性があります"
    """
