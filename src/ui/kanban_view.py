from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtWidgets import QAbstractItemView, QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QSizePolicy, QVBoxLayout, QWidget

from ui.right_panels import SurfaceCard
from ui.theme import (
    SURFACE_BG_EMBED,
    SURFACE_BG_LIGHT,
    SURFACE_BORDER,
    SURFACE_BORDER_SOFT,
    SURFACE_GRADIENT_BASE_END,
    SURFACE_GRADIENT_BASE_START,
    SURFACE_TEXT_MUTED,
    SURFACE_TEXT_PRIMARY,
    SURFACE_TEXT_SECONDARY,
    rgba,
    surface_style,
    text_style,
    TITLE_FONT_FAMILY,
    chip_style,
)


class KanbanList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setStyleSheet(
            surface_style(SURFACE_BG_EMBED, 22, border=SURFACE_BORDER, selector="QListWidget")
            + "QListWidget { padding: 8px; font-size: 14px; }"
            + "QListWidget::item { margin: 6px 0px; padding: 0px; min-height: 0px; background: transparent; border: none; border-radius: 0px; }"
            + "QScrollBar:vertical { width: 4px; background: transparent; border: none; margin: 0; }"
            + "QScrollBar::handle:vertical { background: rgba(255,255,255,0.20); border-radius: 2px; min-height: 24px; }"
            + "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
            + "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }"
        )
        self.setSpacing(4)


class KanbanTaskCard(QFrame):
    def __init__(self, task, stage: str = "todo"):
        super().__init__()
        from datetime import datetime as _dt
        now = _dt.now()
        is_overdue = not task.completed and task.due_at and task.due_at < now
        accent = {"高": "#fb7185", "中": "#f59e0b", "低": "#60a5fa"}.get(task.priority, "#60a5fa")
        card_border = rgba("#fb7185", 60) if is_overdue else SURFACE_BORDER_SOFT
        self.setObjectName("kanbanTaskCard")
        # Priority accent via left border, keep gradient background
        self.setStyleSheet(
            f"QFrame#kanbanTaskCard {{ "
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"stop:0 {SURFACE_GRADIENT_BASE_START}, stop:1 {SURFACE_GRADIENT_BASE_END}); "
            f"border-radius: 14px; "
            f"border: 1px solid {card_border}; "
            f"border-left: 3px solid {accent}; "
            f"}}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(5)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        # Top row: category label + due date
        top = QHBoxLayout()
        top.setSpacing(4)
        top.setContentsMargins(0, 0, 0, 0)
        category = QLabel(task.category or "未分类")
        category.setStyleSheet(
            f"color: {SURFACE_TEXT_MUTED}; font-size: 11px; background: transparent; border: none;"
        )
        due_color = "#fb7185" if is_overdue else SURFACE_TEXT_SECONDARY
        due_text = task.due_at.strftime("%m-%d") if task.due_at else "未设日期"
        due = QLabel(due_text)
        due.setStyleSheet(f"color: {due_color}; font-size: 11px; background: transparent; border: none;")
        top.addWidget(category)
        top.addStretch(1)
        top.addWidget(due)
        layout.addLayout(top)

        # Title
        title = QLabel(task.title)
        title.setWordWrap(True)
        title.setStyleSheet(text_style(SURFACE_TEXT_PRIMARY, 14, 700))
        layout.addWidget(title)

        # Meta (focus/estimate/tags) — shown only when non-empty
        meta_parts = [
            f"专注 {task.tracked_minutes or 0}m",
            f"预估 {task.estimated_minutes or '--'}m" if task.estimated_minutes else "预估 --",
        ]
        if task.tags:
            meta_parts.append(task.tags)
        elif task.recurrence_rule and task.recurrence_rule != "不重复":
            meta_parts.append(task.recurrence_rule)
        meta = QLabel(" · ".join(meta_parts))
        meta.setStyleSheet(
            f"color: {SURFACE_TEXT_SECONDARY}; font-size: 11px; background: transparent; border: none;"
        )
        layout.addWidget(meta)


class KanbanColumn(QWidget):
    def __init__(self, title: str, accent: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.accent = accent
        self.setMinimumWidth(240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header = SurfaceCard(accent=accent, radius=22)
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"color: {accent}; font-size: 17px; font-weight: 800; font-family: {TITLE_FONT_FAMILY};")
        self.count_label = QLabel("0")
        self.count_label.setStyleSheet(chip_style(background=SURFACE_BG_LIGHT, border=accent, radius=12))
        title_row.addWidget(self.title_label)
        title_row.addStretch(1)
        title_row.addWidget(self.count_label)
        header.layout().addLayout(title_row)
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 12))
        header.layout().addWidget(self.subtitle_label)
        layout.addWidget(header)

        self.list_widget = KanbanList()
        layout.addWidget(self.list_widget, 1)

    def update_meta(self, count: int, subtitle: str) -> None:
        self.count_label.setText(str(count))
        self.subtitle_label.setText(subtitle)


class KanbanBoard(QWidget):
    task_detail_requested = pyqtSignal(int)  # emits task_id on card click

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.columns = {}
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 12, 20, 20)
        layout.setSpacing(12)

        # Summary bar
        summary_bar = QWidget()
        summary_bar.setStyleSheet(
            f"background: {SURFACE_BG_EMBED}; border-radius: 14px; border: 1px solid {SURFACE_BORDER};"
        )
        summary_layout = QHBoxLayout(summary_bar)
        summary_layout.setContentsMargins(16, 10, 16, 10)
        summary_layout.setSpacing(16)
        self.summary_labels = {}
        for key, (label, accent) in [
            ("active", ("活跃", "#60a5fa")),
            ("in_progress", ("推进中", "#f59e0b")),
            ("overdue", ("逾期", "#fb7185")),
            ("completed", ("已完成", "#34d399")),
        ]:
            lbl = QLabel(f"{label}: 0")
            lbl.setStyleSheet(f"color: {accent}; font-size: 13px; font-weight: 600; background: transparent; border: none;")
            summary_layout.addWidget(lbl)
            self.summary_labels[key] = lbl
        summary_layout.addStretch(1)
        layout.addWidget(summary_bar)

        # Board columns
        board_container = QWidget()
        board_container.setStyleSheet("background: transparent;")
        self.board_layout = QHBoxLayout(board_container)
        self.board_layout.setContentsMargins(0, 0, 0, 0)
        self.board_layout.setSpacing(12)

        self._add_column("todo", "待办池", "#60a5fa", "排期与拆分")
        self._add_column("in_progress", "推进中", "#f59e0b", "已有实际投入")
        self._add_column("review", "复核区", "#a78bfa", "临近节点")
        self._add_column("done", "已完成", "#34d399", "可复用成果")
        layout.addWidget(board_container, 1)

        root.addWidget(content)

    def _add_column(self, key: str, title: str, accent: str, subtitle: str) -> None:
        column = KanbanColumn(title, accent, subtitle)
        self.columns[key] = column
        column.list_widget.itemClicked.connect(self._on_card_clicked)
        self.board_layout.addWidget(column)

    def _on_card_clicked(self, item: QListWidgetItem) -> None:
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id is not None:
            self.task_detail_requested.emit(task_id)

    def refresh_data(self):
        payload = self.db.kanban_snapshot()
        self._last_snapshot = payload
        summary = payload.get("summary", {})

        self.summary_labels["active"].setText(f"活跃 {summary.get('active', 0)}")
        self.summary_labels["in_progress"].setText(f"推进 {summary.get('in_progress', 0)}")
        self.summary_labels["overdue"].setText(f"逾期 {summary.get('overdue', 0)}")
        self.summary_labels["completed"].setText(f"完成 {summary.get('completed', 0)}")

        subtitles = {
            "todo": "排期与拆分",
            "in_progress": "明确推进",
            "review": "临近复核",
            "done": "沉淀经验",
        }
        for key, column in self.columns.items():
            tasks = payload.get("columns", {}).get(key, [])
            column.update_meta(len(tasks), subtitles[key])
            column.list_widget.clear()
            for task in tasks:
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, task.id)
                card = KanbanTaskCard(task, stage=key)
                # Compact height: base + extra lines for long title + meta row
                card_height = 100
                if len(task.title) > 22:
                    card_height += 18
                if len(task.title) > 44:
                    card_height += 18
                item.setSizeHint(QSize(0, card_height))
                column.list_widget.addItem(item)
                column.list_widget.setItemWidget(item, card)
