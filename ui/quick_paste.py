"""
Quick Paste Floating Popup Window for SNIPLY (Default: Ctrl + Shift + V).
Compact 600 × 480 frameless floating window centered near the cursor or screen center,
supporting instant keyboard navigation (Up/Down/Enter/Escape/Ctrl+F), type icons,
pinned badges, and optional safe auto-paste into the previously focused application.
"""

from typing import List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QCursor, QGuiApplication, QIcon, QKeyEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
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
    QUICK_PASTE_HEIGHT,
    QUICK_PASTE_WIDTH,
)
from app.paths import AppPaths
from core.clipboard_manager import ClipboardManager
from core.i18n import LocalizationManager, tr
from core.window_manager import WindowManager
from models.clip import Clip


class QuickPasteWindow(QWidget):
    """Compact floating Quick Paste launcher summoned via global hotkey."""

    clip_restored = Signal(object)

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
        clipboard_manager: ClipboardManager,
        window_manager: WindowManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.clipboard_manager = clipboard_manager
        self.storage = clipboard_manager.storage
        self.window_manager = window_manager
        self._clips: List[Clip] = []

        self.setWindowTitle(tr("quick_paste.title"))
        self.setFixedSize(QUICK_PASTE_WIDTH, QUICK_PASTE_HEIGHT)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(90)
        self._debounce.timeout.connect(self._reload_entries)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.container = QFrame(self)
        self.container.setObjectName("QuickPasteContainer")
        c_layout = QVBoxLayout(self.container)
        c_layout.setContentsMargins(16, 14, 16, 12)
        c_layout.setSpacing(10)

        # Header & Instant Search Bar
        top_row = QHBoxLayout()
        self.title_lbl = QLabel(f"⚡ {tr('quick_paste.title')}", self.container)
        self.title_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #A78BFA;")
        top_row.addWidget(self.title_lbl)
        top_row.addStretch(1)
        c_layout.addLayout(top_row)

        self.search_input = QLineEdit(self.container)
        self.search_input.setPlaceholderText(tr("search.quick_paste_placeholder"))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(lambda _t: self._debounce.start())
        c_layout.addWidget(self.search_input)

        # Compact Entries List
        self.list_widget = QListWidget(self.container)
        self.list_widget.setStyleSheet(
            "QListWidget { background-color: #17181C; border: 1px solid #292A32; border-radius: 10px; padding: 6px; }"
            "QListWidget::item { padding: 9px 12px; border-radius: 7px; color: #F4F2FA; }"
            "QListWidget::item:selected { background-color: rgba(167, 139, 250, 0.22); border: 1px solid rgba(167, 139, 250, 0.45); }"
        )
        self.list_widget.itemDoubleClicked.connect(lambda _item: self._activate_selected())
        c_layout.addWidget(self.list_widget, stretch=1)

        # Footer Keyboard Hints
        self.hint_lbl = QLabel(tr("quick_paste.hint"), self.container)
        self.hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_lbl.setStyleSheet("font-size: 11px; color: #72717E;")
        c_layout.addWidget(self.hint_lbl)

        outer.addWidget(self.container)
        LocalizationManager.instance().subscribe(self._on_language_changed)

    def summon(self, own_hwnds: Optional[set[int]] = None) -> None:
        """Record foreground window, load top recent entries, position near cursor/center, and focus search."""
        self.window_manager.remember_foreground_window(own_hwnds=own_hwnds)
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self._reload_entries()
        self._position_near_cursor()
        self.show()
        self.raise_()
        self.activateWindow()
        self.search_input.setFocus()

    def _position_near_cursor(self) -> None:
        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos) or QGuiApplication.primaryScreen()
        if screen is None:
            return
        avail = screen.availableGeometry()
        x = min(max(avail.left() + 16, cursor_pos.x() - self.width() // 2), avail.right() - self.width() - 16)
        y = min(max(avail.top() + 16, cursor_pos.y() - 60), avail.bottom() - self.height() - 16)
        self.move(x, y)

    def _reload_entries(self) -> None:
        self.list_widget.clear()
        query = self.search_input.text().strip()
        if self.clipboard_manager.demo_mode:
            self._clips = ClipboardManager.get_demo_clips()
        else:
            # Load limited batch (60 entries) for instantaneous opening
            self._clips = self.storage.query_clips(
                search_query=query,
                pinned_first=True,
                limit=60,
            )

        icons_dir = AppPaths.get_icons_dir()
        for clip in self._clips:
            prefix = f"[{tr('quick_paste.pinned_badge')}]  " if clip.is_pinned else ""
            preview = (clip.preview or clip.text_content or "").replace("\n", " ")[:78]
            rel_t = LocalizationManager.instance().format_relative_time(clip.last_copied_at)
            item = QListWidgetItem(f"{prefix}{preview}   —   {rel_t}")
            icon_name = self._ICON_MAP.get(clip.content_type, "text")
            svg_path = icons_dir / f"{icon_name}_active.svg"
            if svg_path.exists():
                item.setIcon(QIcon(str(svg_path)))
            self.list_widget.addItem(item)

        if self._clips:
            self.list_widget.setCurrentRow(0)

    def _activate_selected(self) -> None:
        row = self.list_widget.currentRow()
        if not (0 <= row < len(self._clips)):
            return
        clip = self._clips[row]
        self.clipboard_manager.restore_clip_to_clipboard(clip)
        self.hide()
        self.clip_restored.emit(clip)

        # Optional automatic paste into previous foreground window (OFF by default)
        if self.clipboard_manager.settings.auto_paste_on_quick_select:
            self.window_manager.restore_and_optional_paste(auto_paste=True)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        mods = event.modifiers()

        if key == Qt.Key.Key_Escape:
            self.hide()
            event.accept()
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._activate_selected()
            event.accept()
            return
        if key == Qt.Key.Key_Down:
            nxt = min(self.list_widget.count() - 1, self.list_widget.currentRow() + 1)
            self.list_widget.setCurrentRow(nxt)
            event.accept()
            return
        if key == Qt.Key.Key_Up:
            prv = max(0, self.list_widget.currentRow() - 1)
            self.list_widget.setCurrentRow(prv)
            event.accept()
            return
        if key == Qt.Key.Key_F and (mods & Qt.KeyboardModifier.ControlModifier):
            self.search_input.setFocus()
            self.search_input.selectAll()
            event.accept()
            return

        super().keyPressEvent(event)

    def _on_language_changed(self, _lang: str) -> None:
        self.setWindowTitle(tr("quick_paste.title"))
        self.title_lbl.setText(f"⚡ {tr('quick_paste.title')}")
        self.search_input.setPlaceholderText(tr("search.quick_paste_placeholder"))
        self.hint_lbl.setText(tr("quick_paste.hint"))
        if self.isVisible():
            self._reload_entries()
