import os
import sys
from pathlib import Path


def _configure_qt_font_directory() -> None:
    if os.environ.get("QT_QPA_FONTDIR"):
        return
    candidates: list[Path] = []
    windir = os.environ.get("WINDIR")
    if windir:
        candidates.append(Path(windir) / "Fonts")
    candidates.append(Path("C:/Windows/Fonts"))
    for candidate in candidates:
        if candidate.exists():
            os.environ["QT_QPA_FONTDIR"] = str(candidate)
            return


_configure_qt_font_directory()

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QFontDatabase
from MainWindow import MainWindow
from runtime_support import load_config, read_bool_setting, setup_logging
from DB import DB
from data_seeder import seed_database_if_empty
from ui.theme import APP_FONT_CANDIDATES, build_app_stylesheet, ensure_app_fonts_loaded
from ui.celestial_theme_catalog import get_theme_profile, scene_palette_for_theme


def _pick_application_font_family() -> str:
    families = set(QFontDatabase.families())
    for family in APP_FONT_CANDIDATES:
        if family in families:
            return family
    return next(iter(APP_FONT_CANDIDATES))

def apply_theme(is_dark_mode: bool, palette_override=None) -> None:
    app = QApplication.instance()
    if app is not None:
        ensure_app_fonts_loaded()
        font = QFont(_pick_application_font_family())
        font.setPointSizeF(10.5)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        try:
            font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        except Exception:
            pass
        app.setFont(font)
        app.setStyle("Fusion")
        app.setStyleSheet(build_app_stylesheet(is_dark_mode, palette_override))


if __name__ == '__main__':
    _configure_qt_font_directory()
    config = load_config()
    logger = setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("Task Forge")
    
    # Init DB and seed
    db = DB()
    seed_database_if_empty(db)
    
    theme_profile = get_theme_profile(config.get("theme_id"))
    apply_theme(True, scene_palette_for_theme(theme_profile))
    window = MainWindow()
    logger.info("应用启动完成")
    window.show()
    sys.exit(app.exec())
