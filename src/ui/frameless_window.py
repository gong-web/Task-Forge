from PyQt6.QtCore import Qt, QRect, QPoint, QEvent
from PyQt6.QtGui import QCursor, QHoverEvent, QMouseEvent
from PyQt6.QtWidgets import QWidget

class FramelessResizeMixin:
    def setup_frameless(self, margin=8):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        # We don't want fully transparent if it makes text unreadable, 
        # but we need it for rounded corners. Let's paint a solid background in MainWindow instead.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setMouseTracking(True)
        self._margin = margin
        self._resize_dir = None
        self._start_pos = None
        self._start_geometry = None

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
        parent_handler = getattr(super(), "mousePressEvent", None)
        if a0.button() == Qt.MouseButton.LeftButton:
            dir_x, dir_y = self._get_resize_direction(a0.pos())
            if dir_x != 0 or dir_y != 0:
                self._resize_dir = (dir_x, dir_y)
                self._start_pos = a0.globalPosition().toPoint()
                self._start_geometry = self.geometry()
            elif callable(parent_handler):
                parent_handler(a0)
        elif callable(parent_handler):
            parent_handler(a0)

    def mouseMoveEvent(self, a0: QMouseEvent | None):
        if a0 is None:
            return
        parent_handler = getattr(super(), "mouseMoveEvent", None)
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
            if callable(parent_handler):
                parent_handler(a0)

    def mouseReleaseEvent(self, a0: QMouseEvent | None):
        if a0 is None:
            return
        self._resize_dir = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        parent_handler = getattr(super(), "mouseReleaseEvent", None)
        if callable(parent_handler):
                parent_handler(a0)
