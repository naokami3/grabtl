"""OCR エンジンの Protocol 定義。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class OCRResult:
    """OCR の認識結果。"""

    text: str
    confidence: float
    lang: str
    bounding_boxes: list[dict[str, int]] | None = field(default=None)


@runtime_checkable
class OCREngine(Protocol):
    """OCR エンジンが実装すべきインターフェース。"""

    def recognize(self, image: bytes, lang: str = "en") -> OCRResult:
        """画像からテキストを認識する。

        Args:
            image: PNG 形式の画像バイト列。
            lang: 認識対象の言語コード。

        Returns:
            認識結果。
        """
        ...

    def available_languages(self) -> list[str]:
        """利用可能な言語コードの一覧を返す。"""
        ...

    @property
    def name(self) -> str:
        """エンジン名を返す。"""
        ...
