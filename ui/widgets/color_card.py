"""
ColorCard Widget for the SNIPLY Colors Workspace.
Displays a large visual color swatch, HEX, RGB, and HSL values, timestamp, and instant format copy buttons.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from core.i18n import LocalizationManager, tr
from models.clip import Clip


class ColorCard(QFrame):
    """Visual color swatch card tailored for designers in the Colors Workspace."""

    selected = Signal(object)
    copy_value_requested = Signal(str, str)  # (format_label, value_str)
    pin_toggled = Signal(object)
    favorite_toggled = Signal(object)

    def __init__(self, clip: Clip, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.clip = clip
        self.setObjectName("ColorCard")
        self.setFixedWidth(250)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        meta = clip.metadata or {}
        self.hex_val = meta.get("hex_full") or meta.get("hex") or clip.text_content or "#A78BFA"
        self.rgb_val = meta.get("rgb_str") or "rgb(167, 139, 250)"
        self.hsl_val = meta.get("hsl_str") or "hsl(255, 92%, 76%)"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Visual Color Swatch Banner
        swatch = QFrame(self)
        swatch.setFixedHeight(84)
        swatch.setStyleSheet(
            f"background-color: {meta.get('hex', '#A78BFA')}; border: 1px solid #30313B; border-radius: 8px;"
        )
        layout.addWidget(swatch)

        # Primary HEX title
        hex_lbl = QLabel(self.hex_val, self)
        hex_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #F4F2FA; background: transparent;")
        layout.addWidget(hex_lbl)

        # RGB & HSL lines
        rgb_lbl = QLabel(self.rgb_val, self)
        rgb_lbl.setStyleSheet("font-size: 12px; color: #A3A1AE; background: transparent;")
        layout.addWidget(rgb_lbl)

        hsl_lbl = QLabel(self.hsl_val, self)
        hsl_lbl.setStyleSheet("font-size: 12px; color: #72717E; background: transparent;")
        layout.addWidget(hsl_lbl)

        # Quick copy format buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        for fmt_name, val in (("HEX", self.hex_val), ("RGB", self.rgb_val), ("HSL", self.hsl_val)):
            btn = QPushButton(fmt_name, self)
            btn.setFixedHeight(26)
            btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
            btn.clicked.connect(lambda checked=False, f=fmt_name, v=val: self.copy_value_requested.emit(f, v))
            btn_row.addWidget(btn)

        layout.addLayout(btn_row)

        rel_time = LocalizationManager.instance().format_relative_time(clip.last_copied_at)
        time_lbl = QLabel(rel_time, self)
        time_lbl.setStyleSheet("font-size: 11px; color: #72717E; background: transparent;")
        layout.addWidget(time_lbl)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.clip)
        super().mousePressEvent(event)
