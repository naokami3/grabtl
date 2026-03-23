"""DLL 競合回避のテスト。

Windows 環境で winocr と argostranslate が同一プロセスで共存できることを確認する。
"""

from __future__ import annotations

import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows 専用テスト")


class TestDllFix:
    def test_preload_system_vcrt_が正常に実行される(self) -> None:
        from grabtl.core.translation._dll_fix import preload_system_vcrt

        # 例外なく完了すること
        preload_system_vcrt()

    def test_preload後にwinocrとtorchが共存できる(self) -> None:
        from grabtl.core.translation._dll_fix import preload_system_vcrt

        preload_system_vcrt()

        # winocr (WinRT) のインポート
        import winocr  # noqa: F401

        # torch (argostranslate の依存) のインポート
        import torch  # noqa: F401

        # 両方が同一プロセスでインポートできること
        assert True

    def test_preload後にWinOCREngineとArgosTranslatorが共存できる(self) -> None:
        from grabtl.core.translation._dll_fix import preload_system_vcrt

        preload_system_vcrt()

        from grabtl.core.ocr.winocr_engine import WinOCREngine
        from grabtl.core.translation.argos import ArgosTranslator

        # 両方インスタンス化できること
        ocr = WinOCREngine()
        translator = ArgosTranslator()

        assert ocr.name == "Windows OCR"
        assert translator.is_local is True
