"""mss を使ったスクリーンキャプチャ。画像はメモリ上でのみ処理する。"""

from __future__ import annotations

import io

import mss
from PIL import Image


def _validate_dimensions(width: int, height: int) -> None:
    """幅と高さのバリデーション。"""
    if width <= 0 or height <= 0:
        msg = f"幅と高さは正の値が必要です: width={width}, height={height}"
        raise ValueError(msg)


def capture_region_pil(x: int, y: int, width: int, height: int) -> Image.Image:
    """指定領域をキャプチャし、PIL Image を直接返す。

    PNG エンコードを行わないため、OCR に直接渡す場合に効率的。

    Args:
        x: 左上の X 座標。
        y: 左上の Y 座標。
        width: キャプチャ幅（ピクセル）。
        height: キャプチャ高さ（ピクセル）。

    Returns:
        RGB モードの PIL Image。

    Raises:
        ValueError: 幅または高さが 0 以下の場合。
    """
    _validate_dimensions(width, height)
    monitor = {"left": x, "top": y, "width": width, "height": height}

    with mss.mss() as sct:
        screenshot = sct.grab(monitor)
        return Image.frombytes("RGB", screenshot.size, screenshot.rgb)


def capture_region(x: int, y: int, width: int, height: int) -> bytes:
    """指定領域をキャプチャし、PNG バイト列を返す。

    Args:
        x: 左上の X 座標。
        y: 左上の Y 座標。
        width: キャプチャ幅（ピクセル）。
        height: キャプチャ高さ（ピクセル）。

    Returns:
        PNG 形式の画像バイト列。

    Raises:
        ValueError: 幅または高さが 0 以下の場合。
    """
    img = capture_region_pil(x, y, width, height)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
