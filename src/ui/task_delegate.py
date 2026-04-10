import sys
from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QApplication, QStyle
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QIcon, QPainterPath
from PyQt6.QtCore import Qt, QRect, QSize, QPointF
from datetime import datetime

TREE_GROUP_ROLE = 1000
TREE_GROUP_SUBTITLE_ROLE = 1001
TREE_GROUP_ACCENT_ROLE = 1002
TREE_GROUP_LEVEL_ROLE = 1003
TREE_STATUS_TEXT_ROLE = 1010
TREE_STATUS_COLOR_ROLE = 1011
TREE_TIMELINE_COLOR_ROLE = 1020

class TaskItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_manager = None
        
    def _get_icon_manager(self):
        if self.icon_manager is None:
            # Import locally to avoid circular dependencies if any
            from ui.icon_manager import IconManager
            self.icon_manager = IconManager()
        return self.icon_manager

    def _theme_profile(self):
        parent = self.parent()
        window = parent.window() if parent is not None else None
        return getattr(window, "theme_profile", None)

    def _ui_palette(self):
        parent = self.parent()
        window = parent.window() if parent is not None else None
        return getattr(window, "ui_palette", None)

    def _paint_group_header(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        level = int(index.siblingAtColumn(0).data(TREE_GROUP_LEVEL_ROLE) or 0)
        accent = QColor(str(index.siblingAtColumn(0).data(TREE_GROUP_ACCENT_ROLE) or "#60a5fa"))

        # Only draw background and accent line for column 0; other columns stay transparent
        if index.column() == 0:
            rect = option.rect.adjusted(4 + level * 10, 6 if level == 0 else 4, -4, -4)
            fill = QColor(accent)
            fill.setAlpha(22 if level == 0 else 14)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fill)
            painter.drawRoundedRect(rect, 14 if level == 0 else 12, 14 if level == 0 else 12)
            painter.setPen(QPen(QColor(accent), 1))
            painter.drawLine(rect.left() + 2, rect.bottom(), rect.right() - 2, rect.bottom())

            title = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
            subtitle = str(index.data(TREE_GROUP_SUBTITLE_ROLE) or "")
            title_rect = QRect(rect.left() + 14, rect.top() + (8 if level == 0 else 6), rect.width() - 28, 18)
            subtitle_rect = QRect(rect.left() + 14, rect.top() + (26 if level == 0 else 22), rect.width() - 28, 16)

            title_font = QFont(option.font)
            title_font.setPointSize(11 if level == 0 else 10)
            title_font.setBold(True)
            painter.setFont(title_font)
            painter.setPen(accent)
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)

            subtitle_font = QFont(option.font)
            subtitle_font.setPointSize(9 if level == 0 else 8)
            painter.setFont(subtitle_font)
            painter.setPen(QColor("#b7c6d8"))
            painter.drawText(subtitle_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, subtitle)

    def _draw_pill(self, painter: QPainter, rect: QRect, text: str, color_text: QColor, color_fill: QColor) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color_fill)
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        painter.setPen(color_text)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Get item data
        is_selected = option.state & QStyle.StateFlag.State_Selected
        is_hovered = option.state & QStyle.StateFlag.State_MouseOver
        
        # Determine background
        bg_rect = option.rect
        accent_hex = getattr(self._theme_profile(), "accent", "#60a5fa")
        muted_hex = getattr(self._ui_palette(), "panel_muted", "#94a3b8")
        if is_selected:
            accent_color = QColor(accent_hex)
            accent_fill = QColor(accent_color)
            accent_fill.setAlpha(28)
            painter.fillRect(bg_rect, accent_fill)
            painter.setPen(QPen(accent_color, 2))
            painter.drawLine(bg_rect.left() + 1, bg_rect.top(), bg_rect.left() + 1, bg_rect.bottom())
        elif is_hovered:
            painter.fillRect(bg_rect, QColor(255, 255, 255, 15))

        is_group_header = bool(index.siblingAtColumn(0).data(TREE_GROUP_ROLE))
        if is_group_header:
            self._paint_group_header(painter, option, index)
            painter.restore()
            return

        col = index.column()
        is_completed = index.siblingAtColumn(0).data(Qt.ItemDataRole.UserRole + 1)
        
        if col == 0:
            # Let the default implementation handle the tree branch, checkbox, and title
            # But we can still draw the background
            super().paint(painter, option, index)
            # Draw bottom separator
            painter.setPen(QColor(255, 255, 255, 10))
            painter.drawLine(bg_rect.bottomLeft(), bg_rect.bottomRight())
            painter.restore()
            return
            
        elif col == 1:
            # Category and Priority Column
            priority = index.data(Qt.ItemDataRole.UserRole)
            category = index.data(Qt.ItemDataRole.UserRole + 1)
            status_text = index.data(TREE_STATUS_TEXT_ROLE)
            status_color_text = str(index.data(TREE_STATUS_COLOR_ROLE) or accent_hex)
            
            if priority or category or status_text:
                current_x = bg_rect.right() - 16
                left_x = bg_rect.left() + 8

                if status_text:
                    status_font = QFont(option.font)
                    status_font.setPointSize(9)
                    status_font.setBold(True)
                    painter.setFont(status_font)
                    sfm = painter.fontMetrics()
                    status_width = sfm.horizontalAdvance(str(status_text)) + 22
                    status_rect = QRect(left_x, bg_rect.top() + (bg_rect.height() - 22) // 2, status_width, 22)
                    status_color = QColor(status_color_text)
                    status_fill = QColor(status_color)
                    status_fill.setAlpha(34)
                    self._draw_pill(painter, status_rect, str(status_text), status_color, status_fill)
                    left_x = status_rect.right() + 10
                
                if priority and not is_completed:
                    p_color = QColor("#ef4444")
                    p_text = "高"
                    if priority == "中":
                        p_color = QColor("#eab308")
                        p_text = "中"
                    elif priority == "低":
                        p_color = QColor(accent_hex)
                        p_text = "低"

                    font = option.font
                    font.setPointSize(9)
                    font.setBold(True)
                    painter.setFont(font)
                    fm = painter.fontMetrics()
                    text_width = fm.horizontalAdvance(p_text)
                    pill_width = text_width + 24
                    pill_height = 22
                    pill_rect = QRect(current_x - pill_width, bg_rect.top() + (bg_rect.height() - pill_height) // 2, pill_width, pill_height)
                    bg_color = QColor(p_color)
                    bg_color.setAlpha(30)
                    self._draw_pill(painter, pill_rect, p_text, p_color, bg_color)
                    current_x = pill_rect.left() - 10

                if category and current_x - left_x > 52:
                    font = option.font
                    font.setPointSize(10)
                    painter.setFont(font)
                    cat_color = QColor("#4b5563") if is_completed else QColor(muted_hex)
                    painter.setPen(cat_color)
                    
                    fm = painter.fontMetrics()
                    category_text = str(category)
                    cat_width = fm.horizontalAdvance(category_text)
                    available_width = max(0, current_x - left_x - 10)
                    cat_rect = QRect(left_x, bg_rect.top(), min(cat_width, available_width), bg_rect.height())
                    painter.drawText(cat_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, fm.elidedText(category_text, Qt.TextElideMode.ElideRight, available_width))
                    
        elif col == 2:
            # Due Date Column
            due_at = index.data(Qt.ItemDataRole.UserRole)
            due_text = index.data(Qt.ItemDataRole.DisplayRole)
            if due_text:
                tone = QColor(str(index.data(TREE_TIMELINE_COLOR_ROLE) or "#9ca3af"))
                tone_fill = QColor(tone)
                tone_fill.setAlpha(26)
                font = option.font
                font.setPointSize(9)
                font.setBold(True)
                painter.setFont(font)
                fm = painter.fontMetrics()
                text = str(due_text)
                text_width = fm.horizontalAdvance(text) + 24
                pill_width = min(max(92, text_width), bg_rect.width() - 16)
                pill_rect = QRect(bg_rect.left() + 8, bg_rect.top() + (bg_rect.height() - 22) // 2, pill_width, 22)
                self._draw_pill(painter, pill_rect, fm.elidedText(text, Qt.TextElideMode.ElideRight, pill_rect.width() - 12), tone, tone_fill)

        elif col == 3:
            # Detail info button — draws a circle with "i" inside
            cx = bg_rect.left() + bg_rect.width() // 2
            cy = bg_rect.top() + bg_rect.height() // 2
            r = 9
            btn_color = QColor(accent_hex) if (is_hovered or is_selected) else QColor("#607a9b")
            painter.setPen(QPen(btn_color, 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
            dot_font = option.font
            dot_font.setPointSize(9)
            dot_font.setBold(True)
            painter.setFont(dot_font)
            painter.setPen(btn_color)
            painter.drawText(
                QRect(cx - r, cy - r, r * 2, r * 2),
                Qt.AlignmentFlag.AlignCenter, "i"
            )

        # Draw bottom separator
        painter.setPen(QColor(255, 255, 255, 6))
        painter.drawLine(bg_rect.bottomLeft(), bg_rect.bottomRight())

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        if bool(index.siblingAtColumn(0).data(TREE_GROUP_ROLE)):
            level = int(index.siblingAtColumn(0).data(TREE_GROUP_LEVEL_ROLE) or 0)
            return QSize(max(0, option.rect.width()), 54 if level == 0 else 42)
        size = super().sizeHint(option, index)
        size.setHeight(48) # Increased height for better elegance
        return size
