from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, Qt, QTimer, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from core.reminder_sounds import reminder_sound_label
from ui.scroll_area import SmartScrollArea
from ui.celestial_theme_catalog import get_theme_profile
from ui.reminder_experience import ReminderExperienceGalleryWidget, reminder_animation_label
from ui.theme_gallery import ThemeGalleryWidget
from ui.theme import (
    ACCENT_BORDER_SOFT,
    DANGER_SURFACE_BG,
    DANGER_SURFACE_BORDER,
    DANGER_SURFACE_TEXT,
    SURFACE_BG_ACCENT,
    SURFACE_BG_HOVER,
    SURFACE_BG_RAISED,
    SURFACE_BORDER,
    SURFACE_TEXT_MUTED,
    SURFACE_TEXT_PRIMARY,
    SURFACE_TEXT_SECONDARY,
    surface_style,
    text_style,
)


SETTING_META = [
    ("toggle_sync", "自动同步", "自动导出本地快照文件，并在切换任务后刷新看板与分析中心。"),
    ("toggle_noise", "专注白噪音", "专注计时开始后自动播放白噪音，暂停或结束时自动停止。"),
    ("toggle_strict", "番茄钟严格模式", "专注开始后禁止暂停与重置，直到当前专注轮次结束。"),
    ("toggle_notify", "任务到期提醒", "关闭后不再弹出到期提醒窗口。"),
    ("toggle_perf", "性能模式", "关闭阴影与部分视觉效果，减少低配设备的绘制压力。"),
]

WORKSPACE_ACTION_META = [
    ("add_root_task", "新建任务", "聚焦左侧新建任务区，直接创建新的顶层任务。", "primary"),
    ("export_data", "导出数据", "将当前任务与便签导出为本地 JSON 备份文件。", "secondary"),
    ("import_data", "导入数据", "从已有备份恢复任务和便签数据。", "ghost"),
    ("export_week_report", "周报导出", "生成当前数据的 Markdown 周报，用于提交或归档。", "ghost"),
    ("open_category_manager", "分类管理", "维护任务分类列表，清理重复分类。", "ghost"),
]


class ModernToggle(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(52, 28)
        self._checked = False
        self._position = 4
        self.animation = QPropertyAnimation(self, b"position")
        self.animation.setDuration(180)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

    @pyqtProperty(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value
        self.update()

    def set_checked(self, checked: bool) -> None:
        self._checked = checked
        self._position = 30 if checked else 4
        self.update()

    def is_checked(self) -> bool:
        return self._checked

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            self.animation.stop()
            self.animation.setStartValue(self._position)
            self.animation.setEndValue(30 if self._checked else 4)
            self.animation.start()
            self.toggled.emit(self._checked)
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0, 0, self.width(), self.height())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#60a5fa") if self._checked else QColor("#475569"))
        painter.drawRoundedRect(rect, 14, 14)
        painter.setBrush(QColor(SURFACE_TEXT_PRIMARY))
        painter.drawEllipse(QRectF(self._position, 5, 18, 18))


class SettingCard(QFrame):
    toggled = pyqtSignal(str, bool)

    def __init__(self, key: str, title: str, description: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.setObjectName("settingCard")
        self.setStyleSheet(
            surface_style(
                SURFACE_BG_RAISED,
                20,
                border="rgba(255,255,255,0)",
                selector="QFrame#settingCard",
                hover_background=SURFACE_BG_HOVER,
                hover_border="rgba(255,255,255,0)",
            )
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(12)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(text_style(SURFACE_TEXT_PRIMARY, 18, 700))
        self.state_label = QLabel("已关闭")
        self.state_label.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 12))
        self.toggle = ModernToggle()
        self.toggle.toggled.connect(self._emit_toggle)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.state_label)

        top.addLayout(title_box, 1)
        top.addWidget(self.toggle)

        self.desc_label = QLabel(description)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet(text_style(SURFACE_TEXT_SECONDARY, 13) + " line-height: 1.6;")

        self.meta_label = QLabel("")
        self.meta_label.setWordWrap(True)
        self.meta_label.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 12))

        layout.addLayout(top)
        layout.addWidget(self.desc_label)
        layout.addWidget(self.meta_label)

    def set_checked(self, checked: bool) -> None:
        self.toggle.set_checked(checked)
        self._update_state_label(checked)

    def set_meta(self, text: str) -> None:
        self.meta_label.setText(text)

    def _emit_toggle(self, checked: bool) -> None:
        self._update_state_label(checked)
        self.toggled.emit(self.key, checked)

    def _update_state_label(self, checked: bool) -> None:
        self.state_label.setText("已开启" if checked else "已关闭")
        self.state_label.setStyleSheet(
            text_style('#34d399' if checked else SURFACE_TEXT_MUTED, 12)
        )


class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards: dict[str, SettingCard] = {}
        self.status_line: QLabel | None = None
        self.theme_gallery: ThemeGalleryWidget | None = None
        self.reminder_gallery: ReminderExperienceGalleryWidget | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = SmartScrollArea()
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(36, 28, 36, 36)
        content_layout.setSpacing(24)
        self.status_line = QLabel("")
        self.status_line.setWordWrap(True)
        self.status_line.setStyleSheet(text_style(SURFACE_TEXT_MUTED, 12))
        self.status_line.hide()
        content_layout.addWidget(self.status_line)

        tabs = QTabWidget()
        tabs.setObjectName("settingsTabs")
        tabs.setStyleSheet(
            "QTabWidget#settingsTabs::pane { border: none; background: transparent; }"
            "QTabBar::tab { background: rgba(255,255,255,0.04); border: none; border-radius: 12px; color: #9fb1c9; font-size: 13px; font-weight: 700; padding: 9px 18px; margin-right: 6px; }"
            "QTabBar::tab:selected { background: rgba(96,165,250,0.18); color: #edf4ff; }"
            "QTabBar::tab:hover:!selected { background: rgba(255,255,255,0.08); color: #dbe7f7; }"
        )
        tabs.addTab(self._build_theme_tab(), "主题外观")
        tabs.addTab(self._build_preferences_tab(), "系统偏好")
        tabs.addTab(self._build_reminder_experience_tab(), "提醒体验")
        tabs.addTab(self._build_workspace_tab(), "工作区操作")
        content_layout.addWidget(tabs)
        content_layout.addStretch(1)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _build_theme_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(18)

        self.theme_gallery = ThemeGalleryWidget(self)
        self.theme_gallery.selectionChanged.connect(self._handle_theme_selection)
        layout.addWidget(self.theme_gallery)
        layout.addStretch(1)
        return tab

    def _build_preferences_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(18)

        grid = QGridLayout()
        grid.setSpacing(18)
        for index, (key, title, description) in enumerate(SETTING_META):
            card = SettingCard(key, title, description)
            card.toggled.connect(self._handle_setting_change)
            self.cards[key] = card
            grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(grid)
        layout.addStretch(1)
        return tab

    def _build_reminder_experience_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(18)

        self.reminder_gallery = ReminderExperienceGalleryWidget(self)
        self.reminder_gallery.soundChanged.connect(self._handle_reminder_sound_change)
        self.reminder_gallery.animationChanged.connect(self._handle_reminder_animation_change)
        self.reminder_gallery.previewSoundRequested.connect(self._preview_reminder_sound)
        self.reminder_gallery.previewAnimationRequested.connect(self._preview_reminder_animation)
        self.reminder_gallery.previewExperienceRequested.connect(self._preview_reminder_experience)

        footnote = QFrame()
        footnote.setStyleSheet(surface_style(SURFACE_BG_ACCENT, 20, border="rgba(255,255,255,0)"))
        footnote_layout = QVBoxLayout(footnote)
        footnote_layout.setContentsMargins(20, 18, 20, 18)
        footnote_layout.setSpacing(8)
        footnote_title = QLabel("提醒资源说明")
        footnote_title.setStyleSheet(text_style(SURFACE_TEXT_PRIMARY, 16, 700))
        footnote_desc = QLabel("新增提示音为应用内合成生成，可离线使用；提醒动画与主题解耦，可单独切换。")
        footnote_desc.setWordWrap(True)
        footnote_desc.setStyleSheet(text_style(SURFACE_TEXT_SECONDARY, 13) + " line-height: 1.6;")
        footnote_layout.addWidget(footnote_title)
        footnote_layout.addWidget(footnote_desc)

        layout.addWidget(self.reminder_gallery)
        layout.addWidget(footnote)
        layout.addStretch(1)
        return tab

    def _build_workspace_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(18)

        action_grid = QGridLayout()
        action_grid.setSpacing(18)
        for index, (action_name, title, description, role) in enumerate(WORKSPACE_ACTION_META):
            action_grid.addWidget(self._build_workspace_action_tile(action_name, title, description, role), index // 2, index % 2)
        layout.addLayout(action_grid)

        danger_box = QFrame()
        danger_box.setStyleSheet(
            surface_style(DANGER_SURFACE_BG, 22, border="rgba(255,255,255,0)")
        )
        danger_layout = QVBoxLayout(danger_box)
        danger_layout.setContentsMargins(24, 20, 24, 20)
        danger_layout.setSpacing(10)
        danger_title = QLabel("危险操作")
        danger_title.setStyleSheet(text_style(SURFACE_TEXT_PRIMARY, 18, 700))
        danger_desc = QLabel("清除任务与便签数据库。该操作会立即刷新所有视图，并且无法撤销。")
        danger_desc.setWordWrap(True)
        danger_desc.setStyleSheet(text_style(DANGER_SURFACE_TEXT, 13) + " line-height: 1.6;")
        clear_button = QPushButton("清除所有数据")
        clear_button.setFixedWidth(160)
        clear_button.setProperty("role", "primary")
        clear_button.clicked.connect(self._handle_clear_data)
        danger_layout.addWidget(danger_title)
        danger_layout.addWidget(danger_desc)
        danger_layout.addWidget(clear_button)
        layout.addWidget(danger_box)
        layout.addStretch(1)
        return tab

    def _build_workspace_action_tile(self, action_name: str, title: str, description: str, role: str) -> QWidget:
        card = QFrame()
        card.setStyleSheet(surface_style(SURFACE_BG_RAISED, 20, border="rgba(255,255,255,0)"))
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setStyleSheet(text_style(SURFACE_TEXT_PRIMARY, 18, 700))
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(text_style(SURFACE_TEXT_SECONDARY, 13) + " line-height: 1.6;")
        action_button = QPushButton(title)
        action_button.setProperty("role", role)
        action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        action_button.clicked.connect(lambda _checked=False, name=action_name, label=title: self._run_workspace_action(name, label))

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addWidget(action_button, 0, Qt.AlignmentFlag.AlignLeft)
        return card

    def sync_from_main_window(self) -> None:
        main_window = self.window()
        if main_window is None:
            return
        mapping = {
            "toggle_sync": bool(main_window.settings.value("toggle_sync", False, type=bool)),
            "toggle_noise": bool(getattr(main_window, "play_white_noise", False)),
            "toggle_strict": bool(getattr(main_window, "strict_pomodoro", False)),
            "toggle_notify": bool(getattr(main_window, "enable_notifications", True)),
            "toggle_perf": bool(getattr(main_window, "performance_mode", False)),
        }
        meta = {
            "toggle_sync": f"当前数据库：{getattr(main_window.db, '_db_file', '')}",
            "toggle_noise": "将在专注计时器开始、暂停与完成时联动音频状态。",
            "toggle_strict": "严格模式下暂停与重置会被拦截。",
            "toggle_notify": "提醒窗口会遵循此开关执行。",
            "toggle_perf": "关闭阴影与重绘增强，优先保证流畅度。",
        }
        for key, card in self.cards.items():
            card.set_checked(mapping.get(key, False))
            card.set_meta(meta.get(key, ""))
        if self.reminder_gallery is not None:
            self.reminder_gallery.set_selection(
                getattr(main_window, "reminder_sound_id", None),
                getattr(main_window, "reminder_animation_id", None),
            )
        if self.theme_gallery is not None:
            self.theme_gallery.set_selection(
                getattr(main_window, "theme_id", "orion_blue"),
                getattr(main_window, "background_id", "orion_blue_galaxy_ridge"),
            )

    def _show_status(self, text: str) -> None:
        if self.status_line is None:
            return
        self.status_line.setText(text)
        self.status_line.show()

    def _handle_setting_change(self, action: str, checked: bool) -> None:
        main_window = self.window()
        if main_window is None:
            return
        main_window.apply_runtime_setting(action, checked)
        label = next((title for key, title, _ in SETTING_META if key == action), action)
        self._show_status(f"{label} 已{'开启' if checked else '关闭'}。")
        self.sync_from_main_window()

    def _handle_theme_selection(self, theme_id: str, background_id: str) -> None:
        main_window = self.window()
        if main_window is None:
            return
        if hasattr(main_window, "apply_theme_selection"):
            main_window.apply_theme_selection(theme_id, background_id)
        self._show_status(f"已切换到主题 {get_theme_profile(theme_id).name}。")

    def _handle_reminder_sound_change(self, sound_id: str) -> None:
        main_window = self.window()
        if main_window is None:
            return
        if hasattr(main_window, "apply_reminder_sound_choice"):
            main_window.apply_reminder_sound_choice(sound_id)
        if hasattr(main_window, "preview_reminder_sound"):
            main_window.preview_reminder_sound()
        self._show_status(f"提醒铃声已切换为“{reminder_sound_label(sound_id)}”，并已自动试听。")

    def _handle_reminder_animation_change(self, animation_id: str) -> None:
        main_window = self.window()
        if main_window is None:
            return
        if hasattr(main_window, "apply_reminder_animation_choice"):
            main_window.apply_reminder_animation_choice(animation_id)
        if hasattr(main_window, "preview_reminder_animation"):
            main_window.preview_reminder_animation()
        self._show_status(f"提醒动画已切换为“{reminder_animation_label(animation_id)}”，并已自动预览。")

    def _preview_reminder_sound(self) -> None:
        main_window = self.window()
        if main_window is None:
            return
        if hasattr(main_window, "preview_reminder_sound"):
            main_window.preview_reminder_sound()
        self._show_status("已播放当前提醒铃声。")

    def _preview_reminder_animation(self) -> None:
        main_window = self.window()
        if main_window is None:
            return
        if hasattr(main_window, "preview_reminder_animation"):
            main_window.preview_reminder_animation()
        self._show_status("已预览当前提醒动画。")

    def _preview_reminder_experience(self) -> None:
        main_window = self.window()
        if main_window is None:
            return
        if hasattr(main_window, "preview_reminder_experience"):
            main_window.preview_reminder_experience()
        self._show_status("已同时预览当前提醒提示音与动画。")

    def _run_workspace_action(self, action_name: str, title: str) -> None:
        main_window = self.window()
        if main_window is None:
            return
        action = getattr(main_window, action_name, None)
        if callable(action):
            action()
            self._show_status(f"已执行“{title}”。")

    def _handle_clear_data(self) -> None:
        main_window = self.window()
        if main_window is None:
            return
        reply = QMessageBox.warning(
            self,
            "警告",
            "确定要清除所有任务与便签数据吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        main_window.db.clear_all_data()
        main_window.refresh_everything()
        self.sync_from_main_window()
        QMessageBox.information(self, "已完成", "本地任务与便签数据已清空。")
