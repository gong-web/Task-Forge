from __future__ import annotations

import random
import time
from dataclasses import dataclass

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget


@dataclass
class _Particle:
    position: QPointF
    velocity: QPointF
    size: float
    color: QColor


class CelebrationOverlay(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.hide()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._particles: list[_Particle] = []
        self._message = "任务完成"
        self._subtitle = ""
        self._started_at = 0.0
        self._duration_seconds = 1.8

    def resize_to_parent(self) -> None:
        parent = self.parentWidget()
        if parent is not None:
            self.setGeometry(parent.rect())

    def start(self, *, completed_count: int = 1, task_title: str = "") -> None:
        self.resize_to_parent()
        self._message = "完成 1 项任务" if completed_count == 1 else f"完成 {completed_count} 项任务"
        self._subtitle = task_title.strip() or "保持节奏，继续推进下一项。"
        self._started_at = time.monotonic()
        self._particles = self._build_particles()
        self.show()
        self.raise_()
        self._timer.start(16)
        self.update()

    def _build_particles(self) -> list[_Particle]:
        bounds = self.rect()
        if bounds.isNull():
            bounds = QRectF(0, 0, 1200, 800).toRect()
        rng = random.Random(time.monotonic_ns())
        center_x = bounds.width() / 2
        center_y = min(bounds.height() * 0.32, 280)
        colors = [
            QColor("#f59e0b"),
            QColor("#22c55e"),
            QColor("#38bdf8"),
            QColor("#f97316"),
            QColor("#fb7185"),
            QColor("#eab308"),
        ]
        particles: list[_Particle] = []
        for _ in range(54):
            particles.append(
                _Particle(
                    position=QPointF(center_x + rng.uniform(-30, 30), center_y + rng.uniform(-12, 12)),
                    velocity=QPointF(rng.uniform(-5.2, 5.2), rng.uniform(-9.5, -2.8)),
                    size=rng.uniform(6.0, 13.0),
                    color=colors[rng.randrange(len(colors))],
                )
            )
        return particles

    def _advance(self) -> None:
        elapsed = time.monotonic() - self._started_at
        if elapsed >= self._duration_seconds:
            self._timer.stop()
            self.hide()
            self._particles.clear()
            return
        for particle in self._particles:
            particle.position += particle.velocity
            particle.velocity.setY(particle.velocity.y() + 0.26)
            particle.velocity.setX(particle.velocity.x() * 0.992)
        self.update()

    def paintEvent(self, a0) -> None:
        if not self._particles:
            return
        elapsed = max(0.0, time.monotonic() - self._started_at)
        progress = min(1.0, elapsed / self._duration_seconds)
        fade = 1.0 - progress

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(4, 10, 18, int(72 * fade)))

        for particle in self._particles:
            color = QColor(particle.color)
            color.setAlpha(max(0, int(255 * fade)))
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(
                QRectF(
                    particle.position.x(),
                    particle.position.y(),
                    particle.size,
                    particle.size * 0.68,
                ),
                2.4,
                2.4,
            )

        card_width = min(420, self.width() - 40)
        card_rect = QRectF((self.width() - card_width) / 2, max(32, self.height() * 0.11), card_width, 112)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(13, 24, 39, int(228 * fade)))
        painter.drawRoundedRect(card_rect, 24, 24)
        painter.setPen(QPen(QColor(255, 255, 255, int(36 * fade)), 1.0))
        painter.drawRoundedRect(card_rect, 24, 24)

        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor(244, 249, 255, int(255 * fade)))
        painter.drawText(
            QRectF(card_rect.left() + 20, card_rect.top() + 20, card_rect.width() - 40, 34),
            Qt.AlignmentFlag.AlignCenter,
            self._message,
        )

        subtitle_font = QFont()
        subtitle_font.setPointSize(11)
        painter.setFont(subtitle_font)
        painter.setPen(QColor(180, 202, 226, int(230 * fade)))
        painter.drawText(
            QRectF(card_rect.left() + 24, card_rect.top() + 58, card_rect.width() - 48, 34),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            self._subtitle,
        )
