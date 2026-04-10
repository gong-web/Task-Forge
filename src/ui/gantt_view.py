from PyQt6.QtCore import QDate, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPen
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from ui.scroll_area import SmartScrollArea
from ui.theme import SURFACE_BG, SURFACE_BG_LIGHT, SURFACE_BG_SOFT, SURFACE_BORDER, SURFACE_BORDER_STRONG, SURFACE_TEXT_MUTED, SURFACE_TEXT_PRIMARY, SURFACE_TEXT_SECONDARY, chip_style, rgba, text_style


def _color_with_alpha(color: str | QColor, alpha: int) -> QColor:
    source = QColor(color) if isinstance(color, str) else QColor(color)
    source.setAlpha(max(0, min(255, alpha)))
    return source


def _priority_color(priority: str, completed: bool) -> QColor:
    if completed:
        return QColor("#34d399")
    if priority == "高":
        return QColor("#fb7185")
    if priority == "中":
        return QColor("#f59e0b")
    return QColor("#60a5fa")


def _progress_state(progress: int, completed: bool) -> str:
    if completed:
        return "已完成"
    if progress <= 0:
        return "未开始"
    if progress >= 100:
        return "待验收"
    return "进行中"

class GanttTimeline(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.start_date = QDate.currentDate().addDays(-7)
        self.days_to_show = 45
        self.row_height = 68
        # Keep a dedicated title band and a dedicated date-axis band to avoid overlap.
        self.header_height = 132
        self.left_label_width = 356
        self.col_width = 38
        self.items = []
        self.setMinimumSize(860, 560)

    def refresh_timeline(self) -> None:
        snapshot = self.db.gantt_entries()
        self.start_date = QDate(snapshot["start_date"].year, snapshot["start_date"].month, snapshot["start_date"].day)
        self.days_to_show = snapshot["days"]
        self.items = snapshot["items"]
        total_width = self.left_label_width + self.days_to_show * self.col_width + 168
        total_height = self.header_height + max(10, len(self.items)) * self.row_height + 40
        self.setMinimumSize(total_width, total_height)
        self.resize(total_width, total_height)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        painter.fillRect(self.rect(), QColor(SURFACE_BG))

        header_top = 12
        metric_row_y = 24
        title_row_y = 46
        day_row_y = 82
        weekday_row_y = 100
        today_badge_y = 116

        left_header_rect = QRectF(10, header_top, self.left_label_width - 18, self.header_height - 20)
        timeline_header_rect = QRectF(self.left_label_width + 8, header_top, width - self.left_label_width - 18, self.header_height - 20)
        painter.setPen(QPen(_color_with_alpha(SURFACE_BORDER_STRONG, 80), 1.1))
        painter.setBrush(_color_with_alpha(SURFACE_BG_SOFT, 244))
        painter.drawRoundedRect(left_header_rect, 18, 18)
        painter.drawRoundedRect(timeline_header_rect, 18, 18)

        title_font = QFont(painter.font())
        title_font.setPointSize(11)
        title_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(title_font)
        painter.setPen(QColor(SURFACE_TEXT_MUTED))
        painter.drawText(QRectF(26, metric_row_y, self.left_label_width - 48, 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "任务 / 状态")
        painter.drawText(QRectF(self.left_label_width + 24, metric_row_y, width - self.left_label_width - 48, 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "排期 / 进度")

        header_note_font = QFont(painter.font())
        header_note_font.setPointSize(13)
        header_note_font.setWeight(QFont.Weight.Bold)
        painter.setFont(header_note_font)
        painter.setPen(QColor(SURFACE_TEXT_PRIMARY))
        painter.drawText(QRectF(26, title_row_y, self.left_label_width - 48, 24), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "任务时间轴")
        painter.drawText(QRectF(self.left_label_width + 24, title_row_y, width - self.left_label_width - 48, 24), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "拖动底部滚动条查看完整跨度")

        weekday_labels = ["一", "二", "三", "四", "五", "六", "日"]
        today = QDate.currentDate()
        painter.setPen(QPen(_color_with_alpha(SURFACE_BORDER, 128), 1))
        painter.drawLine(0, self.header_height, width, self.header_height)

        for day_index in range(self.days_to_show + 1):
            x = self.left_label_width + day_index * self.col_width
            painter.setPen(QPen(_color_with_alpha(SURFACE_BORDER, 96), 1))
            painter.drawLine(x, self.header_height - 4, x, height)
            if day_index >= self.days_to_show:
                continue
            day = self.start_date.addDays(day_index)
            if day.dayOfWeek() >= 6:
                painter.fillRect(x, self.header_height, self.col_width, height - self.header_height, _color_with_alpha("#ffffff", 8))
            if day == today:
                # Fill only the row area (below header) to avoid overwriting header text
                painter.fillRect(x, self.header_height, self.col_width, height - self.header_height - 4, _color_with_alpha("#60a5fa", 14))
                painter.setPen(QPen(_color_with_alpha("#60a5fa", 160), 1.2))
                center_x = int(x + self.col_width / 2)
                painter.drawLine(center_x, self.header_height, center_x, height - 8)

            date_font = QFont(painter.font())
            date_font.setPointSize(10)
            date_font.setWeight(QFont.Weight.Bold if day.day() == 1 or day == today else QFont.Weight.DemiBold)
            painter.setFont(date_font)
            painter.setPen(QColor(SURFACE_TEXT_SECONDARY if day.dayOfWeek() < 6 else SURFACE_TEXT_PRIMARY))
            painter.drawText(QRectF(x, day_row_y, self.col_width, 16), Qt.AlignmentFlag.AlignCenter, f"{day.day():02d}")
            small_font = QFont(painter.font())
            small_font.setPointSize(8)
            small_font.setWeight(QFont.Weight.Medium)
            painter.setFont(small_font)
            painter.setPen(QColor(SURFACE_TEXT_MUTED))
            top_text = f"{day.month():02d}月" if day.day() == 1 or day_index == 0 else weekday_labels[max(0, day.dayOfWeek() - 1)]
            painter.drawText(QRectF(x, weekday_row_y, self.col_width, 14), Qt.AlignmentFlag.AlignCenter, top_text)

        if today >= self.start_date and today <= self.start_date.addDays(max(0, self.days_to_show - 1)):
            today_offset = self.start_date.daysTo(today)
            badge_x = self.left_label_width + today_offset * self.col_width + 3
            today_badge_rect = QRectF(badge_x, today_badge_y, self.col_width - 6, 14)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(_color_with_alpha("#60a5fa", 210))
            painter.drawRoundedRect(today_badge_rect, 7, 7)
            painter.setPen(QColor("#f8fbff"))
            tiny_font = QFont(painter.font())
            tiny_font.setPointSize(7)
            tiny_font.setWeight(QFont.Weight.Bold)
            painter.setFont(tiny_font)
            painter.drawText(today_badge_rect, Qt.AlignmentFlag.AlignCenter, "今天")

        if not self.items:
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "当前没有带日期的任务，无法生成甘特时间轴")
            return

        for row, item in enumerate(self.items):
            try:
                top = self.header_height + row * self.row_height
                depth = item.get("depth", 0)
                indent = depth * 18
                left_card = QRectF(10 + indent, top + 7, self.left_label_width - 18 - indent, self.row_height - 12)
                painter.setPen(QPen(_color_with_alpha(SURFACE_BORDER, 94), 1))
                painter.setBrush(_color_with_alpha(SURFACE_BG_LIGHT, 78 if row % 2 == 0 else 54))
                painter.drawRoundedRect(left_card, 16, 16)

                title_font = QFont(painter.font())
                title_font.setPointSize(10)
                title_font.setWeight(QFont.Weight.Bold)
                painter.setFont(title_font)
                title_metrics = QFontMetrics(title_font)
                title_text = title_metrics.elidedText(item.get("title") or "未命名", Qt.TextElideMode.ElideRight, max(10, int(left_card.width()) - 130))
                painter.setPen(QColor(SURFACE_TEXT_PRIMARY))
                painter.drawText(QRectF(left_card.left() + 14, top + 18, max(10.0, left_card.width() - 140), 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title_text)

                state_text = _progress_state(item["progress"], item["completed"])
                state_rect = QRectF(left_card.right() - 82, top + 16, 68, 18)
                state_color = _priority_color(item["priority"], item["completed"])
                painter.setPen(QPen(_color_with_alpha(state_color, 120), 1))
                painter.setBrush(_color_with_alpha(state_color, 28))
                painter.drawRoundedRect(state_rect, 9, 9)
                state_font = QFont(painter.font())
                state_font.setPointSize(8)
                state_font.setWeight(QFont.Weight.Bold)
                painter.setFont(state_font)
                painter.setPen(QColor(SURFACE_TEXT_PRIMARY))
                painter.drawText(state_rect, Qt.AlignmentFlag.AlignCenter, state_text)

                meta_font = QFont(painter.font())
                meta_font.setPointSize(8)
                meta_font.setWeight(QFont.Weight.Medium)
                painter.setFont(meta_font)
                painter.setPen(QColor(SURFACE_TEXT_MUTED))
                meta_text = f"{item['category']}｜{item['priority']}优先级｜{item['start_date']:%m-%d} → {item['end_date']:%m-%d}"
                meta_metrics = QFontMetrics(meta_font)
                meta_text = meta_metrics.elidedText(meta_text, Qt.TextElideMode.ElideRight, max(10, int(left_card.width()) - 28))
                painter.drawText(QRectF(left_card.left() + 14, top + 39, max(10.0, left_card.width() - 28), 14), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, meta_text)

                start = QDate(item["start_date"].year, item["start_date"].month, item["start_date"].day)
                end = QDate(item["end_date"].year, item["end_date"].month, item["end_date"].day)
                start_offset = max(0, self.start_date.daysTo(start))
                end_offset = max(start_offset, self.start_date.daysTo(end))
                bar_x = self.left_label_width + start_offset * self.col_width + 5
                raw_bar_width = max(self.col_width - 10, (end_offset - start_offset + 1) * self.col_width - 10)
                # Give short-duration tasks a minimum visual width so progress changes remain visible in demos.
                bar_width = max(raw_bar_width, 84)
                bar_rect = QRectF(bar_x, top + 24, bar_width, 18)
                bar_color = _priority_color(item["priority"], item["completed"])

                painter.setPen(QPen(_color_with_alpha(bar_color, 156), 1.2))
                painter.setBrush(_color_with_alpha(bar_color, 34))
                painter.drawRoundedRect(bar_rect, 9, 9)
                progress_value = max(0, min(100, item["progress"]))
                progress_w = bar_width * progress_value / 100
                if progress_value > 0:
                    progress_w = max(progress_w, 6)
                progress_w = min(progress_w, bar_width)
                if progress_w >= 1.0:
                    progress_rect = QRectF(bar_x, top + 24, progress_w, 18)
                    gradient = QLinearGradient(progress_rect.topLeft(), progress_rect.topRight())
                    gradient.setColorAt(0, _color_with_alpha(bar_color, 238))
                    gradient.setColorAt(1, _color_with_alpha(bar_color.lighter(120), 226))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(gradient)
                    painter.drawRoundedRect(progress_rect, 7, 7)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(_color_with_alpha(bar_color, 178))
                painter.drawEllipse(QRectF(bar_x + 5, top + 30, 6, 6))
                painter.drawEllipse(QRectF(bar_rect.right() - 11, top + 30, 6, 6))
                if 0 < item["progress"] < 100:
                    marker_x = bar_x + progress_w
                    painter.setBrush(QColor(255, 255, 255, 220))
                    painter.drawEllipse(QRectF(marker_x - 4, top + 28, 8, 8))
                elif item["progress"] <= 0:
                    painter.setBrush(QColor(255, 255, 255, 210))
                    painter.drawEllipse(QRectF(bar_x + 8, top + 29, 8, 8))

                inline_font = QFont(painter.font())
                inline_font.setPointSize(8)
                inline_font.setWeight(QFont.Weight.Bold)
                inline_text_offset = 22
                if bar_width >= 118:
                    painter.setFont(inline_font)
                    painter.setPen(QColor("#f8fbff"))
                    inline_text = f"{item['start_date']:%m-%d} → {item['end_date']:%m-%d}"
                    available_w = max(0.0, bar_width - inline_text_offset - 18)
                    inline_text = QFontMetrics(inline_font).elidedText(inline_text, Qt.TextElideMode.ElideRight, int(available_w))
                    painter.drawText(QRectF(bar_x + inline_text_offset, top + 24, available_w, 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, inline_text)

                percent_rect = QRectF(bar_rect.right() + 12, top + 21, 64, 24)
                painter.setPen(QPen(_color_with_alpha(bar_color, 84), 1))
                painter.setBrush(_color_with_alpha(bar_color, 24))
                painter.drawRoundedRect(percent_rect, 12, 12)
                painter.setPen(QColor(SURFACE_TEXT_PRIMARY))
                painter.drawText(percent_rect, Qt.AlignmentFlag.AlignCenter, f"{item['progress']}%")
            except Exception:
                pass

class GanttView(QWidget):
    def __init__(self, db, main_window=None):
        super().__init__()
        self.db = db
        self.main_window = main_window
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("项目甘特时间轴")
        title.setStyleSheet(text_style(SURFACE_TEXT_PRIMARY, 22, 800))
        subtitle = QLabel("根据任务创建时间、截止日期和手动标记的任务进度生成时间跨度；父任务会自动汇总子任务进度，进度百分比显示在条形右侧。")
        subtitle.setStyleSheet(text_style(SURFACE_TEXT_SECONDARY, 13))
        layout.addWidget(title)
        layout.addWidget(subtitle)

        summary_row = QHBoxLayout()
        summary_row.setContentsMargins(0, 0, 0, 0)
        summary_row.setSpacing(10)
        self.task_count_label = QLabel("0 个任务")
        self.range_label = QLabel("暂无时间范围")
        self.today_label = QLabel("今天")
        self.scroll_hint_label = QLabel("支持横向滚动")
        for label in (self.task_count_label, self.range_label, self.today_label, self.scroll_hint_label):
            label.setStyleSheet(chip_style(text_color=SURFACE_TEXT_PRIMARY, background=rgba("#ffffff", 10), border=rgba("#ffffff", 20), radius=12, padding="5px 12px"))
            summary_row.addWidget(label)
        summary_row.addStretch(1)
        layout.addLayout(summary_row)

        legend_row = QHBoxLayout()
        legend_row.setContentsMargins(0, 0, 0, 0)
        legend_row.setSpacing(8)
        self.legend_labels = [
            self._make_legend_chip("高优先级", "#fb7185"),
            self._make_legend_chip("中优先级", "#f59e0b"),
            self._make_legend_chip("低优先级", "#60a5fa"),
            self._make_legend_chip("已完成", "#34d399"),
        ]
        for label in self.legend_labels:
            legend_row.addWidget(label)
        legend_row.addStretch(1)
        layout.addLayout(legend_row)

        self.scroll = SmartScrollArea()
        self.scroll.setWidgetResizable(False)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.scroll.setStyleSheet(
            f"QScrollArea {{ background: {SURFACE_BG}; border: 1px solid {SURFACE_BORDER}; border-radius: 18px; }}"
            f"QScrollArea > QWidget > QWidget {{ background: transparent; }}"
            f"QScrollBar:horizontal {{ background: {SURFACE_BG_SOFT}; height: 12px; margin: 0 16px 10px 16px; border-radius: 6px; }}"
            f"QScrollBar::handle:horizontal {{ background: {rgba('#60a5fa', 132)}; min-width: 42px; border-radius: 6px; }}"
            f"QScrollBar::handle:horizontal:hover {{ background: {rgba('#60a5fa', 184)}; }}"
            f"QScrollBar:vertical {{ background: {SURFACE_BG_SOFT}; width: 12px; margin: 16px 8px 16px 0; border-radius: 6px; }}"
            f"QScrollBar::handle:vertical {{ background: {rgba('#ffffff', 82)}; min-height: 42px; border-radius: 6px; }}"
            f"QScrollBar::handle:vertical:hover {{ background: {rgba('#ffffff', 124)}; }}"
            "QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page { background: transparent; border: none; }"
        )
        self.timeline = GanttTimeline(self.db)
        self.scroll.setWidget(self.timeline)
        layout.addWidget(self.scroll, 1)
        self._auto_focus_today_pending = True

    def _make_legend_chip(self, text: str, accent: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(chip_style(text_color=SURFACE_TEXT_PRIMARY, background=rgba(accent, 24), border=rgba(accent, 72), radius=12, padding="5px 12px"))
        return label

    def refresh_data(self):
        self.timeline.refresh_timeline()
        items = self.timeline.items
        self.task_count_label.setText(f"{len(items)} 个任务")
        self.today_label.setText(f"今天 {QDate.currentDate().month()}/{QDate.currentDate().day()}")
        if items:
            first = min(item["start_date"] for item in items)
            last = max(item["end_date"] for item in items)
            if first.year != last.year or (last - first).days > 120:
                self.range_label.setText(f"{first:%Y-%m-%d} 至 {last:%Y-%m-%d}")
            else:
                self.range_label.setText(f"{first:%m-%d} 至 {last:%m-%d}")
            self.scroll_hint_label.setText("拖动底部滚动条查看完整排期")
        else:
            self.range_label.setText("暂无时间范围")
            self.scroll_hint_label.setText("设置截止时间后会生成时间轴")

        if self._auto_focus_today_pending:
            self._auto_focus_today_pending = False
            QTimer.singleShot(0, self._focus_today)

    def _focus_today(self) -> None:
        today = QDate.currentDate()
        day_offset = self.timeline.start_date.daysTo(today)
        if day_offset < 0 or day_offset >= self.timeline.days_to_show:
            return
        target_x = self.timeline.left_label_width + int(day_offset * self.timeline.col_width) - 180
        bar = self.scroll.horizontalScrollBar()
        target_x = max(bar.minimum(), min(bar.maximum(), target_x))
        bar.setValue(target_x)
