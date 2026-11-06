"""
Dedicated Images Workspace View for SNIPLY.
Displays copied images in a responsive multi-column grid using cached thumbnails
without loading every full-resolution image into memory.
"""

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.constants import CONTENT_TYPE_IMAGE
from core.clipboard_manager import ClipboardManager
from core.i18n import LocalizationManager, tr, tr_plural
from models.clip import Clip
from ui.widgets.empty_state import EmptyStateWidget
from ui.widgets.image_card import ImageCard


class ImagesView(QFrame):
    """Responsive grid view for captured clipboard images."""

    clip_selected = Signal(object)
    clip_copied = Signal(object)

    def __init__(
        self,
        clipboard_manager: ClipboardManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.clipboard_manager = clipboard_manager
        self.storage = clipboard_manager.storage

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        header_row = QHBoxLayout()
        self.title_lbl = QLabel(tr("navigation.images"), self)
        self.title_lbl.setStyleSheet("font-size: 20px; font-weight: 700; color: #F4F2FA;")
        header_row.addWidget(self.title_lbl)

        self.count_badge = QLabel("0", self)
        self.count_badge.setStyleSheet(
            "font-size: 12px; color: #A3A1AE; background-color: #22232A; border: 1px solid #292A32; padding: 2px 10px; border-radius: 10px;"
        )
        header_row.addWidget(self.count_badge)
        header_row.addStretch(1)
        main_layout.addLayout(header_row)

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
            icon_name="images",
            title=tr("empty.images.title"),
            subtitle=tr("empty.images.subtitle"),
            parent=self,
        )
        self.empty_state.hide()
        main_layout.addWidget(self.empty_state, stretch=1)

        LocalizationManager.instance().subscribe(self._on_language_changed)

    def refresh_images(self) -> None:
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        clips: List[Clip] = self.storage.query_clips(content_type=CONTENT_TYPE_IMAGE, limit=200)
        self.count_badge.setText(tr_plural("items.count", len(clips)))

        if not clips:
            self.scroll.hide()
            self.empty_state.show()
            return

        self.empty_state.hide()
        self.scroll.show()

        cols = max(1, (self.width() - 48) // 275)
        for idx, clip in enumerate(clips):
            card = ImageCard(
                clip=clip,
                image_manager=self.clipboard_manager.image_manager,
                parent=self.grid_container,
            )
            card.selected.connect(lambda c: self.clip_selected.emit(c))
            card.copy_requested.connect(self._on_copy_image)
            row, col = divmod(idx, cols)
            self.grid_layout.addWidget(card, row, col)

    def _on_copy_image(self, clip: Clip) -> None:
        self.clipboard_manager.restore_clip_to_clipboard(clip)
        self.clip_copied.emit(clip)

    def _on_language_changed(self, _lang: str) -> None:
        self.title_lbl.setText(tr("navigation.images"))
        self.empty_state.set_texts(tr("empty.images.title"), tr("empty.images.subtitle"))
        self.refresh_images()
