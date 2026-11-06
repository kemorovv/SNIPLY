"""
ImageCard Widget for the SNIPLY Images Grid.
Displays cached thumbnail without loading full-resolution images into memory,
alongside dimensions, formatted file size, timestamp, and quick copy/save actions.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from core.i18n import LocalizationManager, tr
from core.image_manager import ImageManager
from models.clip import Clip


class ImageCard(QFrame):
    """Responsive grid card for copied image entries."""

    selected = Signal(object)
    copy_requested = Signal(object)
    delete_requested = Signal(object)

    def __init__(
        self,
        clip: Clip,
        image_manager: ImageManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.clip = clip
        self.image_manager = image_manager
        self.setObjectName("ImageCard")
        self.setFixedWidth(260)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Thumbnail preview container
        self.thumb_label = QLabel(self)
        self.thumb_label.setFixedSize(234, 148)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet(
            "background-color: #17181C; border: 1px solid #292A32; border-radius: 8px;"
        )

        thumb_bytes = self.image_manager.get_thumbnail_bytes(clip.thumbnail_path or "")
        if thumb_bytes:
            pix = QPixmap()
            pix.loadFromData(thumb_bytes)
            scaled = pix.scaled(
                230,
                144,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.thumb_label.setPixmap(scaled)
        else:
            self.thumb_label.setText(clip.preview)
        layout.addWidget(self.thumb_label)

        meta = clip.metadata or {}
        w = meta.get("width", 0)
        h = meta.get("height", 0)
        fmt = meta.get("format", "PNG")
        size_str = LocalizationManager.instance().format_file_size(int(meta.get("file_size", 0)))

        dim_lbl = QLabel(f"{fmt}  •  {w} × {h} px  •  {size_str}", self)
        dim_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #F4F2FA; background: transparent;")
        layout.addWidget(dim_lbl)

        bottom_row = QHBoxLayout()
        rel_time = LocalizationManager.instance().format_relative_time(clip.last_copied_at)
        time_lbl = QLabel(rel_time, self)
        time_lbl.setStyleSheet("font-size: 11px; color: #72717E; background: transparent;")
        bottom_row.addWidget(time_lbl, stretch=1)

        copy_btn = QPushButton(tr("action.copy"), self)
        copy_btn.setFixedHeight(26)
        copy_btn.setStyleSheet("font-size: 11px; padding: 2px 10px;")
        copy_btn.clicked.connect(lambda: self.copy_requested.emit(self.clip))
        bottom_row.addWidget(copy_btn)

        layout.addLayout(bottom_row)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.clip)
        super().mousePressEvent(event)
