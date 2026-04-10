from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.reminder_sounds import ReminderSoundSpec, list_reminder_sound_specs, reminder_sound_spec
from ui.theme import rgba

DEFAULT_REMINDER_ANIMATION_ID = "banner_wave"


@dataclass(frozen=True)
class ReminderAnimationSpec:
    id: str
    label: str
    subtitle: str
    accent: str
    secondary: str
    motion: str


@dataclass
class _ReminderSpark:
    angle: float
    radius: float
    size: float
    phase: float


_REMINDER_ANIMATION_SPECS: tuple[ReminderAnimationSpec, ...] = (
    ReminderAnimationSpec(
        id="nebula_pulse",
        label="中央提醒卡",
        subtitle="中央弹出明确的提醒卡片，带一层柔和呼吸圈，信息最直接。",
        accent="#60a5fa",
        secondary="#22d3ee",
        motion="中央卡片",
    ),
    ReminderAnimationSpec(
        id="banner_wave",
        label="顶部提醒条",
        subtitle="从顶部滑入清晰提醒条，最接近系统通知样式。",
        accent="#f59e0b",
        secondary="#f97316",
        motion="顶部滑入",
    ),
    ReminderAnimationSpec(
        id="corner_beacon",
        label="侧边提醒卡",
        subtitle="右上角滑出一张提醒卡，低打扰但仍然能一眼看懂。",
        accent="#34d399",
        secondary="#2dd4bf",
        motion="右上滑入",
    ),
)
_REMINDER_ANIMATION_INDEX = {spec.id: spec for spec in _REMINDER_ANIMATION_SPECS}


def list_reminder_animation_specs() -> tuple[ReminderAnimationSpec, ...]:
    return _REMINDER_ANIMATION_SPECS


def normalize_reminder_animation_id(animation_id: str | None) -> str:
    requested = (animation_id or "").strip()
    if requested in _REMINDER_ANIMATION_INDEX:
        return requested
    return DEFAULT_REMINDER_ANIMATION_ID


def reminder_animation_spec(animation_id: str | None) -> ReminderAnimationSpec:
    normalized = normalize_reminder_animation_id(animation_id)
    return _REMINDER_ANIMATION_INDEX.get(normalized, _REMINDER_ANIMATION_SPECS[0])


def reminder_animation_label(animation_id: str | None) -> str:
    return reminder_animation_spec(animation_id).label


def _clear_layout(layout: QVBoxLayout | QGridLayout | QHBoxLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item is None:
            continue
        widget = item.widget()
        child_layout = item.layout()
        if widget is not None:
            widget.deleteLater()
        elif child_layout is not None:
            _clear_layout(child_layout)  # type: ignore[arg-type]


def _chip(label: str, accent: str) -> QLabel:
    chip = QLabel(label)
    chip.setStyleSheet(
        f"background: {rgba(accent, 18)}; color: #eef6ff; border: 1px solid {rgba(accent, 62)}; border-radius: 11px; padding: 4px 9px; font-size: 11px; font-weight: 700;"
    )
    return chip


def _ease_out(progress: float) -> float:
    clamped = max(0.0, min(1.0, progress))
    return 1.0 - ((1.0 - clamped) ** 3)


def _ease_in_out(progress: float) -> float:
    clamped = max(0.0, min(1.0, progress))
    return 3 * (clamped ** 2) - 2 * (clamped ** 3)


class ReminderExperienceHeaderCard(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame { background: rgba(15, 23, 42, 0.82); border-radius: 26px; border: 1px solid rgba(255, 255, 255, 0.05); }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        eyebrow = QLabel("提醒体验中心")
        eyebrow.setStyleSheet("background: transparent; color: #8fb2d8; font-size: 11px; font-weight: 800; letter-spacing: 2px;")
        self.title = QLabel("尚未配置提醒体验")
        self.title.setStyleSheet("background: transparent; color: #edf4ff; font-size: 28px; font-weight: 800;")
        self.subtitle = QLabel("")
        self.subtitle.setWordWrap(True)
        self.subtitle.setStyleSheet("background: transparent; color: #a7bad1; font-size: 13px; line-height: 1.7;")

        self.meta_host = QWidget()
        self.meta_layout = QGridLayout(self.meta_host)
        self.meta_layout.setContentsMargins(0, 0, 0, 0)
        self.meta_layout.setSpacing(10)

        self.chips_host = QWidget()
        self.chips_layout = QHBoxLayout(self.chips_host)
        self.chips_layout.setContentsMargins(0, 0, 0, 0)
        self.chips_layout.setSpacing(8)

        layout.addWidget(eyebrow)
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addWidget(self.meta_host)
        layout.addWidget(self.chips_host)

        self.set_selection(reminder_sound_spec(None), reminder_animation_spec(None))

    def set_selection(self, sound: ReminderSoundSpec, animation: ReminderAnimationSpec) -> None:
        self.title.setText(f"{sound.label} + {animation.label}")
        self.subtitle.setText(
            f"当前提示音为“{sound.label}”，动画为“{animation.label}”。提醒触发时会先播放音频，再叠加 {animation.motion} 的视觉反馈。"
        )

        _clear_layout(self.meta_layout)
        meta_cards = (
            ("提示音风格", sound.mood, sound.accent),
            ("铃声时长", f"约 {max(1, round(sound.duration_ms / 100) / 10):.1f} 秒", sound.accent),
            ("动画节奏", animation.motion, animation.accent),
            ("提醒气质", animation.subtitle.split("，", 1)[0], animation.secondary),
        )
        for index, (label, value, accent) in enumerate(meta_cards):
            self.meta_layout.addWidget(_MetaPill(label, value, accent), index // 2, index % 2)

        _clear_layout(self.chips_layout)
        self.chips_layout.addWidget(_chip(sound.label, sound.accent))
        self.chips_layout.addWidget(_chip(sound.subtitle, sound.accent))
        self.chips_layout.addWidget(_chip(animation.label, animation.accent))
        self.chips_layout.addWidget(_chip(animation.motion, animation.accent))
        self.chips_layout.addStretch(1)


class _MetaPill(QFrame):
    def __init__(self, label: str, value: str, accent: str, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: {rgba(accent, 16)}; border-radius: 16px; border: 1px solid {rgba(accent, 42)}; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        title = QLabel(label)
        title.setStyleSheet("background: transparent; color: #9fb5cf; font-size: 11px; font-weight: 700;")
        value_label = QLabel(value)
        value_label.setWordWrap(True)
        value_label.setStyleSheet(f"background: transparent; color: {accent}; font-size: 15px; font-weight: 800;")
        layout.addWidget(title)
        layout.addWidget(value_label)


class _SoundPreviewStripe(QWidget):
    def __init__(self, accent: str, parent=None) -> None:
        super().__init__(parent)
        self._accent = accent
        self.setMinimumHeight(58)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect().adjusted(1, 1, -1, -1))
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, QColor(self._accent))
        gradient.setColorAt(1.0, QColor(18, 30, 48, 220))
        painter.setPen(QPen(QColor(255, 255, 255, 28), 1))
        painter.setBrush(gradient)
        painter.drawRoundedRect(rect, 15, 15)

        pen = QPen(QColor(255, 255, 255, 190), 2.2)
        painter.setPen(pen)
        mid_y = rect.center().y()
        segments = 18
        points: list[QPointF] = []
        for index in range(segments + 1):
            x = rect.left() + rect.width() * index / segments
            lift = math.sin(index * 0.92) * 8
            if index % 4 == 0:
                lift *= 1.45
            points.append(QPointF(x, mid_y - lift))
        for index in range(len(points) - 1):
            painter.drawLine(points[index], points[index + 1])


class ReminderSoundCardButton(QPushButton):
    chosen = pyqtSignal(str)

    def __init__(self, spec: ReminderSoundSpec, parent=None) -> None:
        super().__init__(parent)
        self.spec = spec
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(176)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(self._qss(False))
        self.clicked.connect(lambda: self.chosen.emit(self.spec.id))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 14)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)

        copy_box = QVBoxLayout()
        copy_box.setContentsMargins(0, 0, 0, 0)
        copy_box.setSpacing(3)
        title = QLabel(spec.label)
        title.setStyleSheet("background: transparent; color: #edf4ff; font-size: 15px; font-weight: 800;")
        subtitle = QLabel(spec.subtitle)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("background: transparent; color: #a7bad1; font-size: 11px; line-height: 1.5;")
        copy_box.addWidget(title)
        copy_box.addWidget(subtitle)

        mood = QLabel(spec.mood)
        mood.setStyleSheet(
            f"background: {rgba(spec.accent, 18)}; color: {spec.accent}; border-radius: 10px; border: 1px solid {rgba(spec.accent, 58)}; padding: 4px 8px; font-size: 11px; font-weight: 700;"
        )

        top.addLayout(copy_box, 1)
        top.addWidget(mood, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top)
        layout.addWidget(_SoundPreviewStripe(spec.accent))

        chips = QHBoxLayout()
        chips.setContentsMargins(0, 0, 0, 0)
        chips.setSpacing(8)
        chips.addWidget(_chip(f"{max(1, round(spec.duration_ms / 100) / 10):.1f} 秒", spec.accent))
        chips.addWidget(_chip(spec.texture, spec.accent))
        chips.addStretch(1)
        layout.addLayout(chips)

    def setChecked(self, checked: bool) -> None:
        super().setChecked(checked)
        self.setStyleSheet(self._qss(checked))

    def _qss(self, checked: bool) -> str:
        if checked:
            return (
                f"QPushButton {{ background: {rgba(self.spec.accent, 18)}; border-radius: 22px; border: 1px solid {rgba(self.spec.accent, 56)}; text-align: left; }}"
                f"QPushButton:hover {{ background: {rgba(self.spec.accent, 24)}; }}"
            )
        return (
            "QPushButton { background: rgba(255, 255, 255, 0.04); border-radius: 22px; border: 1px solid rgba(255, 255, 255, 0.05); text-align: left; }"
            "QPushButton:hover { background: rgba(255, 255, 255, 0.07); }"
        )


class _AnimationPreviewTile(QWidget):
    def __init__(self, animation_id: str, accent: str, secondary: str, parent=None) -> None:
        super().__init__(parent)
        self._animation_id = animation_id
        self._accent = accent
        self._secondary = secondary
        self.setMinimumHeight(68)

    def _paint_preview_notice(self, painter: QPainter, rect: QRectF, *, title: str, subtitle: str) -> None:
        painter.setPen(QPen(QColor(255, 255, 255, 34), 1))
        painter.setBrush(QColor(9, 17, 29, 226))
        painter.drawRoundedRect(rect, 10, 10)

        bell_rect = QRectF(rect.left() + 8, rect.top() + 7, 16, 16)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self._accent))
        painter.drawEllipse(bell_rect)

        title_font = QFont()
        title_font.setPointSize(8)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor("#f8fbff"))
        painter.drawText(
            QRectF(bell_rect.right() + 6, rect.top() + 5, rect.width() - 34, 12),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            title,
        )

        subtitle_font = QFont()
        subtitle_font.setPointSize(7)
        painter.setFont(subtitle_font)
        painter.setPen(QColor("#b7c9dd"))
        painter.drawText(
            QRectF(bell_rect.right() + 6, rect.top() + 17, rect.width() - 34, 10),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            subtitle,
        )

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect().adjusted(1, 1, -1, -1))
        painter.setPen(QPen(QColor(255, 255, 255, 24), 1))
        painter.setBrush(QColor(14, 23, 37, 210))
        painter.drawRoundedRect(rect, 16, 16)

        accent = QColor(self._accent)
        secondary = QColor(self._secondary)
        if self._animation_id == "banner_wave":
            banner = QRectF(rect.left() + 10, rect.top() + 10, rect.width() - 20, 22)
            gradient = QLinearGradient(banner.topLeft(), banner.topRight())
            gradient.setColorAt(0.0, accent)
            gradient.setColorAt(1.0, secondary)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(gradient)
            painter.drawRoundedRect(banner, 11, 11)
            self._paint_preview_notice(painter, QRectF(rect.left() + 14, rect.top() + 34, rect.width() - 28, 20), title="任务提醒", subtitle="10:35 到点")
            painter.setPen(QPen(QColor(255, 255, 255, 130), 2))
            base_y = rect.bottom() - 18
            for index in range(14):
                x1 = rect.left() + 12 + index * ((rect.width() - 24) / 14)
                x2 = x1 + ((rect.width() - 24) / 14)
                painter.drawLine(
                    QPointF(x1, base_y + math.sin(index * 0.7) * 3),
                    QPointF(x2, base_y + math.sin((index + 1) * 0.7) * 3),
                )
            return

        if self._animation_id == "corner_beacon":
            beacon_center = QPointF(rect.right() - 26, rect.top() + 24)
            for scale, alpha in ((1.0, 200), (1.55, 110), (2.15, 50)):
                color = QColor(accent)
                color.setAlpha(alpha)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                radius = 7 * scale
                painter.drawEllipse(beacon_center, radius, radius)
            self._paint_preview_notice(painter, QRectF(rect.left() + 12, rect.top() + 14, rect.width() - 60, 26), title="任务提醒", subtitle="右上出现")
            painter.setBrush(QColor(255, 255, 255, 235))
            painter.drawEllipse(beacon_center, 4, 4)
            painter.setPen(QPen(QColor(255, 255, 255, 120), 2))
            painter.drawRoundedRect(QRectF(rect.left() + 12, rect.bottom() - 24, rect.width() - 24, 8), 4, 4)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(accent))
            painter.drawRoundedRect(QRectF(rect.left() + 12, rect.bottom() - 24, rect.width() * 0.58, 8), 4, 4)
            return

        center = rect.center()
        for scale, alpha in ((1.0, 180), (1.55, 96), (2.05, 54)):
            color = QColor(accent)
            color.setAlpha(alpha)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(color, 2.0))
            radius = 14 * scale
            painter.drawEllipse(center, radius, radius)
        self._paint_preview_notice(painter, QRectF(center.x() - 42, center.y() - 14, 84, 28), title="任务提醒", subtitle="中央弹出")


class ReminderAnimationCardButton(QPushButton):
    chosen = pyqtSignal(str)

    def __init__(self, spec: ReminderAnimationSpec, parent=None) -> None:
        super().__init__(parent)
        self.spec = spec
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(182)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(self._qss(False))
        self.clicked.connect(lambda: self.chosen.emit(self.spec.id))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 14)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)
        copy_box = QVBoxLayout()
        copy_box.setContentsMargins(0, 0, 0, 0)
        copy_box.setSpacing(3)

        title = QLabel(spec.label)
        title.setStyleSheet("background: transparent; color: #edf4ff; font-size: 15px; font-weight: 800;")
        subtitle = QLabel(spec.subtitle)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("background: transparent; color: #a7bad1; font-size: 11px; line-height: 1.5;")
        copy_box.addWidget(title)
        copy_box.addWidget(subtitle)

        motion = QLabel(spec.motion)
        motion.setStyleSheet(
            f"background: {rgba(spec.accent, 18)}; color: {spec.accent}; border-radius: 10px; border: 1px solid {rgba(spec.accent, 58)}; padding: 4px 8px; font-size: 11px; font-weight: 700;"
        )

        top.addLayout(copy_box, 1)
        top.addWidget(motion, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top)
        layout.addWidget(_AnimationPreviewTile(spec.id, spec.accent, spec.secondary))

        chips = QHBoxLayout()
        chips.setContentsMargins(0, 0, 0, 0)
        chips.setSpacing(8)
        chips.addWidget(_chip("提醒弹层", spec.accent))
        chips.addWidget(_chip(spec.motion, spec.accent))
        chips.addStretch(1)
        layout.addLayout(chips)

    def setChecked(self, checked: bool) -> None:
        super().setChecked(checked)
        self.setStyleSheet(self._qss(checked))

    def _qss(self, checked: bool) -> str:
        if checked:
            return (
                f"QPushButton {{ background: {rgba(self.spec.accent, 18)}; border-radius: 22px; border: 1px solid {rgba(self.spec.accent, 56)}; text-align: left; }}"
                f"QPushButton:hover {{ background: {rgba(self.spec.accent, 24)}; }}"
            )
        return (
            "QPushButton { background: rgba(255, 255, 255, 0.04); border-radius: 22px; border: 1px solid rgba(255, 255, 255, 0.05); text-align: left; }"
            "QPushButton:hover { background: rgba(255, 255, 255, 0.07); }"
        )


class ReminderExperienceGalleryWidget(QWidget):
    soundChanged = pyqtSignal(str)
    animationChanged = pyqtSignal(str)
    previewSoundRequested = pyqtSignal()
    previewAnimationRequested = pyqtSignal()
    previewExperienceRequested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._selected_sound_id = reminder_sound_spec(None).id
        self._selected_animation_id = reminder_animation_spec(None).id
        self.sound_buttons: dict[str, ReminderSoundCardButton] = {}
        self.animation_buttons: dict[str, ReminderAnimationCardButton] = {}
        self._sound_group = QButtonGroup(self)
        self._sound_group.setExclusive(True)
        self._animation_group = QButtonGroup(self)
        self._animation_group.setExclusive(True)
        self.header_card = ReminderExperienceHeaderCard(self)
        self._setup_ui()
        self.set_selection(self._selected_sound_id, self._selected_animation_id)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addWidget(self.header_card)

        intro_card = QFrame()
        intro_card.setStyleSheet(
            "QFrame { background: rgba(255, 255, 255, 0.04); border-radius: 22px; border: 1px solid rgba(255, 255, 255, 0.05); }"
        )
        intro_layout = QVBoxLayout(intro_card)
        intro_layout.setContentsMargins(22, 20, 22, 20)
        intro_layout.setSpacing(14)
        intro_title = QLabel("选择提示音")
        intro_title.setStyleSheet("background: transparent; color: #edf4ff; font-size: 19px; font-weight: 800;")
        intro_desc = QLabel("所有提醒音均可离线使用，点击卡片即可切换，配合下方按钮可立即试听。")
        intro_desc.setWordWrap(True)
        intro_desc.setStyleSheet("background: transparent; color: #a7bad1; font-size: 13px; line-height: 1.7;")
        intro_layout.addWidget(intro_title)
        intro_layout.addWidget(intro_desc)

        sound_grid = QGridLayout()
        sound_grid.setSpacing(14)
        for index, spec in enumerate(list_reminder_sound_specs()):
            button = ReminderSoundCardButton(spec, self)
            button.chosen.connect(self._choose_sound)
            self.sound_buttons[spec.id] = button
            self._sound_group.addButton(button)
            sound_grid.addWidget(button, index // 2, index % 2)
        intro_layout.addLayout(sound_grid)
        layout.addWidget(intro_card)

        animation_card = QFrame()
        animation_card.setStyleSheet(
            "QFrame { background: rgba(255, 255, 255, 0.04); border-radius: 22px; border: 1px solid rgba(255, 255, 255, 0.05); }"
        )
        animation_layout = QVBoxLayout(animation_card)
        animation_layout.setContentsMargins(22, 20, 22, 20)
        animation_layout.setSpacing(14)
        animation_title = QLabel("选择提醒动画")
        animation_title.setStyleSheet("background: transparent; color: #edf4ff; font-size: 19px; font-weight: 800;")
        animation_desc = QLabel("提醒到点时会在主界面上叠加动画反馈。动画和主题完全独立，可以单独配置。")
        animation_desc.setWordWrap(True)
        animation_desc.setStyleSheet("background: transparent; color: #a7bad1; font-size: 13px; line-height: 1.7;")
        animation_layout.addWidget(animation_title)
        animation_layout.addWidget(animation_desc)

        animation_grid = QGridLayout()
        animation_grid.setSpacing(14)
        for index, spec in enumerate(list_reminder_animation_specs()):
            button = ReminderAnimationCardButton(spec, self)
            button.chosen.connect(self._choose_animation)
            self.animation_buttons[spec.id] = button
            self._animation_group.addButton(button)
            animation_grid.addWidget(button, index // 2, index % 2)
        animation_layout.addLayout(animation_grid)
        layout.addWidget(animation_card)

        action_row = QFrame()
        action_row.setStyleSheet(
            "QFrame { background: rgba(12, 20, 33, 0.72); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.05); }"
        )
        action_layout = QHBoxLayout(action_row)
        action_layout.setContentsMargins(18, 16, 18, 16)
        action_layout.setSpacing(12)

        preview_sound_button = QPushButton("试听当前提示音")
        preview_sound_button.setProperty("role", "secondary")
        preview_sound_button.clicked.connect(self.previewSoundRequested.emit)
        preview_animation_button = QPushButton("预览当前动画")
        preview_animation_button.setProperty("role", "secondary")
        preview_animation_button.clicked.connect(self.previewAnimationRequested.emit)
        preview_all_button = QPushButton("同时预览提醒体验")
        preview_all_button.setProperty("role", "primary")
        preview_all_button.clicked.connect(self.previewExperienceRequested.emit)

        action_layout.addWidget(preview_sound_button)
        action_layout.addWidget(preview_animation_button)
        action_layout.addWidget(preview_all_button)
        action_layout.addStretch(1)
        layout.addWidget(action_row)
        layout.addStretch(1)

    def set_selection(self, sound_id: str, animation_id: str) -> None:
        self._selected_sound_id = reminder_sound_spec(sound_id).id
        self._selected_animation_id = reminder_animation_spec(animation_id).id
        for candidate, button in self.sound_buttons.items():
            button.setChecked(candidate == self._selected_sound_id)
        for candidate, button in self.animation_buttons.items():
            button.setChecked(candidate == self._selected_animation_id)
        self.header_card.set_selection(
            reminder_sound_spec(self._selected_sound_id),
            reminder_animation_spec(self._selected_animation_id),
        )

    def _choose_sound(self, sound_id: str) -> None:
        self.set_selection(sound_id, self._selected_animation_id)
        self.soundChanged.emit(self._selected_sound_id)

    def _choose_animation(self, animation_id: str) -> None:
        self.set_selection(self._selected_sound_id, animation_id)
        self.animationChanged.emit(self._selected_animation_id)


class ReminderOverlay(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.hide()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._started_at = 0.0
        self._duration_seconds = 1.7
        self._title = "任务提醒"
        self._subtitle = ""
        self._animation_id = DEFAULT_REMINDER_ANIMATION_ID
        self._sparks: list[_ReminderSpark] = []

    def resize_to_parent(self) -> None:
        parent = self.parentWidget()
        if parent is not None:
            self.setGeometry(parent.rect())

    def start(self, *, animation_id: str, title: str, subtitle: str) -> None:
        self.resize_to_parent()
        self._animation_id = normalize_reminder_animation_id(animation_id)
        self._title = title.strip() or "任务提醒"
        self._subtitle = subtitle.strip() or reminder_animation_spec(animation_id).subtitle
        self._sparks = self._build_sparks()
        self._started_at = time.monotonic()
        self.show()
        self.raise_()
        self._timer.start(16)
        self.update()

    def _build_sparks(self) -> list[_ReminderSpark]:
        rng = random.Random(time.monotonic_ns())
        sparks: list[_ReminderSpark] = []
        for _ in range(18):
            sparks.append(
                _ReminderSpark(
                    angle=rng.uniform(0.0, math.pi * 2),
                    radius=rng.uniform(36.0, 120.0),
                    size=rng.uniform(4.0, 9.0),
                    phase=rng.uniform(0.0, math.pi * 2),
                )
            )
        return sparks

    def _advance(self) -> None:
        elapsed = time.monotonic() - self._started_at
        if elapsed >= self._duration_seconds:
            self._timer.stop()
            self.hide()
            return
        self.update()

    def paintEvent(self, event) -> None:
        if not self.isVisible():
            return
        progress = min(1.0, max(0.0, (time.monotonic() - self._started_at) / self._duration_seconds))
        fade = 1.0 - progress
        spec = reminder_animation_spec(self._animation_id)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        overlay = QColor(4, 10, 20, int(72 * fade))
        if spec.id == "corner_beacon":
            overlay.setAlpha(int(44 * fade))
        painter.fillRect(self.rect(), overlay)

        if spec.id == "banner_wave":
            self._paint_banner_wave(painter, spec, progress, fade)
        elif spec.id == "corner_beacon":
            self._paint_corner_beacon(painter, spec, progress, fade)
        else:
            self._paint_nebula_pulse(painter, spec, progress, fade)

    def _paint_nebula_pulse(self, painter: QPainter, spec: ReminderAnimationSpec, progress: float, fade: float) -> None:
        center = QPointF(self.width() / 2, min(self.height() * 0.26, 240))
        eased = _ease_out(progress)
        accent = QColor(spec.accent)
        for index, alpha in enumerate((136, 64)):
            color = QColor(accent)
            color.setAlpha(int(alpha * fade))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(color, 2.4))
            radius = 68 + index * 34 + eased * (54 + index * 18)
            painter.drawEllipse(center, radius, radius)
        self._paint_sparks(painter, center, spec, progress, fade)
        card_rect = QRectF((self.width() - min(500, self.width() - 40)) / 2, max(38, self.height() * 0.11), min(500, self.width() - 40), 148)
        self._paint_message_card(painter, card_rect, spec, fade)

    def _paint_banner_wave(self, painter: QPainter, spec: ReminderAnimationSpec, progress: float, fade: float) -> None:
        eased = _ease_out(min(1.0, progress * 1.3))
        banner_width = min(760, self.width() - 56)
        banner_height = 126
        x = (self.width() - banner_width) / 2
        y = -banner_height + eased * (banner_height + 30)
        banner_rect = QRectF(x, y, banner_width, banner_height)

        gradient = QLinearGradient(banner_rect.topLeft(), banner_rect.bottomRight())
        start = QColor(spec.accent)
        end = QColor(spec.secondary)
        start.setAlpha(int(220 * fade))
        end.setAlpha(int(176 * fade))
        gradient.setColorAt(0.0, start)
        gradient.setColorAt(1.0, end)
        painter.setPen(QPen(QColor(255, 255, 255, int(44 * fade)), 1.0))
        painter.setBrush(gradient)
        painter.drawRoundedRect(banner_rect, 28, 28)

        self._paint_wave_lines(painter, banner_rect, fade)
        self._paint_message_card(painter, banner_rect.adjusted(0, 0, 0, 0), spec, fade, title_color="#fefce8", subtitle_color="#fff7ed")

    def _paint_corner_beacon(self, painter: QPainter, spec: ReminderAnimationSpec, progress: float, fade: float) -> None:
        eased = _ease_out(min(1.0, progress * 1.4))
        card_width = min(372, self.width() - 40)
        card_height = 156
        x = self.width() + 28 - eased * (card_width + 52)
        y = 28 + (1.0 - eased) * 18
        rect = QRectF(x, y, card_width, card_height)

        painter.setPen(QPen(QColor(255, 255, 255, int(34 * fade)), 1.0))
        painter.setBrush(QColor(10, 20, 32, int(220 * fade)))
        painter.drawRoundedRect(rect, 24, 24)

        beacon_center = QPointF(rect.right() - 50, y + 42)
        accent = QColor(spec.accent)
        for scale, alpha in ((1.0, 190), (1.75, 100), (2.45, 46)):
            color = QColor(accent)
            color.setAlpha(int(alpha * fade))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(color, 2.0))
            radius = 10 * scale + math.sin(progress * math.pi * 4) * 1.6
            painter.drawEllipse(beacon_center, radius, radius)
        painter.setPen(Qt.PenStyle.NoPen)
        dot = QColor(spec.secondary)
        dot.setAlpha(int(255 * fade))
        painter.setBrush(dot)
        painter.drawEllipse(beacon_center, 6, 6)

        progress_track = QRectF(rect.left() + 20, rect.bottom() - 24, rect.width() - 40, 8)
        painter.setBrush(QColor(255, 255, 255, int(26 * fade)))
        painter.drawRoundedRect(progress_track, 4, 4)
        fill = QRectF(progress_track.left(), progress_track.top(), progress_track.width() * max(0.25, eased), progress_track.height())
        fill_gradient = QLinearGradient(fill.topLeft(), fill.topRight())
        fill_gradient.setColorAt(0.0, QColor(spec.accent))
        fill_gradient.setColorAt(1.0, QColor(spec.secondary))
        painter.setBrush(fill_gradient)
        painter.drawRoundedRect(fill, 4, 4)
        self._paint_message_card(painter, rect.adjusted(0, 0, 0, -14), spec, fade)

    def _paint_wave_lines(self, painter: QPainter, rect: QRectF, fade: float) -> None:
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, int(118 * fade)), 1.8))
        for offset in (0.0, 0.7, 1.4):
            path = QPainterPath()
            base_y = rect.bottom() - 18 - offset * 8
            path.moveTo(rect.left() + 24, base_y)
            segments = 26
            for index in range(1, segments + 1):
                x = rect.left() + 24 + (rect.width() - 48) * index / segments
                y = base_y + math.sin(index * 0.8 + offset) * 4.2
                path.lineTo(x, y)
            painter.drawPath(path)

    def _paint_sparks(self, painter: QPainter, center: QPointF, spec: ReminderAnimationSpec, progress: float, fade: float) -> None:
        accent = QColor(spec.accent)
        accent.setAlpha(int(86 * fade))
        painter.setPen(Qt.PenStyle.NoPen)
        for spark in self._sparks:
            pulse = 1.0 + math.sin(progress * math.pi * 3 + spark.phase) * 0.14
            x = center.x() + math.cos(spark.angle) * spark.radius * pulse
            y = center.y() + math.sin(spark.angle) * spark.radius * pulse * 0.74
            color = QColor(accent)
            color.setAlpha(int((72 + math.sin(progress * math.pi * 5 + spark.phase) * 24) * fade))
            painter.setBrush(color)
            painter.drawEllipse(QPointF(x, y), spark.size, spark.size)

    def _draw_reminder_icon(self, painter: QPainter, rect: QRectF, spec: ReminderAnimationSpec, fade: float) -> None:
        accent = QColor(spec.accent)
        accent.setAlpha(int(230 * fade))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(accent)
        painter.drawEllipse(rect)

        icon_pen = QPen(QColor(255, 255, 255, int(245 * fade)), 2.4)
        painter.setPen(icon_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        bell_rect = rect.adjusted(rect.width() * 0.27, rect.height() * 0.19, -rect.width() * 0.27, -rect.height() * 0.27)
        painter.drawArc(bell_rect, 25 * 16, 130 * 16)
        painter.drawLine(
            QPointF(bell_rect.left() + 3, bell_rect.bottom() - 2),
            QPointF(bell_rect.right() - 3, bell_rect.bottom() - 2),
        )
        painter.drawLine(
            QPointF(rect.center().x(), bell_rect.top() - 3),
            QPointF(rect.center().x(), bell_rect.top() + 5),
        )
        painter.setBrush(QColor(255, 255, 255, int(245 * fade)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(rect.center().x(), bell_rect.bottom() + 3), 2.5, 2.5)

    def _draw_notice_badge(self, painter: QPainter, rect: QRectF, spec: ReminderAnimationSpec, fade: float) -> None:
        badge_rect = QRectF(rect.left(), rect.top(), 62, 24)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, int(34 * fade)))
        painter.drawRoundedRect(badge_rect, 12, 12)
        badge_font = QFont()
        badge_font.setPointSize(9)
        badge_font.setBold(True)
        painter.setFont(badge_font)
        painter.setPen(QColor(spec.accent))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, "提醒")

    def _paint_message_card(
        self,
        painter: QPainter,
        rect: QRectF,
        spec: ReminderAnimationSpec,
        fade: float,
        *,
        title_color: str = "#f8fbff",
        subtitle_color: str = "#dce7f5",
    ) -> None:
        card_rect = QRectF(rect)
        if spec.id == "banner_wave":
            card_rect = QRectF(rect.left() + 22, rect.top() + 16, rect.width() - 44, rect.height() - 30)
        elif spec.id == "corner_beacon":
            card_rect = QRectF(rect.left() + 18, rect.top() + 16, rect.width() - 92, rect.height() - 42)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(9, 17, 29, int(218 * fade)))
            painter.drawRoundedRect(card_rect, 24, 24)
            painter.setPen(QPen(QColor(255, 255, 255, int(34 * fade)), 1.0))
            painter.drawRoundedRect(card_rect, 24, 24)
            card_rect = QRectF(rect.left() + 20, rect.top() + 16, rect.width() - 40, rect.height() - 30)

        self._draw_notice_badge(painter, card_rect, spec, fade)
        icon_rect = QRectF(card_rect.left(), card_rect.top() + 32, 42, 42)
        self._draw_reminder_icon(painter, icon_rect, spec, fade)
        text_left = icon_rect.right() + 14

        title_font = QFont()
        title_font.setPointSize(16 if spec.id == "corner_beacon" else 17)
        title_font.setBold(True)
        painter.setFont(title_font)
        title = QColor(title_color)
        title.setAlpha(int(255 * fade))
        painter.setPen(title)
        painter.drawText(QRectF(text_left, card_rect.top() + 28, card_rect.width() - (text_left - card_rect.left()), 30), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._title)

        subtitle_font = QFont()
        subtitle_font.setPointSize(11)
        painter.setFont(subtitle_font)
        subtitle = QColor(subtitle_color)
        subtitle.setAlpha(int(235 * fade))
        painter.setPen(subtitle)
        painter.drawText(
            QRectF(text_left, card_rect.top() + 60, card_rect.width() - (text_left - card_rect.left()), max(32.0, card_rect.height() - 60)),
            Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap,
            self._subtitle,
        )


class ReminderAnimationPreviewWidget(ReminderOverlay):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self._duration_seconds = 2.05

    def resize_to_parent(self) -> None:
        return

    def start_preview(self, *, animation_id: str, title: str, subtitle: str) -> None:
        self._animation_id = normalize_reminder_animation_id(animation_id)
        self._title = title.strip() or "任务提醒"
        self._subtitle = subtitle.strip() or reminder_animation_spec(animation_id).subtitle
        self._sparks = self._build_sparks()
        self._started_at = time.monotonic()
        self.show()
        self._timer.start(16)
        self.update()

    def stop_preview(self) -> None:
        self._timer.stop()
        self.hide()

    def _advance(self) -> None:
        elapsed = time.monotonic() - self._started_at
        if elapsed >= self._duration_seconds:
            self._started_at = time.monotonic()
            self._sparks = self._build_sparks()
        self.update()


class ReminderPromptDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        *,
        animation_id: str,
        title: str,
        subtitle: str,
        summary_text: str,
        task_count: int,
    ) -> None:
        super().__init__(parent)
        self._selected_delay_minutes: int | None = None
        self._animation_id = normalize_reminder_animation_id(animation_id)
        self.setModal(True)
        self.setWindowTitle("任务提醒")
        self.setMinimumWidth(560)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setStyleSheet(
            "QDialog { background: #0b1220; }"
            "QLabel { color: #edf4ff; }"
            "QFrame#shell { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(25, 34, 56, 244), stop:1 rgba(15, 20, 36, 244)); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 24px; }"
            "QPushButton { min-height: 42px; border-radius: 16px; padding: 0 18px; font-size: 14px; font-weight: 700; }"
            "QPushButton[role='primary'] { background: rgba(245, 158, 11, 0.18); color: #fff7ed; border: 1px solid rgba(245, 158, 11, 0.38); }"
            "QPushButton[role='secondary'] { background: rgba(255, 255, 255, 0.07); color: #edf4ff; border: 1px solid rgba(255, 255, 255, 0.08); }"
            "QPushButton:hover { background: rgba(255, 255, 255, 0.12); }"
        )

        shell = QFrame(self)
        shell.setObjectName("shell")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(shell)

        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(18, 18, 18, 18)
        shell_layout.setSpacing(14)

        self.preview = ReminderAnimationPreviewWidget(shell)
        self.preview.setMinimumHeight(188)
        shell_layout.addWidget(self.preview)

        heading = QLabel("以下任务已到达你设定的提醒时间")
        heading.setStyleSheet("font-size: 18px; font-weight: 800; color: #f8fbff;")
        shell_layout.addWidget(heading)

        meta = QLabel(f"共 {task_count} 项。你可以立即确认，或者统一延后。")
        meta.setWordWrap(True)
        meta.setStyleSheet("font-size: 12px; color: #9fb5cf;")
        shell_layout.addWidget(meta)

        summary = QLabel(summary_text)
        summary.setWordWrap(True)
        summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        summary.setStyleSheet(
            "background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 18px; padding: 14px 16px; font-size: 14px; color: #e5eefb; line-height: 1.6;"
        )
        shell_layout.addWidget(summary)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(10)

        acknowledge_button = QPushButton("知道了")
        acknowledge_button.setProperty("role", "primary")
        acknowledge_button.clicked.connect(self.accept)

        postpone_10 = QPushButton("延后10分钟")
        postpone_10.setProperty("role", "secondary")
        postpone_10.clicked.connect(lambda: self._accept_with_delay(10))

        postpone_30 = QPushButton("延后30分钟")
        postpone_30.setProperty("role", "secondary")
        postpone_30.clicked.connect(lambda: self._accept_with_delay(30))

        postpone_60 = QPushButton("延后1小时")
        postpone_60.setProperty("role", "secondary")
        postpone_60.clicked.connect(lambda: self._accept_with_delay(60))

        button_row.addWidget(acknowledge_button)
        button_row.addWidget(postpone_10)
        button_row.addWidget(postpone_30)
        button_row.addWidget(postpone_60)
        shell_layout.addLayout(button_row)

        self.preview.start_preview(animation_id=self._animation_id, title=title, subtitle=subtitle)

    @property
    def selected_delay_minutes(self) -> int | None:
        return self._selected_delay_minutes

    def _accept_with_delay(self, minutes: int) -> None:
        self._selected_delay_minutes = minutes
        self.accept()

    def closeEvent(self, event) -> None:
        self.preview.stop_preview()
        super().closeEvent(event)
