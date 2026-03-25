"""ドラッグで翻訳対象領域を選択する全画面透過オーバーレイ。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
)
from PySide6.QtWidgets import QWidget

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintEvent

_OVERLAY_COLOR = QColor(0, 0, 0, 80)
_BORDER_COLOR = QColor(0, 191, 255)  # #00BFFF
_BORDER_WIDTH = 2
_MIN_SELECTION_SIZE = 10


class RegionSelector(QWidget):
    """全画面透過オーバーレイ。ドラッグで翻訳対象領域を選択する。

    選択完了時に region_selected シグナルを emit する。
    座標は DPI 補正済みの物理ピクセル座標。
    """

    region_selected = Signal(QRect, QRect)  # (論理座標, 物理ピクセル座標)
    selection_cancelled = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from PySide6.QtCore import Qt

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

        self._origin: QPoint | None = None
        self._current: QPoint | None = None
        self._selecting = False

        # paintEvent のスロットリング（16ms = ~60fps）
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(16)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self.update)

    def start_selection(self) -> None:
        """全画面オーバーレイを表示して選択を開始する。"""
        self._origin = None
        self._current = None
        self._selecting = False

        # マルチモニター: 全画面の union を取得
        screens = QGuiApplication.screens()
        if not screens:
            return
        union = QRect()
        for screen in screens:
            union = union.united(screen.geometry())
        self.setGeometry(union)
        self.show()
        self.raise_()
        self.activateWindow()

    def paintEvent(self, event: QPaintEvent) -> None:
        """半透明暗背景 + 選択矩形の穴抜き + 枠線を描画。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._origin is not None and self._current is not None:
            selection = QRect(
                self.mapFromGlobal(self._origin),
                self.mapFromGlobal(self._current),
            ).normalized()

            # QPainterPath で選択領域に穴を開ける
            path = QPainterPath()
            path.addRect(
                float(self.rect().x()),
                float(self.rect().y()),
                float(self.rect().width()),
                float(self.rect().height()),
            )
            path.addRect(
                float(selection.x()),
                float(selection.y()),
                float(selection.width()),
                float(selection.height()),
            )
            painter.fillPath(path, _OVERLAY_COLOR)

            # 選択矩形の枠線
            pen = painter.pen()
            pen.setColor(_BORDER_COLOR)
            pen.setWidth(_BORDER_WIDTH)
            painter.setPen(pen)
            painter.drawRect(selection)
        else:
            # 選択前は全面を暗くする
            painter.fillRect(self.rect(), _OVERLAY_COLOR)

            # ドラッグ前のヒント表示
            hint_font = QFont("Segoe UI", 16)
            painter.setFont(hint_font)
            painter.setPen(QColor(255, 255, 255, 200))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "翻訳したいテキストをドラッグで選択してください\n\nEsc でキャンセル",
            )

        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """左ボタンでドラッグ開始、右ボタンでキャンセル。"""
        from PySide6.QtCore import Qt

        if event.button() == Qt.MouseButton.RightButton:
            self.hide()
            self.selection_cancelled.emit()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.globalPosition().toPoint()
            self._current = self._origin
            self._selecting = True

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """選択矩形を更新する（16ms スロットリング）。"""
        if self._selecting:
            self._current = event.globalPosition().toPoint()
            if not self._update_timer.isActive():
                self._update_timer.start()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """選択完了。DPI 補正して物理ピクセル座標で emit する。"""
        from PySide6.QtCore import Qt

        if event.button() != Qt.MouseButton.LeftButton or not self._selecting:
            return

        self._selecting = False
        if self._origin is None or self._current is None:
            return

        rect = QRect(self._origin, self._current).normalized()

        # 最小サイズチェック
        if rect.width() < _MIN_SELECTION_SIZE or rect.height() < _MIN_SELECTION_SIZE:
            return

        self.hide()

        # DPI スケーリング補正: 論理座標 → 物理ピクセル座標（キャプチャ用）
        screen = QGuiApplication.screenAt(self._origin)
        dpr = screen.devicePixelRatio() if screen else 1.0
        physical_rect = QRect(
            int(rect.x() * dpr),
            int(rect.y() * dpr),
            int(rect.width() * dpr),
            int(rect.height() * dpr),
        )
        self.region_selected.emit(rect, physical_rect)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Esc でキャンセル。"""
        from PySide6.QtCore import Qt

        if event.key() == Qt.Key.Key_Escape:
            self._selecting = False
            self.hide()
            self.selection_cancelled.emit()
