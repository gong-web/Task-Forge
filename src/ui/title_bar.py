from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ui.icon_manager import IconManager
from ui.theme import DANGER_BORDER_SOFT, DANGER_HOVER_BG, SURFACE_TEXT_MUTED, scene_palette, text_style


class CustomTitleBar(QWidget):
    def __init__(self, parent=None, title="Task Forge - 个人任务驾驶舱"):
        super().__init__(parent)
        self.parent_window = parent
        self.setObjectName("customTitleBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(52)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 8, 12, 8)
        layout.setSpacing(14)
        self.root_layout = layout

        brand_box = QFrame()
        self.brand_box = brand_box
        brand_box.setObjectName("titleBrandBox")
        brand_box.setMaximumWidth(280)
        brand_layout = QHBoxLayout(brand_box)
        brand_layout.setContentsMargins(10, 6, 10, 6)
        brand_layout.setSpacing(8)
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(IconManager().get_pixmap("taskforge-logo", size=22))
        brand_layout.addWidget(self.icon_lbl)

        self.title_lbl = QLabel("Task Forge")
        self.subtitle_lbl = QLabel("星光计划驾驶舱")
        self.subtitle_lbl.setVisible(False)
        brand_layout.addWidget(self.title_lbl)
        layout.addWidget(brand_box)

        layout.addStretch()

        self.btn_min = self._create_control_btn("minus", "#9ca3af", self.parent_window.showMinimized)
        self.btn_max = self._create_control_btn("downloaded/svg/panels-top-left.svg", "#9ca3af", self._toggle_maximize)
        self.btn_close = self._create_control_btn("x", "#ef4444", self.parent_window.close, is_close=True)

        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

        self.start_pos = None
        self.apply_theme()
        self.set_compact(False)

    def _is_window_expanded(self) -> bool:
        return self.parent_window.isMaximized() or self.parent_window.isFullScreen()

    def _create_control_btn(self, icon_name, color, callback, is_close=False):
        btn = QPushButton()
        btn.setFixedSize(36, 36)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setIcon(IconManager().get_icon(icon_name, size=18, color=color))
        btn.setProperty("is_close", is_close)
        btn.clicked.connect(callback)
        return btn

    def apply_theme(self) -> None:
        palette = getattr(self.parent_window, "ui_palette", scene_palette(bool(getattr(self.parent_window, "is_dark_mode", True))))
        self.setStyleSheet(
            f"QWidget#customTitleBar {{ background: rgba(6, 10, 18, 236); border-top-left-radius: 28px; border-top-right-radius: 28px; border-bottom: 1px solid {palette.panel_border}; }}"
        )
        self.brand_box.setStyleSheet(
            f"QFrame#titleBrandBox {{ background: {palette.titlebar_surface}; border: 1px solid {palette.panel_border}; border-radius: 20px; }}"
            "QLabel { background: transparent; border: none; }"
        )
        self.title_lbl.setStyleSheet(text_style(palette.panel_text, 13, 800))
        self.subtitle_lbl.setStyleSheet(text_style(palette.panel_muted, 11))
        for button in (self.btn_min, self.btn_max, self.btn_close):
            is_close = bool(button.property("is_close"))
            hover_bg = DANGER_HOVER_BG if is_close else palette.titlebar_button_hover
            border_color = DANGER_BORDER_SOFT if is_close else palette.panel_border
            button.setStyleSheet(
                f"QPushButton {{ background: {palette.titlebar_button}; border: 1px solid {border_color}; border-radius: 12px; }}"
                f"QPushButton:hover {{ background: {hover_bg}; }}"
            )
        self.btn_min.setIcon(IconManager().get_icon("minus", size=18, color=palette.icon_color))
        current_icon = "downloaded/svg/panel-right.svg" if self._is_window_expanded() else "downloaded/svg/panels-top-left.svg"
        self.btn_max.setIcon(IconManager().get_icon(current_icon, size=18, color=palette.icon_color))
        self.btn_close.setIcon(IconManager().get_icon("x", size=18, color="#ef4444"))

    def set_compact(self, compact: bool) -> None:
        palette = getattr(self.parent_window, "ui_palette", scene_palette(bool(getattr(self.parent_window, "is_dark_mode", True))))
        self.setFixedHeight(44 if compact else 52)
        self.root_layout.setContentsMargins(14 if compact else 18, 6 if compact else 8, 10 if compact else 12, 6 if compact else 8)
        self.root_layout.setSpacing(10 if compact else 14)
        self.title_lbl.setStyleSheet(text_style(palette.panel_text, 12 if compact else 13, 800))
        for button in (self.btn_min, self.btn_max, self.btn_close):
            button.setFixedSize(30 if compact else 34, 30 if compact else 34)
        self.btn_min.setIcon(IconManager().get_icon("minus", size=16 if compact else 18, color=palette.icon_color))
        current_icon = "downloaded/svg/panel-right.svg" if self._is_window_expanded() else "downloaded/svg/panels-top-left.svg"
        self.btn_max.setIcon(IconManager().get_icon(current_icon, size=16 if compact else 18, color=palette.icon_color))
        self.btn_close.setIcon(IconManager().get_icon("x", size=16 if compact else 18, color="#ef4444"))

    def _toggle_maximize(self):
        palette = getattr(self.parent_window, "ui_palette", scene_palette(bool(getattr(self.parent_window, "is_dark_mode", True))))
        if self._is_window_expanded():
            self.parent_window.showNormal()
            normalize_geometry = getattr(self.parent_window, "_normalize_window_geometry", None)
            if callable(normalize_geometry):
                normalize_geometry()
            self.btn_max.setIcon(IconManager().get_icon("downloaded/svg/panels-top-left.svg", size=18, color=palette.icon_color))
        else:
            self.parent_window.showMaximized()
            self.btn_max.setIcon(IconManager().get_icon("downloaded/svg/panel-right.svg", size=18, color=palette.icon_color))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.start_pos is not None:
            delta = event.globalPosition().toPoint() - self.start_pos
            if self._is_window_expanded():
                self.parent_window.showNormal()
                normalize_geometry = getattr(self.parent_window, "_normalize_window_geometry", None)
                if callable(normalize_geometry):
                    normalize_geometry()
            self.parent_window.move(self.parent_window.pos() + delta)
            self.start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = None

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
