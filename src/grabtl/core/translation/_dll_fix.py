"""Windows での DLL ロード競合の回避策。

winrt パッケージがバンドルする msvcp140.dll と、torch の c10.dll が
期待するバージョンが異なるため、winocr (WinRT) と argostranslate (torch)
を同一プロセスで使うと WinError 1114 が発生する。

エントリポイントの最初でシステム版 VC ランタイムを先制ロードし、
winrt のバンドル版が先に読み込まれるのを防ぐ。
"""

from __future__ import annotations

import os
import sys


def preload_system_vcrt() -> None:
    """Windows でシステム版の VC ランタイム DLL を先制ロードする。

    winocr (WinRT) より先に呼ぶ必要がある。
    フルパス指定でシステム版をロードすることで、winrt のバンドル版が
    プロセスに先にロードされるのを防ぐ。
    """
    if sys.platform != "win32":
        return
    import contextlib
    import ctypes

    system_root = os.environ.get("SYSTEMROOT", r"C:\Windows")
    system32 = os.path.join(system_root, "System32")
    for dll_name in ("msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll"):
        dll_path = os.path.join(system32, dll_name)
        if os.path.exists(dll_path):
            with contextlib.suppress(OSError):
                ctypes.CDLL(dll_path)
