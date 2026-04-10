"""
shortcuts_dialog.py
───────────────────
Keyboard-shortcut reference dialog for TaskForge.

Displays all registered shortcuts grouped by category in a clean, scrollable
table.  Activated via the menu or the ``?`` title-bar button.

Usage
-----
::

    dlg = ShortcutsDialog(parent=self)
    dlg.exec()
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QKeyEvent, QKeySequence, QMouseEvent
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.icon_manager import IconManager


# ─────────────────────────── shortcut catalogue ──────────────────────────────

_SHORTCUT_GROUPS: list[tuple[str, str, list[tuple[str, str]]]] = [
    (
        "任务操作",
        "#60a5fa",
        [
            ("Ctrl+N", "新建根任务"),
            ("Ctrl+Shift+N", "新建子任务"),
            ("Ctrl+E", "编辑选中任务"),
            ("Delete / Backspace", "删除选中任务"),
            ("Space", "切换任务完成状态"),
            ("Ctrl+D", "复制任务"),
            ("Ctrl+Shift+D", "复制任务（含子任务）"),
        ],
    ),
    (
        "导航与视图",
        "#34d399",
        [
            ("Ctrl+1", "今日视图"),
            ("Ctrl+2", "计划视图"),
            ("Ctrl+3", "已完成视图"),
            ("Ctrl+4", "日历视图"),
            ("Ctrl+5", "看板视图"),
            ("Ctrl+Tab", "切换到下一视图"),
            ("Ctrl+Shift+Tab", "切换到上一视图"),
        ],
    ),
    (
        "专注计时器",
        "#f472b6",
        [
            ("Ctrl+P", "开始 / 暂停专注计时"),
            ("Ctrl+Shift+P", "重置计时器"),
            ("Ctrl+Shift+F", "进入 / 退出专注模式"),
        ],
    ),
    (
        "编辑器与写作",
        "#c084fc",
        [
            ("Ctrl+Z", "撤销"),
            ("Ctrl+Shift+Z", "重做"),
            ("Ctrl+A", "全选"),
            ("Ctrl+X / C / V", "剪切 / 复制 / 粘贴"),
            ("Ctrl+F", "在当前视图中搜索"),
        ],
    ),
    (
        "窗口控制",
        "#fbbf24",
        [
            ("Ctrl+W", "关闭对话框"),
            ("Ctrl+M", "最小化窗口"),
            ("F11", "切换最大化"),
            ("Ctrl+,", "打开设置"),
            ("Ctrl+?", "打开快捷键参考（本窗口）"),
        ],
    ),
    (
        "数据与同步",
        "#f97316",
        [
            ("Ctrl+S", "手动保存 / 同步"),
            ("Ctrl+Shift+E", "导出任务数据"),
            ("Ctrl+Shift+I", "导入任务数据"),
        ],
    ),
]


# ─────────────────────────── helper widgets ──────────────────────────────────


class _KeyBadge(QLabel):
    """Pill-shaped badge displaying a keyboard shortcut key."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setFamily("Consolas, 'Courier New', monospace")
        font.setPointSize(10)
        self.setFont(font)
        self.setStyleSheet(
            "QLabel {"
            "  background: rgba(255,255,255,0.08);"
            "  border: 1px solid rgba(255,255,255,0.18);"
            "  border-radius: 5px;"
            "  color: #e2e8f0;"
            "  padding: 2px 8px;"
            "  font-weight: 600;"
            "}"
        )
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)


class _ShortcutRow(QWidget):
    """One shortcut row: [key badge(s)] + description label."""

    def __init__(self, shortcut: str, description: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 2, 0, 2)
        row.setSpacing(12)

        # Support "key1 / key2" patterns
        parts = [p.strip() for p in shortcut.split("/")]
        for idx, part in enumerate(parts):
            row.addWidget(_KeyBadge(part))
            if idx < len(parts) - 1:
                sep = QLabel("/")
                sep.setStyleSheet("color: #64748b; font-size: 11px;")
                row.addWidget(sep)

        desc = QLabel(description)
        desc.setStyleSheet("color: #cbd5e1; font-size: 13px;")
        row.addWidget(desc, 1)


class _GroupCard(QFrame):
    """Card containing one shortcut group (header + rows)."""

    def __init__(
        self,
        title: str,
        accent: str,
        shortcuts: list[tuple[str, str]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("shortcutCard")
        self.setStyleSheet(
            "#shortcutCard {"
            "  background: rgba(255,255,255,0.04);"
            "  border: 1px solid rgba(255,255,255,0.09);"
            "  border-radius: 10px;"
            "}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Header with coloured dot
        header = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {accent}; font-size: 14px;")
        header.addWidget(dot)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color: {accent}; font-size: 14px; font-weight: 700;"
        )
        header.addWidget(title_lbl, 1)
        layout.addLayout(header)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background: {accent}; max-height: 1px; opacity: 0.3;")
        layout.addWidget(line)

        # Rows
        for key, desc in shortcuts:
            layout.addWidget(_ShortcutRow(key, desc))


# ─────────────────────────── main dialog ─────────────────────────────────────


class ShortcutsDialog(QDialog):
    """Full keyboard shortcut reference dialog.

    Parameters
    ----------
    parent:
        Owner widget for proper z-order stacking.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("键盘快捷键参考")
        self.setModal(True)
        self.setMinimumSize(560, 640)
        self.resize(560, 720)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet(
            "QDialog { background: #111827; border-radius: 14px; }"
        )
        self._build_ui()

    # ── layout ────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Title bar
        title_bar = self._make_title_bar()
        root.addWidget(title_bar)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        grid = QVBoxLayout(content)
        grid.setContentsMargins(20, 16, 20, 24)
        grid.setSpacing(14)

        # Subtitle
        sub = QLabel("以下快捷键在主界面下全局生效。对话框聚焦时部分快捷键可能不响应。")
        sub.setWordWrap(True)
        sub.setStyleSheet("color: #64748b; font-size: 12px;")
        grid.addWidget(sub)

        for group_title, accent, shortcuts in _SHORTCUT_GROUPS:
            card = _GroupCard(group_title, accent, shortcuts)
            grid.addWidget(card)

        grid.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    def _make_title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(52)
        bar.setStyleSheet("background: rgba(255,255,255,0.05); border-radius: 0;")

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 12, 0)
        layout.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(IconManager().get_pixmap("settings", size=20, color="#94a3b8"))
        layout.addWidget(icon_lbl)

        title = QLabel("键盘快捷键参考")
        title.setStyleSheet("color: #f1f5f9; font-size: 15px; font-weight: 700;")
        layout.addWidget(title, 1)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(
            "QPushButton { background: rgba(239,68,68,0.2); border: none;"
            " border-radius: 14px; color: #ef4444; font-size: 12px; }"
            "QPushButton:hover { background: rgba(239,68,68,0.4); }"
        )
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        return bar

    # ── allow dragging ────────────────────────────────────────────────────────

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:  # noqa: N802
        if a0 is None:
            return
        if a0.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = a0.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:  # noqa: N802
        if a0 is None:
            return
        if a0.buttons() == Qt.MouseButton.LeftButton and hasattr(self, "_drag_pos"):
            self.move(a0.globalPosition().toPoint() - self._drag_pos)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:  # noqa: N802
        if a0 is None:
            return
        if a0.key() in (Qt.Key.Key_Escape, Qt.Key.Key_W) and (
            a0.modifiers() == Qt.KeyboardModifier.NoModifier
            or a0.key() == Qt.Key.Key_W
        ):
            self.accept()
        super().keyPressEvent(a0)
