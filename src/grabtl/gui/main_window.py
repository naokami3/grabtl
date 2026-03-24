"""GUI エントリポイント。システムトレイ常駐 + ホットキー + 翻訳パイプライン統合。"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import io
import sys
from typing import Any

from PySide6.QtCore import QByteArray, QRect, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from grabtl.core.translation.engines import EngineType
from grabtl.gui.overlay import ResultOverlay
from grabtl.gui.region_selector import RegionSelector
from grabtl.gui.settings_dialog import SettingsDialog

# Win32 定数
_WM_HOTKEY = 0x0312
_MOD_CONTROL = 0x0002
_MOD_SHIFT = 0x0004
_HOTKEY_ID = 1
_VK_G = 0x47  # 'G' キー
_CAPTURE_DELAY_MS = 200


class HotkeyFilter:
    """Win32 WM_HOTKEY メッセージをキャッチしてコールバックを呼ぶ。"""

    def __init__(self, callback: Any) -> None:
        from PySide6.QtCore import QAbstractNativeEventFilter

        class _Filter(QAbstractNativeEventFilter):
            def __init__(self, cb: Any) -> None:
                super().__init__()
                self._cb = cb

            def nativeEventFilter(
                self, event_type: QByteArray | bytes, message: int  # type: ignore[override]
            ) -> tuple[bool, int]:
                if event_type == b"windows_generic_MSG":
                    msg = ctypes.wintypes.MSG.from_address(int(message))
                    if msg.message == _WM_HOTKEY and msg.wParam == _HOTKEY_ID:
                        self._cb()
                        return (True, 0)
                return (False, 0)

        self._filter = _Filter(callback)

    def install(self, app: QApplication) -> None:
        """ネイティブイベントフィルタをインストールする。"""
        app.installNativeEventFilter(self._filter)


class TranslationWorker(QThread):
    """OCR → 翻訳をバックグラウンドで実行する。

    OCR 完了時に ocr_done を emit し、段階的表示を可能にする。
    """

    ocr_done = Signal(str)
    finished = Signal(object)
    error = Signal(str)

    def __init__(
        self,
        ocr_engine: Any,
        translator: Any,
        image: bytes,
        source_lang: str,
        target_lang: str,
    ) -> None:
        super().__init__()
        self._ocr_engine = ocr_engine
        self._translator = translator
        self._image = image
        self._source_lang = source_lang
        self._target_lang = target_lang

    def run(self) -> None:
        """OCR → 翻訳を実行する。"""
        try:
            from grabtl.core.pipeline import TranslationResult

            # OCR
            ocr_result = self._ocr_engine.recognize(self._image, lang=self._source_lang)
            self.ocr_done.emit(ocr_result.text)

            # 翻訳
            if not ocr_result.text.strip():
                self.finished.emit(TranslationResult(ocr_result=ocr_result, translated_text=""))
                return

            translated = self._translator.translate(
                ocr_result.text, source=self._source_lang, target=self._target_lang
            )
            self.finished.emit(
                TranslationResult(ocr_result=ocr_result, translated_text=translated)
            )
        except Exception as e:
            self.error.emit(str(e))


class TrayApp:
    """システムトレイ常駐アプリケーション。"""

    def __init__(self, app: QApplication) -> None:
        self._app = app

        # トレイアイコン
        self._tray = QSystemTrayIcon()
        self._tray.setIcon(_create_tray_icon())
        self._tray.setToolTip("grabtl — 待機中 (Ctrl+Shift+G)")

        # トレイメニュー
        menu = QMenu()
        translate_action = QAction("翻訳する (Ctrl+Shift+G)", menu)
        translate_action.triggered.connect(self._activate_selection)
        menu.addAction(translate_action)
        settings_action = QAction("設定...", menu)
        settings_action.triggered.connect(self._show_settings)
        menu.addAction(settings_action)
        menu.addSeparator()
        quit_action = QAction("終了", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)
        self._tray.setContextMenu(menu)
        self._tray.show()

        # GUI ウィジェット
        self._region_selector = RegionSelector()
        self._result_overlay = ResultOverlay()
        self._region_selector.region_selected.connect(self._on_region_selected)
        self._region_selector.selection_cancelled.connect(self._on_selection_cancelled)

        # 翻訳ワーカー
        self._worker: TranslationWorker | None = None
        self._logical_rect = QRect()   # オーバーレイ表示位置用（論理座標）
        self._physical_rect = QRect()  # キャプチャ用（物理ピクセル座標）

        # 設定ダイアログ（多重起動防止用の参照）
        self._settings_dialog: SettingsDialog | None = None

        # パイプラインのエンジン（バックグラウンドで初期化）
        self._ocr_engine: Any = None
        self._translator: Any = None
        self._engines_ready = False
        self._current_engine = self._load_engine_setting()
        self._init_engines(self._current_engine)

        # グローバルホットキー登録
        self._hotkey_filter = HotkeyFilter(self._activate_selection)
        self._hotkey_filter.install(app)
        self._register_hotkey()

    @staticmethod
    def _load_engine_setting() -> str:
        """QSettings から保存済みのエンジン設定を読み込む。"""
        from PySide6.QtCore import QSettings

        settings = QSettings()
        engine = settings.value("translation/engine", EngineType.ARGOS)
        return str(engine)

    def _init_engines(self, engine_type: str = EngineType.ARGOS) -> None:
        """OCR/翻訳エンジンをバックグラウンドで初期化する。"""
        self._engines_ready = False
        self._tray.setToolTip("grabtl — エンジン初期化中...")

        class _InitWorker(QThread):
            done = Signal(object, object)
            init_error = Signal(str)

            def __init__(self, engine: str) -> None:
                super().__init__()
                self._engine = engine

            def run(self) -> None:
                try:
                    from grabtl.core.glossary import Glossary
                    from grabtl.core.glossary.decorator import GlossaryTranslator
                    from grabtl.core.ocr.winocr_engine import WinOCREngine

                    ocr = WinOCREngine()
                    base_translator = _create_translator(self._engine)
                    glossary = Glossary.default()
                    translator = GlossaryTranslator(base_translator, glossary)
                    self.done.emit(ocr, translator)
                except Exception as e:
                    self.init_error.emit(str(e))

        self._init_worker = _InitWorker(engine_type)
        self._init_worker.done.connect(self._on_engines_ready)
        self._init_worker.init_error.connect(self._on_engine_error)
        self._init_worker.start()

    def _on_engines_ready(self, ocr: Any, translator: Any) -> None:
        """エンジンの初期化完了。"""
        self._ocr_engine = ocr
        self._translator = translator
        self._engines_ready = True
        self._tray.setToolTip("grabtl — 待機中 (Ctrl+Shift+G)")

    def _on_engine_error(self, msg: str) -> None:
        """エンジン初期化エラー。"""
        self._tray.showMessage("grabtl", f"翻訳エンジンの初期化に失敗しました: {msg}")

    def _register_hotkey(self) -> None:
        """グローバルホットキーを登録する。"""
        if sys.platform != "win32":
            return
        # Ctrl+Shift+G
        ctypes.windll.user32.RegisterHotKey(0, _HOTKEY_ID, _MOD_CONTROL | _MOD_SHIFT, _VK_G)

    def _unregister_hotkey(self) -> None:
        """グローバルホットキーを解除する。"""
        if sys.platform != "win32":
            return
        ctypes.windll.user32.UnregisterHotKey(0, _HOTKEY_ID)

    def _activate_selection(self) -> None:
        """領域選択モードを開始する。"""
        # 前の結果を消す
        self._result_overlay.dismiss()

        if not self._engines_ready:
            self._tray.showMessage("grabtl", "翻訳エンジンを準備中です。しばらくお待ちください...")
            return

        self._region_selector.start_selection()

    def _on_region_selected(self, logical_rect: QRect, physical_rect: QRect) -> None:
        """領域が選択された。キャプチャ → 翻訳を実行する。"""
        self._logical_rect = logical_rect
        self._physical_rect = physical_rect

        # スピナーはキャプチャ後に表示（キャプチャに映り込むのを防ぐ）
        # RegionSelector の hide() + 200ms 遅延でウィンドウが消えてからキャプチャ
        QTimer.singleShot(_CAPTURE_DELAY_MS, self._do_capture)

    def _do_capture(self) -> None:
        """キャプチャして翻訳ワーカーを起動する。"""
        from grabtl.core.capture.screen import capture_region

        phys = self._physical_rect
        try:
            image = capture_region(phys.x(), phys.y(), phys.width(), phys.height())
        except Exception as e:
            self._result_overlay.show_error(
                f"キャプチャ失敗: {e}", self._logical_rect
            )
            return

        # キャプチャ後にスピナー表示
        self._result_overlay.show_spinner(self._logical_rect)

        # ワーカー起動
        self._worker = TranslationWorker(
            ocr_engine=self._ocr_engine,
            translator=self._translator,
            image=image,
            source_lang="en",
            target_lang="ja",
        )
        self._worker.ocr_done.connect(self._on_ocr_done)
        self._worker.finished.connect(self._on_translation_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_ocr_done(self, text: str) -> None:
        """OCR 結果を先行表示する。"""
        if text.strip():
            self._result_overlay.show_ocr_preview(text, self._logical_rect)
        else:
            self._result_overlay.show_error(
                "テキストが見つかりませんでした。テキスト部分を選択してください。",
                self._logical_rect,
            )

    def _on_translation_done(self, result: Any) -> None:
        """翻訳完了。結果を表示する。"""
        if result.translated_text:
            self._result_overlay.show_result(result, self._logical_rect)
        # 空テキストの場合はエラー表示済み

    def _on_error(self, msg: str) -> None:
        """翻訳エラー。"""
        self._result_overlay.show_error(f"翻訳エラー: {msg}", self._logical_rect)

    def _on_selection_cancelled(self) -> None:
        """選択がキャンセルされた。"""

    def _show_settings(self) -> None:
        """設定ダイアログを表示する。"""
        if self._settings_dialog is not None:
            self._settings_dialog.raise_()
            self._settings_dialog.activateWindow()
            return
        self._settings_dialog = SettingsDialog(current_engine=self._current_engine)
        self._settings_dialog.engine_changed.connect(self._on_engine_changed)
        self._settings_dialog.destroyed.connect(self._on_settings_closed)
        self._settings_dialog.show()

    def _on_engine_changed(self, engine: str) -> None:
        """エンジンが変更された。再初期化する。"""
        self._current_engine = engine
        self._init_engines(engine)

    def _on_settings_closed(self) -> None:
        """設定ダイアログが閉じられた。"""
        self._settings_dialog = None

    def _quit(self) -> None:
        """アプリを終了する。"""
        self._unregister_hotkey()
        self._result_overlay.dismiss()
        self._tray.hide()
        self._app.quit()


def _create_translator(engine_type: str) -> Any:
    """エンジン種別に応じた Translator を生成する。

    Tier 2 エンジンは keystore から API キーを読み込む。
    """
    from grabtl.core.security.keystore import load_api_key

    if engine_type == EngineType.OLLAMA:
        from grabtl.core.translation.ollama import OllamaTranslator

        return OllamaTranslator()

    if engine_type == EngineType.DEEPL:
        from grabtl.core.translation.deepl import DeepLTranslator

        return DeepLTranslator(api_key=load_api_key(EngineType.DEEPL) or "")

    if engine_type == EngineType.CHATGPT:
        from grabtl.core.translation.chatgpt import ChatGPTTranslator

        return ChatGPTTranslator(api_key=load_api_key(EngineType.CHATGPT) or "")

    if engine_type == EngineType.GEMINI:
        from grabtl.core.translation.gemini import GeminiTranslator

        return GeminiTranslator(api_key=load_api_key(EngineType.GEMINI) or "")

    # デフォルト: Argos
    from grabtl.core.translation.argos import ArgosTranslator

    return ArgosTranslator()


def _create_tray_icon() -> QIcon:
    """シンプルなトレイアイコンを生成する。"""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QPainter

    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(0, 120, 215))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(2, 2, 28, 28, 6, 6)
    painter.setPen(QColor(255, 255, 255))
    font = painter.font()
    font.setPointSize(14)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "G")
    painter.end()
    return QIcon(pixmap)


_MUTEX_NAME = "grabtl_single_instance"
_ERROR_ALREADY_EXISTS = 183


def _acquire_single_instance_lock() -> bool:
    """多重起動を防止する。既に起動中なら False を返す。"""
    if sys.platform != "win32":
        return True
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW(None, False, _MUTEX_NAME)
    return ctypes.get_last_error() != _ERROR_ALREADY_EXISTS


def main() -> None:
    """GUI のメインエントリポイント。"""
    # 多重起動防止
    if not _acquire_single_instance_lock():
        print("grabtl は既に起動しています。", file=sys.stderr)
        sys.exit(0)

    # stdout を UTF-8 に設定（ログ出力用）
    if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    # DLL 競合回避: winocr import より先に呼ぶ
    from grabtl.core.translation._dll_fix import preload_system_vcrt

    preload_system_vcrt()

    app = QApplication(sys.argv)
    app.setOrganizationName("grabtl")
    app.setApplicationName("grabtl")
    app.setQuitOnLastWindowClosed(False)  # トレイ常駐のため

    _tray_app = TrayApp(app)  # noqa: F841 (参照を保持)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
