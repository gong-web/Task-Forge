from __future__ import annotations

from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from ai_service import DashboardAIWorker
from ui.ai_card_renderer import parse_ai_json
from ui.right_panels import MetricTile, SurfaceCard
from ui.scroll_area import SmartScrollArea
from ui.theme import (
    SURFACE_TEXT_MUTED, SURFACE_TEXT_PRIMARY, SURFACE_TEXT_SECONDARY,
    rgba, text_style, title_text_style,
)


class DashboardView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._ai_worker = None
        self._last_payload = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.scroll = SmartScrollArea()
        self.scroll.setStyleSheet("background: transparent; border: none;")
        root.addWidget(self.scroll)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 20, 32, 28)
        layout.setSpacing(14)

        # ── Greeting strip ─────────────────────────────────────
        self._greeting_label = QLabel("")
        self._greeting_label.setStyleSheet(
            f"color: {SURFACE_TEXT_MUTED}; font-size: 12px; font-weight: 600; background: transparent;"
        )
        layout.addWidget(self._greeting_label)

        # ── Metric tiles (horizontal row of 4) ─────────────────
        metric_row = QHBoxLayout()
        metric_row.setSpacing(12)
        self.total_card = MetricTile("活跃任务", "#60a5fa", "downloaded/svg/layout-dashboard.svg")
        self.completed_card = MetricTile("本周完成", "#34d399", "downloaded/svg/circle-check-big.svg")
        self.overdue_card = MetricTile("逾期压力", "#fb7185", "downloaded/svg/flame.svg")
        self.focus_card = MetricTile("专注时长", "#c084fc", "downloaded/svg/timer-reset.svg")
        for card in [self.total_card, self.completed_card, self.overdue_card, self.focus_card]:
            metric_row.addWidget(card)
        layout.addLayout(metric_row)

        # ── Two-column: AI panel (left) + task lists (right) ───
        main_row = QHBoxLayout()
        main_row.setSpacing(14)
        main_row.addWidget(self._build_ai_panel(), 57)
        main_row.addWidget(self._build_tasks_panel(), 43)
        layout.addLayout(main_row)

        layout.addStretch(1)
        self.scroll.setWidget(content)

    # ── AI Panel ─────────────────────────────────────────────────

    def _build_ai_panel(self) -> SurfaceCard:
        panel = SurfaceCard(accent="#a78bfa")

        hdr = QHBoxLayout()
        hdr.setSpacing(10)
        title = QLabel("AI 工作洞察")
        title.setStyleSheet(title_text_style(SURFACE_TEXT_PRIMARY, 15, 800))
        hdr.addWidget(title)
        hdr.addStretch()

        self._ai_refresh_btn = QPushButton("⟳  刷新分析")
        self._ai_refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ai_refresh_btn.setStyleSheet(
            f"QPushButton {{ color: #a78bfa; font-size: 12px; font-weight: 700; "
            f"border: 1px solid {rgba('#a78bfa', 52)}; border-radius: 10px; "
            f"padding: 5px 14px; background: {rgba('#a78bfa', 12)}; }}"
            f"QPushButton:hover {{ background: {rgba('#a78bfa', 24)}; }}"
            f"QPushButton:disabled {{ color: {SURFACE_TEXT_MUTED}; border-color: rgba(255,255,255,0.1); }}"
        )
        self._ai_refresh_btn.clicked.connect(self._trigger_ai_analysis)
        hdr.addWidget(self._ai_refresh_btn)
        panel.layout().addLayout(hdr)

        self._ai_content_frame = QFrame()
        self._ai_content_frame.setStyleSheet("background: transparent; border: none;")
        self._ai_content_layout = QVBoxLayout(self._ai_content_frame)
        self._ai_content_layout.setContentsMargins(0, 4, 0, 0)
        self._ai_content_layout.setSpacing(8)

        placeholder = QLabel("点击「刷新分析」获取 AI 工作洞察\n基于你的真实任务数据生成个性化建议")
        placeholder.setWordWrap(True)
        placeholder.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 13))
        self._ai_content_layout.addWidget(placeholder)

        panel.layout().addWidget(self._ai_content_frame)
        panel.layout().addStretch(1)
        return panel

    def _trigger_ai_analysis(self):
        if self._ai_worker and self._ai_worker.isRunning():
            return
        if self._last_payload is None:
            return
        self._ai_refresh_btn.setEnabled(False)
        self._ai_refresh_btn.setText("⏳  分析中...")
        self._clear_ai_content()
        loading = QLabel("⏳  正在调用 AI，请稍候…")
        loading.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 13))
        self._ai_content_layout.addWidget(loading)

        self._ai_worker = DashboardAIWorker(self._last_payload, self)
        self._ai_worker.finished.connect(self._on_ai_finished)
        self._ai_worker.error.connect(self._on_ai_error)
        self._ai_worker.start()

    def _on_ai_finished(self, raw: str):
        self._ai_refresh_btn.setEnabled(True)
        self._ai_refresh_btn.setText("⟳  刷新分析")
        self._clear_ai_content()
        data = parse_ai_json(raw)
        if data:
            self._render_ai_data(data)
        else:
            lbl = QLabel(raw[:500] + ("…" if len(raw) > 500 else ""))
            lbl.setWordWrap(True)
            lbl.setStyleSheet(text_style(SURFACE_TEXT_SECONDARY, 13) + " line-height: 1.72;")
            self._ai_content_layout.addWidget(lbl)

    def _on_ai_error(self, msg: str):
        self._ai_refresh_btn.setEnabled(True)
        self._ai_refresh_btn.setText("⟳  刷新分析")
        self._clear_ai_content()
        err = QLabel(f"⚠  分析暂不可用：{msg}")
        err.setWordWrap(True)
        err.setStyleSheet("color: #fca5a5; font-size: 13px; font-weight: 600; background: transparent;")
        self._ai_content_layout.addWidget(err)

    def _clear_ai_content(self):
        while self._ai_content_layout.count():
            item = self._ai_content_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _render_ai_data(self, data: dict):
        # Greeting banner
        greeting = data.get("greeting", "")
        if greeting:
            greet = QLabel(greeting)
            greet.setWordWrap(True)
            greet.setStyleSheet(
                f"color: {SURFACE_TEXT_PRIMARY}; font-size: 14px; font-weight: 600; "
                f"background: {rgba('#a78bfa', 14)}; border-radius: 12px; "
                f"padding: 11px 14px; border: 1px solid {rgba('#a78bfa', 32)};"
            )
            self._ai_content_layout.addWidget(greet)

        # Focus task highlight
        focus = data.get("focus_task", "")
        if focus:
            focus_row = QHBoxLayout()
            focus_row.setSpacing(8)
            lbl = QLabel("今日聚焦")
            lbl.setStyleSheet(
                f"color: {SURFACE_TEXT_MUTED}; font-size: 11px; font-weight: 700; background: transparent;"
            )
            lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
            val = QLabel(focus)
            val.setWordWrap(True)
            val.setStyleSheet("color: #fbbf24; font-size: 13px; font-weight: 700; background: transparent;")
            focus_row.addWidget(lbl)
            focus_row.addWidget(val, 1)
            self._ai_content_layout.addLayout(focus_row)

        # Insight chips
        for ins in (data.get("insights") or [])[:4]:
            color = ins.get("color", "#60a5fa")
            text = ins.get("text", "")
            tag = ins.get("tag", "")
            row = QFrame()
            row.setStyleSheet(
                f"QFrame {{ background: {rgba(color, 11)}; border-radius: 10px; "
                f"border-left: 3px solid {color}; border-top: none; "
                f"border-right: none; border-bottom: none; }}"
            )
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 7, 12, 7)
            row_layout.setSpacing(8)
            if tag:
                tag_lbl = QLabel(tag)
                tag_lbl.setStyleSheet(
                    f"color: {color}; font-size: 10px; font-weight: 800; "
                    f"background: {rgba(color, 20)}; border-radius: 6px; padding: 2px 6px; border: none;"
                )
                tag_lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
                row_layout.addWidget(tag_lbl)
            text_lbl = QLabel(text)
            text_lbl.setWordWrap(True)
            text_lbl.setStyleSheet(
                f"color: {SURFACE_TEXT_SECONDARY}; font-size: 12px; font-weight: 600; "
                f"background: transparent; border: none;"
            )
            row_layout.addWidget(text_lbl, 1)
            self._ai_content_layout.addWidget(row)

        # Action items
        actions = (data.get("actions") or [])[:3]
        if actions:
            acts_title = QLabel("行动建议")
            acts_title.setStyleSheet(
                f"color: {SURFACE_TEXT_MUTED}; font-size: 11px; font-weight: 700; background: transparent;"
            )
            self._ai_content_layout.addWidget(acts_title)
            _p_colors = {"high": "#fb7185", "medium": "#f59e0b", "low": "#60a5fa"}
            for act in actions:
                color = _p_colors.get(act.get("priority", "low"), "#60a5fa")
                arow = QHBoxLayout()
                arow.setSpacing(6)
                dot = QLabel("▸")
                dot.setFixedWidth(14)
                dot.setStyleSheet(f"color: {color}; font-size: 13px; background: transparent;")
                act_lbl = QLabel(act.get("text", ""))
                act_lbl.setWordWrap(True)
                act_lbl.setStyleSheet(
                    f"color: {SURFACE_TEXT_SECONDARY}; font-size: 12px; font-weight: 600; background: transparent;"
                )
                arow.addWidget(dot)
                arow.addWidget(act_lbl, 1)
                self._ai_content_layout.addLayout(arow)

    # ── Tasks Panel ───────────────────────────────────────────────

    def _build_tasks_panel(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Upcoming / due today
        self._upcoming_card = SurfaceCard(accent="#38bdf8")
        hdr = QHBoxLayout()
        t = QLabel("今日事项")
        t.setStyleSheet(title_text_style(SURFACE_TEXT_PRIMARY, 14, 800))
        self._upcoming_badge = QLabel("0 项")
        self._upcoming_badge.setStyleSheet(
            f"color: #38bdf8; font-size: 11px; font-weight: 700; "
            f"background: {rgba('#38bdf8', 18)}; border-radius: 8px; padding: 2px 8px;"
        )
        hdr.addWidget(t)
        hdr.addStretch()
        hdr.addWidget(self._upcoming_badge)
        self._upcoming_card.layout().addLayout(hdr)
        self._upcoming_body = QVBoxLayout()
        self._upcoming_body.setSpacing(5)
        self._upcoming_card.layout().addLayout(self._upcoming_body)
        layout.addWidget(self._upcoming_card)

        # Recent completed
        self._recent_card = SurfaceCard(accent="#34d399")
        r_hdr = QLabel("近期完成")
        r_hdr.setStyleSheet(title_text_style(SURFACE_TEXT_PRIMARY, 14, 800))
        self._recent_card.layout().addWidget(r_hdr)
        self._recent_body = QVBoxLayout()
        self._recent_body.setSpacing(5)
        self._recent_card.layout().addLayout(self._recent_body)
        layout.addWidget(self._recent_card)

        layout.addStretch(1)
        return container

    def _populate_list(self, layout, lines: list[str], accent: str, empty_msg: str):
        while layout.count():
            item = layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        if not lines or (len(lines) == 1 and lines[0].startswith("暂无")):
            empty = QLabel(empty_msg)
            empty.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 12))
            layout.addWidget(empty)
            return
        for line in lines[:5]:
            row = QFrame()
            row.setStyleSheet(
                f"QFrame {{ background: {rgba(accent, 10)}; border-radius: 8px; "
                f"border: 1px solid {rgba(accent, 22)}; }}"
            )
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 6, 10, 6)
            lbl = QLabel(line)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(
                f"color: {SURFACE_TEXT_SECONDARY}; font-size: 12px; font-weight: 600; "
                f"background: transparent; border: none;"
            )
            row_layout.addWidget(lbl)
            layout.addWidget(row)

    # ── Data Refresh ──────────────────────────────────────────────

    def refresh_data(self):
        payload = self.db.dashboard_story_snapshot()
        self._last_payload = payload
        snapshot = payload["snapshot"]

        today_str = date.today().strftime("%m月%d日")
        parts = payload.get("hero_hint", "").split("｜")
        streak_text = parts[0] if parts else ""
        on_time_text = parts[1] if len(parts) > 1 else ""
        self._greeting_label.setText(f"{today_str}  ·  {streak_text}  ·  {on_time_text}")

        self.total_card.set_values(str(snapshot["active"]), f"今日到期 {snapshot['due_today']} 项")
        weekly_completed = sum(int(item.get("completed", 0)) for item in payload.get("trend", [])[-7:])
        self.completed_card.set_values(str(weekly_completed), f"完成率 {snapshot['completion_rate']}%")
        self.overdue_card.set_values(str(snapshot["overdue"]), "优先清理高风险任务")
        self.focus_card.set_values(f"{snapshot['focus_minutes']}m", f"人均 {payload.get('focus_density', 0)}m/项")

        upcoming = payload.get("upcoming_lines", [])
        shown = [l for l in upcoming if not l.startswith("暂无")]
        self._upcoming_badge.setText(f"{len(shown)} 项")
        self._populate_list(self._upcoming_body, upcoming, "#38bdf8", "暂无今日到期任务")
        self._populate_list(self._recent_body, payload.get("recent_lines", []), "#34d399", "暂无近期完成记录")
