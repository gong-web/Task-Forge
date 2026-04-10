"""AI 结构化分析结果渲染器 —— 将 AI 返回的 JSON 渲染为填充式卡片组件。"""
from __future__ import annotations

import json
import logging
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
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

from ui.theme import (
    SURFACE_BG,
    SURFACE_BG_EMBED,
    SURFACE_BG_LIGHT,
    SURFACE_BORDER,
    SURFACE_BORDER_SOFT,
    SURFACE_TEXT_MUTED,
    SURFACE_TEXT_PRIMARY,
    SURFACE_TEXT_SECONDARY,
    surface_style,
    text_style,
    title_text_style,
    TITLE_FONT_FAMILY,
    rgba,
)

_logger = logging.getLogger("task_forge.ai_renderer")

# ── Severity / trend 颜色映射（语义化）────────────────────────
_SEVERITY_COLORS = {
    "high": "#fb7185",
    "medium": "#f59e0b",
    "low": "#60a5fa",
    "info": "#94a3b8",
    "positive": "#34d399",
    "warning": "#f59e0b",
    "negative": "#fb7185",
}
_SEVERITY_DOTS = {
    "high": "●",
    "medium": "●",
    "low": "●",
    "info": "●",
    "positive": "●",
    "warning": "●",
    "negative": "●",
}
_TREND_ARROWS = {"up": "↑", "down": "↓", "flat": "→"}
_TREND_COLORS = {"up": "#34d399", "down": "#fb7185", "flat": "#94a3b8"}

# Softer section title palette (muted tones, not neon)
_SECTION_ACCENTS = [
    "#7dd3fc",  # soft sky
    "#86efac",  # soft green
    "#fca5a5",  # soft red
    "#fcd34d",  # soft amber
    "#c4b5fd",  # soft violet
    "#f9a8d4",  # soft pink
]


def parse_ai_json(raw: str) -> dict | None:
    """尝试从 AI 返回文本中提取 JSON，容忍首尾多余文字和 markdown 代码块。"""
    text = raw.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1 :]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try to find first { ... last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    return None


class AICardRenderer(QWidget):
    """将结构化 JSON dict 渲染为竖排卡片组，可嵌入任何布局。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(14)
        self._raw_text = ""
        # Placeholder
        self._placeholder = QLabel("AI 结构化结果会显示在这里")
        self._placeholder.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 13))
        self._root.addWidget(self._placeholder)

    def _theme_profile(self):
        return getattr(self.window(), "theme_profile", None)

    def _theme_palette(self):
        return getattr(self.window(), "ui_palette", None)

    def _severity_color(self, severity: str) -> str:
        profile = self._theme_profile()
        if profile is None:
            return _SEVERITY_COLORS.get(severity, SURFACE_TEXT_SECONDARY)
        mapping = {
            "high": profile.danger,
            "negative": profile.danger,
            "medium": profile.warning,
            "warning": profile.warning,
            "low": profile.accent,
            "info": getattr(profile, "text_muted", SURFACE_TEXT_MUTED),
            "positive": profile.success,
        }
        return mapping.get(severity, SURFACE_TEXT_SECONDARY)

    def _section_accents(self) -> list[str]:
        profile = self._theme_profile()
        if profile is None:
            return list(_SECTION_ACCENTS)
        return [
            profile.accent,
            profile.success,
            profile.warning,
            profile.danger,
            profile.brass,
            getattr(profile, "accent_strong", profile.accent),
        ]

    # ── 公共接口 ────────────────────────────────────────────────

    def render_json(self, data: dict) -> None:
        """清空并重新渲染。"""
        self._clear()
        if not data:
            self._add_fallback("AI 未返回有效数据")
            return
        # Summary 横幅
        summary = data.get("summary", "")
        if summary:
            self._add_summary_banner(summary)
        # Metrics 指标行
        metrics = data.get("metrics")
        if metrics and isinstance(metrics, list):
            self._add_metrics_row(metrics)
        # Sections 内容卡
        sections = data.get("sections")
        if sections and isinstance(sections, list):
            for idx, sec in enumerate(sections):
                self._add_section_card(sec, idx)
        # Actions 行动项
        actions = data.get("actions")
        if actions and isinstance(actions, list):
            self._add_action_card(actions)
        self._root.addStretch()
        # Toolbar at bottom
        self._add_toolbar()

    def render_raw(self, raw_text: str) -> None:
        """尝试解析 JSON 渲染；解析失败则回退纯文本。"""
        self._raw_text = raw_text
        data = parse_ai_json(raw_text)
        if data is not None:
            self.render_json(data)
        else:
            self._clear()
            self._add_fallback(raw_text)

    def set_loading(self, message: str = "正在生成 AI 分析...") -> None:
        self._clear()
        lbl = QLabel(message)
        lbl.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 13))
        self._root.addWidget(lbl)

    def set_error(self, message: str) -> None:
        self._clear()
        card = self._make_card("#fb7185")
        card_layout = self._layout_of(card)
        lbl = QLabel(f"⚠  分析失败: {message}")
        lbl.setWordWrap(True)
        lbl.setStyleSheet(text_style("#fecaca", 13))
        card_layout.addWidget(lbl)
        self._root.addWidget(card)

    # ── 内部构建方法 ────────────────────────────────────────────

    def _clear(self) -> None:
        while self._root.count():
            item = self._root.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w:
                w.deleteLater()

    def _make_card(self, accent: str = SURFACE_BORDER, radius: int = 16) -> QFrame:
        """Filled-background card (no outline border)."""
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {rgba(accent, 16)}; border-radius: {radius}px; border: none; }}"
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)
        return card

    def _layout_of(self, card: QFrame) -> QVBoxLayout:
        layout = card.layout()
        assert isinstance(layout, QVBoxLayout)
        return layout

    def _add_toolbar(self) -> None:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addStretch()
        copy_btn = QPushButton("复制结果")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet(
            f"QPushButton {{ color: {SURFACE_TEXT_MUTED}; font-size: 12px; "
            f"border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; "
            f"padding: 4px 12px; background: transparent; }}"
            f"QPushButton:hover {{ background: rgba(255,255,255,0.06); }}"
        )
        copy_btn.clicked.connect(self._copy_to_clipboard)
        row.addWidget(copy_btn)
        self._root.addLayout(row)

    def _copy_to_clipboard(self) -> None:
        if self._raw_text:
            clipboard = QGuiApplication.clipboard()
            if clipboard is not None:
                clipboard.setText(self._raw_text)

    def _add_fallback(self, text: str) -> None:
        accent = getattr(self._theme_profile(), "accent", "#60a5fa")
        card = self._make_card(accent)
        card_layout = self._layout_of(card)
        lbl = QLabel(text or "AI 当前未返回结构化内容，但本地分析仍然可用。")
        lbl.setWordWrap(True)
        lbl.setStyleSheet(text_style(SURFACE_TEXT_SECONDARY, 13, 600) + " line-height: 1.75;")
        card_layout.addWidget(lbl)
        self._root.addWidget(card)

    def _add_summary_banner(self, text: str) -> None:
        accent = getattr(self._theme_profile(), "accent", "#f472b6")
        card = self._make_card(accent)
        card_layout = self._layout_of(card)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            text_style(SURFACE_TEXT_PRIMARY, 14, 600) + " line-height: 1.7;"
        )
        card_layout.addWidget(lbl)
        self._root.addWidget(card)

    def _add_metrics_row(self, metrics: list[dict]) -> None:
        row = QFrame()
        row.setStyleSheet("background: transparent;")
        grid = QGridLayout(row)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(10)
        cols = min(3, len(metrics))
        for i, m in enumerate(metrics[:6]):
            tile = self._build_metric_tile(m)
            grid.addWidget(tile, i // cols, i % cols)
        self._root.addWidget(row)

    def _build_metric_tile(self, m: dict) -> QFrame:
        color = m.get("color", getattr(self._theme_profile(), "accent", "#60a5fa"))
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {rgba(color, 18)}; border-radius: 14px; border: none; }}"
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        value_row = QHBoxLayout()
        value_lbl = QLabel(str(m.get("value", "")))
        value_lbl.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: 800; font-family: {TITLE_FONT_FAMILY};")
        value_row.addWidget(value_lbl)

        trend = m.get("trend", "")
        if trend in _TREND_ARROWS:
            arrow = QLabel(_TREND_ARROWS[trend])
            arrow.setStyleSheet(f"color: {_TREND_COLORS[trend]}; font-size: 16px; font-weight: 700;")
            value_row.addWidget(arrow)
        value_row.addStretch()
        layout.addLayout(value_row)

        label = QLabel(str(m.get("label", "")))
        label.setStyleSheet(text_style(SURFACE_TEXT_SECONDARY, 12))
        layout.addWidget(label)
        return card

    def _add_section_card(self, sec: dict, index: int = 0) -> None:
        title = sec.get("title", "分析")
        section_accents = self._section_accents()
        accent = section_accents[index % len(section_accents)]
        items = sec.get("items", [])
        card = self._make_card(accent)
        card_layout = self._layout_of(card)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color: {accent}; font-size: 14px; font-weight: 700; font-family: {TITLE_FONT_FAMILY};"
        )
        card_layout.addWidget(title_lbl)

        for item in items:
            if isinstance(item, str):
                text = item
                severity = "info"
            else:
                text = item.get("text", "")
                severity = item.get("severity", "info")
            color = self._severity_color(severity)
            dot = _SEVERITY_DOTS.get(severity, "○")
            line = QLabel(f"  {dot}  {text}")
            line.setWordWrap(True)
            line.setStyleSheet(text_style(color, 13) + " line-height: 1.75; padding: 2px 0;")
            card_layout.addWidget(line)
        self._root.addWidget(card)

    def _add_action_card(self, actions: list) -> None:
        success = getattr(self._theme_profile(), "success", "#34d399")
        card = self._make_card(success)
        card_layout = self._layout_of(card)
        title = QLabel("行动建议")
        title.setStyleSheet(
            f"color: {success}; font-size: 14px; font-weight: 700; font-family: {TITLE_FONT_FAMILY};"
        )
        card_layout.addWidget(title)

        for i, act in enumerate(actions, 1):
            if isinstance(act, str):
                text = act
                priority = "medium"
            else:
                text = act.get("text", "")
                priority = act.get("priority", "medium")
            color = self._severity_color(priority)
            number = QLabel(f"  {i}.  {text}")
            number.setWordWrap(True)
            number.setStyleSheet(text_style(color, 13, 600) + " line-height: 1.7;")
            card_layout.addWidget(number)
        self._root.addWidget(card)
