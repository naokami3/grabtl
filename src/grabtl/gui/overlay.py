"""翻訳結果を表示するフローティングオーバーレイ。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QPropertyAnimation, QRect
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPainter, QPainterPath
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from PySide6.QtGui import QKeyEvent, QPaintEvent

    from grabtl.core.pipeline import TranslationResult

_BG_COLOR = QColor(0, 0, 0, 200)
_BORDER_RADIUS = 8
_FADE_DURATION_MS = 300
_PADDING = 12
_MAX_WIDTH = 500
_MAX_HEIGHT = 300


class ResultOverlay(QWidget):
    """翻訳結果をフローティング表示するウィジェット。

    翻訳テキストのみ表示（原文は非表示）。
    長文はスクロールで閲覧可能。
    オーバーレイ外クリックで消える。
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from PySide6.QtCore import Qt

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        self.setMaximumWidth(_MAX_WIDTH)
        self.setMaximumHeight(_MAX_HEIGHT)

        # メインレイアウト
        layout = QVBoxLayout(self)
        layout.setContentsMargins(_PADDING, _PADDING, _PADDING, _PADDING)
        layout.setSpacing(6)

        # スクロールエリア
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll.setStyleSheet(
            "QScrollArea { background: transparent; }"
            "QScrollBar:vertical { background: rgba(255,255,255,30); width: 6px; }"
            "QScrollBar::handle:vertical { background: rgba(255,255,255,80); "
            "border-radius: 3px; min-height: 20px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )

        # スクロール内のコンテンツ
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        # 翻訳テキスト
        self._translation_label = QLabel()
        self._translation_label.setWordWrap(True)
        self._translation_label.setFont(QFont("Segoe UI", 12))
        self._translation_label.setStyleSheet("color: #FFFFFF;")
        scroll_layout.addWidget(self._translation_label)

        self._scroll.setWidget(scroll_content)
        layout.addWidget(self._scroll)

        # ステータス（スピナー/エラー用）
        self._status_label = QLabel()
        self._status_label.setWordWrap(True)
        self._status_label.setFont(QFont("Segoe UI", 10))
        self._status_label.setStyleSheet("color: #AAAAAA;")
        self._status_label.hide()
        layout.addWidget(self._status_label)

        # フェードアニメーション
        self._fade_anim: QPropertyAnimation | None = None

        # 翻訳結果表示中かどうか
        self._is_result_shown = False

        # 表示位置の基準
        self._near_rect = QRect()

    def show_spinner(self, near_rect: QRect) -> None:
        """処理中のスピナーを表示する。"""
        self._near_rect = near_rect
        self._is_result_shown = False
        self._scroll.hide()
        self._status_label.setText("翻訳中...")
        self._status_label.setStyleSheet("color: #AAAAAA;")
        self._status_label.show()
        self._position_near(near_rect)
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()

    def show_ocr_preview(self, text: str, near_rect: QRect) -> None:
        """OCR 結果を先行表示する（翻訳中として表示）。"""
        self._near_rect = near_rect
        self._translation_label.setText("翻訳中...")
        self._translation_label.setStyleSheet("color: #999999;")
        self._scroll.show()
        self._status_label.hide()
        self._position_near(near_rect)
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()

    def show_result(self, result: TranslationResult, near_rect: QRect) -> None:
        """翻訳結果を表示する。オーバーレイ外クリックで消える。"""
        self._near_rect = near_rect
        self._is_result_shown = True
        self._translation_label.setText(result.translated_text)
        self._translation_label.setStyleSheet("color: #FFFFFF;")
        self._scroll.show()
        self._scroll.verticalScrollBar().setValue(0)
        self._status_label.hide()
        self._position_near(near_rect)
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()
        self.activateWindow()

    def show_error(self, message: str, near_rect: QRect) -> None:
        """エラーをインライン表示する。外クリックで消える。"""
        self._near_rect = near_rect
        self._is_result_shown = True
        self._scroll.hide()
        self._status_label.setText(message)
        self._status_label.setStyleSheet("color: #FFA500;")
        self._status_label.show()
        self._position_near(near_rect)
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()
        self.activateWindow()

    def dismiss(self) -> None:
        """即座に非表示にする。"""
        self._is_result_shown = False
        if self._fade_anim is not None:
            self._fade_anim.stop()
        self.hide()

    def _position_near(self, near_rect: QRect) -> None:
        """選択領域の上方向にオーバーレイを配置する。"""
        self.adjustSize()
        overlay_h = min(self.sizeHint().height(), _MAX_HEIGHT)
        overlay_w = min(self.sizeHint().width(), _MAX_WIDTH)

        # 選択領域の上に配置
        x = near_rect.x() + (near_rect.width() - overlay_w) // 2
        y = near_rect.y() - overlay_h - 8

        # 画面内に収める
        screen = QGuiApplication.screenAt(near_rect.topLeft())
        if screen is not None:
            avail = screen.availableGeometry()
            if y < avail.top():
                y = near_rect.bottom() + 8
            if x < avail.left():
                x = avail.left() + 4
            if x + overlay_w > avail.right():
                x = avail.right() - overlay_w - 4

        self.move(x, y)
        self.resize(overlay_w, overlay_h)

    def changeEvent(self, event: Any) -> None:
        """フォーカス喪失（オーバーレイ外クリック）でフェードアウトする。"""
        from PySide6.QtCore import QEvent

        super().changeEvent(event)
        if (
            event.type() == QEvent.Type.ActivationChange
            and not self.isActiveWindow()
            and self._is_result_shown
        ):
            self._fade_out()

    def _fade_out(self) -> None:
        """フェードアウトアニメーションで非表示にする。"""
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(_FADE_DURATION_MS)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.finished.connect(self.hide)
        self._fade_anim.start()

    def paintEvent(self, event: QPaintEvent) -> None:
        """半透明黒背景 + 角丸を描画。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(
            0.0,
            0.0,
            float(self.width()),
            float(self.height()),
            _BORDER_RADIUS,
            _BORDER_RADIUS,
        )
        painter.fillPath(path, _BG_COLOR)
        painter.end()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Esc で非表示。"""
        from PySide6.QtCore import Qt

        if event.key() == Qt.Key.Key_Escape:
            self.dismiss()
