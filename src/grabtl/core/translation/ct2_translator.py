"""CTranslate2 で Opus-MT モデルを直接実行する翻訳エンジン。

argostranslate / stanza / torch に依存しない軽量な Tier 0 実装。
argostranslate がダウンロードしたモデルファイルをそのまま再利用する。
長文は pysbd で文分割してバッチ翻訳する。
アイドル時にモデルをアンロードしてメモリを解放できる。
"""

from __future__ import annotations

import gc
import time
from pathlib import Path
from typing import Any

import pysbd

_DEFAULT_PACKAGES_DIR = Path.home() / ".local" / "share" / "argos-translate" / "packages"
_UNLOAD_AFTER_SECONDS = 300  # 5分


class CT2Translator:
    """CTranslate2 + SentencePiece による Opus-MT 翻訳。

    Tier 0: API キー不要、ネットワーク通信なし、torch 不要。
    アイドル時にモデルをアンロードしてメモリを解放できる。
    """

    def __init__(self, model_dir: str | Path | None = None) -> None:
        if model_dir is not None:
            self._model_dir = Path(model_dir)
        else:
            self._model_dir = _DEFAULT_PACKAGES_DIR / "en_ja"

        self._translator: Any = None
        self._sp: Any = None
        self._loaded = False
        self._last_used: float = 0.0
        self._segmenter = pysbd.Segmenter(language="en", clean=False)

    def _ensure_loaded(self) -> None:
        """初回呼び出し時にモデルをロードする。"""
        if self._loaded:
            return

        import ctranslate2  # type: ignore[import-not-found]
        import sentencepiece  # type: ignore[import-not-found]

        model_path = self._model_dir / "model"
        sp_path = self._model_dir / "sentencepiece.model"

        if not model_path.exists():
            msg = (
                f"翻訳モデルが見つかりません: {model_path}\n"
                "argostranslate で言語パッケージをインストールしてください:\n"
                '  python -c "'
                "import argostranslate.package; "
                "argostranslate.package.update_package_index(); "
                "pkg = next(p for p in argostranslate.package.get_available_packages() "
                "if p.from_code == 'en' and p.to_code == 'ja'); "
                'pkg.install()"'
            )
            raise FileNotFoundError(msg)

        self._translator = ctranslate2.Translator(str(model_path), device="cpu")
        self._sp = sentencepiece.SentencePieceProcessor()
        self._sp.Load(str(sp_path))
        self._loaded = True

    def unload(self) -> None:
        """モデルをアンロードしてメモリを解放する。

        次回 translate() 時に自動で再ロードされる。
        """
        self._translator = None
        self._sp = None
        self._loaded = False
        gc.collect()

    def should_unload(self) -> bool:
        """アンロードすべきかどうかを返す。"""
        if not self._loaded:
            return False
        return time.monotonic() - self._last_used > _UNLOAD_AFTER_SECONDS

    def translate(self, text: str, source: str, target: str) -> str:
        """テキストを翻訳する。

        長文は pysbd で文分割し、バッチ翻訳して結合する。
        """
        if not text.strip():
            return ""

        self._ensure_loaded()
        self._last_used = time.monotonic()

        # 文分割
        sentences = self._split_sentences(text)

        # バッチトークナイズ
        tokenized = [self._sp.encode(s, out_type=str) for s in sentences]

        # バッチ翻訳
        results = self._translator.translate_batch(tokenized)

        # デコードして結合
        translated_sentences = [self._sp.decode(r.hypotheses[0]) for r in results]

        return " ".join(translated_sentences)

    def _split_sentences(self, text: str) -> list[str]:
        """pysbd で文分割する。"""
        sentences = self._segmenter.segment(text)
        return [s.strip() for s in sentences if s.strip()]

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
