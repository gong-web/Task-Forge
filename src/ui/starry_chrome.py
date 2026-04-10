from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

from PyQt6.QtCore import QByteArray, QPoint, QRect, QRectF, QSize, QStringListModel, QDate, QDateTime, QTime, Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCalendarWidget,
    QCheckBox,
    QComboBox,
    QDialog,
    QCompleter,
    QDateTimeEdit,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.theme import BODY_FONT_FAMILY, TITLE_FONT_FAMILY, rgba


@dataclass
class StarryPalette:
    sky_top: str = "#050b15"
    sky_bottom: str = "#0b1526"
    panel_top: str = "#0c1422"
    panel_bottom: str = "#111b2f"
    panel_edge: str = "rgba(168, 187, 214, 0.14)"
    panel_edge_soft: str = "rgba(168, 187, 214, 0.08)"
    line: str = "rgba(151, 169, 196, 0.18)"
    line_soft: str = "rgba(151, 169, 196, 0.10)"
    text_primary: str = "#ecf2fb"
    text_secondary: str = "#c7d4e6"
    text_muted: str = "#8ea0ba"
    text_dim: str = "#6f819b"
    accent: str = "#8ca7d4"
    accent_strong: str = "#c8d5ee"
    accent_soft: str = "rgba(140, 167, 212, 0.18)"
    accent_line: str = "rgba(140, 167, 212, 0.34)"
    brass: str = "#d7c4a2"
    brass_soft: str = "rgba(215, 196, 162, 0.14)"
    success: str = "#a7c6b0"
    warning: str = "#d8c296"
    danger: str = "#c9999e"
    glass: str = "rgba(255, 255, 255, 0.04)"
    field_fill: str = "rgba(12, 20, 33, 0.56)"
    field_fill_hover: str = "rgba(16, 26, 43, 0.72)"
    field_border: str = "rgba(214, 224, 238, 0.12)"
    field_border_focus: str = "rgba(200, 213, 238, 0.42)"
    button_fill: str = "rgba(17, 28, 46, 0.72)"
    button_fill_hover: str = "rgba(24, 38, 60, 0.84)"
    button_fill_active: str = "rgba(48, 73, 108, 0.82)"
    scroll_handle: str = "rgba(193, 203, 220, 0.40)"
    scroll_handle_hover: str = "rgba(214, 222, 236, 0.60)"
    overlay: str = "rgba(3, 7, 13, 0.68)"
    star_soft: str = "rgba(213, 223, 239, 0.38)"
    star_strong: str = "rgba(236, 242, 251, 0.86)"
    separator: str = "rgba(172, 188, 212, 0.16)"


PALETTE = StarryPalette()


def set_starry_palette(palette: StarryPalette) -> None:
    for field_name in PALETTE.__dataclass_fields__:
        setattr(PALETTE, field_name, getattr(palette, field_name))


TITLE_FONT = TITLE_FONT_FAMILY
BODY_FONT = BODY_FONT_FAMILY


def font_rule(size: int, weight: int | str = 500, *, family: str = BODY_FONT) -> str:
    return f"font-size: {size}px; font-weight: {weight}; font-family: {family};"


HEADER_CREST_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="240" height="72" viewBox="0 0 240 72" fill="none">
  <rect x="1" y="1" width="238" height="70" rx="18" stroke="rgba(200,213,238,0.32)"/>
  <path d="M20 36H70" stroke="rgba(140,167,212,0.36)" stroke-width="1.2"/>
  <path d="M170 36H220" stroke="rgba(140,167,212,0.36)" stroke-width="1.2"/>
  <circle cx="120" cy="36" r="18" stroke="rgba(215,196,162,0.75)" stroke-width="1.4"/>
  <circle cx="120" cy="36" r="10" stroke="rgba(200,213,238,0.45)" stroke-width="1.2"/>
  <circle cx="120" cy="36" r="2.2" fill="rgba(236,242,251,0.92)"/>
  <path d="M120 17V11" stroke="rgba(215,196,162,0.78)" stroke-width="1.4" stroke-linecap="round"/>
  <path d="M120 61V55" stroke="rgba(215,196,162,0.78)" stroke-width="1.4" stroke-linecap="round"/>
  <path d="M101 36H95" stroke="rgba(215,196,162,0.78)" stroke-width="1.4" stroke-linecap="round"/>
  <path d="M145 36H139" stroke="rgba(215,196,162,0.78)" stroke-width="1.4" stroke-linecap="round"/>
  <path d="M132.5 23.5L136.7 19.3" stroke="rgba(215,196,162,0.78)" stroke-width="1.4" stroke-linecap="round"/>
  <path d="M107.5 48.5L103.3 52.7" stroke="rgba(215,196,162,0.78)" stroke-width="1.4" stroke-linecap="round"/>
  <path d="M132.5 48.5L136.7 52.7" stroke="rgba(215,196,162,0.78)" stroke-width="1.4" stroke-linecap="round"/>
  <path d="M107.5 23.5L103.3 19.3" stroke="rgba(215,196,162,0.78)" stroke-width="1.4" stroke-linecap="round"/>
  <circle cx="86" cy="18" r="1.4" fill="rgba(236,242,251,0.42)"/>
  <circle cx="153" cy="14" r="1.2" fill="rgba(236,242,251,0.48)"/>
  <circle cx="162" cy="54" r="1.6" fill="rgba(236,242,251,0.38)"/>
  <circle cx="78" cy="50" r="1.1" fill="rgba(236,242,251,0.34)"/>
</svg>
"""


SECTION_DIVIDER_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="640" height="26" viewBox="0 0 640 26" fill="none">
  <path d="M1 13H260" stroke="rgba(151,169,196,0.18)"/>
  <path d="M380 13H639" stroke="rgba(151,169,196,0.18)"/>
  <circle cx="320" cy="13" r="9" stroke="rgba(215,196,162,0.66)" stroke-width="1.2"/>
  <circle cx="320" cy="13" r="3" fill="rgba(236,242,251,0.86)"/>
  <circle cx="300" cy="13" r="1.2" fill="rgba(236,242,251,0.42)"/>
  <circle cx="340" cy="13" r="1.2" fill="rgba(236,242,251,0.42)"/>
</svg>
"""


FIELD_GLYPH_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64" fill="none">
  <rect x="4" y="4" width="56" height="56" rx="18" stroke="rgba(200,213,238,0.26)"/>
  <circle cx="32" cy="32" r="15.5" stroke="rgba(140,167,212,0.52)"/>
  <circle cx="32" cy="32" r="6" stroke="rgba(215,196,162,0.68)"/>
  <path d="M32 10V18" stroke="rgba(215,196,162,0.72)" stroke-linecap="round"/>
  <path d="M32 46V54" stroke="rgba(215,196,162,0.72)" stroke-linecap="round"/>
  <path d="M10 32H18" stroke="rgba(215,196,162,0.72)" stroke-linecap="round"/>
  <path d="M46 32H54" stroke="rgba(215,196,162,0.72)" stroke-linecap="round"/>
  <circle cx="17" cy="17" r="1.2" fill="rgba(236,242,251,0.58)"/>
  <circle cx="47" cy="20" r="1.5" fill="rgba(236,242,251,0.38)"/>
  <circle cx="43" cy="46" r="1.1" fill="rgba(236,242,251,0.52)"/>
  <circle cx="19" cy="45" r="1.1" fill="rgba(236,242,251,0.34)"/>
</svg>
"""


EMPTY_FILE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64" fill="none">
    <rect x="15" y="8" width="34" height="48" rx="12" stroke="rgba(200,213,238,0.24)" stroke-width="1.4"/>
    <path d="M39 8V21H49" stroke="rgba(200,213,238,0.24)" stroke-width="1.4" stroke-linejoin="round"/>
    <path d="M23 31H41" stroke="rgba(140,167,212,0.36)" stroke-width="1.6" stroke-linecap="round"/>
    <path d="M23 39H37" stroke="rgba(140,167,212,0.28)" stroke-width="1.6" stroke-linecap="round"/>
    <circle cx="48" cy="49" r="7.5" fill="rgba(140,167,212,0.14)" stroke="rgba(140,167,212,0.30)" stroke-width="1.2"/>
    <path d="M48 45.8V52.2" stroke="rgba(200,213,238,0.48)" stroke-width="1.4" stroke-linecap="round"/>
    <path d="M44.8 49H51.2" stroke="rgba(200,213,238,0.48)" stroke-width="1.4" stroke-linecap="round"/>
</svg>
"""


BUTTON_BADGE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="180" height="52" viewBox="0 0 180 52" fill="none">
  <rect x="1" y="1" width="178" height="50" rx="14" stroke="rgba(200,213,238,0.28)"/>
  <path d="M21 26H67" stroke="rgba(151,169,196,0.20)"/>
  <path d="M113 26H159" stroke="rgba(151,169,196,0.20)"/>
  <circle cx="90" cy="26" r="8.5" stroke="rgba(215,196,162,0.70)"/>
  <circle cx="90" cy="26" r="2.3" fill="rgba(236,242,251,0.88)"/>
</svg>
"""


STAR_POINTS: tuple[tuple[float, float, float], ...] = (
    (0.06, 0.10, 1.2),
    (0.09, 0.16, 1.6),
    (0.14, 0.08, 1.0),
    (0.18, 0.14, 1.3),
    (0.23, 0.06, 1.0),
    (0.26, 0.18, 1.7),
    (0.31, 0.10, 1.1),
    (0.35, 0.07, 1.4),
    (0.39, 0.16, 1.1),
    (0.42, 0.09, 1.8),
    (0.46, 0.14, 1.0),
    (0.49, 0.05, 1.2),
    (0.54, 0.12, 1.6),
    (0.59, 0.08, 1.1),
    (0.63, 0.15, 1.3),
    (0.67, 0.06, 1.2),
    (0.72, 0.13, 1.0),
    (0.75, 0.18, 1.5),
    (0.81, 0.09, 1.3),
    (0.86, 0.06, 1.6),
    (0.90, 0.16, 1.0),
    (0.94, 0.10, 1.2),
    (0.07, 0.24, 1.0),
    (0.11, 0.28, 1.3),
    (0.16, 0.20, 1.8),
    (0.21, 0.26, 1.1),
    (0.25, 0.22, 1.0),
    (0.29, 0.30, 1.5),
    (0.34, 0.25, 1.2),
    (0.37, 0.20, 1.1),
    (0.41, 0.28, 1.7),
    (0.45, 0.22, 1.0),
    (0.50, 0.30, 1.1),
    (0.56, 0.22, 1.5),
    (0.61, 0.26, 1.0),
    (0.66, 0.20, 1.2),
    (0.70, 0.28, 1.4),
    (0.74, 0.23, 1.0),
    (0.80, 0.27, 1.3),
    (0.84, 0.21, 1.0),
    (0.89, 0.26, 1.7),
    (0.93, 0.23, 1.2),
    (0.05, 0.38, 1.3),
    (0.09, 0.44, 1.0),
    (0.14, 0.35, 1.7),
    (0.18, 0.41, 1.1),
    (0.23, 0.33, 1.0),
    (0.27, 0.39, 1.4),
    (0.30, 0.45, 1.0),
    (0.35, 0.34, 1.1),
    (0.39, 0.42, 1.5),
    (0.42, 0.37, 1.2),
    (0.47, 0.44, 1.0),
    (0.51, 0.36, 1.8),
    (0.56, 0.41, 1.1),
    (0.60, 0.35, 1.3),
    (0.64, 0.43, 1.0),
    (0.68, 0.39, 1.4),
    (0.73, 0.34, 1.0),
    (0.77, 0.45, 1.2),
    (0.82, 0.38, 1.7),
    (0.87, 0.34, 1.0),
    (0.92, 0.41, 1.3),
    (0.96, 0.36, 1.1),
    (0.06, 0.55, 1.0),
    (0.10, 0.49, 1.3),
    (0.15, 0.57, 1.1),
    (0.19, 0.51, 1.5),
    (0.24, 0.58, 1.0),
    (0.28, 0.52, 1.2),
    (0.32, 0.60, 1.6),
    (0.37, 0.48, 1.0),
    (0.41, 0.56, 1.4),
    (0.46, 0.50, 1.0),
    (0.52, 0.59, 1.1),
    (0.55, 0.48, 1.7),
    (0.59, 0.54, 1.0),
    (0.64, 0.60, 1.2),
    (0.68, 0.50, 1.5),
    (0.73, 0.57, 1.0),
    (0.78, 0.49, 1.1),
    (0.81, 0.58, 1.6),
    (0.86, 0.53, 1.0),
    (0.90, 0.60, 1.4),
    (0.95, 0.50, 1.0),
    (0.04, 0.70, 1.3),
    (0.08, 0.64, 1.0),
    (0.13, 0.72, 1.6),
    (0.17, 0.66, 1.1),
    (0.22, 0.74, 1.0),
    (0.26, 0.68, 1.2),
    (0.31, 0.76, 1.5),
    (0.36, 0.65, 1.0),
    (0.40, 0.71, 1.4),
    (0.45, 0.77, 1.0),
    (0.49, 0.67, 1.7),
    (0.54, 0.74, 1.1),
    (0.58, 0.69, 1.0),
    (0.63, 0.76, 1.3),
    (0.67, 0.64, 1.0),
    (0.72, 0.71, 1.4),
    (0.76, 0.77, 1.2),
    (0.81, 0.66, 1.0),
    (0.85, 0.73, 1.6),
    (0.89, 0.68, 1.1),
    (0.94, 0.75, 1.0),
    (0.07, 0.86, 1.0),
    (0.12, 0.81, 1.2),
    (0.16, 0.89, 1.5),
    (0.21, 0.83, 1.0),
    (0.25, 0.90, 1.1),
    (0.30, 0.84, 1.7),
    (0.35, 0.88, 1.0),
    (0.39, 0.82, 1.3),
    (0.44, 0.91, 1.0),
    (0.48, 0.85, 1.4),
    (0.53, 0.89, 1.2),
    (0.57, 0.81, 1.0),
    (0.62, 0.90, 1.5),
    (0.66, 0.84, 1.0),
    (0.71, 0.87, 1.3),
    (0.75, 0.92, 1.0),
    (0.80, 0.83, 1.6),
    (0.84, 0.88, 1.1),
    (0.89, 0.82, 1.0),
    (0.93, 0.90, 1.4),
)


CONSTELLATION_SEGMENTS: tuple[tuple[tuple[float, float], tuple[float, float]], ...] = (
    ((0.08, 0.18), (0.15, 0.22)),
    ((0.15, 0.22), (0.20, 0.15)),
    ((0.20, 0.15), (0.27, 0.24)),
    ((0.62, 0.16), (0.68, 0.22)),
    ((0.68, 0.22), (0.74, 0.18)),
    ((0.74, 0.18), (0.80, 0.27)),
    ((0.18, 0.68), (0.25, 0.62)),
    ((0.25, 0.62), (0.31, 0.72)),
    ((0.70, 0.70), (0.77, 0.63)),
    ((0.77, 0.63), (0.84, 0.76)),
    ((0.46, 0.12), (0.52, 0.18)),
    ((0.52, 0.18), (0.56, 0.12)),
)


def set_layout_margins(layout: QLayout, left: int, top: int, right: int, bottom: int, spacing: int) -> None:
    layout.setContentsMargins(left, top, right, bottom)
    layout.setSpacing(spacing)


class FlowLayout(QLayout):
    def __init__(self, parent: QWidget | None = None, *, h_spacing: int = 8, v_spacing: int = 8) -> None:
        super().__init__(parent)
        self._items: list = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item) -> None:
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect: QRect, *, test_only: bool) -> int:
        margins = self.contentsMargins()
        effective_rect = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0

        for item in self._items:
            size_hint = item.sizeHint()
            next_x = x + size_hint.width() + self._h_spacing
            if line_height > 0 and next_x - self._h_spacing > effective_rect.right() + 1:
                x = effective_rect.x()
                y += line_height + self._v_spacing
                next_x = x + size_hint.width() + self._h_spacing
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), size_hint))
            x = next_x
            line_height = max(line_height, size_hint.height())

        return y + line_height - rect.y() + margins.bottom()


def apply_shadow(widget: QWidget, *, blur: int = 38, alpha: int = 110, offset_y: int = 14) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, offset_y)
    effect.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(effect)


def svg_pixmap(svg_text: str, width: int, height: int) -> QPixmap:
    renderer = QSvgRenderer(QByteArray(svg_text.encode("utf-8")))
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


class SvgStamp(QLabel):
    def __init__(self, svg_text: str, *, width: int, height: int, parent=None) -> None:
        super().__init__(parent)
        self.setPixmap(svg_pixmap(svg_text, width, height))
        self.setFixedSize(width, height)
        self.setStyleSheet("background: transparent; border: none;")


class StarDivider(QLabel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setPixmap(svg_pixmap(SECTION_DIVIDER_SVG, 640, 26))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background: transparent; border: none;")


class StarfieldSurface(QFrame):
    def __init__(self, *, radius: int = 28, surface_mode: str = "starfield", parent=None) -> None:
        super().__init__(parent)
        self.radius = radius
        self.surface_mode = surface_mode
        self.backdrop_pixmap: Optional[QPixmap] = None
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("starfieldSurface")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet("background: transparent; border: none;")

    def set_backdrop_pixmap(self, pixmap: Optional[QPixmap]) -> None:
        if pixmap is None or pixmap.isNull():
            self.backdrop_pixmap = None
        else:
            self.backdrop_pixmap = QPixmap(pixmap)
        self.update()

    def paintEvent(self, a0) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)

        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), self.radius, self.radius)
        painter.setClipPath(path)

        if self.backdrop_pixmap is not None and not self.backdrop_pixmap.isNull():
            scaled = self.backdrop_pixmap.scaled(
                rect.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            offset_x = max(0, (scaled.width() - rect.width()) // 2)
            offset_y = max(0, (scaled.height() - rect.height()) // 2)
            painter.drawPixmap(rect.left(), rect.top(), scaled, offset_x, offset_y, rect.width(), rect.height())

        if self.surface_mode == "workspace":
            if self.backdrop_pixmap is not None and not self.backdrop_pixmap.isNull():
                painter.fillPath(path, QColor(6, 10, 18, 214))

            gradient = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.bottom())
            gradient.setColorAt(0.0, QColor(8, 12, 20, 238))
            gradient.setColorAt(0.48, QColor(11, 16, 28, 244))
            gradient.setColorAt(1.0, QColor(15, 21, 34, 248))
            painter.fillPath(path, gradient)

            top_sheen = QLinearGradient(rect.left(), rect.top(), rect.left(), rect.top() + rect.height() * 0.42)
            top_sheen.setColorAt(0.0, QColor(rgba(PALETTE.accent_strong, 18)))
            top_sheen.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.fillPath(path, top_sheen)

            cool_haze = QRadialGradient(
                rect.left() + rect.width() * 0.14,
                rect.top() + rect.height() * 0.10,
                rect.width() * 0.72,
            )
            cool_haze.setColorAt(0, QColor(rgba(PALETTE.accent, 14)))
            cool_haze.setColorAt(1, QColor(0, 0, 0, 0))
            painter.fillPath(path, cool_haze)

            warm_haze = QRadialGradient(
                rect.right() - rect.width() * 0.10,
                rect.bottom() - rect.height() * 0.06,
                rect.width() * 0.50,
            )
            warm_haze.setColorAt(0, QColor(rgba(PALETTE.brass, 8)))
            warm_haze.setColorAt(1, QColor(0, 0, 0, 0))
            painter.fillPath(path, warm_haze)

            painter.setPen(QPen(QColor(rgba(PALETTE.accent_strong, 14)), 1))
            painter.drawLine(rect.left() + 18, rect.top() + 16, rect.right() - 18, rect.top() + 16)
            painter.setPen(QPen(QColor(PALETTE.line_soft), 1))
            painter.drawRoundedRect(QRectF(rect), self.radius, self.radius)
        elif self.surface_mode == "natural":
            gradient = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.bottom())
            gradient.setColorAt(0.0, QColor(PALETTE.panel_top))
            gradient.setColorAt(0.58, QColor(PALETTE.panel_bottom))
            gradient.setColorAt(1.0, QColor(rgba(PALETTE.brass, 18)))
            painter.fillPath(path, gradient)

            warm_haze = QRadialGradient(
                rect.left() + rect.width() * 0.18,
                rect.top() + rect.height() * 0.18,
                rect.width() * 0.65,
            )
            warm_haze.setColorAt(0, QColor(rgba(PALETTE.brass, 14)))
            warm_haze.setColorAt(1, QColor(0, 0, 0, 0))
            painter.fillPath(path, warm_haze)

            cool_haze = QRadialGradient(
                rect.right() - rect.width() * 0.12,
                rect.top() + rect.height() * 0.10,
                rect.width() * 0.55,
            )
            cool_haze.setColorAt(0, QColor(rgba(PALETTE.accent, 11)))
            cool_haze.setColorAt(1, QColor(0, 0, 0, 0))
            painter.fillPath(path, cool_haze)

            top_plate = QRectF(
                rect.left() + 14,
                rect.top() + 14,
                rect.width() - 28,
                max(28.0, rect.height() * 0.28),
            )
            top_plate_path = QPainterPath()
            top_plate_path.addRoundedRect(top_plate, max(12, self.radius - 10), max(12, self.radius - 10))
            painter.fillPath(top_plate_path, QColor(rgba(PALETTE.accent_strong, 4)))

            lower_plate = QRectF(
                rect.left() + rect.width() * 0.06,
                rect.top() + rect.height() * 0.56,
                rect.width() * 0.88,
                max(22.0, rect.height() * 0.18),
            )
            lower_plate_path = QPainterPath()
            lower_plate_path.addRoundedRect(lower_plate, 18, 18)
            painter.fillPath(lower_plate_path, QColor(rgba(PALETTE.brass, 7)))

            painter.setPen(QPen(QColor(rgba(PALETTE.accent_strong, 14)), 1))
            painter.drawLine(rect.left() + 20, rect.top() + 18, rect.right() - 20, rect.top() + 18)
            painter.setPen(QPen(QColor(PALETTE.line_soft), 1))
            painter.drawRoundedRect(QRectF(rect), self.radius, self.radius)
        else:
            gradient = QLinearGradient(rect.left(), rect.top(), rect.left(), rect.bottom())
            gradient.setColorAt(0, QColor(PALETTE.panel_top))
            gradient.setColorAt(1, QColor(PALETTE.panel_bottom))
            painter.fillPath(path, gradient)

            radial = QRadialGradient(rect.right() - rect.width() * 0.18, rect.top() + rect.height() * 0.10, rect.width() * 0.55)
            radial.setColorAt(0, QColor(140, 167, 212, 18))
            radial.setColorAt(1, QColor(0, 0, 0, 0))
            painter.fillPath(path, radial)

            painter.setPen(QPen(QColor(PALETTE.line_soft), 1))
            painter.drawRoundedRect(QRectF(rect), self.radius, self.radius)

            star_color = QColor(PALETTE.star_soft)
            star_bright = QColor(PALETTE.star_strong)
            for idx, (px, py, size) in enumerate(STAR_POINTS):
                x = rect.left() + rect.width() * px
                y = rect.top() + rect.height() * py
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(star_bright if idx % 7 == 0 else star_color)
                painter.drawEllipse(QRectF(x, y, size, size))

            painter.setPen(QPen(QColor(200, 213, 238, 28), 1))
            for (x1, y1), (x2, y2) in CONSTELLATION_SEGMENTS:
                painter.drawLine(
                    int(rect.left() + rect.width() * x1),
                    int(rect.top() + rect.height() * y1),
                    int(rect.left() + rect.width() * x2),
                    int(rect.top() + rect.height() * y2),
                )

        painter.setClipping(False)
        painter.setPen(QPen(QColor(PALETTE.panel_edge), 1))
        painter.drawRoundedRect(QRectF(rect), self.radius, self.radius)
        painter.end()
        super().paintEvent(a0)


class StarryDialogShell(StarfieldSurface):
    def __init__(self, *, radius: int = 30, parent=None) -> None:
        super().__init__(radius=radius, parent=parent)
        apply_shadow(self, blur=44, alpha=140, offset_y=18)
        self.root_layout = QVBoxLayout(self)
        set_layout_margins(self.root_layout, 28, 24, 28, 20, 16)


class StarrySection(StarfieldSurface):
    def __init__(self, title: str, subtitle: str = "", *, minimum_height: int | None = 110, surface_mode: str = "starfield", parent=None) -> None:
        super().__init__(radius=24, surface_mode=surface_mode, parent=parent)
        if minimum_height is not None:
            self.setMinimumHeight(minimum_height)
        self.layout_ = QVBoxLayout(self)
        set_layout_margins(self.layout_, 18, 18, 18, 18, 12)

        head = QVBoxLayout()
        set_layout_margins(head, 0, 0, 0, 0, 2)
        tag = QLabel(title.upper())
        tag.setStyleSheet(
            f"background: transparent; color: {PALETTE.accent_strong}; {font_rule(13, 700)} letter-spacing: 0.8px;"
        )
        head.addWidget(tag)
        if subtitle:
            note = QLabel(subtitle)
            note.setWordWrap(True)
            note.setStyleSheet(
                f"background: transparent; color: {PALETTE.text_secondary}; {font_rule(12, 500)}"
            )
            head.addWidget(note)
        self.layout_.addLayout(head)
        divider = StarDivider()
        self.layout_.addWidget(divider)
        self.body = QVBoxLayout()
        set_layout_margins(self.body, 0, 0, 0, 0, 10)
        self.layout_.addLayout(self.body)


class StarryHeader(QWidget):
    def __init__(self, eyebrow: str, title: str, subtitle: str = "", *, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        set_layout_margins(layout, 0, 0, 0, 0, 6)

        top = QHBoxLayout()
        set_layout_margins(top, 0, 0, 0, 0, 12)
        crest = SvgStamp(HEADER_CREST_SVG, width=240, height=72)
        top.addWidget(crest, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        top.addStretch(1)
        layout.addLayout(top)

        eyebrow_label = QLabel(eyebrow.upper())
        eyebrow_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.accent}; {font_rule(12, 700)} letter-spacing: 1.8px;"
        )
        layout.addWidget(eyebrow_label)

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary}; {font_rule(30, 700, family=TITLE_FONT)}"
        )
        layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setWordWrap(True)
            subtitle_label.setStyleSheet(
                f"background: transparent; color: {PALETTE.text_secondary}; {font_rule(14, 500)}"
            )
            layout.addWidget(subtitle_label)


class StarryPill(QLabel):
    def __init__(self, text: str, *, tone: str = "accent", parent=None) -> None:
        super().__init__(text, parent)
        self.tone = tone
        self.refresh_theme()

    def refresh_theme(self) -> None:
        tones = {
            "accent": (rgba(PALETTE.accent, 30), rgba(PALETTE.accent, 86), PALETTE.accent_strong),
            "brass": (rgba(PALETTE.brass, 18), rgba(PALETTE.brass, 112), "#fde8b8"),
            "success": (rgba(PALETTE.success, 26), rgba(PALETTE.success, 94), PALETTE.success),
            "danger": (rgba(PALETTE.danger, 24), rgba(PALETTE.danger, 84), PALETTE.danger),
            "muted": (PALETTE.glass, PALETTE.field_border, PALETTE.text_secondary),
        }
        background, border, color = tones.get(self.tone, tones["accent"])
        self.setStyleSheet(
            f"background: {background}; border: 1px solid {border}; border-radius: 12px; color: {color}; padding: 4px 12px; {font_rule(13, 700)}"
        )


class StarryMetricRow(QWidget):
    def __init__(self, label: str, value: str, *, emphasis: bool = False, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        set_layout_margins(layout, 0, 0, 0, 0, 16)
        key = QLabel(label)
        key.setMinimumWidth(96)
        key.setWordWrap(True)
        key.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        key.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_muted}; {font_rule(13, 600)}"
        )
        val = QLabel(value)
        val.setWordWrap(True)
        val.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        val.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary if emphasis else PALETTE.text_secondary}; {font_rule(13, 700 if emphasis else 600)}"
        )
        val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        key.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        val.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(key, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(val, 1, Qt.AlignmentFlag.AlignTop)


class StarryMiniInfoCard(QFrame):
    def __init__(self, title: str, value: str = "", *, tone: str = "accent", parent=None) -> None:
        super().__init__(parent)
        tones = {
            "accent": (rgba(PALETTE.accent, 14), rgba(PALETTE.accent, 38), PALETTE.accent_strong),
            "brass": (rgba(PALETTE.brass, 16), rgba(PALETTE.brass, 42), PALETTE.brass),
            "success": (rgba(PALETTE.success, 18), rgba(PALETTE.success, 40), PALETTE.success),
            "muted": (PALETTE.glass, PALETTE.field_border, PALETTE.text_secondary),
        }
        background, border, value_color = tones.get(tone, tones["accent"])
        self.setStyleSheet(
            f"background: {background}; border: 1px solid {border}; border-radius: 18px;"
        )
        layout = QVBoxLayout(self)
        set_layout_margins(layout, 16, 14, 16, 14, 6)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_muted}; {font_rule(12, 700)} letter-spacing: 0.6px;"
        )
        self.value_label = QLabel(value or "—")
        self.value_label.setWordWrap(True)
        self.value_label.setStyleSheet(
            f"background: transparent; color: {value_color}; {font_rule(15, 800)}"
        )
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str, *, tone: str | None = None) -> None:
        self.value_label.setText(value or "—")
        if tone is not None:
            tones = {
                "accent": PALETTE.accent_strong,
                "brass": PALETTE.brass,
                "success": PALETTE.success,
                "muted": PALETTE.text_secondary,
            }
            self.value_label.setStyleSheet(
                f"background: transparent; color: {tones.get(tone, PALETTE.accent_strong)}; {font_rule(14, 700)}"
            )


class StarryReadOnlyField(QWidget):
    def __init__(self, label: str, value: str, *, multiline: bool = False, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        set_layout_margins(layout, 0, 0, 0, 0, 6)
        tag = QLabel(label)
        tag.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_muted}; {font_rule(12, 700)} letter-spacing: 1.1px;"
        )
        layout.addWidget(tag)
        value_frame = QFrame()
        value_frame.setStyleSheet(
            f"background: {PALETTE.field_fill}; border: 1px solid {PALETTE.field_border}; border-radius: 14px;"
        )
        inner = QVBoxLayout(value_frame)
        set_layout_margins(inner, 14, 12, 14, 12, 4)
        self.text = QLabel(value or "—")
        self.text.setWordWrap(True)
        self.text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.text.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary}; {font_rule(14, 500)}"
        )
        if multiline:
            self.text.setMinimumHeight(70)
            self.text.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        inner.addWidget(self.text)
        layout.addWidget(value_frame)

    def set_value(self, value: str) -> None:
        self.text.setText(value or "—")


class StarryLineEdit(QLineEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(44)
        self.refresh_theme()

    @staticmethod
    def _qss() -> str:
        return (
            f"QLineEdit {{ background: rgba(12, 20, 33, 0.68); border: 1px solid rgba(214, 224, 238, 0.18); border-radius: 16px; padding: 0 16px; color: {PALETTE.text_primary}; placeholder-text-color: rgba(255, 255, 255, 143); {font_rule(14, 500)} }}"
            f"QLineEdit:hover {{ background: {PALETTE.field_fill_hover}; }}"
            f"QLineEdit:focus {{ border: 1px solid rgba(200, 213, 238, 0.52); background: {PALETTE.field_fill_hover}; }}"
        )

    def refresh_theme(self) -> None:
        self.setStyleSheet(self._qss())


class StarryTextEdit(QTextEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.refresh_theme()

    @staticmethod
    def _qss() -> str:
        return (
            f"QTextEdit {{ background: rgba(12, 20, 33, 0.68); border: 1px solid rgba(214, 224, 238, 0.18); border-radius: 16px; padding: 12px 16px; color: {PALETTE.text_primary}; placeholder-text-color: rgba(255, 255, 255, 143); {font_rule(14, 500)} selection-background-color: {PALETTE.accent_soft}; }}"
            f"QTextEdit:hover {{ background: {PALETTE.field_fill_hover}; }}"
            f"QTextEdit:focus {{ border: 1px solid rgba(200, 213, 238, 0.52); background: {PALETTE.field_fill_hover}; }}"
        )

    def refresh_theme(self) -> None:
        self.setStyleSheet(self._qss())


class StarryComboBox(QComboBox):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(44)
        self.refresh_theme()

    @staticmethod
    def _qss() -> str:
        return (
            f"QComboBox {{ background: {PALETTE.field_fill}; border: 1px solid {PALETTE.field_border}; border-radius: 14px; padding: 0 44px 0 14px; color: {PALETTE.text_primary}; {font_rule(14, 500)} }}"
            f"QComboBox:hover {{ background: {PALETTE.field_fill_hover}; }}"
            f"QComboBox:focus {{ border: 1px solid {PALETTE.field_border_focus}; background: {PALETTE.field_fill_hover}; }}"
            "QComboBox::drop-down { width: 30px; border: none; background: transparent; }"
            "QComboBox::down-arrow { image: none; width: 0; height: 0; }"
            f"QComboBox QAbstractItemView {{ background: {PALETTE.panel_bottom}; color: {PALETTE.text_primary}; border: 1px solid {PALETTE.field_border}; padding: 6px; outline: none; selection-background-color: {PALETTE.accent_soft}; }}"
        )

    def refresh_theme(self) -> None:
        self.setStyleSheet(self._qss())

    def paintEvent(self, e) -> None:
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        arrow_color = QColor(PALETTE.accent_strong if self.isEnabled() else PALETTE.text_muted)
        painter.setBrush(arrow_color)
        cx = self.width() - 18
        cy = self.height() // 2
        arrow = QPainterPath()
        arrow.moveTo(cx - 5, cy - 3)
        arrow.lineTo(cx + 5, cy - 3)
        arrow.lineTo(cx, cy + 4)
        arrow.closeSubpath()
        painter.drawPath(arrow)
        painter.end()


class StarrySuggestionComboBox(StarryComboBox):
    textChanged = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._suggestions: list[str] = []
        self._completer_model = QStringListModel(self)
        completer = QCompleter(self._completer_model, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setCompleter(completer)
        self.currentTextChanged.connect(self.textChanged.emit)
        self.refresh_theme()

    def text(self) -> str:
        return self.currentText()

    def setText(self, value: str) -> None:
        self.setCurrentText(value or "")

    def set_placeholder_text(self, value: str) -> None:
        line_edit = self.lineEdit()
        if line_edit is not None:
            line_edit.setPlaceholderText(value)

    def set_suggestions(self, values: Sequence[str]) -> None:
        current = self.currentText()
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw in values:
            text = str(raw or "").strip()
            if not text:
                continue
            key = text.casefold()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(text)
        self._suggestions = cleaned
        self.blockSignals(True)
        self.clear()
        if cleaned:
            self.addItems(cleaned)
        self.setCurrentText(current)
        self.blockSignals(False)
        self._completer_model.setStringList(cleaned)

    def refresh_theme(self) -> None:
        super().refresh_theme()
        line_edit = self.lineEdit()
        if line_edit is not None:
            line_edit.setStyleSheet(
                f"QLineEdit {{ background: transparent; border: none; padding: 0 6px 0 0; color: {PALETTE.text_primary}; placeholder-text-color: rgba(255, 255, 255, 153); selection-background-color: {PALETTE.accent_soft}; {font_rule(14, 500)} }}"
            )
        completer = self.completer()
        if completer is not None and completer.popup() is not None:
            completer.popup().setStyleSheet(
                f"background: {PALETTE.panel_bottom}; color: {PALETTE.text_primary}; border: 1px solid {PALETTE.field_border}; padding: 6px; outline: none; selection-background-color: {PALETTE.accent_soft};"
            )


class StarryDateTimeEdit(QDateTimeEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._picker_title = "选择时间"
        self._picker_subtitle = "先选日期，再设置具体时间。"
        self.setMinimumHeight(44)
        self.setCalendarPopup(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setReadOnly(True)
        self.refresh_theme()

    def configure_picker(self, title: str, subtitle: str = "") -> None:
        self._picker_title = title or "选择时间"
        self._picker_subtitle = subtitle or "先选日期，再设置具体时间。"

    def refresh_theme(self) -> None:
        self.setStyleSheet(
            f"QDateTimeEdit {{ background: rgba(12, 20, 33, 0.68); border: 1px solid rgba(214, 224, 238, 0.18); border-radius: 16px; padding: 0 38px 0 16px; color: {PALETTE.text_primary}; {font_rule(14, 500)} }}"
            f"QDateTimeEdit:hover {{ background: {PALETTE.field_fill_hover}; }}"
            f"QDateTimeEdit:focus {{ border: 1px solid rgba(200, 213, 238, 0.52); background: {PALETTE.field_fill_hover}; }}"
            "QDateTimeEdit::drop-down { width: 30px; border: none; background: transparent; }"
            "QDateTimeEdit::down-arrow { image: none; width: 0; height: 0; }"
        )

    def mousePressEvent(self, a0) -> None:
        if a0 is not None and a0.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self._open_picker()
            a0.accept()
            return
        super().mousePressEvent(a0)

    def keyPressEvent(self, a0) -> None:
        if a0 is not None and self.isEnabled() and a0.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space}:
            self._open_picker()
            a0.accept()
            return
        super().keyPressEvent(a0)

    def wheelEvent(self, a0) -> None:
        if a0 is not None:
            a0.ignore()

    def _open_picker(self) -> None:
        dialog = StarryDateTimeDialog(
            self,
            current=self.dateTime(),
            minimum=self.minimumDateTime(),
            maximum=self.maximumDateTime(),
            title=self._picker_title,
            subtitle=self._picker_subtitle,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.setDateTime(dialog.selected_date_time())

    def paintEvent(self, e) -> None:
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        arrow_color = QColor(PALETTE.accent_strong if self.isEnabled() else PALETTE.text_muted)
        painter.setBrush(arrow_color)
        cx = self.width() - 18
        cy = self.height() // 2
        arrow = QPainterPath()
        arrow.moveTo(cx - 5, cy - 3)
        arrow.lineTo(cx + 5, cy - 3)
        arrow.lineTo(cx, cy + 4)
        arrow.closeSubpath()
        painter.drawPath(arrow)
        painter.end()


class StarryDateTimeDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        current: QDateTime,
        minimum: QDateTime | None = None,
        maximum: QDateTime | None = None,
        title: str = "选择时间",
        subtitle: str = "先选日期，再设置具体时间。",
    ) -> None:
        super().__init__(parent)
        self._minimum = minimum if minimum is not None and minimum.isValid() else QDateTime()
        self._maximum = maximum if maximum is not None and maximum.isValid() else QDateTime()
        initial = current if current.isValid() else QDateTime.currentDateTime()

        self.setModal(True)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.setStyleSheet(
            f"QDialog {{ background: {PALETTE.panel_top}; border: 1px solid {PALETTE.field_border}; border-radius: 22px; }}"
            f"QPushButton {{ background: {PALETTE.button_fill}; border: 1px solid {PALETTE.field_border}; border-radius: 14px; color: {PALETTE.text_primary}; {font_rule(13, 700)} padding: 8px 14px; }}"
            f"QPushButton:hover {{ background: {PALETTE.button_fill_hover}; border: 1px solid {PALETTE.accent_line}; }}"
        )

        layout = QVBoxLayout(self)
        set_layout_margins(layout, 22, 20, 22, 20, 14)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"background: transparent; color: {PALETTE.text_primary}; {font_rule(18, 800)}")
        layout.addWidget(title_label)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet(f"background: transparent; color: {PALETTE.text_secondary}; {font_rule(13, 600)}")
        layout.addWidget(subtitle_label)

        self.preview_label = QLabel("")
        self.preview_label.setStyleSheet(
            f"background: {PALETTE.accent_soft}; border: 1px solid {PALETTE.accent_line}; border-radius: 14px; color: {PALETTE.text_primary}; padding: 10px 12px; {font_rule(13, 700)}"
        )
        layout.addWidget(self.preview_label)

        self.range_hint_label = QLabel("")
        self.range_hint_label.setWordWrap(True)
        self.range_hint_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_muted}; {font_rule(12, 600)}"
        )
        layout.addWidget(self.range_hint_label)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(False)
        self.calendar.setSelectedDate(initial.date())
        self.calendar.setStyleSheet(
            f"QCalendarWidget QWidget {{ alternate-background-color: transparent; color: {PALETTE.text_primary}; background: transparent; }}"
            f"QCalendarWidget QToolButton {{ color: {PALETTE.text_primary}; background: {PALETTE.button_fill}; border: 1px solid {PALETTE.field_border}; border-radius: 10px; padding: 6px 10px; }}"
            f"QCalendarWidget QToolButton:hover {{ background: {PALETTE.button_fill_hover}; border: 1px solid {PALETTE.accent_line}; }}"
            f"QCalendarWidget QAbstractItemView:enabled {{ color: {PALETTE.text_primary}; background: {PALETTE.panel_bottom}; selection-background-color: {PALETTE.accent_soft}; selection-color: {PALETTE.text_primary}; }}"
        )
        if self._minimum.isValid():
            self.calendar.setMinimumDate(self._minimum.date())
        if self._maximum.isValid():
            self.calendar.setMaximumDate(self._maximum.date())
        layout.addWidget(self.calendar)

        time_row = QHBoxLayout()
        set_layout_margins(time_row, 0, 0, 0, 0, 10)
        time_label = QLabel("具体时间")
        time_label.setStyleSheet(f"background: transparent; color: {PALETTE.text_secondary}; {font_rule(13, 700)}")
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setSuffix(" 时")
        self.hour_spin.setValue(initial.time().hour())
        self.hour_spin.setMinimumHeight(42)
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setSuffix(" 分")
        self.minute_spin.setValue(initial.time().minute())
        self.minute_spin.setMinimumHeight(42)
        spin_qss = (
            f"QSpinBox {{ background: {PALETTE.field_fill}; border: 1px solid {PALETTE.field_border}; border-radius: 14px; padding: 0 14px; color: {PALETTE.text_primary}; {font_rule(14, 700)} }}"
            f"QSpinBox:hover {{ background: {PALETTE.field_fill_hover}; }}"
            f"QSpinBox:focus {{ border: 1px solid {PALETTE.field_border_focus}; background: {PALETTE.field_fill_hover}; }}"
            "QSpinBox::up-button, QSpinBox::down-button { width: 16px; border: none; background: transparent; }"
            "QSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right; }"
            "QSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right; }"
        )
        self.hour_spin.setStyleSheet(spin_qss)
        self.minute_spin.setStyleSheet(spin_qss)
        time_row.addWidget(time_label)
        time_row.addWidget(self.hour_spin)
        colon_label = QLabel(":")
        colon_label.setStyleSheet(f"background: transparent; color: {PALETTE.text_primary}; {font_rule(18, 800)}")
        time_row.addWidget(colon_label)
        time_row.addWidget(self.minute_spin)
        time_row.addStretch(1)
        layout.addLayout(time_row)

        quick_row = QHBoxLayout()
        set_layout_margins(quick_row, 0, 0, 0, 0, 8)
        self.quick_time_buttons: list[tuple[QPushButton, int]] = []
        for label, hour, minute in (("上午 09:00", 9, 0), ("下午 14:00", 14, 0), ("晚上 20:00", 20, 0)):
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, h=hour, m=minute: self._set_quick_time(h, m))
            quick_row.addWidget(button)
            self.quick_time_buttons.append((button, hour * 60 + minute))
        layout.addLayout(quick_row)

        actions = QHBoxLayout()
        set_layout_margins(actions, 0, 2, 0, 0, 10)
        now_button = QPushButton("当前时间")
        now_button.clicked.connect(self._set_now)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        apply_button = QPushButton("应用")
        apply_button.clicked.connect(self.accept)
        actions.addWidget(now_button)
        actions.addStretch(1)
        actions.addWidget(cancel_button)
        actions.addWidget(apply_button)
        layout.addLayout(actions)

        self.calendar.selectionChanged.connect(self._sync_time_range)
        self.hour_spin.valueChanged.connect(self._handle_time_component_changed)
        self.minute_spin.valueChanged.connect(self._handle_time_component_changed)
        self._sync_time_range()

    def selected_date_time(self) -> QDateTime:
        return QDateTime(self.calendar.selectedDate(), QTime(self.hour_spin.value(), self.minute_spin.value()))

    def _set_now(self) -> None:
        now = QDateTime.currentDateTime()
        if self._minimum.isValid() and now < self._minimum:
            now = self._minimum
        if self._maximum.isValid() and now > self._maximum:
            now = self._maximum
        self.calendar.setSelectedDate(now.date())
        self._set_selected_minutes(now.time().hour() * 60 + now.time().minute())

    def _set_quick_time(self, hour: int, minute: int) -> None:
        self._set_selected_minutes(hour * 60 + minute)

    def _allowed_range_for_date(self, selected_date: QDate) -> tuple[QTime, QTime]:
        min_time = QTime(0, 0)
        max_time = QTime(23, 59)
        if self._minimum.isValid() and selected_date == self._minimum.date():
            min_time = self._minimum.time()
        if self._maximum.isValid() and selected_date == self._maximum.date():
            max_time = self._maximum.time()
        return min_time, max_time

    def _sync_time_range(self) -> None:
        selected_date = self.calendar.selectedDate()
        min_time, max_time = self._allowed_range_for_date(selected_date)
        min_minutes = min_time.hour() * 60 + min_time.minute()
        max_minutes = max_time.hour() * 60 + max_time.minute()
        current_minutes = self.hour_spin.value() * 60 + self.minute_spin.value()
        if current_minutes < min_minutes:
            current_minutes = min_minutes
        if current_minutes > max_minutes:
            current_minutes = max_minutes
        self.range_hint_label.setText(f"当前可选时间范围：{min_time.toString('HH:mm')} - {max_time.toString('HH:mm')}")
        self._set_selected_minutes(current_minutes, clamp=True)
        self._sync_quick_buttons(min_minutes, max_minutes)
        self._update_preview()

    def _set_selected_minutes(self, total_minutes: int, *, clamp: bool = True) -> None:
        selected_date = self.calendar.selectedDate()
        min_time, max_time = self._allowed_range_for_date(selected_date)
        min_minutes = min_time.hour() * 60 + min_time.minute()
        max_minutes = max_time.hour() * 60 + max_time.minute()
        if clamp:
            total_minutes = max(min_minutes, min(max_minutes, total_minutes))
        hour_value = total_minutes // 60
        minute_value = total_minutes % 60
        minute_min = min_time.minute() if hour_value == min_time.hour() else 0
        minute_max = max_time.minute() if hour_value == max_time.hour() else 59
        self.hour_spin.blockSignals(True)
        self.minute_spin.blockSignals(True)
        self.hour_spin.setRange(min_time.hour(), max_time.hour())
        self.hour_spin.setValue(hour_value)
        self.minute_spin.setRange(minute_min, minute_max)
        self.minute_spin.setValue(max(minute_min, min(minute_max, minute_value)))
        self.hour_spin.blockSignals(False)
        self.minute_spin.blockSignals(False)
        self._update_preview()

    def _handle_time_component_changed(self, *_args) -> None:
        selected_date = self.calendar.selectedDate()
        min_time, max_time = self._allowed_range_for_date(selected_date)
        hour_value = self.hour_spin.value()
        minute_min = min_time.minute() if hour_value == min_time.hour() else 0
        minute_max = max_time.minute() if hour_value == max_time.hour() else 59
        if self.minute_spin.minimum() != minute_min or self.minute_spin.maximum() != minute_max:
            current_minute = self.minute_spin.value()
            self.minute_spin.blockSignals(True)
            self.minute_spin.setRange(minute_min, minute_max)
            self.minute_spin.setValue(max(minute_min, min(minute_max, current_minute)))
            self.minute_spin.blockSignals(False)
        self._update_preview()

    def _sync_quick_buttons(self, min_minutes: int, max_minutes: int) -> None:
        for button, total_minutes in self.quick_time_buttons:
            button.setEnabled(min_minutes <= total_minutes <= max_minutes)

    def _update_preview(self) -> None:
        chosen = self.selected_date_time()
        self.preview_label.setText(f"当前选择：{chosen.toString('yyyy-MM-dd HH:mm')}")


class StarrySpinBox(QSpinBox):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(44)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        self.setStyleSheet(
            f"QSpinBox {{ background: {PALETTE.field_fill}; border: 1px solid {PALETTE.field_border}; border-radius: 14px; padding: 0 14px; color: {PALETTE.text_primary}; {font_rule(14, 500)} }}"
            f"QSpinBox:hover {{ background: {PALETTE.field_fill_hover}; }}"
            f"QSpinBox:focus {{ border: 1px solid {PALETTE.field_border_focus}; background: {PALETTE.field_fill_hover}; }}"
            "QSpinBox::up-button, QSpinBox::down-button { width: 0; height: 0; border: none; }"
        )


class StarryCheckBox(QCheckBox):
    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(text, parent)
        self.setMinimumHeight(44)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        self.setStyleSheet(
            f"QCheckBox {{ color: {PALETTE.text_secondary}; {font_rule(14, 600)} spacing: 10px; padding: 0; }}"
            f"QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px; border: 1px solid {PALETTE.field_border}; background: {PALETTE.field_fill}; }}"
            f"QCheckBox::indicator:unchecked:hover {{ background: {PALETTE.field_fill_hover}; }}"
            f"QCheckBox::indicator:checked {{ background: {PALETTE.button_fill_active}; border: 1px solid {PALETTE.accent_line}; }}"
        )

    def paintEvent(self, a0) -> None:
        super().paintEvent(a0)
        if not self.isChecked():
            return
        opt_rect = self.rect()
        marker = QRectF(4, (opt_rect.height() - 18) / 2, 18, 18)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(PALETTE.accent_strong), 1.8))
        painter.drawLine(int(marker.left() + 4), int(marker.top() + 10), int(marker.left() + 8), int(marker.top() + 13))
        painter.drawLine(int(marker.left() + 8), int(marker.top() + 13), int(marker.left() + 14), int(marker.top() + 5))
        painter.end()


class StarryActionButton(QPushButton):
    def __init__(self, text: str, *, kind: str = "secondary", parent=None) -> None:
        super().__init__(text, parent)
        self.kind = kind
        self.setMinimumHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_theme()

    def _qss(self) -> str:
        if self.kind == "primary":
            return (
                f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(139, 113, 88, 0.94), stop:0.58 rgba(106, 128, 161, 0.96), stop:1 rgba(81, 106, 145, 0.98)); border: 1px solid rgba(222, 230, 242, 0.28); border-radius: 16px; color: {PALETTE.text_primary}; {font_rule(14, 800)} padding: 0 22px; }}"
                f"QPushButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(149, 121, 95, 0.98), stop:0.58 rgba(117, 138, 172, 1.0), stop:1 rgba(90, 116, 156, 1.0)); border: 1px solid rgba(230, 236, 246, 0.34); }}"
                f"QPushButton:pressed {{ background: rgba(58, 75, 101, 0.98); border: 1px solid rgba(190, 201, 220, 0.28); }}"
            )
        if self.kind == "ghost":
            return (
                f"QPushButton {{ background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(214, 224, 238, 0.14); border-radius: 16px; color: {PALETTE.text_secondary}; {font_rule(14, 700)} padding: 0 18px; }}"
                f"QPushButton:hover {{ background: rgba(255, 255, 255, 0.07); border: 1px solid rgba(200, 213, 238, 0.22); color: {PALETTE.text_primary}; }}"
            )
        return (
            f"QPushButton {{ background: {PALETTE.button_fill}; border: 1px solid rgba(214, 224, 238, 0.16); border-radius: 16px; color: {PALETTE.text_secondary}; {font_rule(14, 700)} padding: 0 18px; }}"
            f"QPushButton:hover {{ background: {PALETTE.button_fill_hover}; border: 1px solid {PALETTE.accent_line}; }}"
        )

    def refresh_theme(self) -> None:
        self.setStyleSheet(self._qss())


class StarryTagChip(QFrame):
    removed = pyqtSignal(str)

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(parent)
        self._text = text
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout = QHBoxLayout(self)
        set_layout_margins(layout, 10, 6, 8, 6, 6)

        self.label = QLabel(text)
        self.label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary}; {font_rule(13, 700)}"
        )
        self.remove_button = QPushButton("x")
        self.remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_button.setFixedSize(18, 18)
        self.remove_button.clicked.connect(lambda: self.removed.emit(self._text))
        layout.addWidget(self.label)
        layout.addWidget(self.remove_button)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        self.setStyleSheet(
            f"background: rgba(255, 255, 255, 0.06); border: 1px solid {PALETTE.field_border}; border-radius: 12px;"
        )
        self.label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary}; {font_rule(13, 700)}"
        )
        self.remove_button.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; border-radius: 9px; color: {PALETTE.text_secondary}; {font_rule(12, 800)} padding: 0; }}"
            f"QPushButton:hover {{ background: rgba(255, 255, 255, 0.07); color: {PALETTE.text_primary}; }}"
        )


class StarryTagEditor(QWidget):
    textChanged = pyqtSignal(str)
    tagsChanged = pyqtSignal(list)

    def __init__(self, parent=None, *, max_tags: int = 6) -> None:
        super().__init__(parent)
        self._tags: list[str] = []
        self._suggestions: list[str] = []
        self._max_tags = max_tags
        self._placeholder_text = "输入标签后回车"
        self._completer_model = QStringListModel(self)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        set_layout_margins(layout, 0, 0, 0, 0, 6)

        self.tag_panel = QFrame(self)
        self.tag_panel.setObjectName("starryTagEditor")
        panel_layout = QVBoxLayout(self.tag_panel)
        set_layout_margins(panel_layout, 0, 0, 0, 0, 6)

        self.chips_host = QWidget(self.tag_panel)
        self.chips_host.setStyleSheet("background: transparent; border: none;")
        self.chips_host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.chips_layout = FlowLayout(self.chips_host, h_spacing=8, v_spacing=8)
        self.placeholder_label = QLabel("")
        self.placeholder_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_muted}; {font_rule(13, 600)}"
        )
        self.chips_layout.addWidget(self.placeholder_label)
        panel_layout.addWidget(self.chips_host)

        self.input_row = QWidget(self.tag_panel)
        self.input_row.setStyleSheet("background: transparent; border: none;")
        input_row_layout = QHBoxLayout(self.input_row)
        set_layout_margins(input_row_layout, 0, 0, 0, 0, 8)
        self.input = StarryLineEdit(self.input_row)
        self.input.setMinimumHeight(44)
        self.input.setPlaceholderText(self._placeholder_text)
        completer = QCompleter(self._completer_model, self.input)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.input.setCompleter(completer)
        self.input.returnPressed.connect(self._add_from_input)

        self.add_button = QPushButton("添加")
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_button.setMinimumHeight(0)
        self.add_button.setMinimumWidth(0)
        self.add_button.clicked.connect(self._add_from_input)
        input_row_layout.addWidget(self.input, 1)
        panel_layout.addWidget(self.input_row)

        layout.addWidget(self.tag_panel)
        self.refresh_theme()
        self._sync_input_state()
        self._refresh_chip_host_height()

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._computed_editor_height(width)

    def sizeHint(self) -> QSize:
        width = self.width() if self.width() > 0 else 420
        return QSize(max(260, width), self._computed_editor_height(width))

    def minimumSizeHint(self) -> QSize:
        return QSize(220, self._computed_editor_height(260))

    def showEvent(self, a0) -> None:
        super().showEvent(a0)
        self._refresh_chip_host_height()

    def resizeEvent(self, a0) -> None:
        super().resizeEvent(a0)
        self._refresh_chip_host_height()

    def text(self) -> str:
        return ", ".join(self._tags)

    def tags(self) -> list[str]:
        return list(self._tags)

    def setText(self, value: str) -> None:
        self.set_tags(self._split_tags(value), emit_signal=False)

    def set_placeholder_text(self, value: str) -> None:
        self._placeholder_text = value or "输入标签后回车"
        self._sync_input_state()

    def set_suggestions(self, values: Sequence[str]) -> None:
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw in values:
            text = str(raw or "").strip()
            if not text:
                continue
            key = text.casefold()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(text)
        self._suggestions = cleaned
        self._completer_model.setStringList(cleaned)

    def set_tags(self, values: Sequence[str], *, emit_signal: bool = True) -> None:
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw in values:
            text = str(raw or "").strip()
            if not text:
                continue
            key = text.casefold()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(text)
            if len(cleaned) >= self._max_tags:
                break
        changed = cleaned != self._tags
        self._tags = cleaned
        self._render_tags()
        self._sync_input_state()
        self.updateGeometry()
        if changed and emit_signal:
            self.tagsChanged.emit(self.tags())
            self.textChanged.emit(self.text())

    def refresh_theme(self) -> None:
        self.tag_panel.setStyleSheet(
            "QFrame#starryTagEditor { background: transparent; border: none; }"
            f"QFrame#starryTagEditor QLabel {{ background: transparent; border: none; }}"
        )
        self.placeholder_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_muted}; {font_rule(13, 600)}"
        )
        self.input.setStyleSheet(
            f"QLineEdit {{ background: rgba(13, 22, 36, 0.84); border: 1px solid rgba(214, 224, 238, 0.40); border-radius: 16px; padding: 0 16px; color: {PALETTE.text_primary}; placeholder-text-color: rgba(255, 255, 255, 184); {font_rule(14, 500)} }}"
            f"QLineEdit:hover {{ background: {PALETTE.field_fill_hover}; }}"
            f"QLineEdit:focus {{ background: {PALETTE.field_fill_hover}; border: 2px solid {PALETTE.field_border_focus}; }}"
        )
        completer = self.input.completer()
        if completer is not None and completer.popup() is not None:
            completer.popup().setStyleSheet(
                f"background: {PALETTE.panel_bottom}; color: {PALETTE.text_primary}; border: 1px solid {PALETTE.field_border}; padding: 6px; outline: none; selection-background-color: {PALETTE.accent_soft};"
            )
        self.add_button.hide()
        for index in range(self.chips_layout.count()):
            item = self.chips_layout.itemAt(index)
            widget = item.widget() if item is not None else None
            if isinstance(widget, StarryTagChip):
                widget.refresh_theme()

    def _split_tags(self, value: str | Sequence[str]) -> list[str]:
        if isinstance(value, str):
            raw_parts = value.replace("，", ",").replace("\n", ",").split(",")
            return [part.strip() for part in raw_parts if part.strip()]
        return [str(part or "").strip() for part in value if str(part or "").strip()]

    def _add_from_input(self) -> None:
        candidate_tags = self._split_tags(self.input.text())
        if not candidate_tags:
            return
        self.set_tags([*self._tags, *candidate_tags])
        self.input.clear()

    def _remove_tag(self, value: str) -> None:
        self.set_tags([tag for tag in self._tags if tag != value])
        self.input.setFocus()

    def _render_tags(self) -> None:
        while self.chips_layout.count():
            item = self.chips_layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                if widget is self.placeholder_label:
                    widget.hide()
                else:
                    widget.deleteLater()
        if not self._tags:
            self.chips_host.hide()
            self._refresh_chip_host_height()
            return
        self.chips_host.show()
        self.placeholder_label.hide()
        for tag in self._tags:
            chip = StarryTagChip(tag, self.chips_host)
            chip.removed.connect(self._remove_tag)
            self.chips_layout.addWidget(chip)
        self._refresh_chip_host_height()

    def _sync_input_state(self) -> None:
        can_add_more = len(self._tags) < self._max_tags
        self.input.setEnabled(can_add_more)
        self.add_button.setEnabled(can_add_more)
        self.add_button.hide()
        if can_add_more:
            self.input.setPlaceholderText(self._placeholder_text)
        else:
            self.input.setPlaceholderText(f"最多 {self._max_tags} 个标签")

    def _refresh_chip_host_height(self) -> None:
        if not self._tags:
            self.chips_host.setFixedHeight(0)
            self.chips_host.updateGeometry()
            self.tag_panel.updateGeometry()
            self.updateGeometry()
            return
        target_width = self.chips_host.width() or self.tag_panel.width() or self.width() or 420
        target_height = max(36, self.chips_layout.heightForWidth(target_width))
        self.chips_host.setFixedHeight(target_height)
        self.chips_host.updateGeometry()
        self.tag_panel.updateGeometry()
        self.updateGeometry()

    def _computed_editor_height(self, width: int) -> int:
        margins = self.contentsMargins()
        outer_spacing = 6
        panel_width = max(220, width - margins.left() - margins.right())
        chips_height = 0
        if self._tags:
            chips_height = max(36, self.chips_layout.heightForWidth(panel_width)) + outer_spacing
        input_height = max(self.input.minimumHeight(), self.input.sizeHint().height())
        return margins.top() + chips_height + input_height + margins.bottom()


class StarryChoiceButton(QPushButton):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setFixedHeight(40)
        self.setMinimumWidth(82)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        self.setStyleSheet(
            f"QPushButton {{ background: transparent; border: 1px solid transparent; border-radius: 14px; color: {rgba(PALETTE.text_primary, 140)}; {font_rule(13, 700)} padding: 0 16px; }}"
            f"QPushButton:hover {{ background: rgba(255, 255, 255, 0.05); border: 1px solid {rgba(PALETTE.accent, 38)}; color: {rgba(PALETTE.text_primary, 210)}; }}"
            f"QPushButton:checked {{ background: {PALETTE.button_fill_active}; border: 1px solid {PALETTE.accent_line}; color: #ffffff; }}"
            f"QPushButton:focus {{ border: 1px solid {rgba(PALETTE.accent_strong, 104)}; }}"
        )


class StarryFieldGroup(QWidget):
    def __init__(self, title: str, helper: str = "", parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        set_layout_margins(layout, 0, 0, 0, 0, 6)
        tag = QLabel(title)
        tag.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_muted}; {font_rule(12, 700)} letter-spacing: 1.1px;"
        )
        layout.addWidget(tag)
        if helper:
            tip = QLabel(helper)
            tip.setWordWrap(True)
            tip.setStyleSheet(
                f"background: transparent; color: {PALETTE.text_secondary}; {font_rule(13, 500)}"
            )
            layout.addWidget(tip)
        self.body = QVBoxLayout()
        set_layout_margins(self.body, 0, 0, 0, 0, 0)
        layout.addLayout(self.body)

    def addWidget(self, widget: QWidget) -> None:
        self.body.addWidget(widget)


class StarryInfoList(QListWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"QListWidget {{ background: {PALETTE.field_fill}; border: 1px solid {PALETTE.field_border}; border-radius: 16px; color: {PALETTE.text_primary}; {font_rule(14, 500)} padding: 8px; }}"
            f"QListWidget::item {{ padding: 10px 12px; border-bottom: 1px solid {PALETTE.line_soft}; }}"
            "QListWidget::item:selected { background: transparent; }"
            f"QScrollBar:vertical {{ width: 5px; background: transparent; border: none; margin: 0; }}"
            f"QScrollBar::handle:vertical {{ background: {PALETTE.scroll_handle}; border-radius: 3px; min-height: 24px; }}"
            f"QScrollBar::handle:vertical:hover {{ background: {PALETTE.scroll_handle_hover}; }}"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }"
        )


class StarryScrollArea(QScrollArea):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            f"QScrollBar:vertical {{ width: 5px; background: transparent; border: none; margin: 0; }}"
            f"QScrollBar::handle:vertical {{ background: {PALETTE.scroll_handle}; border-radius: 3px; min-height: 24px; }}"
            f"QScrollBar::handle:vertical:hover {{ background: {PALETTE.scroll_handle_hover}; }}"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }"
        )


class StarryStatGrid(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.grid = QGridLayout(self)
        set_layout_margins(self.grid, 0, 0, 0, 0, 10)
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(10)
        self._row = 0

    def add_row(self, label_left: str, value_left: str, label_right: str = "", value_right: str = "") -> None:
        self.grid.addWidget(StarryMetricRow(label_left, value_left), self._row, 0)
        if label_right:
            self.grid.addWidget(StarryMetricRow(label_right, value_right), self._row, 1)
        self._row += 1


class StarryCloseButton(StarryActionButton):
    def __init__(self, parent=None) -> None:
        super().__init__("✕", kind="ghost", parent=parent)
        self.setFixedSize(42, 42)
        self.setStyleSheet(
            f"QPushButton {{ background: {PALETTE.button_fill}; border: 1px solid {PALETTE.field_border}; border-radius: 14px; color: {PALETTE.text_secondary}; {font_rule(15, 700)} }}"
            f"QPushButton:hover {{ background: rgba(80, 44, 52, 0.72); border: 1px solid rgba(201, 153, 158, 0.48); color: {PALETTE.text_primary}; }}"
        )


class StarryTitleLine(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        set_layout_margins(layout, 0, 0, 0, 0, 4)
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary}; {font_rule(30, 700, family=TITLE_FONT)}"
        )
        layout.addWidget(title_label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setWordWrap(True)
            sub.setStyleSheet(
                f"background: transparent; color: {PALETTE.text_secondary}; {font_rule(13, 500)}"
            )
            layout.addWidget(sub)


class StarryTagRow(QWidget):
    def __init__(self, texts: Sequence[tuple[str, str]], parent=None, *, wrap: bool = False) -> None:
        super().__init__(parent)
        self._wrap = wrap
        self.layout_ = FlowLayout(self, h_spacing=8, v_spacing=8) if wrap else QHBoxLayout(self)
        set_layout_margins(self.layout_, 0, 0, 0, 0, 8)
        self._texts: list[tuple[str, str]] = []
        self.set_texts(texts)

    def set_texts(self, texts: Sequence[tuple[str, str]]) -> None:
        self._texts = list(texts)
        while self.layout_.count():
            item = self.layout_.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for text, tone in texts:
            self.layout_.addWidget(StarryPill(text, tone=tone))
        if not self._wrap:
            self.layout_.addSpacing(0)

    def refresh_theme(self) -> None:
        self.set_texts(self._texts)


class StarryChoiceStrip(QWidget):
    valueChanged = pyqtSignal(str)

    def __init__(self, options: Sequence[str], current: str, *, parent=None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(46)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons: dict[str, StarryChoiceButton] = {}
        layout = QHBoxLayout(self)
        set_layout_margins(layout, 0, 0, 0, 0, 0)
        self.track = QFrame(self)
        self.track.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.track.setFixedHeight(46)
        track_layout = QHBoxLayout(self.track)
        set_layout_margins(track_layout, 3, 3, 3, 3, 6)
        for option in options:
            btn = StarryChoiceButton(option)
            btn.setChecked(option == current)
            btn.toggled.connect(lambda checked, value=option: self._emit_value_changed(value, checked))
            self.group.addButton(btn)
            self.buttons[option] = btn
            track_layout.addWidget(btn)
        layout.addWidget(self.track, 1)
        self.refresh_theme()

    def current_value(self, fallback: str) -> str:
        return next((value for value, btn in self.buttons.items() if btn.isChecked()), fallback)

    def set_current_value(self, value: str) -> None:
        button = self.buttons.get(value)
        if button is not None:
            button.setChecked(True)

    def refresh_theme(self) -> None:
        self.track.setStyleSheet(
            f"background: {PALETTE.field_fill}; border: 1px solid {PALETTE.field_border}; border-radius: 16px;"
        )
        for button in self.buttons.values():
            button.refresh_theme()

    def _emit_value_changed(self, value: str, checked: bool) -> None:
        if checked:
            self.valueChanged.emit(value)


class StarryReadOnlyText(QFrame):
    def __init__(self, text: str, *, min_height: int = 90, empty_height: int = 76, empty_text: str = "暂无说明", parent=None) -> None:
        super().__init__(parent)
        self._filled_min_height = min_height
        self._empty_min_height = empty_height
        self._empty_text = empty_text
        self._showing_empty_state = False
        self.setStyleSheet(
            f"background: rgba(12, 20, 33, 0.34); border: 1px solid rgba(214, 224, 238, 0.08); border-radius: 16px;"
        )
        layout = QVBoxLayout(self)
        set_layout_margins(layout, 14, 12, 14, 12, 6)
        self.label = QLabel("")
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary}; {font_rule(14, 500)}"
        )
        self.label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.empty_state = QWidget()
        empty_layout = QVBoxLayout(self.empty_state)
        set_layout_margins(empty_layout, 0, 4, 0, 4, 6)
        self.empty_icon = SvgStamp(EMPTY_FILE_SVG, width=28, height=28)
        self.empty_label = QLabel(empty_text)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(
            f"background: transparent; color: rgba(255, 255, 255, 0.42); {font_rule(13, 600)}"
        )
        empty_layout.addWidget(self.empty_icon, 0, Qt.AlignmentFlag.AlignHCenter)
        empty_layout.addWidget(self.empty_label, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.label)
        layout.addWidget(self.empty_state)
        self.set_text(text, empty_text=empty_text)

    @property
    def showing_empty_state(self) -> bool:
        return self._showing_empty_state

    def set_text(self, text: str, *, empty_text: str | None = None) -> None:
        content = (text or "").strip()
        placeholder = empty_text or self._empty_text
        self._empty_text = placeholder
        self.empty_label.setText(placeholder)
        if content:
            self._showing_empty_state = False
            self.empty_state.hide()
            self.label.show()
            self.label.setText(content)
            self.label.setMinimumHeight(self._filled_min_height)
            self.setMinimumHeight(self._filled_min_height + 12)
            return
        self._showing_empty_state = True
        self.label.hide()
        self.empty_state.show()
        self.label.setMinimumHeight(0)
        self.setMinimumHeight(self._empty_min_height)

    def setText(self, text: str) -> None:  # noqa: N802
        self.set_text(text)


def info_section_title(text: str) -> QLabel:
    label = QLabel(text.upper())
    label.setStyleSheet(
        f"background: transparent; color: {PALETTE.accent_strong}; {font_rule(12, 700)} letter-spacing: 1.2px;"
    )
    return label


def decorated_panel_layout(panel: QFrame, *, margins: tuple[int, int, int, int] = (16, 14, 16, 16), spacing: int = 10) -> QVBoxLayout:
    panel.setStyleSheet(
        f"background: {PALETTE.field_fill}; border: 1px solid {PALETTE.field_border}; border-radius: 18px;"
    )
    layout = QVBoxLayout(panel)
    set_layout_margins(layout, margins[0], margins[1], margins[2], margins[3], spacing)
    return layout


def status_tone(completed: bool, overdue: bool = False) -> str:
    if completed:
        return "success"
    if overdue:
        return "danger"
    return "accent"


def priority_tone(priority: str) -> str:
    mapping = {
        "高": "danger",
        "中": "brass",
        "低": "accent",
    }
    return mapping.get(priority, "accent")


def tone_for_kind(kind: str) -> tuple[str, str]:
    if kind == "danger":
        return PALETTE.danger, rgba(PALETTE.danger, 28)
    if kind == "success":
        return PALETTE.success, rgba(PALETTE.success, 28)
    if kind == "brass":
        return PALETTE.brass, rgba(PALETTE.brass, 28)
    return PALETTE.accent_strong, PALETTE.accent_soft


class StarryBulletList(QFrame):
    def __init__(self, items: Sequence[str], *, empty_text: str = "暂无内容", parent=None) -> None:
        super().__init__(parent)
        layout = decorated_panel_layout(self)
        values = list(items)
        if not values:
            values = [empty_text]
        for text in values:
            row = QHBoxLayout()
            set_layout_margins(row, 0, 0, 0, 0, 10)
            dot = QLabel("•")
            dot.setStyleSheet(
                f"background: transparent; color: {PALETTE.brass}; {font_rule(14, 700)}"
            )
            label = QLabel(text)
            label.setWordWrap(True)
            label.setStyleSheet(
                f"background: transparent; color: {PALETTE.text_primary}; {font_rule(14, 500)}"
            )
            row.addWidget(dot, 0, Qt.AlignmentFlag.AlignTop)
            row.addWidget(label, 1)
            layout.addLayout(row)


class StarryKVPanel(QFrame):
    def __init__(self, entries: Sequence[tuple[str, str]], parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        self.layout_ = QVBoxLayout(self)
        set_layout_margins(self.layout_, 0, 0, 0, 0, 8)
        self.set_rows(entries)

    def set_rows(self, entries: Sequence[tuple[str, str]]) -> None:
        while self.layout_.count():
            item = self.layout_.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if not entries:
            empty = QLabel("暂无信息")
            empty.setStyleSheet(
                f"background: transparent; color: {PALETTE.text_muted}; {font_rule(13, 600)}"
            )
            self.layout_.addWidget(empty)
            return
        for index, (key, value) in enumerate(entries):
            self.layout_.addWidget(StarryMetricRow(key, value))
            if index != len(entries) - 1:
                divider = QFrame()
                divider.setFixedHeight(1)
                divider.setStyleSheet(f"background: {PALETTE.line_soft}; border: none;")
                self.layout_.addWidget(divider)


class StarryFormScaffold(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.layout_ = QVBoxLayout(self)
        set_layout_margins(self.layout_, 0, 0, 0, 0, 14)

    def add_section(self, section: StarrySection) -> None:
        self.layout_.addWidget(section)


def make_stamp_row(items: Sequence[QWidget]) -> QWidget:
    widget = QWidget()
    layout = QHBoxLayout(widget)
    set_layout_margins(layout, 0, 0, 0, 0, 8)
    for item in items:
        layout.addWidget(item)
    layout.addStretch(1)
    return widget


__all__ = [
    "PALETTE",
    "StarryActionButton",
    "StarryBulletList",
    "StarryCheckBox",
    "StarryChoiceStrip",
    "StarryCloseButton",
    "StarryComboBox",
    "StarryDateTimeEdit",
    "StarryDialogShell",
    "StarryFieldGroup",
    "StarryHeader",
    "StarryInfoList",
    "StarryKVPanel",
    "StarryLineEdit",
    "StarryMetricRow",
    "StarryPill",
    "StarryReadOnlyField",
    "StarryReadOnlyText",
    "StarryScrollArea",
    "StarrySection",
    "StarrySuggestionComboBox",
    "StarrySpinBox",
    "StarryStatGrid",
    "StarryTagEditor",
    "StarryTagRow",
    "StarryTextEdit",
    "StarryTitleLine",
    "apply_shadow",
    "decorated_panel_layout",
    "info_section_title",
    "make_stamp_row",
    "priority_tone",
    "rgba",
    "set_layout_margins",
    "status_tone",
]
