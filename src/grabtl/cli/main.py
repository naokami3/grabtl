"""grabtl CLI エントリポイント。

使用例:
    grabtl --x 100 --y 200 --width 400 --height 50
    grabtl --x 100 --y 200 --width 400 --height 50 --source en --target ja
"""

from __future__ import annotations

import argparse
import io
import sys


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="grabtl",
        description="画面上のテキストをキャプチャして翻訳する",
    )
    parser.add_argument("--x", type=int, required=True, help="キャプチャ領域の左上 X 座標")
    parser.add_argument("--y", type=int, required=True, help="キャプチャ領域の左上 Y 座標")
    parser.add_argument("--width", type=int, required=True, help="キャプチャ領域の幅")
    parser.add_argument("--height", type=int, required=True, help="キャプチャ領域の高さ")
    parser.add_argument(
        "--source", type=str, default="en", help="ソース言語コード（デフォルト: en）"
    )
    parser.add_argument(
        "--target", type=str, default="ja", help="ターゲット言語コード（デフォルト: ja）"
    )
    return parser


def _ensure_utf8_stdout() -> None:
    """stdout/stderr を UTF-8 に設定する。

    Windows のデフォルト (cp932) では翻訳結果の日本語が文字化けするため、
    UTF-8 で出力する。
    """
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if sys.stderr.encoding.lower() != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def main() -> None:
    """CLI のメインエントリポイント。"""
    _ensure_utf8_stdout()

    # DLL 競合回避: winocr (WinRT) と torch の msvcp140.dll バージョン不一致を防ぐ
    # 他の import より先に呼ぶ必要がある
    from grabtl.core.translation._dll_fix import preload_system_vcrt

    preload_system_vcrt()

    parser = _create_parser()
    args = parser.parse_args()

    # Windows チェック（winocr は Windows 専用）
    if sys.platform != "win32":
        print("エラー: grabtl は現在 Windows でのみ動作します", file=sys.stderr)
        sys.exit(1)

    from grabtl.core.capture.screen import capture_region
    from grabtl.core.glossary import Glossary
    from grabtl.core.glossary.decorator import GlossaryTranslator
    from grabtl.core.ocr.winocr_engine import WinOCREngine
    from grabtl.core.pipeline import Pipeline
    from grabtl.core.translation.ct2_translator import CT2Translator

    # キャプチャ
    print(f"キャプチャ中... ({args.x}, {args.y}) {args.width}x{args.height}")
    image = capture_region(args.x, args.y, args.width, args.height)

    # パイプライン実行
    ocr_engine = WinOCREngine()
    base_translator = CT2Translator()
    glossary = Glossary.default()
    translator = GlossaryTranslator(base_translator, glossary)
    pipeline = Pipeline(ocr_engine=ocr_engine, translator=translator)

    result = pipeline.run(image, source_lang=args.source, target_lang=args.target)

    # 結果表示
    print(f"\n--- OCR 結果 (信頼度: {result.ocr_result.confidence:.2f}) ---")
    print(result.ocr_result.text)
    print(f"\n--- 翻訳結果 ({args.source} → {args.target}) ---")
    print(result.translated_text)


if __name__ == "__main__":
    main()
