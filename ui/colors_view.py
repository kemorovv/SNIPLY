"""
Dedicated Colors Workspace View for SNIPLY.
Displays recognized HEX and RGB colors as visual swatch cards with searching,
sorting, and palette export to JSON/CSS.
"""

import json
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.constants import CONTENT_TYPE_COLOR
from core.clipboard_manager import ClipboardManager
from core.i18n import LocalizationManager, tr, tr_plural
from models.clip import Clip
from ui.widgets.color_card import ColorCard
from ui.widgets.empty_state import EmptyStateWidget


class ColorsView(QFrame):
    """Designer-oriented workspace displaying recognized colors as visual swatch cards."""

    clip_selected = Signal(object)
    color_copied = Signal(str, str)  # (format_name, value)

    def __init__(
        self,
        clipboard_manager: ClipboardManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.clipboard_manager = clipboard_manager
        self.storage = clipboard_manager.storage
        self._current_colors: List[Clip] = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        header_row = QHBoxLayout()
        self.title_lbl = QLabel(tr("navigation.colors"), self)
        self.title_lbl.setStyleSheet("font-size: 20px; font-weight: 700; color: #F4F2FA;")
        header_row.addWidget(self.title_lbl)

        self.count_badge = QLabel("0", self)
        self.count_badge.setStyleSheet(
            "font-size: 12px; color: #A3A1AE; background-color: #22232A; border: 1px solid #292A32; padding: 2px 10px; border-radius: 10px;"
        )
        header_row.addWidget(self.count_badge)
        header_row.addStretch(1)

        self.export_btn = QPushButton(tr("colors.export_palette"), self)
        self.export_btn.clicked.connect(self._export_palette)
        header_row.addWidget(self.export_btn)
        main_layout.addLayout(header_row)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText(tr("search.colors_placeholder"))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(lambda _t: self.refresh_colors())
        main_layout.addWidget(self.search_input)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.grid_container = QWidget(self.scroll)
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 4, 4, 12)
        self.grid_layout.setSpacing(14)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.scroll.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll, stretch=1)

        self.empty_state = EmptyStateWidget(
            icon_name="colors",
            title=tr("empty.colors.title"),
            subtitle=tr("empty.colors.subtitle"),
            parent=self,
        )
        self.empty_state.hide()
        main_layout.addWidget(self.empty_state, stretch=1)

        LocalizationManager.instance().subscribe(self._on_language_changed)

    def refresh_colors(self) -> None:
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        search_q = self.search_input.text().strip()
        if self.clipboard_manager.demo_mode:
            clips = [
                c
                for c in ClipboardManager.get_demo_clips()
                if c.content_type == CONTENT_TYPE_COLOR
            ]
        else:
            clips = self.storage.query_clips(
                search_query=search_q,
                content_type=CONTENT_TYPE_COLOR,
                limit=250,
            )

        self._current_colors = clips
        self.count_badge.setText(tr_plural("items.count", len(clips)))

        if not clips:
            self.scroll.hide()
            self.empty_state.show()
            return

        self.empty_state.hide()
        self.scroll.show()

        cols = max(1, (self.width() - 48) // 265)
        for idx, clip in enumerate(clips):
            card = ColorCard(clip=clip, parent=self.grid_container)
            card.selected.connect(lambda c: self.clip_selected.emit(c))
            card.copy_value_requested.connect(self._on_copy_format)
            row, col = divmod(idx, cols)
            self.grid_layout.addWidget(card, row, col)

    def _on_copy_format(self, fmt_name: str, val_str: str) -> None:
        self.clipboard_manager.copy_custom_text(val_str)
        self.color_copied.emit(fmt_name, val_str)

    def _export_palette(self) -> None:
        if not self._current_colors:
            return
        target, _ = QFileDialog.getSaveFileName(
            self,
            tr("colors.export_palette"),
            "sniply_palette.json",
            "JSON Palette (*.json);;CSS Variables (*.css)",
        )
        if not target:
            return

        out_path = Path(target)
        if out_path.suffix.lower() == ".css":
            lines = [":root {"]
            for i, c in enumerate(self._current_colors, start=1):
                hex_val = c.metadata.get("hex", "#A78BFA")
                lines.append(f"  --sniply-color-{i}: {hex_val};")
            lines.append("}")
            out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        else:
            palette = [
                {
                    "hex": c.metadata.get("hex"),
                    "rgb": c.metadata.get("rgb_str"),
                    "hsl": c.metadata.get("hsl_str"),
                }
                for c in self._current_colors
            ]
            out_path.write_text(json.dumps(palette, indent=2) + "\n", encoding="utf-8")

    def _on_language_changed(self, _lang: str) -> None:
        self.title_lbl.setText(tr("navigation.colors"))
        self.export_btn.setText(tr("colors.export_palette"))
        self.search_input.setPlaceholderText(tr("search.colors_placeholder"))
        self.empty_state.set_texts(tr("empty.colors.title"), tr("empty.colors.subtitle"))
        self.refresh_colors()
