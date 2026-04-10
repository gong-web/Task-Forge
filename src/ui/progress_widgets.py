"""
progress_widgets.py
───────────────────
Reusable progress-visualisation components used throughout the task manager.

Widgets
-------
SubtaskProgressBar
    A labelled, themed circular-plus-bar progress indicator showing how many
    sub-tasks within a group are completed.

HeatmapGrid
    A 7 × N grid of coloured cells representing daily task-completion density
    (similar to GitHub contribution graphs).

MiniSparkline
    A compact polyline graph for embedding inline trend data inside cards.

PriorityDistributionBar
    A horizontal segmented bar broken into HIGH / MED / LOW coloured zones.

DeadlineCountdown
    A label widget that dynamically shows how many days until a deadline,
    updating colour as the deadline approaches.
"""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Sequence

from PyQt6.QtCore import QRectF, QSize, Qt, QTimer
from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

ProgressRow = tuple[str, int, int] | tuple[str, int, int, str]


# ─────────────────────────────────────────── palette helpers ──────────────────

_ACCENT_BLUE = "#60a5fa"
_ACCENT_GREEN = "#34d399"
_ACCENT_PINK = "#f472b6"
_ACCENT_YELLOW = "#fbbf24"
_TEXT_PRIMARY = "#f1f5f9"
_TEXT_MUTED = "#94a3b8"
_SURFACE_BORDER = "rgba(255,255,255,0.10)"


def _hex_to_qcolor(hex_str: str) -> QColor:
    color = QColor(hex_str)
    return color if color.isValid() else QColor(150, 150, 150)


# ─────────────────────────────────────────── SubtaskProgressBar ──────────────


class SubtaskProgressBar(QWidget):
    """Circular arc + bar combo showing subtask completion ratio.

    Parameters
    ----------
    total:
        Total number of sub-tasks.
    done:
        Number of completed sub-tasks.
    accent:
        Hex colour string for the progress arc / bar fill.
    label:
        Optional short text rendered below the arc.
    """

    def __init__(
        self,
        total: int = 0,
        done: int = 0,
        accent: str = _ACCENT_BLUE,
        label: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._total = max(1, total)
        self._done = min(done, self._total)
        self._accent = _hex_to_qcolor(accent)
        self._label = label
        self.setFixedSize(QSize(120, 140))
        self.setToolTip(f"{self._done}/{self._total} 已完成")

    # ── public API ────────────────────────────────────────────────────────────

    def set_values(self, total: int, done: int) -> None:
        self._total = max(1, total)
        self._done = min(done, self._total)
        self.setToolTip(f"{self._done}/{self._total} 已完成")
        self.update()

    def set_accent(self, hex_color: str) -> None:
        self._accent = _hex_to_qcolor(hex_color)
        self.update()

    # ── rendering ─────────────────────────────────────────────────────────────

    def paintEvent(self, a0) -> None:  # noqa: N802
        ratio = self._done / self._total
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        arc_size = min(w, h - 30) - 8
        arc_rect = QRectF(
            (w - arc_size) / 2,
            4,
            arc_size,
            arc_size,
        )

        # Background ring
        pen = QPen(QColor(255, 255, 255, 25), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(arc_rect, 90 * 16, -360 * 16)

        # Filled arc
        fill_pen = QPen(self._accent, 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(fill_pen)
        span = int(-ratio * 360 * 16)
        painter.drawArc(arc_rect, 90 * 16, span)

        # Central percentage text
        pct_text = f"{int(ratio * 100)}%"
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(_TEXT_PRIMARY))
        painter.drawText(arc_rect.toRect(), Qt.AlignmentFlag.AlignCenter, pct_text)

        # Bottom label
        label_text = self._label or f"{self._done}/{self._total}"
        font_small = QFont()
        font_small.setPointSize(9)
        painter.setFont(font_small)
        painter.setPen(QColor(_TEXT_MUTED))
        label_rect = self.rect().adjusted(0, h - 26, 0, 0)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label_text)

        painter.end()


# ─────────────────────────────────────────── HeatmapGrid ─────────────────────


class HeatmapGrid(QWidget):
    """7-column task-completion heatmap grid (GitHub-style).

    Each cell represents one day.  Colour intensity scales with the
    completion count supplied.

    Parameters
    ----------
    weeks:
        How many weeks (columns) to render.  Default is 12 (3 months).
    accent:
        Hex colour for the maximum intensity cell.
    """

    _CELL = 14  # px per cell
    _GAP = 2    # px between cells

    def __init__(
        self,
        weeks: int = 12,
        accent: str = _ACCENT_GREEN,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._weeks = weeks
        self._accent = _hex_to_qcolor(accent)
        self._data: dict[date, int] = {}
        self._max_count = 1
        total_w = weeks * (self._CELL + self._GAP) + self._GAP
        total_h = 7 * (self._CELL + self._GAP) + self._GAP
        self.setFixedSize(QSize(total_w, total_h))

    # ── public API ────────────────────────────────────────────────────────────

    def set_data(self, counts: dict[date, int]) -> None:
        """Supply a mapping of date → completion-count."""
        self._data = counts
        self._max_count = max(counts.values(), default=1)
        self.update()

    # ── rendering ─────────────────────────────────────────────────────────────

    def paintEvent(self, a0) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        today = date.today()

        # Determine the start date (Monday, `weeks` weeks ago)
        start = today
        # Roll back to Monday
        start -= __import__("datetime").timedelta(days=start.weekday())
        start -= __import__("datetime").timedelta(weeks=self._weeks - 1)

        cell = self._CELL
        gap = self._GAP
        base = _hex_to_qcolor("#1e293b")

        for week_idx in range(self._weeks):
            for day_idx in range(7):
                cell_date = start + __import__("datetime").timedelta(
                    weeks=week_idx, days=day_idx
                )
                count = self._data.get(cell_date, 0)
                ratio = min(count / self._max_count, 1.0) if count > 0 else 0.0
                if ratio > 0:
                    r = int(base.red() + (self._accent.red() - base.red()) * ratio)
                    g = int(base.green() + (self._accent.green() - base.green()) * ratio)
                    b = int(base.blue() + (self._accent.blue() - base.blue()) * ratio)
                    fill = QColor(r, g, b)
                else:
                    fill = base

                x = gap + week_idx * (cell + gap)
                y = gap + day_idx * (cell + gap)
                painter.fillRect(x, y, cell, cell, fill)

                if cell_date == today:
                    painter.setPen(QPen(QColor(255, 255, 255, 80), 1))
                    painter.drawRect(x, y, cell - 1, cell - 1)
                    painter.setPen(Qt.PenStyle.NoPen)

        painter.end()

    def sizeHint(self) -> QSize:  # noqa: N802
        return self.minimumSize()


# ─────────────────────────────────────────── MiniSparkline ───────────────────


class MiniSparkline(QWidget):
    """Compact inline polyline chart for quick trend visualisation.

    Parameters
    ----------
    values:
        Sequence of numeric values to plot.
    accent:
        Hex colour string for the line/fill gradient.
    show_dots:
        Whether to draw dot markers at each data point.
    """

    def __init__(
        self,
        values: Sequence[float] | None = None,
        accent: str = _ACCENT_BLUE,
        show_dots: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._values: list[float] = list(values or [])
        self._accent = _hex_to_qcolor(accent)
        self._show_dots = show_dots
        self.setMinimumHeight(48)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    # ── public API ────────────────────────────────────────────────────────────

    def set_values(self, values: Sequence[float]) -> None:
        self._values = list(values)
        self.update()

    def set_accent(self, hex_color: str) -> None:
        self._accent = _hex_to_qcolor(hex_color)
        self.update()

    # ── rendering ─────────────────────────────────────────────────────────────

    def paintEvent(self, a0) -> None:  # noqa: N802
        if len(self._values) < 2:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        pad = 4
        plot_w = w - 2 * pad
        plot_h = h - 2 * pad

        v_min = min(self._values)
        v_max = max(self._values)
        v_range = max(v_max - v_min, 1e-9)
        n = len(self._values)

        def to_xy(i: int, v: float):
            x = pad + i * plot_w / (n - 1)
            y = pad + plot_h - (v - v_min) / v_range * plot_h
            return x, y

        # Gradient fill under line
        fill_path = QPainterPath()
        x0, y0 = to_xy(0, self._values[0])
        fill_path.moveTo(x0, h - pad)
        fill_path.lineTo(x0, y0)
        for i, v in enumerate(self._values[1:], start=1):
            xi, yi = to_xy(i, v)
            fill_path.lineTo(xi, yi)
        xn, yn = to_xy(n - 1, self._values[-1])
        fill_path.lineTo(xn, h - pad)
        fill_path.closeSubpath()

        fill_color = QColor(self._accent)
        fill_color.setAlpha(36)
        painter.fillPath(fill_path, fill_color)

        # Line
        line_pen = QPen(self._accent, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                        Qt.PenJoinStyle.RoundJoin)
        painter.setPen(line_pen)
        line_path = QPainterPath()
        x0, y0 = to_xy(0, self._values[0])
        line_path.moveTo(x0, y0)
        for i, v in enumerate(self._values[1:], start=1):
            xi, yi = to_xy(i, v)
            line_path.lineTo(xi, yi)
        painter.drawPath(line_path)

        # Dots
        if self._show_dots:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self._accent)
            for i, v in enumerate(self._values):
                xi, yi = to_xy(i, v)
                painter.drawEllipse(QRectF(xi - 3, yi - 3, 6, 6))

        painter.end()


# ─────────────────────────────────────────── PriorityDistributionBar ─────────


class PriorityDistributionBar(QWidget):
    """Horizontal segmented bar showing HIGH / MED / LOW task counts.

    Parameters
    ----------
    high, med, low:
        Counts for each priority level.
    """

    _HIGH_COLOR = "#ef4444"
    _MED_COLOR = "#eab308"
    _LOW_COLOR = "#3b82f6"
    _EMPTY_COLOR = "#1e293b"

    def __init__(
        self,
        high: int = 0,
        med: int = 0,
        low: int = 0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._high = high
        self._med = med
        self._low = low
        self.setFixedHeight(22)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._update_tooltip()

    # ── public API ────────────────────────────────────────────────────────────

    def set_counts(self, high: int, med: int, low: int) -> None:
        self._high = high
        self._med = med
        self._low = low
        self._update_tooltip()
        self.update()

    def _update_tooltip(self) -> None:
        total = self._high + self._med + self._low
        self.setToolTip(
            f"高优先级：{self._high}  中等：{self._med}  低优先级：{self._low}  共计：{total}"
        )

    # ── rendering ─────────────────────────────────────────────────────────────

    def paintEvent(self, a0) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        total = max(self._high + self._med + self._low, 1)
        w, h = self.width(), self.height()
        radius = h / 2

        segments = [
            (self._high, self._HIGH_COLOR),
            (self._med, self._MED_COLOR),
            (self._low, self._LOW_COLOR),
        ]

        if total == 0:
            path = QPainterPath()
            path.addRoundedRect(QRectF(0, 0, w, h), radius, radius)
            painter.fillPath(path, QColor(self._EMPTY_COLOR))
        else:
            x = 0.0
            for count, hex_col in segments:
                seg_w = w * count / total
                if seg_w < 1:
                    continue
                painter.fillRect(QRectF(x, 0, seg_w, h), QColor(hex_col))
                x += seg_w

            # Clip to rounded rect
            clip_path = QPainterPath()
            clip_path.addRoundedRect(QRectF(0, 0, w, h), radius, radius)
            painter.setClipPath(clip_path)

        painter.end()


# ─────────────────────────────────────────── DeadlineCountdown ───────────────


class DeadlineCountdown(QLabel):
    """Live-updating label displaying days remaining until a deadline.

    Colours:
    - green  : ≥ 7 days remaining
    - yellow : 2–6 days remaining
    - red    : ≤ 1 day or overdue
    """

    _REFRESH_MS = 60_000  # refresh every minute

    def __init__(self, deadline: datetime | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._deadline = deadline
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(self._REFRESH_MS)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._refresh()

    # ── public API ────────────────────────────────────────────────────────────

    def set_deadline(self, deadline: datetime | None) -> None:
        self._deadline = deadline
        self._refresh()

    # ── helpers ───────────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        if self._deadline is None:
            self.setText("—")
            self.setStyleSheet("color: #94a3b8; font-size: 12px;")
            return

        now = datetime.now()
        delta = self._deadline - now
        days = delta.days
        hours = delta.seconds // 3600

        if days > 6:
            text = f"还剩 {days} 天"
            color = "#34d399"
        elif days >= 2:
            text = f"还剩 {days} 天"
            color = "#fbbf24"
        elif days >= 0:
            if days == 0:
                text = f"今天到期，还剩 {hours} 小时"
            else:
                text = f"明天到期"
            color = "#f97316"
        else:
            text = f"已逾期 {abs(days)} 天"
            color = "#ef4444"

        self.setText(text)
        self.setStyleSheet(
            f"color: {color}; font-size: 12px; font-weight: 600;"
        )


# ─────────────────────────────────────────── InlineProgressRow ───────────────


class InlineProgressRow(QWidget):
    """One-line widget: [label] ────── [bar] ── [count/total].

    Suitable for embedding inside list items or compact summaries.

    Parameters
    ----------
    label:
        Short category / project name shown on the left.
    done, total:
        Completion statistics.
    accent:
        Hex colour for the bar fill.
    """

    def __init__(
        self,
        label: str = "",
        done: int = 0,
        total: int = 0,
        accent: str = _ACCENT_BLUE,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._accent = accent
        self._done = done
        self._total = max(1, total)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        self._lbl = QLabel(label)
        self._lbl.setFixedWidth(110)
        self._lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        row.addWidget(self._lbl)

        self._bar = _InlineBar(done, total, accent)
        row.addWidget(self._bar, 1)

        self._count_lbl = QLabel(f"{done}/{total}")
        self._count_lbl.setFixedWidth(48)
        self._count_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._count_lbl.setStyleSheet(f"color: {accent}; font-size: 11px; font-weight: 600;")
        row.addWidget(self._count_lbl)

    def set_values(self, done: int, total: int) -> None:
        self._done = done
        self._total = max(1, total)
        self._bar.set_values(done, total)
        self._count_lbl.setText(f"{done}/{total}")


class _InlineBar(QWidget):
    """Private thin bar used by InlineProgressRow."""

    def __init__(self, done: int, total: int, accent: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._done = done
        self._total = max(1, total)
        self._accent = _hex_to_qcolor(accent)
        self.setFixedHeight(6)

    def set_values(self, done: int, total: int) -> None:
        self._done = done
        self._total = max(1, total)
        self.update()

    def paintEvent(self, a0) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        r = h / 2
        # Track
        painter.fillRect(0, 0, w, h, QColor(255, 255, 255, 20))
        # Fill
        ratio = min(self._done / self._total, 1.0)
        fill_w = int(w * ratio)
        if fill_w > 0:
            path = QPainterPath()
            path.addRoundedRect(QRectF(0, 0, fill_w, h), r, r)
            painter.fillPath(path, self._accent)
        painter.end()


# ─────────────────────────────────────────── CategoryProgressPanel ────────────


class CategoryProgressPanel(QWidget):
    """Vertical stack of InlineProgressRow widgets, one per category.

    Parameters
    ----------
    rows:
        List of ``(label, done, total, hex_accent)`` tuples.
    title:
        Optional header text displayed above the list.
    """

    def __init__(
        self,
        rows: list[ProgressRow] | None = None,
        title: str = "分类进度",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        if title:
            header = QLabel(title)
            header.setStyleSheet("color: #f1f5f9; font-size: 13px; font-weight: 700;")
            root.addWidget(header)

        self._row_widgets: list[InlineProgressRow] = []
        self._layout = root
        if rows:
            self.set_rows(rows)

    def set_rows(self, rows: list[ProgressRow]) -> None:
        """Replace all rows with new data.

        Each tuple: ``(label, done, total, hex_accent)``.
        """
        # Remove old rows (keep the header)
        while len(self._row_widgets) > 0:
            w = self._row_widgets.pop()
            self._layout.removeWidget(w)
            w.setParent(None)  # type: ignore[call-overload]
            w.deleteLater()

        palette = [_ACCENT_BLUE, _ACCENT_GREEN, _ACCENT_PINK, _ACCENT_YELLOW,
                   "#c084fc", "#f97316", "#06b6d4"]
        for idx, item in enumerate(rows):
            if len(item) == 4:
                label, done, total, accent = item
            else:
                label, done, total = item
                accent = palette[idx % len(palette)]
            row = InlineProgressRow(label=label, done=done, total=total, accent=accent)
            self._row_widgets.append(row)
            self._layout.addWidget(row)
