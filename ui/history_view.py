"""
History View for All Clips, Pinned, and Favorites pages.
Supports debounced search, type filtering, sorting, list/grid toggle,
pagination, multi-selection deletion, and Demo Gallery banner.
"""

from typing import List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.constants import (
    CONTENT_TYPE_CODE,
    CONTENT_TYPE_COLOR,
    CONTENT_TYPE_EMAIL,
    CONTENT_TYPE_IMAGE,
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_TEXT,
    CONTENT_TYPE_URL,
)
from core.clipboard_manager import ClipboardManager
from core.i18n import LocalizationManager, tr, tr_plural
from models.clip import Clip
from models.collection import Collection
from ui.widgets.clip_card import ClipCard
from ui.widgets.demo_banner import DemoBanner
from ui.widgets.empty_state import EmptyStateWidget


class HistoryView(QFrame):
    """Main clipboard history view supporting All Clips, Pinned Only, Favorites Only, or Collection filter."""

    clip_selected = Signal(object)
    clip_copied = Signal(object)
    history_mutated = Signal()

    def __init__(
        self,
        clipboard_manager: ClipboardManager,
        mode: str = "all_clips",  # 'all_clips' | 'pinned' | 'favorites'
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.clipboard_manager = clipboard_manager
        self.storage = clipboard_manager.storage
        self.mode = mode
        self._active_collection_id: Optional[int] = None
        self._selected_clip_id: Optional[int] = None
        self._cards: List[ClipCard] = []

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(180)
        self._search_timer.timeout.connect(self.refresh_entries)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # Header Row: Title + Item Count + Inspector Toggle
        top_row = QHBoxLayout()
        self.page_title = QLabel(self._get_title_text(), self)
        self.page_title.setStyleSheet("font-size: 20px; font-weight: 700; color: #F4F2FA;")
        top_row.addWidget(self.page_title)

        self.count_badge = QLabel("0", self)
        self.count_badge.setStyleSheet(
            "font-size: 12px; color: #A3A1AE; background-color: #22232A; border: 1px solid #292A32; padding: 2px 10px; border-radius: 10px;"
        )
        top_row.addWidget(self.count_badge)
        top_row.addStretch(1)
        main_layout.addLayout(top_row)

        # Demo Mode Banner (visible only when demo_mode is active)
        self.demo_banner = DemoBanner(on_exit=self._exit_demo_mode, parent=self)
        self.demo_banner.hide()
        main_layout.addWidget(self.demo_banner)

        # Toolbar: Debounced Search + Type Filter + Sort Selector
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText(tr("search.placeholder"))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(lambda _t: self._search_timer.start())
        toolbar.addWidget(self.search_input, stretch=1)

        self.filter_combo = QComboBox(self)
        self._populate_filter_combo()
        self.filter_combo.currentIndexChanged.connect(lambda _i: self.refresh_entries())
        toolbar.addWidget(self.filter_combo)

        self.sort_combo = QComboBox(self)
        self._populate_sort_combo()
        self.sort_combo.currentIndexChanged.connect(lambda _i: self.refresh_entries())
        toolbar.addWidget(self.sort_combo)

        main_layout.addLayout(toolbar)

        # Scrollable Cards Container
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.list_container = QWidget(self.scroll)
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 4, 4, 12)
        self.list_layout.setSpacing(8)
        self.scroll.setWidget(self.list_container)
        main_layout.addWidget(self.scroll, stretch=1)

        self.empty_state = EmptyStateWidget(
            icon_name="all_clips",
            title=tr("empty.history.title"),
            subtitle=tr("empty.history.subtitle"),
            action_text=tr("demo.enter_button"),
            on_action=self._enter_demo_mode,
            parent=self,
        )
        self.empty_state.hide()
        main_layout.addWidget(self.empty_state, stretch=1)

        LocalizationManager.instance().subscribe(self._on_language_changed)

    def _get_title_text(self) -> str:
        if self.mode == "pinned":
            return tr("navigation.pinned")
        if self.mode == "favorites":
            return tr("navigation.favorites")
        return tr("navigation.all_clips")

    def _populate_filter_combo(self) -> None:
        current_data = self.filter_combo.currentData() or "all"
        self.filter_combo.blockSignals(True)
        self.filter_combo.clear()
        options = [
            ("all", tr("filter.all")),
            (CONTENT_TYPE_TEXT, tr("filter.text")),
            (CONTENT_TYPE_COLOR, tr("filter.color")),
            (CONTENT_TYPE_URL, tr("filter.url")),
            (CONTENT_TYPE_JSON, tr("filter.json")),
            (CONTENT_TYPE_CODE, tr("filter.code")),
            (CONTENT_TYPE_EMAIL, tr("filter.email")),
            (CONTENT_TYPE_IMAGE, tr("filter.image")),
        ]
        for idx, (val, label) in enumerate(options):
            self.filter_combo.addItem(label, val)
            if val == current_data:
                self.filter_combo.setCurrentIndex(idx)
        self.filter_combo.blockSignals(False)

    def _populate_sort_combo(self) -> None:
        current_data = self.sort_combo.currentData() or "recent_copied"
        self.sort_combo.blockSignals(True)
        self.sort_combo.clear()
        options = [
            ("recent_copied", tr("sort.recent_copied")),
            ("recent_used", tr("sort.recent_used")),
            ("most_used", tr("sort.most_used")),
            ("oldest", tr("sort.oldest")),
        ]
        for idx, (val, label) in enumerate(options):
            self.sort_combo.addItem(label, val)
            if val == current_data:
                self.sort_combo.setCurrentIndex(idx)
        self.sort_combo.blockSignals(False)

    def set_mode(self, mode: str, collection_id: Optional[int] = None) -> None:
        self.mode = mode
        self._active_collection_id = collection_id
        self.page_title.setText(self._get_title_text())
        self.refresh_entries()

    def _enter_demo_mode(self) -> None:
        self.clipboard_manager.demo_mode = True
        self.refresh_entries()

    def _exit_demo_mode(self) -> None:
        self.clipboard_manager.demo_mode = False
        self.refresh_entries()

    def refresh_entries(self) -> None:
        # Clear existing card widgets
        self._cards.clear()
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        search_q = self.search_input.text().strip()
        filter_type = self.filter_combo.currentData()
        sort_by = self.sort_combo.currentData() or "recent_copied"

        if self.clipboard_manager.demo_mode:
            self.demo_banner.show()
            clips = ClipboardManager.get_demo_clips()
            if filter_type and filter_type != "all":
                clips = [c for c in clips if c.content_type == filter_type]
            if self.mode == "pinned":
                clips = [c for c in clips if c.is_pinned]
            elif self.mode == "favorites":
                clips = [c for c in clips if c.is_favorite]
            if search_q:
                q_low = search_q.casefold()
                clips = [
                    c
                    for c in clips
                    if q_low in (c.text_content or "").casefold()
                    or q_low in c.preview.casefold()
                ]
        else:
            self.demo_banner.hide()
            clips = self.storage.query_clips(
                search_query=search_q,
                content_type=filter_type,
                only_pinned=(self.mode == "pinned"),
                only_favorites=(self.mode == "favorites"),
                collection_id=self._active_collection_id,
                sort_by=sort_by,
                limit=250,
            )

        self.count_badge.setText(tr_plural("items.count", len(clips)))
        collections: List[Collection] = self.storage.list_collections()
        compact = self.clipboard_manager.settings.density == "compact"

        if not clips:
            self.scroll.hide()
            if search_q:
                self.empty_state.set_texts(
                    tr("empty.search.title"), tr("empty.search.subtitle"), None
                )
            elif self.mode == "pinned":
                self.empty_state.set_texts(
                    tr("empty.pinned.title"), tr("empty.pinned.subtitle"), None
                )
            elif self.mode == "favorites":
                self.empty_state.set_texts(
                    tr("empty.favorites.title"), tr("empty.favorites.subtitle"), None
                )
            else:
                self.empty_state.set_texts(
                    tr("empty.history.title"),
                    tr("empty.history.subtitle"),
                    tr("demo.enter_button"),
                )
            self.empty_state.show()
            return

        self.empty_state.hide()
        self.scroll.show()

        for clip in clips:
            card = ClipCard(
                clip=clip,
                collections=collections,
                compact=compact,
                parent=self.list_container,
            )
            if clip.id == self._selected_clip_id:
                card.set_selected(True)
            card.clicked.connect(self._on_card_clicked)
            card.double_clicked.connect(self._on_card_copy)
            card.copy_requested.connect(self._on_card_copy)
            card.pin_toggled.connect(self._on_pin_toggled)
            card.favorite_toggled.connect(self._on_fav_toggled)
            card.delete_requested.connect(self._on_delete_requested)
            card.collection_assigned.connect(self._on_collection_assigned)
            self._cards.append(card)
            self.list_layout.addWidget(card)

        self.list_layout.addStretch(1)

    def _on_card_clicked(self, clip: Clip) -> None:
        self._selected_clip_id = clip.id
        for card in self._cards:
            card.set_selected(card.clip.id == clip.id)
        self.clip_selected.emit(clip)

    def _on_card_copy(self, clip: Clip) -> None:
        self.clipboard_manager.restore_clip_to_clipboard(clip)
        self.clip_copied.emit(clip)

    def _on_pin_toggled(self, clip: Clip) -> None:
        if clip.is_demo or clip.id is None:
            return
        updated = self.storage.set_pinned(clip.id, not clip.is_pinned)
        self.refresh_entries()
        if updated:
            self.clip_selected.emit(updated)
        self.history_mutated.emit()

    def _on_fav_toggled(self, clip: Clip) -> None:
        if clip.is_demo or clip.id is None:
            return
        updated = self.storage.set_favorite(clip.id, not clip.is_favorite)
        self.refresh_entries()
        if updated:
            self.clip_selected.emit(updated)
        self.history_mutated.emit()

    def _on_collection_assigned(self, clip: Clip, collection_id: Optional[int]) -> None:
        if clip.is_demo or clip.id is None:
            return
        updated = self.storage.set_clip_collection(clip.id, collection_id)
        self.refresh_entries()
        if updated:
            self.clip_selected.emit(updated)
        self.history_mutated.emit()

    def _on_delete_requested(self, clip: Clip) -> None:
        if clip.is_demo or clip.id is None:
            return
        if clip.is_pinned:
            resp = QMessageBox.question(
                self,
                tr("dialog.confirm_delete_pinned.title"),
                tr("dialog.confirm_delete_pinned.body"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                return
            self.storage.delete_clip(clip.id, allow_pinned=True)
        else:
            self.storage.delete_clip(clip.id, allow_pinned=False)

        self.refresh_entries()
        self.clip_selected.emit(None)
        self.history_mutated.emit()

    def _on_language_changed(self, _lang: str) -> None:
        self.page_title.setText(self._get_title_text())
        self.search_input.setPlaceholderText(tr("search.placeholder"))
        self.demo_banner.refresh_translations()
        self._populate_filter_combo()
        self._populate_sort_combo()
        self.refresh_entries()
