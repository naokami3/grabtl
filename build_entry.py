"""Nuitka ビルド用エントリポイント。

パッケージの import パスを正しく解決するためのランチャースクリプト。
直接 src/grabtl/gui/main_window.py を指定するとパッケージ構造が壊れるため、
このファイルを Nuitka のエントリポイントに使う。
"""

from grabtl.gui.main_window import main

main()
