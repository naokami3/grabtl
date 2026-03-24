"""設定ダイアログ。翻訳エンジンの切替と Ollama セットアップガイド。"""

from __future__ import annotations

import webbrowser
from typing import Any

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from grabtl.core.translation.engines import EngineType

_OLLAMA_DOWNLOAD_URL = "https://ollama.com/download"
_DEFAULT_OLLAMA_MODEL = "qwen2.5:3b"


class _OllamaCheckWorker(QThread):
    """Ollama の接続テストをバックグラウンドで実行する。"""

    result = Signal(bool, bool, str)  # (server_ok, model_ok, message)

    def __init__(self, model: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model = model

    def run(self) -> None:
        """接続テストを実行する。"""
        try:
            from grabtl.core.translation.ollama import OllamaTranslator

            translator = OllamaTranslator(model=self._model)
            server_ok = translator.is_available()
            if not server_ok:
                self.result.emit(False, False, "Ollama が起動していません")
                return
            model_ok = translator.is_model_available()
            if not model_ok:
                self.result.emit(
                    True,
                    False,
                    f"モデル '{self._model}' が未ダウンロードです",
                )
                return
            self.result.emit(True, True, "接続OK・モデル準備完了")
        except Exception as e:
            self.result.emit(False, False, str(e))


class SettingsDialog(QWidget):
    """設定ダイアログ。非モーダルで表示する。

    翻訳エンジンの切替と Ollama のセットアップガイドを提供する。
    """

    engine_changed = Signal(str)  # EngineType の値

    def __init__(self, current_engine: str = EngineType.ARGOS) -> None:
        super().__init__()
        self.setWindowTitle("grabtl 設定")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setMinimumWidth(450)
        self.setMaximumWidth(550)

        self._current_engine = current_engine
        self._check_worker: _OllamaCheckWorker | None = None

        main_layout = QVBoxLayout(self)

        # --- エンジン選択 ---
        engine_group = QGroupBox("翻訳エンジン")
        engine_layout = QVBoxLayout(engine_group)

        self._radio_argos = QRadioButton("機械翻訳（オフライン）")
        self._radio_ollama = QRadioButton("AI翻訳（Ollama）")
        self._radio_deepl = QRadioButton("DeepL API (準備中)")
        self._radio_chatgpt = QRadioButton("ChatGPT API (準備中)")
        self._radio_gemini = QRadioButton("Gemini API (準備中)")

        self._radio_deepl.setEnabled(False)
        self._radio_chatgpt.setEnabled(False)
        self._radio_gemini.setEnabled(False)
        self._radio_deepl.setToolTip("今後のアップデートで追加予定です")
        self._radio_chatgpt.setToolTip("今後のアップデートで追加予定です")
        self._radio_gemini.setToolTip("今後のアップデートで追加予定です")

        engine_layout.addWidget(self._radio_argos)
        engine_layout.addWidget(self._radio_ollama)
        engine_layout.addWidget(self._radio_deepl)
        engine_layout.addWidget(self._radio_chatgpt)
        engine_layout.addWidget(self._radio_gemini)

        main_layout.addWidget(engine_group)

        # --- 詳細パネル ---
        self._stack = QStackedWidget()

        # Page 0: 機械翻訳の説明
        argos_page = QLabel(
            "APIキー不要で即座に翻訳できます。\n"
            "インターネット接続は不要です。\n"
            "翻訳品質は基本レベルですが、ゲーム用語辞書で補正されます。"
        )
        argos_page.setWordWrap(True)
        argos_page.setContentsMargins(8, 8, 8, 8)
        self._stack.addWidget(argos_page)

        # Page 1: Ollama セットアップ
        ollama_page = self._create_ollama_page()
        self._stack.addWidget(ollama_page)

        # Page 2-4: Coming Soon
        for _name in ("DeepL", "ChatGPT", "Gemini"):
            label = QLabel("今後のアップデートで追加予定です。")
            label.setContentsMargins(8, 8, 8, 8)
            self._stack.addWidget(label)

        main_layout.addWidget(self._stack)

        # --- ボタン ---
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_ok)
        button_box.rejected.connect(self.close)
        main_layout.addWidget(button_box)

        # --- シグナル接続 ---
        self._radio_argos.toggled.connect(
            lambda checked: self._stack.setCurrentIndex(0) if checked else None
        )
        self._radio_ollama.toggled.connect(
            lambda checked: self._stack.setCurrentIndex(1) if checked else None
        )

        # 現在のエンジンを選択
        self._select_engine(current_engine)

        # 画面中央に配置
        self._center_on_screen()

    def _create_ollama_page(self) -> QWidget:
        """Ollama セットアップパネルを作成する。"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)

        desc = QLabel(
            "ローカル AI で高品質な翻訳を行います。\n"
            "Ollama のインストールとモデルのダウンロードが必要です。"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # ステータス
        self._ollama_status = QLabel("ステータス: 未確認")
        layout.addWidget(self._ollama_status)

        # ダウンロードリンク
        download_btn = QPushButton("Ollama をダウンロード（公式サイトを開く）")
        download_btn.clicked.connect(
            lambda: webbrowser.open(_OLLAMA_DOWNLOAD_URL)
        )
        layout.addWidget(download_btn)

        # コマンドコピー
        cmd_layout = QHBoxLayout()
        cmd_label = QLabel(f"ollama pull {_DEFAULT_OLLAMA_MODEL}")
        cmd_label.setStyleSheet(
            "background-color: #F0F0F0; padding: 4px 8px; "
            "border: 1px solid #CCCCCC; font-family: Consolas;"
        )
        copy_btn = QPushButton("コピー")
        copy_btn.setFixedWidth(60)
        copy_btn.clicked.connect(
            lambda: self._copy_to_clipboard(f"ollama pull {_DEFAULT_OLLAMA_MODEL}")
        )
        cmd_layout.addWidget(cmd_label)
        cmd_layout.addWidget(copy_btn)
        layout.addLayout(cmd_layout)

        # 接続テストボタン
        self._test_btn = QPushButton("接続テスト")
        self._test_btn.clicked.connect(self._run_ollama_check)
        layout.addWidget(self._test_btn)

        return page

    def _select_engine(self, engine: str) -> None:
        """エンジンに対応するラジオボタンを選択する。"""
        radio_map: dict[str, tuple[QRadioButton, int]] = {
            EngineType.ARGOS: (self._radio_argos, 0),
            EngineType.OLLAMA: (self._radio_ollama, 1),
        }
        radio, page = radio_map.get(engine, (self._radio_argos, 0))
        radio.setChecked(True)
        self._stack.setCurrentIndex(page)

    def _get_selected_engine(self) -> str:
        """選択されているエンジンを返す。"""
        if self._radio_ollama.isChecked():
            return EngineType.OLLAMA
        return EngineType.ARGOS

    def _on_ok(self) -> None:
        """OK ボタン押下。設定を保存してシグナルを emit する。"""
        from PySide6.QtCore import QSettings

        engine = self._get_selected_engine()
        settings = QSettings()
        settings.setValue("translation/engine", engine)

        if engine != self._current_engine:
            self.engine_changed.emit(engine)

        self.close()

    def _run_ollama_check(self) -> None:
        """Ollama 接続テストをバックグラウンドで実行する。"""
        self._test_btn.setText("テスト中...")
        self._test_btn.setEnabled(False)
        self._ollama_status.setText("ステータス: 確認中...")

        self._check_worker = _OllamaCheckWorker(_DEFAULT_OLLAMA_MODEL, parent=self)
        self._check_worker.result.connect(self._on_check_result)
        self._check_worker.start()

    def _on_check_result(self, server_ok: bool, model_ok: bool, message: str) -> None:
        """接続テスト結果を表示する。"""
        self._test_btn.setText("接続テスト")
        self._test_btn.setEnabled(True)

        if server_ok and model_ok:
            self._ollama_status.setText(f"ステータス: ✅ {message}")
            self._ollama_status.setStyleSheet("color: green;")
        elif server_ok:
            self._ollama_status.setText(f"ステータス: ⚠️ {message}")
            self._ollama_status.setStyleSheet("color: orange;")
        else:
            self._ollama_status.setText(f"ステータス: ❌ {message}")
            self._ollama_status.setStyleSheet("color: red;")

    def _copy_to_clipboard(self, text: str) -> None:
        """テキストをクリップボードにコピーする。"""
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(text)

    def _center_on_screen(self) -> None:
        """画面中央に配置する。"""
        self.adjustSize()
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            geo = screen.availableGeometry()
            self.move(
                geo.center().x() - self.width() // 2,
                geo.center().y() - self.height() // 2,
            )

    def _get_any_result(self) -> Any:
        """型チェック用のダミー。"""
        return None
