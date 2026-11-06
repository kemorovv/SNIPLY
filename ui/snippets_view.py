"""
Snippets Library View for SNIPLY.
Manages manually saved reusable templates (prompts, commands, code templates, email responses)
with search, creation, editing, duplication, pinning, and 1-click copy.
"""

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.clipboard_manager import ClipboardManager
from core.i18n import LocalizationManager, tr, tr_plural
from models.snippet import Snippet
from ui.widgets.empty_state import EmptyStateWidget


class SnippetEditorDialog(QDialog):
    """Modal dialog for creating or editing a reusable Snippet."""

    def __init__(
        self,
        snippet: Optional[Snippet] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(
            tr("snippets.edit_title") if snippet else tr("snippets.create_title")
        )
        self.setMinimumSize(480, 420)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit(snippet.name if snippet else "", self)
        form.addRow(tr("snippets.name_label"), self.name_edit)

        self.desc_edit = QLineEdit(snippet.description if snippet else "", self)
        form.addRow(tr("snippets.description_label"), self.desc_edit)

        self.cat_edit = QLineEdit(snippet.category if snippet else "General", self)
        form.addRow(tr("snippets.category_label"), self.cat_edit)

        self.tags_edit = QLineEdit(snippet.tags_str if snippet else "", self)
        form.addRow(tr("snippets.tags_label"), self.tags_edit)

        layout.addLayout(form)

        content_lbl = QLabel(tr("snippets.content_label"), self)
        layout.addWidget(content_lbl)

        self.content_edit = QPlainTextEdit(snippet.content if snippet else "", self)
        self.content_edit.setMinimumHeight(160)
        layout.addWidget(self.content_edit, stretch=1)

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


class SnippetsView(QFrame):
    """Snippets Library page for managing reusable templates."""

    snippet_copied = Signal(str)

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
        self.title_lbl = QLabel(tr("navigation.snippets"), self)
        self.title_lbl.setStyleSheet("font-size: 20px; font-weight: 700; color: #F4F2FA;")
        header_row.addWidget(self.title_lbl)

        self.count_badge = QLabel("0", self)
        self.count_badge.setStyleSheet(
            "font-size: 12px; color: #A3A1AE; background-color: #22232A; border: 1px solid #292A32; padding: 2px 10px; border-radius: 10px;"
        )
        header_row.addWidget(self.count_badge)
        header_row.addStretch(1)

        self.new_btn = QPushButton(f"+ {tr('snippets.new_button')}", self)
        self.new_btn.setObjectName("PrimaryButton")
        self.new_btn.clicked.connect(self._create_snippet)
        header_row.addWidget(self.new_btn)
        main_layout.addLayout(header_row)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText(tr("search.snippets_placeholder"))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(lambda _t: self.refresh_snippets())
        main_layout.addWidget(self.search_input)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.list_container = QWidget(self.scroll)
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 4, 4, 12)
        self.list_layout.setSpacing(10)
        self.scroll.setWidget(self.list_container)
        main_layout.addWidget(self.scroll, stretch=1)

        self.empty_state = EmptyStateWidget(
            icon_name="snippets",
            title=tr("empty.snippets.title"),
            subtitle=tr("empty.snippets.subtitle"),
            action_text=f"+ {tr('snippets.new_button')}",
            on_action=self._create_snippet,
            parent=self,
        )
        self.empty_state.hide()
        main_layout.addWidget(self.empty_state, stretch=1)

        LocalizationManager.instance().subscribe(self._on_language_changed)

    def refresh_snippets(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        snippets: List[Snippet] = self.storage.list_snippets(
            search_query=self.search_input.text().strip()
        )
        self.count_badge.setText(tr_plural("items.count", len(snippets)))

        if not snippets:
            self.scroll.hide()
            self.empty_state.show()
            return

        self.empty_state.hide()
        self.scroll.show()

        for snip in snippets:
            card = self._build_snippet_card(snip)
            self.list_layout.addWidget(card)
        self.list_layout.addStretch(1)

    def _build_snippet_card(self, snip: Snippet) -> QFrame:
        card = QFrame(self.list_container)
        card.setObjectName("SnippetCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        title = QLabel(snip.name, card)
        title.setStyleSheet("font-size: 14px; font-weight: 600; color: #F4F2FA; background: transparent;")
        top_row.addWidget(title)

        cat_badge = QLabel(snip.category, card)
        cat_badge.setStyleSheet(
            "font-size: 11px; color: #A78BFA; background-color: rgba(167, 139, 250, 0.14); padding: 1px 7px; border-radius: 4px;"
        )
        top_row.addWidget(cat_badge)
        top_row.addStretch(1)

        copy_btn = QPushButton(tr("action.copy"), card)
        copy_btn.setObjectName("PrimaryButton")
        copy_btn.setFixedHeight(26)
        copy_btn.clicked.connect(lambda checked=False, s=snip: self._copy_snippet(s))
        top_row.addWidget(copy_btn)

        edit_btn = QPushButton(tr("action.edit"), card)
        edit_btn.setFixedHeight(26)
        edit_btn.clicked.connect(lambda checked=False, s=snip: self._edit_snippet(s))
        top_row.addWidget(edit_btn)

        dup_btn = QPushButton(tr("action.duplicate"), card)
        dup_btn.setFixedHeight(26)
        dup_btn.clicked.connect(lambda checked=False, s=snip: self._duplicate_snippet(s))
        top_row.addWidget(dup_btn)

        del_btn = QPushButton(tr("action.delete"), card)
        del_btn.setObjectName("DangerButton")
        del_btn.setFixedHeight(26)
        del_btn.clicked.connect(lambda checked=False, s=snip: self._delete_snippet(s))
        top_row.addWidget(del_btn)

        layout.addLayout(top_row)

        if snip.description:
            desc = QLabel(snip.description, card)
            desc.setStyleSheet("font-size: 12px; color: #A3A1AE; background: transparent;")
            layout.addWidget(desc)

        preview = QLabel(snip.content[:240], card)
        preview.setWordWrap(True)
        preview.setStyleSheet(
            "font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 12px; color: #F4F2FA; background-color: #17181C; border: 1px solid #292A32; border-radius: 6px; padding: 8px;"
        )
        layout.addWidget(preview)
        return card

    def _copy_snippet(self, snip: Snippet) -> None:
        self.clipboard_manager.copy_custom_text(snip.content)
        if snip.id is not None:
            self.storage.mark_snippet_used(snip.id)
        self.snippet_copied.emit(snip.content)

    def _create_snippet(self) -> None:
        dlg = SnippetEditorDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name = dlg.name_edit.text().strip()
            content = dlg.content_edit.toPlainText()
            if name and content:
                tags = [t.strip() for t in dlg.tags_edit.text().split(",") if t.strip()]
                self.storage.create_snippet(
                    Snippet(
                        name=name,
                        description=dlg.desc_edit.text().strip(),
                        content=content,
                        category=dlg.cat_edit.text().strip() or "General",
                        tags=tags,
                    )
                )
                self.refresh_snippets()

    def _edit_snippet(self, snip: Snippet) -> None:
        dlg = SnippetEditorDialog(snippet=snip, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            snip.name = dlg.name_edit.text().strip() or snip.name
            snip.description = dlg.desc_edit.text().strip()
            snip.category = dlg.cat_edit.text().strip() or "General"
            snip.tags = [t.strip() for t in dlg.tags_edit.text().split(",") if t.strip()]
            snip.content = dlg.content_edit.toPlainText()
            self.storage.update_snippet(snip)
            self.refresh_snippets()

    def _duplicate_snippet(self, snip: Snippet) -> None:
        if snip.id is not None:
            self.storage.duplicate_snippet(snip.id)
            self.refresh_snippets()

    def _delete_snippet(self, snip: Snippet) -> None:
        if snip.id is not None:
            self.storage.delete_snippet(snip.id)
            self.refresh_snippets()

    def _on_language_changed(self, _lang: str) -> None:
        self.title_lbl.setText(tr("navigation.snippets"))
        self.new_btn.setText(f"+ {tr('snippets.new_button')}")
        self.search_input.setPlaceholderText(tr("search.snippets_placeholder"))
        self.empty_state.set_texts(
            tr("empty.snippets.title"),
            tr("empty.snippets.subtitle"),
            f"+ {tr('snippets.new_button')}",
        )
        self.refresh_snippets()
