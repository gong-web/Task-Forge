from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import QDateTime, QEvent, QSettings, QTime, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIntValidator
from PyQt6.QtWidgets import QAbstractItemView, QDateTimeEdit, QFrame, QGraphicsOpacityEffect, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea, QSizePolicy, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from DB import DB
from Task import Task
from ui.starry_chrome import (
    BODY_FONT,
    PALETTE,
    StarryActionButton,
    StarryCheckBox,
    StarryChoiceStrip,
    StarryComboBox,
    StarryLineEdit,
    StarrySuggestionComboBox,
    StarrySpinBox,
    StarfieldSurface,
    StarryTagEditor,
    StarryTagRow,
    StarryTextEdit,
    set_layout_margins,
)


def _button_qss(*, primary: bool) -> str:
    if primary:
        return (
            f"QPushButton {{ background: {PALETTE.button_fill_active}; border: 1px solid {_rgba(PALETTE.accent, 80)}; border-radius: 10px; color: {PALETTE.text_primary}; font-size: 14px; font-weight: 700; font-family: {BODY_FONT}; padding: 0 20px; min-height: 42px; }}"
            f"QPushButton:hover {{ background: {PALETTE.button_fill_hover}; border: 1px solid {_rgba(PALETTE.accent, 110)}; color: {PALETTE.text_primary}; }}"
            f"QPushButton:pressed {{ background: {PALETTE.button_fill}; border: 1px solid {_rgba(PALETTE.accent, 60)}; }}"
            f"QPushButton:disabled {{ color: {_rgba(PALETTE.text_primary, 130)}; border: 1px solid {_rgba(PALETTE.accent, 28)}; background: rgba(255, 255, 255, 0.04); }}"
        )
    return (
        f"QPushButton {{ background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 10px; color: {PALETTE.text_primary}; font-size: 14px; font-weight: 600; font-family: {BODY_FONT}; padding: 0 16px; min-height: 42px; }}"
        f"QPushButton:hover {{ background: rgba(255, 255, 255, 0.10); border: 1px solid rgba(255, 255, 255, 0.18); color: {PALETTE.text_primary}; }}"
        f"QPushButton:pressed {{ background: rgba(255, 255, 255, 0.03); }}"
        f"QPushButton:disabled {{ color: {_rgba(PALETTE.text_primary, 90)}; border: 1px solid rgba(255, 255, 255, 0.06); }}"
    )


def _rgba(color: str, alpha: int) -> str:
    qcolor = QColor(color)
    return f"rgba({qcolor.red()}, {qcolor.green()}, {qcolor.blue()}, {alpha})"


def _mix_hex(left: str, right: str, ratio: float) -> str:
    ratio = max(0.0, min(1.0, ratio))
    left_color = QColor(left)
    right_color = QColor(right)
    red = int(left_color.red() + (right_color.red() - left_color.red()) * ratio)
    green = int(left_color.green() + (right_color.green() - left_color.green()) * ratio)
    blue = int(left_color.blue() + (right_color.blue() - left_color.blue()) * ratio)
    return f"#{red:02x}{green:02x}{blue:02x}"


def _card_qss(name: str, *, preview: bool = False) -> str:
    bg = "rgba(255, 255, 255, 0.05)" if preview else "rgba(255, 255, 255, 0.03)"
    border = _rgba(PALETTE.accent, 22) if preview else "rgba(255, 255, 255, 0.08)"
    return (
        f"QFrame#{name} {{ background: {bg}; border: 1px solid {border}; border-radius: 12px; }}"
        f"QFrame#{name} QLabel {{ background: transparent; border: none; }}"
    )


def _preview_card_qss(name: str) -> str:
    return (
        f"QFrame#{name} {{ background: rgba(255, 255, 255, 0.04); border: 1px solid {_rgba(PALETTE.accent, 24)}; border-radius: 12px; }}"
        f"QFrame#{name} QLabel {{ background: transparent; border: none; }}"
    )


def _preview_stage_qss(name: str) -> str:
    return (
        f"QFrame#{name} {{ background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 10px; }}"
        f"QFrame#{name} QLabel {{ background: transparent; border: none; }}"
    )


def _preview_tree_qss(name: str) -> str:
    return (
        f"QTreeWidget#{name} {{ background: rgba(8, 14, 24, 0.88); border: 1px solid {_rgba(PALETTE.accent, 22)}; border-radius: 18px; padding: 10px 12px; color: {PALETTE.text_primary}; outline: none; }}"
        f"QTreeWidget#{name}::item {{ padding: 7px 2px 7px 0; border: none; }}"
        f"QTreeWidget#{name}::item:hover {{ background: {_rgba(PALETTE.accent, 9)}; }}"
        f"QTreeWidget#{name}::item:selected {{ background: transparent; color: {PALETTE.text_primary}; }}"
        "QTreeWidget::branch { background: transparent; }"
    )


def _preview_time_unit_qss() -> str:
    return (
        f"background: {_rgba(PALETTE.accent, 12)}; border: 1px solid {_rgba(PALETTE.accent, 38)}; border-radius: 12px; color: {_rgba(PALETTE.text_primary, 214)}; padding: 0 10px; font-size: 12px; font-weight: 700; font-family: {BODY_FONT};"
    )


def _preview_stat_qss() -> str:
    return (
        f"QFrame {{ background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; }}"
        f"QFrame QLabel {{ background: transparent; border: none; }}"
    )


def _inline_warning_qss() -> str:
    return (
        f"background: rgba(255, 255, 255, 0.04); border: 1px solid {_rgba(PALETTE.warning, 60)}; border-radius: 8px; "
        f"color: {_rgba(PALETTE.text_primary, 200)}; padding: 10px 12px; font-size: 12px; font-weight: 500; font-family: {BODY_FONT};"
    )


def _field_shell_qss() -> str:
    return (
        f"background: rgba(13, 22, 36, 0.84); border: 1px solid rgba(214, 224, 238, 0.40); border-radius: 16px; color: {PALETTE.text_primary};"
    )


def _input_qss() -> str:
    return (
        f"QLineEdit {{ {_field_shell_qss()} padding: 0 16px; font-size: 14px; font-weight: 500; font-family: {BODY_FONT}; placeholder-text-color: rgba(244, 248, 255, 212); }}"
        f"QLineEdit:hover {{ background: {PALETTE.field_fill_hover}; }}"
        f"QLineEdit:focus {{ background: {PALETTE.field_fill_hover}; border: 2px solid {_rgba(PALETTE.accent_strong, 184)}; }}"
    )


def _textedit_qss() -> str:
    return (
        f"QTextEdit {{ {_field_shell_qss()} padding: 12px 16px; font-size: 14px; font-weight: 500; font-family: {BODY_FONT}; placeholder-text-color: rgba(244, 248, 255, 212); selection-background-color: rgba(88, 145, 255, 0.24); }}"
        f"QTextEdit:hover {{ background: {PALETTE.field_fill_hover}; }}"
        f"QTextEdit:focus {{ background: {PALETTE.field_fill_hover}; border: 2px solid {_rgba(PALETTE.accent_strong, 184)}; }}"
    )


def _datetime_qss() -> str:
    return (
        f"QDateTimeEdit {{ {_field_shell_qss()} padding: 0 38px 0 16px; font-size: 14px; font-weight: 500; font-family: {BODY_FONT}; }}"
        f"QDateTimeEdit:hover {{ background: {PALETTE.field_fill_hover}; }}"
        f"QDateTimeEdit:focus {{ background: {PALETTE.field_fill_hover}; border: 2px solid {_rgba(PALETTE.accent_strong, 184)}; }}"
        f"QDateTimeEdit:disabled {{ color: {_rgba(PALETTE.text_primary, 188)}; border: 1px solid {_rgba(PALETTE.accent, 52)}; background: rgba(15, 24, 38, 0.90); }}"
        "QDateTimeEdit::drop-down { width: 30px; border: none; background: transparent; }"
        "QDateTimeEdit::down-arrow { image: none; width: 0; height: 0; }"
    )


def _dateonly_qss() -> str:
    return (
        f"QDateTimeEdit {{ {_field_shell_qss()} padding: 0 36px 0 16px; font-size: 14px; font-weight: 600; font-family: {BODY_FONT}; }}"
        f"QDateTimeEdit:hover {{ background: {PALETTE.field_fill_hover}; }}"
        f"QDateTimeEdit:focus {{ background: {PALETTE.field_fill_hover}; border: 2px solid {_rgba(PALETTE.accent_strong, 184)}; }}"
        f"QDateTimeEdit:disabled {{ color: {_rgba(PALETTE.text_primary, 188)}; border: 1px solid {_rgba(PALETTE.accent, 52)}; background: rgba(15, 24, 38, 0.90); }}"
        "QDateTimeEdit::drop-down { width: 28px; border: none; background: transparent; }"
        "QDateTimeEdit::down-arrow { image: none; width: 0; height: 0; }"
    )


def _mini_preset_qss() -> str:
    return (
        f"QPushButton {{ background: {_rgba(PALETTE.accent, 16)}; border: 1px solid {_rgba(PALETTE.accent, 44)}; border-radius: 12px; color: {PALETTE.text_primary}; font-size: 12px; font-weight: 700; font-family: {BODY_FONT}; padding: 0 12px; min-height: 34px; }}"
        f"QPushButton:hover {{ background: {_rgba(PALETTE.accent, 24)}; border: 1px solid {_rgba(PALETTE.accent_strong, 96)}; }}"
        f"QPushButton:disabled {{ background: rgba(255, 255, 255, 0.04); border: 1px solid {_rgba(PALETTE.accent, 18)}; color: {_rgba(PALETTE.text_primary, 118)}; }}"
    )


def _combo_qss() -> str:
    return (
        f"QComboBox {{ {_field_shell_qss()} padding: 0 44px 0 16px; font-size: 14px; font-weight: 500; font-family: {BODY_FONT}; }}"
        f"QComboBox:hover {{ background: {PALETTE.field_fill_hover}; }}"
        f"QComboBox:focus {{ background: {PALETTE.field_fill_hover}; border: 2px solid {_rgba(PALETTE.accent_strong, 184)}; }}"
        "QComboBox::drop-down { width: 30px; border: none; background: transparent; }"
        "QComboBox::down-arrow { image: none; width: 0; height: 0; }"
        f"QComboBox QAbstractItemView {{ background: {PALETTE.panel_bottom}; color: {PALETTE.text_primary}; border: 1px solid {PALETTE.field_border}; padding: 6px; outline: none; selection-background-color: {PALETTE.accent_soft}; }}"
    )


def _spin_qss() -> str:
    return (
        f"QSpinBox {{ {_field_shell_qss()} padding: 0 24px 0 14px; font-size: 14px; font-weight: 600; font-family: {BODY_FONT}; }}"
        f"QSpinBox:hover {{ background: {PALETTE.field_fill_hover}; }}"
        f"QSpinBox:focus {{ background: {PALETTE.field_fill_hover}; border: 1px solid {PALETTE.field_border_focus}; }}"
        "QSpinBox::up-button, QSpinBox::down-button { width: 0; height: 0; border: none; }"
    )


def _time_part_qss() -> str:
    return (
        f"QLineEdit {{ {_field_shell_qss()} padding: 0 10px; font-size: 14px; font-weight: 700; font-family: {BODY_FONT}; }}"
        f"QLineEdit:hover {{ background: {PALETTE.field_fill_hover}; }}"
        f"QLineEdit:focus {{ background: {PALETTE.field_fill_hover}; border: 1px solid {PALETTE.field_border_focus}; }}"
    )


def _scroll_area_qss(name: str) -> str:
    handle = _rgba(PALETTE.accent, 98)
    handle_hover = _rgba(PALETTE.accent_strong, 142)
    track = _rgba(PALETTE.panel_top, 82)
    return (
        f"QScrollArea#{name} {{ background: transparent; border: none; }}"
        f"QScrollArea#{name} > QWidget > QWidget {{ background: transparent; border: none; }}"
        f"QScrollBar:vertical {{ background: {track}; width: 10px; margin: 2px 0 2px 0; border: none; border-radius: 5px; }}"
        f"QScrollBar::handle:vertical {{ background: {handle}; min-height: 28px; border-radius: 5px; }}"
        f"QScrollBar::handle:vertical:hover {{ background: {handle_hover}; }}"
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; border: none; background: transparent; }"
        "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }"
        "QScrollBar:horizontal { height: 0; border: none; background: transparent; }"
    )


def _priority_tone(priority: str) -> str:
    if priority == "高":
        return "danger"
    if priority == "低":
        return "muted"
    return "accent"


def _checkbox_qss() -> str:
    return (
        f"QCheckBox {{ color: {_rgba(PALETTE.text_primary, 238)}; font-size: 13px; font-weight: 700; font-family: {BODY_FONT}; spacing: 6px; padding: 0; }}"
        f"QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px; border: 1px solid {PALETTE.field_border}; background: {PALETTE.field_fill}; }}"
        f"QCheckBox::indicator:unchecked:hover {{ background: {PALETTE.field_fill_hover}; }}"
        f"QCheckBox::indicator:checked {{ background: {PALETTE.button_fill_active}; border: 1px solid {PALETTE.accent_line}; }}"
    )


def _section_toggle_qss(*, active: bool, emphasized: bool = False) -> str:
    if active:
        background = _rgba(PALETTE.accent, 18)
        border = _rgba(PALETTE.accent, 52)
        color = PALETTE.text_primary
    elif emphasized:
        background = _rgba(PALETTE.accent, 14)
        border = _rgba(PALETTE.accent, 42)
        color = _rgba(PALETTE.text_primary, 220)
    else:
        background = "rgba(255, 255, 255, 0.055)"
        border = _rgba(PALETTE.accent, 28)
        color = _rgba(PALETTE.text_primary, 206)
    return (
        f"QPushButton {{ background: {background}; border: 1px solid {border}; border-radius: 10px; color: {color}; font-size: 13px; font-weight: 700; font-family: {BODY_FONT}; padding: 0 16px; text-align: left; }}"
        f"QPushButton:hover {{ background: {_rgba(PALETTE.accent, 16)}; border: 1px solid {_rgba(PALETTE.accent, 48)}; color: {PALETTE.text_primary}; }}"
    )


def _due_pill_qss(*, active: bool) -> str:
    if active:
        return (
            f"background: transparent; border: none; color: {PALETTE.accent_strong}; padding: 2px 0; font-size: 13px; font-weight: 700; font-family: {BODY_FONT};"
        )
    return (
        f"background: transparent; border: none; color: {_rgba(PALETTE.text_primary, 178)}; padding: 2px 0; font-size: 13px; font-weight: 600; font-family: {BODY_FONT};"
    )


class EditorCard(QFrame):
    def __init__(self, title: str, subtitle: str = "", *, preview: bool = False, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("editorPreviewSection" if preview else "editorFormSection")
        self.setStyleSheet(_card_qss(self.objectName(), preview=preview))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout = QVBoxLayout(self)
        set_layout_margins(layout, 22, 18, 22, 18, 12)

        self.title_label = QLabel(title)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.title_label.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_muted, 220)}; font-size: 12px; font-weight: 700; font-family: {BODY_FONT};"
        )
        layout.addWidget(self.title_label)

        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setWordWrap(True)
            self.subtitle_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.subtitle_label.setStyleSheet(
                f"background: transparent; color: {_rgba(PALETTE.text_primary, 165)}; font-size: 12px; font-weight: 500; font-family: {BODY_FONT};"
            )
            layout.addWidget(self.subtitle_label)
        else:
            self.subtitle_label = None

        self.body = QVBoxLayout()
        set_layout_margins(self.body, 0, 6, 0, 0, 14)
        layout.addLayout(self.body)


class EditorField(QWidget):
    def __init__(self, title: str, helper: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout = QVBoxLayout(self)
        set_layout_margins(layout, 0, 0, 0, 0, 8)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_primary, 190)}; font-size: 12px; font-weight: 600; font-family: {BODY_FONT};"
        )
        layout.addWidget(title_label)

        if helper:
            helper_label = QLabel(helper)
            helper_label.setWordWrap(True)
            helper_label.setStyleSheet(
                f"background: transparent; color: {_rgba(PALETTE.text_primary, 186)}; font-size: 12px; font-weight: 500; font-family: {BODY_FONT};"
            )
            layout.addWidget(helper_label)

        self.body = QVBoxLayout()
        set_layout_margins(self.body, 0, 0, 0, 0, 0)
        layout.addLayout(self.body)

    def addWidget(self, widget: QWidget) -> None:
        self.body.addWidget(widget)


class TimeValueSpinBox(QLineEdit):
    valueChanged = pyqtSignal(int)

    def __init__(self, minimum: int, maximum: int, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._minimum = minimum
        self._maximum = maximum
        self._validator = QIntValidator(minimum, maximum, self)
        self.setValidator(self._validator)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMaxLength(2)
        self.setMinimumHeight(46)
        self.setStyleSheet(_time_part_qss())
        self.editingFinished.connect(self._normalize_text)
        self.setValue(minimum)

    def lineEdit(self) -> "TimeValueSpinBox":
        return self

    def setRange(self, minimum: int, maximum: int) -> None:
        self._minimum = minimum
        self._maximum = maximum
        self._validator.setRange(minimum, maximum)
        self.setValue(self.value())

    def minimum(self) -> int:
        return self._minimum

    def maximum(self) -> int:
        return self._maximum

    def suffix(self) -> str:
        return ""

    def value(self) -> int:
        text = self.text().strip()
        if not text:
            return self._minimum
        try:
            parsed = int(text)
        except ValueError:
            return self._minimum
        return max(self._minimum, min(self._maximum, parsed))

    def setValue(self, value: int) -> None:
        clamped = max(self._minimum, min(self._maximum, int(value)))
        normalized = f"{clamped:02d}"
        changed = self.text() != normalized
        self.setText(normalized)
        if changed and not self.signalsBlocked():
            self.valueChanged.emit(clamped)

    def focusInEvent(self, a0) -> None:
        super().focusInEvent(a0)
        self.selectAll()

    def mouseReleaseEvent(self, a0) -> None:
        super().mouseReleaseEvent(a0)
        if a0 is not None and a0.button() == Qt.MouseButton.LeftButton:
            self.selectAll()

    def _normalize_text(self) -> None:
        normalized = self.value()
        self.setText(f"{normalized:02d}")
        if not self.signalsBlocked():
            self.valueChanged.emit(normalized)


@dataclass(slots=True)
class PreviewTaskNode:
    title: str
    completed: bool = False
    children: list["PreviewTaskNode"] = field(default_factory=list)


class PreviewTaskTree(QTreeWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("taskPreviewTree")
        self.setHeaderHidden(True)
        self.setRootIsDecorated(True)
        self.setItemsExpandable(True)
        self.setExpandsOnDoubleClick(False)
        self.setIndentation(22)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setUniformRowHeights(False)
        self.setRootIsDecorated(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(220)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        self.setStyleSheet(_preview_tree_qss(self.objectName()))

    def set_nodes(self, nodes: list[PreviewTaskNode]) -> None:
        self.clear()
        for node in nodes:
            self.addTopLevelItem(self._build_item(node))
        self.expandAll()

    def _build_item(self, node: PreviewTaskNode) -> QTreeWidgetItem:
        prefix = "✓ " if node.completed else "○ "
        item = QTreeWidgetItem([f"{prefix}{node.title}"])
        color = QColor(PALETTE.success if node.completed else PALETTE.text_primary)
        item.setForeground(0, color)
        font = item.font(0)
        font.setBold(bool(node.children))
        item.setFont(0, font)
        for child in node.children:
            item.addChild(self._build_item(child))
        return item


class EditorDateTimeField(QWidget):
    dateTimeChanged = pyqtSignal(QDateTime)

    def __init__(self, *, preset_times: tuple[tuple[str, int, int], ...] | None = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._minimum = QDateTime(1900, 1, 1, 0, 0)
        self._maximum = QDateTime(7999, 12, 31, 23, 59)
        self._preset_times = preset_times or (("09:00", 9, 0), ("14:00", 14, 0), ("20:00", 20, 0))
        self._preset_buttons: list[tuple[QPushButton, int]] = []
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        set_layout_margins(layout, 0, 0, 0, 0, 8)

        main_row = QHBoxLayout()
        set_layout_margins(main_row, 0, 0, 0, 0, 10)

        self.date_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMinimumHeight(46)
        self.date_edit.setMinimumWidth(176)
        self.date_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.date_edit.setStyleSheet(_dateonly_qss())

        self.hour_spin = TimeValueSpinBox(0, 23)
        self.hour_spin.setMinimumWidth(84)
        self.hour_spin.setMaximumWidth(92)
        self.hour_spin.setStyleSheet(_time_part_qss())

        self.minute_spin = TimeValueSpinBox(0, 59)
        self.minute_spin.setMinimumWidth(84)
        self.minute_spin.setMaximumWidth(92)
        self.minute_spin.setStyleSheet(_time_part_qss())

        hour_unit_label = QLabel("时")
        hour_unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hour_unit_label.setMinimumHeight(46)
        hour_unit_label.setStyleSheet(_preview_time_unit_qss())

        minute_unit_label = QLabel("分")
        minute_unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        minute_unit_label.setMinimumHeight(46)
        minute_unit_label.setStyleSheet(_preview_time_unit_qss())

        divider = QLabel(":")
        divider.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_primary, 190)}; font-size: 16px; font-weight: 600; font-family: {BODY_FONT};"
        )

        main_row.addWidget(self.date_edit, 1)
        main_row.addWidget(self.hour_spin)
        main_row.addWidget(hour_unit_label)
        main_row.addWidget(divider)
        main_row.addWidget(self.minute_spin)
        main_row.addWidget(minute_unit_label)
        layout.addLayout(main_row)

        preset_row = QHBoxLayout()
        set_layout_margins(preset_row, 0, 0, 0, 0, 8)
        for label, hour, minute in self._preset_times:
            button = QPushButton(label)
            button.setStyleSheet(_mini_preset_qss())
            button.clicked.connect(lambda _checked=False, h=hour, m=minute: self._apply_time(h, m))
            preset_row.addWidget(button)
            self._preset_buttons.append((button, hour * 60 + minute))
        preset_row.addStretch(1)
        layout.addLayout(preset_row)

        self.date_edit.dateTimeChanged.connect(self._sync_bounds)
        self.hour_spin.valueChanged.connect(self._handle_time_changed)
        self.minute_spin.valueChanged.connect(self._handle_time_changed)
        self.refresh_theme()
        self._sync_bounds()

    def refresh_theme(self) -> None:
        self.date_edit.setStyleSheet(_dateonly_qss())
        self.hour_spin.setStyleSheet(_time_part_qss())
        self.minute_spin.setStyleSheet(_time_part_qss())
        for button, _minutes in self._preset_buttons:
            button.setStyleSheet(_mini_preset_qss())

    def dateTime(self) -> QDateTime:
        return QDateTime(self.date_edit.date(), QTime(self.hour_spin.value(), self.minute_spin.value()))

    def setDateTime(self, value: QDateTime) -> None:
        target = QDateTime(value)
        if not target.isValid():
            return
        self.date_edit.blockSignals(True)
        self.date_edit.setDateTime(target)
        self.date_edit.blockSignals(False)
        self._set_time(target.time().hour(), target.time().minute(), clamp=True, emit_signal=False)
        self._sync_bounds(emit_signal=False)
        self.dateTimeChanged.emit(self.dateTime())

    def setMinimumDateTime(self, value: QDateTime) -> None:
        previous = self.dateTime()
        self._minimum = QDateTime(value) if value.isValid() else QDateTime(1900, 1, 1, 0, 0)
        self._sync_bounds(previous=previous)

    def setMaximumDateTime(self, value: QDateTime) -> None:
        previous = self.dateTime()
        self._maximum = QDateTime(value) if value.isValid() else QDateTime(7999, 12, 31, 23, 59)
        self._sync_bounds(previous=previous)

    def maximumDateTime(self) -> QDateTime:
        return QDateTime(self._maximum)

    def minimumDateTime(self) -> QDateTime:
        return QDateTime(self._minimum)

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        for widget in (self.date_edit, self.hour_spin, self.minute_spin):
            widget.setEnabled(enabled)
        for button, _minutes in self._preset_buttons:
            button.setEnabled(enabled and button.isEnabled())
        self._sync_preset_button_states()

    def _apply_time(self, hour: int, minute: int) -> None:
        self._set_time(hour, minute)

    def _allowed_bounds(self) -> tuple[QTime, QTime]:
        selected_date = self.date_edit.date()
        min_time = QTime(0, 0)
        max_time = QTime(23, 59)
        if self._minimum.isValid() and selected_date == self._minimum.date():
            min_time = self._minimum.time()
        if self._maximum.isValid() and selected_date == self._maximum.date():
            max_time = self._maximum.time()
        return min_time, max_time

    def _set_time(self, hour: int, minute: int, *, clamp: bool = True, emit_signal: bool = True) -> None:
        min_time, max_time = self._allowed_bounds()
        total_minutes = hour * 60 + minute
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
        self._sync_preset_button_states()
        if emit_signal:
            self.dateTimeChanged.emit(self.dateTime())

    def _handle_time_changed(self, *_args) -> None:
        self._set_time(self.hour_spin.value(), self.minute_spin.value(), clamp=True)

    def _sync_preset_button_states(self) -> None:
        min_time, max_time = self._allowed_bounds()
        min_minutes = min_time.hour() * 60 + min_time.minute()
        max_minutes = max_time.hour() * 60 + max_time.minute()
        for button, total_minutes in self._preset_buttons:
            button.setEnabled(self.isEnabled() and min_minutes <= total_minutes <= max_minutes)

    def _sync_bounds(self, *_args, emit_signal: bool = True, previous: QDateTime | None = None) -> None:
        before = QDateTime(previous) if previous is not None and previous.isValid() else self.dateTime()
        self.date_edit.blockSignals(True)
        self.date_edit.setMinimumDateTime(self._minimum)
        self.date_edit.setMaximumDateTime(self._maximum)
        self.date_edit.blockSignals(False)
        self._set_time(self.hour_spin.value(), self.minute_spin.value(), clamp=True, emit_signal=False)
        after = self.dateTime()
        if emit_signal and after != before:
            self.dateTimeChanged.emit(after)


class TaskEditorView(QWidget):
    submitted = pyqtSignal(dict)
    canceled = pyqtSignal()

    def __init__(self, db: DB, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.db = db
        self.task: Optional[Task] = None
        self.fixed_parent_id: Optional[int] = None
        self.parent_hint = ""
        self._preview_children_map: dict[Optional[int], list[Task]] = {}
        self._wide_mode: Optional[bool] = None
        self._build_ui()
        self.set_context()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        set_layout_margins(outer, 16, 14, 16, 14, 0)

        self.page_shell = StarfieldSurface(radius=30, surface_mode="workspace", parent=self)
        outer.addWidget(self.page_shell)
        layout = QVBoxLayout(self.page_shell)
        set_layout_margins(layout, 24, 20, 24, 20, 14)

        header_row = QHBoxLayout()
        set_layout_margins(header_row, 0, 0, 0, 0, 16)

        header_layout = QVBoxLayout()
        set_layout_margins(header_layout, 0, 0, 0, 0, 6)
        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary}; font-size: 22px; font-weight: 700; font-family: {BODY_FONT};"
        )
        self.subtitle_label = QLabel()
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_primary, 180)}; font-size: 13px; font-weight: 500; font-family: {BODY_FONT};"
        )
        self.parent_hint_label = QLabel()
        self.parent_hint_label.setWordWrap(True)
        self.parent_hint_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.accent_strong}; font-size: 13px; font-weight: 600; font-family: {BODY_FONT};"
        )
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.subtitle_label)
        header_layout.addWidget(self.parent_hint_label)
        header_row.addLayout(header_layout, 1)

        actions = QHBoxLayout()
        set_layout_margins(actions, 0, 0, 0, 0, 10)
        self.cancel_button = StarryActionButton("返回上一页", kind="ghost")
        self.cancel_button.setMinimumWidth(122)
        self.cancel_button.setMinimumHeight(46)
        self.cancel_button.setStyleSheet(_button_qss(primary=False))
        self.cancel_button.clicked.connect(self.canceled.emit)
        self.submit_button = StarryActionButton("保存任务", kind="primary")
        self.submit_button.setMinimumWidth(148)
        self.submit_button.setMinimumHeight(46)
        self.submit_button.setStyleSheet(_button_qss(primary=True))
        self.submit_button.clicked.connect(self._submit)
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.submit_button)
        header_row.addLayout(actions)
        layout.addLayout(header_row)

        self.context_tags = StarryTagRow([])
        layout.addWidget(self.context_tags)

        self.content_grid = QGridLayout()
        set_layout_margins(self.content_grid, 0, 0, 0, 0, 14)
        self.content_grid.setHorizontalSpacing(20)
        self.content_grid.setVerticalSpacing(14)

        self.form_column = QWidget()
        self.form_column.setObjectName("taskEditorFormColumn")
        self.form_column.setStyleSheet("QWidget#taskEditorFormColumn { background: transparent; border: none; }")
        self.form_column_layout = QVBoxLayout(self.form_column)
        set_layout_margins(self.form_column_layout, 0, 0, 0, 0, 18)

        self.form_scroll_area = QScrollArea()
        self.form_scroll_area.setObjectName("taskEditorFormScrollArea")
        self.form_scroll_area.setWidgetResizable(True)
        self.form_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.form_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.form_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.form_scroll_area.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.form_scroll_area.setStyleSheet(_scroll_area_qss(self.form_scroll_area.objectName()))
        self.form_scroll_area.setWidget(self.form_column)

        self.summary_column = QWidget()
        self.summary_column.setObjectName("taskEditorSummaryColumn")
        self.summary_column.setStyleSheet("QWidget#taskEditorSummaryColumn { background: transparent; border: none; }")
        self.summary_column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.summary_column_layout = QVBoxLayout(self.summary_column)
        set_layout_margins(self.summary_column_layout, 0, 0, 0, 0, 14)

        self.primary_section = EditorCard("任务内容")
        title_group = EditorField("标题")
        self.name_input = StarryLineEdit()
        self.name_input.setStyleSheet(_input_qss())
        self.name_input.setMinimumHeight(46)
        self.name_input.setPlaceholderText("任务标题")
        title_group.addWidget(self.name_input)
        self.primary_section.body.addWidget(title_group)

        desc_group = EditorField("描述")
        self.details_edit = StarryTextEdit()
        self.details_edit.setStyleSheet(_textedit_qss())
        self.details_edit.setPlaceholderText("补充说明")
        self.details_edit.setMinimumHeight(100)
        self.details_edit.setMaximumHeight(110)
        desc_group.addWidget(self.details_edit)
        self.primary_section.body.addWidget(desc_group)
        self.form_column_layout.addWidget(self.primary_section)

        self.config_section = EditorCard("基础设置")
        config_host = QWidget()
        config_host.setObjectName("taskEditorConfigHost")
        config_host.setStyleSheet("QWidget#taskEditorConfigHost { background: transparent; border: none; }")
        config_grid = QGridLayout(config_host)
        set_layout_margins(config_grid, 0, 0, 0, 0, 16)
        config_grid.setHorizontalSpacing(18)
        config_grid.setVerticalSpacing(16)

        category_group = EditorField("分类")
        category_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.category_input = StarrySuggestionComboBox()
        self.category_input.setMinimumHeight(46)
        self.category_input.set_placeholder_text("无分类")
        self.category_input.setStyleSheet(_combo_qss())
        category_group.addWidget(self.category_input)

        priority_group = EditorField("优先级")
        priority_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.priority_strip = StarryChoiceStrip(["高", "中", "低"], "中")
        self.priority_strip.setMinimumHeight(46)
        priority_group.addWidget(self.priority_strip)

        due_group = EditorField("截止时间")
        due_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.due_toggle = StarryCheckBox("设置截止时间")
        self.due_toggle.setMinimumHeight(46)
        self.due_toggle.setMinimumWidth(0)
        self.due_toggle.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.due_toggle.setStyleSheet(_checkbox_qss())
        self.due_toggle.toggled.connect(self._sync_due_state)
        self.due_edit = EditorDateTimeField()
        self.due_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        due_group.addWidget(self.due_toggle)
        due_group.addWidget(self.due_edit)

        config_grid.addWidget(category_group, 0, 0, alignment=Qt.AlignmentFlag.AlignTop)
        config_grid.addWidget(priority_group, 0, 1, alignment=Qt.AlignmentFlag.AlignTop)
        config_grid.addWidget(due_group, 1, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignTop)
        config_grid.setColumnStretch(0, 1)
        config_grid.setColumnStretch(1, 1)
        self.config_section.body.addWidget(config_host)
        self.form_column_layout.addWidget(self.config_section)

        self.summary_section = EditorCard("任务预览", preview=True)
        self.summary_section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_intro = QLabel("创建后列表中的卡片会按这个样式显示。")
        self.preview_intro.setWordWrap(True)
        self.preview_intro.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.preview_intro.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_primary, 210)}; font-size: 12px; font-weight: 600; font-family: {BODY_FONT};"
        )
        self.summary_section.body.addWidget(self.preview_intro)
        self.preview_intro.hide()

        self.preview_card = QFrame()
        self.preview_card.setObjectName("taskPreviewCard")
        self.preview_card.setStyleSheet(_preview_card_qss(self.preview_card.objectName()))
        self.preview_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.preview_card.setMinimumHeight(312)
        preview_layout = QVBoxLayout(self.preview_card)
        set_layout_margins(preview_layout, 20, 16, 20, 18, 10)

        self.preview_signal_label = QLabel("任务舞台")
        self.preview_signal_label.hide()

        self.preview_tags = StarryTagRow([], wrap=True)
        self.preview_title_label = QLabel("未命名任务")
        self.preview_title_label.setWordWrap(True)
        self.preview_title_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary}; font-size: 17px; font-weight: 700; font-family: {BODY_FONT};"
        )

        self.preview_meta_label = QLabel("")
        self.preview_meta_label.setWordWrap(True)
        self.preview_meta_label.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_secondary, 232)}; font-size: 13px; font-weight: 700; font-family: {BODY_FONT}; padding: 2px 0 0 0;"
        )

        self.preview_snapshot_label = QLabel("")
        self.preview_snapshot_label.setWordWrap(True)
        self.preview_snapshot_label.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_secondary, 216)}; font-size: 12px; font-weight: 600; font-family: {BODY_FONT}; padding: 0;"
        )

        self.preview_due_label = QLabel("")
        self.preview_due_label.setWordWrap(True)
        self.preview_due_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.preview_due_label.setStyleSheet(_due_pill_qss(active=False))
        self.summary_label = self.preview_due_label

        self.preview_description_label = QLabel("")
        self.preview_description_label.setWordWrap(True)
        self.preview_description_label.setMinimumHeight(78)
        self.preview_description_label.setStyleSheet(
            f"background: transparent; border: none; color: {_rgba(PALETTE.text_primary, 202)}; padding: 2px 0 0 0; font-size: 13px; font-weight: 500; font-family: {BODY_FONT};"
        )

        stats_row = QHBoxLayout()
        set_layout_margins(stats_row, 0, 0, 0, 0, 10)
        self.preview_scope_stat = self._create_preview_stat_card("任务类型")
        self.preview_estimate_stat = self._create_preview_stat_card("预估投入")
        self.preview_progress_stat = self._create_preview_stat_card("任务进度")
        self.preview_reminder_stat = self._create_preview_stat_card("提醒状态")
        stats_row.addWidget(self.preview_scope_stat, 1)
        stats_row.addWidget(self.preview_estimate_stat, 1)
        stats_row.addWidget(self.preview_progress_stat, 1)
        stats_row.addWidget(self.preview_reminder_stat, 1)

        self.preview_structure_card = QFrame()
        self.preview_structure_card.setObjectName("taskPreviewStructureCard")
        self.preview_structure_card.setStyleSheet(_preview_stage_qss(self.preview_structure_card.objectName()))
        self.preview_structure_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_structure_card.setMinimumHeight(280)
        structure_layout = QVBoxLayout(self.preview_structure_card)
        set_layout_margins(structure_layout, 18, 16, 18, 16, 10)

        self.preview_tree_summary_label = QLabel("子任务树")
        self.preview_tree_summary_label.setWordWrap(True)
        self.preview_tree_summary_label.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_secondary, 228)}; font-size: 12px; font-weight: 700; font-family: {BODY_FONT}; padding: 8px 0 0 0;"
        )

        self.preview_tree_hint_label = QLabel("父子关系、执行顺序和完成状态会在这里预览。")
        self.preview_tree_hint_label.setWordWrap(True)
        self.preview_tree_hint_label.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_primary, 176)}; font-size: 12px; font-weight: 500; font-family: {BODY_FONT}; padding: 0;"
        )

        self.preview_tree = PreviewTaskTree()

        preview_layout.addWidget(self.preview_signal_label)
        preview_layout.addWidget(self.preview_tags)
        preview_layout.addWidget(self.preview_title_label)
        preview_layout.addSpacing(6)
        preview_layout.addWidget(self.preview_meta_label)
        preview_layout.addWidget(self.preview_snapshot_label)
        preview_layout.addWidget(self.preview_due_label, 0, Qt.AlignmentFlag.AlignLeft)
        preview_layout.addSpacing(4)
        preview_layout.addWidget(self.preview_description_label)
        preview_layout.addLayout(stats_row)
        structure_layout.addWidget(self.preview_tree_summary_label)
        structure_layout.addWidget(self.preview_tree_hint_label)
        structure_layout.addWidget(self.preview_tree, 1)
        self.summary_section.body.addWidget(self.preview_card)
        self.summary_section.body.addWidget(self.preview_structure_card, 1)
        self.summary_column_layout.addWidget(self.summary_section, 1)

        self.advanced_section = EditorCard("补充设置", "把进度、循环和提醒分组排布，避免信息挤在一起。")
        self.advanced_note_label = QLabel("")
        self.advanced_examples_label = QLabel("")

        self.advanced_host = QWidget()
        self.advanced_host.setObjectName("taskEditorAdvancedHost")
        self.advanced_host.setStyleSheet("QWidget#taskEditorAdvancedHost { background: transparent; border: none; }")
        self.advanced_grid = QGridLayout(self.advanced_host)
        set_layout_margins(self.advanced_grid, 0, 0, 0, 20, 12)
        self.advanced_grid.setHorizontalSpacing(16)
        self.advanced_grid.setVerticalSpacing(14)

        self.tags_group = EditorField("标签")
        self.tags_input = StarryTagEditor(max_tags=6)
        self.tags_input.set_placeholder_text("输入后回车，例如 会议")
        self.tags_group.addWidget(self.tags_input)

        self.estimate_group = EditorField("预估投入", "用于估算任务跨度")
        self.estimated_spin = StarrySpinBox()
        self.estimated_spin.setStyleSheet(_spin_qss())
        self.estimated_spin.setRange(0, 10000)
        self.estimated_spin.setSuffix(" 分钟")
        self.estimated_spin.setMinimumHeight(46)
        self.estimate_group.addWidget(self.estimated_spin)

        self.progress_group = EditorField("任务进度", "手动标记 0 到 100%")
        self.progress_spin = StarrySpinBox()
        self.progress_spin.setStyleSheet(_spin_qss())
        self.progress_spin.setRange(0, 100)
        self.progress_spin.setSuffix(" %")
        self.progress_spin.setMinimumHeight(46)
        self.progress_group.addWidget(self.progress_spin)

        self.recurrence_group = EditorField("循环", "按规则生成下一次任务")
        self.recurrence_combo = StarryComboBox()
        self.recurrence_combo.setStyleSheet(_combo_qss())
        self.recurrence_combo.addItems(["不重复", "每天", "每工作日", "每周", "每两周", "每月"])
        self.recurrence_combo.setMinimumHeight(46)
        self.recurrence_group.addWidget(self.recurrence_combo)

        self.remind_group = EditorField("提醒", "提醒时间不会晚于截止时间")
        self.remind_toggle = StarryCheckBox("设置提醒")
        self.remind_toggle.setMinimumHeight(46)
        self.remind_toggle.setMinimumWidth(0)
        self.remind_toggle.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.remind_toggle.setStyleSheet(_checkbox_qss())
        self.remind_toggle.toggled.connect(self._sync_reminder_state)
        self.remind_edit = EditorDateTimeField()
        self.remind_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.reminder_disabled_label = QLabel("全局提醒当前已关闭。任务会保存提醒时间，但到点不会弹窗；可在“设置 > 系统偏好 > 任务到期提醒”中重新开启。")
        self.reminder_disabled_label.setWordWrap(True)
        self.reminder_disabled_label.hide()
        self.remind_group.addWidget(self.remind_toggle)
        self.remind_group.addWidget(self.remind_edit)
        self.remind_group.addWidget(self.reminder_disabled_label)

        self.advanced_grid.addWidget(self.tags_group, 0, 0, 1, 3, alignment=Qt.AlignmentFlag.AlignTop)
        self.advanced_grid.addWidget(self.estimate_group, 1, 0, alignment=Qt.AlignmentFlag.AlignTop)
        self.advanced_grid.addWidget(self.progress_group, 1, 1, alignment=Qt.AlignmentFlag.AlignTop)
        self.advanced_grid.addWidget(self.recurrence_group, 1, 2, alignment=Qt.AlignmentFlag.AlignTop)
        self.advanced_grid.addWidget(self.remind_group, 2, 0, 1, 3, alignment=Qt.AlignmentFlag.AlignTop)
        self.advanced_grid.setColumnStretch(0, 1)
        self.advanced_grid.setColumnStretch(1, 1)
        self.advanced_grid.setColumnStretch(2, 1)
        self.advanced_section.body.addWidget(self.advanced_host)
        self.form_column_layout.addWidget(self.advanced_section)

        layout.addLayout(self.content_grid, 1)
        self._reflow_columns(force=True)

        self.name_input.textChanged.connect(self._update_summary)
        self.details_edit.textChanged.connect(self._update_summary)
        self.category_input.textChanged.connect(self._handle_category_changed)
        self.priority_strip.valueChanged.connect(lambda *_: self._update_summary())
        self.due_toggle.toggled.connect(lambda *_: self._update_summary())
        self.due_edit.dateTimeChanged.connect(self._handle_due_datetime_changed)
        self.tags_input.textChanged.connect(self._handle_tags_changed)
        self.estimated_spin.valueChanged.connect(lambda *_: self._update_summary())
        self.progress_spin.valueChanged.connect(lambda *_: self._update_summary())
        self.recurrence_combo.currentTextChanged.connect(lambda *_: self._update_summary())
        self.remind_toggle.toggled.connect(lambda *_: self._update_summary())
        self.remind_edit.dateTimeChanged.connect(self._handle_reminder_datetime_changed)
        self.apply_theme()

    def resizeEvent(self, a0) -> None:
        super().resizeEvent(a0)
        self._reflow_columns()

    def set_context(
        self,
        *,
        task: Optional[Task] = None,
        preferred_parent_id: Optional[int] = None,
        parent_title: str = "",
    ) -> None:
        self.task = task
        self.fixed_parent_id = task.parent_id if task is not None else preferred_parent_id
        self.parent_hint = parent_title
        self._preview_children_map = self._load_preview_children_map()

        is_edit = task is not None
        self.title_label.setText("修改任务" if is_edit else "新建任务")
        self.subtitle_label.setText("")
        self.subtitle_label.hide()
        self.submit_button.setText("保存修改" if is_edit else "创建任务")

        self.name_input.setText(task.title if task else "")
        self.details_edit.setPlainText(task.description if task else "")
        self.category_input.setText(task.category if task and task.category and task.category != "默认" else "")
        self.priority_strip.set_current_value(task.priority if task and task.priority else "中")
        self.tags_input.setText(task.tags if task and task.tags else "")
        self.estimated_spin.setValue(task.estimated_minutes if task else 25)
        self.progress_spin.setValue(100 if task and task.completed else max(0, min(100, task.progress if task else 0)))
        self.recurrence_combo.setCurrentText(task.recurrence_rule if task and task.recurrence_rule else "不重复")
        if task and task.due_at:
            self.due_toggle.setChecked(True)
            self.due_edit.setDateTime(self._to_qdatetime(task.due_at))
        else:
            self.due_toggle.setChecked(False)
            self.due_edit.setDateTime(QDateTime.currentDateTime().addDays(1))
        if task and task.remind_at:
            self.remind_toggle.setChecked(True)
            self.remind_edit.setDateTime(self._to_qdatetime(task.remind_at))
        else:
            self.remind_toggle.setChecked(False)
            self.remind_edit.setDateTime(self._default_remind_datetime())
        self._sync_due_state(self.due_toggle.isChecked())
        self._sync_reminder_state(self.remind_toggle.isChecked())
        self._sync_reminder_constraints()

        if self.fixed_parent_id is not None:
            parent_text = self.parent_hint or f"父任务 ID {self.fixed_parent_id}"
            self.parent_hint_label.setText(f"将作为子任务保存到：{parent_text}")
            self.parent_hint_label.show()
        else:
            self.parent_hint_label.hide()
        self._refresh_taxonomy_examples()
        self._sync_tags_with_category()
        self._update_summary()

    def set_back_text(self, text: str) -> None:
        self.cancel_button.setText(text or "返回上一页")

    def payload(self) -> dict[str, object]:
        normalized_tags = ", ".join(self._normalized_tags())
        return {
            "title": self.name_input.text().strip(),
            "description": self.details_edit.toPlainText().strip(),
            "category": self.category_input.text().strip() or "无分类",
            "priority": self.priority_strip.current_value("中"),
            "due_at": self.due_edit.dateTime().toPyDateTime() if self.due_toggle.isChecked() else None,
            "remind_at": self.remind_edit.dateTime().toPyDateTime() if self.remind_toggle.isChecked() else None,
            "parent_id": self.fixed_parent_id,
            "progress": self.progress_spin.value(),
            "estimated_minutes": self.estimated_spin.value(),
            "recurrence_rule": self.recurrence_combo.currentText().strip() or "不重复",
            "tags": normalized_tags,
        }

    def apply_theme(self) -> None:
        self.title_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary}; font-size: 22px; font-weight: 700; font-family: {BODY_FONT};"
        )
        self.subtitle_label.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_primary, 180)}; font-size: 13px; font-weight: 500; font-family: {BODY_FONT};"
        )
        self.parent_hint_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.accent_strong}; font-size: 13px; font-weight: 600; font-family: {BODY_FONT};"
        )
        self.cancel_button.setStyleSheet(_button_qss(primary=False))
        self.submit_button.setStyleSheet(_button_qss(primary=True))
        self.primary_section.setStyleSheet(_card_qss(self.primary_section.objectName(), preview=False))
        self.config_section.setStyleSheet(_card_qss(self.config_section.objectName(), preview=False))
        self.summary_section.setStyleSheet(_card_qss(self.summary_section.objectName(), preview=True))
        self.advanced_section.setStyleSheet(_card_qss(self.advanced_section.objectName(), preview=False))
        self.name_input.setStyleSheet(_input_qss())
        self.details_edit.setStyleSheet(_textedit_qss())
        self.form_scroll_area.setStyleSheet(_scroll_area_qss(self.form_scroll_area.objectName()))
        self.category_input.refresh_theme()
        self.category_input.setStyleSheet(_combo_qss())
        self.priority_strip.refresh_theme()
        self.due_toggle.setStyleSheet(_checkbox_qss())
        self.due_edit.refresh_theme()
        self.tags_input.refresh_theme()
        self.estimated_spin.setStyleSheet(_spin_qss())
        self.progress_spin.setStyleSheet(_spin_qss())
        self.recurrence_combo.setStyleSheet(_combo_qss())
        self.remind_toggle.setStyleSheet(_checkbox_qss())
        self.remind_edit.refresh_theme()
        self.reminder_disabled_label.setStyleSheet(_inline_warning_qss())
        self.preview_intro.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_primary, 210)}; font-size: 12px; font-weight: 600; font-family: {BODY_FONT};"
        )
        self.preview_card.setStyleSheet(_preview_card_qss(self.preview_card.objectName()))
        self.preview_signal_label.hide()
        self.preview_title_label.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary}; font-size: 17px; font-weight: 700; font-family: {BODY_FONT};"
        )
        self.preview_meta_label.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_secondary, 232)}; font-size: 13px; font-weight: 700; font-family: {BODY_FONT}; padding: 2px 0 0 0;"
        )
        self.preview_snapshot_label.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_secondary, 216)}; font-size: 12px; font-weight: 600; font-family: {BODY_FONT}; padding: 0;"
        )
        self.preview_description_label.setStyleSheet(
            f"background: transparent; border: none; color: {_rgba(PALETTE.text_primary, 202)}; padding: 2px 0 0 0; font-size: 13px; font-weight: 500; font-family: {BODY_FONT};"
        )
        self.preview_structure_card.setStyleSheet(_preview_stage_qss(self.preview_structure_card.objectName()))
        self.preview_tree_summary_label.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_secondary, 228)}; font-size: 12px; font-weight: 700; font-family: {BODY_FONT}; padding: 8px 0 0 0;"
        )
        self.preview_tree_hint_label.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_primary, 176)}; font-size: 12px; font-weight: 500; font-family: {BODY_FONT}; padding: 0;"
        )
        self.preview_tree.refresh_theme()
        self.context_tags.refresh_theme()
        self.preview_tags.refresh_theme()
        self._refresh_taxonomy_examples()
        self._update_summary()

    def _reflow_columns(self, *, force: bool = False) -> None:
        wide = self.width() >= 1000
        if not force and wide == self._wide_mode:
            return
        self._wide_mode = wide

        while self.content_grid.count():
            self.content_grid.takeAt(0)

        if wide:
            summary_width = min(420, max(324, self.width() // 3 - 8))
            self.summary_column.setMinimumWidth(summary_width)
            self.summary_column.setMaximumWidth(summary_width)
            self.content_grid.addWidget(self.form_scroll_area, 0, 0)
            self.content_grid.addWidget(self.summary_column, 0, 1)
            self.content_grid.setColumnStretch(0, 1)
            self.content_grid.setColumnStretch(1, 0)
        else:
            self.summary_column.setMinimumWidth(0)
            self.summary_column.setMaximumWidth(16777215)
            self.content_grid.addWidget(self.form_scroll_area, 0, 0)
            self.content_grid.addWidget(self.summary_column, 1, 0)
            self.content_grid.setColumnStretch(0, 1)
            self.content_grid.setColumnStretch(1, 0)

    def _create_preview_stat_card(self, label: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(_preview_stat_qss())
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(card)
        set_layout_margins(layout, 12, 10, 12, 10, 4)
        caption = QLabel(label)
        caption.setStyleSheet(
            f"background: transparent; color: {_rgba(PALETTE.text_primary, 160)}; font-size: 11px; font-weight: 700; font-family: {BODY_FONT};"
        )
        value = QLabel("-")
        value.setStyleSheet(
            f"background: transparent; color: {PALETTE.text_primary}; font-size: 14px; font-weight: 600; font-family: {BODY_FONT};"
        )
        layout.addWidget(caption)
        layout.addWidget(value)
        card.value_label = value  # type: ignore[attr-defined]
        return card

    def _sync_due_state(self, checked: bool) -> None:
        self.due_edit.setEnabled(checked)
        effect = self.due_edit.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(self.due_edit)
            self.due_edit.setGraphicsEffect(effect)
        effect.setOpacity(1.0 if checked else 0.60)
        self._sync_reminder_constraints()

    def _sync_reminder_state(self, checked: bool) -> None:
        self.remind_edit.setEnabled(checked)
        effect = self.remind_edit.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(self.remind_edit)
            self.remind_edit.setGraphicsEffect(effect)
        effect.setOpacity(1.0 if checked else 0.60)
        if checked and not self.remind_edit.dateTime().isValid():
            self.remind_edit.setDateTime(self._default_remind_datetime())
        self._sync_reminder_constraints()
        self._sync_reminder_notice()

    def _handle_due_datetime_changed(self, *_args) -> None:
        self._sync_reminder_constraints()
        self._update_summary()

    def _handle_reminder_datetime_changed(self, *_args) -> None:
        self._sync_reminder_constraints()
        self._update_summary()

    def _notifications_enabled(self) -> bool:
        settings = QSettings("TaskForge", "TaskForgeDesktop")
        return settings.value("toggle_notify", True, type=bool)

    def _sync_reminder_notice(self) -> None:
        should_warn = self.remind_toggle.isChecked() and not self._notifications_enabled()
        self.reminder_disabled_label.setVisible(should_warn)

    def _sync_reminder_constraints(self) -> None:
        if self.due_toggle.isChecked():
            due_dt = self.due_edit.dateTime()
            latest_reminder = due_dt
            self.remind_edit.setMaximumDateTime(latest_reminder)
            if self.remind_toggle.isChecked() and self.remind_edit.dateTime() > due_dt:
                self.remind_edit.blockSignals(True)
                self.remind_edit.setDateTime(due_dt)
                self.remind_edit.blockSignals(False)
        else:
            self.remind_edit.setMaximumDateTime(QDateTime(7999, 12, 31, 23, 59))

    def _handle_category_changed(self, _value: str) -> None:
        self._sync_tags_with_category()
        self._update_summary()

    def _handle_tags_changed(self, _value: str) -> None:
        self._sync_tags_with_category()
        self._update_summary()

    def _default_remind_datetime(self) -> QDateTime:
        if self.due_toggle.isChecked():
            due_dt = self.due_edit.dateTime()
            if due_dt > QDateTime.currentDateTime().addSecs(3600):
                return due_dt.addSecs(-3600)
            return due_dt.addSecs(-60)
        return QDateTime.currentDateTime().addSecs(3600)

    def _normalized_tags(self) -> list[str]:
        category_key = (self.category_input.text().strip() or "").casefold()
        seen: set[str] = set()
        normalized: list[str] = []
        for tag in self.tags_input.tags():
            tag = tag.strip()
            if not tag:
                continue
            key = tag.casefold()
            if key in seen or key == category_key:
                continue
            seen.add(key)
            normalized.append(tag)
        return normalized[:6]

    def _sync_tags_with_category(self) -> None:
        normalized = self._normalized_tags()
        if normalized != self.tags_input.tags():
            self.tags_input.set_tags(normalized, emit_signal=False)

    def _refresh_taxonomy_examples(self) -> None:
        categories = self._clean_taxonomy_examples(self.db.list_categories(), exclude={"默认", "无分类", "未分类"})
        tags = self._clean_taxonomy_examples(self.db.list_tags())
        self.category_input.set_suggestions(categories)
        self.tags_input.set_suggestions(tags)

    @staticmethod
    def _clean_taxonomy_examples(values: list[str], *, exclude: set[str] | None = None) -> list[str]:
        blocked = {item.strip() for item in (exclude or set())}
        cleaned: list[str] = []
        for raw in values:
            text = (raw or "").strip()
            if not text or text in blocked:
                continue
            if "?" in text or "�" in text:
                continue
            if all(char in {"?", "？", "/", "·", "-", "_", ".", " ", "　"} for char in text):
                continue
            cleaned.append(text)
            if len(cleaned) == 4:
                break
        return cleaned

    def _load_preview_children_map(self) -> dict[Optional[int], list[Task]]:
        children_map: dict[Optional[int], list[Task]] = {}
        for preview_task in self.db.list_tasks():
            children_map.setdefault(preview_task.parent_id, []).append(preview_task)
        for children in children_map.values():
            children.sort(key=lambda item: (item.sort_order, item.created_at, item.id))
        return children_map

    def _existing_preview_children(self, task_id: int, *, depth: int = 0) -> list[PreviewTaskNode]:
        if depth >= 3:
            return []
        nodes: list[PreviewTaskNode] = []
        for child in self._preview_children_map.get(task_id, [])[:4]:
            nodes.append(
                PreviewTaskNode(
                    title=child.title,
                    completed=child.completed,
                    children=self._existing_preview_children(child.id, depth=depth + 1),
                )
            )
        return nodes

    def _sample_preview_children(self) -> list[PreviewTaskNode]:
        return [
            PreviewTaskNode("拆分边界与准备资料", completed=True),
            PreviewTaskNode(
                "推进主流程",
                children=[
                    PreviewTaskNode("同步关键节点"),
                    PreviewTaskNode("补齐验收清单"),
                ],
            ),
            PreviewTaskNode("检查交付与收尾"),
        ]

    @staticmethod
    def _count_preview_nodes(nodes: list[PreviewTaskNode]) -> int:
        return sum(1 + TaskEditorView._count_preview_nodes(node.children) for node in nodes)

    @staticmethod
    def _count_preview_completed(nodes: list[PreviewTaskNode]) -> int:
        return sum((1 if node.completed else 0) + TaskEditorView._count_preview_completed(node.children) for node in nodes)

    def _preview_tree_nodes(self) -> tuple[list[PreviewTaskNode], str]:
        existing_children: list[PreviewTaskNode] = []
        if self.task is not None:
            existing_children = self._existing_preview_children(self.task.id)

        if existing_children:
            total = self._count_preview_nodes(existing_children)
            done = self._count_preview_completed(existing_children)
            return existing_children, f"子任务结构 · {done} / {total} 已完成"

        # No real children — hide the structure panel entirely
        return [], ""

    def _update_summary(self) -> None:
        title = self.name_input.text().strip() or "未命名任务"
        category = self.category_input.text().strip() or "无分类"
        priority = self.priority_strip.current_value("中")
        has_due = self.due_toggle.isChecked()
        due_text = self.due_edit.dateTime().toString("yyyy-MM-dd HH:mm") if has_due else "未设置截止时间"
        description = self.details_edit.toPlainText().strip()
        tags = self._normalized_tags()
        recurrence = self.recurrence_combo.currentText().strip() or "不重复"
        has_reminder = self.remind_toggle.isChecked()
        reminder_text = self.remind_edit.dateTime().toString("MM-dd HH:mm") if has_reminder else "无提醒"
        reminder_enabled = self._notifications_enabled()
        scope_text = "主任务"
        if self.fixed_parent_id is not None:
            scope_text = "子任务"
        estimated_minutes = self.estimated_spin.value()
        progress_value = self.progress_spin.value()

        context_items: list[tuple[str, str]] = []
        if self.fixed_parent_id is not None:
            context_items.append((scope_text, "accent"))
        self.context_tags.set_texts(context_items)
        self.context_tags.setVisible(bool(context_items))
        self.preview_tags.set_texts(
            [
                (scope_text, "accent"),
                (category, "brass"),
                (f"{priority}优先级", _priority_tone(priority)),
            ] + [(tag, "muted") for tag in tags[:2]]
        )
        self.preview_title_label.setText(title)
        meta_parts: list[str] = []
        if estimated_minutes > 0:
            meta_parts.append(f"预计 {estimated_minutes} 分钟")
        meta_parts.append(f"进度 {progress_value}%")
        if recurrence != "不重复":
            meta_parts.append(recurrence)
        self.preview_meta_label.setVisible(bool(meta_parts))
        self.preview_meta_label.setText(" · ".join(meta_parts))
        if has_reminder:
            snapshot_text = f"提醒 {reminder_text}"
            if not reminder_enabled:
                snapshot_text += " · 全局提醒已关闭"
            self.preview_snapshot_label.setText(snapshot_text)
            self.preview_snapshot_label.show()
        else:
            self.preview_snapshot_label.hide()
        self.preview_due_label.setText(f"截止 {due_text}" if has_due else "未设置截止时间")
        self.preview_due_label.setStyleSheet(_due_pill_qss(active=has_due))
        self.preview_description_label.setText(description or "暂无任务说明。")
        self.preview_scope_stat.value_label.setText(scope_text)  # type: ignore[attr-defined]
        self.preview_estimate_stat.value_label.setText(f"{estimated_minutes or 0} 分钟")  # type: ignore[attr-defined]
        self.preview_progress_stat.value_label.setText(f"{progress_value}%")  # type: ignore[attr-defined]
        if has_reminder and not reminder_enabled:
            self.preview_reminder_stat.value_label.setText(f"{reminder_text} · 已关闭")  # type: ignore[attr-defined]
        else:
            self.preview_reminder_stat.value_label.setText(reminder_text if has_reminder else "未设置")  # type: ignore[attr-defined]
        self._sync_reminder_notice()
        preview_nodes, preview_tree_summary = self._preview_tree_nodes()
        has_tree = bool(preview_nodes)
        self.preview_structure_card.setVisible(has_tree)
        if has_tree:
            self.preview_tree_summary_label.setText(preview_tree_summary)
            self.preview_tree.set_nodes(preview_nodes)

    def _submit(self) -> None:
        payload = self.payload()
        if not str(payload["title"] or "").strip():
            QMessageBox.warning(self, "名称不能为空", "请先输入任务名称。")
            return
        due_at = payload.get("due_at")
        remind_at = payload.get("remind_at")
        if isinstance(due_at, datetime) and self.task is None and due_at < datetime.now():
            QMessageBox.warning(self, "截止时间无效", "新建任务的截止时间不能早于当前时间。")
            return
        if isinstance(remind_at, datetime) and self.task is None and remind_at < datetime.now():
            QMessageBox.warning(self, "提醒时间无效", "新建任务的提醒时间不能早于当前时间。")
            return
        if isinstance(due_at, datetime) and isinstance(remind_at, datetime) and remind_at > due_at:
            QMessageBox.warning(self, "提醒时间无效", "提醒时间不能晚于截止时间。")
            return
        self.submitted.emit(payload)

    @staticmethod
    def _to_qdatetime(value: datetime) -> QDateTime:
        return QDateTime(value.year, value.month, value.day, value.hour, value.minute, value.second)