from __future__ import annotations

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.celestial_theme_catalog import (
    BackgroundSpec,
    ThemeProfile,
    background_path,
    get_background_spec,
    get_theme_profile,
    list_backgrounds_for_theme,
    list_theme_profiles,
    theme_background_count,
    theme_metric_items,
    theme_preview_swatches,
    theme_story_lines,
)
from ui.theme import rgba


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


class SwatchDot(QWidget):
    def __init__(self, color: str, parent=None) -> None:
        super().__init__(parent)
        self.color = color
        self.setFixedSize(18, 18)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(255, 255, 255, 34), 1))
        painter.setBrush(QColor(self.color))
        painter.drawEllipse(self.rect().adjusted(1, 1, -1, -1))
        painter.end()


class SoftMetricPill(QFrame):
    def __init__(self, label: str, value: str, accent: str, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: {rgba(accent, 18)}; border-radius: 14px; border: none; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        value_label = QLabel(value)
        value_label.setStyleSheet(
            f"background: transparent; color: {accent}; font-size: 16px; font-weight: 800;"
        )
        label_widget = QLabel(label)
        label_widget.setStyleSheet(
            "background: transparent; color: #d7e2f1; font-size: 11px; font-weight: 600;"
        )
        layout.addWidget(value_label)
        layout.addWidget(label_widget)


class StoryLine(QFrame):
    def __init__(self, text: str, accent: str, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: {rgba(accent, 12)}; border-radius: 12px; border: none; }}"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        bullet = QLabel("●")
        bullet.setStyleSheet(f"background: transparent; color: {accent}; font-size: 11px; font-weight: 800;")
        copy = QLabel(text)
        copy.setWordWrap(True)
        copy.setStyleSheet("background: transparent; color: #dce7f5; font-size: 12px; line-height: 1.6;")
        layout.addWidget(bullet, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(copy, 1)


class PaletteRibbon(QFrame):
    def __init__(self, colors: tuple[str, str, str, str], parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet("QFrame { background: transparent; border: none; }")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        for color in colors:
            layout.addWidget(SwatchDot(color))
        layout.addStretch(1)


class ThemeHeaderCard(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame { background: rgba(15, 23, 42, 0.76); border-radius: 24px; border: none; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)

        eyebrow = QLabel("视觉主题中心")
        eyebrow.setStyleSheet("background: transparent; color: #8ca7d4; font-size: 11px; font-weight: 800; letter-spacing: 2px;")
        self.title = QLabel("主题未加载")
        self.title.setStyleSheet("background: transparent; color: #edf4ff; font-size: 28px; font-weight: 800;")
        self.subtitle = QLabel("")
        self.subtitle.setWordWrap(True)
        self.subtitle.setStyleSheet("background: transparent; color: #a7bad1; font-size: 13px; line-height: 1.7;")

        layout.addWidget(eyebrow)
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        self.ribbon_host = QWidget()
        self.ribbon_layout = QVBoxLayout(self.ribbon_host)
        self.ribbon_layout.setContentsMargins(0, 0, 0, 0)
        self.ribbon_layout.setSpacing(0)
        self.ribbon = PaletteRibbon(("#8ca7d4", "#d7c8a4", "#6fd2c3", "#d7969b"))
        self.ribbon_layout.addWidget(self.ribbon)
        layout.addWidget(self.ribbon_host)

        self.metrics_host = QWidget()
        self.metrics_layout = QGridLayout(self.metrics_host)
        self.metrics_layout.setContentsMargins(0, 0, 0, 0)
        self.metrics_layout.setSpacing(10)
        layout.addWidget(self.metrics_host)

        self.story_host = QWidget()
        self.story_layout = QVBoxLayout(self.story_host)
        self.story_layout.setContentsMargins(0, 0, 0, 0)
        self.story_layout.setSpacing(8)
        layout.addWidget(self.story_host)

    def set_theme(self, theme: ThemeProfile) -> None:
        self.title.setText(theme.name)
        self.subtitle.setText(theme.tagline)
        _clear_layout(self.ribbon_layout)
        self.ribbon = PaletteRibbon(theme_preview_swatches(theme.id))
        self.ribbon_layout.addWidget(self.ribbon)

        _clear_layout(self.metrics_layout)
        for index, (label, value) in enumerate(theme_metric_items(theme.id)):
            self.metrics_layout.addWidget(SoftMetricPill(label, value, theme.accent), index // 2, index % 2)

        _clear_layout(self.story_layout)
        for line in theme_story_lines(theme.id):
            self.story_layout.addWidget(StoryLine(line, theme.accent))


class ThemeCardButton(QPushButton):
    chosen = pyqtSignal(str)

    def __init__(self, theme: ThemeProfile, parent=None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(148)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(self._qss(False))
        self.clicked.connect(lambda: self.chosen.emit(self.theme.id))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 14)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)
        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(2)

        self.title = QLabel(theme.name)
        self.title.setStyleSheet("background: transparent; color: #edf4ff; font-size: 15px; font-weight: 800;")
        subtitle = QLabel(theme.tagline)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("background: transparent; color: #a7bad1; font-size: 11px; line-height: 1.5;")
        title_box.addWidget(self.title)
        title_box.addWidget(subtitle)

        count = QLabel(f"{theme_background_count(theme.id)} 张背景")
        count.setStyleSheet(
            f"background: {rgba(theme.accent, 18)}; color: {theme.accent_strong}; border-radius: 10px; border: 1px solid {rgba(theme.accent, 56)}; padding: 4px 8px; font-size: 11px; font-weight: 700;"
        )

        top.addLayout(title_box, 1)
        top.addWidget(count, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top)

        preview = QFrame()
        preview.setFixedHeight(52)
        preview.setStyleSheet(
            f"QFrame {{ border-radius: 16px; border: 1px solid {rgba(theme.accent, 60)}; background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {theme.sky_top}, stop:0.45 {theme.sky_mid}, stop:1 {theme.sky_bottom}); }}"
        )
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(12, 10, 12, 10)
        preview_layout.setSpacing(0)
        preview_text = QLabel("柔和渐层预览")
        preview_text.setStyleSheet(f"background: transparent; color: {theme.text_primary}; font-size: 12px; font-weight: 700;")
        preview_layout.addWidget(preview_text)
        layout.addWidget(preview)

        swatches = PaletteRibbon(theme_preview_swatches(theme.id))
        layout.addWidget(swatches)

    def setChecked(self, checked: bool) -> None:
        super().setChecked(checked)
        self.setStyleSheet(self._qss(checked))

    def _qss(self, checked: bool) -> str:
        if checked:
            return (
                f"QPushButton {{ background: {rgba(self.theme.accent, 20)}; border-radius: 22px; border: none; text-align: left; }}"
                f"QPushButton:hover {{ background: {rgba(self.theme.accent, 24)}; }}"
            )
        return (
            "QPushButton { background: rgba(255, 255, 255, 0.04); border-radius: 22px; border: none; text-align: left; }"
            "QPushButton:hover { background: rgba(255, 255, 255, 0.07); }"
        )


class BackgroundCardButton(QPushButton):
    chosen = pyqtSignal(str)

    def __init__(self, spec: BackgroundSpec, parent=None) -> None:
        super().__init__(parent)
        self.spec = spec
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(QSize(220, 180))
        self.setMaximumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(self._qss(False))
        self.clicked.connect(lambda: self.chosen.emit(self.spec.id))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.preview_label = QLabel()
        self.preview_label.setFixedHeight(112)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background: rgba(255,255,255,0.03); border-radius: 18px; border: none;")
        layout.addWidget(self.preview_label)

        title = QLabel(spec.title)
        title.setWordWrap(True)
        title.setStyleSheet("background: transparent; color: #edf4ff; font-size: 13px; font-weight: 800;")
        subtitle = QLabel(spec.subtitle)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("background: transparent; color: #a7bad1; font-size: 11px; line-height: 1.5;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        tags = QHBoxLayout()
        tags.setContentsMargins(0, 0, 0, 0)
        tags.setSpacing(6)
        motif_tag = QLabel(spec.motif.upper())
        motif_tag.setStyleSheet(
            f"background: {rgba(spec.accent_primary, 18)}; color: {spec.text_primary}; border-radius: 10px; border: 1px solid {rgba(spec.accent_primary, 60)}; padding: 4px 8px; font-size: 10px; font-weight: 800;"
        )
        star_tag = QLabel(f"{spec.star_density} stars")
        star_tag.setStyleSheet(
            f"background: {rgba(spec.accent_secondary, 18)}; color: {spec.text_secondary}; border-radius: 10px; border: 1px solid {rgba(spec.accent_secondary, 60)}; padding: 4px 8px; font-size: 10px; font-weight: 700;"
        )
        tags.addWidget(motif_tag)
        tags.addWidget(star_tag)
        tags.addStretch(1)
        layout.addLayout(tags)

        self._load_preview()

    def setChecked(self, checked: bool) -> None:
        super().setChecked(checked)
        self.setStyleSheet(self._qss(checked))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._load_preview()

    def _load_preview(self) -> None:
        pixmap = QPixmap(str(background_path(self.spec.id)))
        target_size = self.preview_label.size().expandedTo(QSize(200, 112))
        if pixmap.isNull():
            fallback = QPixmap(max(120, self.preview_label.width()), self.preview_label.height())
            fallback.fill(QColor(self.spec.sky_bottom))
            painter = QPainter(fallback)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(fallback.rect(), QColor(self.spec.sky_bottom))
            painter.fillRect(fallback.rect().adjusted(0, 0, 0, -fallback.height() // 3), QColor(self.spec.sky_mid))
            painter.fillRect(fallback.rect().adjusted(0, 0, 0, -fallback.height() * 2 // 3), QColor(self.spec.sky_top))
            painter.end()
            pixmap = fallback
        scaled = pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    def _qss(self, checked: bool) -> str:
        if checked:
            return (
                f"QPushButton {{ background: {rgba(self.spec.accent_primary, 18)}; border-radius: 24px; border: none; text-align: left; }}"
                f"QPushButton:hover {{ background: {rgba(self.spec.accent_primary, 22)}; }}"
            )
        return (
            "QPushButton { background: rgba(255, 255, 255, 0.04); border-radius: 24px; border: none; text-align: left; }"
            "QPushButton:hover { background: rgba(255, 255, 255, 0.07); }"
        )


class SectionTitle(QWidget):
    def __init__(self, title: str, subtitle: str, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("background: transparent; color: #edf4ff; font-size: 18px; font-weight: 800;")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet("background: transparent; color: #9fb1c9; font-size: 12px; line-height: 1.6;")
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)


class ThemeGalleryWidget(QWidget):
    selectionChanged = pyqtSignal(str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.theme_buttons = QButtonGroup(self)
        self.theme_buttons.setExclusive(True)
        self.background_buttons = QButtonGroup(self)
        self.background_buttons.setExclusive(True)
        self._suspend_emit = False
        self.current_theme_id = get_theme_profile(None).id
        self.current_background_id = list_backgrounds_for_theme(self.current_theme_id)[0].id
        self._setup_ui()
        self._render_themes()
        self._render_backgrounds()
        self._sync_summary()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(20)

        self.summary_card = ThemeHeaderCard()
        root.addWidget(self.summary_card)

        theme_box = QFrame()
        theme_box.setStyleSheet(
            "QFrame { background: rgba(10, 16, 30, 0.70); border-radius: 22px; border: none; }"
        )
        theme_layout = QVBoxLayout(theme_box)
        theme_layout.setContentsMargins(20, 18, 20, 18)
        theme_layout.setSpacing(14)
        theme_layout.addWidget(SectionTitle("主题色方案", "每套主题都会同步主窗口、详情弹窗、编辑弹窗与滚动条对比色。"))
        self.theme_grid = QGridLayout()
        self.theme_grid.setContentsMargins(0, 0, 0, 0)
        self.theme_grid.setSpacing(14)
        theme_layout.addLayout(self.theme_grid)
        root.addWidget(theme_box)

        bg_box = QFrame()
        bg_box.setStyleSheet(
            "QFrame { background: rgba(10, 16, 30, 0.70); border-radius: 22px; border: none; }"
        )
        bg_layout = QVBoxLayout(bg_box)
        bg_layout.setContentsMargins(20, 18, 20, 18)
        bg_layout.setSpacing(14)
        self.background_title = SectionTitle("背景图库", "同一主题下准备 5 张不同场景背景，保证文字阅读区依然保持柔和对比。")
        bg_layout.addWidget(self.background_title)
        self.background_grid = QGridLayout()
        self.background_grid.setContentsMargins(0, 0, 0, 0)
        self.background_grid.setSpacing(14)
        bg_layout.addLayout(self.background_grid)
        root.addWidget(bg_box)

    def set_selection(self, theme_id: str, background_id: str) -> None:
        self._suspend_emit = True
        self.current_theme_id = get_theme_profile(theme_id).id
        available = list_backgrounds_for_theme(self.current_theme_id)
        available_ids = {spec.id for spec in available}
        self.current_background_id = background_id if background_id in available_ids else available[0].id
        self._render_themes()
        self._render_backgrounds()
        self._sync_summary()
        self._suspend_emit = False

    def _render_themes(self) -> None:
        _clear_layout(self.theme_grid)
        self.theme_buttons = QButtonGroup(self)
        self.theme_buttons.setExclusive(True)
        for index, theme in enumerate(list_theme_profiles()):
            card = ThemeCardButton(theme)
            card.setChecked(theme.id == self.current_theme_id)
            card.chosen.connect(self._choose_theme)
            self.theme_buttons.addButton(card)
            self.theme_grid.addWidget(card, index // 2, index % 2)

    def _render_backgrounds(self) -> None:
        _clear_layout(self.background_grid)
        self.background_buttons = QButtonGroup(self)
        self.background_buttons.setExclusive(True)
        backgrounds = list_backgrounds_for_theme(self.current_theme_id)
        for index, spec in enumerate(backgrounds):
            card = BackgroundCardButton(spec)
            card.setChecked(spec.id == self.current_background_id)
            card.chosen.connect(self._choose_background)
            self.background_buttons.addButton(card)
            self.background_grid.addWidget(card, index // 3, index % 3)

    def _sync_summary(self) -> None:
        self.summary_card.set_theme(get_theme_profile(self.current_theme_id))
        current = get_background_spec(self.current_background_id)
        self.background_title.title_label.setText(f"背景图库 · {current.theme_name}")
        self.background_title.subtitle_label.setText(
            f"当前使用 {current.title}。该背景会作用于主窗口场景层，并根据主题同步字体和描边对比度。"
        )

    def _choose_theme(self, theme_id: str) -> None:
        if theme_id == self.current_theme_id:
            return
        self.current_theme_id = theme_id
        self.current_background_id = list_backgrounds_for_theme(theme_id)[0].id
        self._render_themes()
        self._render_backgrounds()
        self._sync_summary()
        if not self._suspend_emit:
            self.selectionChanged.emit(self.current_theme_id, self.current_background_id)

    def _choose_background(self, background_id: str) -> None:
        if background_id == self.current_background_id:
            return
        self.current_background_id = background_id
        self._render_backgrounds()
        self._sync_summary()
        if not self._suspend_emit:
            self.selectionChanged.emit(self.current_theme_id, self.current_background_id)