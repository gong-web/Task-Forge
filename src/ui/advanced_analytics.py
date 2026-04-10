"""深度分析中心 —— AI 能力维度 + AI 结构化分析。"""
import math
from typing import Any

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF, QFont
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar,
    QSizePolicy, QVBoxLayout, QWidget,
)

from ai_service import AnalyticsAIWorker
from ui.ai_card_renderer import AICardRenderer, parse_ai_json
from ui.celestial_theme_catalog import mix_hex
from ui.scroll_area import SmartScrollArea
from ui.theme import (
    SURFACE_BG, SURFACE_BG_EMBED, SURFACE_BORDER, SURFACE_BORDER_SOFT,
    SURFACE_TEXT_MUTED, SURFACE_TEXT_PRIMARY, SURFACE_TEXT_SECONDARY,
    TITLE_FONT_FAMILY, rgba, surface_style, text_style, title_text_style,
)


# ── 雷达图 ─────────────────────────────────────────────────────
class RadarChart(QWidget):
    def __init__(self, data, labels, parent=None):
        super().__init__(parent)
        self.data = data
        self.labels = labels
        self.setMinimumSize(360, 320)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        center = QPointF(w / 2, h / 2)
        radius = min(w, h) / 2 * 0.65
        n = len(self.labels)
        if n == 0:
            return
        step = 2 * math.pi / n

        # Web
        painter.setPen(QPen(QColor(255, 255, 255, 44), 1))
        for lv in range(1, 7):
            r = radius * lv / 6
            poly = QPolygonF()
            for i in range(n):
                a = i * step - math.pi / 2
                poly.append(QPointF(center.x() + r * math.cos(a), center.y() + r * math.sin(a)))
            painter.drawPolygon(poly)

        # Axes and labels
        font = QFont(TITLE_FONT_FAMILY, 9)
        painter.setFont(font)
        fm = painter.fontMetrics()
        th = fm.height()
        for i in range(n):
            a = i * step - math.pi / 2
            ex, ey = center.x() + radius * math.cos(a), center.y() + radius * math.sin(a)
            painter.setPen(QPen(QColor(255, 255, 255, 36), 1))
            painter.drawLine(center, QPointF(ex, ey))
            # Vertex label with score combined on one line
            val = self.data[i] if i < len(self.data) else 0
            vertex_text = f"{self.labels[i]} {round(val * 100)}%"
            lx = center.x() + (radius + 40) * math.cos(a)
            ly = center.y() + (radius + 40) * math.sin(a)
            painter.setPen(QColor("#b0bcc8"))
            tw = fm.horizontalAdvance(vertex_text)
            painter.drawText(int(lx - tw / 2), int(ly + th / 4), vertex_text)

        # Polygon
        poly = QPolygonF()
        for i in range(n):
            a = i * step - math.pi / 2
            r = radius * (self.data[i] if i < len(self.data) else 0)
            poly.append(QPointF(center.x() + r * math.cos(a), center.y() + r * math.sin(a)))
        painter.setPen(QPen(QColor("#f472b6"), 2))
        painter.setBrush(QColor(244, 114, 182, 70))
        painter.drawPolygon(poly)
        painter.setBrush(QColor(SURFACE_TEXT_PRIMARY))
        for pt in poly:
            painter.drawEllipse(pt, 4, 4)


# ── 维度分数条 ──────────────────────────────────────────────────
def _make_dimension_bar(label: str, value: float, color: str, summary: str = "") -> QFrame:
    card = QFrame()
    card.setStyleSheet(
        f"QFrame {{ background: {rgba(color, 18)}; border-radius: 12px; border: none; }}"
    )
    outer = QVBoxLayout(card)
    outer.setContentsMargins(14, 10, 14, 10)
    outer.setSpacing(6)
    layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)
    name = QLabel(label)
    name.setStyleSheet(text_style(SURFACE_TEXT_SECONDARY, 13, 600))
    name.setFixedWidth(72)
    layout.addWidget(name)

    pct = max(0.0, min(1.0, value))
    bar_bg = QProgressBar()
    bar_bg.setRange(0, 100)
    bar_bg.setValue(int(pct * 100))
    bar_bg.setTextVisible(False)
    bar_bg.setFixedHeight(8)
    bar_bg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    bar_bg.setStyleSheet(
        f"QProgressBar {{ background: rgba(255,255,255,0.06); border-radius: 4px; border: none; }}"
        f"QProgressBar::chunk {{ background: {color}; border-radius: 4px; }}"
    )
    layout.addWidget(bar_bg)

    score = QLabel(f"{round(value * 100)}%")
    score.setFixedWidth(42)
    score.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    score.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 700;")
    layout.addWidget(score)
    outer.addLayout(layout)
    if summary:
        detail = QLabel(summary)
        detail.setWordWrap(True)
        detail.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 11) + " line-height: 1.5;")
        outer.addWidget(detail)
    return card


def _clamp_score(raw: Any) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    if value > 1.0:
        value /= 100.0
    return max(0.0, min(1.0, value))


_CAT_COLORS = ["#60a5fa", "#38bdf8", "#7dd3fc", "#0ea5e9", "#3b82f6", "#818cf8", "#a78bfa", "#6366f1"]


# ── 主视图 ──────────────────────────────────────────────────────
class AdvancedAnalyticsView(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.ai_worker = None
        self._last_ai_signature: str = ""
        self._last_snapshot: dict[str, Any] = {}
        self._last_visual_payload: dict[str, Any] = {"ability_profile": []}
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(0)

        # Header
        self.header_label = QLabel("深度分析中心")
        self.header_label.setStyleSheet(title_text_style(SURFACE_TEXT_PRIMARY, 22, 800))
        self.subtitle_label = QLabel("以结构化方式呈现 AI 生成的能力维度与深度洞察")
        self.subtitle_label.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 13) + " padding-bottom: 8px;")
        root.addWidget(self.header_label)
        root.addWidget(self.subtitle_label)

        scroll = SmartScrollArea()
        scroll.setStyleSheet("background: transparent; border: none;")
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(0, 12, 0, 12)
        self._body_layout.setSpacing(20)
        self._cards: list[QFrame] = []

        ability_card = self._card("AI 能力维度")
        self.ability_card = ability_card
        self._dim_container = QVBoxLayout()
        self._dim_container.setSpacing(8)
        ability_card.layout().addLayout(self._dim_container)
        ability_card.layout().addStretch()
        self._body_layout.addWidget(ability_card)

        # ── AI 分析 ──────────────────────────────────
        ai_card = self._card("AI 深度洞察")
        self.ai_card = ai_card

        self.ai_status_label = QLabel("")
        self.ai_status_label.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 13))
        self.ai_status_label.hide()
        ai_card.layout().addWidget(self.ai_status_label)

        self.ai_renderer = AICardRenderer()
        ai_card.layout().addWidget(self.ai_renderer)
        self._body_layout.addWidget(ai_card)

        self._body_layout.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll)
        self.apply_theme()

    def _theme_profile(self):
        return getattr(self.window(), "theme_profile", None)

    def _ui_palette(self):
        return getattr(self.window(), "ui_palette", None)

    def _accent_palette(self) -> list[str]:
        profile = self._theme_profile()
        if profile is None:
            return _CAT_COLORS
        return [
            profile.accent,
            profile.success,
            profile.warning,
            profile.danger,
            profile.brass,
            mix_hex(profile.accent, profile.brass, 0.35),
            mix_hex(profile.accent, "#ffffff", 0.18),
            mix_hex(profile.success, "#ffffff", 0.15),
        ]

    def apply_theme(self) -> None:
        ui_palette = self._ui_palette()
        panel_text = getattr(ui_palette, "panel_text", SURFACE_TEXT_PRIMARY)
        panel_muted = getattr(ui_palette, "panel_muted", SURFACE_TEXT_MUTED)
        self.header_label.setStyleSheet(title_text_style(panel_text, 22, 800))
        self.subtitle_label.setStyleSheet(text_style(panel_muted, 13) + " padding-bottom: 8px;")
        for card in getattr(self, "_cards", []):
            title_label = getattr(card, "_title_label", None)
            if title_label is not None:
                title_label.setStyleSheet(title_text_style(panel_text, 15, 700) + " border: none;")
            background = getattr(ui_palette, "card_secondary_bg", SURFACE_BG)
            card.setStyleSheet(surface_style(background, 18, border="rgba(255,255,255,0)"))
        self._apply_visual_payload(self._last_visual_payload)
        if getattr(self.ai_renderer, "_raw_text", ""):
            self.ai_renderer.render_raw(self.ai_renderer._raw_text)

    # ── 辅助 ──────────────────────────────────────────────────

    def _card(self, title: str) -> QFrame:
        card = QFrame()
        ui_palette = self._ui_palette()
        background = getattr(ui_palette, "card_secondary_bg", SURFACE_BG)
        card.setStyleSheet(surface_style(background, 18, border="rgba(255,255,255,0)"))
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        lbl = QLabel(title)
        lbl.setStyleSheet(
            title_text_style(SURFACE_TEXT_PRIMARY, 15, 700) + " border: none;"
        )
        layout.addWidget(lbl)
        card._title_label = lbl
        self._cards.append(card)
        return card

    def _local_ai_payload(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        radar = snapshot.get("radar", {})
        labels = radar.get("labels", [])
        values = radar.get("values", [])
        insights = snapshot.get("insights", [])
        strongest = max(zip(labels, values), key=lambda item: item[1], default=("暂无", 0))
        weakest = min(zip(labels, values), key=lambda item: item[1], default=("暂无", 0))
        palette = self._accent_palette()
        return {
            "summary": f"当前最强维度为{strongest[0]}，当前最弱维度为{weakest[0]}，建议围绕短板做持续修正。",
            "metrics": [
                {"label": "优势维度", "value": strongest[0], "trend": "up", "color": palette[1]},
                {"label": "待提升", "value": weakest[0], "trend": "down", "color": palette[2]},
                {"label": "洞察条数", "value": str(len(insights)), "trend": "flat", "color": palette[0]},
            ],
            "sections": [
                {
                    "title": "本地统计判断",
                    "color": palette[0],
                    "items": [
                        {"text": item, "severity": "info"} for item in insights[:3]
                    ] or [{"text": "当前暂无足够的历史统计洞察。", "severity": "low"}],
                },
                {
                    "title": "结构建议",
                    "color": palette[2],
                    "items": [
                        {"text": "进入详情页时自动阅读 AI 判断，把分析结果直接放进结构化卡片，而不是长文本段落。", "severity": "info"},
                        {"text": "如果短板维度长期不变，优先回看该类任务的描述和截止设置是否过于模糊。", "severity": "medium"},
                    ],
                },
            ],
            "actions": [
                {"text": f"优先围绕 {weakest[0]} 相关任务调整描述、时长和提醒。", "priority": "high"},
                {"text": "保持任务分类数量精简，避免过多分类削弱统计意义。", "priority": "medium"},
            ],
            "ability_profile": [
                {
                    "label": label,
                    "score": value,
                    "color": palette[index % len(palette)],
                    "summary": (
                        "保持稳定优势，可继续放大。" if value >= 0.75
                        else "表现中等，可通过更清晰的任务约束继续提升。" if value >= 0.5
                        else "当前偏弱，建议优先做针对性修正。"
                    ),
                }
                for index, (label, value) in enumerate(zip(labels, values))
            ],
        }

    def _visual_payload_from_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        return {"ability_profile": []}

    def _extract_visual_payload(self, data: dict[str, Any] | None, snapshot: dict[str, Any]) -> dict[str, Any]:
        fallback = self._visual_payload_from_snapshot(snapshot)
        if not isinstance(data, dict):
            return fallback

        ability_profile = data.get("ability_profile")
        parsed_abilities: list[dict[str, Any]] = []
        palette = self._accent_palette()
        if isinstance(ability_profile, list):
            for index, item in enumerate(ability_profile):
                if not isinstance(item, dict):
                    continue
                label = str(item.get("label") or "").strip()
                if not label:
                    continue
                parsed_abilities.append(
                    {
                        "label": label,
                        "score": _clamp_score(item.get("score")),
                        "color": palette[index % len(palette)],
                        "summary": str(item.get("summary") or "").strip(),
                    }
                )

        radar = data.get("radar")
        if isinstance(radar, dict):
            labels = [str(label).strip() for label in radar.get("labels", []) if str(label).strip()]
            values = [_clamp_score(value) for value in radar.get("values", [])]
            if not parsed_abilities and labels and len(labels) == len(values):
                parsed_abilities = [
                    {
                        "label": label,
                        "score": _clamp_score(value),
                        "color": palette[index % len(palette)],
                        "summary": "AI 已生成该维度评分。",
                    }
                    for index, (label, value) in enumerate(zip(labels, values))
                ]

        return {"ability_profile": parsed_abilities or fallback.get("ability_profile", [])}

    def _apply_visual_payload(self, visual_payload: dict[str, Any]) -> None:
        self._last_visual_payload = visual_payload if isinstance(visual_payload, dict) else {"ability_profile": []}

        while self._dim_container.count():
            item = self._dim_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        ability_profile = visual_payload.get("ability_profile", []) if isinstance(visual_payload, dict) else []
        if not ability_profile:
            empty = QLabel("AI 返回能力维度后会在这里展示，并按主题色重绘。")
            empty.setWordWrap(True)
            empty.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 12) + " line-height: 1.65;")
            self._dim_container.addWidget(empty)
            self._dim_container.addStretch(1)
            return
        for index, item in enumerate(ability_profile):
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or "").strip()
            if not label:
                continue
            score = _clamp_score(item.get("score"))
            palette = self._accent_palette()
            color = str(item.get("color") or palette[index % len(palette)])
            summary = str(item.get("summary") or "").strip()
            bar = _make_dimension_bar(label, score, color, summary)
            if summary:
                bar.setToolTip(summary)
            self._dim_container.addWidget(bar)

        self._dim_container.addStretch(1)

    def _analytics_signature(self, snapshot: dict[str, Any], tasks: list[Any]) -> str:
        marker = tuple(
            (task.id, getattr(task, "updated_at", None), getattr(task, "completed", False))
            for task in tasks[:80]
        )
        radar = tuple(snapshot.get("radar", {}).get("values", []))
        return repr((len(tasks), marker, radar, tuple(snapshot.get("insights", []))))

    # ── 数据刷新 ─────────────────────────────────────────────

    def refresh_data(self):
        snapshot = self.db.personal_analytics_snapshot()
        self._last_snapshot = snapshot
        if self._last_visual_payload.get("ability_profile"):
            self._apply_visual_payload(self._last_visual_payload)
        else:
            self._apply_visual_payload(self._visual_payload_from_snapshot(snapshot))

        self._refresh_ai_insights(snapshot)

    def _refresh_ai_insights(self, snapshot=None):
        analytics_snapshot = snapshot or self.db.personal_analytics_snapshot()
        tasks = self.db.list_tasks()
        signature = self._analytics_signature(analytics_snapshot, tasks)
        if signature == self._last_ai_signature and self.ai_worker is None:
            return
        if self.ai_worker is not None and self.ai_worker.isRunning():
            return
        self._last_ai_signature = signature
        self.ai_status_label.hide()
        self.ai_renderer.set_loading("AI 结构化分析中")
        self.ai_worker = AnalyticsAIWorker(analytics_snapshot, tasks, self)
        self.ai_worker.finished.connect(self._apply_ai_result)
        self.ai_worker.error.connect(self._apply_ai_error)
        self.ai_worker.finished.connect(self._finalize_ai_worker)
        self.ai_worker.error.connect(self._finalize_ai_worker)
        self.ai_worker.start()

    def _apply_ai_result(self, text: str):
        snapshot = self.db.personal_analytics_snapshot()
        parsed = parse_ai_json(text)
        success = getattr(self._theme_profile(), "success", "#34d399")
        self.ai_status_label.setText("AI 深度分析已更新")
        self.ai_status_label.setStyleSheet(
            f"color: {success}; font-size: 13px; font-weight: 600; "
            f"background: {rgba(success, 14)}; border-radius: 8px; padding: 4px 10px;"
        )
        self.ai_status_label.show()
        self._apply_visual_payload(self._extract_visual_payload(parsed, snapshot))
        self.ai_renderer.render_raw(text)

    def _apply_ai_error(self, message: str):
        snapshot = self.db.personal_analytics_snapshot()
        self._last_ai_signature = ""
        danger = getattr(self._theme_profile(), "danger", "#fb7185")
        self.ai_status_label.setText("AI 分析暂不可用")
        self.ai_status_label.setStyleSheet(
            f"color: {danger}; font-size: 13px; font-weight: 600; "
            f"background: {rgba(danger, 14)}; border-radius: 8px; padding: 4px 10px;"
        )
        self.ai_status_label.show()
        self._apply_visual_payload(self._visual_payload_from_snapshot(snapshot))
        self.ai_renderer.set_error(message)

    def _finalize_ai_worker(self, *_args) -> None:
        self.ai_worker = None
