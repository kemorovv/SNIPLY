"""
Adaptive Right-Side Inspector Panel for SNIPLY.
Dynamically adapts to the selected Clip's content type:
- Color: Large swatch + HEX, RGB, HSL, Alpha conversions and 1-click copy buttons.
- JSON: Syntax validation badge, collapsible QTreeWidget structure viewer, pretty & minified copy actions.
- Code: Language badge, Pygments syntax-highlighted preview, and original copy button.
- URL: Domain breakdown, Copy URL, and Open in Default Browser button.
- Image: High-resolution preview, dimensions, format, file size, and Save to Disk action.
- Text / Email: Full text preview, character/word/line counts, reading time, collection selector, and tag editor.
"""

import json
from pathlib import Path
import shutil
from typing import Any, List, Optional
import webbrowser

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
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
    INSPECTOR_DEFAULT_WIDTH,
)
from core.i18n import LocalizationManager, tr, tr_plural
from models.clip import Clip
from models.collection import Collection


class InspectorPanel(QFrame):
    """Collapsible right-side detail inspector adapting to each clip type."""

    copy_text_requested = Signal(str)
    copy_clip_requested = Signal(object)
    collection_changed = Signal(object, object)  # (Clip, Optional[int])
    tags_changed = Signal(object, list)  # (Clip, List[str])

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("InspectorPanel")
        self.setFixedWidth(INSPECTOR_DEFAULT_WIDTH)

        self._current_clip: Optional[Clip] = None
        self._collections: List[Collection] = []

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.body_widget = QWidget(scroll)
        self.body_layout = QVBoxLayout(self.body_widget)
        self.body_layout.setContentsMargins(16, 16, 16, 16)
        self.body_layout.setSpacing(12)
        scroll.setWidget(self.body_widget)
        outer_layout.addWidget(scroll)

        self._render_empty()
        LocalizationManager.instance().subscribe(self._on_language_changed)

    def set_collections(self, collections: List[Collection]) -> None:
        self._collections = list(collections)
        if self._current_clip is not None:
            self.inspect_clip(self._current_clip)

    def _clear_body(self) -> None:
        while self.body_layout.count():
            item = self.body_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _render_empty(self) -> None:
        self._clear_body()
        header = QLabel(tr("inspector.title"), self.body_widget)
        header.setStyleSheet("font-size: 15px; font-weight: 700; color: #F4F2FA;")
        self.body_layout.addWidget(header)

        empty_lbl = QLabel(tr("inspector.no_selection"), self.body_widget)
        empty_lbl.setWordWrap(True)
        empty_lbl.setStyleSheet("color: #72717E; font-size: 13px; margin-top: 24px;")
        self.body_layout.addWidget(empty_lbl)
        self.body_layout.addStretch(1)

    def inspect_clip(self, clip: Optional[Clip]) -> None:
        self._current_clip = clip
        if clip is None:
            self._render_empty()
            return

        self._clear_body()

        # Header Row
        title_row = QHBoxLayout()
        header = QLabel(tr("inspector.title"), self.body_widget)
        header.setStyleSheet("font-size: 15px; font-weight: 700; color: #F4F2FA;")
        title_row.addWidget(header)
        title_row.addStretch(1)

        type_pill = QLabel(tr(f"type.{clip.content_type}"), self.body_widget)
        type_pill.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #A78BFA; background-color: rgba(167, 139, 250, 0.14); padding: 2px 8px; border-radius: 5px;"
        )
        title_row.addWidget(type_pill)
        self.body_layout.addLayout(title_row)

        # Render specialized view based on content_type
        if clip.content_type == CONTENT_TYPE_COLOR:
            self._build_color_section(clip)
        elif clip.content_type == CONTENT_TYPE_JSON:
            self._build_json_section(clip)
        elif clip.content_type == CONTENT_TYPE_CODE:
            self._build_code_section(clip)
        elif clip.content_type == CONTENT_TYPE_URL:
            self._build_url_section(clip)
        elif clip.content_type == CONTENT_TYPE_IMAGE:
            self._build_image_section(clip)
        else:
            self._build_text_section(clip)

        # Common Metadata & Organization Card
        self._build_common_metadata(clip)
        self.body_layout.addStretch(1)

    def _build_color_section(self, clip: Clip) -> None:
        meta = clip.metadata or {}
        hex_val = meta.get("hex_full") or meta.get("hex") or clip.text_content or "#A78BFA"
        rgb_val = meta.get("rgb_str") or "rgb(167, 139, 250)"
        hsl_val = meta.get("hsl_str") or "hsl(255, 92%, 76%)"
        alpha_val = meta.get("alpha", 1.0)

        swatch = QFrame(self.body_widget)
        swatch.setFixedHeight(96)
        swatch.setStyleSheet(
            f"background-color: {meta.get('hex', '#A78BFA')}; border: 1px solid #30313B; border-radius: 10px;"
        )
        self.body_layout.addWidget(swatch)

        conv_title = QLabel(tr("inspector.color_conversions"), self.body_widget)
        conv_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #A3A1AE;")
        self.body_layout.addWidget(conv_title)

        for label, value, btn_key in (
            ("HEX", hex_val, "action.copy_hex"),
            ("RGB", rgb_val, "action.copy_rgb"),
            ("HSL", hsl_val, "action.copy_hsl"),
        ):
            row = QHBoxLayout()
            val_lbl = QLabel(f"{label}:  {value}", self.body_widget)
            val_lbl.setStyleSheet("font-size: 12px; color: #F4F2FA;")
            row.addWidget(val_lbl, stretch=1)

            copy_btn = QPushButton(tr(btn_key), self.body_widget)
            copy_btn.setFixedHeight(26)
            copy_btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
            copy_btn.clicked.connect(lambda checked=False, v=value: self.copy_text_requested.emit(v))
            row.addWidget(copy_btn)
            self.body_layout.addLayout(row)

        alpha_lbl = QLabel(f"{tr('inspector.alpha')}: {int(float(alpha_val) * 100)}%", self.body_widget)
        alpha_lbl.setStyleSheet("font-size: 12px; color: #72717E;")
        self.body_layout.addWidget(alpha_lbl)

    def _build_json_section(self, clip: Clip) -> None:
        meta = clip.metadata or {}
        is_valid = bool(meta.get("valid", True))
        status_lbl = QLabel(
            tr("inspector.json_valid") if is_valid else f"{tr('inspector.json_invalid')}: {meta.get('error', '')}",
            self.body_widget,
        )
        status_color = "#6DD6A5" if is_valid else "#F07886"
        status_lbl.setWordWrap(True)
        status_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {status_color};")
        self.body_layout.addWidget(status_lbl)

        if is_valid:
            tree_lbl = QLabel(tr("inspector.json_tree"), self.body_widget)
            tree_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #A3A1AE;")
            self.body_layout.addWidget(tree_lbl)

            tree = QTreeWidget(self.body_widget)
            tree.setHeaderHidden(True)
            tree.setMinimumHeight(180)
            tree.setStyleSheet(
                "background-color: #17181C; border: 1px solid #30313B; border-radius: 8px; padding: 4px;"
            )
            try:
                parsed = json.loads(clip.text_content or "{}")
                self._populate_json_tree(tree.invisibleRootItem(), parsed)
                tree.expandToDepth(1)
            except Exception:
                pass
            self.body_layout.addWidget(tree)

            pretty_str = meta.get("pretty") or clip.text_content or ""
            min_str = meta.get("minified") or clip.text_content or ""

            btn_pretty = QPushButton(tr("action.copy_formatted_json"), self.body_widget)
            btn_pretty.setObjectName("PrimaryButton")
            btn_pretty.clicked.connect(lambda: self.copy_text_requested.emit(pretty_str))
            self.body_layout.addWidget(btn_pretty)

            btn_min = QPushButton(tr("action.copy_minified_json"), self.body_widget)
            btn_min.clicked.connect(lambda: self.copy_text_requested.emit(min_str))
            self.body_layout.addWidget(btn_min)

    def _populate_json_tree(self, parent_item: QTreeWidgetItem, data: Any, key_name: str = "") -> None:
        if isinstance(data, dict):
            label = f"{key_name}: {{ {len(data)} keys }}" if key_name else f"{{ {len(data)} keys }}"
            node = QTreeWidgetItem(parent_item, [label])
            for k, v in list(data.items())[:100]:
                self._populate_json_tree(node, v, str(k))
        elif isinstance(data, list):
            label = f"{key_name}: [ {len(data)} items ]" if key_name else f"[ {len(data)} items ]"
            node = QTreeWidgetItem(parent_item, [label])
            for idx, v in enumerate(data[:100]):
                self._populate_json_tree(node, v, f"[{idx}]")
        else:
            val_repr = json.dumps(data, ensure_ascii=False)
            text = f"{key_name}: {val_repr}" if key_name else val_repr
            QTreeWidgetItem(parent_item, [text])

    def _build_code_section(self, clip: Clip) -> None:
        meta = clip.metadata or {}
        lang = meta.get("language", "Code")
        lang_lbl = QLabel(f"{tr('inspector.language')}: {lang}", self.body_widget)
        lang_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #A3A1AE;")
        self.body_layout.addWidget(lang_lbl)

        browser = QTextBrowser(self.body_widget)
        browser.setMinimumHeight(210)
        browser.setStyleSheet(
            "background-color: #17181C; border: 1px solid #30313B; border-radius: 8px;"
        )
        html_preview = meta.get("highlighted_html")
        if html_preview:
            browser.setHtml(html_preview)
        else:
            browser.setPlainText(clip.text_content or "")
        self.body_layout.addWidget(browser)

        btn_copy = QPushButton(tr("action.copy_original"), self.body_widget)
        btn_copy.setObjectName("PrimaryButton")
        btn_copy.clicked.connect(lambda: self.copy_clip_requested.emit(clip))
        self.body_layout.addWidget(btn_copy)

    def _build_url_section(self, clip: Clip) -> None:
        meta = clip.metadata or {}
        url_str = meta.get("url") or (clip.text_content or "").strip()
        domain = meta.get("domain", "")

        dom_lbl = QLabel(f"{tr('inspector.domain')}:  {domain}", self.body_widget)
        dom_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #F4F2FA;")
        self.body_layout.addWidget(dom_lbl)

        url_box = QTextBrowser(self.body_widget)
        url_box.setMaximumHeight(90)
        url_box.setPlainText(url_str)
        url_box.setStyleSheet(
            "background-color: #17181C; border: 1px solid #30313B; border-radius: 8px; color: #A78BFA;"
        )
        self.body_layout.addWidget(url_box)

        btn_copy = QPushButton(tr("action.copy"), self.body_widget)
        btn_copy.setObjectName("PrimaryButton")
        btn_copy.clicked.connect(lambda: self.copy_text_requested.emit(url_str))
        self.body_layout.addWidget(btn_copy)

        btn_open = QPushButton(tr("action.open_url"), self.body_widget)
        btn_open.clicked.connect(lambda: webbrowser.open(url_str))
        self.body_layout.addWidget(btn_open)

    def _build_image_section(self, clip: Clip) -> None:
        meta = clip.metadata or {}
        img_lbl = QLabel(self.body_widget)
        img_lbl.setMinimumHeight(180)
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_lbl.setStyleSheet(
            "background-color: #17181C; border: 1px solid #30313B; border-radius: 8px;"
        )
        img_path_str = clip.image_path or clip.thumbnail_path
        if img_path_str and Path(img_path_str).exists():
            pix = QPixmap(img_path_str).scaled(
                290,
                200,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            img_lbl.setPixmap(pix)
        self.body_layout.addWidget(img_lbl)

        w, h = meta.get("width", 0), meta.get("height", 0)
        fmt = meta.get("format", "PNG")
        fsize = LocalizationManager.instance().format_file_size(int(meta.get("file_size", 0)))

        info = QLabel(
            f"{tr('inspector.dimensions')}: {w} × {h} px\n"
            f"{tr('inspector.format')}: {fmt}\n"
            f"{tr('inspector.file_size')}: {fsize}",
            self.body_widget,
        )
        info.setStyleSheet("font-size: 12px; color: #A3A1AE; line-height: 1.5;")
        self.body_layout.addWidget(info)

        btn_copy = QPushButton(tr("action.copy"), self.body_widget)
        btn_copy.setObjectName("PrimaryButton")
        btn_copy.clicked.connect(lambda: self.copy_clip_requested.emit(clip))
        self.body_layout.addWidget(btn_copy)

        btn_save = QPushButton(tr("action.save_image_as"), self.body_widget)
        btn_save.clicked.connect(lambda: self._save_image_to_disk(clip))
        self.body_layout.addWidget(btn_save)

    def _save_image_to_disk(self, clip: Clip) -> None:
        if not clip.image_path or not Path(clip.image_path).exists():
            return
        target, _ = QFileDialog.getSaveFileName(
            self,
            tr("action.save_image_as"),
            f"sniply_image_{clip.id or 1}.png",
            "PNG Images (*.png);;All Files (*)",
        )
        if target:
            shutil.copy2(clip.image_path, target)

    def _build_text_section(self, clip: Clip) -> None:
        meta = clip.metadata or {}
        viewer = QTextBrowser(self.body_widget)
        viewer.setMinimumHeight(190)
        viewer.setPlainText(clip.text_content or "")
        viewer.setStyleSheet(
            "background-color: #17181C; border: 1px solid #30313B; border-radius: 8px; padding: 8px;"
        )
        self.body_layout.addWidget(viewer)

        chars = int(meta.get("char_count", len(clip.text_content or "")))
        words = int(meta.get("word_count", len((clip.text_content or "").split())))
        lines = int(meta.get("line_count", len((clip.text_content or "").splitlines()) or 1))
        read_sec = int(meta.get("reading_time_sec", 1))

        stats_text = (
            f"{tr_plural('chars.count', chars)}  •  "
            f"{tr_plural('words.count', words)}  •  "
            f"{tr_plural('lines.count', lines)}\n"
            f"{tr('inspector.reading_time', seconds=read_sec)}"
        )
        stats_lbl = QLabel(stats_text, self.body_widget)
        stats_lbl.setStyleSheet("font-size: 12px; color: #A3A1AE;")
        self.body_layout.addWidget(stats_lbl)

        btn_copy = QPushButton(tr("action.copy"), self.body_widget)
        btn_copy.setObjectName("PrimaryButton")
        btn_copy.clicked.connect(lambda: self.copy_clip_requested.emit(clip))
        self.body_layout.addWidget(btn_copy)

    def _build_common_metadata(self, clip: Clip) -> None:
        sep = QFrame(self.body_widget)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #292A32;")
        self.body_layout.addWidget(sep)

        uses_lbl = QLabel(tr_plural("uses.count", clip.usage_count), self.body_widget)
        uses_lbl.setStyleSheet("font-size: 12px; color: #72717E;")
        self.body_layout.addWidget(uses_lbl)

        if not clip.is_demo:
            # Collection selector
            col_lbl = QLabel(tr("inspector.collection"), self.body_widget)
            col_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #A3A1AE;")
            self.body_layout.addWidget(col_lbl)

            combo = QComboBox(self.body_widget)
            combo.addItem(tr("inspector.no_collection"), None)
            selected_idx = 0
            for idx, col in enumerate(self._collections, start=1):
                combo.addItem(col.name, col.id)
                if col.id == clip.collection_id:
                    selected_idx = idx
            combo.setCurrentIndex(selected_idx)
            combo.currentIndexChanged.connect(
                lambda _i: self.collection_changed.emit(clip, combo.currentData())
            )
            self.body_layout.addWidget(combo)

            # Tags input
            tags_lbl = QLabel(tr("inspector.tags"), self.body_widget)
            tags_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #A3A1AE;")
            self.body_layout.addWidget(tags_lbl)

            tag_input = QLineEdit(", ".join(clip.tags), self.body_widget)
            tag_input.setPlaceholderText(tr("inspector.add_tag_placeholder"))
            tag_input.editingFinished.connect(
                lambda: self.tags_changed.emit(
                    clip,
                    [t.strip() for t in tag_input.text().split(",") if t.strip()],
                )
            )
            self.body_layout.addWidget(tag_input)

    def _on_language_changed(self, _lang: str) -> None:
        self.inspect_clip(self._current_clip)
