"""
Clipboard Insights / Analytics View for SNIPLY.
Displays real statistics computed strictly from stored SQLite records using lightweight custom QPainter charts.
"""

from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.clipboard_manager import ClipboardManager
from core.i18n import LocalizationManager, tr, tr_plural


class DailyActivityBarChart(QWidget):
    """Lightweight custom QPainter 7-day activity bar chart."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(180)
        self._data: List[Tuple[str, int]] = []

    def set_data(self, data: List[Tuple[str, int]]) -> None:
        self._data = list(data)
        self.update()

    def paintEvent(self, _event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        if not self._data or w < 100 or h < 80:
            painter.end()
            return

        max_val = max((cnt for _, cnt in self._data), default=1)
        if max_val <= 0:
            max_val = 1

        n = len(self._data)
        left_pad = 24
        right_pad = 24
        top_pad = 26
        bottom_pad = 32
        usable_w = w - left_pad - right_pad
        usable_h = h - top_pad - bottom_pad
        slot_w = usable_w / max(1, n)
        bar_w = min(44.0, slot_w * 0.56)

        font = QFont("Inter", 9)
        painter.setFont(font)

        for idx, (day_str, count) in enumerate(self._data):
            cx = left_pad + (idx + 0.5) * slot_w
            bx = cx - bar_w / 2.0
            ratio = count / float(max_val)
            bh = max(4.0, ratio * usable_h)
            by = top_pad + (usable_h - bh)

            # Draw subtle track
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#17181C"))
            painter.drawRoundedRect(QRectF(bx, top_pad, bar_w, usable_h), 6, 6)

            # Draw accent bar
            painter.setBrush(QColor("#A78BFA" if count > 0 else "#30313B"))
            painter.drawRoundedRect(QRectF(bx, by, bar_w, bh), 6, 6)

            # Value label above bar
            painter.setPen(QColor("#F4F2FA"))
            painter.drawText(
                QRectF(cx - 25, by - 20, 50, 16),
                Qt.AlignmentFlag.AlignCenter,
                str(count),
            )

            # Date short label below bar (MM-DD)
            short_date = day_str[5:] if len(day_str) >= 10 else day_str
            painter.setPen(QColor("#A3A1AE"))
            painter.drawText(
                QRectF(cx - 28, h - bottom_pad + 6, 56, 20),
                Qt.AlignmentFlag.AlignCenter,
                short_date,
            )

        painter.end()


class InsightsView(QFrame):
    """Analytics dashboard displaying real database metrics."""

    def __init__(
        self,
        clipboard_manager: ClipboardManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.clipboard_manager = clipboard_manager
        self.storage = clipboard_manager.storage

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content = QWidget(scroll)
        self.main_layout = QVBoxLayout(self.content)
        self.main_layout.setContentsMargins(24, 20, 24, 24)
        self.main_layout.setSpacing(16)
        scroll.setWidget(self.content)
        outer_layout.addWidget(scroll)

        # Header
        self.title_lbl = QLabel(tr("navigation.insights"), self.content)
        self.title_lbl.setStyleSheet("font-size: 20px; font-weight: 700; color: #F4F2FA;")
        self.main_layout.addWidget(self.title_lbl)

        self.sub_lbl = QLabel(tr("insights.subtitle"), self.content)
        self.sub_lbl.setStyleSheet("font-size: 13px; color: #A3A1AE;")
        self.main_layout.addWidget(self.sub_lbl)

        # 4 KPI Cards Row
        self.kpi_row = QHBoxLayout()
        self.kpi_row.setSpacing(12)
        self._kpi_labels: Dict[str, Tuple[QLabel, QLabel]] = {}
        for key, trans_key, accent in (
            ("total_clips", "insights.total_clips", "#A78BFA"),
            ("text_entries", "insights.text_clips", "#6DD6A5"),
            ("image_entries", "insights.image_clips", "#E9BB70"),
            ("color_entries", "insights.color_clips", "#F07886"),
        ):
            card = QFrame(self.content)
            card.setObjectName("StatCard")
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(16, 14, 16, 14)
            c_layout.setSpacing(4)

            val_lbl = QLabel("0", card)
            val_lbl.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {accent}; background: transparent;")
            c_layout.addWidget(val_lbl)

            cap_lbl = QLabel(tr(trans_key), card)
            cap_lbl.setStyleSheet("font-size: 12px; color: #A3A1AE; background: transparent;")
            c_layout.addWidget(cap_lbl)

            self._kpi_labels[key] = (val_lbl, cap_lbl)
            self.kpi_row.addWidget(card, stretch=1)

        self.main_layout.addLayout(self.kpi_row)

        # Daily Activity Chart Card
        self.chart_card = QFrame(self.content)
        self.chart_card.setObjectName("StatCard")
        chart_layout = QVBoxLayout(self.chart_card)
        chart_layout.setContentsMargins(18, 16, 18, 16)
        self.chart_title = QLabel(tr("insights.daily_activity"), self.chart_card)
        self.chart_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #F4F2FA; background: transparent;")
        chart_layout.addWidget(self.chart_title)

        self.bar_chart = DailyActivityBarChart(self.chart_card)
        chart_layout.addWidget(self.bar_chart)
        self.main_layout.addWidget(self.chart_card)

        # Bottom Split: Most Frequently Used Clips & Collections Breakdown
        bottom_split = QHBoxLayout()
        bottom_split.setSpacing(14)

        self.top_clips_card = QFrame(self.content)
        self.top_clips_card.setObjectName("StatCard")
        self.top_clips_layout = QVBoxLayout(self.top_clips_card)
        self.top_clips_layout.setContentsMargins(16, 14, 16, 14)
        self.top_clips_layout.setSpacing(8)
        bottom_split.addWidget(self.top_clips_card, stretch=1)

        self.top_cols_card = QFrame(self.content)
        self.top_cols_card.setObjectName("StatCard")
        self.top_cols_layout = QVBoxLayout(self.top_cols_card)
        self.top_cols_layout.setContentsMargins(16, 14, 16, 14)
        self.top_cols_layout.setSpacing(8)
        bottom_split.addWidget(self.top_cols_card, stretch=1)

        self.main_layout.addLayout(bottom_split)
        self.main_layout.addStretch(1)

        LocalizationManager.instance().subscribe(self._on_language_changed)

    def refresh_insights(self) -> None:
        stats = self.storage.get_statistics()
        for key, (val_lbl, _) in self._kpi_labels.items():
            val_lbl.setText(str(stats.get(key, 0)))

        self.bar_chart.set_data(stats.get("daily_activity", []))

        # Populate Most Used Clips
        self._clear_layout(self.top_clips_layout)
        tc_header = QLabel(tr("insights.top_copied"), self.top_clips_card)
        tc_header.setStyleSheet("font-size: 14px; font-weight: 600; color: #F4F2FA; background: transparent;")
        self.top_clips_layout.addWidget(tc_header)

        for item in stats.get("most_frequent_clips", []):
            row = QHBoxLayout()
            prev = QLabel(str(item.get("preview", ""))[:65], self.top_clips_card)
            prev.setStyleSheet("font-size: 12px; color: #F4F2FA; background: transparent;")
            row.addWidget(prev, stretch=1)

            cnt_lbl = QLabel(tr_plural("uses.count", int(item.get("usage_count", 1))), self.top_clips_card)
            cnt_lbl.setStyleSheet("font-size: 11px; color: #A78BFA; background: transparent;")
            row.addWidget(cnt_lbl)
            self.top_clips_layout.addLayout(row)
        self.top_clips_layout.addStretch(1)

        # Populate Collections Breakdown
        self._clear_layout(self.top_cols_layout)
        col_header = QLabel(tr("insights.top_collections"), self.top_cols_card)
        col_header.setStyleSheet("font-size: 14px; font-weight: 600; color: #F4F2FA; background: transparent;")
        self.top_cols_layout.addWidget(col_header)

        for col in stats.get("collections_breakdown", []):
            row = QHBoxLayout()
            name_lbl = QLabel(f"●  {col.get('name', '')}", self.top_cols_card)
            name_lbl.setStyleSheet(
                f"font-size: 12px; color: {col.get('color', '#A78BFA')}; font-weight: 600; background: transparent;"
            )
            row.addWidget(name_lbl, stretch=1)

            c_cnt = QLabel(tr_plural("items.count", int(col.get("clip_count", 0))), self.top_cols_card)
            c_cnt.setStyleSheet("font-size: 11px; color: #A3A1AE; background: transparent;")
            row.addWidget(c_cnt)
            self.top_cols_layout.addLayout(row)
        self.top_cols_layout.addStretch(1)

    @staticmethod
    def _clear_layout(layout: QVBoxLayout) -> None:
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                InsightsView._clear_layout(child.layout())  # type: ignore[arg-type]

    def _on_language_changed(self, _lang: str) -> None:
        self.title_lbl.setText(tr("navigation.insights"))
        self.sub_lbl.setText(tr("insights.subtitle"))
        self.chart_title.setText(tr("insights.daily_activity"))
        key_map = {
            "total_clips": "insights.total_clips",
            "text_entries": "insights.text_clips",
            "image_entries": "insights.image_clips",
            "color_entries": "insights.color_clips",
        }
        for k, t_key in key_map.items():
            self._kpi_labels[k][1].setText(tr(t_key))
        self.refresh_insights()
