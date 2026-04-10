from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    path = project_root() / "data"
    path.mkdir(exist_ok=True)
    return path


def load_config() -> dict[str, Any]:
    config_path = data_dir() / "app_config.json"
    default = {
        "theme": "light",
        "theme_id": "orion_blue",
        "background_id": "orion_blue_galaxy_ridge",
        "reminder_interval_ms": 15000,
        "default_pomodoro_minutes": 25,
        "ai_api_base": "https://yunwu.ai/v1",
        "ai_model": "gpt-4o",
        "ai_api_key": "",
        "ai_timeout_sec": 30,
    }
    if not config_path.exists():
        config_path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
        return default
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default
    if not isinstance(payload, dict):
        return default
    merged = default.copy()
    merged.update(payload)
    return merged


def save_config(changes: dict[str, Any]) -> dict[str, Any]:
    config_path = data_dir() / "app_config.json"
    merged = load_config()
    merged.update(changes)
    config_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return merged


def setup_logging() -> logging.Logger:
    log_path = data_dir() / "task_forge.log"
    logger = logging.getLogger("task_forge")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    return logger


def read_bool_setting(name: str, default: bool) -> bool:
    try:
        from PyQt6.QtCore import QSettings
    except ImportError:
        return default
    settings = QSettings("TaskForge", "TaskForgeDesktop")
    return settings.value(name, default, type=bool)
