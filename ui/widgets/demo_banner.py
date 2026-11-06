"""
Demonstration Mode Banner Widget.
Clearly indicates when the user is viewing sample demonstration items and allows instant exit.
"""

from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from core.i18n import tr


class DemoBanner(QFrame):
    """Top banner shown when Demo Gallery mode is active."""

    def __init__(self, on_exit: Callable[[], None], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("DemoBanner")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(12)

        self.badge = QLabel(tr("demo.badge"), self)
        self.badge.setStyleSheet(
            "background-color: #8B5CF6; color: #17181C; font-weight: 700; font-size: 11px; padding: 2px 7px; border-radius: 4px;"
        )
        layout.addWidget(self.badge)

        self.text_label = QLabel(tr("demo.banner_text"), self)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("color: #F4F2FA; font-size: 12px;")
        layout.addWidget(self.text_label, stretch=1)

        self.exit_btn = QPushButton(tr("demo.exit_button"), self)
        self.exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exit_btn.clicked.connect(on_exit)
        layout.addWidget(self.exit_btn)

    def refresh_translations(self) -> None:
        self.badge.setText(tr("demo.badge"))
        self.text_label.setText(tr("demo.banner_text"))
        self.exit_btn.setText(tr("demo.exit_button"))
