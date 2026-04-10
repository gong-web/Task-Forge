from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtGui import QColor, QFontDatabase
from PyQt6.QtWidgets import QApplication


def rgba(hex_color: str, alpha: int) -> str:
    color = QColor(hex_color)
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha})"


SURFACE_BG = "rgba(9, 14, 28, 0.9)"
SURFACE_BG_SOFT = "rgba(12, 18, 34, 0.86)"
SURFACE_BG_LIGHT = "rgba(255, 255, 255, 0.04)"
SURFACE_BG_FLOAT = "rgba(255, 255, 255, 0.1)"
SURFACE_BG_RAISED = "rgba(12, 18, 28, 0.88)"
SURFACE_BG_HOVER = "rgba(15, 24, 36, 0.94)"
SURFACE_BG_EMBED = "rgba(8, 12, 20, 0.72)"
SURFACE_BG_ACCENT = "rgba(15, 23, 42, 0.86)"
SURFACE_BG_DIM = "rgba(0, 0, 0, 0.2)"
SURFACE_BG_DIM_HOVER = "rgba(0, 0, 0, 0.4)"
SURFACE_BORDER = "rgba(255, 255, 255, 0.08)"
SURFACE_BORDER_SOFT = "rgba(255, 255, 255, 0.06)"
SURFACE_BORDER_STRONG = "rgba(255, 255, 255, 0.12)"
SURFACE_RING_TRACK = "rgba(255, 255, 255, 0.09)"
SURFACE_RING_INNER = "rgba(8, 12, 24, 0.73)"
SURFACE_GRADIENT_BASE_START = "rgba(8, 12, 24, 0.95)"
SURFACE_GRADIENT_BASE_END = "rgba(14, 20, 38, 0.86)"
SURFACE_GRADIENT_RAISED_START = "rgba(12, 18, 34, 0.93)"
SURFACE_GRADIENT_RAISED_END = "rgba(19, 27, 48, 0.84)"
DANGER_SURFACE_BG = "rgba(127, 29, 29, 0.92)"
DANGER_SURFACE_BORDER = "rgba(248, 113, 113, 0.35)"
DANGER_SURFACE_TEXT = "#fecaca"
DANGER_HOVER_BG = "rgba(239, 68, 68, 0.2)"
DANGER_BORDER_SOFT = "rgba(248, 113, 113, 0.28)"
ACCENT_SURFACE_SOFT = "rgba(96, 165, 250, 0.15)"
ACCENT_BORDER_SOFT = "rgba(96, 165, 250, 0.45)"
ACCENT_BORDER_STRONG = "rgba(96, 165, 250, 0.5)"
ACCENT_BORDER = "#60a5fa"
SURFACE_TEXT_PRIMARY = "#edf4ff"
SURFACE_TEXT_SECONDARY = "#d7e2f1"
SURFACE_TEXT_MUTED = "#94a3b8"
SURFACE_TEXT_DISABLED = "#7c8ba1"

APP_FONT_CANDIDATES: tuple[str, ...] = (
    "Microsoft YaHei UI",
    "Microsoft YaHei",
    "SimHei",
    "SimSun",
    "PingFang SC",
    "Noto Sans CJK SC",
    "Segoe UI Variable Text",
    "Segoe UI",
)

BODY_FONT_FAMILY = "'Microsoft YaHei UI', 'Microsoft YaHei', 'SimHei', 'PingFang SC', 'Noto Sans CJK SC', 'Segoe UI Variable Text', 'Segoe UI', sans-serif"
TITLE_FONT_FAMILY = "'Microsoft YaHei UI', 'Microsoft YaHei', 'Source Han Serif SC', 'PingFang SC', 'Noto Sans CJK SC', 'SimSun', 'Segoe UI Variable Display', 'Segoe UI', sans-serif"

_WINDOWS_FONT_FILES: tuple[str, ...] = (
    "msyh.ttc",
    "msyhbd.ttc",
    "msyhl.ttc",
    "simhei.ttf",
    "simsun.ttc",
)
_APP_FONTS_LOADED = False


def _system_font_roots() -> tuple[Path, ...]:
    roots: list[Path] = []
    windir = os.environ.get("WINDIR")
    if windir:
        roots.append(Path(windir) / "Fonts")
    roots.append(Path("C:/Windows/Fonts"))
    existing: list[Path] = []
    for root in roots:
        if root.exists() and root not in existing:
            existing.append(root)
    return tuple(existing)


def ensure_app_fonts_loaded() -> None:
    global _APP_FONTS_LOADED
    if _APP_FONTS_LOADED:
        return

    font_roots = _system_font_roots()
    if not os.environ.get("QT_QPA_FONTDIR") and font_roots:
        os.environ["QT_QPA_FONTDIR"] = str(font_roots[0])

    app = QApplication.instance()
    if app is None:
        return

    for root in font_roots:
        for filename in _WINDOWS_FONT_FILES:
            font_path = root / filename
            if font_path.exists():
                QFontDatabase.addApplicationFont(str(font_path))

    _APP_FONTS_LOADED = True


@dataclass(frozen=True)
class ScenePalette:
    panel_bg: str
    panel_text: str
    panel_text_soft: str
    panel_muted: str
    panel_border: str
    input_bg: str
    input_text: str
    input_border: str
    overlay: str
    frame_border: str
    view_text: str
    view_active_text: str
    titlebar_bg: str
    titlebar_surface: str
    titlebar_button: str
    titlebar_button_hover: str
    theme_tag_bg: str
    theme_tag_border: str
    # New component semantic colors
    dialog_bg: str
    composer_bg: str
    btn_primary_start: str
    btn_primary_end: str
    btn_primary_hover_start: str
    btn_primary_hover_end: str
    btn_primary_border: str
    btn_secondary_bg: str
    btn_secondary_border: str
    calendar_text: str
    calendar_disabled: str
    header_text: str
    icon_color: str
    scrollbar_handle: str
    scrollbar_handle_hover: str
    selection_bg: str
    checkbox_border: str
    card_secondary_bg: str
    card_secondary_border: str


def scene_palette(is_dark_mode: bool) -> ScenePalette:
    if is_dark_mode:
        return ScenePalette(
            panel_bg="rgba(10, 14, 24, 0.94)",
            panel_text=SURFACE_TEXT_PRIMARY,
            panel_text_soft=SURFACE_TEXT_SECONDARY,
            panel_muted=SURFACE_TEXT_MUTED,
            panel_border=SURFACE_BORDER,
            input_bg="rgba(15, 23, 42, 0.92)",
            input_text=SURFACE_TEXT_PRIMARY,
            input_border=SURFACE_BORDER,
            overlay="rgba(7, 10, 20, 0.94)",
            frame_border="rgba(255, 255, 255, 0.16)",
            view_text=SURFACE_TEXT_SECONDARY,
            view_active_text=SURFACE_TEXT_PRIMARY,
            titlebar_bg="rgba(7, 10, 20, 0.12)",
            titlebar_surface="rgba(9, 14, 28, 0.72)",
            titlebar_button="rgba(9, 14, 28, 0.62)",
            titlebar_button_hover="rgba(255, 255, 255, 0.1)",
            theme_tag_bg="rgba(96, 165, 250, 0.16)",
            theme_tag_border="rgba(96, 165, 250, 0.3)",
            dialog_bg="#18181b",
            composer_bg="#242529",
            btn_primary_start="#ec4899",
            btn_primary_end="#8b5cf6",
            btn_primary_hover_start="#f472b6",
            btn_primary_hover_end="#a78bfa",
            btn_primary_border="rgba(244, 114, 182, 0.4)",
            btn_secondary_bg="rgba(96, 165, 250, 0.12)",
            btn_secondary_border="rgba(96, 165, 250, 0.3)",
            calendar_text="#f1f5f9",
            calendar_disabled="#4b5563",
            header_text="#6b7280",
            icon_color="#d1d5db",
            scrollbar_handle="rgba(255, 255, 255, 0.38)",
            scrollbar_handle_hover="rgba(255, 255, 255, 0.54)",
            selection_bg="rgba(96, 165, 250, 0.22)",
            checkbox_border="rgba(255, 255, 255, 0.3)",
            card_secondary_bg="rgba(96, 165, 250, 0.12)",
            card_secondary_border="rgba(96, 165, 250, 0.35)",
        )
    return ScenePalette(
        panel_bg="rgba(10, 16, 30, 0.9)",
        panel_text=SURFACE_TEXT_PRIMARY,
        panel_text_soft=SURFACE_TEXT_SECONDARY,
        panel_muted=SURFACE_TEXT_MUTED,
        panel_border="rgba(255, 255, 255, 0.1)",
        input_bg="rgba(15, 23, 42, 0.88)",
        input_text=SURFACE_TEXT_PRIMARY,
        input_border="rgba(255, 255, 255, 0.12)",
        overlay="rgba(15, 23, 42, 0.46)",
        frame_border="rgba(15, 23, 42, 0.18)",
        view_text=SURFACE_TEXT_SECONDARY,
        view_active_text=SURFACE_TEXT_PRIMARY,
        titlebar_bg="rgba(15, 23, 42, 0.1)",
        titlebar_surface="rgba(9, 14, 28, 0.66)",
        titlebar_button="rgba(9, 14, 28, 0.56)",
        titlebar_button_hover="rgba(255, 255, 255, 0.14)",
        theme_tag_bg="rgba(251, 191, 36, 0.18)",
        theme_tag_border="rgba(251, 191, 36, 0.34)",
        dialog_bg="#f8fafc",
        composer_bg="#f1f5f9",
        btn_primary_start="#f472b6",
        btn_primary_end="#a78bfa",
        btn_primary_hover_start="#fbcfe8",
        btn_primary_hover_end="#c4b5fd",
        btn_primary_border="rgba(244, 114, 182, 0.6)",
        btn_secondary_bg="rgba(59, 130, 246, 0.1)",
        btn_secondary_border="rgba(59, 130, 246, 0.3)",
        calendar_text="#1e293b",
        calendar_disabled="#94a3b8",
        header_text="#475569",
        icon_color="#64748b",
        scrollbar_handle="rgba(0, 0, 0, 0.32)",
        scrollbar_handle_hover="rgba(0, 0, 0, 0.50)",
        selection_bg="rgba(96, 165, 250, 0.18)",
        checkbox_border="rgba(15, 23, 42, 0.25)",
        card_secondary_bg="rgba(96, 165, 250, 0.08)",
        card_secondary_border="rgba(96, 165, 250, 0.35)",
    )

def text_style(color: str, size: int, weight: int | str = 400, *, background: str = "transparent") -> str:
    return f"color: {color}; font-size: {size}px; font-weight: {weight}; background: {background};"


def title_text_style(color: str, size: int, weight: int | str = "bold", *, background: str = "transparent") -> str:
    return f"color: {color}; font-size: {size}px; font-weight: {weight}; font-family: {TITLE_FONT_FAMILY}; background: {background};"


def surface_style(
    background: str,
    radius: int,
    *,
    border: str = SURFACE_BORDER,
    selector: str = "QFrame",
    hover_background: str | None = None,
    hover_border: str | None = None,
) -> str:
    body = f"{selector} {{ background: {background}; border-radius: {radius}px; border: 1px solid {border}; }}"
    if hover_background or hover_border:
        body += (
            f"{selector}:hover {{ background: {hover_background or background}; border: 1px solid {hover_border or border}; }}"
        )
    return body


def gradient_surface_style(
    start: str,
    end: str,
    radius: int,
    *,
    border: str = SURFACE_BORDER,
    selector: str = "QFrame",
) -> str:
    return (
        f"{selector} {{ background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 {start}, stop: 1 {end}); "
        f"border-radius: {radius}px; border: 1px solid {border}; }}"
    )


def chip_style(
    *,
    text_color: str = SURFACE_TEXT_PRIMARY,
    background: str = SURFACE_BG_LIGHT,
    border: str = SURFACE_BORDER_SOFT,
    radius: int = 10,
    padding: str = "4px 10px",
) -> str:
    return f"color: {text_color}; background: {background}; border-radius: {radius}px; padding: {padding}; border: 1px solid {border};"


def build_app_stylesheet(is_dark_mode: bool, palette_override: ScenePalette | None = None) -> str:
    palette = palette_override or scene_palette(is_dark_mode)
    return f"""
* {{
    font-family: {BODY_FONT_FAMILY};
}}

#appRoot {{
    background: transparent;
    color: {palette.panel_text};
}}

#sidebarPanel {{
    background: {palette.panel_bg};
    border-right: 1px solid {palette.panel_border};
}}

#mainPanel {{
    background: transparent;
}}

#detailTabs::pane {{
    background: transparent;
}}

#rightPanelContainer {{
    background: {palette.panel_bg};
    border-left: 1px solid {palette.panel_border};
}}

QDialog {{
    background: {palette.dialog_bg};
    border: 1px solid {SURFACE_BORDER_STRONG};
    border-radius: 12px;
    color: {palette.panel_text};
}}

QMenuBar,
QStatusBar,
QToolBar {{
    background: transparent;
    color: {SURFACE_TEXT_MUTED};
    border: none;
}}

QMenuBar {{
    padding: 6px 10px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 8px 12px;
    border-radius: 8px;
}}

QMenuBar::item:selected {{
    background: {SURFACE_BG_LIGHT};
}}

QToolButton,
QPushButton {{
    background: {SURFACE_BG_FLOAT};
    color: {SURFACE_TEXT_PRIMARY};
    border: 1px solid {SURFACE_BORDER_STRONG};
    border-radius: 12px;
    padding: 8px 14px;
}}

QToolButton:hover,
QPushButton:hover {{
    background: rgba(255, 255, 255, 0.16);
    color: {SURFACE_TEXT_PRIMARY};
}}

QPushButton[role="primary"] {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 {palette.btn_primary_start},
        stop: 1 {palette.btn_primary_end}
    );
    color: {SURFACE_TEXT_PRIMARY};
    border: 1px solid {palette.btn_primary_border};
    border-radius: 12px;
    padding: 8px 16px;
    font-weight: bold;
}}

QPushButton[role="primary"]:hover {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 {palette.btn_primary_hover_start},
        stop: 1 {palette.btn_primary_hover_end}
    );
}}

QPushButton[role="secondary"] {{
    background: {palette.btn_secondary_bg};
    color: {SURFACE_TEXT_PRIMARY};
    border: 1px solid {palette.btn_secondary_border};
}}

QPushButton[role="secondary"]:hover {{
    background: {palette.btn_secondary_border};
    border: 1px solid {palette.btn_secondary_border};
}}

QPushButton[role="ghost"] {{
    background: rgba(255, 255, 255, 0.06);
    color: {SURFACE_TEXT_PRIMARY};
    border: 1px solid {SURFACE_BORDER_STRONG};
}}

QPushButton[role="ghost"]:hover {{
    background: rgba(255, 255, 255, 0.14);
    color: {SURFACE_TEXT_PRIMARY};
}}

QFrame#topHeader,
#contextStrip,
#sidebarPanel,
#mainPanel,
QTabWidget#detailTabs {{
    background: transparent;
    border: none;
}}

QTabWidget#detailTabs::pane {{
    background: transparent;
    border: none;
}}

#boardTitle {{
    color: {SURFACE_TEXT_PRIMARY};
    font-size: 24px;
    font-weight: 700;
}}

#boardSubtitle {{
    color: {SURFACE_TEXT_MUTED};
    font-size: 13px;
}}

QGroupBox {{
    border: none;
    margin-top: 24px;
    padding-top: 12px;
    background: transparent;
    color: {SURFACE_TEXT_MUTED};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 0px;
    padding: 0px;
    color: {SURFACE_TEXT_MUTED};
    font-size: 13px;
    font-weight: bold;
}}

#viewCard {{
    background: rgba(255, 255, 255, 0.035);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    color: {SURFACE_TEXT_SECONDARY};
}}

#viewCard:hover {{
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
}}

#viewCard[role="secondary"] {{
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 {palette.card_secondary_bg}, stop: 1 {palette.btn_secondary_bg});
    border: 1px solid {palette.card_secondary_border};
}}

#viewCardTitle {{
    color: {SURFACE_TEXT_SECONDARY};
    font-size: 14px;
    font-weight: bold;
    padding-left: 4px;
}}

#viewCard[role="secondary"] #viewCardTitle {{
    color: {SURFACE_TEXT_PRIMARY};
}}

#viewCardCount {{
    color: {SURFACE_TEXT_SECONDARY};
    font-size: 12px;
    font-weight: bold;
    background: {SURFACE_BG_FLOAT};
    border-radius: 11px;
    padding: 4px 8px;
}}

#viewCard[role="secondary"] #viewCardCount {{
    color: {SURFACE_TEXT_PRIMARY};
    background: rgba(255, 255, 255, 0.10);
}}

QTabWidget::pane {{
    border: none;
    background: transparent;
}}

QTabBar::tab {{
    background: transparent;
    color: {SURFACE_TEXT_MUTED};
    padding: 8px 16px;
    border: none;
    font-size: 14px;
}}

QTabBar::tab:selected {{
    color: {SURFACE_TEXT_PRIMARY};
    font-weight: bold;
    border-bottom: 2px solid {palette.btn_primary_start};
}}

QTabBar::tab:hover {{
    color: {SURFACE_TEXT_SECONDARY};
}}

QLineEdit,
QComboBox,
QSpinBox,
QPlainTextEdit,
QTextEdit,
QListWidget,
QTreeWidget {{
    background: transparent;
    border: none;
    color: {SURFACE_TEXT_SECONDARY};
    selection-background-color: {palette.selection_bg};
    selection-color: {SURFACE_TEXT_PRIMARY};
}}

QLineEdit,
QComboBox,
QSpinBox {{
    background: {palette.input_bg};
    border: 1px solid {palette.input_border};
    border-radius: 8px;
    padding: 8px 12px;
    color: {palette.input_text};
    font-size: 14px;
}}

QPlainTextEdit,
QTextEdit,
QListWidget,
QTreeWidget {{
    font-size: 14px;
}}

QComboBox::drop-down {{
    width: 26px;
    border: none;
    background: transparent;
}}

QComboBox::down-arrow {{
    image: none;
    border: none;
}}

QComboBox QAbstractItemView {{
    background: #0c1222;
    border: 1px solid {SURFACE_BORDER_STRONG};
    border-radius: 4px;
    color: {SURFACE_TEXT_PRIMARY};
    selection-background-color: {palette.selection_bg};
    selection-color: {SURFACE_TEXT_PRIMARY};
    outline: none;
    padding: 4px;
}}

QLineEdit::placeholder,
QTextEdit::placeholder,
QPlainTextEdit::placeholder {{
    color: #a8b8cc;
}}

QLineEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QPlainTextEdit:focus,
QTextEdit:focus {{
    background: {SURFACE_BG_LIGHT};
    border: 1px solid {SURFACE_BORDER_STRONG};
}}

QAbstractItemView {{
    background: {SURFACE_BG_SOFT};
    color: {SURFACE_TEXT_PRIMARY};
    selection-background-color: {palette.selection_bg};
    selection-color: {SURFACE_TEXT_PRIMARY};
    outline: none;
    border: 1px solid {SURFACE_BORDER_STRONG};
    border-radius: 4px;
}}

QHeaderView::section {{
    background: transparent;
    color: {palette.header_text};
    border: none;
    border-bottom: 1px solid {SURFACE_BORDER_SOFT};
    padding: 8px;
    font-size: 12px;
    font-weight: bold;
}}

QSplitter::handle {{
    background-color: transparent;
    width: 1px;
}}

QSplitter::handle:hover {{
    background-color: {SURFACE_BG_FLOAT};
}}

#statsHint {{
    color: {SURFACE_TEXT_MUTED};
    font-size: 13px;
    line-height: 1.5;
}}

QListWidget::item {{
    padding: 12px 16px;
    border-bottom: 1px solid {SURFACE_BORDER_SOFT};
    min-height: 40px;
    margin: 4px 8px;
    border-radius: 8px;
    background: {SURFACE_BG_LIGHT};
}}

QTreeWidget::item {{
    padding: 8px 16px;
    border-bottom: 1px solid {SURFACE_BORDER_SOFT};
    min-height: 36px;
    background: transparent;
}}

QTreeWidget::item:hover,
QListWidget::item:hover {{
    background: {SURFACE_BG_LIGHT};
}}

QTreeWidget::item:selected {{
    background: {palette.selection_bg};
    border-left: 3px solid {palette.btn_primary_start};
    border-top-left-radius: 6px;
    border-bottom-left-radius: 6px;
}}

QCalendarWidget QWidget {{
    alternate-background-color: {SURFACE_BG_SOFT};
    background-color: {SURFACE_BG_SOFT};
}}

QCalendarWidget QAbstractItemView:enabled {{
    background-color: {SURFACE_BG_SOFT};
    color: {palette.calendar_text};
    selection-background-color: {palette.btn_primary_start};
    selection-color: {SURFACE_TEXT_PRIMARY};
    border-radius: 8px;
}}

QCalendarWidget QAbstractItemView:disabled {{
    color: {palette.calendar_disabled};
}}

QCalendarWidget QToolButton {{
    color: {SURFACE_TEXT_PRIMARY};
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 4px;
}}

QCalendarWidget QToolButton:hover {{
    background-color: {SURFACE_BG_FLOAT};
}}

QCalendarWidget QMenu {{
    background-color: {SURFACE_BG};
    border: 1px solid {SURFACE_BORDER_STRONG};
    border-radius: 8px;
    color: {SURFACE_TEXT_SECONDARY};
}}

QCalendarWidget QSpinBox {{
    background-color: transparent;
    border: none;
    color: {SURFACE_TEXT_PRIMARY};
    border-radius: 4px;
}}

QTreeWidget::item:selected,
QListWidget::item:selected {{
    background: {palette.selection_bg};
    color: {SURFACE_TEXT_PRIMARY};
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-left: 3px solid {palette.btn_primary_start};
    border-top-left-radius: 6px;
    border-bottom-left-radius: 6px;
    outline: none;
}}

QTreeWidget::item:focus,
QListWidget::item:focus {{
    outline: none;
    border: none;
}}

QTreeWidget {{
    alternate-background-color: transparent;
    outline: 0;
}}

QTreeView {{
    background: transparent;
    border: none;
    outline: none;
    show-decoration-selected: 1;
}}

QTreeView::branch {{
    background: transparent;
}}

QTreeView::branch:selected {{
    background: {palette.selection_bg};
}}

QTreeView::branch:hover {{
    background: {SURFACE_BG_LIGHT};
}}

QScrollBar:vertical {{
    width: 10px;
    background: transparent;
}}

QScrollBar::handle:vertical {{
    background: {palette.scrollbar_handle};
    min-height: 28px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: {palette.scrollbar_handle_hover};
}}

QScrollBar:horizontal {{
    height: 10px;
    background: transparent;
}}

QScrollBar::handle:horizontal {{
    background: {palette.scrollbar_handle};
    min-width: 28px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {palette.scrollbar_handle_hover};
}}

QScrollBar::add-line,
QScrollBar::sub-line,
QScrollBar::add-page,
QScrollBar::sub-page {{
    background: none;
    height: 0;
    width: 0;
}}

QCheckBox,
QTreeView {{
    color: {palette.icon_color};
}}

QCheckBox::indicator,
QTreeWidget::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 10px;
    border: 2px solid {palette.checkbox_border};
    background: transparent;
    margin-right: 8px;
}}

QTreeWidget::indicator:checked {{
    background: {palette.btn_primary_start};
    border: 2px solid {palette.btn_primary_start};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {palette.checkbox_border};
}}

QCheckBox::indicator:checked {{
    background: {palette.btn_primary_start};
    border: 2px solid {palette.btn_primary_start};
}}

QCheckBox::indicator:hover,
QTreeView::indicator:hover {{
    border: 2px solid {palette.btn_primary_start};
    background: {palette.selection_bg};
}}

QMessageBox,
QDialog {{
    background: {palette.dialog_bg};
}}

#focusTimerLabel {{
    color: {SURFACE_TEXT_PRIMARY};
    letter-spacing: 2px;
    qproperty-alignment: AlignCenter;
    padding: 10px 0;
    font-family: "JetBrains Mono", "Roboto Mono", monospace;
    font-size: 48px;
    font-weight: bold;
}}

#focusProgressBar {{
    background: {SURFACE_BG_LIGHT};
    border: none;
    border-radius: 4px;
    height: 8px;
}}

#composerWrapper {{
    background: {palette.composer_bg};
    border-radius: 16px;
    border: 1px solid {SURFACE_BORDER_SOFT};
}}

#composerTitle {{
    color: {SURFACE_TEXT_PRIMARY};
    font-size: 16px;
    font-weight: bold;
}}

#composerCloseBtn {{
    background: transparent;
    color: {SURFACE_TEXT_MUTED};
    font-size: 16px;
    border-radius: 14px;
    padding: 0;
}}

#composerCloseBtn:hover {{
    background: {SURFACE_BG_FLOAT};
    color: {SURFACE_TEXT_PRIMARY};
}}

#composerNameInput {{
    background: transparent;
    border: none;
    border-bottom: 2px solid {SURFACE_BORDER_STRONG};
    color: {SURFACE_TEXT_PRIMARY};
    font-size: 20px;
    font-weight: bold;
    padding: 8px 0;
    border-radius: 0;
}}

#composerNameInput:focus {{
    border-bottom: 2px solid {palette.btn_primary_start};
    background: transparent;
}}

#composerDetailsInput {{
    background: {SURFACE_BG_LIGHT};
    border: 1px solid {SURFACE_BORDER_SOFT};
    border-radius: 8px;
    padding: 12px;
    font-size: 14px;
}}
"""
