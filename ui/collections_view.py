"""
Collections Management View for SNIPLY.
Allows users to create, rename, color-code, delete collections (asking whether to keep or delete underlying entries),
and browse all clips inside any selected collection.
"""

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.clipboard_manager import ClipboardManager
from core.i18n import LocalizationManager, tr, tr_plural
from models.clip import Clip
from models.collection import Collection
from ui.widgets.clip_card import ClipCard


class CollectionEditorDialog(QDialog):
    """Modal dialog for creating or editing a Collection."""

    COLOR_OPTIONS = [
        ("#A78BFA", "Purple"),
        ("#6DD6A5", "Mint Green"),
        ("#E9BB70", "Amber Gold"),
        ("#F07886", "Coral Rose"),
        ("#60A5FA", "Sky Blue"),
        ("#F472B6", "Pink"),
    ]

    def __init__(
        self,
        collection: Optional[Collection] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.collection = collection
        self.setWindowTitle(
            tr("collections.edit_title") if collection else tr("collections.create_title")
        )
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit(collection.name if collection else "", self)
        form.addRow(tr("collections.name_label"), self.name_edit)

        self.desc_edit = QLineEdit(collection.description if collection else "", self)
        form.addRow(tr("collections.description_label"), self.desc_edit)

        self.color_combo = QComboBox(self)
        for idx, (hex_val, name) in enumerate(self.COLOR_OPTIONS):
            self.color_combo.addItem(f"{name} ({hex_val})", hex_val)
            if collection and collection.color.upper() == hex_val.upper():
                self.color_combo.setCurrentIndex(idx)
        form.addRow(tr("collections.color_label"), self.color_combo)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        cancel_btn = QPushButton(tr("action.cancel"), self)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton(tr("action.save"), self)
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)


class CollectionsView(QFrame):
    """Split view for managing collections and viewing entries inside the selected collection."""

    clip_selected = Signal(object)
    clip_copied = Signal(object)
    collections_mutated = Signal()

    def __init__(
        self,
        clipboard_manager: ClipboardManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.clipboard_manager = clipboard_manager
        self.storage = clipboard_manager.storage
        self._collections: List[Collection] = []
        self._selected_collection_id: Optional[int] = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # Top Bar
        header_row = QHBoxLayout()
        self.title_lbl = QLabel(tr("navigation.collections"), self)
        self.title_lbl.setStyleSheet("font-size: 20px; font-weight: 700; color: #F4F2FA;")
        header_row.addWidget(self.title_lbl)
        header_row.addStretch(1)

        self.new_btn = QPushButton(f"+ {tr('collections.new_button')}", self)
        self.new_btn.setObjectName("PrimaryButton")
        self.new_btn.clicked.connect(self._create_collection)
        header_row.addWidget(self.new_btn)

        self.edit_btn = QPushButton(tr("action.edit"), self)
        self.edit_btn.clicked.connect(self._edit_selected_collection)
        header_row.addWidget(self.edit_btn)

        self.del_btn = QPushButton(tr("action.delete"), self)
        self.del_btn.setObjectName("DangerButton")
        self.del_btn.clicked.connect(self._delete_selected_collection)
        header_row.addWidget(self.del_btn)

        main_layout.addLayout(header_row)

        # Content Split: Left collection list + Right entries scroll area
        split_row = QHBoxLayout()
        split_row.setSpacing(16)

        self.col_list = QListWidget(self)
        self.col_list.setFixedWidth(250)
        self.col_list.setStyleSheet(
            "QListWidget { background-color: #1C1D23; border: 1px solid #292A32; border-radius: 10px; padding: 6px; }"
            "QListWidget::item { padding: 9px 10px; border-radius: 7px; }"
            "QListWidget::item:selected { background-color: rgba(167, 139, 250, 0.18); color: #F4F2FA; }"
        )
        self.col_list.currentRowChanged.connect(self._on_collection_row_changed)
        split_row.addWidget(self.col_list)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.clips_container = QWidget(self.scroll)
        self.clips_layout = QVBoxLayout(self.clips_container)
        self.clips_layout.setContentsMargins(0, 0, 4, 0)
        self.clips_layout.setSpacing(8)
        self.scroll.setWidget(self.clips_container)
        split_row.addWidget(self.scroll, stretch=1)

        main_layout.addLayout(split_row, stretch=1)
        LocalizationManager.instance().subscribe(self._on_language_changed)

    def refresh_collections(self) -> None:
        self._collections = self.storage.list_collections()
        self.col_list.blockSignals(True)
        self.col_list.clear()
        selected_row = 0
        for idx, col in enumerate(self._collections):
            count_text = tr_plural("items.count", col.clip_count)
            item = QListWidgetItem(f"●  {col.name}   ({count_text})")
            item.setData(Qt.ItemDataRole.UserRole, col.id)
            self.col_list.addItem(item)
            if col.id == self._selected_collection_id:
                selected_row = idx
        self.col_list.blockSignals(False)

        if self._collections:
            self.col_list.setCurrentRow(selected_row)
            self._selected_collection_id = self._collections[selected_row].id
        else:
            self._selected_collection_id = None
        self._refresh_collection_clips()

    def _on_collection_row_changed(self, row: int) -> None:
        if 0 <= row < len(self._collections):
            self._selected_collection_id = self._collections[row].id
        else:
            self._selected_collection_id = None
        self._refresh_collection_clips()

    def _refresh_collection_clips(self) -> None:
        while self.clips_layout.count():
            item = self.clips_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        if self._selected_collection_id is None:
            return

        clips = self.storage.query_clips(collection_id=self._selected_collection_id, limit=200)
        for clip in clips:
            card = ClipCard(
                clip=clip,
                collections=self._collections,
                parent=self.clips_container,
            )
            card.clicked.connect(lambda c: self.clip_selected.emit(c))
            card.copy_requested.connect(self._on_copy_clip)
            card.pin_toggled.connect(self._on_pin_clip)
            card.favorite_toggled.connect(self._on_fav_clip)
            card.delete_requested.connect(self._on_del_clip)
            card.collection_assigned.connect(self._on_reassign_clip)
            self.clips_layout.addWidget(card)
        self.clips_layout.addStretch(1)

    def _on_copy_clip(self, clip: Clip) -> None:
        self.clipboard_manager.restore_clip_to_clipboard(clip)
        self.clip_copied.emit(clip)

    def _on_pin_clip(self, clip: Clip) -> None:
        if clip.id is not None:
            self.storage.set_pinned(clip.id, not clip.is_pinned)
            self._refresh_collection_clips()

    def _on_fav_clip(self, clip: Clip) -> None:
        if clip.id is not None:
            self.storage.set_favorite(clip.id, not clip.is_favorite)
            self._refresh_collection_clips()

    def _on_del_clip(self, clip: Clip) -> None:
        if clip.id is not None:
            self.storage.delete_clip(clip.id, allow_pinned=True)
            self.refresh_collections()

    def _on_reassign_clip(self, clip: Clip, col_id: Optional[int]) -> None:
        if clip.id is not None:
            self.storage.set_clip_collection(clip.id, col_id)
            self.refresh_collections()
            self.collections_mutated.emit()

    def _create_collection(self) -> None:
        dlg = CollectionEditorDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name = dlg.name_edit.text().strip()
            if name:
                created = self.storage.create_collection(
                    name=name,
                    description=dlg.desc_edit.text().strip(),
                    color=dlg.color_combo.currentData() or "#A78BFA",
                )
                self._selected_collection_id = created.id
                self.refresh_collections()
                self.collections_mutated.emit()

    def _edit_selected_collection(self) -> None:
        col = next((c for c in self._collections if c.id == self._selected_collection_id), None)
        if not col or col.id is None:
            return
        dlg = CollectionEditorDialog(collection=col, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name = dlg.name_edit.text().strip()
            if name:
                self.storage.update_collection(
                    collection_id=col.id,
                    name=name,
                    description=dlg.desc_edit.text().strip(),
                    color=dlg.color_combo.currentData() or col.color,
                )
                self.refresh_collections()
                self.collections_mutated.emit()

    def _delete_selected_collection(self) -> None:
        col = next((c for c in self._collections if c.id == self._selected_collection_id), None)
        if not col or col.id is None:
            return

        msg = QMessageBox(self)
        msg.setWindowTitle(tr("collections.delete_title"))
        msg.setText(tr("collections.delete_prompt", name=col.name))
        btn_keep = msg.addButton(tr("collections.keep_entries"), QMessageBox.ButtonRole.AcceptRole)
        btn_del_all = msg.addButton(
            tr("collections.delete_entries"), QMessageBox.ButtonRole.DestructiveRole
        )
        btn_cancel = msg.addButton(tr("action.cancel"), QMessageBox.ButtonRole.RejectRole)
        msg.exec()

        clicked = msg.clickedButton()
        if clicked == btn_cancel:
            return
        delete_underlying = clicked == btn_del_all
        self.storage.delete_collection(col.id, delete_underlying_clips=delete_underlying)
        self._selected_collection_id = None
        self.refresh_collections()
        self.collections_mutated.emit()

    def _on_language_changed(self, _lang: str) -> None:
        self.title_lbl.setText(tr("navigation.collections"))
        self.new_btn.setText(f"+ {tr('collections.new_button')}")
        self.edit_btn.setText(tr("action.edit"))
        self.del_btn.setText(tr("action.delete"))
        self.refresh_collections()
