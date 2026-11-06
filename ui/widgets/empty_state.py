"""
Informative Empty State Widget for SNIPLY views.
"""

from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget

from app.paths import AppPaths


class EmptyStateWidget(QFrame):
    """Displays a centered icon, title, subtitle, and optional action button when a view has no items."""

    def __init__(
        self,
        icon_name: str = "all_clips",
        title: str = "",
        subtitle: str = "",
        action_text: Optional[str] = None,
        on_action: Optional[Callable[[], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("EmptyStateWidget")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(32, 48, 32, 48)
        layout.setSpacing(12)

        self.icon_label = QLabel(self)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        svg_path = AppPaths.get_icons_dir() / f"{icon_name}_active.svg"
        if svg_path.exists():
            self.icon_label.setPixmap(QIcon(str(svg_path)).pixmap(42, 42))
        layout.addWidget(self.icon_label)

        self.title_label = QLabel(title, self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #F4F2FA;")
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(subtitle, self)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setMaximumWidth(440)
        self.subtitle_label.setStyleSheet("font-size: 13px; color: #A3A1AE; line-height: 1.4;")
        layout.addWidget(self.subtitle_label)

        self.action_btn = QPushButton(action_text or "", self)
        self.action_btn.setObjectName("PrimaryButton")
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if action_text and on_action:
            self.action_btn.clicked.connect(on_action)
            self.action_btn.show()
        else:
            self.action_btn.hide()
        layout.addWidget(self.action_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_texts(self, title: str, subtitle: str, action_text: Optional[str] = None) -> None:
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)
        if action_text:
            self.action_btn.setText(action_text)
            self.action_btn.show()
        else:
            self.action_btn.hide()
