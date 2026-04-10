from __future__ import annotations

import csv
import json
import logging
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Iterable, Optional

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session, sessionmaker

from Note import Note
from Task import BaseClass, Task
from runtime_support import read_bool_setting


DEFAULT_DB_NAME = "task_forge.db"
LEGACY_DB_NAME = "task_studio.db"


class DB:
    def __init__(self, db_name: str = DEFAULT_DB_NAME):
        self._logger = logging.getLogger("task_forge")
        self._db_name = db_name
        self._project_root = Path(__file__).resolve().parent.parent
        self._data_dir = self._project_root / "data"
        self._data_dir.mkdir(exist_ok=True)
        self._category_file = self._data_dir / "categories.json"
        self._db_file = self._resolve_db_path(db_name)
        
        auto_backup = read_bool_setting("auto_backup", True)
        
        # Auto-backup on start
        if auto_backup and self._db_file.exists():
            import shutil
            try:
                shutil.copy2(self._db_file, self._db_file.with_suffix(".db.bak"))
            except OSError as exc:
                self._logger.warning("自动备份数据库失败: %s", exc)
                
        self._db_path = f"sqlite:///{self._db_file.as_posix()}"
        self._engine = create_engine(
            self._db_path,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False},
        )
        self._session_factory = sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            future=True,
        )
        BaseClass.metadata.create_all(self._engine)
        self._ensure_schema()

    def _resolve_db_path(self, db_name: str) -> Path:
        db_path = Path(db_name)
        if not db_path.is_absolute():
            db_path = self._project_root / db_path if db_path.parent != Path(".") else self._data_dir / db_path
        if db_name == DEFAULT_DB_NAME and not db_path.exists():
            legacy_path = self._data_dir / LEGACY_DB_NAME
            if legacy_path.exists():
                try:
                    legacy_path.replace(db_path)
                    self._logger.info("已将旧数据库迁移为 %s", db_path.name)
                except OSError as exc:
                    self._logger.warning("迁移旧数据库失败，继续使用旧库: %s", exc)
                    return legacy_path
        return db_path

    def _ensure_schema(self) -> None:
        with self._engine.begin() as connection:
            columns = {
                row[1]
                for row in connection.execute(text("PRAGMA table_info(tasks)")).fetchall()
            }
            migrations = {
                "tags": "ALTER TABLE tasks ADD COLUMN tags TEXT NOT NULL DEFAULT ''",
                "tracked_minutes": "ALTER TABLE tasks ADD COLUMN tracked_minutes INTEGER NOT NULL DEFAULT 0",
                "progress": "ALTER TABLE tasks ADD COLUMN progress INTEGER NOT NULL DEFAULT 0",
                "recurrence_rule": "ALTER TABLE tasks ADD COLUMN recurrence_rule TEXT NOT NULL DEFAULT '不重复'",
            }
            for column, sql in migrations.items():
                if column not in columns:
                    connection.execute(text(sql))

    def list_tasks(self) -> list[Task]:
        with self._session_factory() as session:
            statement = select(Task).order_by(Task.sort_order, Task.created_at, Task.id)
            return list(session.scalars(statement).all())

    def get_task(self, task_id: int) -> Optional[Task]:
        with self._session_factory() as session:
            return session.get(Task, task_id)

    def get_note(self, note_id: int) -> Optional[Note]:
        with self._session_factory() as session:
            return session.get(Note, note_id)

    def get_one_day_tasks(self, date_filter: date, state_filter: Optional[bool] = None) -> tuple[Task, ...]:
        tasks = [
            task
            for task in self.list_tasks()
            if task.due_at and task.due_at.date() == date_filter
        ]
        if state_filter is not None:
            tasks = [task for task in tasks if task.completed == state_filter]
        return tuple(tasks)

    def get_several_days_tasks(
        self,
        date_filter: list[date],
        state_filter: Optional[bool] = None,
    ) -> tuple[Task, ...]:
        start_date, end_date = date_filter
        tasks = [
            task
            for task in self.list_tasks()
            if task.due_at and start_date <= task.due_at.date() <= end_date
        ]
        if state_filter is not None:
            tasks = [task for task in tasks if task.completed == state_filter]
        return tuple(tasks)

    def get_radar_stats(self) -> list[float]:
        # Dimensions: Development(开发), Design(设计), Planning(规划), Communication(沟通), Execution(执行)
        tasks = self.list_tasks()
        
        dev_count = sum(1 for t in tasks if any(kw in t.title.lower() or kw in t.category.lower() or kw in t.tags.lower() for kw in ["开发", "代码", "前端", "后端", "测试", "dev", "code"]))
        design_count = sum(1 for t in tasks if any(kw in t.title.lower() or kw in t.category.lower() or kw in t.tags.lower() for kw in ["设计", "ui", "ux", "交互", "设计图"]))
        plan_count = sum(1 for t in tasks if any(kw in t.title.lower() or kw in t.category.lower() or kw in t.tags.lower() for kw in ["规划", "计划", "架构", "需求"]))
        comm_count = sum(1 for t in tasks if any(kw in t.title.lower() or kw in t.category.lower() or kw in t.tags.lower() for kw in ["沟通", "会议", "邮件", "讨论", "对齐"]))
        
        # Execution is based on completion rate
        total = len(tasks)
        completed = sum(1 for t in tasks if t.completed)
        exec_score = (completed / total) if total > 0 else 0.0
        
        def normalize(count: int, max_val: int = 10) -> float:
            return min(1.0, count / max_val)
            
        return [
            normalize(dev_count),
            normalize(design_count),
            normalize(plan_count),
            normalize(comm_count),
            exec_score
        ]

    def get_yearly_activity_matrix(self) -> list[list[int]]:
        # Returns a 52x7 matrix of activity levels (0-10)
        # Based on task completed_at and created_at dates
        tasks = self.list_tasks()
        
        activity_map = {}
        for t in tasks:
            if t.completed and t.completed_at:
                d = t.completed_at.date()
                activity_map[d] = activity_map.get(d, 0) + 2
            if t.created_at:
                d = t.created_at.date()
                activity_map[d] = activity_map.get(d, 0) + 1
                
        matrix = [[0 for _ in range(7)] for _ in range(52)]
        today = date.today()
        start_date = today - timedelta(days=364)
        
        # Align start_date to Monday
        while start_date.weekday() != 0:
            start_date -= timedelta(days=1)
            
        current_date = start_date
        for col in range(52):
            for row in range(7):
                matrix[col][row] = activity_map.get(current_date, 0)
                current_date += timedelta(days=1)
                
        return matrix

    def clear_all_data(self) -> None:
        with self._session_factory() as session:
            session.query(Task).delete()
            session.query(Note).delete()
            session.commit()

    def dashboard_snapshot(self) -> dict[str, Any]:
        tasks = self.list_tasks()
        notes = self.list_notes()
        today = date.today()

        total = len(tasks)
        completed = [task for task in tasks if task.completed]
        active = [task for task in tasks if not task.completed]
        overdue = [task for task in active if task.due_at and task.due_at.date() < today]
        due_today = [task for task in active if task.due_at and task.due_at.date() == today]
        focus_minutes = sum(task.tracked_minutes for task in tasks)
        estimated_minutes = sum(task.estimated_minutes for task in tasks)
        completion_rate = round((len(completed) / total) * 100) if total else 0
        focus_rate = round((focus_minutes / estimated_minutes) * 100) if estimated_minutes else 0

        category_counter = Counter(task.category or "未分类" for task in tasks)
        priority_counter = Counter(task.priority or "中" for task in tasks)
        note_counter = {
            "notes_total": len(notes),
            "notes_pinned": sum(1 for note in notes if note.pinned),
        }

        return {
            "total": total,
            "completed": len(completed),
            "active": len(active),
            "overdue": len(overdue),
            "due_today": len(due_today),
            "focus_minutes": focus_minutes,
            "estimated_minutes": estimated_minutes,
            "completion_rate": completion_rate,
            "focus_rate": focus_rate,
            "category_distribution": category_counter.most_common(6),
            "priority_distribution": dict(priority_counter),
            "notes": note_counter,
            "recent_due": sorted(
                [task for task in tasks if task.due_at],
                key=lambda item: item.due_at or datetime.max,
            )[:6],
        }

    def gantt_entries(self, window_days: int = 45) -> dict[str, Any]:
        all_tasks = self.list_tasks()
        task_map = {task.id: task for task in all_tasks}
        dated_task_ids = {task.id for task in all_tasks if task.due_at}
        if not dated_task_ids:
            today = date.today()
            return {
                "start_date": today,
                "days": window_days,
                "items": [],
            }

        # Include all ancestors for dated tasks so parent progress can be demonstrated.
        included_ids = set(dated_task_ids)
        for task_id in list(dated_task_ids):
            parent_id = task_map[task_id].parent_id
            seen: set[int] = set()
            while parent_id is not None and parent_id in task_map and parent_id not in seen:
                seen.add(parent_id)
                included_ids.add(parent_id)
                parent_id = task_map[parent_id].parent_id

        child_ids_by_parent: dict[int, list[int]] = defaultdict(list)
        for task_id in included_ids:
            parent_id = task_map[task_id].parent_id
            if parent_id is not None and parent_id in included_ids:
                child_ids_by_parent[parent_id].append(task_id)

        for children in child_ids_by_parent.values():
            children.sort(
                key=lambda child_id: (
                    task_map[child_id].sort_order,
                    task_map[child_id].created_at or datetime.min,
                    task_map[child_id].id,
                )
            )

        date_cache: dict[int, Optional[tuple[date, date]]] = {}

        def _resolve_date_range(task_id: int, trail: set[int]) -> Optional[tuple[date, date]]:
            if task_id in date_cache:
                return date_cache[task_id]
            if task_id in trail:
                date_cache[task_id] = None
                return None

            task = task_map[task_id]
            if task.due_at:
                end_date = task.due_at.date()
                duration_days = max(1, int(task.estimated_minutes or 0) // 120)
                if task.created_at:
                    start_date = min(end_date, task.created_at.date())
                else:
                    start_date = end_date - timedelta(days=duration_days - 1)
                if start_date > end_date:
                    start_date = end_date
                date_cache[task_id] = (start_date, end_date)
                return date_cache[task_id]

            child_ranges: list[tuple[date, date]] = []
            next_trail = set(trail)
            next_trail.add(task_id)
            for child_id in child_ids_by_parent.get(task_id, []):
                child_range = _resolve_date_range(child_id, next_trail)
                if child_range is not None:
                    child_ranges.append(child_range)

            if not child_ranges:
                date_cache[task_id] = None
                return None

            min_child_start = min(r[0] for r in child_ranges)
            max_child_end = max(r[1] for r in child_ranges)
            created_day = task.created_at.date() if task.created_at else min_child_start
            start_date = min(created_day, min_child_start)
            end_date = max(max_child_end, start_date)
            date_cache[task_id] = (start_date, end_date)
            return date_cache[task_id]

        for task_id in included_ids:
            _resolve_date_range(task_id, set())

        visible_ids = [task_id for task_id in included_ids if date_cache.get(task_id) is not None]
        if not visible_ids:
            today = date.today()
            return {
                "start_date": today,
                "days": window_days,
                "items": [],
            }

        visible_set = set(visible_ids)
        child_ids_by_parent = defaultdict(list)
        for task_id in visible_ids:
            parent_id = task_map[task_id].parent_id
            if parent_id is not None and parent_id in visible_set:
                child_ids_by_parent[parent_id].append(task_id)

        for children in child_ids_by_parent.values():
            children.sort(
                key=lambda child_id: (
                    task_map[child_id].sort_order,
                    task_map[child_id].created_at or datetime.min,
                    task_map[child_id].id,
                )
            )

        progress_cache: dict[int, int] = {}

        def _resolve_progress(task_id: int, trail: set[int]) -> int:
            if task_id in progress_cache:
                return progress_cache[task_id]
            if task_id in trail:
                task = task_map[task_id]
                fallback = 100 if task.completed else self._normalize_progress(task.progress)
                progress_cache[task_id] = fallback
                return fallback

            task = task_map[task_id]
            base_progress = 100 if task.completed else self._normalize_progress(task.progress)
            child_ids = child_ids_by_parent.get(task_id, [])
            if task.completed or not child_ids:
                progress_cache[task_id] = base_progress
                return base_progress

            next_trail = set(trail)
            next_trail.add(task_id)
            child_progress = [_resolve_progress(child_id, next_trail) for child_id in child_ids]
            rolled_progress = round(sum(child_progress) / len(child_progress)) if child_progress else 0
            effective_progress = max(base_progress, int(rolled_progress))
            progress_cache[task_id] = self._normalize_progress(effective_progress)
            return progress_cache[task_id]

        items_by_id: dict[int, dict[str, Any]] = {}
        all_dates: list[date] = []

        for task_id in visible_ids:
            task = task_map[task_id]
            resolved_range = date_cache.get(task_id)
            if resolved_range is None:
                continue
            start_date, end_date = resolved_range
            progress = _resolve_progress(task_id, set())
            all_dates.extend([start_date, end_date])
            parent_id = task.parent_id if task.parent_id in visible_set else None
            items_by_id[task_id] = {
                "id": task_id,
                "title": task.title or "未命名",
                "category": task.category or "未分类",
                "priority": task.priority or "中",
                "completed": task.completed,
                "start_date": start_date,
                "end_date": end_date,
                "progress": progress,
                "parent_id": parent_id,
                "depth": 0,
            }

        # Compute depth for each item (capped at 2)
        for item in items_by_id.values():
            depth, pid = 0, item["parent_id"]
            while pid is not None and pid in items_by_id:
                depth += 1
                pid = items_by_id[pid]["parent_id"]
            item["depth"] = min(depth, 2)

        # Build parent → children map, then flatten so children follow their parent
        def _sort_key(it: dict) -> tuple:
            return (it["start_date"], it["end_date"], it["title"])

        _children_map: dict[int, list[dict]] = {}
        _root_items: list[dict] = []
        for item in items_by_id.values():
            pid = item["parent_id"]
            if pid is not None and pid in items_by_id:
                _children_map.setdefault(pid, []).append(item)
            else:
                _root_items.append(item)

        _root_items.sort(key=_sort_key)
        for _children in _children_map.values():
            _children.sort(key=_sort_key)

        def _flatten(item_list: list[dict]) -> list[dict]:
            result: list[dict] = []
            for it in item_list:
                result.append(it)
                if it["id"] in _children_map:
                    result.extend(_flatten(_children_map[it["id"]]))
            return result

        items = _flatten(_root_items)
        min_date = min(all_dates)
        max_date = max(all_dates)

        today = date.today()
        start_date = min(min_date, today - timedelta(days=7))
        total_span_days = (max_date - min_date).days
        # If historical outliers make the span too wide, keep the viewport focused on recent schedules.
        if total_span_days > 180:
            start_date = max(min_date, today - timedelta(days=30))

        # Keep only rows that can still be observed in the current viewport.
        items = [item for item in items if item["end_date"] >= start_date]
        if items:
            max_visible_date = max(item["end_date"] for item in items)
            end_date = max(max_visible_date, start_date + timedelta(days=window_days - 1))
        else:
            end_date = start_date + timedelta(days=window_days - 1)

        days = (end_date - start_date).days + 1
        return {
            "start_date": start_date,
            "days": days,
            "items": items,
        }

    def personal_analytics_snapshot(self) -> dict[str, Any]:
        tasks = self.list_tasks()
        notes = self.list_notes()
        today = date.today()
        total = len(tasks)
        completed = [task for task in tasks if task.completed]
        active = [task for task in tasks if not task.completed]
        overdue = [task for task in active if task.due_at and task.due_at.date() < today]
        on_time_completed = [
            task for task in completed
            if task.due_at is None or (task.completed_at and task.completed_at.date() <= task.due_at.date())
        ]

        focus_minutes = sum(task.tracked_minutes for task in tasks)
        estimated_minutes = sum(max(task.estimated_minutes, 0) for task in tasks)
        category_counter = Counter(task.category or "未分类" for task in tasks)
        top_category_count = category_counter.most_common(1)[0][1] if category_counter else 0

        completion_rate = (len(completed) / total) if total else 0.0
        on_time_rate = (len(on_time_completed) / len(completed)) if completed else 0.0
        focus_rate = min(1.0, focus_minutes / estimated_minutes) if estimated_minutes else 0.0
        planning_rate = min(1.0, sum(1 for task in tasks if task.due_at) / total) if total else 0.0
        balance_rate = 1.0 - min(1.0, (top_category_count / total)) if total else 0.0
        note_capture_rate = min(1.0, len(notes) / max(1, total))
        health_rate = 1.0 - min(1.0, len(overdue) / max(1, len(active))) if active else 1.0

        radar = {
            "labels": ["执行完成", "按期交付", "专注投入", "计划严谨", "工作平衡", "知识沉淀", "任务健康"],
            "values": [
                round(completion_rate, 4),
                round(on_time_rate, 4),
                round(focus_rate, 4),
                round(planning_rate, 4),
                round(balance_rate, 4),
                round(note_capture_rate, 4),
                round(health_rate, 4),
            ],
        }

        activity_map = self._build_focus_activity_map(tasks, notes)

        matrix = [[0 for _ in range(7)] for _ in range(53)]
        start_date = today - timedelta(days=370)
        while start_date.weekday() != 0:
            start_date -= timedelta(days=1)
        current_date = start_date
        for col in range(53):
            for row in range(7):
                matrix[col][row] = min(10, activity_map.get(current_date, 0))
                current_date += timedelta(days=1)

        peak_day = max(activity_map, key=activity_map.get, default=today)
        active_days = sum(1 for value in activity_map.values() if value > 0)

        insight_lines = [
            f"完成率 {round(completion_rate * 100)}%",
            f"按期率 {round(on_time_rate * 100)}%",
            f"累计专注 {focus_minutes} 分钟",
            f"最高频分类 {category_counter.most_common(1)[0][0] if category_counter else '未分类'}",
            f"便签沉淀 {len(notes)} 条",
        ]

        return {
            "radar": radar,
            "heatmap": matrix,
            "insights": insight_lines,
            "category_distribution": category_counter.most_common(8),
            "heatmap_summary": {
                "active_days": active_days,
                "peak_day": peak_day.strftime("%Y-%m-%d"),
                "peak_value": activity_map.get(peak_day, 0),
                "date_range": f"{start_date:%Y-%m-%d} ~ {(current_date - timedelta(days=1)):%Y-%m-%d}",
            },
        }

    def create_task(self, payload: dict[str, Any]) -> Task:
        category = str(payload.get("category", "学习") or "学习").strip() or "学习"
        progress = self._normalize_progress(payload.get("progress", 0))
        if bool(payload.get("completed", False)):
            progress = 100
        with self._session_factory() as session:
            task = Task(
                title=payload["title"],
                description=payload.get("description", ""),
                category=category,
                tags=payload.get("tags", ""),
                priority=payload.get("priority", "中"),
                due_at=payload.get("due_at"),
                remind_at=payload.get("remind_at"),
                progress=progress,
                estimated_minutes=payload.get("estimated_minutes", 0),
                tracked_minutes=payload.get("tracked_minutes", 0),
                recurrence_rule=payload.get("recurrence_rule", "不重复"),
                parent_id=payload.get("parent_id"),
                sort_order=self._next_sort_order(session, payload.get("parent_id")),
            )
            session.add(task)
            session.flush()
            self._refresh_parent_chain(session, task.parent_id)
            session.commit()
            if category not in {"默认", "无分类", "未分类"}:
                self.add_category(category)
            return task

    def update_task(self, task_id: int, payload: dict[str, Any]) -> Optional[Task]:
        with self._session_factory() as session:
            task = session.get(Task, task_id)
            if task is None:
                return None
            recurrence_payload = None
                
            # If payload only contains a few fields (like {"completed": True}), we shouldn't overwrite everything else.
            # update_task is usually called with a full payload from TaskEditorView.
            # Let's make it robust so it only updates fields that are actually in the payload.
            
            if "parent_id" in payload:
                previous_parent_id = task.parent_id
                new_parent_id = payload["parent_id"]
                if previous_parent_id != new_parent_id:
                    task.sort_order = self._next_sort_order(session, new_parent_id)
                task.parent_id = new_parent_id
                if previous_parent_id and previous_parent_id != new_parent_id:
                    self._refresh_parent_chain(session, previous_parent_id)
                self._refresh_parent_chain(session, new_parent_id)
                
            if "remind_at" in payload:
                previous_remind_at = task.remind_at
                task.remind_at = payload["remind_at"]
                if previous_remind_at != task.remind_at:
                    task.reminder_sent = False
                    
            if "title" in payload:
                task.title = payload["title"]
            if "description" in payload:
                task.description = payload["description"]
            if "category" in payload:
                task.category = payload["category"]
            if "tags" in payload:
                task.tags = payload["tags"]
            if "priority" in payload:
                task.priority = payload["priority"]
            if "due_at" in payload:
                task.due_at = payload["due_at"]
            if "progress" in payload:
                task.progress = self._normalize_progress(payload["progress"])
            if "estimated_minutes" in payload:
                task.estimated_minutes = payload["estimated_minutes"]
            if "tracked_minutes" in payload:
                task.tracked_minutes = payload["tracked_minutes"]
            if "recurrence_rule" in payload:
                task.recurrence_rule = payload["recurrence_rule"]
            if "completed" in payload:
                target_completed = bool(payload["completed"])
                if task.completed != target_completed:
                    task_map = self._task_map(session)
                    self._set_completion_state(session, task_map, task_id, target_completed, cascade=True)
                    self._refresh_parent_chain(session, task.parent_id, task_map=task_map)
                    recurrence_payload = self._build_next_recurrence_payload(task) if target_completed else None
                
            task.updated_at = datetime.now()
            session.commit()
            if recurrence_payload is not None:
                self.create_task(recurrence_payload)
            category = (task.category or "").strip()
            if category and category not in {"默认", "无分类", "未分类"}:
                self.add_category(category)
            return task

    def save_task(self, task: Task) -> Task:
        with self._session_factory() as session:
            merged = session.merge(task)
            merged.updated_at = datetime.now()
            session.flush()
            self._refresh_parent_chain(session, merged.parent_id)
            session.commit()
            return merged

    def delete_task(self, task: Task | int) -> None:
        task_id = task if isinstance(task, int) else task.id
        with self._session_factory() as session:
            existing = session.get(Task, task_id)
            if existing is None:
                return
            parent_id = existing.parent_id
            session.delete(existing)
            session.flush()
            self._refresh_parent_chain(session, parent_id)
            session.commit()

    def update_task_fields(self, task_id: int, payload: dict[str, Any]) -> Optional[Task]:
        with self._session_factory() as session:
            task = session.get(Task, task_id)
            if task is None:
                return None
            for field, value in payload.items():
                if hasattr(task, field):
                    setattr(task, field, value)
            task.updated_at = datetime.now()
            session.commit()
            return task

    def capture_task_subtree(self, task_id: int) -> Optional[dict[str, Any]]:
        tasks = self.list_tasks()
        task_map = {task.id: task for task in tasks}
        root = task_map.get(task_id)
        if root is None:
            return None
        children_map: dict[Optional[int], list[Task]] = {}
        for task in tasks:
            children_map.setdefault(task.parent_id, []).append(task)
        for children in children_map.values():
            children.sort(key=lambda item: (item.sort_order, item.created_at, item.id))
        ordered: list[Task] = []
        queue = [root]
        while queue:
            current = queue.pop(0)
            ordered.append(current)
            queue[0:0] = children_map.get(current.id, [])
        return {
            "root_id": root.id,
            "tasks": [self._task_to_dict(task) for task in ordered],
        }

    def restore_task_subtree(self, snapshot: dict[str, Any]) -> Optional[int]:
        tasks_data = snapshot.get("tasks", [])
        if not tasks_data:
            return None
        self._validate_tasks_payload(tasks_data)
        old_ids = {int(task_data["id"]) for task_data in tasks_data}
        with self._session_factory() as session:
            old_to_new: dict[int, int] = {}
            for task_data in tasks_data:
                external_parent_id = task_data.get("parent_id")
                parent_id = old_to_new.get(external_parent_id)
                if external_parent_id is not None and external_parent_id not in old_ids:
                    parent_id = external_parent_id if session.get(Task, external_parent_id) is not None else None
                task = Task(
                    title=str(task_data["title"]),
                    description=str(task_data.get("description", "")),
                    category=str(task_data.get("category", "学习")),
                    tags=str(task_data.get("tags", "")),
                    priority=str(task_data.get("priority", "中")),
                    due_at=self._parse_datetime(task_data.get("due_at")),
                    remind_at=self._parse_datetime(task_data.get("remind_at")),
                    progress=self._normalize_progress(task_data.get("progress", 0)),
                    estimated_minutes=int(task_data.get("estimated_minutes", 0)),
                    tracked_minutes=int(task_data.get("tracked_minutes", 0)),
                    recurrence_rule=str(task_data.get("recurrence_rule", "不重复")),
                    completed=bool(task_data.get("completed", False)),
                    completed_at=self._parse_datetime(task_data.get("completed_at")),
                    reminder_sent=bool(task_data.get("reminder_sent", False)),
                    sort_order=int(task_data.get("sort_order", 0)),
                    parent_id=parent_id,
                    created_at=self._parse_datetime(task_data.get("created_at")) or datetime.now(),
                    updated_at=self._parse_datetime(task_data.get("updated_at")) or datetime.now(),
                )
                session.add(task)
                session.flush()
                old_to_new[int(task_data["id"])] = task.id
            session.commit()
            root_old_id = int(snapshot.get("root_id", tasks_data[0]["id"]))
            return old_to_new.get(root_old_id)

    def toggle_task(self, task_id: int) -> Optional[Task]:
        with self._session_factory() as session:
            task = session.get(Task, task_id)
            if task is None:
                return None
            target_state = not task.completed
            task_map = self._task_map(session)
            self._set_completion_state(session, task_map, task_id, target_state, cascade=True)
            self._refresh_parent_chain(session, task.parent_id, task_map=task_map)
            recurrence_payload = self._build_next_recurrence_payload(task) if target_state else None
            session.commit()
            if recurrence_payload is not None:
                self.create_task(recurrence_payload)
            return task

    def batch_toggle_tasks(self, task_ids: Iterable[int]) -> None:
        ids = list(dict.fromkeys(task_ids))
        for task_id in ids:
            self.toggle_task(task_id)

    def search_tasks(self, keyword: str) -> list[Task]:
        lowered = keyword.strip().lower()
        if not lowered:
            return self.list_tasks()
        matched: list[Task] = []
        for task in self.list_tasks():
            haystack = "\n".join(filter(None, [task.title, task.description, task.category, task.tags])).lower()
            if lowered in haystack:
                matched.append(task)
        return matched

    def list_categories(self) -> list[str]:
        values = {task.category.strip() for task in self.list_tasks() if (task.category or "").strip()}
        values.update(self._load_category_registry())
        return sorted(values)

    def add_category(self, name: str) -> None:
        normalized = name.strip()
        if not normalized:
            return
        categories = self._load_category_registry()
        categories.add(normalized)
        self._save_category_registry(categories)

    def rename_category(self, old_name: str, new_name: str) -> None:
        normalized = new_name.strip()
        if not normalized:
            return
        with self._session_factory() as session:
            statement = select(Task).where(Task.category == old_name)
            for task in session.scalars(statement).all():
                task.category = normalized
                task.updated_at = datetime.now()
            session.commit()
        categories = self._load_category_registry()
        if old_name in categories:
            categories.remove(old_name)
        categories.add(normalized)
        self._save_category_registry(categories)

    def delete_category(self, category_name: str, replacement: str = "未分类") -> None:
        with self._session_factory() as session:
            statement = select(Task).where(Task.category == category_name)
            for task in session.scalars(statement).all():
                task.category = replacement
                task.updated_at = datetime.now()
            session.commit()
        categories = self._load_category_registry()
        if category_name in categories:
            categories.remove(category_name)
            self._save_category_registry(categories)

    def list_tags(self) -> list[str]:
        tags: set[str] = set()
        for task in self.list_tasks():
            tags.update(self.parse_tags(task.tags))
        return sorted(tags)

    def agenda_for_day(self, target_day: date) -> list[Task]:
        tasks = [
            task
            for task in self.list_tasks()
            if task.due_at and task.due_at.date() == target_day
        ]
        return sorted(
            tasks,
            key=lambda item: (
                item.completed,
                item.due_at or datetime.max,
                item.priority,
                item.title.lower(),
            ),
        )

    def upcoming_reminders(self, limit: int = 8) -> list[Task]:
        tasks = [
            task
            for task in self.list_tasks()
            if not task.completed and task.remind_at is not None
        ]
        tasks.sort(key=lambda item: (item.remind_at or datetime.max, item.priority, item.title.lower()))
        return tasks[:limit]

    def list_notes(self) -> list[Note]:
        with self._session_factory() as session:
            statement = select(Note).order_by(Note.pinned.desc(), Note.updated_at.desc(), Note.id.desc())
            return list(session.scalars(statement).all())

    def get_notes(self) -> list[Note]:
        return self.list_notes()

    def create_note(self, title: str, content: str = "", pinned: bool = False) -> Note:
        with self._session_factory() as session:
            note = Note(title=title or "未命名便签", content=content, pinned=pinned)
            session.add(note)
            session.commit()
            return note

    def save_note(self, note: Note) -> Note:
        with self._session_factory() as session:
            merged = session.merge(note)
            merged.updated_at = datetime.now()
            session.commit()
            return merged

    def delete_note(self, note: Note | int) -> None:
        note_id = note if isinstance(note, int) else note.id
        with self._session_factory() as session:
            existing = session.get(Note, note_id)
            if existing is None:
                return
            session.delete(existing)
            session.commit()

    def postpone_reminder(self, task_id: int, minutes: int = 10) -> Optional[Task]:
        with self._session_factory() as session:
            task = session.get(Task, task_id)
            if task is None:
                return None
            base_time = task.remind_at or datetime.now()
            task.remind_at = base_time + timedelta(minutes=minutes)
            task.reminder_sent = False
            task.updated_at = datetime.now()
            session.commit()
            return task

    def dashboard_counts(self) -> dict[str, int]:
        tasks = self.list_tasks()
        today = date.today()
        total = len(tasks)
        completed = sum(1 for task in tasks if task.completed)
        pending = total - completed
        overdue = sum(1 for task in tasks if not task.completed and task.due_at and task.due_at.date() < today)
        today_due = sum(1 for task in tasks if not task.completed and task.due_at and task.due_at.date() == today)
        reminders = sum(1 for task in tasks if not task.completed and task.remind_at)
        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "overdue": overdue,
            "today_due": today_due,
            "reminders": reminders,
        }

    def _kanban_stage(self, task: Task, today: date) -> str:
        if task.completed:
            return "done"
        if task.tracked_minutes >= max(25, task.estimated_minutes // 4) or (task.tracked_minutes > 0 and task.priority == "高"):
            return "in_progress"
        if (task.due_at and task.due_at.date() <= today + timedelta(days=1)) or task.priority == "高" or task.remind_at:
            return "review"
        return "todo"

    def _build_focus_activity_map(self, tasks: list[Task], notes: list[Note]) -> dict[date, int]:
        today = date.today()
        activity_map: dict[date, int] = defaultdict(int)
        for task in tasks:
            created_day = task.created_at.date() if task.created_at else None
            due_day = task.due_at.date() if task.due_at else None
            done_day = task.completed_at.date() if task.completed_at else None
            updated_day = task.updated_at.date() if task.updated_at else None
            if created_day:
                activity_map[created_day] += 1
            if due_day:
                activity_map[due_day] += 1
            if done_day:
                activity_map[done_day] += 2
            if updated_day and updated_day not in {created_day, done_day}:
                activity_map[updated_day] += 1
            if task.tracked_minutes:
                anchor_day = done_day or updated_day or due_day or created_day or today
                activity_map[anchor_day] += max(1, task.tracked_minutes // 25)
        for note in notes:
            note_day = note.updated_at.date() if note.updated_at else note.created_at.date()
            activity_map[note_day] += 1
        return activity_map

    def weekly_series(self, days: int = 7) -> list[dict[str, Any]]:
        today = date.today()
        result: list[dict[str, Any]] = []
        tasks = self.list_tasks()
        notes = self.list_notes()
        activity_map = self._build_focus_activity_map(tasks, notes)
        for offset in range(days - 1, -1, -1):
            target = today - timedelta(days=offset)
            completed_count = sum(
                1 for task in tasks if task.completed_at and task.completed_at.date() == target
            )
            due_count = sum(
                1 for task in tasks if task.due_at and task.due_at.date() == target
            )
            result.append(
                {
                    "label": target.strftime("%m-%d"),
                    "completed": completed_count,
                    "due": due_count,
                    "focus": activity_map.get(target, 0) * 25,
                }
            )
        return result

    def week_tasks(self, start_day: date) -> dict[date, list[Task]]:
        tasks = self.list_tasks()
        result: dict[date, list[Task]] = {}
        for day_offset in range(7):
            current = start_day + timedelta(days=day_offset)
            result[current] = sorted(
                [
                    task
                    for task in tasks
                    if task.due_at and task.due_at.date() == current
                ],
                key=lambda item: (item.completed, item.due_at or datetime.max, item.priority, item.title.lower()),
            )
        return result

    def kanban_snapshot(self) -> dict[str, Any]:
        tasks = self.list_tasks()
        notes = self.list_notes()
        today = date.today()
        stage_map = {"todo": [], "in_progress": [], "review": [], "done": []}
        for task in tasks:
            stage_map[self._kanban_stage(task, today)].append(task)
        for bucket in stage_map.values():
            bucket.sort(
                key=lambda item: (
                    item.completed,
                    item.due_at or datetime.max,
                    {"高": 0, "中": 1, "低": 2}.get(item.priority, 3),
                    item.title.lower(),
                )
            )

        active = [task for task in tasks if not task.completed]
        category_distribution = Counter(task.category or "未分类" for task in tasks).most_common(6)
        throughput = sum(1 for task in tasks if task.completed_at and (today - task.completed_at.date()).days <= 7)
        focus_minutes = sum(task.tracked_minutes for task in tasks)
        overdue = sum(1 for task in active if task.due_at and task.due_at.date() < today)
        due_today = sum(1 for task in active if task.due_at and task.due_at.date() == today)
        return {
            "hero_hint": f"活跃任务 {len(active)} 项｜本周完成 {throughput} 项｜便签 {len(notes)} 条｜今日到期 {due_today} 项",
            "summary": {
                "active": len(active),
                "in_progress": len(stage_map["in_progress"]),
                "completed": len(stage_map["done"]),
                "focus_minutes": focus_minutes,
                "overdue": overdue,
                "due_today": due_today,
                "throughput": throughput,
            },
            "categories": category_distribution,
            "columns": stage_map,
            "insights": [
                f"推进中 {len(stage_map['in_progress'])} 项，适合继续保持连贯执行",
                f"复核区 {len(stage_map['review'])} 项，其中到期压力 {due_today + overdue} 项",
                f"知识沉淀 {len(notes)} 条，可用于补强任务说明与复盘",
            ],
        }

    def dashboard_story_snapshot(self) -> dict[str, Any]:
        tasks = self.list_tasks()
        notes = self.list_notes()
        snapshot = self.dashboard_snapshot()
        series = self.weekly_series(14)
        today = date.today()
        active = [task for task in tasks if not task.completed]
        completed = [task for task in tasks if task.completed]
        category_distribution = Counter(task.category or "未分类" for task in tasks).most_common(6)
        top_focus_tasks = sorted(tasks, key=lambda item: (-item.tracked_minutes, item.title.lower()))[:6]
        recent_completed = sorted(
            [task for task in completed if task.completed_at],
            key=lambda item: item.completed_at or datetime.min,
            reverse=True,
        )[:5]
        upcoming = sorted(
            [task for task in active if task.due_at and task.due_at.date() <= today],
            key=lambda item: item.due_at or datetime.max,
        )[:5]
        on_time_count = sum(
            1
            for task in completed
            if task.due_at is None or (task.completed_at and task.completed_at.date() <= task.due_at.date())
        )
        on_time_rate = round((on_time_count / len(completed)) * 100) if completed else 100
        active_days = [item for item in series if int(item.get("completed", 0)) or int(item.get("due", 0)) or int(item.get("focus", 0))]
        streak = 0
        for item in reversed(series):
            if int(item.get("completed", 0)) or int(item.get("focus", 0)):
                streak += 1
            else:
                break
        return {
            "snapshot": snapshot,
            "trend": series,
            "hero_hint": f"连续活跃 {streak} 天｜按期率 {on_time_rate}%｜活跃天数 {len(active_days)} 天",
            "execution_lines": [
                f"最近两周完成 {sum(int(item['completed']) for item in series)} 项任务",
                f"当前活跃 {snapshot['active']} 项，其中逾期 {snapshot['overdue']} 项",
                f"今日到期 {snapshot['due_today']} 项，适合优先清理短周期事项",
                f"累计专注 {snapshot['focus_minutes']} 分钟，专注转化率 {snapshot['focus_rate']}%",
            ],
            "structure_lines": [
                f"最高频分类 {category_distribution[0][0] if category_distribution else '未分类'}",
                f"高优先级 {snapshot['priority_distribution'].get('高', 0)} 项",
                f"便签沉淀 {len(notes)} 条，置顶 {snapshot['notes']['notes_pinned']} 条",
                f"在途任务 {len(active)} 项，已完成 {snapshot['completed']} 项",
            ],
            "focus_lines": [
                f"{task.title}｜累计 {task.tracked_minutes} 分钟｜{task.category}"
                for task in top_focus_tasks
                if task.tracked_minutes > 0
            ]
            or ["暂无专注记录"],
            "upcoming_lines": [
                f"{task.title}｜{task.due_at:%m-%d %H:%M}"
                for task in upcoming
                if task.due_at
            ]
            or ["暂无近期到期任务"],
            "recent_lines": [
                f"{task.title}｜{task.completed_at:%m-%d %H:%M}"
                for task in recent_completed
                if task.completed_at
            ]
            or ["暂无最近完成记录"],
            "categories": category_distribution,
            "on_time_rate": on_time_rate,
            "active_ratio": round((snapshot["active"] / max(1, snapshot["total"])) * 100) if snapshot["total"] else 0,
            "focus_density": round(snapshot["focus_minutes"] / max(1, snapshot["active"])) if snapshot["active"] else 0,
        }

    def weekly_operational_snapshot(self, start_day: date) -> dict[str, Any]:
        tasks = self.list_tasks()
        end_day = start_day + timedelta(days=6)
        week_map = self.week_tasks(start_day)
        all_week_tasks = [
            task for task in tasks if task.due_at and start_day <= task.due_at.date() <= end_day
        ]
        scheduled = len(all_week_tasks)
        completed = sum(1 for task in all_week_tasks if task.completed)
        focus_minutes = sum(task.tracked_minutes for task in all_week_tasks)
        overdue = sum(1 for task in tasks if not task.completed and task.due_at and task.due_at.date() < date.today())
        high_priority = sum(1 for task in all_week_tasks if task.priority == "高")
        categories = Counter(task.category or "未分类" for task in all_week_tasks).most_common(6)
        trend = []
        days_payload = []
        best_day = None
        best_score = -1
        for current_day, day_tasks in week_map.items():
            day_focus = sum(task.tracked_minutes for task in day_tasks)
            day_completed = sum(1 for task in day_tasks if task.completed)
            score = day_completed * 3 + day_focus
            if score > best_score:
                best_day = current_day
                best_score = score
            day_payload = {
                "date": current_day,
                "label": "今天" if current_day == date.today() else f"{['周一','周二','周三','周四','周五','周六','周日'][current_day.weekday()]}",
                "date_text": current_day.strftime("%Y-%m-%d"),
                "tasks": day_tasks,
                "focus_minutes": day_focus,
                "completed_count": day_completed,
                "completion_rate": round((day_completed / len(day_tasks)) * 100) if day_tasks else 0,
            }
            days_payload.append(day_payload)
            trend.append(
                {
                    "label": current_day.strftime("%m-%d"),
                    "scheduled": len(day_tasks),
                    "completed": day_completed,
                    "focus": day_focus,
                }
            )
        return {
            "hero_hint": f"本周窗口 {start_day:%m-%d} 至 {end_day:%m-%d}｜逾期池 {overdue} 项",
            "summary": {
                "scheduled": scheduled,
                "completed": completed,
                "high_priority": high_priority,
                "focus_minutes": focus_minutes,
                "completion_rate": round((completed / scheduled) * 100) if scheduled else 0,
                "range_text": f"{start_day:%m-%d} ~ {end_day:%m-%d}",
                "best_day_text": f"最佳推进日 {best_day:%m-%d}" if best_day else "暂无明显高峰日",
                "overdue": overdue,
            },
            "trend": trend,
            "days": days_payload,
            "categories": categories,
            "insights": [
                f"本周共安排 {scheduled} 项任务，完成 {completed} 项",
                f"高优先级事项 {high_priority} 项，建议在前半周优先清理",
                f"周内累计专注 {focus_minutes} 分钟，说明执行投入已经形成沉淀",
            ],
            "insight_subtitle": "真实周历节奏",
            "category_subtitle": "本周涉及项目",
        }

    def stats_overview_snapshot(self, days: int = 14) -> dict[str, Any]:
        tasks = self.list_tasks()
        snapshot = self.dashboard_snapshot()
        trend = self.weekly_series(days)
        categories = Counter(task.category or "未分类" for task in tasks).most_common(6)
        active = [task for task in tasks if not task.completed]
        completed_total = sum(int(item["completed"]) for item in trend)
        due_total = sum(int(item["due"]) for item in trend)
        focus_total = sum(int(item.get("focus", 0)) for item in trend)
        completion_rate = round((completed_total / max(1, due_total)) * 100) if due_total else 0
        focus_tasks = sorted(tasks, key=lambda item: (-item.tracked_minutes, item.title.lower()))[:5]
        return {
            "hero_hint": f"近 {days} 天完成 {completed_total} 项｜到期 {due_total} 项｜活跃任务 {len(active)} 项",
            "summary": {
                "completed_total": completed_total,
                "completed_meta": f"平均每天完成 {round(completed_total / max(1, days), 1)} 项",
                "due_total": due_total,
                "due_meta": f"待到期压力 {snapshot['due_today']} 项今天触发",
                "focus_total": focus_total,
                "focus_meta": f"任务总专注 {snapshot['focus_minutes']} 分钟",
                "completion_rate": completion_rate,
                "rate_meta": f"当前总完成率 {snapshot['completion_rate']}%",
            },
            "trend": trend,
            "execution_lines": [
                f"逾期 {snapshot['overdue']} 项，说明最近窗口仍有拖延需要化解",
                f"活跃任务 {snapshot['active']} 项，可结合周视图做再分配",
                f"完成率 {completion_rate}% 基于近 {days} 天真实完成/到期比值",
                f"提醒任务 {self.dashboard_counts()['reminders']} 项，存在提醒负载",
            ],
            "structure_lines": [
                f"最高频分类 {categories[0][0] if categories else '未分类'}",
                f"高优先级 {snapshot['priority_distribution'].get('高', 0)} 项",
                f"中优先级 {snapshot['priority_distribution'].get('中', 0)} 项",
                f"低优先级 {snapshot['priority_distribution'].get('低', 0)} 项",
            ],
            "execution_subtitle": "任务负荷",
            "structure_subtitle": "结构画像",
            "focus_lines": [
                f"{task.title}｜{task.tracked_minutes} 分钟｜{task.category}"
                for task in focus_tasks
                if task.tracked_minutes > 0
            ]
            or ["暂无专注排行榜数据"],
            "focus_subtitle": "最高投入任务",
            "categories": categories,
            "distribution_hint": "横向条带使用当前分类任务量比例绘制，避免只显示冷冰冰的数字。",
        }

    def management_center_snapshot(self, auto_sync_enabled: bool) -> dict[str, Any]:
        tasks = self.list_tasks()
        notes = self.list_notes()
        snapshot = self.dashboard_snapshot()
        completed = [task for task in tasks if task.completed]
        on_time_completed = [
            task for task in completed
            if task.due_at is None or (task.completed_at and task.completed_at.date() <= task.due_at.date())
        ]
        on_time_rate = round((len(on_time_completed) / len(completed)) * 100) if completed else 100
        categories = Counter(task.category or "未分类" for task in tasks).most_common(6)
        backlog_tasks = sorted(
            [task for task in tasks if not task.completed],
            key=lambda item: (
                item.due_at or datetime.max,
                {"高": 0, "中": 1, "低": 2}.get(item.priority, 3),
                item.title.lower(),
            ),
        )[:6]
        health_score = round(
            snapshot["completion_rate"] * 0.35
            + on_time_rate * 0.35
            + min(100, snapshot["focus_rate"]) * 0.15
            + max(0, 100 - snapshot["overdue"] * 10) * 0.15
        )
        sync_state = "已开启" if auto_sync_enabled else "已关闭"
        sync_meta = "切换任务后自动导出快照" if auto_sync_enabled else "目前仅支持手动导出"
        return {
            "health_score": health_score,
            "health_caption": f"逾期 {snapshot['overdue']} 项｜活跃 {snapshot['active']} 项",
            "health_accent": "#34d399" if health_score >= 75 else "#f59e0b",
            "hero_hint": f"总任务 {snapshot['total']} 项｜已完成 {snapshot['completed']} 项｜同步 {sync_state}",
            "completion_rate": snapshot["completion_rate"],
            "completion_meta": f"累计完成 {snapshot['completed']} 项任务",
            "on_time_rate": on_time_rate,
            "on_time_meta": f"按期完成 {len(on_time_completed)} 项",
            "notes_total": snapshot["notes"]["notes_total"],
            "notes_meta": f"置顶 {snapshot['notes']['notes_pinned']} 条｜适合沉淀 SOP 与复盘",
            "sync_state": sync_state,
            "sync_meta": sync_meta,
            "insights": [
                f"最高频分类 {categories[0][0] if categories else '未分类'}，说明当前资源主要投入在该项目",
                f"提醒与逾期合计 {self.dashboard_counts()['reminders'] + snapshot['overdue']} 项，需要压缩噪音",
                f"任务总专注 {snapshot['focus_minutes']} 分钟，估算总量 {snapshot['estimated_minutes']} 分钟",
            ],
            "insight_subtitle": "工作流状态",
            "categories": categories,
            "knowledge_lines": [
                f"便签总量 {len(notes)} 条",
                f"最近到期 {snapshot['due_today']} 项",
            ],
            "structure_subtitle": "分类分布与知识资产",
            "backlog_lines": [
                f"{task.title}｜{task.category}｜{task.priority}｜{task.due_at:%m-%d %H:%M}" if task.due_at
                else f"{task.title}｜{task.category}｜{task.priority}｜未设日期"
                for task in backlog_tasks
            ]
            or ["暂无待处理事项"],
            "backlog_subtitle": "当前应优先清理的任务",
        }

    def due_reminders(self, current_time: datetime) -> list[Task]:
        with self._session_factory() as session:
            statement = (
                select(Task)
                .where(Task.completed.is_(False))
                .where(Task.reminder_sent.is_(False))
                .where(Task.remind_at.is_not(None))
                .where(Task.remind_at <= current_time)
                .order_by(Task.remind_at, Task.priority)
            )
            return list(session.scalars(statement).all())

    def next_pending_reminder_at(self) -> Optional[datetime]:
        with self._session_factory() as session:
            statement = (
                select(Task.remind_at)
                .where(Task.completed.is_(False))
                .where(Task.reminder_sent.is_(False))
                .where(Task.remind_at.is_not(None))
                .order_by(Task.remind_at)
                .limit(1)
            )
            return session.scalar(statement)

    def mark_reminders_sent(self, task_ids: Iterable[int]) -> None:
        ids = list(task_ids)
        if not ids:
            return
        with self._session_factory() as session:
            statement = select(Task).where(Task.id.in_(ids))
            for task in session.scalars(statement).all():
                task.reminder_sent = True
                task.updated_at = datetime.now()
            session.commit()

    def export_data(self, output_path: str | Path) -> None:
        payload = {
            "exported_at": datetime.now().isoformat(),
            "tasks": [self._task_to_dict(task) for task in self.list_tasks()],
            "notes": [self._note_to_dict(note) for note in self.list_notes()],
        }
        Path(output_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def export_csv(self, output_path: str | Path) -> None:
        fieldnames = [
            "id",
            "title",
            "category",
            "tags",
            "priority",
            "status",
            "due_at",
            "remind_at",
            "progress",
            "estimated_minutes",
            "parent_id",
            "created_at",
            "updated_at",
            "description",
        ]
        with Path(output_path).open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for task in self.list_tasks():
                writer.writerow(
                    {
                        "id": task.id,
                        "title": task.title,
                        "category": task.category,
                        "tags": task.tags,
                        "priority": task.priority,
                        "status": "已完成" if task.completed else "进行中",
                        "due_at": task.due_at.isoformat() if task.due_at else "",
                        "remind_at": task.remind_at.isoformat() if task.remind_at else "",
                        "progress": 100 if task.completed else self._normalize_progress(task.progress),
                        "estimated_minutes": task.estimated_minutes,
                        "parent_id": task.parent_id or "",
                        "created_at": task.created_at.isoformat() if task.created_at else "",
                        "updated_at": task.updated_at.isoformat() if task.updated_at else "",
                        "description": task.description,
                    }
                )

    def export_week_report(self, output_path: str | Path, start_day: Optional[date] = None) -> None:
        week_start = start_day or (date.today() - timedelta(days=date.today().weekday()))
        payload = self.week_tasks(week_start)
        lines = [f"# Task Forge 周报\n", f"统计周期：{week_start:%Y-%m-%d} 至 {(week_start + timedelta(days=6)):%Y-%m-%d}\n"]
        for current_day, tasks in payload.items():
            lines.append(f"## {current_day:%Y-%m-%d}\n")
            if not tasks:
                lines.append("- 当天没有任务安排\n")
                continue
            for task in tasks:
                status = "已完成" if task.completed else "进行中"
                lines.append(
                    f"- {task.title}｜{status}｜{task.priority}｜分类：{task.category}｜截止：{task.due_at:%H:%M}\n"
                )
        Path(output_path).write_text("".join(lines), encoding="utf-8")

    def apply_tree_order(self, ordered_nodes: list[dict[str, Optional[int]]]) -> None:
        with self._session_factory() as session:
            for node in ordered_nodes:
                raw_id = node.get("id")
                if raw_id is None:
                    continue
                task = session.get(Task, int(raw_id))
                if task is None:
                    continue
                task.parent_id = node["parent_id"]
                task.sort_order = int(node["sort_order"])
                task.updated_at = datetime.now()
            session.commit()

    def record_focus_minutes(self, task_id: int, minutes: int) -> None:
        if minutes <= 0:
            return
        with self._session_factory() as session:
            task = session.get(Task, task_id)
            if task is None:
                return
            task.tracked_minutes += minutes
            task.updated_at = datetime.now()
            session.commit()

    def import_data(self, input_path: str | Path) -> None:
        try:
            payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"导入失败，JSON 格式错误：{exc.msg}") from exc
        self._validate_import_payload(payload)
        with self._session_factory() as session:
            session.query(Task).delete()
            session.query(Note).delete()
            session.flush()
            old_to_new: dict[int, int] = {}
            for task_data in payload.get("tasks", []):
                task = Task(
                    title=task_data["title"],
                    description=task_data.get("description", ""),
                    category=task_data.get("category", "学习"),
                    tags=task_data.get("tags", ""),
                    priority=task_data.get("priority", "中"),
                    due_at=self._parse_datetime(task_data.get("due_at")),
                    remind_at=self._parse_datetime(task_data.get("remind_at")),
                    progress=self._normalize_progress(task_data.get("progress", 0)),
                    estimated_minutes=int(task_data.get("estimated_minutes", 0)),
                    tracked_minutes=int(task_data.get("tracked_minutes", 0)),
                    recurrence_rule=str(task_data.get("recurrence_rule", "不重复")),
                    completed=bool(task_data.get("completed", False)),
                    completed_at=self._parse_datetime(task_data.get("completed_at")),
                    reminder_sent=bool(task_data.get("reminder_sent", False)),
                    sort_order=int(task_data.get("sort_order", 0)),
                    created_at=self._parse_datetime(task_data.get("created_at")) or datetime.now(),
                    updated_at=self._parse_datetime(task_data.get("updated_at")) or datetime.now(),
                )
                session.add(task)
                session.flush()
                old_to_new[int(task_data["id"])] = task.id
            session.flush()
            imported_tasks = list(session.scalars(select(Task).order_by(Task.id)).all())
            for source_task, task_data in zip(imported_tasks, payload.get("tasks", [])):
                parent_id = task_data.get("parent_id")
                source_task.parent_id = old_to_new.get(parent_id) if parent_id is not None else None
            for note_data in payload.get("notes", []):
                session.add(
                    Note(
                        title=note_data.get("title", "未命名便签"),
                        content=note_data.get("content", ""),
                        pinned=bool(note_data.get("pinned", False)),
                        created_at=self._parse_datetime(note_data.get("created_at")) or datetime.now(),
                        updated_at=self._parse_datetime(note_data.get("updated_at")) or datetime.now(),
                    )
                )
            session.commit()

    def close(self) -> None:
        self._engine.dispose()

    def _next_sort_order(self, session: Session, parent_id: Optional[int]) -> int:
        statement = select(func.max(Task.sort_order)).where(Task.parent_id == parent_id)
        current = session.scalar(statement)
        return int(current or 0) + 1

    def _task_map(self, session: Session) -> dict[int, Task]:
        statement = select(Task)
        return {task.id: task for task in session.scalars(statement).all()}

    def _children_map(self, task_map: dict[int, Task]) -> dict[Optional[int], list[Task]]:
        children_map: dict[Optional[int], list[Task]] = {}
        for task in task_map.values():
            children_map.setdefault(task.parent_id, []).append(task)
        for children in children_map.values():
            children.sort(key=lambda item: (item.sort_order, item.created_at, item.id))
        return children_map

    def _set_completion_state(
        self,
        session: Session,
        task_map: dict[int, Task],
        task_id: int,
        completed: bool,
        *,
        cascade: bool,
    ) -> None:
        target = task_map.get(task_id)
        if target is None:
            return
        target.completed = completed
        target.completed_at = datetime.now() if completed else None
        if completed:
            target.progress = 100
            target.reminder_sent = True
        elif target.remind_at:
            target.reminder_sent = False
        target.updated_at = datetime.now()
        if not cascade:
            return
        children_map = self._children_map(task_map)
        for child in children_map.get(task_id, []):
            self._set_completion_state(session, task_map, child.id, completed, cascade=True)

    def _refresh_parent_chain(
        self,
        session: Session,
        parent_id: Optional[int],
        *,
        task_map: Optional[dict[int, Task]] = None,
    ) -> None:
        if parent_id is None:
            return
        task_map = task_map or self._task_map(session)
        children_map = self._children_map(task_map)
        current_parent_id = parent_id
        while current_parent_id is not None:
            parent = task_map.get(current_parent_id)
            if parent is None:
                return
            children = children_map.get(current_parent_id, [])
            if children:
                should_complete = all(child.completed for child in children)
                parent.completed = should_complete
                parent.completed_at = datetime.now() if should_complete else None
                # When auto-completing a parent (all children done), suppress its reminder
                # to prevent it re-triggering if a new child is added later.
                if should_complete:
                    parent.reminder_sent = True
                parent.updated_at = datetime.now()
            current_parent_id = parent.parent_id

    def _task_to_dict(self, task: Task) -> dict[str, Any]:
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "category": task.category,
            "tags": task.tags,
            "priority": task.priority,
            "due_at": task.due_at.isoformat() if task.due_at else None,
            "remind_at": task.remind_at.isoformat() if task.remind_at else None,
            "progress": 100 if task.completed else self._normalize_progress(task.progress),
            "estimated_minutes": task.estimated_minutes,
            "tracked_minutes": task.tracked_minutes,
            "recurrence_rule": task.recurrence_rule,
            "completed": task.completed,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "reminder_sent": task.reminder_sent,
            "sort_order": task.sort_order,
            "parent_id": task.parent_id,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }

    def _validate_import_payload(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            raise ValueError("导入失败，文件根结构必须为对象。")
        tasks = payload.get("tasks")
        notes = payload.get("notes")
        if not isinstance(tasks, list) or not isinstance(notes, list):
            raise ValueError("导入失败，缺少 tasks 或 notes 列表。")
        self._validate_tasks_payload(tasks)
        for note_data in notes:
            if not isinstance(note_data, dict):
                raise ValueError("导入失败，notes 中存在非法条目。")

    def _validate_tasks_payload(self, tasks: list[Any]) -> None:
        required = {"id", "title"}
        for index, task_data in enumerate(tasks, start=1):
            if not isinstance(task_data, dict):
                raise ValueError(f"导入失败，第 {index} 条任务不是对象。")
            missing = [field for field in required if field not in task_data]
            if missing:
                raise ValueError(f"导入失败，第 {index} 条任务缺少字段：{', '.join(missing)}")
            if task_data.get("parent_id") == task_data.get("id"):
                raise ValueError(f"导入失败，第 {index} 条任务的 parent_id 不能指向自身。")

    @staticmethod
    def parse_tags(value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    def _build_next_recurrence_payload(self, task: Task) -> Optional[dict[str, Any]]:
        if task.recurrence_rule == "不重复":
            return None
        
        current_due = task.due_at or datetime.now()
        next_due = None
        
        if task.recurrence_rule == "每天":
            next_due = current_due + timedelta(days=1)
        elif task.recurrence_rule == "每工作日":
            # 1=Mon, 5=Fri, 6=Sat, 7=Sun
            days_to_add = 1
            if current_due.isoweekday() == 5: # Friday
                days_to_add = 3
            elif current_due.isoweekday() == 6: # Saturday
                days_to_add = 2
            next_due = current_due + timedelta(days=days_to_add)
        elif task.recurrence_rule == "每周":
            next_due = current_due + timedelta(weeks=1)
        elif task.recurrence_rule == "每两周":
            next_due = current_due + timedelta(weeks=2)
        elif task.recurrence_rule == "每月":
            # Add one month logic
            import calendar
            month = current_due.month
            year = current_due.year + month // 12
            month = month % 12 + 1
            day = min(current_due.day, calendar.monthrange(year, month)[1])
            next_due = current_due.replace(year=year, month=month, day=day)
        
        if next_due is None:
            return None
            
        # Calculate remind_at delta if exists
        remind_at = None
        if task.remind_at and task.due_at:
            delta = task.due_at - task.remind_at
            remind_at = next_due - delta
        elif task.remind_at:
            # If no due_at but has remind_at, just add the same interval
            interval = next_due - current_due
            remind_at = task.remind_at + interval

        return {
            "title": task.title,
            "description": task.description,
            "category": task.category,
            "tags": task.tags,
            "priority": task.priority,
            "due_at": next_due,
            "remind_at": remind_at,
            "progress": 0,
            "estimated_minutes": task.estimated_minutes,
            "tracked_minutes": 0,
            "recurrence_rule": task.recurrence_rule,
            "parent_id": task.parent_id,
        }

    @staticmethod
    def _normalize_progress(value: Any) -> int:
        try:
            progress = int(value)
        except (TypeError, ValueError):
            return 0
        return max(0, min(100, progress))

    def _load_category_registry(self) -> set[str]:
        if not self._category_file.exists():
            return set()
        try:
            payload = json.loads(self._category_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return set()
        if not isinstance(payload, list):
            return set()
        return {str(item).strip() for item in payload if str(item).strip()}

    def _save_category_registry(self, categories: set[str]) -> None:
        self._category_file.write_text(
            json.dumps(sorted(categories), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _note_to_dict(self, note: Note) -> dict[str, Any]:
        return {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "pinned": note.pinned,
            "created_at": note.created_at.isoformat() if note.created_at else None,
            "updated_at": note.updated_at.isoformat() if note.updated_at else None,
        }

    @staticmethod
    def combine_date_and_time(day: Optional[date], moment: Optional[time]) -> Optional[datetime]:
        if day is None or moment is None:
            return None
        return datetime.combine(day, moment)

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        return datetime.fromisoformat(value)
