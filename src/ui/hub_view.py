"""工作台：看板 + 深度分析，统一承载任务流与自动分析。"""
from __future__ import annotations

from typing import Protocol, cast

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from ui.advanced_analytics import AdvancedAnalyticsView
from ui.kanban_view import KanbanBoard
from ui.theme import SURFACE_BG_EMBED, SURFACE_BORDER, rgba


class RefreshableView(Protocol):
    def refresh_data(self) -> None: ...


class HubView(QWidget):
    """把看板和深度分析整合在同一个标签页界面里。"""
    task_detail_requested = pyqtSignal(int)  # propagated from KanbanBoard

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("hubTabs")
        self.apply_theme()

        self.kanban_view = KanbanBoard(self.db, self)
        self.kanban_view.task_detail_requested.connect(self.task_detail_requested)
        self.analytics_view = AdvancedAnalyticsView(self.db, self)

        self.tabs.addTab(self.kanban_view, "看板")
        self.tabs.addTab(self.analytics_view, "分析")

        # Refresh the currently visible tab whenever the index changes
        self.tabs.currentChanged.connect(self._on_tab_changed)

        root.addWidget(self.tabs)

    def apply_theme(self) -> None:
        main_window = self.window()
        ui_palette = getattr(main_window, "ui_palette", None)
        theme_profile = getattr(main_window, "theme_profile", None)
        accent = getattr(theme_profile, "accent", "#60a5fa")
        accent_soft = getattr(theme_profile, "accent_soft", rgba(accent, 28))
        panel_top = getattr(theme_profile, "panel_top", "#0c1222")
        tab_text = getattr(ui_palette, "panel_muted", "#94a3b8")
        active_text = getattr(ui_palette, "panel_text", "#edf4ff")
        self.tabs.setStyleSheet(
            f"""
            QTabWidget#hubTabs::pane {{
                border: none;
                background: transparent;
            }}
            QTabBar::tab {{
                background: {SURFACE_BG_EMBED};
                border: 1px solid {SURFACE_BORDER};
                border-bottom: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                color: {tab_text};
                font-size: 13px;
                font-weight: 700;
                padding: 8px 22px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background: {accent_soft};
                color: {active_text};
                border-color: {rgba(accent, 110)};
                border-bottom: 2px solid {accent};
            }}
            QTabBar::tab:hover:!selected {{
                background: {rgba(accent, 14)};
                color: {active_text};
            }}
            QTabBar QToolButton {{
                background: {panel_top};
                border: none;
            }}
            """
        )
        if hasattr(self, "analytics_view"):
            self.analytics_view.apply_theme()

    def _on_tab_changed(self, index: int) -> None:
        view = self.tabs.widget(index)
        if hasattr(view, "refresh_data"):
            cast(RefreshableView, view).refresh_data()

    def refresh_data(self) -> None:
        """刷新当前活跃 tab 的数据；其他 tab 切换时再按需刷新。"""
        current = self.tabs.currentWidget()
        if hasattr(current, "refresh_data"):
            cast(RefreshableView, current).refresh_data()
