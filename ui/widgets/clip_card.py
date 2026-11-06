"""
ClipCard Widget for SNIPLY History Views.
Displays type icon, content preview, color swatch or thumbnail preview, timestamp,
pin/favorite badges, collection pill, and custom styled right-click context menu.
"""

from typing import Callable, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.constants import (
    CONTENT_TYPE_CODE,
    CONTENT_TYPE_COLOR,
    CONTENT_TYPE_EMAIL,
    CONTENT_TYPE_IMAGE,
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_URL,
)
from app.paths import AppPaths
from core.i18n import LocalizationManager, tr
from models.clip import Clip
from models.collection import Collection


class ClipCard(QFrame):
    """Interactive card representing a single Clip entry in All Clips, Pinned, or Favorites."""

    clicked = Signal(object)
    double_clicked = Signal(object)
    copy_requested = Signal(object)
    pin_toggled = Signal(object)
    favorite_toggled = Signal(object)
    delete_requested = Signal(object)
    collection_assigned = Signal(object, object)  # (Clip, Optional[int])

    _ICON_MAP = {
        CONTENT_TYPE_COLOR: "colors",
        CONTENT_TYPE_URL: "link",
        CONTENT_TYPE_JSON: "json",
        CONTENT_TYPE_CODE: "snippets",
        CONTENT_TYPE_EMAIL: "email",
        CONTENT_TYPE_IMAGE: "images",
    }

    def __init__(
        self,
        clip: Clip,
        collections: Optional[List[Collection]] = None,
        compact: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.clip = clip
        self.collections = collections or []
        self.setObjectName("ClipCard")
        self.setProperty("selected", "false")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        pad_v = 8 if compact else 12
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(14, pad_v, 14, pad_v)
        main_layout.setSpacing(12)

        # Left indicator: Color swatch if color clip, else type icon
        if clip.content_type == CONTENT_TYPE_COLOR:
            hex_color = clip.metadata.get("hex", "#A78BFA")
            swatch = QFrame(self)
            swatch.setFixedSize(34, 34)
            swatch.setStyleSheet(
                f"background-color: {hex_color}; border: 1px solid #30313B; border-radius: 8px;"
            )
            main_layout.addWidget(swatch)
        else:
            icon_lbl = QLabel(self)
            icon_lbl.setFixedSize(34, 34)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setStyleSheet(
                "background-color: #1C1D23; border: 1px solid #292A32; border-radius: 8px;"
            )
            icon_name = self._ICON_MAP.get(clip.content_type, "text")
            svg_file = AppPaths.get_icons_dir() / f"{icon_name}_active.svg"
            if svg_file.exists():
                icon_lbl.setPixmap(QIcon(str(svg_file)).pixmap(18, 18))
            main_layout.addWidget(icon_lbl)

        # Center stack: preview + metadata row
        center_col = QVBoxLayout()
        center_col.setSpacing(4)

        preview_text = (clip.preview or clip.text_content or "").replace("\n", " ")[:150]
        self.preview_lbl = QLabel(preview_text, self)
        self.preview_lbl.setStyleSheet(
            "font-size: 13px; font-weight: 500; color: #F4F2FA; background: transparent;"
        )
        center_col.addWidget(self.preview_lbl)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)

        type_badge = QLabel(tr(f"type.{clip.content_type}"), self)
        type_badge.setStyleSheet(
            "font-size: 11px; color: #A78BFA; background-color: rgba(167, 139, 250, 0.12); padding: 1px 6px; border-radius: 4px;"
        )
        meta_row.addWidget(type_badge)

        if clip.is_demo:
            demo_badge = QLabel(tr("demo.badge"), self)
            demo_badge.setStyleSheet(
                "font-size: 10px; font-weight: 700; color: #17181C; background-color: #E9BB70; padding: 1px 6px; border-radius: 4px;"
            )
            meta_row.addWidget(demo_badge)

        if clip.collection_name:
            col_color = clip.collection_color or "#A78BFA"
            col_badge = QLabel(clip.collection_name, self)
            col_badge.setStyleSheet(
                f"font-size: 11px; color: {col_color}; border: 1px solid {col_color}; padding: 0px 6px; border-radius: 4px; background: transparent;"
            )
            meta_row.addWidget(col_badge)

        rel_time = LocalizationManager.instance().format_relative_time(clip.last_copied_at)
        time_lbl = QLabel(rel_time, self)
        time_lbl.setStyleSheet("font-size: 11px; color: #72717E; background: transparent;")
        meta_row.addWidget(time_lbl)
        meta_row.addStretch(1)
        center_col.addLayout(meta_row)

        main_layout.addLayout(center_col, stretch=1)

        # Right quick action buttons (Pin, Favorite, Copy)
        actions_row = QHBoxLayout()
        actions_row.setSpacing(6)

        self.pin_btn = QPushButton(self)
        self.pin_btn.setFixedSize(28, 28)
        self.pin_btn.setToolTip(tr("action.unpin") if clip.is_pinned else tr("action.pin"))
        pin_icon = "pinned_active.svg" if clip.is_pinned else "pinned.svg"
        self.pin_btn.setIcon(QIcon(str(AppPaths.get_icons_dir() / pin_icon)))
        self.pin_btn.clicked.connect(lambda: self.pin_toggled.emit(self.clip))
        actions_row.addWidget(self.pin_btn)

        self.fav_btn = QPushButton(self)
        self.fav_btn.setFixedSize(28, 28)
        self.fav_btn.setToolTip(tr("action.unfavorite") if clip.is_favorite else tr("action.favorite"))
        fav_icon = "favorites_active.svg" if clip.is_favorite else "favorites.svg"
        self.fav_btn.setIcon(QIcon(str(AppPaths.get_icons_dir() / fav_icon)))
        self.fav_btn.clicked.connect(lambda: self.favorite_toggled.emit(self.clip))
        actions_row.addWidget(self.fav_btn)

        self.copy_btn = QPushButton(tr("action.copy"), self)
        self.copy_btn.setFixedHeight(28)
        self.copy_btn.setToolTip(tr("action.restore"))
        self.copy_btn.clicked.connect(lambda: self.copy_requested.emit(self.clip))
        actions_row.addWidget(self.copy_btn)

        main_layout.addLayout(actions_row)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.clip)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.clip)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)

        act_copy = QAction(tr("action.copy"), self)
        act_copy.triggered.connect(lambda: self.copy_requested.emit(self.clip))
        menu.addAction(act_copy)

        act_restore = QAction(tr("action.restore"), self)
        act_restore.triggered.connect(lambda: self.copy_requested.emit(self.clip))
        menu.addAction(act_restore)

        menu.addSeparator()

        act_pin = QAction(tr("action.unpin") if self.clip.is_pinned else tr("action.pin"), self)
        act_pin.triggered.connect(lambda: self.pin_toggled.emit(self.clip))
        menu.addAction(act_pin)

        act_fav = QAction(
            tr("action.unfavorite") if self.clip.is_favorite else tr("action.favorite"), self
        )
        act_fav.triggered.connect(lambda: self.favorite_toggled.emit(self.clip))
        menu.addAction(act_fav)

        if self.collections:
            col_menu = menu.addMenu(tr("action.add_to_collection"))
            for col in self.collections:
                a = QAction(col.name, self)
                a.triggered.connect(
                    lambda checked=False, cid=col.id: self.collection_assigned.emit(self.clip, cid)
                )
                col_menu.addAction(a)
            if self.clip.collection_id is not None:
                col_menu.addSeparator()
                rem = QAction(tr("action.remove_from_collection"), self)
                rem.triggered.connect(lambda: self.collection_assigned.emit(self.clip, None))
                col_menu.addAction(rem)

        menu.addSeparator()
        act_details = QAction(tr("action.view_details"), self)
        act_details.triggered.connect(lambda: self.clicked.emit(self.clip))
        menu.addAction(act_details)

        act_del = QAction(tr("action.delete"), self)
        act_del.triggered.connect(lambda: self.delete_requested.emit(self.clip))
        menu.addAction(act_del)

        menu.exec(event.globalPos())
