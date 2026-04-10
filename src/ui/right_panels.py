from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from Task import Task
from ui.icon_manager import IconManager
from ui.scroll_area import SmartScrollArea
from ui.theme import (
    SURFACE_BG_ACCENT,
    SURFACE_BG,
    SURFACE_BG_LIGHT,
    SURFACE_BG_RAISED,
    SURFACE_GRADIENT_BASE_END,
    SURFACE_GRADIENT_BASE_START,
    SURFACE_GRADIENT_RAISED_END,
    SURFACE_GRADIENT_RAISED_START,
    SURFACE_BORDER,
    SURFACE_BORDER_SOFT,
    SURFACE_RING_INNER,
    SURFACE_RING_TRACK,
    SURFACE_TEXT_DISABLED,
    SURFACE_TEXT_MUTED,
    SURFACE_TEXT_PRIMARY,
    SURFACE_TEXT_SECONDARY,
    chip_style,
    gradient_surface_style,
    rgba,
    surface_style,
    text_style,
    title_text_style,
)


def clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        child_layout = item.layout()
        if widget is not None:
            widget.deleteLater()
        elif child_layout is not None:
            clear_layout(child_layout)


class SurfaceCard(QFrame):
    def __init__(self, accent: str = "#60a5fa", padded: bool = True, radius: int = 24, parent=None):
        super().__init__(parent)
        self.accent = accent
        self.radius = radius
        self.setObjectName("surfaceCard")
        self.setStyleSheet(
            gradient_surface_style(
                SURFACE_GRADIENT_BASE_START,
                SURFACE_GRADIENT_BASE_END,
                radius,
                border=SURFACE_BORDER,
                selector="QFrame#surfaceCard",
            )
        )
        self.layout_ref = QVBoxLayout(self)
        margin = 20 if padded else 0
        self.layout_ref.setContentsMargins(margin, margin, margin, margin)
        self.layout_ref.setSpacing(14)

    def layout(self):
        return self.layout_ref


class ArtworkStamp(QLabel):
    def __init__(self, art_name: str, size: int = 52, glow: str = "#60a5fa", parent=None):
        super().__init__(parent)
        self.setFixedSize(size + 24, size + 24)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            chip_style(
                background=rgba(glow, 24),
                border=rgba(glow, 72),
                radius=18,
                padding="0px",
            )
        )
        self.set_art(art_name, size)

    def set_art(self, art_name: str, size: int = 52) -> None:
        pixmap = IconManager().get_pixmap(art_name, size=size)
        self.setPixmap(pixmap)


class MetricTile(QFrame):
    def __init__(self, title: str, accent: str = "#60a5fa", art_name: str = "downloaded/svg/layout-dashboard.svg", parent=None):
        super().__init__(parent)
        self.accent = accent
        self.setObjectName("metricTile")
        self.setStyleSheet(
            gradient_surface_style(
                SURFACE_GRADIENT_RAISED_START,
                SURFACE_GRADIENT_RAISED_END,
                22,
                border=rgba(accent, 72),
                selector="QFrame#metricTile",
            )
        )
        self.setMinimumHeight(106)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 14, 14)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(10)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(text_style(SURFACE_TEXT_SECONDARY, 12, 700))
        self.value_label = QLabel("0")
        self.value_label.setStyleSheet(f"color: {accent}; font-size: 26px; font-weight: 900;")
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.value_label)
        top.addLayout(title_box, 1)
        self.art = ArtworkStamp(art_name, size=20, glow=accent)
        self.art.setFixedSize(38, 38)
        top.addWidget(self.art)

        self.meta_label = QLabel("")
        self.meta_label.setWordWrap(True)
        self.meta_label.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 12, 600) + " line-height: 1.55;")

        layout.addLayout(top)
        layout.addWidget(self.meta_label)

    def set_values(self, value: str, meta: str, *, art_name: str | None = None) -> None:
        self.value_label.setText(value)
        self.meta_label.setText(meta)
        if art_name:
            self.art.set_art(art_name, 28)


class ScoreRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.title = "健康度"
        self.subtitle = ""
        self.accent = QColor("#f472b6")
        self.setMinimumSize(220, 220)

    def set_values(self, value: int, title: str, subtitle: str, accent: str = "#f472b6") -> None:
        self.value = max(0, min(100, int(value)))
        self.title = title
        self.subtitle = subtitle
        self.accent = QColor(accent)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(26, 26, -26, -26)
        diameter = min(rect.width(), rect.height())
        square = QRectF(
            rect.center().x() - diameter / 2,
            rect.center().y() - diameter / 2,
            diameter,
            diameter,
        )
        painter.setPen(QPen(QColor(SURFACE_RING_TRACK), 18))
        painter.drawArc(square, 0, 360 * 16)
        painter.setPen(QPen(self.accent, 18, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(square, 90 * 16, int(-self.value / 100 * 360 * 16))
        inner = square.adjusted(26, 26, -26, -26)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(SURFACE_RING_INNER))
        painter.drawEllipse(inner)

        painter.setPen(QColor(SURFACE_TEXT_PRIMARY))
        value_font = painter.font()
        value_font.setPointSize(24)
        value_font.setBold(True)
        painter.setFont(value_font)
        painter.drawText(inner.adjusted(0, -20, 0, 0), Qt.AlignmentFlag.AlignCenter, f"{self.value}")

        title_font = painter.font()
        title_font.setPointSize(10)
        title_font.setBold(False)
        painter.setFont(title_font)
        painter.setPen(QColor(SURFACE_TEXT_SECONDARY))
        painter.drawText(inner.adjusted(0, 16, 0, 0), Qt.AlignmentFlag.AlignCenter, self.title)
        painter.setPen(QColor(SURFACE_TEXT_MUTED))
        painter.drawText(inner.adjusted(-16, 50, 16, 0), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.subtitle)


class MultiSeriesChart(QWidget):
    def __init__(self, series_keys: list[tuple[str, str, str, int]], parent=None):
        super().__init__(parent)
        self.series_keys = series_keys
        self.series: list[dict[str, Any]] = []
        self.setMinimumHeight(286)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_series(self, series: Iterable[dict[str, Any]]) -> None:
        self.series = list(series)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Wider left margin for Y-axis labels
        rect = self.rect().adjusted(44, 28, -18, -44)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        if not self.series:
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "暂无数据")
            return

        # Compute max first so Y labels are accurate
        max_value = 1
        for item in self.series:
            for _, key, _, _ in self.series_keys:
                max_value = max(max_value, int(item.get(key, 0)))
        max_value = max(max_value, 4)

        # Legend at top-right as compact dots
        legend_x = rect.right()
        small_font = painter.font()
        small_font.setPointSize(8)
        painter.setFont(small_font)
        for label, _, color_hex, _ in reversed(self.series_keys):
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(label)
            legend_x -= tw + 22
            painter.setBrush(QColor(color_hex))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(legend_x, 10), 4, 4)
            painter.setPen(QColor(SURFACE_TEXT_SECONDARY))
            painter.drawText(int(legend_x + 10), 14, label)

        # Y-axis ticks, labels and horizontal grid lines
        y_ticks = 4
        for tick in range(y_ticks + 1):
            y = rect.top() + rect.height() * (y_ticks - tick) / y_ticks
            val = round(max_value * tick / y_ticks)
            line_alpha = 18 if tick > 0 else 0
            painter.setPen(QPen(QColor(255, 255, 255, line_alpha), 1, Qt.PenStyle.DashLine))
            painter.drawLine(rect.left(), int(y), rect.right(), int(y))
            painter.setPen(QColor(SURFACE_TEXT_MUTED))
            fm = painter.fontMetrics()
            label_rect = QRectF(0, y - 8, rect.left() - 5, 16)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(val))

        # Left axis line and baseline
        painter.setPen(QPen(QColor(255, 255, 255, 28), 1))
        painter.drawLine(rect.left(), rect.top(), rect.left(), rect.bottom() + 1)
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

        step_x = rect.width() / max(1, len(self.series) - 1)

        for label, key, color_hex, fill_alpha in self.series_keys:
            color = QColor(color_hex)
            path = QPainterPath()
            points: list[QPointF] = []
            for index, item in enumerate(self.series):
                value = int(item.get(key, 0))
                x = rect.left() + index * step_x
                y = rect.bottom() - rect.height() * 0.90 * value / max_value
                y = max(float(rect.top()) + 4.0, y)
                point = QPointF(x, y)
                points.append(point)
                if index == 0:
                    path.moveTo(point)
                else:
                    path.lineTo(point)
            if points:
                capped_alpha = min(fill_alpha, 14)
                fill_path = QPainterPath(path)
                fill_path.lineTo(points[-1].x(), rect.bottom())
                fill_path.lineTo(points[0].x(), rect.bottom())
                fill_path.closeSubpath()
                painter.fillPath(fill_path, QColor(color.red(), color.green(), color.blue(), capped_alpha))
                painter.setPen(QPen(color, 2.3))
                painter.drawPath(path)
                painter.setBrush(color)
                painter.setPen(QPen(QColor(SURFACE_BG), 1.6))
                for point in points:
                    painter.drawEllipse(point, 4.0, 4.0)

        # X-axis labels
        n = len(self.series)
        skip = max(1, (n + 6) // 7)
        painter.setPen(QColor(SURFACE_TEXT_SECONDARY))
        for index, item in enumerate(self.series):
            if skip > 1 and index % skip != 0 and index != n - 1:
                continue
            x = rect.left() + index * step_x
            label_text = str(item.get("label", ""))
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(label_text)
            painter.drawText(int(x - tw / 2), rect.bottom() + 18, label_text)


class BulletPanel(SurfaceCard):
    def __init__(self, title: str, accent: str, art_name: str, parent=None):
        super().__init__(accent=accent, parent=parent)
        header = QHBoxLayout()
        header.setSpacing(10)
        self.stamp = ArtworkStamp(art_name, size=20, glow=accent)
        self.stamp.setFixedSize(42, 42)
        header.addWidget(self.stamp)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(text_style(SURFACE_TEXT_PRIMARY, 16, 700))
        self.subtitle_label = QLabel("")
        self.subtitle_label.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 13))
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.subtitle_label)
        header.addLayout(title_box, 1)
        self.layout().addLayout(header)
        self.body_label = QLabel("")
        self.body_label.setWordWrap(True)
        self.body_label.setStyleSheet(text_style(SURFACE_TEXT_SECONDARY, 14) + " line-height: 1.8;")
        self.layout().addWidget(self.body_label)

    def set_items(self, items: list[str], subtitle: str = "") -> None:
        self.subtitle_label.setText(subtitle)
        self.body_label.setText("\n".join(f"• {line}" for line in items) if items else "• 暂无数据")


class DistributionStrip(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items: list[tuple[str, int, str]] = []
        self.setMinimumHeight(80)

    def set_items(self, items: list[tuple[str, int, str]]) -> None:
        self.items = items
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(8, 18, -8, -12)
        total = max(1, sum(value for _, value, _ in self.items))
        x = rect.left()
        usable_width = rect.width()
        for index, (label, value, color_hex) in enumerate(self.items):
            width = usable_width * value / total
            if index == len(self.items) - 1:
                width = rect.right() - x
            block = QRectF(x, rect.top() + 12, max(22, width), 18)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(color_hex))
            painter.drawRoundedRect(block, 9, 9)
            painter.setPen(QColor(SURFACE_TEXT_SECONDARY))
            painter.drawText(QRectF(x, rect.top() - 2, max(80, width), 12), f"{label} {value}")
            x += width + 6


class HeroBanner(SurfaceCard):
    def __init__(self, title: str, subtitle: str, accent: str, art_name: str, parent=None):
        super().__init__(accent=accent, radius=28, parent=parent)
        top = QHBoxLayout()
        top.setSpacing(18)
        self.text_box = QVBoxLayout()
        self.text_box.setSpacing(8)
        self.title_label = QLabel(title)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet(title_text_style(SURFACE_TEXT_PRIMARY, 24, 800))
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet(text_style(SURFACE_TEXT_SECONDARY, 13) + " line-height: 1.75;")
        self.hint_label = QLabel("")
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet(f"color: {accent}; font-size: 12px; font-weight: 700;")
        self.text_box.addWidget(self.title_label)
        self.text_box.addWidget(self.subtitle_label)
        self.text_box.addWidget(self.hint_label)
        top.addLayout(self.text_box, 1)
        self.art = ArtworkStamp(art_name, size=84, glow=accent)
        self.art.setFixedSize(112, 112)
        top.addWidget(self.art)
        self.layout().addLayout(top)

    def set_hint(self, text: str) -> None:
        self.hint_label.setText(text)


class WeekTaskRow(QFrame):
    def __init__(self, task: Task | None, parent=None):
        super().__init__(parent)
        self.setObjectName("weekTaskRow")
        self.setStyleSheet(
            f"""
            QFrame#weekTaskRow {{
                background: {SURFACE_BG_LIGHT};
                border-radius: 18px;
                border: none;
            }}
            """
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        if task is None:
            icon = ArtworkStamp("downloaded/svg/calendar-days.svg", size=18, glow="#64748b")
            icon.setFixedSize(40, 40)
            layout.addWidget(icon)
            title = QLabel("无任务安排")
            title.setStyleSheet(text_style("#64748b", 13))
            layout.addWidget(title)
            return

        accent = {"高": "#fb7185", "中": "#f59e0b", "低": "#60a5fa"}.get(task.priority, "#60a5fa")
        art_name = "downloaded/svg/circle-check-big.svg" if task.completed else "downloaded/svg/list-todo.svg"
        icon = ArtworkStamp(art_name, size=20, glow=accent)
        icon.setFixedSize(44, 44)
        layout.addWidget(icon)

        text_box = QVBoxLayout()
        text_box.setSpacing(3)
        title = QLabel(task.title)
        title.setWordWrap(True)
        title.setStyleSheet(text_style(SURFACE_TEXT_DISABLED if task.completed else SURFACE_TEXT_PRIMARY, 14, 700))
        due_text = task.due_at.strftime("%H:%M") if task.due_at else "未设时间"
        meta = QLabel(f"{task.category}｜{task.priority} 优先级｜{due_text}｜专注 {task.tracked_minutes} 分钟")
        meta.setWordWrap(True)
        meta.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 12))
        text_box.addWidget(title)
        text_box.addWidget(meta)
        layout.addLayout(text_box, 1)

        badge = QLabel("已完成" if task.completed else "待推进")
        badge.setStyleSheet(chip_style(background=rgba(accent, 72), border=rgba(accent, 96), radius=12, padding="6px 12px"))
        layout.addWidget(badge)


class DayAgendaCard(SurfaceCard):
    def __init__(self, parent=None):
        super().__init__(accent="#60a5fa", parent=parent)
        self.header_layout = QHBoxLayout()
        self.header_layout.setSpacing(12)
        self.day_label = QLabel("")
        self.day_label.setStyleSheet(text_style(SURFACE_TEXT_PRIMARY, 18, 800))
        self.meta_label = QLabel("")
        self.meta_label.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 12))
        header_box = QVBoxLayout()
        header_box.setSpacing(2)
        header_box.addWidget(self.day_label)
        header_box.addWidget(self.meta_label)
        self.header_layout.addLayout(header_box, 1)
        self.completion_badge = QLabel("")
        self.completion_badge.setStyleSheet(
            chip_style(background=rgba("#60a5fa", 41), border=rgba("#60a5fa", 82), radius=12, padding="6px 12px")
        )
        self.header_layout.addWidget(self.completion_badge)
        self.layout().addLayout(self.header_layout)
        self.task_layout = QVBoxLayout()
        self.task_layout.setSpacing(10)
        self.layout().addLayout(self.task_layout)

    def set_payload(self, payload: dict[str, Any]) -> None:
        task_total = len(payload.get("tasks", []))
        focus_minutes = int(payload.get("focus_minutes", 0))
        completed = int(payload.get("completed_count", 0))
        self.day_label.setText(payload.get("label", ""))
        self.meta_label.setText(
            f"{payload.get('date_text', '')}｜安排 {task_total} 项｜完成 {completed} 项｜专注 {focus_minutes} 分钟"
        )
        self.completion_badge.setText(f"完成率 {payload.get('completion_rate', 0)}%")
        clear_layout(self.task_layout)
        tasks = payload.get("tasks", [])
        if not tasks:
            self.task_layout.addWidget(WeekTaskRow(None))
            return
        for task in tasks:
            self.task_layout.addWidget(WeekTaskRow(task))


class WeeklyPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.scroll = SmartScrollArea()
        self.scroll.setStyleSheet("background: transparent; border: none;")
        root.addWidget(self.scroll)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(12, 12, 12, 18)
        self.content_layout.setSpacing(14)

        _wday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        today = date.today()
        header_card = SurfaceCard(accent="#60a5fa", radius=20)
        hdr = QHBoxLayout()
        hdr.setSpacing(12)
        hero_title = QLabel("周视图")
        hero_title.setStyleSheet(title_text_style(SURFACE_TEXT_PRIMARY, 20, 800))
        date_lbl = QLabel(f"{today.month}/{today.day} {_wday[today.weekday()]}")
        date_lbl.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 14))
        self.hero_hint = QLabel("")
        self.hero_hint.setWordWrap(True)
        self.hero_hint.setStyleSheet("color: #60a5fa; font-size: 13px; font-weight: 700;")
        hdr.addWidget(hero_title)
        hdr.addWidget(date_lbl)
        hdr.addStretch()
        hdr.addWidget(self.hero_hint)
        header_card.layout().addLayout(hdr)
        self.content_layout.addWidget(header_card)

        metric_grid = QGridLayout()
        metric_grid.setSpacing(12)
        self.summary_cards = [
            MetricTile("安排总量", "#60a5fa", "downloaded/svg/calendar-range.svg"),
            MetricTile("本周完成", "#34d399", "downloaded/svg/circle-check-big.svg"),
            MetricTile("高优事项", "#fb7185", "downloaded/svg/flame.svg"),
            MetricTile("专注沉淀", "#c084fc", "downloaded/png/target.png"),
        ]
        for index, card in enumerate(self.summary_cards):
            metric_grid.addWidget(card, index // 2, index % 2)
        self.content_layout.addLayout(metric_grid)

        self.trend_card = SurfaceCard(accent="#60a5fa")
        trend_header = QLabel("周节奏走势")
        trend_header.setStyleSheet(text_style(SURFACE_TEXT_PRIMARY, 16, 700))
        self.trend_card.layout().addWidget(trend_header)
        self.week_chart = MultiSeriesChart(
            [
                ("安排", "scheduled", "#60a5fa", 28),
                ("完成", "completed", "#34d399", 34),
                ("专注", "focus", "#f472b6", 24),
            ]
        )
        self.trend_card.layout().addWidget(self.week_chart)
        self.content_layout.addWidget(self.trend_card)

        insight_row = QHBoxLayout()
        insight_row.setSpacing(12)
        self.week_insights = BulletPanel("本周洞察", "#f472b6", "downloaded/png/idea.png")
        self.week_mix = BulletPanel("项目分布", "#60a5fa", "downloaded/svg/notebook-tabs.svg")
        insight_row.addWidget(self.week_insights, 1)
        insight_row.addWidget(self.week_mix, 1)
        self.content_layout.addLayout(insight_row)

        self.day_cards_layout = QVBoxLayout()
        self.day_cards_layout.setSpacing(12)
        self.content_layout.addLayout(self.day_cards_layout)
        self.content_layout.addStretch(1)
        self.scroll.setWidget(content)

    def apply_snapshot(self, snapshot: dict[str, Any]) -> None:
        summary = snapshot.get("summary", {})
        self.hero_hint.setText(snapshot.get("hero_hint", ""))
        self.summary_cards[0].set_values(str(summary.get("scheduled", 0)), f"本周跨度 {summary.get('range_text', '')}")
        self.summary_cards[1].set_values(str(summary.get("completed", 0)), f"完成率 {summary.get('completion_rate', 0)}%")
        self.summary_cards[2].set_values(str(summary.get("high_priority", 0)), f"需要特别关注 {summary.get('overdue', 0)} 项")
        self.summary_cards[3].set_values(f"{summary.get('focus_minutes', 0)} 分钟", summary.get("best_day_text", ""))
        self.week_chart.set_series(snapshot.get("trend", []))
        self.week_insights.set_items(snapshot.get("insights", []), snapshot.get("insight_subtitle", "真实周节奏"))
        mix_lines = [f"{name}：{count} 项" for name, count in snapshot.get("categories", [])[:6]]
        self.week_mix.set_items(mix_lines, snapshot.get("category_subtitle", "重点项目分布"))

        clear_layout(self.day_cards_layout)
        for day_payload in snapshot.get("days", []):
            card = DayAgendaCard()
            card.set_payload(day_payload)
            self.day_cards_layout.addWidget(card)


class StatsOverviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.scroll = SmartScrollArea()
        self.scroll.setStyleSheet("background: transparent; border: none;")
        root.addWidget(self.scroll)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 18)
        layout.setSpacing(14)

        header_card = SurfaceCard(accent="#f472b6", radius=20)
        shdr = QHBoxLayout()
        shdr.setSpacing(12)
        stats_title = QLabel("统计概览")
        stats_title.setStyleSheet(title_text_style(SURFACE_TEXT_PRIMARY, 20, 800))
        self.hero_hint = QLabel("")
        self.hero_hint.setWordWrap(True)
        self.hero_hint.setStyleSheet("color: #f472b6; font-size: 13px; font-weight: 700;")
        shdr.addWidget(stats_title)
        shdr.addStretch()
        shdr.addWidget(self.hero_hint)
        header_card.layout().addLayout(shdr)
        layout.addWidget(header_card)

        metric_grid = QGridLayout()
        metric_grid.setSpacing(12)
        self.metric_cards = [
            MetricTile("完成任务", "#34d399", "downloaded/svg/circle-check-big.svg"),
            MetricTile("到期任务", "#60a5fa", "downloaded/svg/calendar-days.svg"),
            MetricTile("累计专注", "#c084fc", "downloaded/svg/timer-reset.svg"),
            MetricTile("完成率", "#f472b6", "downloaded/svg/chart-spline.svg"),
        ]
        for index, card in enumerate(self.metric_cards):
            metric_grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(metric_grid)

        self.trend_card = SurfaceCard(accent="#f472b6")
        trend_title = QLabel("近两周执行与负荷走势")
        trend_title.setStyleSheet(text_style(SURFACE_TEXT_PRIMARY, 16, 700))
        self.trend_card.layout().addWidget(trend_title)
        self.chart = MultiSeriesChart(
            [
                ("完成", "completed", "#34d399", 30),
                ("到期", "due", "#60a5fa", 26),
                ("专注", "focus", "#c084fc", 22),
            ]
        )
        self.trend_card.layout().addWidget(self.chart)
        layout.addWidget(self.trend_card)

        detail_row = QHBoxLayout()
        detail_row.setSpacing(12)
        self.execution_panel = BulletPanel("执行摘要", "#34d399", "downloaded/png/rocket.png")
        self.structure_panel = BulletPanel("结构摘要", "#60a5fa", "downloaded/svg/panels-top-left.svg")
        detail_row.addWidget(self.execution_panel, 1)
        detail_row.addWidget(self.structure_panel, 1)
        layout.addLayout(detail_row)

        self.distribution_card = SurfaceCard(accent="#60a5fa")
        distribution_title = QLabel("分类负载与优先级密度")
        distribution_title.setStyleSheet(text_style(SURFACE_TEXT_PRIMARY, 16, 700))
        self.distribution_card.layout().addWidget(distribution_title)
        self.distribution_strip = DistributionStrip()
        self.distribution_card.layout().addWidget(self.distribution_strip)
        self.distribution_meta = QLabel("")
        self.distribution_meta.setWordWrap(True)
        self.distribution_meta.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 13) + " line-height: 1.7;")
        self.distribution_card.layout().addWidget(self.distribution_meta)
        layout.addWidget(self.distribution_card)

        self.focus_panel = BulletPanel("高投入事项", "#c084fc", "downloaded/png/glow.png")
        layout.addWidget(self.focus_panel)
        layout.addStretch(1)
        self.scroll.setWidget(content)

    def apply_snapshot(self, snapshot: dict[str, Any]) -> None:
        summary = snapshot.get("summary", {})
        self.hero_hint.setText(snapshot.get("hero_hint", ""))
        self.metric_cards[0].set_values(str(summary.get("completed_total", 0)), summary.get("completed_meta", ""))
        self.metric_cards[1].set_values(str(summary.get("due_total", 0)), summary.get("due_meta", ""))
        self.metric_cards[2].set_values(f"{summary.get('focus_total', 0)} 分钟", summary.get("focus_meta", ""))
        self.metric_cards[3].set_values(f"{summary.get('completion_rate', 0)}%", summary.get("rate_meta", ""))
        self.chart.set_series(snapshot.get("trend", []))
        self.execution_panel.set_items(snapshot.get("execution_lines", []), snapshot.get("execution_subtitle", ""))
        self.structure_panel.set_items(snapshot.get("structure_lines", []), snapshot.get("structure_subtitle", ""))
        strip_items = []
        palette = ["#60a5fa", "#34d399", "#f472b6", "#f59e0b", "#a78bfa"]
        for index, (name, count) in enumerate(snapshot.get("categories", [])[:5]):
            strip_items.append((name, count, palette[index % len(palette)]))
        self.distribution_strip.set_items(strip_items)
        self.distribution_meta.setText(snapshot.get("distribution_hint", ""))
        self.focus_panel.set_items(snapshot.get("focus_lines", []), snapshot.get("focus_subtitle", ""))


class ManagementCenterPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.scroll = SmartScrollArea()
        self.scroll.setStyleSheet("background: transparent; border: none;")
        root.addWidget(self.scroll)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 18)
        layout.setSpacing(14)

        hero = SurfaceCard(accent="#f59e0b", radius=28)
        hero_row = QHBoxLayout()
        hero_row.setSpacing(16)
        self.score_ring = ScoreRing()
        hero_row.addWidget(self.score_ring)
        hero_text = QVBoxLayout()
        hero_text.setSpacing(8)
        self.title_label = QLabel("管理中心")
        self.title_label.setStyleSheet(title_text_style(SURFACE_TEXT_PRIMARY, 24, 800))
        self.subtitle_label = QLabel("把同步、分类、知识沉淀和流程健康集中到同一处运营面板。")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet(text_style(SURFACE_TEXT_SECONDARY, 13) + " line-height: 1.75;")
        self.hint_label = QLabel("")
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet("color: #f59e0b; font-size: 12px; font-weight: 700;")
        hero_text.addWidget(self.title_label)
        hero_text.addWidget(self.subtitle_label)
        hero_text.addWidget(self.hint_label)
        hero_row.addLayout(hero_text, 1)
        hero.layout().addLayout(hero_row)
        layout.addWidget(hero)

        grid = QGridLayout()
        grid.setSpacing(12)
        self.overview_cards = [
            MetricTile("完成率", "#34d399", "downloaded/svg/shield-check.svg"),
            MetricTile("按期率", "#60a5fa", "downloaded/svg/chart-column-big.svg"),
            MetricTile("便签沉淀", "#f472b6", "downloaded/png/memo.png"),
            MetricTile("同步状态", "#f59e0b", "downloaded/svg/orbit.svg"),
        ]
        for index, card in enumerate(self.overview_cards):
            grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(grid)

        middle_row = QHBoxLayout()
        middle_row.setSpacing(12)
        self.insight_panel = BulletPanel("运营洞察", "#f59e0b", "downloaded/png/idea.png")
        self.structure_panel = BulletPanel("分类与沉淀", "#60a5fa", "downloaded/svg/folder-kanban.svg")
        middle_row.addWidget(self.insight_panel, 1)
        middle_row.addWidget(self.structure_panel, 1)
        layout.addLayout(middle_row)

        self.backlog_panel = BulletPanel("待处理事项", "#fb7185", "downloaded/svg/briefcase-business.svg")
        layout.addWidget(self.backlog_panel)

        action_card = SurfaceCard(accent="#60a5fa")
        action_title = QLabel("管理操作")
        action_title.setStyleSheet(text_style(SURFACE_TEXT_PRIMARY, 16, 700))
        action_card.layout().addWidget(action_title)
        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        self.export_button = QPushButton("导出数据")
        self.import_button = QPushButton("导入数据")
        self.category_button = QPushButton("分类管理")
        self.settings_button = QPushButton("打开设置")
        for button, role in [
            (self.export_button, "secondary"),
            (self.import_button, "ghost"),
            (self.category_button, "ghost"),
            (self.settings_button, "primary"),
        ]:
            button.setProperty("role", role)
            action_row.addWidget(button)
        action_card.layout().addLayout(action_row)
        layout.addWidget(action_card)
        layout.addStretch(1)
        self.scroll.setWidget(content)

    def apply_snapshot(self, snapshot: dict[str, Any]) -> None:
        self.score_ring.set_values(
            snapshot.get("health_score", 0),
            "健康指数",
            snapshot.get("health_caption", ""),
            snapshot.get("health_accent", "#f59e0b"),
        )
        self.hint_label.setText(snapshot.get("hero_hint", ""))
        self.overview_cards[0].set_values(f"{snapshot.get('completion_rate', 0)}%", snapshot.get("completion_meta", ""))
        self.overview_cards[1].set_values(f"{snapshot.get('on_time_rate', 0)}%", snapshot.get("on_time_meta", ""))
        self.overview_cards[2].set_values(str(snapshot.get("notes_total", 0)), snapshot.get("notes_meta", ""))
        self.overview_cards[3].set_values(snapshot.get("sync_state", "未同步"), snapshot.get("sync_meta", ""))
        self.insight_panel.set_items(snapshot.get("insights", []), snapshot.get("insight_subtitle", ""))
        structure_lines = [f"{name}：{count} 项" for name, count in snapshot.get("categories", [])[:6]]
        structure_lines.extend(snapshot.get("knowledge_lines", []))
        self.structure_panel.set_items(structure_lines, snapshot.get("structure_subtitle", ""))
        self.backlog_panel.set_items(snapshot.get("backlog_lines", []), snapshot.get("backlog_subtitle", ""))
