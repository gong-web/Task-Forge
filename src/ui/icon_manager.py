from pathlib import Path
import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

class IconManager:
    _instance = None
    _cache = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IconManager, cls).__new__(cls)
            cls._instance.logger = logging.getLogger("task_forge")
            cls._instance.asset_root = Path(__file__).resolve().parent.parent / "assets"
            cls._instance.base_path = cls._instance.asset_root / "icons"
            cls._instance.search_paths = [
                cls._instance.base_path,
                cls._instance.asset_root / "downloaded" / "svg",
                cls._instance.asset_root / "downloaded" / "png",
            ]
        return cls._instance

    def get_icon(self, name, size=24, color=None):
        key = f"{name}_{size}_{color}"
        if key in self._cache:
            return self._cache[key]

        path = self.resolve_path(name)
        if path is None:
            self.logger.warning("图标资源不存在: %s", name)
            return QIcon()

        pixmap = self._load_pixmap(path, size, color)
        icon = QIcon(pixmap)
        self._cache[key] = icon
        return icon

    def get_pixmap(self, name, size=24, color=None):
        path = self.resolve_path(name)
        if path is None:
            return QPixmap(size, size)
        return self._load_pixmap(path, size, color)

    def resolve_path(self, name) -> Path | None:
        raw_name = Path(str(name))
        if raw_name.is_absolute() and raw_name.exists():
            return raw_name

        if raw_name.suffix:
            if len(raw_name.parts) > 1:
                candidate = self.asset_root / raw_name
                if candidate.exists():
                    return candidate
            for directory in self.search_paths:
                candidate = directory / raw_name.name
                if candidate.exists():
                    return candidate

        for directory in self.search_paths:
            for extension in (".svg", ".png", ".jpg", ".jpeg", ".webp"):
                candidate = directory / f"{raw_name.name}{extension}"
                if candidate.exists():
                    return candidate
        return None

    def _load_pixmap(self, path: Path, size: int, color=None) -> QPixmap:
        suffix = path.suffix.lower()
        if suffix == ".svg":
            renderer = QSvgRenderer(str(path))
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            if color:
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                painter.fillRect(pixmap.rect(), QColor(color))
            painter.end()
            return pixmap

        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return QPixmap(size, size)
        scaled = pixmap.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        if color is None:
            return scaled
        tinted = QPixmap(scaled.size())
        tinted.fill(Qt.GlobalColor.transparent)
        painter = QPainter(tinted)
        painter.drawPixmap(0, 0, scaled)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), QColor(color))
        painter.end()
        return tinted
