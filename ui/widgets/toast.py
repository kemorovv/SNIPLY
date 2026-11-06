"""
Subtle Animated Toast Notification Widget for SNIPLY.
Displays non-intrusive feedback (e.g., "Copied to clipboard") with fade animation.
"""

from typing import Optional

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QWidget

from app.paths import AppPaths


class ToastNotification(QFrame):
    """Floating bottom-center toast banner inside the parent window."""

    def __init__(self, parent: QWidget, reduced_motion: bool = False) -> None:
        super().__init__(parent)
        self.reduced_motion = reduced_motion
        self.setObjectName("ToastNotification")
        self.setWindowFlags(Qt.WindowType.SubWindow | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self.setStyleSheet(
            """
            QFrame#ToastNotification {
                background-color: #282932;
                border: 1px solid #A78BFA;
                border-radius: 9px;
                padding: 8px 16px;
            }
            QLabel {
                background: transparent;
                color: #F4F2FA;
                font-weight: 600;
                font-size: 13px;
            }
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(8)

        self.icon_label = QLabel(self)
        check_svg = AppPaths.get_icons_dir() / "check_active.svg"
        if check_svg.exists():
            self.icon_label.setPixmap(QIcon(str(check_svg)).pixmap(16, 16))
        layout.addWidget(self.icon_label)

        self.text_label = QLabel("", self)
        layout.addWidget(self.text_label)

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._fade_out)
        self.hide()

    def show_message(self, message: str, duration_ms: int = 1900) -> None:
        self.text_label.setText(message)
        self.adjustSize()

        parent_widget: Optional[QWidget] = self.parentWidget()
        if parent_widget is not None:
            x = (parent_widget.width() - self.width()) // 2
            y = parent_widget.height() - self.height() - 28
            self.move(max(16, x), max(16, y))

        self.raise_()
        self.show()

        if self.reduced_motion:
            self._opacity_effect.setOpacity(1.0)
        else:
            self._anim.stop()
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(1.0)
            self._anim.start()

        self._hide_timer.start(duration_ms)

    def _fade_out(self) -> None:
        if self.reduced_motion:
            self.hide()
            return
        self._anim.stop()
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(self._on_fade_finished)
        self._anim.start()

    def _on_fade_finished(self) -> None:
        try:
            self._anim.finished.disconnect(self._on_fade_finished)
        except Exception:
            pass
        if self._opacity_effect.opacity() <= 0.05:
            self.hide()
