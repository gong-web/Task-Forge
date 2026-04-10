from __future__ import annotations

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import QFrame, QScrollArea, QScrollBar, QWidget


class SmartScrollArea(QScrollArea):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tracked_widgets: set[int] = set()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def setWidget(self, widget: QWidget) -> None:
        super().setWidget(widget)
        self._tracked_widgets.clear()
        self._bind_widget(widget)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.ChildAdded:
            child = event.child()
            if isinstance(child, QWidget):
                self._bind_widget(child)
        elif (
            event.type() == QEvent.Type.Wheel
            and watched not in (self, self.viewport())
            and self._scroll_bar_can_move(self.verticalScrollBar())
        ):
            delta = event.pixelDelta().y() or event.angleDelta().y()
            if delta:
                self._apply_wheel_delta(self.verticalScrollBar(), delta)
                event.accept()
                return True
        return super().eventFilter(watched, event)

    def _bind_widget(self, widget: QWidget) -> None:
        widget_id = id(widget)
        if widget_id in self._tracked_widgets:
            return
        self._tracked_widgets.add(widget_id)
        widget.installEventFilter(self)
        for child in widget.findChildren(QWidget):
            child_id = id(child)
            if child_id in self._tracked_widgets:
                continue
            self._tracked_widgets.add(child_id)
            child.installEventFilter(self)

    @staticmethod
    def _scroll_bar_can_move(scroll_bar: QScrollBar) -> bool:
        return scroll_bar.maximum() > scroll_bar.minimum()

    @staticmethod
    def _apply_wheel_delta(scroll_bar: QScrollBar, delta: int) -> None:
        step = scroll_bar.singleStep() or 24
        amount = max(step, step * max(1, abs(delta) // 120))
        direction = -1 if delta > 0 else 1
        scroll_bar.setValue(scroll_bar.value() + direction * amount)
