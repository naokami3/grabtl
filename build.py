"""Nuitka ビルドスクリプト。

Usage:
    python build.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent
_BUILD_DIR = _PROJECT_ROOT / "build" / "release"
_MODEL_SRC = Path.home() / ".local" / "share" / "argos-translate" / "packages" / "en_ja"
_DIST_DIR = _BUILD_DIR / "build_entry.dist"

_NUITKA_ARGS = [
    sys.executable,
    "-m",
    "nuitka",
    "--mode=standalone",
    "--enable-plugin=pyside6",
    "--windows-console-mode=disable",
    "--assume-yes-for-downloads",
    f"--output-dir={_BUILD_DIR}",
    "--output-filename=grabtl.exe",
    "--include-package=grabtl",
    # WinRT モジュール（winocr 用）
    "--include-module=winrt.runtime",
    "--include-module=winrt.windows.media.ocr",
    "--include-module=winrt.windows.graphics.imaging",
    "--include-module=winrt.windows.storage.streams",
    "--include-module=winrt.windows.globalization",
    "--include-module=winrt.windows.foundation",
    "--include-module=winrt.windows.foundation.collections",
    # 不要モジュールの除外（サイズ削減）
    "--nofollow-import-to=torch",
    "--nofollow-import-to=tensorflow",
    "--nofollow-import-to=PySide6.QtWebEngine*",
    "--nofollow-import-to=PySide6.QtMultimedia*",
    "--nofollow-import-to=PySide6.Qt3D*",
    "--nofollow-import-to=PySide6.QtQuick*",
    "--nofollow-import-to=PySide6.QtQml*",
    # Windows メタデータ
    "--windows-company-name=grabtl",
    "--windows-product-name=grabtl",
    "--windows-file-version=0.1.0.0",
    "--windows-product-version=0.1.0.0",
    '--windows-file-description=Game Chat Translator',
    # エントリポイント
    str(_PROJECT_ROOT / "build_entry.py"),
]


def _copy_models() -> None:
    """翻訳モデルをビルド出力にコピーする。"""
    dest = _DIST_DIR / "models" / "en_ja"

    if not _MODEL_SRC.exists():
        print(f"WARNING: モデルが見つかりません: {_MODEL_SRC}")
        print("  argostranslate で言語パッケージをインストールしてください。")
        return

    # model/ ディレクトリ
    model_src = _MODEL_SRC / "model"
    model_dest = dest / "model"
    if model_src.exists():
        print(f"Copying {model_src} -> {model_dest}")
        if model_dest.exists():
            shutil.rmtree(model_dest)
        shutil.copytree(model_src, model_dest)

    # sentencepiece.model
    sp_src = _MODEL_SRC / "sentencepiece.model"
    sp_dest = dest / "sentencepiece.model"
    if sp_src.exists():
        print(f"Copying {sp_src} -> {sp_dest}")
        shutil.copy2(sp_src, sp_dest)


def main() -> None:
    """ビルドを実行する。"""
    print("=" * 60)
    print("grabtl Nuitka Build")
    print("=" * 60)

    # Nuitka ビルド
    print("\n[1/2] Running Nuitka...")
    result = subprocess.run(_NUITKA_ARGS, cwd=_PROJECT_ROOT)
    if result.returncode != 0:
        print("ERROR: Nuitka build failed!")
        sys.exit(1)

    # モデルコピー
    print("\n[2/2] Copying translation models...")
    _copy_models()

    # サマリー
    print("\n" + "=" * 60)
    print("Build complete!")
    exe_path = _DIST_DIR / "grabtl.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / 1024 / 1024
        print(f"  Executable: {exe_path} ({size_mb:.1f} MB)")

        # dist フォルダ全体のサイズ
        total = sum(f.stat().st_size for f in _DIST_DIR.rglob("*") if f.is_file())
        print(f"  Total dist size: {total / 1024 / 1024:.1f} MB")
    else:
        print(f"  WARNING: {exe_path} not found")
    print("=" * 60)


if __name__ == "__main__":
    main()
