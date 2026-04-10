from __future__ import annotations

from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QSizePolicy, QVBoxLayout, QWidget

from DB import DB
from Task import Task
from ui.icon_manager import IconManager
from ui.starry_chrome import BODY_FONT, PALETTE, StarryActionButton, StarfieldSurface, StarryTagRow, set_layout_margins


def _fmt_dt(dt: Optional[datetime]) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%Y-%m-%d %H:%M")


def _fmt_compact_dt(dt: Optional[datetime]) -> str:
    if dt is None:
        return "未设置"
    return dt.strftime("%m-%d %H:%M")


def _button_qss(*, primary: bool) -> str:
    if primary:
        return (
            f"QPushButton {{ background: {PALETTE.button_fill_active}; border: 1px solid {_rgba(PALETTE.accent, 80)}; border-radius: 10px; color: {PALETTE.text_primary}; font-size: 14px; font-weight: 700; font-family: {BODY_FONT}; padding: 0 20px; min-height: 40px; }}"
            f"QPushButton:hover {{ background: {PALETTE.button_fill_hover}; border: 1px solid {_rgba(PALETTE.accent, 110)}; color: {PALETTE.text_primary}; }}"
            f"QPushButton:pressed {{ background: {PALETTE.button_fill}; }}"
            f"QPushButton:disabled {{ color: {_rgba(PALETTE.text_primary, 120)}; border: 1px solid {_rgba(PALETTE.accent, 28)}; background: rgba(255, 255, 255, 0.04); }}"
        )
    return (
        f"QPushButton {{ background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 10px; color: {PALETTE.text_primary}; font-size: 14px; font-weight: 600; font-family: {BODY_FONT}; padding: 0 16px; min-height: 40px; }}"
        f"QPushButton:hover {{ background: rgba(255, 255, 255, 0.10); border: 1px solid rgba(255, 255, 255, 0.18); color: {PALETTE.text_primary}; }}"
        f"QPushButton:pressed {{ background: rgba(255, 255, 255, 0.03); }}"
        f"QPushButton:disabled {{ color: {_rgba(PALETTE.text_primary, 90)}; border: 1px solid rgba(255, 255, 255, 0.06); }}"
    )


def _rgba(color: str, alpha: int) -> str:
    qcolor = QColor(color)
    return f"rgba({qcolor.red()}, {qcolor.green()}, {qcolor.blue()}, {alpha})"


def _mix_hex(left: str, right: str, ratio: float) -> str:
    ratio = max(0.0, min(1.0, ratio))
    left_color = QColor(left)
    right_color = QColor(right)
    red = int(left_color.red() + (right_color.red() - left_color.red()) * ratio)
    green = int(left_color.green() + (right_color.green() - left_color.green()) * ratio)
    blue = int(left_color.blue() + (right_color.blue() - left_color.blue()) * ratio)
    return f"#{red:02x}{green:02x}{blue:02x}"


def _card_qss(name: str) -> str:
    return (
        f"QFrame#{name} {{ background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; }}"
        f"QFrame#{name} QLabel {{ background: transparent; border: none; }}"
    )


def _inner_panel_qss(name: str) -> str:
    return (
        f"QFrame#{name} {{ background: rgba(255, 255, 255, 0.025); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 10px; }}"
        f"QFrame#{name} QLabel {{ background: transparent; border: none; }}"
    )


def _priority_tone(priority: str) -> str:
    if priority == "高":
        return "danger"
    if priority == "低":
        return "muted"
    return "accent"


class DetailCard(QFrame):
    def __init__(self, title: str, subtitle: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._title_text = title
        self._subtitle_text = subtitle
        self.setObjectName("detailCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.layout_ = QVBoxLayout(self)
        set_layout_margins(self.layout_, 22, 20, 22, 20, 10)

        self.title_label = QLabel(title)
        self.layout_.addWidget(self.title_label)

        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setWordWrap(True)
            self.layout_.addWidget(self.subtitle_label)
        else:
            self.subtitle_label = None

        self.body = QVBoxLayout()
        set_layout_margins(self.body, 0, 2, 0, 0, 14)
        self.layout_.addLayout(self.body)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        self.setStyleSheet(_card_qss(self.objectName()))
        self.title_label.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_muted, 220)}; font-size: 12px; font-weight: 700; font-family: {BODY_FONT};"
        )
        if self.subtitle_label is not None:
            self.subtitle_label.setStyleSheet(
                f"background: transparent; color: {_rgba(PALETTE.text_primary, 170)}; font-size: 12px; font-weight: 500; font-family: {BODY_FONT};"
            )


class DetailTextPanel(QFrame):
    def __init__(
        self,
        text: str,
        *,
        min_height: int = 96,
        empty_height: int = 78,
        empty_text: str = "暂无说明",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._filled_min_height = min_height
        self._empty_min_height = empty_height
        self._empty_text = empty_text
        self._current_text = text
        self._showing_empty_state = False
        self.setObjectName("detailTextPanel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(self)
        set_layout_margins(layout, 20, 18, 20, 18, 12)

        self.label = QLabel("")
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.label.setContentsMargins(0, 1, 0, 1)
        self.label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary}; font-size: 15px; font-weight: 500; font-family: {BODY_FONT};"
        )

        self.empty_label = QLabel(empty_text)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_muted}; font-size: 14px; font-weight: 600; font-family: {BODY_FONT};"
        )

        layout.addWidget(self.label)
        layout.addWidget(self.empty_label)
        self.refresh_theme()
        self.set_text(text, empty_text=empty_text)

    @property
    def showing_empty_state(self) -> bool:
        return self._showing_empty_state

    def set_text(self, text: str, *, empty_text: str | None = None) -> None:
        self._current_text = text
        content = (text or "").strip()
        self._empty_text = empty_text or self._empty_text
        self.empty_label.setText(self._empty_text)
        if content:
            self._showing_empty_state = False
            self.label.show()
            self.empty_label.hide()
            self.label.setText(content)
            self.setMinimumHeight(self._filled_min_height)
            return
        self._showing_empty_state = True
        self.label.hide()
        self.empty_label.show()
        self.setMinimumHeight(self._empty_min_height)

    def setText(self, text: str) -> None:  # noqa: N802
        self.set_text(text)

    def refresh_theme(self) -> None:
        self.setStyleSheet(_inner_panel_qss(self.objectName()))
        self.label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary}; font-size: 15px; font-weight: 500; font-family: {BODY_FONT};"
        )
        self.empty_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_muted}; font-size: 14px; font-weight: 600; font-family: {BODY_FONT};"
        )


class DetailMetricPanel(QFrame):
    def __init__(self, entries: list[tuple[str, str]] | None = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.layout_ = QVBoxLayout(self)
        set_layout_margins(self.layout_, 0, 0, 0, 0, 14)
        self._entries: list[tuple[str, str]] = []
        self.set_rows(entries or [])

    def set_rows(self, entries: list[tuple[str, str]]) -> None:
        self._entries = list(entries)
        while self.layout_.count():
            item = self.layout_.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not entries:
            empty = QLabel("暂无信息")
            empty.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            empty.setStyleSheet(
                f"background: transparent; color: {_rgba(PALETTE.text_primary, 194)}; font-size: 14px; font-weight: 600; font-family: {BODY_FONT};"
            )
            self.layout_.addWidget(empty)
            return

        for key, value in entries:
            row = QWidget()
            row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            row_layout = QVBoxLayout(row)
            set_layout_margins(row_layout, 0, 0, 0, 0, 3)

            key_label = QLabel(key)
            key_label.setWordWrap(False)
            key_label.setStyleSheet(
                f"background: transparent; color: {_rgba(PALETTE.text_primary, 172)}; font-size: 11px; font-weight: 700; font-family: {BODY_FONT}; letter-spacing: 0.8px;"
            )

            value_label = QLabel((value or "—").strip() or "—")
            value_label.setWordWrap(True)
            value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value_label.setStyleSheet(
                f"background: transparent; color: {PALETTE.text_primary}; font-size: 15px; font-weight: 700; font-family: {BODY_FONT};"
            )

            row_layout.addWidget(key_label)
            row_layout.addWidget(value_label)
            row.setMinimumHeight(42)
            self.layout_.addWidget(row)

    def refresh_theme(self) -> None:
        self.set_rows(self._entries)


class DetailProgressPanel(QFrame):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._progress = 0
        self._completed = False
        self.setObjectName("detailProgressPanel")
        self.layout_ = QVBoxLayout(self)
        set_layout_margins(self.layout_, 18, 16, 18, 16, 10)

        header = QHBoxLayout()
        set_layout_margins(header, 0, 0, 0, 0, 8)
        self.percent_label = QLabel("0%")
        self.percent_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary}; font-size: 22px; font-weight: 700; font-family: {BODY_FONT};"
        )
        self.state_label = QLabel("初始状态")
        self.state_label.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.accent_strong, 188)}; font-size: 12px; font-weight: 700; font-family: {BODY_FONT};"
        )
        header.addWidget(self.percent_label)
        header.addStretch(1)
        header.addWidget(self.state_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimumHeight(12)

        self.hint_label = QLabel("手动标记的任务进度会同步显示在甘特图中。")
        self.hint_label.setWordWrap(True)

        self.layout_.addLayout(header)
        self.layout_.addWidget(self.progress_bar)
        self.layout_.addWidget(self.hint_label)
        self.refresh_theme()

    def set_progress(self, progress: int, *, completed: bool) -> None:
        self._completed = completed
        self._progress = max(0, min(100, 100 if completed else progress))
        self.percent_label.setText(f"{self._progress}%")
        self.progress_bar.setValue(self._progress)
        if completed:
            self.state_label.setText("已完成")
            self.hint_label.setText("任务已完成，进度自动按 100% 展示。")
        elif self._progress <= 0:
            self.state_label.setText("尚未开始")
            self.hint_label.setText("初始进度为 0%，可在修改任务时手动标记。")
        else:
            self.state_label.setText("推进中")
            self.hint_label.setText("这是你手动标记的任务进度，甘特图会同步按这个比例展示。")
        self.refresh_theme()

    def refresh_theme(self) -> None:
        self.setStyleSheet(_inner_panel_qss(self.objectName()))
        self.percent_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary}; font-size: 22px; font-weight: 700; font-family: {BODY_FONT};"
        )
        accent = PALETTE.success if self._completed else PALETTE.accent_strong
        self.state_label.setStyleSheet(
            f"background: transparent; color: {_rgba(accent, 188)}; font-size: 12px; font-weight: 700; font-family: {BODY_FONT};"
        )
        self.hint_label.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_primary, 194)}; font-size: 13px; font-weight: 600; font-family: {BODY_FONT};"
        )
        chunk = PALETTE.success if self._completed else PALETTE.accent_strong
        self.progress_bar.setStyleSheet(
            f"QProgressBar {{ background: rgba(255, 255, 255, 0.06); border: 1px solid {_rgba(PALETTE.accent, 18)}; border-radius: 6px; }}"
            f"QProgressBar::chunk {{ background: {chunk}; border-radius: 5px; }}"
        )


class SubtaskListPanel(QFrame):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.row_count = 0
        self._tasks: list[Task] = []
        self._icon_manager = IconManager()
        self.setObjectName("subtaskListPanel")
        self.layout_ = QVBoxLayout(self)
        set_layout_margins(self.layout_, 14, 14, 14, 14, 10)
        self.refresh_theme()

    def set_tasks(self, tasks: list[Task]) -> None:
        self._tasks = list(tasks)
        while self.layout_.count():
            item = self.layout_.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.row_count = len(tasks)
        if not tasks:
            empty_label = QLabel("没有子任务")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(
                f"background: transparent; color: {PALETTE.text_muted}; font-size: 14px; font-weight: 600; font-family: {BODY_FONT};"
            )
            self.layout_.addWidget(empty_label)
            return

        for index, child in enumerate(tasks):
            row = QFrame()
            row.setStyleSheet(
                "background: rgba(255, 255, 255, 0.035);"
                "border: 1px solid rgba(214, 224, 238, 0.05);"
                "border-radius: 16px;"
            )
            row_layout = QHBoxLayout(row)
            set_layout_margins(row_layout, 14, 12, 14, 12, 12)

            icon_label = QLabel()
            icon_label.setPixmap(
                self._icon_manager.get_icon(
                    "check-circle" if child.completed else "circle",
                    size=16,
                    color=PALETTE.success if child.completed else PALETTE.accent_strong,
                ).pixmap(16, 16)
            )
            icon_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            icon_label.setFixedWidth(18)

            text_col = QVBoxLayout()
            set_layout_margins(text_col, 0, 0, 0, 0, 4)
            title_label = QLabel(child.title)
            title_label.setWordWrap(True)
            title_label.setStyleSheet(
                f"background: transparent; color: {PALETTE.text_primary}; font-size: 14px; font-weight: 700; font-family: {BODY_FONT};"
            )
            meta_parts: list[str] = []
            if child.priority:
                meta_parts.append(f"{child.priority}优先级")
            if child.due_at:
                meta_parts.append(f"截止 {_fmt_compact_dt(child.due_at)}")
            meta_label = QLabel(" · ".join(meta_parts) if meta_parts else "等待安排")
            meta_label.setWordWrap(True)
            meta_label.setStyleSheet(
                f"background: transparent; color: {_rgba(PALETTE.text_primary, 208)}; font-size: 12px; font-weight: 600; font-family: {BODY_FONT};"
            )
            text_col.addWidget(title_label)
            text_col.addWidget(meta_label)

            state_label = QLabel("已完成" if child.completed else "进行中")
            state_color = PALETTE.success if child.completed else PALETTE.accent_strong
            state_label.setStyleSheet(
                f"background: transparent; color: {_rgba(state_color, 196)}; border: none; padding: 0 2px; font-size: 11px; font-weight: 600; font-family: {BODY_FONT};"
            )

            row_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)
            row_layout.addLayout(text_col, 1)
            row_layout.addWidget(state_label, 0, Qt.AlignmentFlag.AlignTop)
            self.layout_.addWidget(row)

            if index != len(tasks) - 1:
                spacer = QFrame()
                spacer.setFixedHeight(2)
                spacer.setStyleSheet("background: transparent; border: none;")
                self.layout_.addWidget(spacer)

    def refresh_theme(self) -> None:
        self.setStyleSheet(_inner_panel_qss(self.objectName()))
        self.set_tasks(self._tasks)


class TaskDetailView(QWidget):
    back_requested = pyqtSignal()
    edit_requested = pyqtSignal(int)

    def __init__(self, db: DB, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.db = db
        self.task: Optional[Task] = None
        self.child_tasks: list[Task] = []
        self._wide_mode: Optional[bool] = None
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        set_layout_margins(outer, 18, 16, 18, 16, 0)

        self.page_shell = StarfieldSurface(radius=30, surface_mode="workspace", parent=self)
        outer.addWidget(self.page_shell)
        layout = QVBoxLayout(self.page_shell)
        set_layout_margins(layout, 24, 22, 24, 22, 18)

        header_row = QHBoxLayout()
        set_layout_margins(header_row, 0, 0, 0, 0, 18)

        title_box = QVBoxLayout()
        set_layout_margins(title_box, 0, 0, 0, 0, 6)
        self.title_label = QLabel("任务详情")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary}; font-size: 22px; font-weight: 700; font-family: {BODY_FONT};"
        )
        self.subtitle_label = QLabel("")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_secondary}; font-size: 13px; font-weight: 500; font-family: {BODY_FONT};"
        )
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.subtitle_label)
        header_row.addLayout(title_box, 1)

        action_row = QHBoxLayout()
        set_layout_margins(action_row, 0, 0, 0, 0, 10)
        self.back_button = StarryActionButton("返回上一页", kind="ghost")
        self.back_button.setMinimumWidth(122)
        self.back_button.setStyleSheet(_button_qss(primary=False))
        self.back_button.clicked.connect(self.back_requested.emit)

        self.edit_button = StarryActionButton("修改任务", kind="primary")
        self.edit_button.setMinimumWidth(138)
        self.edit_button.setStyleSheet(_button_qss(primary=True))
        self.edit_button.clicked.connect(self._emit_edit)

        action_row.addWidget(self.back_button)
        action_row.addWidget(self.edit_button)
        header_row.addLayout(action_row, 0)
        layout.addLayout(header_row)

        self.summary_tags = StarryTagRow([])
        layout.addWidget(self.summary_tags)

        self.content_grid = QGridLayout()
        set_layout_margins(self.content_grid, 0, 0, 0, 0, 18)
        self.content_grid.setHorizontalSpacing(18)
        self.content_grid.setVerticalSpacing(18)

        self.left_column = QWidget()
        self.left_column_layout = QVBoxLayout(self.left_column)
        set_layout_margins(self.left_column_layout, 0, 0, 0, 0, 18)

        self.right_column = QWidget()
        self.right_column_layout = QVBoxLayout(self.right_column)
        set_layout_margins(self.right_column_layout, 0, 0, 0, 0, 18)

        self.description_section = DetailCard("任务说明")
        self.description_view = DetailTextPanel("", min_height=84, empty_height=74, empty_text="暂无描述")
        self.description_section.body.addWidget(self.description_view)

        self.children_section = DetailCard("子任务")
        self.children_summary = QLabel("0 / 0 已完成")
        self.children_summary.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_secondary}; font-size: 14px; font-weight: 600; font-family: {BODY_FONT};"
        )
        self.children_panel = SubtaskListPanel()
        self.children_section.body.addWidget(self.children_summary)
        self.children_section.body.addWidget(self.children_panel)

        self.schedule_section = DetailCard("时间安排")
        self.schedule_panel = DetailMetricPanel([])
        self.schedule_section.body.addWidget(self.schedule_panel)

        self.progress_section = DetailCard("任务进度")
        self.progress_panel = DetailProgressPanel()
        self.progress_section.body.addWidget(self.progress_panel)

        self.execution_section = DetailCard("投入记录")
        self.execution_panel = DetailMetricPanel([])
        self.execution_section.body.addWidget(self.execution_panel)

        self.meta_section = DetailCard("记录信息")
        self.meta_panel = DetailMetricPanel([])
        self.meta_section.body.addWidget(self.meta_panel)

        self.left_column_layout.addWidget(self.description_section)
        self.left_column_layout.addWidget(self.children_section, 1)
        self.left_column_layout.addWidget(self.progress_section)

        self.right_column_layout.addWidget(self.schedule_section)
        self.right_column_layout.addWidget(self.execution_section)
        self.right_column_layout.addWidget(self.meta_section)
        self.right_column_layout.addStretch(1)

        layout.addLayout(self.content_grid)
        self._reflow_columns(force=True)
        self.apply_theme()

    def resizeEvent(self, a0) -> None:
        super().resizeEvent(a0)
        self._reflow_columns()

    def set_task(self, task: Task, children_map: dict) -> None:
        self.task = task
        self.child_tasks = children_map.get(task.id, [])

        category_text = task.category if task.category and task.category != "默认" else "无分类"
        tags = self.db.parse_tags(task.tags)
        scope_text = "子任务" if task.parent_id is not None else "主任务"
        state_text = "已完成" if task.completed else ("已逾期" if self._is_overdue(task) else "进行中")

        self.title_label.setText(task.title or "未命名任务")
        self.subtitle_label.setText(f"更新时间 · {_fmt_dt(task.updated_at)}")

        self.description_view.set_text(task.description or "", empty_text="暂无描述")
        self.schedule_panel.set_rows(
            [
                ("截止时间", _fmt_dt(task.due_at) if task.due_at else "未设置"),
                ("提醒时间", _fmt_dt(task.remind_at) if task.remind_at else "未设置"),
                ("循环", task.recurrence_rule or "不重复"),
            ]
        )
        self.execution_panel.set_rows(
            [
                ("预估投入", f"{task.estimated_minutes or 0} 分钟"),
                ("已投入", f"{task.tracked_minutes or 0} 分钟"),
            ]
        )
        self.progress_panel.set_progress(getattr(task, "progress", 0), completed=task.completed)

        meta_rows = [
            ("创建时间", _fmt_dt(task.created_at)),
        ]
        if task.completed_at:
            meta_rows.append(("完成时间", _fmt_dt(task.completed_at)))
        self.meta_panel.set_rows(meta_rows)

        self._fill_children()
        self._update_summary_tags(category_text, state_text, tags)

    def set_back_text(self, text: str) -> None:
        self.back_button.setText(text or "返回上一页")

    def _reflow_columns(self, *, force: bool = False) -> None:
        wide = self.width() >= 1200
        if not force and wide == self._wide_mode:
            return
        self._wide_mode = wide

        while self.content_grid.count():
            self.content_grid.takeAt(0)

        if wide:
            self.content_grid.addWidget(self.left_column, 0, 0)
            self.content_grid.addWidget(self.right_column, 0, 1)
            self.content_grid.setColumnStretch(0, 6)
            self.content_grid.setColumnStretch(1, 5)
        else:
            self.content_grid.addWidget(self.left_column, 0, 0)
            self.content_grid.addWidget(self.right_column, 1, 0)
            self.content_grid.setColumnStretch(0, 1)
            self.content_grid.setColumnStretch(1, 0)

    def _fill_children(self) -> None:
        if not self.child_tasks:
            self.children_section.setVisible(False)
            return
        self.children_section.setVisible(True)
        done = sum(1 for child in self.child_tasks if child.completed)
        self.children_summary.setText(f"{done} / {len(self.child_tasks)} 已完成")
        self.children_panel.set_tasks(self.child_tasks)

    def _update_summary_tags(self, category_text: str, state_text: str, tags: list[str]) -> None:
        if self.task is None:
            self.summary_tags.set_texts([])
            return

        scope_text = "子任务" if self.task.parent_id is not None else "主任务"

        self.summary_tags.set_texts(
            [
                (state_text, "success" if self.task.completed else ("danger" if self._is_overdue(self.task) else "accent")),
                (scope_text, "muted"),
                (category_text, "brass"),
                (f"{100 if self.task.completed else max(0, min(100, getattr(self.task, 'progress', 0)))}%", "accent"),
            ] + [(tag, "muted") for tag in tags[:2]]
        )

    def apply_theme(self) -> None:
        self.title_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary}; font-size: 22px; font-weight: 700; font-family: {BODY_FONT};"
        )
        self.subtitle_label.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_primary, 180)}; font-size: 13px; font-weight: 500; font-family: {BODY_FONT};"
        )
        self.back_button.setStyleSheet(_button_qss(primary=False))
        self.edit_button.setStyleSheet(_button_qss(primary=True))
        self.summary_tags.refresh_theme()
        self.description_section.refresh_theme()
        self.children_section.refresh_theme()
        self.schedule_section.refresh_theme()
        self.progress_section.refresh_theme()
        self.progress_panel.refresh_theme()
        self.execution_section.refresh_theme()
        self.meta_section.refresh_theme()
        self.description_view.refresh_theme()
        self.schedule_panel.refresh_theme()
        self.execution_panel.refresh_theme()
        self.meta_panel.refresh_theme()
        self.children_panel.refresh_theme()
        self.children_summary.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_primary, 214)}; font-size: 14px; font-weight: 700; font-family: {BODY_FONT};"
        )
        if self.task is not None:
            self.set_task(self.task, {self.task.id: self.child_tasks})

    def _emit_edit(self) -> None:
        if self.task is not None:
            self.edit_requested.emit(self.task.id)

    @staticmethod
    def _is_overdue(task: Task) -> bool:
        return bool(not task.completed and task.due_at and task.due_at < datetime.now())


class TaskDetailDialog(QDialog):
    def __init__(self, parent: QWidget, db: DB, task: Task, children_map: dict) -> None:
        super().__init__(parent)
        self.setWindowTitle("任务详情")
        self.resize(980, 720)
        layout = QVBoxLayout(self)
        self.view = TaskDetailView(db, self)
        self.view.set_task(task, children_map)
        self.view.back_requested.connect(self.reject)
        self.view.edit_requested.connect(lambda _task_id: self.accept())
        layout.addWidget(self.view)

    def payload_changed(self) -> bool:
        return False