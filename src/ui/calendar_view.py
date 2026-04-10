from __future__ import annotations

from datetime import date as dt_date

from PyQt6.QtCore import QPoint, QDate, Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ui.scroll_area import SmartScrollArea
from ui.theme import ACCENT_BORDER, ACCENT_SURFACE_SOFT, SURFACE_BG_DIM, SURFACE_BG_DIM_HOVER, SURFACE_BG_FLOAT, SURFACE_BORDER_SOFT, SURFACE_TEXT_MUTED, SURFACE_TEXT_PRIMARY, SURFACE_TEXT_SECONDARY, chip_style, rgba, surface_style, text_style


class CalendarDayCell(QFrame):
    clicked = pyqtSignal(QDate, QPoint)

    def __init__(self, target_date: QDate, parent=None):
        super().__init__(parent)
        self.target_date = target_date
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.target_date, self.mapToGlobal(self.rect().bottomLeft()))
        super().mousePressEvent(event)


class DayTaskPopup(QDialog):
    def __init__(self, main_window, target_date: dt_date, tasks: list, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.target_date = target_date
        self.tasks = tasks
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        theme_profile = getattr(main_window, "theme_profile", None)
        ui_palette = getattr(main_window, "ui_palette", None)
        accent = getattr(theme_profile, "accent", ACCENT_BORDER)
        accent_soft = getattr(theme_profile, "accent_soft", ACCENT_SURFACE_SOFT)
        success = getattr(theme_profile, "success", "#10b981")
        warning = getattr(theme_profile, "warning", "#f59e0b")
        danger = getattr(theme_profile, "danger", "#fb7185")
        panel_bg = getattr(theme_profile, "panel_bottom", "#0f172a")
        panel_text = getattr(ui_palette, "panel_text", SURFACE_TEXT_PRIMARY)
        muted = getattr(ui_palette, "panel_muted", SURFACE_TEXT_MUTED)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        shell = QFrame()
        shell.setStyleSheet(
            f"QFrame {{ background: {rgba(panel_bg, 238)}; border-radius: 18px; border: 1px solid {rgba(accent, 92)}; }}"
            "QLabel { background: transparent; border: none; }"
        )
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(16, 14, 16, 14)
        shell_layout.setSpacing(10)

        title = QLabel(f"{target_date:%Y年%m月%d日} 的任务")
        title.setStyleSheet(text_style(panel_text, 14, 800))
        subtitle = QLabel(f"共 {len(tasks)} 项到期任务")
        subtitle.setStyleSheet(text_style(muted, 11))
        shell_layout.addWidget(title)
        shell_layout.addWidget(subtitle)

        if tasks:
            today = dt_date.today()
            for task in tasks[:6]:
                row = QPushButton(task.title)
                row.setCursor(Qt.CursorShape.PointingHandCursor)
                row.setStyleSheet(
                    f"QPushButton {{ text-align: left; background: {rgba(accent, 18)}; border: none; border-radius: 12px; color: {panel_text}; padding: 10px 12px; font-size: 12px; font-weight: 600; }}"
                    f"QPushButton:hover {{ background: {rgba(accent, 28)}; }}"
                )
                if task.completed:
                    row.setToolTip("已完成任务")
                    row.setStyleSheet(
                        f"QPushButton {{ text-align: left; background: {rgba(success, 18)}; border: none; border-radius: 12px; color: {panel_text}; padding: 10px 12px; font-size: 12px; font-weight: 600; }}"
                        f"QPushButton:hover {{ background: {rgba(success, 28)}; }}"
                    )
                elif target_date < today:
                    row.setToolTip("已逾期任务")
                    row.setStyleSheet(
                        f"QPushButton {{ text-align: left; background: {rgba(danger, 18)}; border: none; border-radius: 12px; color: {panel_text}; padding: 10px 12px; font-size: 12px; font-weight: 600; }}"
                        f"QPushButton:hover {{ background: {rgba(danger, 28)}; }}"
                    )
                else:
                    row.setToolTip("点击查看详情")
                row.clicked.connect(lambda _, task_id=task.id: self._open_task(task_id))
                shell_layout.addWidget(row)
            if len(tasks) > 6:
                more = QLabel(f"其余 {len(tasks) - 6} 项可在任务树中查看")
                more.setStyleSheet(text_style(muted, 11))
                shell_layout.addWidget(more)
        else:
            empty = QLabel("当天没有到期任务")
            empty.setStyleSheet(text_style(muted, 12))
            shell_layout.addWidget(empty)

        jump_btn = QPushButton("定位到任务树日期分组")
        jump_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        jump_btn.setStyleSheet(
            chip_style(text_color=panel_text, background=accent_soft, border=rgba(accent, 92), radius=12, padding="8px 12px")
        )
        jump_btn.clicked.connect(self._jump_to_tree)
        shell_layout.addWidget(jump_btn)

        layout.addWidget(shell)

    def _jump_to_tree(self) -> None:
        if self.main_window is not None:
            self.main_window.focus_tasks_for_date(self.target_date)
        self.close()

    def _open_task(self, task_id: int) -> None:
        self.close()
        if self.main_window is not None:
            self.main_window.open_task_detail(task_id)


class CalendarView(QWidget):
    def __init__(self, db, main_window=None):
        super().__init__()
        self.db = db
        self.main_window = main_window
        self.current_date = QDate.currentDate()
        self.selected_date = QDate.currentDate()
        self._legend_labels: list[tuple[QLabel, QLabel]] = []
        self._nav_buttons: list[QPushButton] = []
        self._day_popup: DayTaskPopup | None = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        self.month_lbl = QLabel()
        self.month_lbl.setStyleSheet(text_style(SURFACE_TEXT_PRIMARY, 20, "bold"))
        
        prev_btn = QPushButton("<")
        prev_btn.setFixedSize(32, 32)
        prev_btn.clicked.connect(self._prev_month)

        today_btn = QPushButton("今日")
        today_btn.setFixedHeight(32)
        today_btn.clicked.connect(self._goto_today)

        next_btn = QPushButton(">")
        next_btn.setFixedSize(32, 32)
        next_btn.clicked.connect(self._next_month)
        self._nav_buttons = [prev_btn, today_btn, next_btn]

        header_layout.addWidget(self.month_lbl)
        header_layout.addStretch()
        header_layout.addWidget(prev_btn)
        header_layout.addWidget(today_btn)
        header_layout.addWidget(next_btn)

        layout.addLayout(header_layout)

        # Color legend
        legend_row = QHBoxLayout()
        legend_row.setSpacing(14)
        legend_row.setContentsMargins(0, 0, 0, 0)
        for color_hex, legend_text in [("#10b981", "已完成"), (ACCENT_BORDER, "进行中"), ("#fb7185", "已逾期")]:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color_hex}; font-size: 13px; background: transparent;")
            lbl = QLabel(legend_text)
            lbl.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 12))
            legend_row.addWidget(dot)
            legend_row.addWidget(lbl)
            self._legend_labels.append((dot, lbl))
        legend_row.addStretch()
        layout.addLayout(legend_row)
        
        # Weekdays header
        week_layout = QGridLayout()
        week_layout.setSpacing(8)
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i, wd in enumerate(weekdays):
            lbl = QLabel(wd)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 14, "bold") + " padding: 8px;")
            week_layout.addWidget(lbl, 0, i)
            
        # Grid for days
        self.grid = QGridLayout()
        self.grid.setSpacing(8)
        
        grid_container = QWidget()
        grid_container.setLayout(self.grid)
        
        scroll = SmartScrollArea()
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setWidget(grid_container)
        
        layout.addLayout(week_layout)
        layout.addWidget(scroll, 1)
        
        self.apply_theme()
        self.refresh_data()
        
    def _prev_month(self):
        self.current_date = self.current_date.addMonths(-1)
        self.refresh_data()

    def _next_month(self):
        self.current_date = self.current_date.addMonths(1)
        self.refresh_data()

    def _goto_today(self):
        self.current_date = QDate.currentDate()
        self.selected_date = QDate.currentDate()
        self.refresh_data()

    def _theme_tokens(self) -> dict[str, str]:
        theme_profile = getattr(self.main_window, "theme_profile", None)
        ui_palette = getattr(self.main_window, "ui_palette", None)
        return {
            "accent": getattr(theme_profile, "accent", ACCENT_BORDER),
            "accent_soft": getattr(theme_profile, "accent_soft", ACCENT_SURFACE_SOFT),
            "success": getattr(theme_profile, "success", "#10b981"),
            "warning": getattr(theme_profile, "warning", "#f59e0b"),
            "danger": getattr(theme_profile, "danger", "#fb7185"),
            "text": getattr(ui_palette, "panel_text", SURFACE_TEXT_PRIMARY),
            "text_secondary": getattr(ui_palette, "panel_text_soft", SURFACE_TEXT_SECONDARY),
            "muted": getattr(ui_palette, "panel_muted", SURFACE_TEXT_MUTED),
            "cell_bg": getattr(theme_profile, "field_fill", SURFACE_BG_DIM),
            "cell_hover": getattr(theme_profile, "field_fill_hover", SURFACE_BG_DIM_HOVER),
            "cell_border": getattr(ui_palette, "panel_border", SURFACE_BORDER_SOFT),
        }

    def apply_theme(self):
        tokens = self._theme_tokens()
        self.month_lbl.setStyleSheet(text_style(tokens["text"], 20, "bold"))
        for button in self._nav_buttons:
            button.setStyleSheet(
                chip_style(
                    radius=16 if button.text() in {"<", ">"} else 8,
                    padding="0px" if button.text() in {"<", ">"} else "0px 10px",
                    background=rgba(tokens["accent"], 18),
                    border=rgba(tokens["accent"], 72),
                    text_color=tokens["text"],
                )
            )
        legend_colors = [tokens["success"], tokens["accent"], tokens["danger"]]
        for index, (dot, label) in enumerate(self._legend_labels):
            dot.setStyleSheet(f"color: {legend_colors[index]}; font-size: 13px; background: transparent;")
            label.setStyleSheet(text_style(tokens["muted"], 12))
        self.refresh_data()

    def _dismiss_day_popup(self) -> None:
        popup = self._day_popup
        self._day_popup = None
        if popup is None:
            return
        try:
            popup.close()
        except RuntimeError:
            pass

    def _handle_day_clicked(self, target_date: QDate, global_pos: QPoint) -> None:
        self.selected_date = target_date
        self.refresh_data()
        self._dismiss_day_popup()
        if self.main_window is not None:
            self.main_window.focus_tasks_for_date(target_date.toPyDate())
        
    def refresh_data(self):
        tokens = self._theme_tokens()
        self.month_lbl.setText(f"{self.current_date.year()}年 {self.current_date.month()}月")
        
        # Clear grid
        for i in reversed(range(self.grid.count())): 
            widget = self.grid.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
                
        # Get tasks
        tasks = self.db.list_tasks()
        tasks_by_date = {}
        for t in tasks:
            if t.due_at:
                d = t.due_at.date()
                if d not in tasks_by_date:
                    tasks_by_date[d] = []
                tasks_by_date[d].append(t)
                
        first_day = QDate(self.current_date.year(), self.current_date.month(), 1)
        day_of_week = first_day.dayOfWeek() # 1 = Monday, 7 = Sunday
        
        days_in_month = self.current_date.daysInMonth()
        
        row = 0
        col = day_of_week - 1
        
        for day in range(1, days_in_month + 1):
            cell = CalendarDayCell(QDate(self.current_date.year(), self.current_date.month(), day))
            cell.setMinimumHeight(100)
            cell.clicked.connect(self._handle_day_clicked)
            cell.setStyleSheet(
                surface_style(
                    rgba(tokens["cell_bg"], 228) if tokens["cell_bg"].startswith("#") else tokens["cell_bg"],
                    10,
                    border="rgba(255,255,255,0)",
                    hover_background=tokens["cell_hover"],
                    hover_border=rgba(tokens["accent"], 96),
                )
            )
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(8, 8, 8, 8)
            cell_layout.setSpacing(4)
            
            date_lbl = QLabel(str(day))
            date_lbl.setStyleSheet(text_style(tokens["text_secondary"], 12, "bold"))
            
            # Check if today
            current_iter_date = QDate(self.current_date.year(), self.current_date.month(), day)
            if current_iter_date == QDate.currentDate():
                date_lbl.setStyleSheet(text_style(tokens["accent"], 12, 800))
                cell.setStyleSheet(surface_style(tokens["accent_soft"], 10, border=rgba(tokens["accent"], 96)))
            if current_iter_date == self.selected_date:
                date_lbl.setStyleSheet(text_style(tokens["text"], 12, 900))
                cell.setStyleSheet(surface_style(rgba(tokens["accent"], 24), 10, border=rgba(tokens["accent"], 120)))
                
            cell_layout.addWidget(date_lbl)
            
            py_date = current_iter_date.toPyDate()
            if py_date in tasks_by_date:
                _today = dt_date.today()
                for i, t in enumerate(tasks_by_date[py_date][:3]): # Show up to 3 tasks
                    t_lbl = QLabel(t.title)
                    # Do not use WordWrap to prevent overlap, use elide text
                    font = t_lbl.font()
                    font.setPointSize(9)
                    t_lbl.setFont(font)
                    fm = t_lbl.fontMetrics()
                    elided_title = fm.elidedText(t.title, Qt.TextElideMode.ElideRight, 100) # approximate width
                    t_lbl.setText(elided_title)
                    t_lbl.setFixedHeight(24)

                    is_overdue = not t.completed and py_date < _today
                    if t.completed:
                        color = tokens["success"]
                    elif is_overdue:
                        color = tokens["danger"]
                    else:
                        color = tokens["accent"]
                    t_lbl.setStyleSheet(f"background: {color}; color: #ffffff; border-radius: 4px; padding: 4px 4px 4px 6px; font-size: 11px; margin-bottom: 2px;")
                    cell_layout.addWidget(t_lbl)
                if len(tasks_by_date[py_date]) > 3:
                    more_lbl = QLabel(f"+{len(tasks_by_date[py_date]) - 3} 更多")
                    more_lbl.setStyleSheet(text_style(tokens["muted"], 11))
                    cell_layout.addWidget(more_lbl)
                    
            cell_layout.addStretch()
            self.grid.addWidget(cell, row, col)
            
            col += 1
            if col > 6:
                col = 0
                row += 1
