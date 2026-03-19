"""mss を使ったスクリーンキャプチャ。画像はメモリ上でのみ処理する。"""

from __future__ import annotations

import io

import mss
from PIL import Image


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
    if width <= 0 or height <= 0:
        msg = f"幅と高さは正の値が必要です: width={width}, height={height}"
        raise ValueError(msg)

    monitor = {"left": x, "top": y, "width": width, "height": height}

    with mss.mss() as sct:
        screenshot = sct.grab(monitor)
        # BGRA → RGB に変換して PNG バイト列にする
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
