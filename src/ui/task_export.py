"""
task_export.py
──────────────
Export utilities for TaskForge task data.

Supports three export formats:

1. **Markdown** — human-readable checklist document.
2. **CSV** — spreadsheet-compatible, flat task list with all key fields.
3. **JSON** — structured hierarchical export preserving parent-child
   relationships, suitable for backup or migration.

All functions are pure (no side-effects beyond writing the target file)
and can be tested without a running Qt application.

Usage (from MainWindow or a QAction slot)::

    from ui.task_export import export_tasks_markdown, export_tasks_csv, export_tasks_json

    export_tasks_markdown(tasks, children_map, path)
    export_tasks_csv(tasks, path)
    export_tasks_json(tasks, children_map, path)
"""

from __future__ import annotations

import csv
import json
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any

# We intentionally avoid importing Task directly so this module stays
# importable without a database connection (useful for unit testing the
# formatting logic independently).


# ────────────────────────────────────────── internal helpers ─────────────────


def _fmt_dt(dt: datetime | None) -> str:
    """Return a human-readable date-time string or empty string."""
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M")


def _priority_emoji(priority: str) -> str:
    return {"高": "🔴", "中": "🟡", "低": "🔵"}.get(priority, "⚪")


def _checked(completed: bool) -> str:
    return "x" if completed else " "


# ────────────────────────────────────────── Markdown export ──────────────────


def export_tasks_markdown(
    tasks: list[Any],
    children_map: dict[int | None, list[Any]],
    output_path: Path | str,
    *,
    include_metadata: bool = True,
) -> None:
    """Export tasks to a Markdown checklist file.

    Parameters
    ----------
    tasks:
        All task objects (must have the attributes defined in ``Task``).
    children_map:
        Mapping of ``parent_id → [child_task, …]``.
    output_path:
        Destination file path.  Parent directories are created as needed.
    include_metadata:
        When *True*, each task block includes priority, due date, tags and
        estimated time as indented sub-lines.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    now_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    lines.append(f"# TaskForge 任务导出")
    lines.append(f"\n> 导出时间：{now_str}\n")
    lines.append("---\n")

    # Statistics summary
    total = len(tasks)
    completed_count = sum(1 for t in tasks if t.completed)
    lines.append(
        f"**任务总数**：{total}  |  "
        f"**已完成**：{completed_count}  |  "
        f"**进行中**：{total - completed_count}\n"
    )
    lines.append("---\n")

    def _write_branch(parent_id: int | None, depth: int = 0) -> None:
        for task in children_map.get(parent_id, []):
            indent = "  " * depth
            emoji = _priority_emoji(task.priority)
            checked_mark = _checked(task.completed)
            lines.append(f"{indent}- [{checked_mark}] {emoji} **{task.title}**")

            if include_metadata:
                meta_parts: list[str] = []
                if task.category:
                    meta_parts.append(f"分类: {task.category}")
                if task.priority:
                    meta_parts.append(f"优先级: {task.priority}")
                if task.due_at:
                    meta_parts.append(f"截止: {_fmt_dt(task.due_at)}")
                if task.tags:
                    meta_parts.append(f"标签: {task.tags}")
                if task.estimated_minutes:
                    meta_parts.append(f"预估: {task.estimated_minutes} 分钟")
                if task.tracked_minutes:
                    meta_parts.append(f"累计专注: {task.tracked_minutes} 分钟")
                if meta_parts:
                    lines.append(f"{indent}  *{' · '.join(meta_parts)}*")

                if task.description:
                    wrapped = textwrap.fill(
                        task.description, width=80,
                        initial_indent=indent + "  > ",
                        subsequent_indent=indent + "  > ",
                    )
                    lines.append(wrapped)

            _write_branch(task.id, depth + 1)

    _write_branch(None)

    output_path.write_text("\n".join(lines), encoding="utf-8")


# ────────────────────────────────────────── CSV export ───────────────────────

_CSV_FIELDS = [
    "id",
    "title",
    "description",
    "category",
    "tags",
    "priority",
    "due_at",
    "remind_at",
    "estimated_minutes",
    "tracked_minutes",
    "recurrence_rule",
    "completed",
    "completed_at",
    "parent_id",
    "created_at",
    "updated_at",
]

_CSV_HEADERS = {
    "id": "ID",
    "title": "任务标题",
    "description": "描述",
    "category": "分类",
    "tags": "标签",
    "priority": "优先级",
    "due_at": "截止时间",
    "remind_at": "提醒时间",
    "estimated_minutes": "预估分钟",
    "tracked_minutes": "已追踪分钟",
    "recurrence_rule": "循环规则",
    "completed": "已完成",
    "completed_at": "完成时间",
    "parent_id": "父任务ID",
    "created_at": "创建时间",
    "updated_at": "更新时间",
}


def export_tasks_csv(
    tasks: list[Any],
    output_path: Path | str,
) -> None:
    """Export a flat task list to CSV format.

    Parameters
    ----------
    tasks:
        All task objects.
    output_path:
        Destination ``.csv`` file path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    headers = [_CSV_HEADERS.get(f, f) for f in _CSV_FIELDS]

    with output_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(headers)
        for task in tasks:
            row: list[str] = []
            for field in _CSV_FIELDS:
                value = getattr(task, field, "")
                if isinstance(value, datetime):
                    value = _fmt_dt(value)
                elif isinstance(value, bool):
                    value = "是" if value else "否"
                elif value is None:
                    value = ""
                else:
                    value = str(value)
                row.append(value)
            writer.writerow(row)


# ────────────────────────────────────────── JSON export ──────────────────────


def _task_to_dict(task: Any) -> dict[str, Any]:
    """Convert a Task ORM object to a plain serialisable dict."""
    return {
        "id": task.id,
        "title": task.title,
        "description": getattr(task, "description", ""),
        "category": task.category,
        "tags": task.tags,
        "priority": task.priority,
        "due_at": _fmt_dt(task.due_at),
        "remind_at": _fmt_dt(getattr(task, "remind_at", None)),
        "estimated_minutes": getattr(task, "estimated_minutes", 0),
        "tracked_minutes": getattr(task, "tracked_minutes", 0),
        "recurrence_rule": getattr(task, "recurrence_rule", ""),
        "completed": task.completed,
        "completed_at": _fmt_dt(getattr(task, "completed_at", None)),
        "parent_id": getattr(task, "parent_id", None),
        "created_at": _fmt_dt(getattr(task, "created_at", None)),
        "updated_at": _fmt_dt(getattr(task, "updated_at", None)),
    }


def export_tasks_json(
    tasks: list[Any],
    children_map: dict[int | None, list[Any]],
    output_path: Path | str,
    *,
    pretty: bool = True,
) -> None:
    """Export tasks to a hierarchical JSON file.

    Each task node may contain a ``children`` list with its subtasks,
    mirroring the in-app tree structure.

    Parameters
    ----------
    tasks:
        All task objects.
    children_map:
        Mapping of ``parent_id → [child_task, …]``.
    output_path:
        Destination ``.json`` file path.
    pretty:
        When *True* (default) the JSON is indented for readability.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    def _build_node(task: Any) -> dict[str, Any]:
        node = _task_to_dict(task)
        children = children_map.get(task.id, [])
        if children:
            node["children"] = [_build_node(c) for c in children]
        else:
            node["children"] = []
        return node

    root_tasks = children_map.get(None, [])
    payload: dict[str, Any] = {
        "export_version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "total_tasks": len(tasks),
        "completed_tasks": sum(1 for t in tasks if t.completed),
        "tasks": [_build_node(t) for t in root_tasks],
    }

    indent = 2 if pretty else None
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=indent),
        encoding="utf-8",
    )


# ────────────────────────────────────────── import (JSON round-trip) ─────────


def load_tasks_from_json(json_path: Path | str) -> list[dict[str, Any]]:
    """Load a previously exported JSON file and return a flat list of task dicts.

    The hierarchical ``children`` nesting is flattened; ``parent_id`` fields
    are preserved so the caller can reconstruct the tree.

    Parameters
    ----------
    json_path:
        Path to a ``.json`` file produced by :func:`export_tasks_json`.

    Returns
    -------
    list[dict]
        Flat list of task dicts, each carrying all exported fields.

    Raises
    ------
    FileNotFoundError
        If the supplied path does not exist.
    ValueError
        If the JSON is malformed or the version is unsupported.
    """
    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"导入文件不存在：{json_path}")

    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 格式错误：{exc}") from exc

    version = payload.get("export_version", "")
    if not version.startswith("1."):
        raise ValueError(f"不支持的导出版本：{version!r}")

    result: list[dict[str, Any]] = []

    def _flatten(node_list: list[dict[str, Any]]) -> None:
        for node in node_list:
            children = node.pop("children", [])
            result.append(node)
            _flatten(children)

    _flatten(list(payload.get("tasks", [])))
    return result


# ────────────────────────────────────────── statistics helpers ────────────────


def compute_export_stats(tasks: list[Any]) -> dict[str, Any]:
    """Compute a summary statistics dict from a task list.

    Returns a dict with keys::

        total, completed, pending, overdue,
        high_priority, med_priority, low_priority,
        completion_rate,          # float 0–100
        total_estimated_minutes,
        total_tracked_minutes,
        categories,               # {name: count}
        tags,                     # {tag: count}

    Parameters
    ----------
    tasks:
        All task objects (must expose the standard Task attributes).
    """
    now = datetime.now()
    total = len(tasks)
    completed = sum(1 for t in tasks if t.completed)
    overdue = sum(
        1 for t in tasks
        if not t.completed and t.due_at and t.due_at < now
    )
    high = sum(1 for t in tasks if t.priority == "高")
    med = sum(1 for t in tasks if t.priority == "中")
    low = sum(1 for t in tasks if t.priority == "低")

    categories: dict[str, int] = {}
    tags_count: dict[str, int] = {}
    total_est = 0
    total_tracked = 0

    for task in tasks:
        cat = task.category or "未分类"
        categories[cat] = categories.get(cat, 0) + 1

        raw_tags = task.tags or ""
        for tag in (t.strip() for t in raw_tags.split(",") if t.strip()):
            tags_count[tag] = tags_count.get(tag, 0) + 1

        total_est += getattr(task, "estimated_minutes", 0) or 0
        total_tracked += getattr(task, "tracked_minutes", 0) or 0

    return {
        "total": total,
        "completed": completed,
        "pending": total - completed,
        "overdue": overdue,
        "high_priority": high,
        "med_priority": med,
        "low_priority": low,
        "completion_rate": round(completed / total * 100, 1) if total else 0.0,
        "total_estimated_minutes": total_est,
        "total_tracked_minutes": total_tracked,
        "categories": dict(sorted(categories.items(), key=lambda x: -x[1])),
        "tags": dict(sorted(tags_count.items(), key=lambda x: -x[1])),
    }
