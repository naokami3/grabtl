"""Windows OCR (winocr) を使った OCR エンジン実装。"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from grabtl.core.ocr.base import OCRResult


class WinOCREngine:
    """Windows OCR API を利用する OCR エンジン。

    Windows 環境でのみ動作する。winocr パッケージが必要。
    """

    def __init__(self) -> None:
        if sys.platform != "win32":
            msg = "WinOCREngine は Windows でのみ利用可能です"
            raise RuntimeError(msg)
        try:
            import winocr as _winocr  # type: ignore[import-not-found]
        except ImportError:
            msg = "winocr がインストールされていません: pip install winocr"
            raise ImportError(msg) from None  # noqa: B904
        self._winocr: Any = _winocr

    def recognize(self, image: bytes, lang: str = "en") -> OCRResult:
        """画像からテキストを認識する。

        Args:
            image: PNG 形式の画像バイト列。
            lang: 認識対象の言語コード。

        Returns:
            認識結果。
        """
        result = asyncio.run(self._winocr.recognize_png(image, lang=lang))

        lines: list[str] = []
        total_confidence = 0.0
        count = 0
        bounding_boxes: list[dict[str, int]] = []

        for line in result["lines"]:
            lines.append(line["text"])
            for word in line.get("words", []):
                total_confidence += word.get("confidence", 0.0)
                count += 1
                bbox = word.get("bounding_rect")
                if bbox:
                    bounding_boxes.append(
                        {
                            "x": int(bbox["x"]),
                            "y": int(bbox["y"]),
                            "width": int(bbox["width"]),
                            "height": int(bbox["height"]),
                        }
                    )

        text = "\n".join(lines)
        confidence = total_confidence / count if count > 0 else 0.0

        return OCRResult(
            text=text,
            confidence=confidence,
            lang=lang,
            bounding_boxes=bounding_boxes if bounding_boxes else None,
        )

    def available_languages(self) -> list[str]:
        """利用可能な言語コードの一覧を返す。"""
        # Windows OCR は OS にインストールされた言語パックに依存する
        # 主要な言語を返す（実際の利用可否は OS の設定に依存）
        return ["en", "ja", "zh", "ko", "de", "fr", "es", "pt", "ru"]

    @property
    def name(self) -> str:
        """エンジン名を返す。"""
        return "Windows OCR"
