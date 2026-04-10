from __future__ import annotations

import sys
import ctypes

from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Optional, cast

from PyQt6.QtCore import QDateTime, QEvent, QPoint, QRect, QSize, QSettings, QTimer, Qt, QUrl
from PyQt6.QtGui import QCloseEvent, QIcon, QAction, QKeyEvent, QKeySequence, QResizeEvent, QShortcut, QColor, QFont, QLinearGradient, QMouseEvent, QPalette, QPainter, QPen, QPixmap, QRadialGradient
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QStyle,
    QSystemTrayIcon,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from DB import DB
from Note import Note
from Task import Task
from runtime_support import load_config, save_config
from ui.icon_manager import IconManager
from ui.hub_view import HubView
from ui.calendar_view import CalendarView
from ui.gantt_view import GanttView
from ui.right_panels import ManagementCenterPanel
from ui.task_detail_dialog import TaskDetailView
from ui.scroll_area import SmartScrollArea
from ui.shortcuts_dialog import ShortcutsDialog
from ui.celestial_theme_catalog import (
    background_path,
    default_background_for_theme,
    get_theme_profile,
    mix_hex,
    scene_palette_for_theme,
    starry_palette_for_theme,
)
from ui.starry_chrome import set_starry_palette
from ui.task_composer import TaskEditorView
from ui.task_export import export_tasks_markdown, export_tasks_csv, export_tasks_json, compute_export_stats
from ui.progress_widgets import CategoryProgressPanel
from ui.theme import SURFACE_BG, SURFACE_BG_LIGHT, SURFACE_BG_ACCENT, SURFACE_BORDER, SURFACE_BORDER_STRONG, SURFACE_TEXT_PRIMARY, SURFACE_TEXT_MUTED, SURFACE_TEXT_SECONDARY, TITLE_FONT_FAMILY, build_app_stylesheet, chip_style, ensure_app_fonts_loaded, rgba, surface_style, text_style, title_text_style
from ui.celebration_overlay import CelebrationOverlay
from ui.reminder_experience import (
    DEFAULT_REMINDER_ANIMATION_ID,
    ReminderOverlay,
    ReminderPromptDialog,
    normalize_reminder_animation_id,
    reminder_animation_label,
    reminder_animation_spec,
)
from core.reminder_sounds import (
    DEFAULT_REMINDER_SOUND_ID,
    normalize_reminder_sound_id,
    reminder_sound_label,
    reminder_sound_path,
)

try:
    import winsound
except ImportError:
    winsound = None


if sys.platform == "win32":
    from ctypes import wintypes

    class _WinPoint(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    class _WinMsg(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("message", wintypes.UINT),
            ("wParam", wintypes.WPARAM),
            ("lParam", wintypes.LPARAM),
            ("time", wintypes.DWORD),
            ("pt", _WinPoint),
        ]

    WM_NCHITTEST = 0x0084
    HTLEFT = 10
    HTRIGHT = 11
    HTTOP = 12
    HTTOPLEFT = 13
    HTTOPRIGHT = 14
    HTBOTTOM = 15
    HTBOTTOMLEFT = 16
    HTBOTTOMRIGHT = 17


PRIORITY_ORDER = {"高": 0, "中": 1, "低": 2}
PRIORITY_COLORS = {"高": "#b91c1c", "中": "#b45309", "低": "#2563eb"}
PRIORITY_BACKGROUNDS = {"高": "#fee2e2", "中": "#fef3c7", "低": "#dbeafe"}
TREE_GROUP_ROLE = 1000
TREE_GROUP_SUBTITLE_ROLE = 1001
TREE_GROUP_ACCENT_ROLE = 1002
TREE_GROUP_LEVEL_ROLE = 1003
TREE_DATE_GROUP_KEY_ROLE = 1004
TREE_STATUS_TEXT_ROLE = 1010
TREE_STATUS_COLOR_ROLE = 1011
TREE_TIMELINE_COLOR_ROLE = 1020


class MetricCard(QFrame):
    def __init__(self, title: str, accent: str) -> None:
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("metricCard")
        self.setProperty("accent", accent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("metricTitle")
        self.value_label = QLabel("0")
        self.value_label.setObjectName("metricValue")
        self.value_label.setProperty("accent", accent)
        self.value_label.setStyleSheet(f"color: {accent};")
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class InfoPill(QFrame):
    def __init__(self, title: str, value: str = "", *, accent: str = "#94a3b8") -> None:
        super().__init__()
        self.setObjectName("infoPill")
        self.setMinimumHeight(124)
        self.setStyleSheet(
            f"QFrame#infoPill {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {rgba(accent, 18)}, stop:1 rgba(12, 18, 30, 210)); border-radius: 20px; border: 1px solid {rgba(accent, 28)}; }}"
            "QFrame#infoPill QLabel { background: transparent; border: none; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(0)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)
        accent_dot = QFrame()
        accent_dot.setFixedSize(8, 8)
        accent_dot.setStyleSheet(f"background: {accent}; border-radius: 4px;")
        self.title_label = QLabel(title)
        self.title_label.setObjectName("infoPillTitle")
        self.title_label.setStyleSheet(text_style("#dfe9f6", 11, 800))
        self.value_label = QLabel(value)
        self.value_label.setObjectName("infoPillValue")
        self.value_label.setStyleSheet(text_style(SURFACE_TEXT_PRIMARY, 24, 800))
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        header_row.addWidget(accent_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        header_row.addWidget(self.title_label, 1)
        layout.addLayout(header_row)
        layout.addStretch(1)
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class SummaryCard(QFrame):
    def __init__(self, title: str, body: str = "", accent: str = "#60a5fa") -> None:
        super().__init__()
        self.setStyleSheet(surface_style(SURFACE_BG, 18, border="rgba(255,255,255,0)"))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {accent};")
        self.body_label = QLabel(body)
        self.body_label.setWordWrap(True)
        self.body_label.setStyleSheet(text_style(SURFACE_TEXT_SECONDARY, 13) + " line-height: 1.6;")
        layout.addWidget(self.title_label)
        layout.addWidget(self.body_label)

    def set_body(self, body: str) -> None:
        self.body_label.setText(body)


class TrendChartWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.series: list[dict[str, int | str]] = []
        self.setMinimumHeight(180)

    def set_series(self, series: list[dict[str, int | str]]) -> None:
        self.series = series
        self.update()

    def paintEvent(self, a0) -> None:
        parent_paint = getattr(super(), "paintEvent", None)
        if callable(parent_paint):
            parent_paint(a0)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(24, 18, -18, -34)
        painter.fillRect(self.rect(), QColor("#141a22"))
        if not self.series:
            painter.setPen(QColor("#7b8aa0"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "暂无统计数据")
            return
        max_value = max(max(int(item["completed"]), int(item["due"])) for item in self.series) or 1
        bar_width = max(16, rect.width() // max(1, len(self.series) * 3))
        spacing = max(10, bar_width)
        x = rect.left()
        baseline = rect.bottom()
        for item in self.series:
            completed = int(item["completed"])
            due = int(item["due"])
            completed_height = int((rect.height() - 20) * completed / max_value)
            due_height = int((rect.height() - 20) * due / max_value)
            painter.fillRect(x, baseline - completed_height, bar_width, completed_height, QColor("#16a34a"))
            painter.fillRect(x + bar_width + 4, baseline - due_height, bar_width, due_height, QColor("#2563eb"))
            painter.setPen(QColor("#8ca0b8"))
            painter.drawText(x - 4, baseline + 18, bar_width * 2 + 8, 16, Qt.AlignmentFlag.AlignCenter, str(item["label"]))
            x += bar_width * 2 + spacing + 4
        painter.setPen(QPen(QColor("#314156"), 1))
        painter.drawLine(rect.left(), baseline, rect.right(), baseline)
        painter.setPen(QColor("#cbd8e6"))
        painter.drawText(12, 14, "完成")
        painter.drawText(64, 14, "到期")
        painter.fillRect(0, 4, 8, 8, QColor("#16a34a"))
        painter.fillRect(52, 4, 8, 8, QColor("#2563eb"))


class TaskTreeWidget(QTreeWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.after_drop: Callable[[], None] | None = None
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def header(self) -> QHeaderView:
        return cast(QHeaderView, super().header())

    def viewport(self) -> QWidget:
        return cast(QWidget, super().viewport())

    def dropEvent(self, event) -> None:
        super().dropEvent(event)
        if callable(self.after_drop):
            self.after_drop()


def apply_elevation(widget: QWidget, *, blur: int = 24, alpha: int = 90, offset_y: int = 8) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, offset_y)
    effect.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(effect)


class CategoryManagerDialog(QDialog):
    def __init__(self, parent: QWidget, db: DB) -> None:
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("分类管理")
        self.resize(360, 320)
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        button_row = QHBoxLayout()
        for text, slot in (("新增", self.add_category), ("重命名", self.rename_category), ("删除", self.delete_category)):
            button = QPushButton(text)
            button.clicked.connect(slot)
            button_row.addWidget(button)
        layout.addLayout(button_row)
        self.refresh_list()

    def refresh_list(self) -> None:
        self.list_widget.clear()
        self.list_widget.addItems(self.db.list_categories())

    def add_category(self) -> None:
        value, ok = QInputDialog.getText(self, "新增分类", "分类名称")
        if ok and value.strip():
            self.db.add_category(value.strip())
            self.refresh_list()

    def rename_category(self) -> None:
        current = self.list_widget.currentItem()
        if current is None:
            return
        value, ok = QInputDialog.getText(self, "重命名分类", "新的分类名称", text=current.text())
        if ok and value.strip():
            self.db.rename_category(current.text(), value.strip())
            self.refresh_list()

    def delete_category(self) -> None:
        current = self.list_widget.currentItem()
        if current is None:
            return
        self.db.delete_category(current.text())
        self.refresh_list()


class FocusTimerWidget(QFrame):
    def __init__(self, on_finished) -> None:
        super().__init__()
        self.setObjectName("focusTimerFrame")
        self.setMinimumHeight(182)
        self.on_finished = on_finished
        self.remaining_seconds = 25 * 60
        self.active_minutes = 25
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Title row
        title_row = QHBoxLayout()
        self.title_icon_label = QLabel("专注")
        self.title_label = QLabel("专注计时")
        title_row.addWidget(self.title_icon_label)
        title_row.addWidget(self.title_label)
        title_row.addStretch()
        layout.addLayout(title_row)
        self.time_label = QLabel("25:00")
        self.time_label.setObjectName("focusTimerLabel")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setMinimumHeight(64)
        layout.addWidget(self.time_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.active_minutes * 60)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setObjectName("focusProgressBar")
        layout.addWidget(self.progress_bar)
        self.mode_box = QComboBox()
        self.mode_box.addItems(["25 分钟", "15 分钟", "5 分钟"])
        self.mode_box.setMinimumHeight(38)
        self.mode_box.currentTextChanged.connect(self._change_mode)
        layout.addWidget(self.mode_box)
        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        self.start_button = QPushButton("开始")
        self.pause_button = QPushButton("暂停")
        self.reset_button = QPushButton("重置")
        for button, slot in (
            (self.start_button, self.start),
            (self.pause_button, self.pause),
            (self.reset_button, self.reset),
        ):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(40)
            button.clicked.connect(slot)
            button_row.addWidget(button)
        layout.addLayout(button_row)
        self.apply_theme()

    def showEvent(self, a0) -> None:
        self.apply_theme()
        super().showEvent(a0)

    def apply_theme(self) -> None:
        main_window = self.window()
        theme_profile = getattr(main_window, "theme_profile", None)
        ui_palette = getattr(main_window, "ui_palette", None)
        accent = getattr(theme_profile, "accent", "#60a5fa")
        accent_alt = getattr(theme_profile, "brass", accent)
        accent_soft = getattr(theme_profile, "accent_soft", rgba(accent, 22))
        border = getattr(ui_palette, "panel_border", rgba(accent, 54))
        text = getattr(ui_palette, "panel_text", "#edf4ff")
        muted = getattr(ui_palette, "panel_muted", "#9fb1c9")
        panel_top = getattr(theme_profile, "panel_top", "#111827")
        panel_bottom = getattr(theme_profile, "panel_bottom", "#0b1220")

        self.setStyleSheet(
            f"QFrame#focusTimerFrame {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {rgba(panel_top, 236)}, stop:1 {rgba(panel_bottom, 224)}); border-radius: 18px; border: 1px solid {rgba(accent, 86)}; }}"
        )
        self.title_icon_label.setStyleSheet(
            f"font-size: 12px; color: {accent}; font-weight: 800; background: transparent; border: none;"
        )
        self.title_label.setStyleSheet(
            f"color: {text}; font-size: 16px; font-weight: 800; background: transparent; border: none;"
        )
        self.time_label.setStyleSheet(
            f"color: {text}; font-size: 40px; font-weight: 900; letter-spacing: 3px; background: transparent; border: none;"
        )
        self.progress_bar.setStyleSheet(
            f"QProgressBar {{ background: {rgba(panel_bottom, 88)}; border-radius: 3px; border: none; }}"
            f"QProgressBar::chunk {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {accent}, stop:1 {accent_alt}); border-radius: 3px; }}"
        )
        self.mode_box.setStyleSheet(
            f"background: {rgba(panel_bottom, 102)}; border: 1px solid {rgba(accent, 72)}; border-radius: 10px; padding: 6px 12px; color: {text};"
        )
        self.start_button.setStyleSheet(
            f"background: {accent_soft}; color: {text}; border-radius: 12px; padding: 10px 16px; font-size: 13px; font-weight: 800; border: 1px solid {rgba(accent, 90)};"
        )
        self.pause_button.setStyleSheet(
            f"background: {rgba(panel_bottom, 70)}; color: {text}; border-radius: 12px; padding: 10px 16px; font-size: 13px; font-weight: 700; border: 1px solid {rgba(border, 100) if border.startswith('#') else border};"
        )
        self.reset_button.setStyleSheet(
            f"background: transparent; color: {muted}; border-radius: 12px; padding: 10px 16px; font-size: 13px; font-weight: 700; border: 1px solid {rgba(accent, 38)};"
        )

    def _change_mode(self) -> None:
        mapping = {"25 分钟": 25, "15 分钟": 15, "5 分钟": 5}
        self.active_minutes = mapping.get(self.mode_box.currentText(), 25)
        self.reset()

    def start(self) -> None:
        if not self.timer.isActive():
            self.timer.start(1000)
            main_window = cast("MainWindow | None", self.window())
            if main_window is not None and main_window.play_white_noise:
                main_window.start_white_noise()

    def pause(self) -> None:
        main_window = cast("MainWindow | None", self.window())
        if main_window is not None and main_window.strict_pomodoro:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "严格模式", "番茄钟严格模式已开启，无法提前终止当前专注周期！\n请坚持到时间结束。")
            return
        self.timer.stop()
        if main_window is not None:
            main_window.stop_white_noise()

    def reset(self) -> None:
        main_window = cast("MainWindow | None", self.window())
        if main_window is not None and main_window.strict_pomodoro and self.timer.isActive():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "严格模式", "番茄钟严格模式已开启，无法重置当前专注周期！\n请坚持到时间结束。")
            return
            
        self.timer.stop()
        if main_window is not None:
            main_window.stop_white_noise()
        self.remaining_seconds = self.active_minutes * 60
        self.progress_bar.setRange(0, self.active_minutes * 60)
        self.progress_bar.setValue(0)
        self._update_text()

    def _tick(self) -> None:
        self.remaining_seconds -= 1
        self._update_text()
        if self.remaining_seconds <= 0:
            self.timer.stop()
            main_window = cast("MainWindow | None", self.window())
            if main_window is not None:
                main_window.stop_white_noise()
            if winsound is not None:
                winsound.MessageBeep(winsound.MB_OK)
            else:
                QApplication.beep()
            self.on_finished(self.active_minutes)
            
            # Show missed reminders after focus session
            self.reset()
            main_win = cast("MainWindow | None", self.window())
            if main_win is not None:
                QTimer.singleShot(1000, main_win.check_reminders)

    def _update_text(self) -> None:
        minutes = max(0, self.remaining_seconds) // 60
        seconds = max(0, self.remaining_seconds) % 60
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")
        elapsed = self.active_minutes * 60 - max(0, self.remaining_seconds)
        self.progress_bar.setValue(elapsed)


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget, settings: QSettings) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("应用设置")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.reminder_interval = QSpinBox()
        self.reminder_interval.setRange(5, 300)
        self.reminder_interval.setSuffix(" 秒")
        self.reminder_interval.setValue(int(self.settings.value("reminder_interval", 15)))
        
        self.auto_backup = QCheckBox("启动时自动备份数据库")
        self.auto_backup.setChecked(self.settings.value("auto_backup", "true") == "true")
        
        form.addRow("提醒轮询间隔", self.reminder_interval)
        form.addRow("数据安全", self.auto_backup)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def payload(self) -> dict[str, Any]:
        return {
            "theme": "深色模式",
            "reminder_interval": self.reminder_interval.value(),
            "auto_backup": "true" if self.auto_backup.isChecked() else "false",
        }


class CloseDecisionDialog(QDialog):
    def __init__(self, parent: QWidget, *, default_behavior: str = "tray") -> None:
        super().__init__(parent)
        self.selected_behavior = default_behavior if default_behavior in {"tray", "exit"} else "tray"
        self.setWindowTitle("关闭 Task Forge")
        self.setModal(True)
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(14)

        title = QLabel("点击关闭按钮时，如何处理当前程序？")
        title.setStyleSheet(text_style(SURFACE_TEXT_PRIMARY, 18, 800))
        title.setWordWrap(True)
        layout.addWidget(title)

        subtitle = QLabel("退到后台后，托盘提醒与定时功能会继续运行；直接退出会彻底关闭软件。")
        subtitle.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 13))
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.remember_choice = QCheckBox("记住本次选择，之后点击右上角 X 直接按此行为执行")
        self.remember_choice.setChecked(False)
        self.remember_choice.setStyleSheet("QCheckBox { spacing: 8px; } QCheckBox::indicator { width: 18px; height: 18px; }")
        layout.addWidget(self.remember_choice)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 4, 0, 0)
        action_row.setSpacing(10)

        self.tray_button = QPushButton("退到后台")
        self.tray_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tray_button.setProperty("role", "secondary")
        self.tray_button.clicked.connect(lambda: self._choose("tray"))

        self.exit_button = QPushButton("直接退出")
        self.exit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exit_button.setProperty("role", "primary")
        self.exit_button.clicked.connect(lambda: self._choose("exit"))

        cancel_button = QPushButton("取消")
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_button.setProperty("role", "ghost")
        cancel_button.clicked.connect(self.reject)

        action_row.addWidget(self.tray_button, 1)
        action_row.addWidget(self.exit_button, 1)
        action_row.addWidget(cancel_button)
        layout.addLayout(action_row)

    def _choose(self, behavior: str) -> None:
        self.selected_behavior = behavior
        self.accept()


class DateFocusDialog(QDialog):
    def __init__(self, parent: QWidget, *, current_date: Optional[date] = None) -> None:
        super().__init__(parent)
        self.result_action = "apply"
        self.setWindowTitle("按日期筛选任务")
        self.setModal(True)
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        title = QLabel("选择一个截止日期")
        title.setStyleSheet(text_style(SURFACE_TEXT_PRIMARY, 17, 800))
        layout.addWidget(title)

        subtitle = QLabel("任务列表会聚焦到对应日期分组，方便按天查看和回顾。")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 13))
        layout.addWidget(subtitle)

        self.date_edit = QDateTimeEdit(self)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        picked = current_date or date.today()
        self.date_edit.setDateTime(QDateTime(picked.year, picked.month, picked.day, 0, 0))
        self.date_edit.setStyleSheet(
            f"QDateTimeEdit {{ background: {rgba('#0f172a', 206)}; border: 1px solid {rgba('#94a3b8', 56)}; border-radius: 14px; padding: 10px 12px; color: {SURFACE_TEXT_PRIMARY}; font-size: 14px; font-weight: 600; }}"
            f"QDateTimeEdit:focus {{ border: 1px solid {rgba('#8ca7d4', 116)}; }}"
        )
        layout.addWidget(self.date_edit)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 2, 0, 0)
        actions.setSpacing(8)

        today_button = QPushButton("今天")
        today_button.setCursor(Qt.CursorShape.PointingHandCursor)
        today_button.clicked.connect(self._pick_today)

        clear_button = QPushButton("清除筛选")
        clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_button.clicked.connect(self._clear)

        apply_button = QPushButton("应用日期")
        apply_button.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_button.setDefault(True)
        apply_button.clicked.connect(self._apply)

        cancel_button = QPushButton("取消")
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_button.clicked.connect(self.reject)

        actions.addWidget(today_button)
        actions.addWidget(clear_button)
        actions.addStretch(1)
        actions.addWidget(cancel_button)
        actions.addWidget(apply_button)
        layout.addLayout(actions)

    def selected_date(self) -> date:
        return self.date_edit.dateTime().toPyDateTime().date()

    def _pick_today(self) -> None:
        today = date.today()
        self.date_edit.setDateTime(QDateTime(today.year, today.month, today.day, 0, 0))

    def _clear(self) -> None:
        self.result_action = "clear"
        self.accept()

    def _apply(self) -> None:
        self.result_action = "apply"
        self.accept()

from ui.task_delegate import TaskItemDelegate
from ui.title_bar import CustomTitleBar
from ui.frameless_window import FramelessResizeMixin
from ui.rich_components import SettingsView
from PyQt6.QtGui import QPainter, QPainterPath

import os
from PyQt6.QtMultimedia import QSoundEffect
from core.audio_engine import generate_white_noise_file

class MainWindow(QMainWindow, FramelessResizeMixin):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        ensure_app_fonts_loaded()
        self.settings = QSettings("TaskForge", "TaskForgeDesktop")
        self._use_frameless_window = False if sys.platform == "win32" else self.settings.value(
            "use_frameless_window",
            True,
            type=bool,
        )
        if self._use_frameless_window:
            self.setup_frameless()
        else:
            self.setAttribute(Qt.WidgetAttribute.WA_Hover)
            self.setMouseTracking(True)
            self._margin = 8
            self._resize_dir = None
            self._start_pos = None
            self._start_geometry = None
        self.visual_config = load_config()
        self.theme_id = str(self.visual_config.get("theme_id") or "orion_blue")
        self.theme_profile = get_theme_profile(self.theme_id)
        self.background_id = str(
            self.visual_config.get("background_id")
            or default_background_for_theme(self.theme_id)
        )
        self.is_dark_mode = True
        self.play_white_noise = self.settings.value("toggle_noise", False, type=bool)
        self.strict_pomodoro = self.settings.value("toggle_strict", False, type=bool)
        self.enable_notifications = self.settings.value("toggle_notify", True, type=bool)
        self.performance_mode = self.settings.value("toggle_perf", False, type=bool)
        self.auto_sync_enabled = self.settings.value("toggle_sync", False, type=bool)
        self.ui_palette = scene_palette_for_theme(self.theme_profile)
        set_starry_palette(starry_palette_for_theme(self.theme_profile))
        self.background_pixmap = QPixmap(str(background_path(self.background_id)))
        self.brand_theme_tag: Optional[QLabel] = None
        self.focus_due_date: Optional[date] = None
        self.tree_date_groups: dict[str, QTreeWidgetItem] = {}
        
        # Audio Setup
        self.noise_player = QSoundEffect()
        noise_path = os.path.join(os.path.dirname(__file__), "assets", "audio", "noise.wav")
        generate_white_noise_file(noise_path)
        self.noise_player.setSource(QUrl.fromLocalFile(noise_path))
        self.noise_player.setLoopCount(-2) # QSoundEffect.Infinite is typically -2
        self.noise_player.setVolume(0.5)
        self.reminder_player = QSoundEffect(self)
        self.reminder_player.setLoopCount(1)
        self.reminder_player.setVolume(0.92)
        self.reminder_sound_id = normalize_reminder_sound_id(
            str(self.settings.value("reminder_sound_id", DEFAULT_REMINDER_SOUND_ID) or DEFAULT_REMINDER_SOUND_ID)
        )
        self.reminder_animation_id = normalize_reminder_animation_id(
            str(self.settings.value("reminder_animation_id", DEFAULT_REMINDER_ANIMATION_ID) or DEFAULT_REMINDER_ANIMATION_ID)
        )
        self._configure_reminder_sound(self.reminder_sound_id, persist=False)

        self.db = DB()
        self.current_note_id: Optional[int] = None
        self.all_tasks: list[Task] = []
        self.task_map: dict[int, Task] = {}
        self.children_map: dict[Optional[int], list[Task]] = defaultdict(list)
        self.tree_items: dict[int, QTreeWidgetItem] = {}
        self._allow_close = False
        self.close_button_behavior = str(self.settings.value("close_button_behavior", "ask") or "ask")
        if self.close_button_behavior not in {"ask", "tray", "exit"}:
            self.close_button_behavior = "ask"
        self._startup_message_sent = False
        self._last_deleted_snapshot: Optional[dict[str, Any]] = None
        self._undo_stack: list[dict[str, Any]] = []
        self._redo_stack: list[dict[str, Any]] = []
        self._browse_history: list[dict[str, Any]] = []
        self._suspend_browse_history = False
        self._pending_tree_check_updates: dict[int, bool] = {}
        self._tree_check_update_queued = False
        self.week_panel: Any | None = None
        self.stats_panel: Any | None = None
        self.current_view_mode = "today"
        self._last_browse_view = "today"
        self._detail_return_mode = "today"
        self._editor_return_mode = "tasktree"
        self._editor_return_task_id: Optional[int] = None

        self.setWindowTitle("Task Forge - 个人任务驾驶舱")
        self.resize(1440, 900)
        self._build_actions()
        self._build_toolbar()
        self._build_window()
        self.apply_runtime_theme()
        self._build_tray()
        self._restore_window_state()
        self._apply_responsive_layout()
        self.celebration_overlay = CelebrationOverlay(self)
        self.celebration_overlay.resize_to_parent()
        self.reminder_overlay = ReminderOverlay(self)
        self.reminder_overlay.resize_to_parent()

        self.reminder_timer = QTimer(self)
        self.reminder_timer.setSingleShot(True)
        self.reminder_timer.timeout.connect(self.check_reminders)
        self._reminder_fallback_interval_ms = 15_000
        self._refresh_reminder_schedule_policy()

        self.switch_view("today")
        self.refresh_everything()

    def start_white_noise(self):
        if self.play_white_noise and not self.noise_player.isPlaying():
            self.noise_player.play()
            
    def stop_white_noise(self):
        if self.noise_player.isPlaying():
            self.noise_player.stop()

    def _refresh_reminder_schedule_policy(self) -> None:
        interval_seconds = max(1, int(self.settings.value("reminder_interval", 15)))
        self._reminder_fallback_interval_ms = max(1_000, interval_seconds * 1_000)

    def _schedule_next_reminder_check(self, *, reference_time: Optional[datetime] = None, force_poll: bool = False) -> None:
        if not hasattr(self, "reminder_timer"):
            return
        self.reminder_timer.stop()
        self._refresh_reminder_schedule_policy()
        if not getattr(self, "enable_notifications", True):
            return
        if force_poll:
            self.reminder_timer.start(self._reminder_fallback_interval_ms)
            return
        next_due = self.db.next_pending_reminder_at()
        if next_due is None:
            self.reminder_timer.start(self._reminder_fallback_interval_ms)
            return
        now = reference_time or datetime.now()
        delay_ms = int((next_due - now).total_seconds() * 1000)
        self.reminder_timer.start(max(50, min(delay_ms, 2_147_483_000)))

    def _configure_reminder_sound(self, sound_id: str, *, persist: bool = True) -> None:
        normalized = normalize_reminder_sound_id(sound_id)
        self.reminder_sound_id = normalized
        sound_path = reminder_sound_path(normalized)
        if sound_path.exists():
            self.reminder_player.setSource(QUrl.fromLocalFile(str(sound_path)))
        if persist:
            self.settings.setValue("reminder_sound_id", normalized)

    def _reminder_sound_path(self) -> Path:
        return reminder_sound_path(self.reminder_sound_id)

    def _ensure_reminder_player_source(self) -> Path:
        sound_path = self._reminder_sound_path()
        if not sound_path.exists():
            return sound_path
        target_source = QUrl.fromLocalFile(str(sound_path))
        if self.reminder_player.source() != target_source:
            self.reminder_player.setSource(target_source)
        return sound_path

    def apply_reminder_sound_choice(self, sound_id: str) -> None:
        self._configure_reminder_sound(sound_id)
        self.statusBar().showMessage(f"提醒铃声已切换为“{reminder_sound_label(self.reminder_sound_id)}”", 3500)
        if hasattr(self, "settings_view"):
            self.settings_view.sync_from_main_window()

    def apply_reminder_animation_choice(self, animation_id: str) -> None:
        self.reminder_animation_id = normalize_reminder_animation_id(animation_id)
        self.settings.setValue("reminder_animation_id", self.reminder_animation_id)
        self.statusBar().showMessage(f"提醒动画已切换为“{reminder_animation_label(self.reminder_animation_id)}”", 3500)
        if hasattr(self, "settings_view"):
            self.settings_view.sync_from_main_window()

    def _play_reminder_sound(self) -> bool:
        sound_path = self._ensure_reminder_player_source()
        if winsound is not None and sound_path.exists():
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
                winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
                return True
            except RuntimeError:
                pass
        if not self.reminder_player.source().isEmpty():
            if self.reminder_player.isPlaying():
                self.reminder_player.stop()
            self.reminder_player.play()
            return True
        if self.reminder_player.source().isEmpty():
            if winsound is not None:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            else:
                QApplication.beep()
            return False
        return False

    def preview_reminder_sound(self) -> None:
        if self._play_reminder_sound():
            self.statusBar().showMessage(f"正在试听“{reminder_sound_label(self.reminder_sound_id)}”", 2500)
            return
        self.statusBar().showMessage("当前提醒铃声不可用，已退回系统提示音", 3000)

    def _show_reminder_overlay(self, *, title: str, subtitle: str) -> None:
        if getattr(self, "reminder_overlay", None) is None:
            return
        self.reminder_overlay.start(
            animation_id=self.reminder_animation_id,
            title=title,
            subtitle=subtitle,
        )

    def preview_reminder_animation(self) -> None:
        animation = reminder_animation_spec(self.reminder_animation_id)
        self._show_reminder_overlay(
            title="提醒动画预览",
            subtitle=f"当前动画：{animation.label}。{animation.subtitle}",
        )
        self.statusBar().showMessage(f"正在预览“{animation.label}”", 2500)

    def preview_reminder_experience(self) -> None:
        sound_label = reminder_sound_label(self.reminder_sound_id)
        animation = reminder_animation_spec(self.reminder_animation_id)
        self._play_reminder_sound()
        self._show_reminder_overlay(
            title="提醒体验预览",
            subtitle=f"当前组合：{sound_label} + {animation.label}。",
        )
        self.statusBar().showMessage(f"正在预览“{sound_label} + {animation.label}”", 2800)

    def _reminder_display_dt(self, task: Task) -> str:
        return self._format_dt(task.remind_at or task.due_at)

    def _reminder_overlay_copy(self, due_tasks: list[Task]) -> tuple[str, str]:
        if not due_tasks:
            return "任务提醒", "你有新的待办提醒。"
        title = "任务提醒" if len(due_tasks) == 1 else f"{len(due_tasks)} 项任务到达提醒时间"
        primary = due_tasks[0]
        primary_line = f"{primary.title}｜提醒时间 {self._reminder_display_dt(primary)}"
        if len(due_tasks) == 1:
            return title, primary_line
        return title, f"{primary_line}，另有 {len(due_tasks) - 1} 项待查看。"

    def _should_show_system_reminder_toast(self) -> bool:
        platform_name = QApplication.platformName().lower()
        if platform_name == "offscreen":
            return False
        return winsound is None

    def _completed_task_ids(self) -> set[int]:
        return {task.id for task in self.all_tasks if task.completed}

    def _maybe_show_completion_celebration(self, before_completed: set[int], *, preferred_task_ids: Optional[list[int]] = None) -> None:
        after_completed = self._completed_task_ids()
        new_completed_ids = list(after_completed - before_completed)
        if not new_completed_ids:
            return
        ordered_ids = preferred_task_ids or new_completed_ids
        primary_task = next((self.task_map.get(task_id) for task_id in ordered_ids if task_id in after_completed), None)
        if primary_task is None:
            primary_task = next((self.task_map.get(task_id) for task_id in new_completed_ids), None)
        task_title = primary_task.title if primary_task is not None and len(new_completed_ids) == 1 else ""
        self.celebration_overlay.start(completed_count=len(new_completed_ids), task_title=task_title)
        self.statusBar().showMessage(f"已完成 {len(new_completed_ids)} 项任务，继续保持节奏", 4200)

    def apply_runtime_setting(self, action: str, checked: bool) -> None:
        if action == "toggle_sync":
            self.auto_sync_enabled = checked
            self.settings.setValue("toggle_sync", checked)
            self.statusBar().showMessage("自动同步已开启" if checked else "自动同步已关闭", 3000)
            if checked:
                self._trigger_auto_sync()
        elif action == "toggle_noise":
            self.play_white_noise = checked
            self.settings.setValue("toggle_noise", checked)
            if not checked:
                self.stop_white_noise()
        elif action == "toggle_strict":
            self.strict_pomodoro = checked
            self.settings.setValue("toggle_strict", checked)
        elif action == "toggle_notify":
            self.enable_notifications = checked
            self.settings.setValue("toggle_notify", checked)
            self.statusBar().showMessage("任务提醒已开启" if checked else "任务提醒已关闭", 3000)
            self._schedule_next_reminder_check()
        elif action == "toggle_perf":
            self.performance_mode = checked
            self.settings.setValue("toggle_perf", checked)
            self.apply_runtime_theme()
            self.refresh_everything(self.selected_task_id())
        if hasattr(self, "settings_view"):
            self.settings_view.sync_from_main_window()

    def statusBar(self) -> QStatusBar:
        return cast(QStatusBar, super().statusBar())

    def menuBar(self) -> QMenuBar:
        return cast(QMenuBar, super().menuBar())

    def style(self) -> QStyle:
        return cast(QStyle, super().style())

    def apply_runtime_theme(self) -> None:
        self.ui_palette = scene_palette_for_theme(self.theme_profile)
        set_starry_palette(starry_palette_for_theme(self.theme_profile))
        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.setStyleSheet(build_app_stylesheet(self.is_dark_mode, self.ui_palette))
        panel_bg = self.ui_palette.panel_bg
        panel_fg = self.ui_palette.panel_text
        muted_fg = self.ui_palette.panel_muted
        border = self.ui_palette.panel_border
        input_bg = self.ui_palette.input_bg
        input_fg = self.ui_palette.input_text
        self._runtime_stylesheet = f"""
        #sidebarPanel {{
            background: {panel_bg};
            border-right: 1px solid {border};
        }}
        #mainTitle {{
            color: {panel_fg};
        }}
        #mainSubtitle {{
            color: {self.ui_palette.panel_text_soft};
        }}
        QGroupBox, QGroupBox::title {{
            color: {muted_fg};
        }}
        #sidebarStatsHint {{
            color: {self.ui_palette.panel_text_soft};
        }}
        QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTextEdit, QListWidget, QTreeWidget {{
            color: {input_fg};
            background: {input_bg};
            border: 1px solid {self.ui_palette.input_border};
            border-radius: 12px;
            font-size: 14px;
            selection-background-color: {self.ui_palette.selection_bg};
        }}
        """
        self.setStyleSheet(self._runtime_stylesheet)
        if getattr(self, "task_editor_view", None) is not None:
            self.task_editor_view.page_shell.set_backdrop_pixmap(self.background_pixmap)
            self.task_editor_view.apply_theme()
        if getattr(self, "task_detail_view", None) is not None:
            self.task_detail_view.page_shell.set_backdrop_pixmap(self.background_pixmap)
            self.task_detail_view.apply_theme()
        if getattr(self, "title_bar", None) is not None:
            self.title_bar.apply_theme()
        if hasattr(self, "quick_add_input"):
            self.quick_add_input.setStyleSheet(
                f"background: {input_bg}; border: 1px solid {self.ui_palette.input_border}; border-radius: 14px; padding: 12px 16px; font-size: 15px; color: {input_fg}; margin-bottom: 12px;"
            )
        if hasattr(self, "note_title_edit"):
            self.note_title_edit.setStyleSheet(
                f"font-size: 20px; font-weight: bold; font-family: {TITLE_FONT_FAMILY}; border: none; background: transparent; padding: 4px 0; color: {panel_fg};"
            )
        if hasattr(self, "board_title"):
            self.board_title.setStyleSheet(title_text_style(panel_fg, 28, "bold"))
        if hasattr(self, "board_subtitle"):
            self.board_subtitle.setStyleSheet(text_style(self.ui_palette.panel_text_soft, 14, 600))
        if hasattr(self, "empty_text_label"):
            self.empty_text_label.setStyleSheet(text_style(self.ui_palette.panel_text_soft, 16, 600))
        self._apply_inline_theme_styles()
        if hasattr(self, "hub_view"):
            self.hub_view.apply_theme()
        if hasattr(self, "calendar_view"):
            self.calendar_view.apply_theme()
        if hasattr(self, "focus_timer"):
            self.focus_timer.apply_theme()
        if hasattr(self, "tree"):
            self.tree.viewport().update()

    def _sidebar_tabs_stylesheet(self) -> str:
        return (
            "QTabWidget#sidebarBottomTabs::pane { border: none; background: transparent; }"
            f"QTabBar::tab {{ background: {rgba(self.theme_profile.sky_bottom, 64)}; border: 1px solid {rgba(self.theme_profile.panel_edge, 52)};"
            f" border-radius: 6px; color: {self.ui_palette.panel_muted}; font-size: 11px; font-weight: 700;"
            " padding: 4px 10px; margin: 0 2px 4px 0; }"
            f"QTabBar::tab:selected {{ background: {self.theme_profile.accent_soft}; color: {self.ui_palette.panel_text};"
            f" border-color: {rgba(self.theme_profile.accent, 96)}; }}"
        )

    def _view_card_style(self, *, active: bool) -> str:
        if active:
            background = (
                "qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                f"stop:0 {rgba(self.theme_profile.accent, 58)}, stop:0.62 {rgba(self.theme_profile.sky_bottom, 178)}, stop:1 {rgba(self.theme_profile.sky_bottom, 196)})"
            )
            border = rgba(self.theme_profile.accent, 112)
            hover_background = (
                "qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                f"stop:0 {rgba(self.theme_profile.accent, 72)}, stop:0.62 {rgba(self.theme_profile.sky_bottom, 190)}, stop:1 {rgba(self.theme_profile.sky_bottom, 208)})"
            )
        else:
            background = rgba(self.theme_profile.sky_bottom, 92)
            border = rgba(self.theme_profile.accent, 20)
            hover_background = rgba(self.theme_profile.accent, 16)
        return (
            f"QPushButton#viewCard {{ background: {background}; border: 1px solid {border}; border-radius: 16px; padding: 0; }}"
            f"QPushButton#viewCard:hover {{ background: {hover_background}; border: 1px solid {rgba(self.theme_profile.accent, 72 if active else 44)}; }}"
        )

    def _view_count_style(self, *, active: bool) -> str:
        if active:
            return (
                f"background: {rgba(self.theme_profile.accent, 18)}; border: 1px solid {rgba(self.theme_profile.accent, 42)}; border-radius: 10px; padding: 2px 8px; "
                f"color: {self.ui_palette.panel_text}; font-size: 11px; font-weight: 800;"
            )
        return (
            f"background: {rgba(self.theme_profile.sky_bottom, 104)}; border: 1px solid {rgba(self.theme_profile.accent, 18)}; border-radius: 10px; padding: 2px 8px; "
            f"color: {self.ui_palette.panel_text_soft}; font-size: 11px; font-weight: 700;"
        )

    def _tree_scope_button_style(self) -> str:
        return (
            f"QPushButton {{ background: {rgba(self.theme_profile.sky_bottom, 72)}; border: none; border-radius: 12px; padding: 8px 14px; color: {self.ui_palette.panel_muted}; font-size: 12px; font-weight: 700; }}"
            f"QPushButton:hover {{ background: {rgba(self.theme_profile.accent, 24)}; color: {self.ui_palette.panel_text}; }}"
            f"QPushButton:checked {{ background: {self.theme_profile.accent_soft}; color: {self.ui_palette.panel_text}; }}"
        )

    def _tree_combo_style(self) -> str:
        return (
            f"QComboBox {{ background: {rgba(self.theme_profile.sky_bottom, 116)}; border: 1px solid {rgba(self.theme_profile.accent, 40)}; "
            f"border-radius: 12px; padding: 7px 10px; color: {self.ui_palette.panel_text}; font-size: 13px; }}"
            "QComboBox::drop-down { width: 24px; border: none; }"
            f"QComboBox::down-arrow {{ width: 0; height: 0; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid {rgba(self.theme_profile.accent, 180)}; margin-right: 6px; }}"
            f"QComboBox QAbstractItemView {{ background: {self.theme_profile.panel_top}; border: none; "
            f"color: {self.ui_palette.panel_text}; selection-background-color: {self.ui_palette.selection_bg}; padding: 4px; }}"
        )

    def _filter_action_button_style(self, *, active: bool = False) -> str:
        background = self.theme_profile.accent_soft if active else rgba(self.theme_profile.sky_bottom, 110)
        border = rgba(self.theme_profile.accent, 96 if active else 42)
        hover_background = rgba(self.theme_profile.accent, 28 if active else 18)
        return (
            f"QPushButton {{ background: {background}; border: 1px solid {border}; border-radius: 12px; padding: 7px 12px; color: {self.ui_palette.panel_text}; font-size: 13px; font-weight: 700; }}"
            f"QPushButton:hover {{ background: {hover_background}; border: 1px solid {rgba(self.theme_profile.accent, 112)}; }}"
            f"QPushButton:disabled {{ background: {rgba(self.theme_profile.sky_bottom, 80)}; border: 1px solid {rgba(self.theme_profile.accent, 24)}; color: {self.ui_palette.panel_muted}; }}"
        )

    def _format_focus_due_date(self, target_date: date) -> str:
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return f"{target_date:%m月%d日} {weekdays[target_date.weekday()]}"

    def _update_date_focus_chip(self) -> None:
        if not getattr(self, "date_focus_chip", None):
            return
        if self.focus_due_date is None:
            self.date_focus_chip.hide()
            self._apply_filter_action_styles()
            return
        self.date_focus_chip.setText(f"日期：{self._format_focus_due_date(self.focus_due_date)}  清除筛选")
        self.date_focus_chip.show()
        self._apply_filter_action_styles()

    def _apply_filter_action_styles(self) -> None:
        if getattr(self, "history_back_button", None) is not None:
            self.history_back_button.setStyleSheet(self._filter_action_button_style())
        if getattr(self, "date_picker_button", None) is not None:
            self.date_picker_button.setStyleSheet(self._filter_action_button_style(active=self.focus_due_date is not None))

    def _apply_view_card_states(self) -> None:
        if not hasattr(self, "view_cards"):
            return
        mode = getattr(self, "current_view_mode", "today")
        for key, card_data in self.view_cards.items():
            btn, count_lbl, icon_lbl, icon_name = card_data
            title_lbl = btn.findChild(QLabel, "viewCardTitle")
            is_active = key == mode
            btn.setProperty("role", "ghost")
            btn.setStyleSheet(self._view_card_style(active=is_active))
            icon_color = self.theme_profile.accent if is_active else self.ui_palette.icon_color
            icon_lbl.setPixmap(IconManager().get_pixmap(icon_name, size=20 if is_active else 18, color=icon_color))
            if title_lbl:
                title_lbl.setStyleSheet(
                    text_style(self.ui_palette.view_active_text if is_active else self.ui_palette.panel_text_soft, 14 if is_active else 13, "bold" if is_active else 600)
                    + " padding-left: 4px;"
                )
            if count_lbl.isVisible():
                count_lbl.setStyleSheet(self._view_count_style(active=is_active))
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _apply_inline_theme_styles(self) -> None:
        if getattr(self, "sidebar_brand_box", None) is not None:
            self.sidebar_brand_box.setStyleSheet(
                f"QFrame#sidebarBrandBox {{ background: {self.ui_palette.titlebar_surface}; border-radius: 20px; border: 1px solid {self.ui_palette.panel_border}; }}"
                "QLabel { background: transparent; border: none; }"
            )
        if getattr(self, "sidebar_brand_title", None) is not None:
            self.sidebar_brand_title.setStyleSheet(text_style(self.ui_palette.panel_text, 15, 800))
        if getattr(self, "sidebar_brand_subtitle", None) is not None:
            self.sidebar_brand_subtitle.setStyleSheet(text_style(self.ui_palette.panel_text_soft, 10, 600))
        if self.brand_theme_tag is not None:
            self.brand_theme_tag.setText(self.theme_profile.name)
            self.brand_theme_tag.setStyleSheet(
                f"color: {self.ui_palette.panel_text}; background: {self.ui_palette.theme_tag_bg}; border-radius: 10px; padding: 4px 9px; font-size: 12px; font-weight: 700; border: 1px solid {self.ui_palette.theme_tag_border};"
            )
        if getattr(self, "sidebar_bottom_tabs", None) is not None:
            self.sidebar_bottom_tabs.setStyleSheet(self._sidebar_tabs_stylesheet())
        if getattr(self, "tree_scope_hint", None) is not None:
            self.tree_scope_hint.setStyleSheet(text_style(self.ui_palette.panel_muted, 12, 700))
        if hasattr(self, "tree_scope_summary"):
            self.tree_scope_summary.setStyleSheet(text_style(self.ui_palette.panel_muted, 12, 600))
        for button in getattr(self, "tree_scope_buttons", {}).values():
            button.setStyleSheet(self._tree_scope_button_style())
        if getattr(self, "tree_add_button", None) is not None:
            self.tree_add_button.setStyleSheet(self._filter_action_button_style())
        if getattr(self, "tree_toggle_button", None) is not None:
            self.tree_toggle_button.setStyleSheet(self._filter_action_button_style())
        if getattr(self, "tree_delete_button", None) is not None:
            self.tree_delete_button.setStyleSheet(self._filter_action_button_style())
        if getattr(self, "search_icon_label", None) is not None:
            self.search_icon_label.setPixmap(IconManager().get_pixmap("search", size=16, color=self.ui_palette.icon_color))
        if hasattr(self, "category_filter"):
            self.category_filter.setStyleSheet(self._tree_combo_style())
        if hasattr(self, "tag_filter"):
            self.tag_filter.setStyleSheet(self._tree_combo_style())
        self._apply_filter_action_styles()
        if getattr(self, "date_focus_chip", None) is not None:
            self.date_focus_chip.setStyleSheet(
                chip_style(
                    text_color=self.ui_palette.panel_text,
                    background=self.theme_profile.accent_soft,
                    border=rgba(self.theme_profile.accent, 88),
                    radius=12,
                    padding="6px 12px",
                )
            )
        if getattr(self, "tree_inline_empty", None) is not None:
            self.tree_inline_empty.setStyleSheet(
                surface_style(
                    rgba(self.theme_profile.sky_bottom, 118),
                    18,
                    border=rgba(self.theme_profile.accent, 36),
                    selector="QFrame#treeInlineEmpty",
                )
            )
            self.tree_inline_empty_title.setStyleSheet(text_style(self.ui_palette.panel_text, 18, 800))
            self.tree_inline_empty_subtitle.setStyleSheet(text_style(self.ui_palette.panel_text_soft, 13, 600))
        self._apply_sidebar_create_styles()
        self._update_date_focus_chip()
        self._apply_view_card_states()
        self._update_browse_back_button()

    def _apply_sidebar_create_styles(self) -> None:
        if getattr(self, "sidebar_create_card", None) is not None:
            self.sidebar_create_card.setStyleSheet(
                surface_style(
                    rgba(self.theme_profile.sky_bottom, 124),
                    18,
                    border=rgba(self.theme_profile.accent, 42),
                    selector="QFrame#sidebarCreateCard",
                    hover_background=rgba(self.theme_profile.sky_bottom, 152),
                    hover_border=rgba(self.theme_profile.accent, 68),
                )
            )
        if getattr(self, "sidebar_create_title", None) is not None:
            self.sidebar_create_title.setStyleSheet(text_style(self.ui_palette.panel_text, 15, 800))
        if getattr(self, "sidebar_create_subtitle", None) is not None:
            self.sidebar_create_subtitle.setStyleSheet(text_style(self.ui_palette.panel_text_soft, 12, 600))
        if getattr(self, "sidebar_task_input", None) is not None:
            self.sidebar_task_input.setStyleSheet(
                f"background: {self.ui_palette.input_bg}; border: 1px solid {self.ui_palette.input_border}; border-radius: 12px; padding: 10px 12px; font-size: 13px; color: {self.ui_palette.input_text};"
            )
        active_preset = getattr(self, "sidebar_due_preset", "none")
        for preset, button in getattr(self, "sidebar_due_buttons", {}).items():
            is_active = preset == active_preset
            button.setStyleSheet(
                f"QPushButton {{ background: {self.theme_profile.accent_soft if is_active else rgba(self.theme_profile.sky_bottom, 86)}; border: 1px solid {rgba(self.theme_profile.accent, 84) if is_active else rgba(self.ui_palette.panel_border, 100) if self.ui_palette.panel_border.startswith('#') else self.ui_palette.panel_border}; border-radius: 11px; padding: 7px 10px; color: {self.ui_palette.panel_text if is_active else self.ui_palette.panel_muted}; font-size: 12px; font-weight: 700; }}"
                f"QPushButton:hover {{ color: {self.ui_palette.panel_text}; border-color: {rgba(self.theme_profile.accent, 92)}; }}"
            )

    def _set_sidebar_due_preset(self, preset: str) -> None:
        self.sidebar_due_preset = preset
        for key, button in getattr(self, "sidebar_due_buttons", {}).items():
            button.blockSignals(True)
            button.setChecked(key == preset)
            button.blockSignals(False)
        self._apply_sidebar_create_styles()

    def _quick_create_due_at(self) -> Optional[datetime]:
        preset = getattr(self, "sidebar_due_preset", "none")
        if preset == "none":
            return None
        target = datetime.now().replace(second=0, microsecond=0)
        if preset == "tomorrow":
            target = target + timedelta(days=1)
        return target.replace(hour=23, minute=59)

    def _quick_create_category(self) -> str:
        if hasattr(self, "category_filter"):
            current = self.category_filter.currentText().strip()
            if current and not current.startswith("📁"):
                return current
        if getattr(self, "sidebar_due_preset", "none") == "today" or getattr(self, "current_view_mode", "") == "today":
            return "今日"
        return "无分类"

    def _reset_sidebar_create_form(self) -> None:
        if getattr(self, "sidebar_task_input", None) is not None:
            self.sidebar_task_input.clear()
        self._set_sidebar_due_preset("none")

    def focus_tasks_for_date(self, target_date: date, *, task_id: Optional[int] = None) -> None:
        self._push_browse_history()
        self.focus_due_date = target_date
        self._update_date_focus_chip()
        self.switch_view("tasktree")
        if task_id is not None:
            self._refresh_tree(task_id)
        self.statusBar().showMessage(f"已定位到 {self._format_focus_due_date(target_date)} 的任务分组", 3000)

    def clear_date_focus(self) -> None:
        if self.focus_due_date is None:
            return
        self._push_browse_history()
        self.focus_due_date = None
        self._update_date_focus_chip()
        if self.current_view_mode in {"today", "plan", "completed", "tasktree"}:
            self.switch_view(self.current_view_mode)

    def _capture_browse_state(self) -> dict[str, object]:
        browse_modes = {"today", "plan", "tasktree", "calendar", "completed", "hub", "gantt", "settings"}
        mode = getattr(self, "current_view_mode", "today")
        if mode not in browse_modes:
            mode = getattr(self, "_last_browse_view", "today")
        return {"mode": mode, "focus_due_date": self.focus_due_date}

    @staticmethod
    def _browse_state_equals(left: dict[str, object], right: dict[str, object]) -> bool:
        return left.get("mode") == right.get("mode") and left.get("focus_due_date") == right.get("focus_due_date")

    def _push_browse_history(self) -> None:
        if self._suspend_browse_history:
            return
        snapshot = self._capture_browse_state()
        if self._browse_history and self._browse_state_equals(self._browse_history[-1], snapshot):
            return
        self._browse_history.append(snapshot)
        if len(self._browse_history) > 40:
            self._browse_history.pop(0)
        self._update_browse_back_button()

    def _update_browse_back_button(self) -> None:
        if getattr(self, "history_back_button", None) is None:
            return
        enabled = bool(self._browse_history)
        self.history_back_button.setEnabled(enabled)
        if enabled:
            previous = self._browse_history[-1]
            self.history_back_button.setToolTip(f"返回{self._view_title_for_mode(str(previous.get('mode') or 'today'))}")
        else:
            self.history_back_button.setToolTip("当前没有更早的浏览记录")

    def navigate_back(self) -> None:
        current = self._capture_browse_state()
        while self._browse_history:
            snapshot = self._browse_history.pop()
            if self._browse_state_equals(snapshot, current):
                continue
            self._suspend_browse_history = True
            try:
                focus_value = snapshot.get("focus_due_date")
                self.focus_due_date = focus_value if isinstance(focus_value, date) else None
                self._update_date_focus_chip()
                target_mode = str(snapshot.get("mode") or "today")
                self.switch_view(target_mode)
            finally:
                self._suspend_browse_history = False
            self._update_browse_back_button()
            self.statusBar().showMessage(f"已返回{self._view_title_for_mode(target_mode)}", 3000)
            return
        self._update_browse_back_button()
        self.statusBar().showMessage("没有更早的浏览记录", 3000)

    def _open_date_focus_dialog(self) -> None:
        dialog = DateFocusDialog(self, current_date=self.focus_due_date)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if dialog.result_action == "clear":
            self.clear_date_focus()
            return
        self.focus_tasks_for_date(dialog.selected_date())

    def _close_to_tray(self, *, show_message: bool = True) -> None:
        self.hide()
        if show_message:
            self.tray.showMessage(
                "Task Forge",
                "程序已退到后台，提醒与专注计时会继续运行。",
                QSystemTrayIcon.MessageIcon.Information,
                5000,
            )

    def _resolve_close_behavior(self) -> Optional[str]:
        if QApplication.platformName().lower() == "offscreen":
            return "exit"
        if self.close_button_behavior in {"tray", "exit"}:
            return self.close_button_behavior
        dialog = CloseDecisionDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        behavior = dialog.selected_behavior
        if dialog.remember_choice.isChecked():
            self.close_button_behavior = behavior
            self.settings.setValue("close_button_behavior", behavior)
        else:
            self.close_button_behavior = "ask"
            self.settings.setValue("close_button_behavior", "ask")
        return behavior

    def apply_theme_selection(self, theme_id: str, background_id: str) -> None:
        new_theme = get_theme_profile(theme_id)
        self.theme_profile = new_theme
        self.theme_id = new_theme.id
        self.background_id = background_id or default_background_for_theme(new_theme.id)
        self.background_pixmap = QPixmap(str(background_path(self.background_id)))
        self.visual_config = save_config({"theme_id": self.theme_id, "background_id": self.background_id})
        self.apply_runtime_theme()
        self.update()
        if hasattr(self, "settings_view"):
            self.settings_view.sync_from_main_window()
        self.statusBar().showMessage(f"视觉主题已切换为 {self.theme_profile.name}", 3000)

    def _trigger_auto_sync(self) -> None:
        export_path = self.db._data_dir / "auto_sync_snapshot.json"
        self.db.export_data(export_path)
        self.statusBar().showMessage(f"已同步本地快照：{export_path.name}", 4000)

    def _on_splitter_moved(self, pos: int, index: int) -> None:
        pass

    def _apply_responsive_layout(self) -> None:
        if not hasattr(self, "main_splitter") or not hasattr(self, "left_panel"):
            return
        width = max(self.width(), self.minimumWidth())
        if width < 1120:
            left_width = 248
            compact_title = True
        elif width < 1440:
            left_width = 280
            compact_title = False
        elif width < 1680:
            left_width = 308
            compact_title = False
        else:
            left_width = 340
            compact_title = False
        self.left_panel.setMinimumWidth(left_width)
        self.left_panel.setMaximumWidth(left_width)
        middle_width = max(420, width - left_width - 48)
        self.main_splitter.setSizes([left_width, middle_width])
        if getattr(self, "title_bar", None) is not None:
            self.title_bar.set_compact(compact_title)

    def _build_actions(self) -> None:
        self.new_root_action = QAction("新建任务", self)
        self.new_root_action.triggered.connect(self.add_root_task)
        self.new_root_action.setShortcut(QKeySequence("Ctrl+N"))
        self.new_child_action = QAction("新建子任务", self)
        self.new_child_action.triggered.connect(self.add_subtask)
        self.new_child_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        self.edit_action = QAction("编辑任务", self)
        self.edit_action.triggered.connect(self.edit_selected_task)
        self.edit_action.setShortcut(QKeySequence("Ctrl+E"))
        self.toggle_action = QAction("切换完成", self)
        self.toggle_action.triggered.connect(self.toggle_selected_task)
        self.toggle_action.setShortcut(QKeySequence("Space"))
        self.delete_action = QAction("删除任务", self)
        self.delete_action.triggered.connect(self.delete_selected_task)
        self.delete_action.setShortcut(QKeySequence("Delete"))
        self.undo_action = QAction("撤销", self)
        self.undo_action.triggered.connect(self.undo)
        self.undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        self.redo_action = QAction("重做", self)
        self.redo_action.triggered.connect(self.redo)
        self.redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        self.export_action = QAction("导出数据", self)
        self.export_action.triggered.connect(self.export_data)
        self.export_csv_action = QAction("导出CSV", self)
        self.export_csv_action.triggered.connect(self.export_csv)
        self.export_week_report_action = QAction("导出周报", self)
        self.export_week_report_action.triggered.connect(self.export_week_report)
        self.settings_action = QAction("设置", self)
        self.settings_action.triggered.connect(self.show_settings_dialog)
        self.settings_action.setShortcut(QKeySequence("Ctrl+,"))
        self.import_action = QAction("导入数据", self)
        self.import_action.triggered.connect(self.import_data)
        self.postpone_action = QAction("提醒延后 10 分钟", self)
        self.postpone_action.triggered.connect(self.postpone_selected_reminder)
        self.batch_priority_action = QAction("批量设置优先级", self)
        self.batch_priority_action.triggered.connect(self.batch_set_priority)
        self.category_manager_action = QAction("分类管理", self)
        self.category_manager_action.triggered.connect(self.open_category_manager)
        self.search_action = QAction("聚焦搜索", self)
        self.search_action.triggered.connect(lambda: self.search_edit.setFocus())
        self.search_action.setShortcut(QKeySequence("Ctrl+F"))
        self.exit_action = QAction("退出", self)
        self.exit_action.triggered.connect(self.exit_application)
        self.exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        # Shortcuts reference dialog
        self.shortcuts_action = QAction("键盘快捷键参考", self)
        self.shortcuts_action.triggered.connect(self._show_shortcuts_dialog)
        self.shortcuts_action.setShortcut(QKeySequence("Ctrl+/"))
        self.addAction(self.shortcuts_action)
        # Structured export actions
        self.export_markdown_action = QAction("导出为 Markdown", self)
        self.export_markdown_action.triggered.connect(self._export_markdown)
        self.export_markdown_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        self.addAction(self.export_markdown_action)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("操作栏", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        self.command_toolbar = toolbar
        toolbar.hide()
        self.addAction(self.search_action)
        self.addAction(self.undo_action)
        self.addAction(self.redo_action)
        for action in (
            self.new_root_action,
            self.new_child_action,
            self.edit_action,
            self.toggle_action,
            self.undo_action,
            self.redo_action,
            self.batch_priority_action,
            self.postpone_action,
            self.delete_action,
            self.export_action,
            self.export_csv_action,
            self.export_week_report_action,
            self.settings_action,
            self.import_action,
        ):
            toolbar.addAction(action)

        # No longer need this pass

    def _get_resize_direction(self, pos: QPoint):
        x = pos.x()
        y = pos.y()
        w = self.width()
        h = self.height()
        m = self._margin
        
        dir_x = 0 # -1 left, 1 right
        dir_y = 0 # -1 top, 1 bottom
        
        if x < m: dir_x = -1
        elif x > w - m: dir_x = 1
        
        if y < m: dir_y = -1
        elif y > h - m: dir_y = 1
        
        return dir_x, dir_y

    def _set_cursor_shape(self, dir_x, dir_y):
        if dir_x == 0 and dir_y == 0:
            if self.cursor().shape() != Qt.CursorShape.ArrowCursor:
                self.setCursor(Qt.CursorShape.ArrowCursor)
        elif dir_x == -1 and dir_y == -1:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif dir_x == 1 and dir_y == 1:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif dir_x == 1 and dir_y == -1:
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif dir_x == -1 and dir_y == 1:
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif dir_x != 0:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif dir_y != 0:
            self.setCursor(Qt.CursorShape.SizeVerCursor)

    def mousePressEvent(self, a0: QMouseEvent | None):
        if a0 is None:
            return
        if not self._use_frameless_window:
            super().mousePressEvent(a0)
            return
        if self.isMaximized() or self.isFullScreen():
            self._resize_dir = None
            super().mousePressEvent(a0)
            return
        if a0.button() == Qt.MouseButton.LeftButton:
            dir_x, dir_y = self._get_resize_direction(a0.pos())
            if dir_x != 0 or dir_y != 0:
                self._resize_dir = (dir_x, dir_y)
                self._start_pos = a0.globalPosition().toPoint()
                self._start_geometry = self.geometry()
            else:
                super().mousePressEvent(a0)
        else:
            super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0: QMouseEvent | None):
        if a0 is None:
            return
        if not self._use_frameless_window:
            super().mouseMoveEvent(a0)
            return
        if (self.isMaximized() or self.isFullScreen()) and self._resize_dir is None:
            self._set_cursor_shape(0, 0)
            super().mouseMoveEvent(a0)
            return
        if self._resize_dir is not None and self._start_pos is not None and self._start_geometry is not None:
            delta = a0.globalPosition().toPoint() - self._start_pos
            rect = QRect(self._start_geometry)
            
            dir_x, dir_y = self._resize_dir
            if dir_x == -1:
                rect.setLeft(rect.left() + delta.x())
            elif dir_x == 1:
                rect.setRight(rect.right() + delta.x())
                
            if dir_y == -1:
                rect.setTop(rect.top() + delta.y())
            elif dir_y == 1:
                rect.setBottom(rect.bottom() + delta.y())
                
            self.setGeometry(rect)
        else:
            dir_x, dir_y = self._get_resize_direction(a0.pos())
            self._set_cursor_shape(dir_x, dir_y)
            super().mouseMoveEvent(a0)

    def mouseReleaseEvent(self, a0: QMouseEvent | None):
        if a0 is None:
            return
        if not self._use_frameless_window:
            super().mouseReleaseEvent(a0)
            return
        self._resize_dir = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(a0)

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        if a0 is None:
            return
        super().resizeEvent(a0)
        if getattr(self, "celebration_overlay", None) is not None:
            self.celebration_overlay.resize_to_parent()
        if getattr(self, "reminder_overlay", None) is not None:
            self.reminder_overlay.resize_to_parent()
        self._apply_responsive_layout()

    def changeEvent(self, event: QEvent | None) -> None:
        super().changeEvent(event)
        if event is not None and event.type() == QEvent.Type.WindowStateChange:
            if self._use_frameless_window and self.isMaximized():
                screen = QApplication.screenAt(self.pos()) or QApplication.primaryScreen()
                if screen is not None:
                    QTimer.singleShot(0, lambda: self._apply_maximized_geometry(screen.availableGeometry()))
            if getattr(self, "title_bar", None) is not None:
                self.title_bar.apply_theme()

    def _apply_maximized_geometry(self, available_geometry: QRect) -> None:
        # Avoid stale queued callbacks forcing a normal window into full-size geometry.
        if self.isMaximized():
            self.setGeometry(available_geometry)

    def nativeEvent(self, eventType, message):
        # Returning `(False, 0)` lets Qt perform default processing and avoids
        # platform-specific crashes observed with superclass/native pointer paths.
        return False, 0

    def paintEvent(self, a0):
        parent_paint = getattr(super(), "paintEvent", None)
        if callable(parent_paint):
            parent_paint(a0)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if hasattr(self, "background_pixmap") and isinstance(self.background_pixmap, QPixmap) and not self.background_pixmap.isNull():
            scaled = self.background_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            offset_x = (scaled.width() - self.width()) // 2
            offset_y = (scaled.height() - self.height()) // 2
            painter.drawPixmap(-offset_x, -offset_y, scaled)
        else:
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0.0, QColor(self.theme_profile.sky_top))
            gradient.setColorAt(0.5, QColor(self.theme_profile.sky_mid))
            gradient.setColorAt(1.0, QColor(self.theme_profile.sky_bottom))
            painter.fillRect(self.rect(), gradient)

        overlay = QLinearGradient(0, 0, 0, self.height())
        top_overlay = QColor(self.theme_profile.window_overlay_top)
        top_overlay.setAlpha(188)
        mid_overlay = QColor(self.theme_profile.window_overlay_bottom)
        mid_overlay.setAlpha(172)
        bottom_overlay = QColor(self.theme_profile.window_overlay_top)
        bottom_overlay.setAlpha(214)
        overlay.setColorAt(0.0, top_overlay)
        overlay.setColorAt(0.58, mid_overlay)
        overlay.setColorAt(1.0, bottom_overlay)
        painter.fillRect(self.rect(), overlay)

        soft_glow = QRadialGradient(self.width() * 0.78, self.height() * 0.12, max(self.width(), self.height()) * 0.36)
        glow_color = QColor(self.theme_profile.accent)
        glow_color.setAlpha(42)
        soft_glow.setColorAt(0.0, glow_color)
        soft_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), soft_glow)

        border_color = QColor(self.theme_profile.panel_edge)
        border_color.setAlpha(44)
        painter.setPen(border_color)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

    def _build_window(self) -> None:
        if self._use_frameless_window:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        else:
            self.setWindowFlags(Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setMinimumSize(960, 680)
        
        self.setMouseTracking(True)
        self._margin = 8
        self._resize_dir = None
        self._start_pos = None
        self._start_geometry = None
        
        self.setStatusBar(QStatusBar(self))
        root = QWidget()
        root.setObjectName("appRoot")
        self.app_root = root
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.title_bar = None
        if self._use_frameless_window:
            self.title_bar = CustomTitleBar(self)
            outer.addWidget(self.title_bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(5)
        splitter.splitterMoved.connect(self._on_splitter_moved)
        self.main_splitter = splitter
        outer.addWidget(splitter, 1)

        left_panel = self._build_left_panel()
        middle_panel = self._build_middle_panel()
        self.left_panel = left_panel

        splitter.addWidget(left_panel)
        splitter.addWidget(middle_panel)
        splitter.setSizes([320, 680])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        self.menuBar().hide()

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("sidebarPanel")
        panel.setMinimumWidth(240)
        panel.setMaximumWidth(340)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        brand_box = QFrame()
        self.sidebar_brand_box = brand_box
        brand_box.setObjectName("sidebarBrandBox")
        brand_box.setStyleSheet(
            f"QFrame#sidebarBrandBox {{ background: {self.ui_palette.titlebar_surface}; border-radius: 20px; border: 1px solid {self.ui_palette.panel_border}; }}"
            "QLabel { background: transparent; border: none; }"
        )
        brand_layout = QHBoxLayout(brand_box)
        brand_layout.setContentsMargins(10, 8, 10, 8)
        brand_layout.setSpacing(8)
        brand_icon = QLabel()
        brand_icon.setPixmap(IconManager().get_pixmap("taskforge-logo", size=26))
        brand_text_box = QVBoxLayout()
        brand_text_box.setSpacing(1)
        brand_title = QLabel("Task Forge")
        self.sidebar_brand_title = brand_title
        brand_title.setStyleSheet(text_style(self.ui_palette.panel_text, 15, 800))
        brand_subtitle = QLabel("星轨任务指挥台")
        self.sidebar_brand_subtitle = brand_subtitle
        brand_subtitle.setStyleSheet(text_style(self.ui_palette.panel_muted, 10))
        brand_text_box.addWidget(brand_title)
        brand_text_box.addWidget(brand_subtitle)
        brand_layout.addWidget(brand_icon)
        brand_layout.addLayout(brand_text_box, 1)
        theme_tag = QLabel(self.theme_profile.name)
        theme_tag.setStyleSheet(
            f"color: {self.ui_palette.panel_text}; background: {self.ui_palette.theme_tag_bg}; border-radius: 10px; padding: 3px 8px; font-size: 11px; border: 1px solid {self.ui_palette.theme_tag_border};"
        )
        self.brand_theme_tag = theme_tag
        brand_layout.addWidget(theme_tag)
        layout.addWidget(brand_box)

        views_layout = QVBoxLayout()
        views_layout.setSpacing(8)

        self.view_cards = {}
        for key, title, icon_name in [
            ("create", "新建任务", "add"),
            ("today", "今日", "today"),
            ("plan", "计划", "plan"),
            ("tasktree", "任务树", "downloaded/svg/layout-dashboard.svg"),
            ("calendar", "日历", "calendar"),
            ("completed", "已完成", "completed"),
            ("hub", "工作台", "downloaded/svg/kanban-square.svg"),
            ("gantt", "甘特图", "gantt"),
            ("settings", "系统设置", "settings"),
        ]:
            btn = QPushButton()
            btn.setProperty("role", "ghost")
            btn.setObjectName("viewCard")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(48)
            btn.setStyleSheet(self._view_card_style(active=False))

            btn_layout = QHBoxLayout(btn)
            btn_layout.setContentsMargins(14, 10, 14, 10)
            btn_layout.setSpacing(12)

            icon_lbl = QLabel()
            icon_lbl.setPixmap(IconManager().get_pixmap(icon_name, size=18, color=self.ui_palette.icon_color))
            icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

            title_lbl = QLabel(title)
            title_lbl.setObjectName("viewCardTitle")
            title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            title_lbl.setStyleSheet(text_style(self.ui_palette.view_text, 13, "bold") + " padding-left: 4px;")
            
            count_lbl = QLabel("0" if key in ["today", "plan", "completed", "hub", "calendar", "tasktree"] else "")
            count_lbl.setObjectName("viewCardCount")
            count_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            count_lbl.setMinimumHeight(24)
            count_lbl.setMinimumWidth(28)
            count_lbl.setStyleSheet(self._view_count_style(active=False))
            if key not in ["today", "plan", "completed", "hub", "calendar", "tasktree"]:
                count_lbl.hide()
            
            btn_layout.addWidget(icon_lbl)
            btn_layout.addWidget(title_lbl)
            btn_layout.addStretch(1)
            btn_layout.addWidget(count_lbl)

            btn.clicked.connect(lambda _, k=key: self.switch_view(k))
            self.view_cards[key] = (btn, count_lbl, icon_lbl, icon_name)
            views_layout.addWidget(btn)

        layout.addLayout(views_layout)
        layout.addStretch(1)

        # Filters moved to middle panel — create the widgets here for early access
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索任务...")
        self.search_edit.textChanged.connect(lambda *_: self.refresh_views())
        self.category_filter = QComboBox()
        self.category_filter.addItem("📁 所有分类")
        self.category_filter.currentIndexChanged.connect(lambda *_: self.refresh_views())
        self.tag_filter = QComboBox()
        self.tag_filter.addItem("🏷️ 所有标签")
        self.tag_filter.currentIndexChanged.connect(lambda *_: self.refresh_views())

        # Bottom section: tabs for stats overview and focus timer
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {self.ui_palette.panel_border};")
        layout.addWidget(sep)

        bottom_tabs = QTabWidget()
        self.sidebar_bottom_tabs = bottom_tabs
        bottom_tabs.setObjectName("sidebarBottomTabs")
        bottom_tabs.setStyleSheet(self._sidebar_tabs_stylesheet())

        # Tab 1: 统计
        stats_tab = QWidget()
        stats_tab.setStyleSheet("background: transparent;")
        stats_layout = QVBoxLayout(stats_tab)
        stats_layout.setContentsMargins(0, 12, 0, 6)
        stats_layout.setSpacing(12)
        metrics_grid = QGridLayout()
        metrics_grid.setContentsMargins(0, 0, 0, 0)
        metrics_grid.setHorizontalSpacing(12)
        metrics_grid.setVerticalSpacing(12)
        self.sidebar_metric_cards = {}
        metric_accents = {
            "专注": mix_hex(self.theme_profile.accent, self.theme_profile.brass, 0.35),
            "进行中": self.theme_profile.accent,
            "已逾期": self.theme_profile.danger,
            "完成率": self.theme_profile.success,
        }
        for index, title in enumerate(["专注", "进行中", "已逾期", "完成率"]):
            card = InfoPill(title, accent=metric_accents[title])
            metrics_grid.addWidget(card, index // 2, index % 2)
            self.sidebar_metric_cards[title] = card
        metrics_grid.setColumnStretch(0, 1)
        metrics_grid.setColumnStretch(1, 1)
        stats_layout.addLayout(metrics_grid)
        self.sidebar_stats_hint = QLabel("")
        self.sidebar_stats_hint.setObjectName("sidebarStatsHint")
        self.sidebar_stats_hint.setWordWrap(True)
        self.sidebar_stats_hint.setStyleSheet("color: #c8d6e5; font-size: 12px; line-height: 1.55;")
        self.sidebar_stats_hint.hide()  # Hides duplicate of metric pills above
        stats_layout.addWidget(self.sidebar_stats_hint)
        bottom_tabs.addTab(stats_tab, "统计")

        # Tab 2: 专注计时
        self.focus_timer = FocusTimerWidget(self.finish_focus_timer)
        bottom_tabs.addTab(self.focus_timer, "专注")

        layout.addWidget(bottom_tabs)

        return panel

    def _build_sidebar_create_card(self) -> QWidget:
        card = QFrame()
        self.sidebar_create_card = card
        card.setObjectName("sidebarCreateCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.sidebar_create_title = QLabel("新建任务")
        self.sidebar_create_subtitle = QLabel("只输入标题即可创建，日期用按钮决定，不再打开额外的新建面板。")
        self.sidebar_create_subtitle.setWordWrap(True)
        layout.addWidget(self.sidebar_create_title)
        layout.addWidget(self.sidebar_create_subtitle)

        self.sidebar_task_input = QLineEdit()
        self.sidebar_task_input.setPlaceholderText("输入任务标题后回车")
        self.sidebar_task_input.returnPressed.connect(self._handle_quick_add)
        layout.addWidget(self.sidebar_task_input)

        due_row = QHBoxLayout()
        due_row.setContentsMargins(0, 0, 0, 0)
        due_row.setSpacing(8)
        self.sidebar_due_buttons: dict[str, QPushButton] = {}
        for preset, label in (("none", "无日期"), ("today", "今天"), ("tomorrow", "明天")):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked, value=preset: self._set_sidebar_due_preset(value) if checked else None)
            self.sidebar_due_buttons[preset] = button
            due_row.addWidget(button)
        layout.addLayout(due_row)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(8)
        self.sidebar_create_button = QPushButton("创建任务")
        self.sidebar_create_button.setProperty("role", "primary")
        self.sidebar_create_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sidebar_create_button.clicked.connect(self._handle_quick_add)
        self.sidebar_clear_button = QPushButton("清空")
        self.sidebar_clear_button.setProperty("role", "ghost")
        self.sidebar_clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sidebar_clear_button.clicked.connect(self._reset_sidebar_create_form)
        action_row.addWidget(self.sidebar_create_button, 1)
        action_row.addWidget(self.sidebar_clear_button)
        layout.addLayout(action_row)

        self._set_sidebar_due_preset("none")
        return card

    def _build_middle_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        panel.setObjectName("middlePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        self.middle_header = header
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(32, 32, 32, 16)
        
        self.board_title = QLabel("今日")
        self.board_title.setObjectName("mainTitle")
        self.board_title.setStyleSheet(title_text_style(self.ui_palette.panel_text, 28, "bold"))
        
        self.board_subtitle = QLabel("")
        self.board_subtitle.setObjectName("mainSubtitle")
        self.board_subtitle.setStyleSheet(text_style(self.ui_palette.panel_muted, 14))
        
        header_layout.addWidget(self.board_title)
        header_layout.addWidget(self.board_subtitle)
        layout.addWidget(header)
        
        # Stack for views
        self.middle_stack = QStackedWidget()
        layout.addWidget(self.middle_stack, 1)
        
        # We need padding for the stack content except when we want it full screen
        self.middle_stack.setContentsMargins(0, 0, 0, 0)
        
        # 1. Tree View (List)
        self.tree_container = QWidget()
        self.tree_container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self.tree_container)
        layout.setContentsMargins(16, 0, 16, 16)
        
        self.quick_add_input = QLineEdit()
        self.quick_add_input.setObjectName("quickAddInput")
        self.quick_add_input.setPlaceholderText("添加新任务 (按回车键保存)...")
        self.quick_add_input.setStyleSheet(
            f"background: {rgba(self.theme_profile.sky_bottom, 208)}; border: none; border-radius: 14px; padding: 13px 16px; font-size: 14px; color: {self.ui_palette.input_text}; margin-bottom: 12px;"
        )
        self.quick_add_input.returnPressed.connect(self._handle_quick_add)
        layout.addWidget(self.quick_add_input)

        self.tree_action_bar = QWidget()
        self.tree_action_bar.setStyleSheet("background: transparent;")
        tree_action_layout = QHBoxLayout(self.tree_action_bar)
        tree_action_layout.setContentsMargins(0, 0, 0, 8)
        tree_action_layout.setSpacing(8)

        self.tree_add_button = QPushButton("新增")
        self.tree_add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tree_add_button.clicked.connect(self.add_root_task)

        self.tree_toggle_button = QPushButton("完成/恢复")
        self.tree_toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tree_toggle_button.clicked.connect(self.toggle_selected_task)

        self.tree_delete_button = QPushButton("删除")
        self.tree_delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tree_delete_button.clicked.connect(self.delete_selected_task)

        tree_action_layout.addWidget(self.tree_add_button)
        tree_action_layout.addWidget(self.tree_toggle_button)
        tree_action_layout.addWidget(self.tree_delete_button)
        tree_action_layout.addStretch(1)
        layout.addWidget(self.tree_action_bar)

        self.quick_add_input.hide()
        self.tree_action_bar.hide()

        self.tree_scope_bar = QWidget()
        self.tree_scope_bar.setStyleSheet("background: transparent;")
        scope_layout = QHBoxLayout(self.tree_scope_bar)
        scope_layout.setContentsMargins(0, 0, 0, 10)
        scope_layout.setSpacing(8)
        scope_hint = QLabel("计划树视角")
        scope_hint.setStyleSheet(text_style(self.ui_palette.panel_muted, 12, 700))
        scope_layout.addWidget(scope_hint)
        self.tree_scope_buttons: dict[str, QPushButton] = {}
        self.tree_scope_hint = scope_hint
        scope_button_style = self._tree_scope_button_style()
        for mode, label in [("plan", "未完成"), ("completed", "已完成"), ("tasktree", "全部")]:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet(scope_button_style)
            button.clicked.connect(lambda checked, target=mode: self.switch_view(target) if checked else None)
            self.tree_scope_buttons[mode] = button
            scope_layout.addWidget(button)
        scope_layout.addStretch(1)
        self.tree_scope_summary = QLabel("")
        self.tree_scope_summary.setStyleSheet(text_style(self.ui_palette.panel_muted, 12, 600))
        scope_layout.addWidget(self.tree_scope_summary)
        layout.addWidget(self.tree_scope_bar)

        # Filter bar (search + category + tag inline)
        filter_bar = QWidget()
        filter_bar.setStyleSheet("background: transparent;")
        filter_bar_layout = QHBoxLayout(filter_bar)
        filter_bar_layout.setContentsMargins(0, 0, 0, 8)
        filter_bar_layout.setSpacing(8)

        search_container = QWidget()
        search_h = QHBoxLayout(search_container)
        search_h.setContentsMargins(10, 0, 10, 0)
        search_h.setSpacing(6)
        search_icon = QLabel()
        self.search_icon_label = search_icon
        search_icon.setPixmap(IconManager().get_pixmap("search", size=16, color=self.ui_palette.icon_color))
        self.search_edit.setStyleSheet(f"background: transparent; border: none; padding: 6px 0; font-size: 13px; color: {SURFACE_TEXT_PRIMARY};")
        search_h.addWidget(search_icon)
        search_h.addWidget(self.search_edit)
        search_container.setStyleSheet(
            f"background: {SURFACE_BG_ACCENT}; border-radius: 12px; border: 1px solid rgba(140, 167, 212, 0.28);"
        )
        combo_style = self._tree_combo_style()
        self.category_filter.setStyleSheet(combo_style)
        self.tag_filter.setStyleSheet(combo_style)
        self.history_back_button = QPushButton("返回上一步")
        self.history_back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.history_back_button.clicked.connect(self.navigate_back)
        self.date_picker_button = QPushButton("按日期筛选")
        self.date_picker_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.date_picker_button.clicked.connect(self._open_date_focus_dialog)
        filter_bar_layout.addWidget(self.history_back_button, 0)
        filter_bar_layout.addWidget(search_container, 3)
        filter_bar_layout.addWidget(self.category_filter, 1)
        filter_bar_layout.addWidget(self.tag_filter, 1)
        filter_bar_layout.addWidget(self.date_picker_button, 0)
        self.date_focus_chip = QPushButton()
        self.date_focus_chip.setCursor(Qt.CursorShape.PointingHandCursor)
        self.date_focus_chip.clicked.connect(self.clear_date_focus)
        self.date_focus_chip.hide()
        filter_bar_layout.addWidget(self.date_focus_chip, 0)
        filter_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        layout.addWidget(filter_bar)
        
        self.tree = TaskTreeWidget(self)
        self.tree.setStyleSheet('''
            QTreeWidget {
                background: rgba(7, 11, 20, 0.70);
                border: none;
                outline: none;
                font-size: 14px;
                border-radius: 18px;
                padding: 6px 0;
            }
            QTreeWidget::item {
                border: none;
            }
        ''')
        self.tree.setItemDelegate(TaskItemDelegate(self.tree))
        self.tree.setObjectName("taskTree")
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(4)
        self.tree.setIndentation(20)
        # Enable full row selection and style
        self.tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.tree.after_drop = self.persist_tree_from_ui
        self.tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        self.tree.itemDoubleClicked.connect(self._on_tree_double_click)
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        self.tree.itemChanged.connect(self._on_tree_item_changed)
        self.tree.customContextMenuRequested.connect(self._show_tree_context_menu)
        
        layout.addWidget(self.tree, 1)
        self.tree_inline_empty = self._build_tree_inline_empty()
        layout.addWidget(self.tree_inline_empty, 1)
        self.middle_stack.addWidget(self.tree_container)

        self.task_editor_view = TaskEditorView(self.db, self)
        self.task_editor_view.submitted.connect(self._handle_task_editor_submit)
        self.task_editor_view.canceled.connect(self._handle_task_editor_cancel)
        self.task_editor_view.page_shell.set_backdrop_pixmap(self.background_pixmap)
        self.middle_stack.addWidget(self.task_editor_view)

        self.task_detail_view = TaskDetailView(self.db, self)
        self.task_detail_view.back_requested.connect(self._return_to_last_browse_view)
        self.task_detail_view.edit_requested.connect(self._open_editor_from_detail)
        self.task_detail_view.page_shell.set_backdrop_pixmap(self.background_pixmap)
        self.middle_stack.addWidget(self.task_detail_view)
        
        # 2. Hub (Dashboard + Kanban + Analytics)
        self.hub_view = HubView(self.db, self)
        self.hub_view.task_detail_requested.connect(self.open_task_detail)
        self.middle_stack.addWidget(self.hub_view)
        
        # 3. Calendar
        self.calendar_view = CalendarView(self.db, self)
        self.middle_stack.addWidget(self.calendar_view)
        
        # 5. Gantt
        self.gantt_view = GanttView(self.db, self)
        self.middle_stack.addWidget(self.gantt_view)
        
        # 6. Settings
        self.settings_view = SettingsView(self)
        self.middle_stack.addWidget(self.settings_view)
        
        # 8. Empty State
        self.empty_state_container = QWidget()
        self.empty_state_container.setStyleSheet("background: transparent;")
        empty_layout = QVBoxLayout(self.empty_state_container)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_icon = QLabel()
        empty_icon.setPixmap(IconManager().get_pixmap("star", size=64, color=self.theme_profile.accent))
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.empty_text_label = QLabel("今天还没有任务\n享受这份宁静，或者开始新的计划")
        self.empty_text_label.setStyleSheet("color: #9ca3af; font-size: 16px; text-align: center;")
        self.empty_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Dashboard stats for empty state
        self.empty_stats_layout = QHBoxLayout()
        self.empty_stats_layout.setSpacing(20)
        self.empty_stats_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.empty_cards = []
        for title, color in [
            ("待办", self.theme_profile.accent),
            ("已完成", self.theme_profile.success),
            ("专注", mix_hex(self.theme_profile.accent, self.theme_profile.brass, 0.45)),
        ]:
            card = QFrame()
            card.setMinimumWidth(100)
            card.setStyleSheet(surface_style(SURFACE_BG_LIGHT, 10, border="rgba(255,255,255,0)"))
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 12, 16, 12)
            ct = QLabel(title)
            ct.setStyleSheet(text_style(self.ui_palette.panel_muted, 12))
            cv = QLabel("0")
            cv.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
            cl.addWidget(ct)
            cl.addWidget(cv)
            self.empty_stats_layout.addWidget(card)
            self.empty_cards.append(cv)

        add_btn = QPushButton("立即添加任务")
        add_btn.setProperty("role", "primary")
        add_btn.setFixedSize(140, 44)
        add_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        add_btn.clicked.connect(self.add_root_task)
        
        empty_layout.addStretch()
        empty_layout.addWidget(empty_icon)
        empty_layout.addSpacing(16)
        empty_layout.addWidget(self.empty_text_label)
        empty_layout.addSpacing(32)
        empty_layout.addLayout(self.empty_stats_layout)
        empty_layout.addSpacing(32)
        empty_layout.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        empty_layout.addStretch()
        
        self.middle_stack.addWidget(self.empty_state_container)
        
        return panel

    def _build_tree_inline_empty(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("treeInlineEmpty")
        panel.hide()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)

        self.tree_inline_empty_title = QLabel("当前没有可展示的任务")
        self.tree_inline_empty_title.setStyleSheet(text_style(self.ui_palette.panel_text, 18, 800))
        self.tree_inline_empty_subtitle = QLabel("")
        self.tree_inline_empty_subtitle.setWordWrap(True)
        self.tree_inline_empty_subtitle.setStyleSheet(text_style(self.ui_palette.panel_muted, 13))

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(8)
        self.tree_inline_empty_primary = QPushButton("新建任务")
        self.tree_inline_empty_primary.setProperty("role", "primary")
        self.tree_inline_empty_primary.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tree_inline_empty_primary.clicked.connect(self._handle_tree_inline_primary)
        self.tree_inline_empty_secondary = QPushButton("查看全部任务")
        self.tree_inline_empty_secondary.setProperty("role", "ghost")
        self.tree_inline_empty_secondary.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tree_inline_empty_secondary.clicked.connect(lambda: self.switch_view("tasktree"))
        button_row.addWidget(self.tree_inline_empty_primary)
        button_row.addWidget(self.tree_inline_empty_secondary)
        button_row.addStretch(1)

        layout.addWidget(self.tree_inline_empty_title)
        layout.addWidget(self.tree_inline_empty_subtitle)
        layout.addLayout(button_row)
        return panel

    def _handle_tree_inline_primary(self) -> None:
        if self.focus_due_date is not None:
            self.clear_date_focus()
            return
        self.switch_view("create")

    def _update_tree_inline_empty(self, is_empty: bool) -> None:
        if not hasattr(self, "tree_inline_empty"):
            return
        self.tree_inline_empty.setVisible(is_empty)
        if not is_empty:
            return
        if self.focus_due_date is not None:
            focus_label = self._format_focus_due_date(self.focus_due_date)
            self.tree_inline_empty_title.setText(f"{focus_label} 没有匹配任务")
            self.tree_inline_empty_subtitle.setText("筛选条和日期标签仍然保留在上方，可以直接清除日期筛选或切回全部任务。")
            self.tree_inline_empty_primary.setText("清除日期筛选")
            self.tree_inline_empty_secondary.show()
        else:
            self.tree_inline_empty_title.setText("当前没有可展示的任务")
            self.tree_inline_empty_subtitle.setText("筛选条仍然可用。你可以直接搜索、切换分类，或进入“新建任务”页面录入具体任务。")
            self.tree_inline_empty_primary.setText("新建任务")
            self.tree_inline_empty_secondary.hide()

    def _build_workflow_board(self) -> QWidget:
        board = QFrame()
        board.setObjectName("workflowBoard")
        layout = QHBoxLayout(board)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.workflow_lists: dict[str, QListWidget] = {}
        self.workflow_columns: list[QFrame] = []
        workflow_meta = [
            ("today", "今日", "今天必须推进或完成的任务"),
            ("planning", "计划", "未来安排、循环任务与长期推进项"),
        ]
        for key, title, subtitle in workflow_meta:
            column = QFrame()
            column.setObjectName("workflowColumn")
            column_layout = QVBoxLayout(column)
            column_layout.setContentsMargins(12, 12, 12, 12)
            column_layout.setSpacing(8)
            title_label = QLabel(title)
            title_label.setObjectName("workflowTitle")
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("workflowSubtitle")
            list_widget = QListWidget()
            list_widget.setObjectName("workflowList")
            list_widget.itemDoubleClicked.connect(self._activate_list_task)
            self.workflow_lists[key] = list_widget
            self.workflow_columns.append(column)
            apply_elevation(column, blur=30, alpha=75, offset_y=6)
            column_layout.addWidget(title_label)
            column_layout.addWidget(subtitle_label)
            column_layout.addWidget(list_widget, 1)
            layout.addWidget(column, 1)
        return board

    def _build_notes_panel(self) -> QWidget:
        self.notes_stack = QStackedWidget()
        
        # === View 0: Notes List ===
        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(12, 12, 12, 12)
        list_layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        title_lbl = QLabel("便签")
        title_lbl.setStyleSheet(text_style(self.ui_palette.panel_text, 18, "bold"))
        
        add_btn = QPushButton()
        add_btn.setIcon(IconManager().get_icon("add", size=16, color=self.ui_palette.panel_text))
        add_btn.setFixedSize(32, 32)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setToolTip("新增便签")
        add_btn.clicked.connect(self.create_note)
        
        delete_btn = QPushButton()
        delete_btn.setIcon(IconManager().get_icon("trash", size=16, color=self.ui_palette.panel_text))
        delete_btn.setFixedSize(32, 32)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setToolTip("删除便签")
        delete_btn.clicked.connect(self.delete_current_note)
        
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(add_btn)
        header_layout.addWidget(delete_btn)
        
        self.note_list = QListWidget()
        self.note_list.itemSelectionChanged.connect(self.load_selected_note)
        self.note_list.itemClicked.connect(lambda: self.notes_stack.setCurrentIndex(1))
        
        list_layout.addLayout(header_layout)
        list_layout.addWidget(self.note_list)
        
        # === View 1: Note Editor ===
        editor_panel = QWidget()
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.setContentsMargins(12, 12, 12, 12)
        editor_layout.setSpacing(12)
        
        edit_header = QHBoxLayout()
        back_btn = QPushButton("← 返回")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(lambda: self.notes_stack.setCurrentIndex(0))
        
        self.note_pin_box = QCheckBox("置顶显示")
        # Fix vertical alignment
        self.note_pin_box.setStyleSheet("QCheckBox { spacing: 8px; } QCheckBox::indicator { width: 18px; height: 18px; }")
        
        save_note_button = QPushButton("保存")
        save_note_button.setCursor(Qt.CursorShape.PointingHandCursor)
        save_note_button.clicked.connect(self.save_current_note)
        
        edit_header.addWidget(back_btn)
        edit_header.addStretch()
        edit_header.addWidget(self.note_pin_box)
        edit_header.addWidget(save_note_button)
        
        self.note_title_edit = QLineEdit()
        self.note_title_edit.setPlaceholderText("便签标题...")
        self.note_title_edit.setStyleSheet(
            f"font-size: 20px; font-weight: bold; font-family: {TITLE_FONT_FAMILY}; border: none; background: transparent; padding: 4px 0; color: {self.ui_palette.panel_text};"
        )
        
        self.note_content_edit = QPlainTextEdit()
        self.note_content_edit.setPlaceholderText("在此输入便签内容...")
        
        editor_layout.addLayout(edit_header)
        editor_layout.addWidget(self.note_title_edit)
        editor_layout.addWidget(self.note_content_edit, 1)
        
        self.notes_stack.addWidget(list_panel)
        self.notes_stack.addWidget(editor_panel)
        
        return self.notes_stack

    def _build_manage_panel(self) -> QWidget:
        self.manage_panel = ManagementCenterPanel()
        self.manage_panel.export_button.clicked.connect(self.export_data)
        self.manage_panel.import_button.clicked.connect(self.import_data)
        self.manage_panel.category_button.clicked.connect(self.open_category_manager)
        self.manage_panel.settings_button.clicked.connect(lambda: self.switch_view("settings"))
        return self.manage_panel

    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon), self)
        menu = QMenu(self)
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self._restore_window)
        menu.addAction(show_action)
        exit_action = QAction("退出软件", self)
        exit_action.triggered.connect(self.exit_application)
        menu.addAction(exit_action)
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("Task Forge")
        self.tray.activated.connect(
            lambda reason: self._restore_window()
            if reason == QSystemTrayIcon.ActivationReason.Trigger
            else None
        )
        self.tray.show()

    def refresh_everything(self, preferred_task_id: Optional[int] = None) -> None:
        self.all_tasks = self.db.list_tasks()
        self.task_map = {task.id: task for task in self.all_tasks}
        self.children_map = defaultdict(list)
        for task in self.all_tasks:
            self.children_map[task.parent_id].append(task)
        for children in self.children_map.values():
            children.sort(key=lambda item: (item.sort_order, PRIORITY_ORDER.get(item.priority, 99), item.title.lower()))
        if getattr(self, "current_view_mode", "") == "detail" and getattr(self, "task_detail_view", None) is not None:
            detail_task = self.task_detail_view.task
            if detail_task is not None:
                fresh = self.task_map.get(detail_task.id)
                if fresh is not None:
                    self.task_detail_view.set_task(fresh, self.children_map)
        if getattr(self, "current_view_mode", "") == "gantt" and getattr(self, "gantt_view", None) is not None:
            self.gantt_view.refresh_data()
        if hasattr(self, 'board_subtitle'):
            today = date.today()
            weekday_text = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][today.weekday()]
            self.board_subtitle.setText(f"{today:%Y年%m月%d日} {weekday_text}，准备好开始专注了吗？")
        self._refresh_category_filter()
        self._refresh_metrics()
        self.refresh_views(preferred_task_id)
        self.refresh_notes()
        self._refresh_manage_panel()
        if hasattr(self, "settings_view"):
            self.settings_view.sync_from_main_window()
        self._schedule_next_reminder_check()
        self._show_load_feedback()

    def refresh_views(self, preferred_task_id: Optional[int] = None) -> None:
        self._refresh_metrics()
        self._refresh_category_filter()
        self._refresh_tree(preferred_task_id)
        self._refresh_side_lists()
        self._refresh_workflow_board()
        self._refresh_task_board_state()
        self._refresh_manage_panel()

    def _refresh_metrics(self) -> None:
        if not hasattr(self, 'view_cards'):
            return
        
        self.all_tasks = self.db.list_tasks()
        
        counts = self.db.dashboard_counts()
        dashboard = self.db.dashboard_snapshot()
        today = date.today()
        
        inbox_count = 0
        today_count = sum(1 for task in self.all_tasks if not task.completed and task.due_at and task.due_at.date() <= today)
        plan_count = sum(1 for task in self.all_tasks if not task.completed)
        completed_count = sum(1 for task in self.all_tasks if task.completed)
        
        # Add Hub stats
        hub_count = sum(1 for task in self.all_tasks if not task.completed)
        
        self.view_cards["today"][1].setText(str(today_count))
        self.view_cards["plan"][1].setText(str(plan_count))
        self.view_cards["completed"][1].setText(str(completed_count))
        self.view_cards["hub"][1].setText(str(hub_count))
        _cal_today = today
        calendar_month_count = sum(
            1 for task in self.all_tasks
            if not task.completed and task.due_at
            and task.due_at.year == _cal_today.year
            and task.due_at.month == _cal_today.month
        )
        self.view_cards["calendar"][1].setText(str(calendar_month_count))
        self.view_cards["tasktree"][1].setText(str(len(self.all_tasks)))
        
        total_focus = sum(task.tracked_minutes for task in self.all_tasks)
        pending = counts.get('pending', 0)
        overdue = counts.get('overdue', 0)
        
        if hasattr(self, 'sidebar_stats_hint'):
            self.sidebar_stats_hint.setText(
                f"当前聚焦 {pending} 项进行中任务，逾期 {overdue} 项，建议优先处理最早到期事项。"
            )
        if hasattr(self, "sidebar_metric_cards"):
            self.sidebar_metric_cards["专注"].set_value(f"{total_focus} 分钟")
            self.sidebar_metric_cards["进行中"].set_value(str(pending))
            self.sidebar_metric_cards["已逾期"].set_value(str(overdue))
            self.sidebar_metric_cards["完成率"].set_value(f"{dashboard['completion_rate']}%")
            
        if hasattr(self, 'empty_cards'):
            self.empty_cards[0].setText(str(pending))
            self.empty_cards[1].setText(str(completed_count))
            self.empty_cards[2].setText(f"{total_focus}m")
        self._update_tree_scope_controls()

    def _update_tree_scope_controls(self) -> None:
        if not hasattr(self, "tree_scope_bar"):
            return
        mode = getattr(self, "current_view_mode", "today")
        pending_count = sum(1 for task in self.all_tasks if not task.completed)
        completed_count = sum(1 for task in self.all_tasks if task.completed)
        total_count = len(self.all_tasks)
        self.tree_scope_bar.setVisible(mode in {"plan", "completed", "tasktree"})
        self.tree_scope_summary.setText(f"未完成 {pending_count} · 已完成 {completed_count} · 全部 {total_count}")
        for target_mode, button in self.tree_scope_buttons.items():
            button.blockSignals(True)
            button.setChecked(target_mode == mode)
            button.blockSignals(False)
        self._update_date_focus_chip()

    def _refresh_category_filter(self) -> None:
        categories = sorted({task.category for task in self.all_tasks if task.category})
        current = self.category_filter.currentText()
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("📁 所有分类")
        self.category_filter.addItems(categories)
        if current in categories or current == "📁 所有分类":
            self.category_filter.setCurrentText(current)
        self.category_filter.blockSignals(False)
        tags = self.db.list_tags()
        tag_current = self.tag_filter.currentText()
        self.tag_filter.blockSignals(True)
        self.tag_filter.clear()
        self.tag_filter.addItem("🏷️ 所有标签")
        self.tag_filter.addItems(tags)
        if tag_current in tags or tag_current == "🏷️ 所有标签":
            self.tag_filter.setCurrentText(tag_current)
        self.tag_filter.blockSignals(False)

    def _create_tree_group_item(
        self,
        title: str,
        subtitle: str,
        accent: str,
        *,
        level: int = 0,
        date_key: str | None = None,
    ) -> QTreeWidgetItem:
        item = QTreeWidgetItem([title, "", "", ""])
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        item.setExpanded(True)
        item.setData(0, TREE_GROUP_ROLE, True)
        item.setData(0, TREE_GROUP_SUBTITLE_ROLE, subtitle)
        item.setData(0, TREE_GROUP_ACCENT_ROLE, accent)
        item.setData(0, TREE_GROUP_LEVEL_ROLE, level)
        if date_key is not None:
            item.setData(0, TREE_DATE_GROUP_KEY_ROLE, date_key)
        return item

    def _date_group_meta(self, anchor_date: date | None, count: int) -> tuple[str, str, str, str]:
        if anchor_date is None:
            return "none", "未设日期", f"{count} 项任务 · 暂无截止时间", self.ui_palette.panel_muted
        today = date.today()
        label = self._format_focus_due_date(anchor_date)
        if anchor_date < today:
            return anchor_date.isoformat(), label, f"{count} 项任务 · 已过截止日期", self.theme_profile.danger
        if anchor_date == today:
            return anchor_date.isoformat(), label, f"{count} 项任务 · 今天需要处理", self.theme_profile.warning
        return anchor_date.isoformat(), label, f"{count} 项任务 · 按到期日归类", self.theme_profile.accent

    def _semantic_group_meta(self, bucket: str, count: int) -> tuple[str, str, str]:
        mapping = {
            "today": ("今日", f"{count} 条任务分支 · 今天需要处理", self.theme_profile.warning),
            "overdue": ("昨日未完成", f"{count} 条任务分支 · 已逾期仍未完成", self.theme_profile.danger),
            "future": ("未来", f"{count} 条任务分支 · 后续安排与无日期任务", self.theme_profile.accent),
            "done": ("昨日已完成", f"{count} 条任务分支 · 已完成归档", self.theme_profile.success),
        }
        return mapping[bucket]

    def _root_branch_bucket(self, task: Task, anchor_date: date | None) -> str:
        today = date.today()
        if task.completed:
            return "done"
        if anchor_date == today:
            return "today"
        if anchor_date is not None and anchor_date < today:
            return "overdue"
        return "future"

    def _status_badge_for_task(self, task: Task, child_count: int, done_count: int) -> tuple[str, str]:
        now = datetime.now()
        if task.completed:
            return "已完成", self.theme_profile.success
        if task.due_at and task.due_at < now:
            return "已逾期", self.theme_profile.danger
        if task.due_at and task.due_at.date() == now.date():
            return "今日", self.theme_profile.warning
        if child_count > 0 and done_count > 0:
            return "推进中", self.theme_profile.accent
        return "待推进", mix_hex(self.theme_profile.accent, "#ffffff", 0.18)

    def _timeline_label_for_task(self, task: Task) -> tuple[str, str]:
        now = datetime.now()
        if task.completed:
            if task.completed_at:
                return f"完成 {self._format_dt(task.completed_at)}", self.theme_profile.success
            if task.due_at:
                return f"截止 {self._format_dt(task.due_at)}", self.ui_palette.panel_muted
            return "已归档", self.ui_palette.panel_muted
        if task.due_at is None:
            return "无期限", self.ui_palette.panel_muted
        if task.due_at < now:
            return f"逾期 {self._format_dt(task.due_at)}", self.theme_profile.danger
        if task.due_at.date() == now.date():
            return f"今天 {task.due_at:%H:%M}", self.theme_profile.warning
        if (task.due_at - now).total_seconds() <= 24 * 3600:
            return f"24h 内 {task.due_at:%H:%M}", mix_hex(self.theme_profile.warning, "#ffffff", 0.12)
        return self._format_dt(task.due_at), self.ui_palette.panel_muted

    def _build_tree_task_item(self, task: Task) -> QTreeWidgetItem:
        item = QTreeWidgetItem([task.title, "", "", ""])
        item.setCheckState(0, Qt.CheckState.Checked if task.completed else Qt.CheckState.Unchecked)
        item.setData(0, Qt.ItemDataRole.UserRole, task.id)
        item.setTextAlignment(1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        item.setTextAlignment(2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._style_tree_item(item, task)
        item.setSizeHint(0, item.sizeHint(0))
        self.tree_items[task.id] = item
        return item

    def _append_tree_branch(self, parent_widget: Optional[QTreeWidgetItem], task: Task, visible_ids: set[int]) -> None:
        if task.id not in visible_ids:
            return
        item = self._build_tree_task_item(task)
        if parent_widget is None:
            self.tree.addTopLevelItem(item)
        else:
            parent_widget.addChild(item)
        for child in self.children_map.get(task.id, []):
            self._append_tree_branch(item, child, visible_ids)

    def _force_visible_branch_ids(self, task_id: Optional[int]) -> set[int]:
        if task_id is None:
            return set()
        forced: set[int] = set()
        current = self.task_map.get(task_id)
        while current is not None:
            forced.add(current.id)
            current = self.task_map.get(current.parent_id) if current.parent_id is not None else None

        queue = list(self.children_map.get(task_id, []))
        while queue:
            child = queue.pop(0)
            forced.add(child.id)
            queue.extend(self.children_map.get(child.id, []))
        return forced

    def _refresh_tree(self, preferred_task_id: Optional[int] = None) -> None:
        visible_ids = self._visible_ids()
        selected_task_id = preferred_task_id or self.selected_task_id()
        forced_visible_ids = self._force_visible_branch_ids(selected_task_id)
        visible_ids.update(forced_visible_ids)
        
        self.tree.blockSignals(True)
        self.tree.clear()
        self.tree_items.clear()
        self.tree_date_groups.clear()

        mode = getattr(self, 'current_view_mode', 'today')
        root_tasks = [task for task in self.children_map.get(None, []) if task.id in visible_ids]

        anchor_cache: dict[int, date | None] = {}

        def resolve_anchor(task: Task) -> date | None:
            if task.id in anchor_cache:
                return anchor_cache[task.id]
            candidate_dates: list[date] = []
            if task.due_at and task.id in visible_ids:
                candidate_dates.append(task.due_at.date())
            for child in self.children_map.get(task.id, []):
                if child.id not in visible_ids:
                    continue
                child_anchor = resolve_anchor(child)
                if child_anchor is not None:
                    candidate_dates.append(child_anchor)
            if self.focus_due_date is not None:
                for candidate in candidate_dates:
                    if candidate == self.focus_due_date:
                        anchor_cache[task.id] = candidate
                        return candidate
            anchor_cache[task.id] = min(candidate_dates) if candidate_dates else None
            return anchor_cache[task.id]

        def root_sort_key(task: Task) -> tuple[date, int, str]:
            anchor_date = resolve_anchor(task)
            if task.completed and task.completed_at is not None:
                return task.completed_at.date(), PRIORITY_ORDER.get(task.priority or "中", 1), task.title.lower()
            return anchor_date or date.max, PRIORITY_ORDER.get(task.priority or "中", 1), task.title.lower()

        def add_roots(parent_item: QTreeWidgetItem, tasks: list[Task]) -> None:
            for root_task in sorted(tasks, key=root_sort_key):
                self._append_tree_branch(parent_item, root_task, visible_ids)

        def add_semantic_groups(tasks: list[Task], buckets: list[str]) -> None:
            grouped: dict[str, list[Task]] = {bucket: [] for bucket in buckets}
            for root_task in tasks:
                bucket = self._root_branch_bucket(root_task, resolve_anchor(root_task))
                if bucket in grouped:
                    grouped[bucket].append(root_task)
            for bucket in buckets:
                bucket_tasks = grouped.get(bucket, [])
                if not bucket_tasks:
                    continue
                title, subtitle, accent = self._semantic_group_meta(bucket, len(bucket_tasks))
                group_item = self._create_tree_group_item(title, subtitle, accent)
                self.tree.addTopLevelItem(group_item)
                add_roots(group_item, bucket_tasks)

        if self.focus_due_date is not None and root_tasks:
            date_key, title, subtitle, accent = self._date_group_meta(self.focus_due_date, len(root_tasks))
            group_item = self._create_tree_group_item(title, subtitle, accent, date_key=date_key)
            self.tree.addTopLevelItem(group_item)
            self.tree_date_groups[date_key] = group_item
            add_roots(group_item, root_tasks)
        elif mode == "completed":
            add_semantic_groups(root_tasks, ["done"])
        elif mode == "plan":
            add_semantic_groups(root_tasks, ["today", "overdue", "future"])
        elif mode == "tasktree":
            add_semantic_groups(root_tasks, ["today", "overdue", "future", "done"])
        else:
            buckets = ["today", "overdue"]
            # Keep the just-created/selected branch visible even if it falls into the
            # "future" bucket while the user is currently in today-like views.
            if forced_visible_ids:
                buckets.append("future")
            add_semantic_groups(root_tasks, buckets)

        self.tree.expandAll()

        is_empty = not self.tree_items
        self.tree.setVisible(not is_empty)
        self._update_tree_inline_empty(is_empty)

        if mode in ["today", "completed", "plan", "tasktree"]:
            self.empty_state_container.setVisible(False)
            if hasattr(self, 'middle_stack'):
                self.middle_stack.setCurrentWidget(self.tree_container)
        
        if selected_task_id in self.tree_items:
            self.tree.setCurrentItem(self.tree_items[selected_task_id])
        elif self.focus_due_date is not None:
            focus_group = self.tree_date_groups.get(self.focus_due_date.isoformat())
            if focus_group is not None:
                self.tree.scrollToItem(focus_group, QAbstractItemView.ScrollHint.PositionAtTop)
                current = self._first_task_item(focus_group)
                if current is not None:
                    self.tree.setCurrentItem(current)
        elif self.tree_items:
            self.tree.setCurrentItem(next(iter(self.tree_items.values())))
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.tree.setColumnWidth(1, 240)
        self.tree.setColumnWidth(2, 160)
        self.tree.setColumnWidth(3, 40)
        self.tree.blockSignals(False)

    def _style_tree_item(self, item: QTreeWidgetItem, task: Task) -> None:
        # ---------- priority icon in column 0 ----------
        _icon_mgr = IconManager()
        if task.completed:
            item.setIcon(0, _icon_mgr.get_icon("check-circle", size=16, color="#6b7280"))
        elif task.priority == "高":
            item.setIcon(0, _icon_mgr.get_icon("downloaded/svg/flame.svg", size=16, color="#ef4444"))
        elif task.priority == "中":
            item.setIcon(0, _icon_mgr.get_icon("star", size=16, color="#eab308"))
        elif task.priority == "低":
            item.setIcon(0, _icon_mgr.get_icon("circle", size=16, color=self.theme_profile.accent))
        else:
            item.setIcon(0, _icon_mgr.get_icon("circle", size=16, color="#6b7280"))

        # ---------- child count badge for parent tasks ----------
        child_tasks = self.children_map.get(task.id, [])
        child_count = len(child_tasks)
        done_count = sum(1 for c in child_tasks if c.completed)
        if child_count > 0:
            item.setIcon(0, _icon_mgr.get_icon("downloaded/svg/list-todo.svg", size=16,
                                                color="#6b7280" if task.completed else self.theme_profile.accent))

        # Title column
        title_color = "#6b7280" if task.completed else self.ui_palette.panel_text
        item.setForeground(0, QColor(title_color))
        
        # Right align columns
        item.setTextAlignment(1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        item.setTextAlignment(2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Priority mapping to string
        priority_str = ""
        priority_color = ""
        if task.priority == "高":
            priority_color = "#ef4444"
        elif task.priority == "中":
            priority_color = "#eab308"
        elif task.priority == "低":
            priority_color = self.theme_profile.accent

        # Column 1: show category or child progress
        if child_count > 0:
            category_text = f"{done_count}/{child_count} 子任务"
        else:
            raw_cat = task.category or ""
            # Filter out corrupt/garbage category text
            if raw_cat in {"默认", "无分类", "未分类"} or "?" in raw_cat or "\ufffd" in raw_cat:
                category_text = ""
            else:
                category_text = raw_cat

        item.setText(1, category_text)

        status_text, status_color = self._status_badge_for_task(task, child_count, done_count)
        timeline_text, timeline_color = self._timeline_label_for_task(task)
        
        # Subtitle columns (category, due)
        sub_color = "#4b5563" if task.completed else self.ui_palette.panel_muted
        if child_count > 0:
            progress_color = self.theme_profile.success if done_count == child_count else self.theme_profile.accent
            item.setForeground(1, QColor("#6b7280" if task.completed else progress_color))
        elif priority_color and not task.completed:
            item.setForeground(1, QColor(priority_color))
        else:
            item.setForeground(1, QColor(sub_color))
        
        # Due Date Color
        due_color = self.ui_palette.panel_muted
        if not task.completed and task.due_at:
            now = datetime.now()
            if task.due_at < now:
                due_color = self.theme_profile.danger
            elif task.due_at.date() == now.date():
                due_color = self.theme_profile.warning
                
        # Date Text
        item.setText(2, timeline_text)
        item.setForeground(2, QColor(timeline_color if timeline_text else (due_color if not task.completed else sub_color)))
        
        # Store data for custom delegate
        item.setData(1, Qt.ItemDataRole.UserRole, task.priority)
        item.setData(1, Qt.ItemDataRole.UserRole + 1, category_text)
        item.setData(1, TREE_STATUS_TEXT_ROLE, status_text)
        item.setData(1, TREE_STATUS_COLOR_ROLE, status_color)
        item.setData(2, Qt.ItemDataRole.UserRole, task.due_at)
        item.setData(2, TREE_TIMELINE_COLOR_ROLE, timeline_color)
        item.setData(0, Qt.ItemDataRole.UserRole + 1, task.completed)
        item.setData(0, Qt.ItemDataRole.UserRole + 2, child_count)  # expose child count
        
        font = item.font(0)
        font.setBold(task.parent_id is None and not task.completed)
        font.setStrikeOut(task.completed)
        item.setFont(0, font)
        
        font_small = item.font(1)
        font_small.setPointSize(10)
        item.setFont(1, font_small)
        item.setFont(2, font_small)
        
        # Rich tooltip
        child_hint = f"\n子任务：{done_count}/{child_count} 已完成" if child_count > 0 else ""
        item.setToolTip(0, (
            f"{task.title}{child_hint}\n"
            f"优先级：{task.priority or '普通'}\n"
            f"分类：{task.category or '未分类'}\n"
            f"标签：{task.tags or '无'}\n"
            f"循环：{task.recurrence_rule}"
        ))

    def _refresh_side_lists(self) -> None:
        pass

    def _refresh_workflow_board(self) -> None:
        if not hasattr(self, "workflow_lists"):
            return
        today = date.today()
        buckets = {
            "today": [
                task for task in self.all_tasks
                if not task.completed and task.due_at and task.due_at.date() <= today
            ],
            "planning": [
                task for task in self.all_tasks
                if not task.completed and ((task.due_at and task.due_at.date() > today) or task.recurrence_rule != "不重复")
            ],
        }
        subtitles = {
            "today": ("今日暂无待办", "可以切换到计划或看板继续推进"),
            "planning": ("计划区为空", "给未来安排一些里程碑任务"),
        }
        for key, list_widget in self.workflow_lists.items():
            list_widget.clear()
            tasks = buckets.get(key, [])[:8]
            if not tasks:
                self._add_empty_state_items(list_widget, *subtitles[key])
                continue
            for task in tasks:
                due_text = self._format_dt(task.due_at) or "未设日期"
                item = QListWidgetItem(f"{task.title}\n{task.category}｜{task.priority}｜{due_text}")
                item.setToolTip(self._task_path(task.id))
                item.setData(Qt.ItemDataRole.UserRole, task.id)
                icon_name = "check-circle" if task.completed else "circle"
                icon_color = "#64748b" if task.completed else PRIORITY_COLORS.get(task.priority, self.theme_profile.accent)
                item.setIcon(IconManager().get_icon(icon_name, color=icon_color))
                list_widget.addItem(item)

    def _add_empty_state_items(self, list_widget: QListWidget, primary: str, secondary: Optional[str] = None) -> None:
        for text in [primary, secondary]:
            if not text:
                continue
            item = QListWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            item.setForeground(QColor(255, 255, 255, 115))
            list_widget.addItem(item)

    def _refresh_week_view(self) -> None:
        if self.week_panel is not None:
            start_day = date.today() - timedelta(days=date.today().weekday())
            self.week_panel.apply_snapshot(self.db.weekly_operational_snapshot(start_day))

    def _refresh_stats_chart(self) -> None:
        if self.stats_panel is not None:
            self.stats_panel.apply_snapshot(self.db.stats_overview_snapshot(days=14))

    def _refresh_manage_panel(self) -> None:
        if hasattr(self, "manage_panel"):
            self.manage_panel.apply_snapshot(self.db.management_center_snapshot(self.auto_sync_enabled))

    def _build_week_header_widget(self, title: str, subtitle: str, accent: str) -> QWidget:
        frame = SummaryCard(title, subtitle, accent)
        return frame

    def _build_week_task_widget(self, task: Optional[Task]) -> QWidget:
        frame = QFrame()
        frame.setStyleSheet(
            f"background: {self.ui_palette.panel_bg}; border-radius: 18px; border: none;"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        icon = QLabel()
        if task is None:
            icon.setPixmap(IconManager().get_pixmap("calendar", size=18, color="#475569"))
            title = QLabel("无任务安排")
            title.setStyleSheet(text_style("#64748b", 13))
            layout.addWidget(icon)
            layout.addWidget(title)
            return frame
        icon_name = "check-circle" if task.completed else "circle"
        icon_color = "#64748b" if task.completed else PRIORITY_COLORS.get(task.priority, self.theme_profile.accent)
        icon.setPixmap(IconManager().get_pixmap(icon_name, size=20, color=icon_color))
        layout.addWidget(icon)
        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        title = QLabel(task.title)
        title.setStyleSheet(text_style("#64748b" if task.completed else self.ui_palette.panel_text, 14, 600))
        meta = QLabel(f"{task.category}｜{task.priority} 优先级｜{self._format_dt(task.due_at)}")
        meta.setStyleSheet(text_style(self.ui_palette.panel_muted, 12))
        text_box.addWidget(title)
        text_box.addWidget(meta)
        layout.addLayout(text_box, 1)
        badge = QLabel("完成" if task.completed else "待办")
        badge_color = self.theme_profile.success if task.completed else self.theme_profile.accent
        badge.setStyleSheet(chip_style(text_color=self.ui_palette.panel_text, background=rgba(badge_color, 61), border=rgba(badge_color, 92)))
        layout.addWidget(badge)
        return frame

    def _refresh_task_board_state(self) -> None:
        self.all_tasks = self.db.list_tasks()
        self.task_map = {t.id: t for t in self.all_tasks}
        self.children_map = defaultdict(list)
        for t in self.all_tasks:
            self.children_map[t.parent_id].append(t)
            
        mode = getattr(self, 'current_view_mode', 'today')
        show_quick_controls = mode in {"today", "plan", "tasktree", "completed"}
        if hasattr(self, 'quick_add_input'):
            self.quick_add_input.setVisible(show_quick_controls)
        if hasattr(self, 'tree_action_bar'):
            self.tree_action_bar.setVisible(show_quick_controls)

    def refresh_focus_panel(self) -> None:
        """No-op — 详情已改为主内容区页面。"""
        pass

    def _on_tree_selection_changed(self) -> None:
        """Update status bar with selected task info."""
        task = self.current_task()
        if task:
            self.statusBar().showMessage(f"选中: {task.title}（双击查看详情）", 3000)

    def _on_tree_double_click(self, item: QTreeWidgetItem, column: int) -> None:
        task_id = item.data(0, Qt.ItemDataRole.UserRole)
        if task_id is not None:
            self.open_task_detail(task_id)

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        if column == 3:
            task_id = item.data(0, Qt.ItemDataRole.UserRole)
            if task_id is not None:
                self.open_task_detail(task_id)

    def _view_title_for_mode(self, mode: str) -> str:
        labels = {
            "today": "今日任务",
            "plan": "计划树",
            "tasktree": "全部任务",
            "calendar": "日历",
            "completed": "已完成",
            "hub": "工作台",
            "gantt": "甘特图",
            "settings": "系统设置",
            "detail": "任务详情",
        }
        return labels.get(mode, "上一页")

    def _back_button_text(self, mode: str) -> str:
        return f"返回{self._view_title_for_mode(mode)}"

    def open_task_detail(self, task_id: int) -> None:
        task = self.task_map.get(task_id)
        if not task:
            return
        current_mode = getattr(self, "current_view_mode", "tasktree")
        self._detail_return_mode = current_mode if current_mode in {"today", "plan", "tasktree", "calendar", "completed", "hub", "gantt", "settings"} else getattr(self, "_last_browse_view", "tasktree")
        self.task_detail_view.set_back_text(self._back_button_text(self._detail_return_mode))
        self.task_detail_view.set_task(task, self.children_map)
        self.switch_view("detail")

    def _open_editor_from_detail(self, task_id: int) -> None:
        task = self.task_map.get(task_id)
        if task is None:
            return
        self._editor_return_mode = "detail"
        self._editor_return_task_id = task.id
        self.task_editor_view.set_back_text("返回任务详情")
        self.task_editor_view.set_context(task=task)
        self.switch_view("edit")

    def _return_to_last_browse_view(self) -> None:
        self.switch_view(getattr(self, "_detail_return_mode", getattr(self, "_last_browse_view", "tasktree")))

    def _handle_task_editor_cancel(self) -> None:
        if self._editor_return_mode == "detail" and self._editor_return_task_id is not None:
            self.open_task_detail(self._editor_return_task_id)
            return
        self._return_to_last_browse_view()

    def _handle_task_editor_submit(self, payload: dict[str, object]) -> None:
        editing_task = self.task_editor_view.task
        if editing_task is not None:
            before_payload = self.db._task_to_dict(self.task_map.get(editing_task.id) or editing_task)
            self.db.update_task(editing_task.id, payload)
            target_id = editing_task.id
            self._push_undo({"type": "update", "task_id": editing_task.id, "before": before_payload})
        else:
            created = self.db.create_task(payload)
            target_id = created.id
            self._push_undo({"type": "create", "task_id": created.id})

        if self._editor_return_mode == "detail":
            self.refresh_everything(target_id)
            self.open_task_detail(target_id)
        else:
            target_mode = self._editor_return_mode if self._editor_return_mode in {"today", "plan", "tasktree", "calendar", "completed", "hub", "gantt", "settings"} else "tasktree"
            # Suppress the internal refresh_views() inside switch_view so the tree
            # is only built once (below), with the correct forced-visibility context.
            self._suppress_switch_view_refresh = True
            try:
                self.switch_view(target_mode)
            finally:
                self._suppress_switch_view_refresh = False
            self.refresh_everything(target_id)

    def _show_tree_context_menu(self, pos: QPoint) -> None:
        item = self.tree.itemAt(pos)
        if not item:
            return
        
        task_id = item.data(0, Qt.ItemDataRole.UserRole)
        task = self.task_map.get(task_id)
        if not task:
            return

        menu = QMenu(self)
        
        toggle_text = "标记为未完成" if task.completed else "标记为已完成"
        toggle_act = QAction(toggle_text, self)
        toggle_act.triggered.connect(lambda: self.toggle_selected_task())
        menu.addAction(toggle_act)
        
        menu.addSeparator()
        
        detail_act = QAction("查看详情", self)
        detail_act.triggered.connect(lambda: self.open_task_detail(task_id))
        menu.addAction(detail_act)
        
        edit_act = QAction("编辑任务", self)
        edit_act.triggered.connect(lambda: self.edit_selected_task())
        menu.addAction(edit_act)
        
        add_sub_act = QAction("新增子任务", self)
        add_sub_act.triggered.connect(lambda: self.add_subtask())
        menu.addAction(add_sub_act)
        
        clone_act = QAction("克隆任务", self)
        clone_act.triggered.connect(lambda: self._clone_task(task_id))
        menu.addAction(clone_act)
        
        menu.addSeparator()
        
        delete_act = QAction("删除任务", self)
        delete_act.triggered.connect(lambda: self.delete_selected_task())
        menu.addAction(delete_act)
        
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _clone_task(self, task_id: int) -> None:
        task = self.task_map.get(task_id)
        if not task:
            return
        
        new_task = self.db.create_task(
            {
                "title": f"{task.title} (副本)",
                "description": task.description,
                "category": task.category,
                "tags": task.tags,
                "priority": task.priority,
                "due_at": task.due_at,
                "remind_at": task.remind_at,
                "estimated_minutes": task.estimated_minutes,
                "recurrence_rule": task.recurrence_rule,
                "parent_id": task.parent_id,
            }
        )
        self.refresh_everything(new_task.id)

    def _visible_ids(self) -> set[int]:
        visible = set()
        
        # In modern to-do lists, we only show root tasks that match the filter.
        # Subtasks will be loaded under their parents regardless of whether the subtask matches the filter.
        # BUT if a subtask matches the filter and its parent doesn't, we should STILL show the parent 
        # so the user can see the matching subtask.
        
        def check_and_add(t_id: int) -> bool:
            task = self.task_map.get(t_id)
            if not task:
                return False
            matches = self._matches_filters(task)
            
            # Check if any child matches
            child_matches = False
            for child in self.children_map.get(t_id, []):
                if check_and_add(child.id):
                    child_matches = True
                    
            if matches or child_matches:
                visible.add(t_id)
                return True
            return False

        # Start checking from root tasks
        for t in self.children_map.get(None, []):
            check_and_add(t.id)
            
        return visible

    def switch_view(self, mode: str) -> None:
        browse_modes = {"today", "plan", "tasktree", "calendar", "completed", "hub", "gantt", "settings"}
        current_mode = getattr(self, "current_view_mode", "today")
        if (
            not self._suspend_browse_history
            and mode in browse_modes
            and current_mode in browse_modes
            and current_mode != mode
        ):
            self._push_browse_history()
        if mode in browse_modes:
            self._last_browse_view = mode
        self.current_view_mode = mode
        today = date.today()
        weekday_text = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][today.weekday()]
        titles = {
            "create": ("新建任务", "在主页面内填写任务内容，不再弹窗。", "暂无数据"),
            "today": ("今日任务", f"{today:%Y年%m月%d日} {weekday_text}，准备好开始专注了吗？", "今天还没有任务\n享受这份宁静，或者开始新的计划"),
            "plan": ("计划树 · 未完成", "当前视图只保留未完成任务，适合持续推进和排计划。", "未完成计划树为空\n可以先新建任务，或切到“全部”检查层级结构"),
            "completed": ("计划树 · 已完成", "回顾已完成层级，快速复盘近期成果。", "还没有已完成的任务\n完成后会自动出现在这里"),
            "hub": ("看板与分析", "自动汇聚看板流转与深度分析，不再保留独立仪表盘。", "暂无数据"),
            "gantt": ("甘特图", "项目进度一目了然", "暂无数据"),
            "calendar": ("日历", "月度任务分布", "暂无数据"),
            "settings": ("系统设置", "个性化配置", "无数据"),
        }
        title, subtitle, empty_text = titles.get(mode, ("任务列表", "", "暂无任务"))
        # Add tasktree title dynamically
        if mode == "tasktree":
            title, subtitle, empty_text = "计划树 · 全部", "完整展示已完成与未完成任务的父子层级结构。", "暂无任务\n从全部视角检查当前任务结构"
        elif mode == "edit":
            title, subtitle, empty_text = "修改任务", "直接在主页面内修改，不再弹窗。", "暂无数据"
        elif mode == "detail":
            title, subtitle, empty_text = "任务详情", "完整展示任务内容，不再出现站位性空白。", "暂无数据"
        if self.focus_due_date is not None and mode in {"today", "plan", "completed", "tasktree"}:
            focus_label = self._format_focus_due_date(self.focus_due_date)
            subtitle = f"按日期定位：{focus_label}，任务树已按截止日期归类展示。"
            empty_text = f"{focus_label} 没有匹配任务\n可清除日期筛选后查看全部任务"
        if hasattr(self, 'board_title'):
            self.board_title.setText(title)
        if hasattr(self, 'board_subtitle'):
            self.board_subtitle.setText(subtitle)
            self.board_subtitle.setStyleSheet(text_style(self.ui_palette.panel_text_soft, 14, 600))
        if hasattr(self, 'empty_text_label'):
            self.empty_text_label.setText(empty_text)
        if hasattr(self, "middle_header"):
            self.middle_header.setVisible(mode not in {"create", "edit", "detail"})
            
        # Switch middle stack
        if mode == "create":
            self._editor_return_mode = getattr(self, "_last_browse_view", "tasktree")
            self._editor_return_task_id = None
            self.task_editor_view.set_back_text(self._back_button_text(self._editor_return_mode))
            self.task_editor_view.set_context(task=None)
            current_category = self.category_filter.currentText().strip() if hasattr(self, "category_filter") else ""
            if current_category and not current_category.startswith("📁"):
                self.task_editor_view.category_input.setText(current_category)
            if self.focus_due_date is not None:
                self.task_editor_view.due_toggle.setChecked(True)
                self.task_editor_view.due_edit.setDateTime(QDateTime(self.focus_due_date.year, self.focus_due_date.month, self.focus_due_date.day, 23, 59))
            elif getattr(self, "_last_browse_view", "") == "today":
                current_dt = QDateTime.currentDateTime()
                self.task_editor_view.due_toggle.setChecked(True)
                self.task_editor_view.due_edit.setDateTime(QDateTime(current_dt.date(), current_dt.time()))
            self.middle_stack.setContentsMargins(0, 0, 0, 0)
            self.middle_stack.setCurrentWidget(self.task_editor_view)
        elif mode == "edit":
            self.task_editor_view.set_back_text("返回任务详情" if self._editor_return_mode == "detail" else self._back_button_text(self._editor_return_mode))
            self.middle_stack.setContentsMargins(0, 0, 0, 0)
            self.middle_stack.setCurrentWidget(self.task_editor_view)
        elif mode == "detail":
            self.task_detail_view.set_back_text(self._back_button_text(getattr(self, "_detail_return_mode", getattr(self, "_last_browse_view", "tasktree"))))
            self.middle_stack.setContentsMargins(0, 0, 0, 0)
            self.middle_stack.setCurrentWidget(self.task_detail_view)
        elif mode == "hub":
            self.middle_stack.setContentsMargins(0, 0, 0, 0)
            self.middle_stack.setCurrentWidget(self.hub_view)
            self.hub_view.refresh_data()
        elif mode == "calendar":
            self.middle_stack.setContentsMargins(0, 0, 0, 0)
            self.middle_stack.setCurrentWidget(self.calendar_view)
            self.calendar_view.refresh_data()
        elif mode == "gantt":
            self.middle_stack.setContentsMargins(0, 0, 0, 0)
            self.middle_stack.setCurrentWidget(self.gantt_view)
            self.gantt_view.refresh_data()
        elif mode == "settings":
            self.middle_stack.setContentsMargins(0, 0, 0, 0)
            self.middle_stack.setCurrentWidget(self.settings_view)
            self.settings_view.sync_from_main_window()
        elif mode == "completed":
            self.middle_stack.setContentsMargins(16, 0, 16, 16)
            self.middle_stack.setCurrentWidget(self.tree_container)
        elif mode == "tasktree":
            self.middle_stack.setContentsMargins(16, 0, 16, 16)
            self.middle_stack.setCurrentWidget(self.tree_container)
        else:
            self.middle_stack.setContentsMargins(16, 0, 16, 16)
            self.middle_stack.setCurrentWidget(self.tree_container)
            
        self._apply_view_card_states()
            
        if mode in ["today", "completed", "plan", "hub", "calendar", "gantt", "tasktree"]:
            if not getattr(self, "_suppress_switch_view_refresh", False):
                self.refresh_views()
        self._update_tree_scope_controls()
        self._apply_responsive_layout()
        self._update_browse_back_button()

    def _matches_filters(self, task: Task) -> bool:
        keyword = self.search_edit.text().strip().lower()
        if keyword:
            haystack = " ".join(filter(None, [task.title, task.description, task.category])).lower()
            if keyword not in haystack:
                return False
        
        today = date.today()
        mode = getattr(self, 'current_view_mode', 'today')
        
        if mode == "completed":
            if not task.completed:
                return False
        elif mode == "tasktree":
            pass  # Show all tasks in tree mode
        elif mode == "plan":
            if task.completed:
                return False
        elif mode in ["today", "calendar", "gantt", "hub"]:
            if task.completed:
                return False
                
            if mode == "today":
                if not (task.due_at and task.due_at.date() <= today):
                    return False

        focus_due_date = getattr(self, "focus_due_date", None)
        if focus_due_date is not None and mode in {"today", "plan", "completed", "tasktree"}:
            if not task.due_at or task.due_at.date() != focus_due_date:
                return False

        if hasattr(self, 'category_filter'):
            category = self.category_filter.currentText()
            if not category.startswith("📁"):
                if task.category != category:
                    return False
                
        if hasattr(self, 'tag_filter'):
            tag_value = self.tag_filter.currentText()
            if not tag_value.startswith("🏷"):
                if tag_value not in self.db.parse_tags(task.tags):
                    return False
                
        return True

    def _handle_quick_add(self) -> None:
        source_input = None
        if getattr(self, "sidebar_task_input", None) is not None and self.sidebar_task_input.text().strip():
            source_input = self.sidebar_task_input
        elif self.quick_add_input.text().strip():
            source_input = self.quick_add_input

        title = source_input.text().strip() if source_input is not None else ""
        if not title:
            return
        
        if source_input is getattr(self, "sidebar_task_input", None):
            due_at = self._quick_create_due_at()
            category = self._quick_create_category()
        else:
            due_at = datetime.now() if getattr(self, 'current_view_mode', '') == 'today' else None
            category = "今日" if due_at is not None else "无分类"
        
        payload = {
            "title": title,
            "category": category,
            "due_at": due_at,
            "priority": "中",
            "tags": "",
            "description": "",
            "estimated_minutes": 25,
            "recurrence_rule": "不重复",
            "parent_id": None
        }
        
        task = self.db.create_task(payload)
        if source_input is not None:
            source_input.clear()
        if source_input is getattr(self, "sidebar_task_input", None):
            self._reset_sidebar_create_form()
            self.sidebar_task_input.setFocus()
        
        # Push to undo stack
        self._push_undo({"type": "create", "task_id": task.id})
        
        self.refresh_everything(task.id)

    def _push_undo(self, action: dict[str, Any]) -> None:
        self._undo_stack.append(action)
        if len(self._undo_stack) > 50:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self) -> None:
        if not self._undo_stack:
            self.statusBar().showMessage("没有可撤销的操作", 4000)
            return
        
        action = self._undo_stack.pop()
        redo_action = None
        
        if action["type"] == "delete":
            restored_ids = []
            for snapshot in action["snapshots"]:
                restored_id = self.db.restore_task_subtree(snapshot)
                if restored_id is not None:
                    restored_ids.append(restored_id)
            redo_action = {"type": "delete_restore", "task_ids": restored_ids, "snapshots": action["snapshots"]}
            self.refresh_everything(restored_ids[0] if restored_ids else None)
            
        elif action["type"] == "create":
            task_id = action["task_id"]
            task = self.db.get_task(task_id)
            if task:
                snapshot = self.db.capture_task_subtree(task_id)
                self.db.delete_task(task_id)
                redo_action = {"type": "delete", "snapshots": [snapshot]}
            self.refresh_everything()
            
        elif action["type"] == "update":
            task_id = action["task_id"]
            current_task = self.db.get_task(task_id)
            if current_task:
                redo_payload = self.db._task_to_dict(current_task)
                self.db.update_task(task_id, action["before"])
                redo_action = {"type": "update", "task_id": task_id, "before": redo_payload}
            self.refresh_everything(task_id)
            
        elif action["type"] == "toggle":
            task_ids = action["task_ids"]
            self.db.batch_toggle_tasks(task_ids)
            redo_action = {"type": "toggle", "task_ids": task_ids}
            self.refresh_everything(task_ids[0] if task_ids else None)
            
        elif action["type"] == "delete_restore":
            # This is the redo of a delete
            task_ids = action["task_ids"]
            snapshots = []
            for tid in task_ids:
                snap = self.db.capture_task_subtree(tid)
                if snap: snapshots.append(snap)
                self.db.delete_task(tid)
            redo_action = {"type": "delete", "snapshots": snapshots}
            self.refresh_everything()

        if redo_action:
            self._redo_stack.append(redo_action)
        self.statusBar().showMessage(f"已撤销操作", 5000)

    def redo(self) -> None:
        if not self._redo_stack:
            self.statusBar().showMessage("没有可重做的操作", 4000)
            return
            
        action = self._redo_stack.pop()
        undo_action = None
        
        if action["type"] == "delete":
            restored_ids = []
            for snapshot in action["snapshots"]:
                restored_id = self.db.restore_task_subtree(snapshot)
                if restored_id is not None:
                    restored_ids.append(restored_id)
            undo_action = {"type": "delete_restore", "task_ids": restored_ids, "snapshots": action["snapshots"]}
            self.refresh_everything(restored_ids[0] if restored_ids else None)
            
        elif action["type"] == "create":
            task_id = action["task_id"]
            task = self.db.get_task(task_id)
            if task:
                snapshot = self.db.capture_task_subtree(task_id)
                self.db.delete_task(task_id)
                undo_action = {"type": "delete", "snapshots": [snapshot]}
            self.refresh_everything()
            
        elif action["type"] == "update":
            task_id = action["task_id"]
            current_task = self.db.get_task(task_id)
            if current_task:
                undo_payload = self.db._task_to_dict(current_task)
                self.db.update_task(task_id, action["before"])
                undo_action = {"type": "update", "task_id": task_id, "before": undo_payload}
            self.refresh_everything(task_id)
            
        elif action["type"] == "toggle":
            task_ids = action["task_ids"]
            self.db.batch_toggle_tasks(task_ids)
            undo_action = {"type": "toggle", "task_ids": task_ids}
            self.refresh_everything(task_ids[0] if task_ids else None)
            
        elif action["type"] == "delete_restore":
            task_ids = action["task_ids"]
            snapshots = []
            for tid in task_ids:
                snap = self.db.capture_task_subtree(tid)
                if snap: snapshots.append(snap)
                self.db.delete_task(tid)
            undo_action = {"type": "delete", "snapshots": snapshots}
            self.refresh_everything()

        if undo_action:
            self._undo_stack.append(undo_action)
        self.statusBar().showMessage(f"已重做操作", 5000)

    def add_root_task(self) -> None:
        self._editor_return_mode = getattr(self, "_last_browse_view", "tasktree")
        self._editor_return_task_id = None
        self.switch_view("create")

    def add_subtask(self) -> None:
        current = self.current_task()
        if current is None:
            QMessageBox.information(self, "未选择任务", "请先在任务地图中选择父任务。")
            return
        self._editor_return_mode = getattr(self, "_last_browse_view", "tasktree")
        self._editor_return_task_id = None
        self.task_editor_view.set_context(task=None, preferred_parent_id=current.id, parent_title=current.title)
        self.task_editor_view.category_input.setText(current.category if current.category and current.category != "默认" else "")
        self.switch_view("edit")

    def show_settings_dialog(self) -> None:
        self.switch_view("settings")

    def edit_selected_task(self) -> None:
        current = self.current_task()
        if current is None:
            QMessageBox.information(self, "未选择任务", "请先选择一个任务。")
            return
        self._editor_return_mode = getattr(self, "current_view_mode", "tasktree") if self.current_view_mode == "detail" else getattr(self, "_last_browse_view", "tasktree")
        if self.current_view_mode == "detail":
            self._editor_return_mode = "detail"
            self._editor_return_task_id = current.id
        else:
            self._editor_return_task_id = None
        self.task_editor_view.set_context(task=current)
        self.switch_view("edit")

    def toggle_selected_task(self) -> None:
        task_ids = self.selected_task_ids()
        if not task_ids:
            QMessageBox.information(self, "未选择任务", "请先选择一个任务。")
            return
        before_completed = self._completed_task_ids()
        self.db.batch_toggle_tasks(task_ids)
        self._push_undo({"type": "toggle", "task_ids": task_ids})
        self.refresh_everything(task_ids[0])
        self._maybe_show_completion_celebration(before_completed, preferred_task_ids=task_ids)

    def _queue_tree_check_update(self, task_id: int, is_checked: bool) -> None:
        self._pending_tree_check_updates[task_id] = is_checked
        if self._tree_check_update_queued:
            return
        self._tree_check_update_queued = True
        QTimer.singleShot(0, self._apply_pending_tree_check_updates)

    def _apply_pending_tree_check_updates(self) -> None:
        self._tree_check_update_queued = False
        pending_updates = self._pending_tree_check_updates
        self._pending_tree_check_updates = {}
        if not pending_updates:
            return
        before_completed = self._completed_task_ids()
        changed_task_ids: list[int] = []
        for task_id, is_checked in pending_updates.items():
            task = self.task_map.get(task_id)
            if task is None or task.completed == is_checked:
                continue
            self.db.update_task(task_id, {"completed": is_checked})
            changed_task_ids.append(task_id)
        if not changed_task_ids:
            return
        self.refresh_everything(changed_task_ids[0])
        self._maybe_show_completion_celebration(before_completed, preferred_task_ids=changed_task_ids)

    def _on_tree_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if column != 0:
            return
        task_id = item.data(0, Qt.ItemDataRole.UserRole)
        if task_id is None:
            return
        task = self.task_map.get(task_id)
        if task is None:
            return
            
        is_checked = item.checkState(0) == Qt.CheckState.Checked
        if task.completed != is_checked:
            self._queue_tree_check_update(task_id, is_checked)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0 is None:
            return
        if a0.key() == Qt.Key.Key_Delete:
            self.delete_selected_task()
        elif a0.key() == Qt.Key.Key_Space:
            self.toggle_selected_task()
        elif a0.key() == Qt.Key.Key_Enter or a0.key() == Qt.Key.Key_Return:
            if self.tree.hasFocus():
                self.edit_selected_task()
        elif a0.key() == Qt.Key.Key_Left:
            if self.tree.hasFocus():
                item = self.tree.currentItem()
                if item and item.childCount() > 0:
                    item.setExpanded(False)
        elif a0.key() == Qt.Key.Key_Right:
            if self.tree.hasFocus():
                item = self.tree.currentItem()
                if item and item.childCount() > 0:
                    item.setExpanded(True)
        else:
            super().keyPressEvent(a0)

    def postpone_selected_reminder(self) -> None:
        current = self.current_task()
        if current is None:
            QMessageBox.information(self, "未选择任务", "请先选择一个任务。")
            return
        self.db.postpone_reminder(current.id, 10)
        self.refresh_everything(current.id)
        self.statusBar().showMessage("提醒已延后 10 分钟", 4000)

    def delete_selected_task(self) -> None:
        task_ids = self.selected_root_task_ids()
        if not task_ids:
            QMessageBox.information(self, "未选择任务", "请先选择一个任务。")
            return
        snapshots = [self.db.capture_task_subtree(task_id) for task_id in task_ids]
        snapshots = [snapshot for snapshot in snapshots if snapshot is not None]
        names = [self.task_map[task_id].title for task_id in task_ids if task_id in self.task_map]
        answer = QMessageBox.question(
            self,
            "确认删除",
            f"将删除 {len(task_ids)} 个任务/子树：{', '.join(names[:3])}{'...' if len(names) > 3 else ''}，是否继续？",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        for task_id in task_ids:
            self.db.delete_task(task_id)
        self._push_undo({"type": "delete", "snapshots": snapshots})
        self.refresh_everything()
        self.statusBar().showMessage("删除完成，可按 Ctrl+Z 撤销", 8000)

    def undo_last_delete(self) -> None:
        if not self._undo_stack:
            self.statusBar().showMessage("当前没有可撤销的删除操作", 4000)
            return
        action = self._undo_stack.pop()
        if action["type"] != "delete":
            return
        restored_ids = []
        for snapshot in action["snapshots"]:
            restored_id = self.db.restore_task_subtree(snapshot)
            if restored_id is not None:
                restored_ids.append(restored_id)
        self._redo_stack.append({"type": "delete", "task_ids": restored_ids, "snapshots": action["snapshots"]})
        self.refresh_everything(restored_ids[0] if restored_ids else None)
        self.statusBar().showMessage("已撤销上一次删除操作", 5000)

    def redo_last_delete(self) -> None:
        if not self._redo_stack:
            self.statusBar().showMessage("当前没有可重做的删除操作", 4000)
            return
        action = self._redo_stack.pop()
        if action["type"] != "delete":
            return
        task_ids = [task_id for task_id in action["task_ids"] if self.db.get_task(task_id) is not None]
        for task_id in task_ids:
            self.db.delete_task(task_id)
        self._undo_stack.append({"type": "delete", "snapshots": action["snapshots"]})
        self.refresh_everything()
        self.statusBar().showMessage("已重做删除操作", 5000)

    def export_data(self) -> None:
        default_name = f"task_forge_backup_{datetime.now():%Y%m%d_%H%M%S}.json"
        file_path, _ = QFileDialog.getSaveFileName(self, "导出数据", str(Path.cwd() / default_name), "JSON Files (*.json)")
        if not file_path:
            return
        self.db.export_data(file_path)
        self.statusBar().showMessage(f"数据已导出到 {file_path}", 5000)

    def export_csv(self) -> None:
        default_name = f"task_forge_report_{datetime.now():%Y%m%d_%H%M%S}.csv"
        file_path, _ = QFileDialog.getSaveFileName(self, "导出CSV", str(Path.cwd() / default_name), "CSV Files (*.csv)")
        if not file_path:
            return
        self.db.export_csv(file_path)
        self.statusBar().showMessage(f"CSV 已导出到 {file_path}", 5000)

    def export_week_report(self) -> None:
        default_name = f"task_forge_weekly_{datetime.now():%Y%m%d_%H%M%S}.md"
        file_path, _ = QFileDialog.getSaveFileName(self, "导出周报", str(Path.cwd() / default_name), "Markdown Files (*.md)")
        if not file_path:
            return
        self.db.export_week_report(file_path)
        self.statusBar().showMessage(f"周报已导出到 {file_path}", 5000)

    def _export_markdown(self) -> None:
        """Export all tasks as a richly formatted Markdown checklist."""
        default_name = f"taskforge_tasks_{datetime.now():%Y%m%d_%H%M%S}.md"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出为 Markdown",
            str(Path.cwd() / default_name),
            "Markdown Files (*.md);;All Files (*)",
        )
        if not file_path:
            return
        all_tasks = self.db.list_tasks()
        export_tasks_markdown(all_tasks, self.children_map, file_path)
        stats = compute_export_stats(all_tasks)
        self.statusBar().showMessage(
            f"Markdown 已导出 · 共 {stats['total']} 项任务，完成率 {stats['completion_rate']}%",
            6000,
        )

    def _show_shortcuts_dialog(self) -> None:
        """Open the keyboard shortcut reference dialog."""
        dlg = ShortcutsDialog(parent=self)
        dlg.exec()

    def import_data(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "导入数据", str(Path.cwd()), "JSON Files (*.json)")
        if not file_path:
            return
        answer = QMessageBox.warning(
            self,
            "覆盖当前数据",
            "导入会替换现有任务与便签，是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.db.import_data(file_path)
        except ValueError as exc:
            QMessageBox.warning(self, "导入失败", str(exc))
            return
        self.refresh_everything()

    def batch_set_priority(self) -> None:
        task_ids = self.selected_task_ids()
        if not task_ids:
            QMessageBox.information(self, "未选择任务", "请先选择一个或多个任务。")
            return
        priority, ok = QInputDialog.getItem(self, "批量设置优先级", "选择优先级", ["高", "中", "低"], editable=False)
        if not ok:
            return
        for task_id in task_ids:
            self.db.update_task_fields(task_id, {"priority": priority})
        self.refresh_everything(task_ids[0])
        self.statusBar().showMessage(f"已批量更新 {len(task_ids)} 个任务的优先级", 5000)

    def open_category_manager(self) -> None:
        dialog = CategoryManagerDialog(self, self.db)
        dialog.exec()
        self.refresh_everything(self.selected_task_id())

    def refresh_notes(self) -> None:
        if not hasattr(self, "note_list"):
            return
        notes = self.db.list_notes()
        selected_id = self.current_note_id
        self.note_list.blockSignals(True)
        self.note_list.clear()
        for note in notes:
            text = f"  {note.title}"
            item = QListWidgetItem(text)
            item.setIcon(IconManager().get_icon("star" if note.pinned else "activity", color="#60a5fa" if note.pinned else "#9ca3af"))
            item.setData(Qt.ItemDataRole.UserRole, note.id)
            self.note_list.addItem(item)
        self.note_list.blockSignals(False)
        if not notes:
            self.current_note_id = None
            self.note_title_edit.clear()
            self.note_content_edit.clear()
            self.note_pin_box.setChecked(False)
            return
        target = selected_id if selected_id is not None else notes[0].id
        for row in range(self.note_list.count()):
            note_item = self.note_list.item(row)
            if note_item is not None and note_item.data(Qt.ItemDataRole.UserRole) == target:
                self.note_list.setCurrentRow(row)
                break

    def load_selected_note(self) -> None:
        item = self.note_list.currentItem()
        if item is None:
            return
        note_id = item.data(Qt.ItemDataRole.UserRole)
        note = self.db.get_note(note_id)
        if note is None:
            return
        self.current_note_id = note.id
        self.note_title_edit.setText(note.title)
        self.note_content_edit.setPlainText(note.content)
        self.note_pin_box.setChecked(note.pinned)

    def create_note(self) -> None:
        note = self.db.create_note("新便签")
        self.current_note_id = note.id
        self.refresh_notes()
        self.notes_stack.setCurrentIndex(1)

    def save_current_note(self) -> None:
        title = self.note_title_edit.text().strip() or "未命名便签"
        content = self.note_content_edit.toPlainText()
        pinned = self.note_pin_box.isChecked()
        if self.current_note_id is None:
            note = self.db.create_note(title, content, pinned)
            self.current_note_id = note.id
        else:
            note = self.db.get_note(self.current_note_id)
            if note is None:
                note = self.db.create_note(title, content, pinned)
                self.current_note_id = note.id
            else:
                note.title = title
                note.content = content
                note.pinned = pinned
                self.db.save_note(note)
        self.refresh_notes()
        self.statusBar().showMessage("便签已保存", 3000)

    def delete_current_note(self) -> None:
        if self.current_note_id is None:
            QMessageBox.information(self, "未选择便签", "请先选择一个便签。")
            return
        answer = QMessageBox.question(self, "删除便签", "确定删除当前便签吗？")
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.db.delete_note(self.current_note_id)
        self.current_note_id = None
        self.refresh_notes()

    def check_reminders(self) -> None:
        now = datetime.now()
        force_poll = False
        try:
            if not getattr(self, "enable_notifications", True):
                return

            if self.focus_timer.timer.isActive():
                force_poll = True
                return

            due_tasks = self.db.due_reminders(now)
            if not due_tasks:
                return
            self._play_reminder_sound()
            self.db.mark_reminders_sent([task.id for task in due_tasks])
            preview = "\n".join(f"{task.title}｜提醒 {self._reminder_display_dt(task)}" for task in due_tasks[:5])
            if len(due_tasks) > 5:
                preview += f"\n其余 {len(due_tasks) - 5} 项请在应用内查看"
            if self._should_show_system_reminder_toast():
                self.tray.showMessage("任务提醒", preview, QSystemTrayIcon.MessageIcon.Information, 12000)
            self.statusBar().showMessage(f"收到 {len(due_tasks)} 条任务提醒", 8000)
            self._show_reminder_dialog(due_tasks, preview)
            self.refresh_everything(self.selected_task_id())
        finally:
            self._schedule_next_reminder_check(reference_time=now, force_poll=force_poll)

    def current_task(self) -> Optional[Task]:
        task_id = self.selected_task_id()
        if task_id is None:
            return None
        return self.task_map.get(task_id)

    def _first_task_item(self, item: QTreeWidgetItem) -> Optional[QTreeWidgetItem]:
        task_id = item.data(0, Qt.ItemDataRole.UserRole)
        if task_id is not None:
            return item
        for index in range(item.childCount()):
            child_item = item.child(index)
            if child_item is None:
                continue
            child = self._first_task_item(child_item)
            if child is not None:
                return child
        return None

    def selected_task_id(self) -> Optional[int]:
        item = self.tree.currentItem()
        if item is None:
            return None
        return item.data(0, Qt.ItemDataRole.UserRole)

    def selected_task_ids(self) -> list[int]:
        return [
            item.data(0, Qt.ItemDataRole.UserRole)
            for item in self.tree.selectedItems()
            if item.data(0, Qt.ItemDataRole.UserRole) is not None
        ]

    def selected_root_task_ids(self) -> list[int]:
        selected = self.selected_task_ids()
        selected_set = set(selected)
        root_ids: list[int] = []
        for task_id in selected:
            current = self.task_map.get(task_id)
            is_nested = False
            while current and current.parent_id is not None:
                if current.parent_id in selected_set:
                    is_nested = True
                    break
                current = self.task_map.get(current.parent_id)
            if not is_nested:
                root_ids.append(task_id)
        return root_ids

    def _activate_list_task(self, item: QListWidgetItem) -> None:
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id is None:
            return
        self._refresh_tree(task_id)
        self.open_task_detail(task_id)

    def persist_tree_from_ui(self) -> None:
        ordered_nodes: list[dict[str, Optional[int]]] = []

        def visit(item: QTreeWidgetItem, parent_id: Optional[int]) -> None:
            task_id = item.data(0, Qt.ItemDataRole.UserRole)
            next_parent_id = parent_id
            if task_id is not None:
                ordered_nodes.append(
                    {
                        "id": int(task_id),
                        "parent_id": parent_id,
                        "sort_order": len([node for node in ordered_nodes if node["parent_id"] == parent_id]) + 1,
                    }
                )
                next_parent_id = int(task_id)
            for index in range(item.childCount()):
                child_item = item.child(index)
                if child_item is not None:
                    visit(child_item, next_parent_id)

        for index in range(self.tree.topLevelItemCount()):
            top_item = self.tree.topLevelItem(index)
            if top_item is not None:
                visit(top_item, None)
        self.db.apply_tree_order(ordered_nodes)
        self.refresh_everything(self.selected_task_id())

    def finish_focus_timer(self, minutes: int) -> None:
        current = self.current_task()
        if current is None:
            self.statusBar().showMessage("专注结束，但当前未选择任务，未记录时长", 5000)
            return
        self.db.record_focus_minutes(current.id, minutes)
        self.refresh_everything(current.id)
        self.statusBar().showMessage(f"已为“{current.title}”记录 {minutes} 分钟专注时长", 5000)

    def _progress_text(self, task_id: int) -> str:
        descendants = self._descendants(task_id)
        if not descendants:
            return "100%" if self.task_map[task_id].completed else "0%"
        done = sum(1 for child in descendants if child.completed)
        percent = round(done * 100 / len(descendants))
        return f"{percent}% ({done}/{len(descendants)})"

    def _descendants(self, task_id: int) -> list[Task]:
        result: list[Task] = []
        queue = list(self.children_map.get(task_id, []))
        while queue:
            current = queue.pop(0)
            result.append(current)
            queue.extend(self.children_map.get(current.id, []))
        return result

    def _task_depth(self, task_id: int) -> int:
        depth = 0
        current = self.task_map.get(task_id)
        while current and current.parent_id is not None:
            depth += 1
            current = self.task_map.get(current.parent_id)
        return depth

    def _task_path(self, task_id: int) -> str:
        path: list[str] = []
        current = self.task_map.get(task_id)
        while current is not None:
            path.append(current.title)
            current = self.task_map.get(current.parent_id) if current.parent_id is not None else None
        return " / ".join(reversed(path))

    def _restore_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _show_reminder_dialog(self, due_tasks: list[Task], preview: str) -> None:
        if not getattr(self, 'enable_notifications', True):
            # Notifications disabled in settings
            return
        if not self.isVisible():
            self._restore_window()

        overlay_title, overlay_subtitle = self._reminder_overlay_copy(due_tasks)
        dialog = ReminderPromptDialog(
            self,
            animation_id=self.reminder_animation_id,
            title=overlay_title,
            subtitle=overlay_subtitle,
            summary_text=preview,
            task_count=len(due_tasks),
        )
        dialog.exec()
        if dialog.selected_delay_minutes == 10:
            for task in due_tasks:
                self.db.postpone_reminder(task.id, 10)
            self.statusBar().showMessage("提醒已统一延后 10 分钟", 5000)
        elif dialog.selected_delay_minutes == 30:
            for task in due_tasks:
                self.db.postpone_reminder(task.id, 30)
            self.statusBar().showMessage("提醒已统一延后 30 分钟", 5000)
        elif dialog.selected_delay_minutes == 60:
            for task in due_tasks:
                self.db.postpone_reminder(task.id, 60)
            self.statusBar().showMessage("提醒已统一延后 1 小时", 5000)

    def _show_load_feedback(self) -> None:
        task_count = len(self.all_tasks)
        note_count = len(self.db.list_notes())
        if not self._startup_message_sent:
            self.statusBar().showMessage(f"已自动加载 {task_count} 条任务、{note_count} 条便签", 8000)
            self._startup_message_sent = True
        else:
            self.statusBar().showMessage(f"当前共有 {task_count} 条任务、{note_count} 条便签", 4000)

    def exit_application(self) -> None:
        self._allow_close = True
        self.close()

    def _restore_window_state(self) -> None:
        saved_geometry = self.settings.value("window_geometry")
        if saved_geometry:
            restored = self.restoreGeometry(saved_geometry)
            if restored:
                if self.isFullScreen() or self.isMaximized():
                    self.showNormal()
                self._normalize_window_geometry()
                return
        screen = QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            target_width = min(1480, max(available.width() - 96, 980))
            target_height = min(920, max(available.height() - 96, 680))
            self.resize(target_width, target_height)
            self.move(available.x() + max(20, (available.width() - target_width) // 2), available.y() + max(20, (available.height() - target_height) // 2))
        self._normalize_window_geometry()

    def _normalize_window_geometry(self) -> None:
        if self.isMaximized() or self.isFullScreen():
            return
        screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        frame = self.frameGeometry()

        target_width = frame.width()
        target_height = frame.height()
        if target_width >= available.width():
            target_width = max(self.minimumWidth(), available.width() - 80)
        if target_height >= available.height():
            target_height = max(self.minimumHeight(), available.height() - 80)

        if target_width != frame.width() or target_height != frame.height():
            self.resize(target_width, target_height)
            frame = self.frameGeometry()

        bounded_x = min(max(frame.x(), available.x()), available.right() - frame.width() + 1)
        bounded_y = min(max(frame.y(), available.y()), available.bottom() - frame.height() + 1)
        if bounded_x != frame.x() or bounded_y != frame.y():
            self.move(bounded_x, bounded_y)

    @staticmethod
    def _format_dt(value: Optional[datetime]) -> str:
        if value is None:
            return ""
        if value.date() == date.today():
            return f"今天 {value:%H:%M}"
        if value.date() == date.today() - timedelta(days=1):
            return f"昨天 {value:%H:%M}"
        if value.date() == date.today() + timedelta(days=1):
            return f"明天 {value:%H:%M}"
        if value.year == date.today().year:
            return f"{value:%m-%d %H:%M}"
        return value.strftime("%Y-%m-%d %H:%M")

    def _status_text(self, task: Task) -> str:
        if task.completed:
            return "已完成"
        if task.due_at and task.due_at < datetime.now():
            return "已逾期"
        if task.due_at and task.due_at.date() == date.today():
            return "今日"
        if task.due_at and (task.due_at - datetime.now()).total_seconds() <= 24 * 3600:
            return "24小时内"
        return "进行中"

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if a0 is None:
            return
        if not self._allow_close:
            behavior = self._resolve_close_behavior()
            if behavior is None:
                a0.ignore()
                return
            if behavior == "tray":
                a0.ignore()
                self._close_to_tray(show_message=True)
                return
        self.settings.setValue("window_geometry", self.saveGeometry())
        self.db.close()
        self.tray.hide()
        super().closeEvent(a0)
