"""設定ダイアログ。翻訳エンジンの切替、Ollama セットアップ、API キー管理。"""

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
    QLineEdit,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from grabtl.core.security.keystore import load_api_key, mask_api_key, save_api_key
from grabtl.core.translation.engines import EngineType

_OLLAMA_DOWNLOAD_URL = "https://ollama.com/download"
_DEFAULT_OLLAMA_MODEL = "qwen2.5:3b"

_API_CONSOLE_URLS: dict[str, str] = {
    EngineType.DEEPL: "https://www.deepl.com/your-account/keys",
    EngineType.CHATGPT: "https://platform.openai.com/api-keys",
    EngineType.GEMINI: "https://aistudio.google.com/apikey",
}


class _OllamaCheckWorker(QThread):
    """Ollama の接続テストをバックグラウンドで実行する。"""

    result = Signal(bool, bool, str)

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
                    True, False, f"モデル '{self._model}' が未ダウンロードです"
                )
                return
            self.result.emit(True, True, "接続OK・モデル準備完了")
        except Exception as e:
            self.result.emit(False, False, str(e))


class _ApiKeyCheckWorker(QThread):
    """API キーの接続テストをバックグラウンドで実行する。"""

    result = Signal(bool, str)  # (success, message)

    def __init__(
        self, engine: str, api_key: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._engine = engine
        self._api_key = api_key

    def run(self) -> None:
        """軽量なリクエストで API キーが有効か確認する。"""
        import requests

        try:
            if self._engine == EngineType.DEEPL:
                # DeepL: 使用量取得（翻訳せずにキーを検証）
                base = "https://api-free.deepl.com" if self._api_key.endswith(":fx") else "https://api.deepl.com"
                resp = requests.get(
                    f"{base}/v2/usage",
                    headers={"Authorization": f"DeepL-Auth-Key {self._api_key}"},
                    timeout=10,
                )
                if resp.ok:
                    usage = resp.json()
                    used = usage.get("character_count", 0)
                    limit = usage.get("character_limit", 0)
                    self.result.emit(True, f"接続OK（使用量: {used:,} / {limit:,} 文字）")
                    return
            elif self._engine == EngineType.CHATGPT:
                # OpenAI: モデル一覧取得（翻訳せずにキーを検証）
                resp = requests.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    timeout=10,
                )
                if resp.ok:
                    self.result.emit(True, "接続OK")
                    return
            elif self._engine == EngineType.GEMINI:
                # Gemini: モデル一覧取得（翻訳せずにキーを検証）
                resp = requests.get(
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    headers={"x-goog-api-key": self._api_key},
                    timeout=10,
                )
                if resp.ok:
                    self.result.emit(True, "接続OK")
                    return
            else:
                self.result.emit(False, f"不明なエンジン: {self._engine}")
                return

            # HTTP エラー
            if resp.status_code in (401, 403):
                self.result.emit(False, "API キーが無効です")
            else:
                self.result.emit(False, f"API エラー（HTTP {resp.status_code}）")
        except requests.exceptions.ConnectionError:
            self.result.emit(
                False, "サーバーに接続できません。インターネット接続を確認してください。"
            )
        except Exception as e:
            self.result.emit(False, str(e))


class SettingsDialog(QWidget):
    """設定ダイアログ。非モーダルで表示する。"""

    engine_changed = Signal(str)

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
        self._api_check_worker: _ApiKeyCheckWorker | None = None

        main_layout = QVBoxLayout(self)

        # --- エンジン選択 ---
        engine_group = QGroupBox("翻訳エンジン")
        engine_layout = QVBoxLayout(engine_group)

        self._radio_argos = QRadioButton("機械翻訳（オフライン）")
        self._radio_ollama = QRadioButton("AI翻訳（Ollama）")
        self._radio_deepl = QRadioButton("DeepL API")
        self._radio_chatgpt = QRadioButton("ChatGPT API")
        self._radio_gemini = QRadioButton("Gemini API")

        engine_layout.addWidget(self._radio_argos)
        engine_layout.addWidget(self._radio_ollama)
        engine_layout.addWidget(self._radio_deepl)
        engine_layout.addWidget(self._radio_chatgpt)
        engine_layout.addWidget(self._radio_gemini)

        main_layout.addWidget(engine_group)

        # --- 詳細パネル ---
        self._stack = QStackedWidget()

        # Page 0: 機械翻訳
        argos_page = QLabel(
            "APIキー不要で即座に翻訳できます。\n"
            "インターネット接続は不要です。\n"
            "翻訳品質は基本レベルですが、ゲーム用語辞書で補正されます。"
        )
        argos_page.setWordWrap(True)
        argos_page.setContentsMargins(8, 8, 8, 8)
        self._stack.addWidget(argos_page)

        # Page 1: Ollama
        ollama_page = self._create_ollama_page()
        self._stack.addWidget(ollama_page)

        # Page 2-4: API キー入力
        self._api_pages: dict[str, dict[str, Any]] = {}
        for engine, label in [
            (EngineType.DEEPL, "DeepL"),
            (EngineType.CHATGPT, "ChatGPT (OpenAI)"),
            (EngineType.GEMINI, "Gemini (Google)"),
        ]:
            page, widgets = self._create_api_key_page(engine, label)
            self._api_pages[engine] = widgets
            self._stack.addWidget(page)

        main_layout.addWidget(self._stack)

        # --- ボタン ---
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_ok)
        button_box.rejected.connect(self.close)
        main_layout.addWidget(button_box)

        # --- シグナル接続 ---
        radio_page_map = [
            (self._radio_argos, 0),
            (self._radio_ollama, 1),
            (self._radio_deepl, 2),
            (self._radio_chatgpt, 3),
            (self._radio_gemini, 4),
        ]
        for radio, page_idx in radio_page_map:
            radio.toggled.connect(self._make_page_switcher(page_idx))

        self._select_engine(current_engine)
        self._center_on_screen()

    def _make_page_switcher(self, idx: int) -> Any:
        """ラジオボタン用のページ切替コールバックを生成する。"""
        return lambda checked: self._stack.setCurrentIndex(idx) if checked else None

    def _create_ollama_page(self) -> QWidget:
        """Ollama セットアップパネル。"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)

        desc = QLabel(
            "ローカル AI で高品質な翻訳を行います。\n"
            "Ollama のインストールとモデルのダウンロードが必要です。"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self._ollama_status = QLabel("ステータス: 未確認")
        layout.addWidget(self._ollama_status)

        download_btn = QPushButton("Ollama をダウンロード（公式サイトを開く）")
        download_btn.clicked.connect(lambda: webbrowser.open(_OLLAMA_DOWNLOAD_URL))
        layout.addWidget(download_btn)

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

        self._test_btn = QPushButton("接続テスト")
        self._test_btn.clicked.connect(self._run_ollama_check)
        layout.addWidget(self._test_btn)

        return page

    def _create_api_key_page(
        self, engine: str, display_name: str
    ) -> tuple[QWidget, dict[str, Any]]:
        """API キー入力パネルを作成する。"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)

        desc = QLabel(f"{display_name} の API キーを入力してください。")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # API キー入力
        key_layout = QHBoxLayout()
        key_input = QLineEdit()
        key_input.setEchoMode(QLineEdit.EchoMode.Password)
        key_input.setPlaceholderText("API キーを貼り付け")

        # 保存済みキーがあれば部分マスク表示
        saved_key = load_api_key(engine)
        if saved_key:
            key_input.setPlaceholderText(f"保存済み: {mask_api_key(saved_key)}")

        show_btn = QPushButton("表示")
        show_btn.setFixedWidth(50)
        show_btn.setCheckable(True)
        show_btn.toggled.connect(
            lambda checked: key_input.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )

        key_layout.addWidget(key_input)
        key_layout.addWidget(show_btn)
        layout.addLayout(key_layout)

        # ボタン行
        btn_layout = QHBoxLayout()
        test_btn = QPushButton("テストして保存")
        test_btn.clicked.connect(lambda: self._test_and_save_api_key(engine))
        btn_layout.addWidget(test_btn)

        console_url = _API_CONSOLE_URLS.get(engine, "")
        if console_url:
            console_btn = QPushButton("管理画面を開く")
            # clicked は bool を渡すので、_checked で受けて無視する
            console_btn.clicked.connect(
                lambda _checked=False, url=console_url: webbrowser.open(url)
            )
            btn_layout.addWidget(console_btn)

        layout.addLayout(btn_layout)

        # ステータス
        status_label = QLabel("ステータス: 未確認")
        layout.addWidget(status_label)

        widgets = {
            "key_input": key_input,
            "test_btn": test_btn,
            "status_label": status_label,
        }
        return page, widgets

    def _select_engine(self, engine: str) -> None:
        """エンジンに対応するラジオボタンを選択する。"""
        radio_map: dict[str, tuple[QRadioButton, int]] = {
            EngineType.ARGOS: (self._radio_argos, 0),
            EngineType.OLLAMA: (self._radio_ollama, 1),
            EngineType.DEEPL: (self._radio_deepl, 2),
            EngineType.CHATGPT: (self._radio_chatgpt, 3),
            EngineType.GEMINI: (self._radio_gemini, 4),
        }
        radio, page = radio_map.get(engine, (self._radio_argos, 0))
        radio.setChecked(True)
        self._stack.setCurrentIndex(page)

    def _get_selected_engine(self) -> str:
        """選択されているエンジンを返す。"""
        if self._radio_ollama.isChecked():
            return EngineType.OLLAMA
        if self._radio_deepl.isChecked():
            return EngineType.DEEPL
        if self._radio_chatgpt.isChecked():
            return EngineType.CHATGPT
        if self._radio_gemini.isChecked():
            return EngineType.GEMINI
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

    def _test_and_save_api_key(self, engine: str) -> None:
        """API キーをテストし、成功したら keyring に保存する。"""
        widgets = self._api_pages[engine]
        key_input: QLineEdit = widgets["key_input"]
        test_btn: QPushButton = widgets["test_btn"]
        status_label: QLabel = widgets["status_label"]

        api_key = key_input.text().strip()
        if not api_key:
            # 入力が空の場合、保存済みキーを使う
            saved = load_api_key(engine)
            if saved:
                api_key = saved
            else:
                status_label.setText("ステータス: ❌ API キーを入力してください")
                status_label.setStyleSheet("color: red;")
                return

        test_btn.setText("テスト中...")
        test_btn.setEnabled(False)
        status_label.setText("ステータス: 確認中...")
        status_label.setStyleSheet("")

        self._api_check_worker = _ApiKeyCheckWorker(engine, api_key, parent=self)
        self._api_check_worker.result.connect(
            lambda ok, msg: self._on_api_check_result(engine, api_key, ok, msg)
        )
        self._api_check_worker.start()

    def _on_api_check_result(
        self, engine: str, api_key: str, success: bool, message: str
    ) -> None:
        """API キーテスト結果を処理する。"""
        widgets = self._api_pages[engine]
        test_btn: QPushButton = widgets["test_btn"]
        status_label: QLabel = widgets["status_label"]
        key_input: QLineEdit = widgets["key_input"]

        test_btn.setText("テストして保存")
        test_btn.setEnabled(True)

        if success:
            # keyring に保存
            save_api_key(engine, api_key)
            status_label.setText(f"ステータス: ✅ {message}")
            status_label.setStyleSheet("color: green;")
            key_input.clear()
            key_input.setPlaceholderText(f"保存済み: {mask_api_key(api_key)}")
        else:
            status_label.setText(f"ステータス: ❌ {message}")
            status_label.setStyleSheet("color: red;")

    def _run_ollama_check(self) -> None:
        """Ollama 接続テスト。"""
        self._test_btn.setText("テスト中...")
        self._test_btn.setEnabled(False)
        self._ollama_status.setText("ステータス: 確認中...")

        self._check_worker = _OllamaCheckWorker(_DEFAULT_OLLAMA_MODEL, parent=self)
        self._check_worker.result.connect(self._on_ollama_check_result)
        self._check_worker.start()

    def _on_ollama_check_result(
        self, server_ok: bool, model_ok: bool, message: str
    ) -> None:
        """Ollama 接続テスト結果。"""
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
