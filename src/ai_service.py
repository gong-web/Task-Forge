"""AI Service — 基于云雾API (OpenAI-compatible) 的智能分析服务。

所有分析均基于用户真实任务数据，绝不使用mock数据。
使用 QThread 避免阻塞 UI。
"""
from __future__ import annotations

import json
import logging
import os
import socket
import ssl
import time
import urllib.request
import urllib.error
from datetime import date, datetime
from typing import Any, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from runtime_support import load_config

_logger = logging.getLogger("task_forge.ai")

DEFAULT_API_BASE = "https://yunwu.ai/v1"
DEFAULT_MODEL = "gpt-4o"
LEGACY_API_KEY = "sk-RtqbnLgCnRcoVY8ignf3VjlWktWVmzJ2vtFb2EEmG9uyLAnJ"
RETRYABLE_HTTP_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


def _build_ssl_context() -> ssl.SSLContext:
    cafile = None
    try:
        import certifi  # type: ignore

        cafile = certifi.where()
    except Exception:
        cafile = None

    context = ssl.create_default_context(cafile=cafile)
    if hasattr(ssl, "TLSVersion"):
        context.minimum_version = ssl.TLSVersion.TLSv1_2
    if hasattr(ssl, "OP_NO_COMPRESSION"):
        context.options |= ssl.OP_NO_COMPRESSION
    return context


def _ai_error_text(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"AI 服务响应异常（HTTP {exc.code}）"
    if isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        if isinstance(reason, ssl.SSLError):
            return "安全连接被对端中断，已自动重试但仍未成功"
        if isinstance(reason, TimeoutError | socket.timeout):
            return "连接 AI 服务超时"
        return f"网络连接失败：{reason}"
    if isinstance(exc, ssl.SSLError):
        return "安全连接被对端中断，已自动重试但仍未成功"
    if isinstance(exc, TimeoutError | socket.timeout):
        return "连接 AI 服务超时"
    return str(exc)


def _is_retryable_ai_error(exc: Exception) -> bool:
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in RETRYABLE_HTTP_STATUS
    if isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        if isinstance(reason, (TimeoutError, socket.timeout, ssl.SSLError)):
            return True
        text = str(reason).lower()
        return any(token in text for token in ["timed out", "timeout", "eof", "connection reset", "temporarily", "handshake"])
    if isinstance(exc, (TimeoutError, socket.timeout, ssl.SSLError)):
        return True
    text = str(exc).lower()
    return any(token in text for token in ["timed out", "timeout", "eof", "connection reset", "temporarily", "handshake"])


def _ai_settings() -> tuple[str, str, str, int]:
    config = load_config()
    api_base = (
        os.getenv("TASK_FORGE_AI_API_BASE")
        or os.getenv("OPENAI_BASE_URL")
        or config.get("ai_api_base")
        or DEFAULT_API_BASE
    ).rstrip("/")
    api_key = (
        os.getenv("TASK_FORGE_AI_API_KEY")
        or os.getenv("YUNWU_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or config.get("ai_api_key")
        or LEGACY_API_KEY
    ).strip()
    model = (
        os.getenv("TASK_FORGE_AI_MODEL")
        or os.getenv("OPENAI_MODEL")
        or config.get("ai_model")
        or DEFAULT_MODEL
    ).strip()
    timeout = int(config.get("ai_timeout_sec", 30) or 30)
    return api_base, api_key, model, timeout


def _chat_completion(messages: list[dict], temperature: float = 0.7, max_tokens: int = 2048) -> str:
    """同步调用 OpenAI-compatible chat completions 接口，返回 assistant 内容。"""
    api_base, api_key, model, timeout = _ai_settings()
    if not api_key:
        return "[AI 未配置 API Key]"
    url = f"{api_base}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Connection": "close",
            "User-Agent": "TaskForgeDesktop/1.0",
        },
        method="POST",
    )
    context = _build_ssl_context()
    last_exc: Exception | None = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body["choices"][0]["message"]["content"]
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError, ssl.SSLError, TimeoutError, socket.timeout) as exc:
            last_exc = exc
            should_retry = attempt < 3 and _is_retryable_ai_error(exc)
            _logger.warning("AI 请求失败（第 %s/3 次）: %s", attempt, exc)
            if should_retry:
                time.sleep(min(3.0, 0.8 * (2 ** (attempt - 1))))
                continue
            break
    return f"[AI 分析暂时不可用: {_ai_error_text(last_exc or Exception('未知错误'))}]"


# ── 数据摘要构造 ────────────────────────────────────────────────────

def _build_task_summary(tasks: list) -> str:
    """将任务列表转为紧凑文本摘要，供 LLM 分析。"""
    if not tasks:
        return "当前没有任何任务数据。"
    lines = []
    for t in tasks[:60]:  # 限制发送量
        status = "已完成" if t.completed else "进行中"
        due = t.due_at.strftime("%Y-%m-%d %H:%M") if t.due_at else "无截止"
        tags = t.tags if t.tags else ""
        lines.append(
            f"- [{status}] {t.title} | 分类:{t.category} | 优先级:{t.priority} "
            f"| 截止:{due} | 预估:{t.estimated_minutes}m | 专注:{t.tracked_minutes}m "
            f"| 循环:{t.recurrence_rule} | 标签:{tags}"
        )
    header = f"共 {len(tasks)} 条任务（以下展示前 {min(len(tasks), 60)} 条）：\n"
    return header + "\n".join(lines)


def _build_kanban_context(snapshot: dict) -> str:
    """为看板视图构建分析上下文。"""
    summary = snapshot.get("summary", {})
    columns = snapshot.get("columns", {})
    lines = [
        f"看板概况: 活跃{summary.get('active', 0)}项, 本周完成{summary.get('throughput', 0)}项, "
        f"逾期{summary.get('overdue', 0)}项, 今日到期{summary.get('due_today', 0)}项",
        f"专注总计: {summary.get('focus_minutes', 0)}分钟",
    ]
    for col_key, col_tasks in columns.items():
        names = [t.title for t in col_tasks[:8]]
        lines.append(f"  {col_key}列({len(col_tasks)}项): {', '.join(names) if names else '空'}")
    return "\n".join(lines)


def _build_analytics_context(snapshot: dict, tasks: list) -> str:
    """为深度分析视图构建分析上下文。"""
    radar = snapshot.get("radar", {})
    insights = snapshot.get("insights", [])
    task_summary = _build_task_summary(tasks)
    lines = [
        "雷达图维度分数(0~1):",
    ]
    labels = radar.get("labels", [])
    values = radar.get("values", [])
    for lbl, val in zip(labels, values):
        lines.append(f"  {lbl}: {val:.2f}")
    lines.append(f"\n现有洞察: {'; '.join(insights)}")
    lines.append(f"\n任务明细:\n{task_summary}")
    return "\n".join(lines)


def _build_task_detail_context(task: Any, children: list[Any]) -> str:
    child_lines = []
    for child in children[:12]:
        child_state = "完成" if child.completed else "未完成"
        child_lines.append(f"- {child_state} | {child.title} | 预估 {child.estimated_minutes or 0}m | 已投入 {child.tracked_minutes or 0}m")
    due_text = task.due_at.strftime("%Y-%m-%d %H:%M") if getattr(task, "due_at", None) else "未设置"
    remind_text = task.remind_at.strftime("%Y-%m-%d %H:%M") if getattr(task, "remind_at", None) else "未设置"
    return "\n".join(
        [
            f"标题: {task.title}",
            f"分类: {task.category or '默认'}",
            f"优先级: {task.priority or '中'}",
            f"描述: {task.description or '无'}",
            f"截止: {due_text}",
            f"提醒: {remind_text}",
            f"循环: {task.recurrence_rule or '不重复'}",
            f"预估投入: {task.estimated_minutes or 0} 分钟",
            f"实际投入: {task.tracked_minutes or 0} 分钟",
            f"完成状态: {'已完成' if task.completed else '未完成'}",
            f"标签: {task.tags or '无'}",
            "子任务:\n" + ("\n".join(child_lines) if child_lines else "- 无子任务"),
        ]
    )


def _build_task_draft_context(payload: dict[str, Any]) -> str:
    due_at = payload.get("due_at")
    due_text = due_at.strftime("%Y-%m-%d %H:%M") if due_at else "未设置"
    return "\n".join(
        [
            f"标题: {payload.get('title') or '无'}",
            f"描述: {payload.get('description') or '无'}",
            f"现有分类: {payload.get('category') or '默认'}",
            f"现有标签: {payload.get('tags') or '无'}",
            f"现有优先级: {payload.get('priority') or '中'}",
            f"预估时长: {payload.get('estimated_minutes') or 0} 分钟",
            f"截止时间: {due_text}",
            f"循环规则: {payload.get('recurrence_rule') or '不重复'}",
        ]
    )


def _infer_category_from_text(text: str) -> str:
    mapping = {
        "实验": "实验",
        "课程": "学习",
        "考试": "学习",
        "论文": "学习",
        "报告": "学习",
        "作业": "学习",
        "会议": "工作",
        "汇报": "工作",
        "项目": "项目",
        "代码": "开发",
        "开发": "开发",
        "测试": "开发",
        "设计": "设计",
        "采购": "生活",
        "收纳": "生活",
        "运动": "生活",
    }
    for keyword, category in mapping.items():
        if keyword in text:
            return category
    return "默认"


def _infer_tags_from_text(text: str) -> list[str]:
    mapping = {
        "实验": "实验",
        "报告": "报告",
        "论文": "写作",
        "答辩": "答辩",
        "考试": "考试",
        "复习": "复习",
        "会议": "会议",
        "汇报": "汇报",
        "整理": "整理",
        "代码": "编码",
        "开发": "编码",
        "测试": "测试",
        "设计": "设计",
        "调研": "调研",
        "阅读": "阅读",
    }
    tags: list[str] = []
    for keyword, tag in mapping.items():
        if keyword in text and tag not in tags:
            tags.append(tag)
    return tags[:4]


def _infer_priority(text: str, due_at: Any) -> str:
    if any(word in text for word in ["紧急", "马上", "尽快", "今天", "明天", "答辩", "考试", "截止"]):
        return "高"
    if due_at:
        try:
            if (due_at - datetime.now()).total_seconds() <= 24 * 3600:
                return "高"
        except Exception:
            pass
    if any(word in text for word in ["整理", "阅读", "记录"]):
        return "低"
    return "中"


def _infer_estimated_minutes(text: str, current: int) -> int:
    if current and current > 0:
        return current
    if any(word in text for word in ["答辩", "论文", "实验报告", "项目汇报"]):
        return 120
    if any(word in text for word in ["报告", "作业", "开发", "设计", "调研"]):
        return 90
    if any(word in text for word in ["会议", "沟通", "复盘", "整理"]):
        return 45
    if any(word in text for word in ["阅读", "背诵", "练习"]):
        return 35
    return 60


def local_task_draft_payload(payload: dict[str, Any]) -> dict[str, Any]:
    title = str(payload.get("title") or "").strip()
    description = str(payload.get("description") or "").strip()
    category = str(payload.get("category") or "默认").strip()
    tags = str(payload.get("tags") or "").strip()
    priority = str(payload.get("priority") or "中").strip()
    due_at = payload.get("due_at")
    merged_text = f"{title} {description} {category}".lower()

    inferred_category = category if category and category != "默认" else _infer_category_from_text(merged_text)
    inferred_tags = [tag.strip() for tag in tags.split(",") if tag.strip()] or _infer_tags_from_text(merged_text)
    inferred_priority = priority if priority in {"高", "中", "低"} and priority != "中" else _infer_priority(merged_text, due_at)
    estimated_minutes = _infer_estimated_minutes(merged_text, int(payload.get("estimated_minutes") or 0))
    refined_description = description or f"围绕“{title or '当前任务'}”拆分执行步骤，先明确完成标准，再按优先顺序推进，过程中记录关键阻塞与结果。"

    return {
        "summary": f"已根据当前输入生成结构化录入建议，建议分类为{inferred_category}，优先级为{inferred_priority}。",
        "metrics": [
            {"label": "建议分类", "value": inferred_category, "trend": "flat", "color": "#78aef6"},
            {"label": "建议优先级", "value": inferred_priority, "trend": "up" if inferred_priority == "高" else "flat", "color": "#d7b277"},
            {"label": "建议时长", "value": f"{estimated_minutes} 分钟", "trend": "flat", "color": "#6fd2c3"},
        ],
        "sections": [
            {
                "title": "录入判断",
                "color": "#78aef6",
                "items": [
                    {"text": f"任务当前更接近“{inferred_category}”场景。", "severity": "info"},
                    {"text": f"建议保留 {len(inferred_tags) or 1} 个标签，避免过多标签稀释检索效果。", "severity": "low"},
                ],
            },
            {
                "title": "补全建议",
                "color": "#d7b277",
                "items": [
                    {"text": "如果任务描述偏短，系统会自动补足执行导向说明，但不会覆盖已写好的长描述。", "severity": "medium"},
                    {"text": "优先级和预估时长只会在默认值或空白状态下自动填充。", "severity": "info"},
                ],
            },
        ],
        "actions": [
            {"text": "确认标题是否已经指向明确产出物，例如报告、作业、页面或实验。", "priority": "medium"},
            {"text": "若存在截止时间，优先补充关键约束与交付标准。", "priority": "high" if inferred_priority == "高" else "medium"},
        ],
        "autofill": {
            "category": inferred_category,
            "priority": inferred_priority,
            "estimated_minutes": estimated_minutes,
            "tags": inferred_tags,
            "description_refined": refined_description,
        },
    }


def local_task_insight_payload(task: Any, children: list[Any]) -> dict[str, Any]:
    overdue = bool(not task.completed and getattr(task, "due_at", None) and task.due_at < datetime.now())
    child_total = len(children)
    child_done = sum(1 for child in children if child.completed)
    due_text = task.due_at.strftime("%m-%d %H:%M") if getattr(task, "due_at", None) else "未设截止"
    tracked = int(getattr(task, "tracked_minutes", 0) or 0)
    estimated = int(getattr(task, "estimated_minutes", 0) or 0)
    load_rate = round(tracked / estimated * 100) if estimated else 0
    state_text = "已完成" if task.completed else ("逾期待推进" if overdue else "推进中")
    next_focus = "优先梳理剩余阻塞并完成当前主产出。"
    if task.completed:
        next_focus = "当前任务已完成，可转向归档与复盘。"
    elif child_total and child_done < child_total:
        next_focus = "先推进未完成子任务中最接近截止的一项。"

    return {
        "summary": f"当前任务状态为{state_text}，截止 {due_text}，建议下一步保持单点推进。",
        "metrics": [
            {"label": "当前状态", "value": state_text, "trend": "down" if overdue else "flat", "color": "#d7969b" if overdue else "#78aef6"},
            {"label": "子任务进度", "value": f"{child_done}/{child_total}", "trend": "up" if child_done else "flat", "color": "#6fd2c3"},
            {"label": "投入比", "value": f"{load_rate}%", "trend": "up" if load_rate >= 100 else "flat", "color": "#d7b277"},
        ],
        "sections": [
            {
                "title": "当前态势",
                "color": "#78aef6",
                "items": [
                    {"text": f"分类 {task.category or '默认'}，优先级 {task.priority or '中'}，循环规则 {task.recurrence_rule or '不重复'}。", "severity": "info"},
                    {"text": f"已投入 {tracked} 分钟，预估 {estimated} 分钟。", "severity": "low"},
                ],
            },
            {
                "title": "风险提示",
                "color": "#d7969b",
                "items": [
                    {"text": "任务已逾期，建议先缩小范围并确保最小交付物先完成。", "severity": "high"} if overdue else {"text": "暂无硬性时间风险，但仍需避免继续积压。", "severity": "info"},
                    {"text": "存在子任务未完成，详情页建议以单一阻塞点为中心阅读。", "severity": "medium"} if child_total and child_done < child_total else {"text": "层级结构较简单，后续维护成本较低。", "severity": "low"},
                ],
            },
            {
                "title": "下一步建议",
                "color": "#6fd2c3",
                "items": [
                    {"text": next_focus, "severity": "positive"},
                    {"text": "如果描述仍偏空泛，建议在编辑页补充完成标准、依赖项和输出文件。", "severity": "info"},
                ],
            },
        ],
        "actions": [
            {"text": "进入编辑页补充完成标准和关键约束。", "priority": "medium"},
            {"text": "按优先级先推进最接近交付的子任务。", "priority": "high" if overdue else "medium"},
        ],
        "briefing": {
            "state": state_text,
            "next_focus": next_focus,
            "due_text": due_text,
        },
    }


# ── 系统提示词 ──────────────────────────────────────────────────────

KANBAN_SYSTEM = """你是一个专业的任务管理AI助手，擅长分析看板数据并给出可执行的建议。
请用中文回答，保持简洁有力。

你必须返回**严格的 JSON 对象**（不要包含任何 markdown 代码块标记），格式如下：
{
  "summary": "一句话总结当前看板状态",
  "metrics": [
    {"label": "指标名", "value": "数值", "trend": "up/down/flat", "color": "#hex颜色"}
  ],
  "sections": [
    {
      "title": "分析维度标题",
      "color": "#hex颜色",
      "items": [
        {"text": "具体内容", "severity": "high/medium/low/info"}
      ]
    }
  ],
  "actions": [
    {"text": "行动建议内容", "priority": "high/medium/low"}
  ]
}

包含以下分析维度(作为 sections):
- 瓶颈识别(color:#fb7185): 哪些任务或阶段需要关注
- 优先级建议(color:#f59e0b): 今天/本周应该先做什么
- 风险提示(color:#60a5fa): 逾期、负载过重等
metrics 包含 2-4 个关键指标如执行率、完成率等。
actions 包含 2-3 条具体可执行的下一步行动。
"""

ANALYTICS_SYSTEM = """你是一个专业的个人效能分析AI助手，擅长从任务数据中发现深层模式和改进机会。
请用中文回答。

你必须返回**严格的 JSON 对象**（不要包含任何 markdown 代码块标记），格式如下：
{
  "summary": "一句话总结个人效能状况",
  "metrics": [
    {"label": "指标名", "value": "数值/百分比", "trend": "up/down/flat", "color": "#hex颜色"}
  ],
  "sections": [
    {
      "title": "分析维度标题",
      "color": "#hex颜色",
      "items": [
        {"text": "具体分析内容", "severity": "high/medium/low/info"}
      ]
    }
  ],
  "actions": [
    {"text": "具体行动建议", "priority": "high/medium/low"}
    ],
    "ability_profile": [
        {"label": "执行完成", "score": 0.0, "color": "#hex颜色", "summary": "一句点评"}
    ]
}

包含以下分析维度(作为 sections):
- 能力画像: 基于任务数据概括当前能力结构
- 优势识别: 哪些维度表现突出
- 改进空间: 哪些维度需要提升及具体建议
- 时间洞察: 专注投入、估时、到期安排之间是否协调
额外要求：
- 只输出上面的 JSON，不要额外解释，不要输出 markdown。
- ability_profile 必须严格覆盖这 7 个固定维度，顺序不能改：执行完成、按期交付、专注投入、计划严谨、工作平衡、知识沉淀、任务健康。
- ability_profile.score 必须是 0~1 之间的小数。
- ability_profile.summary 必须是短句，适合直接放进界面。
- 不要输出 radar、chart、extra_notes 等重复结构。
metrics 包含 3-5 个关键指标如执行力、完成率、专注度等。
actions 包含 3-5 条个性化行动计划。
"""

TASK_DETAIL_SYSTEM = """你是任务详情分析助手。请根据单个任务及其子任务数据，输出严格 JSON 对象（不要 markdown 代码块）。
格式如下：
{
  "summary": "一句任务态势判断",
  "metrics": [
    {"label": "指标名", "value": "值", "trend": "up/down/flat", "color": "#hex"}
  ],
  "sections": [
    {
      "title": "区块标题",
      "color": "#hex",
      "items": [
        {"text": "内容", "severity": "high/medium/low/info/positive"}
      ]
    }
  ],
  "actions": [
    {"text": "具体动作", "priority": "high/medium/low"}
  ],
  "briefing": {
    "state": "状态短语",
    "next_focus": "下一步聚焦",
    "due_text": "截止判断"
  }
}
要求：判断必须具体，不能空泛，不要虚构任务中不存在的信息。"""

TASK_DRAFT_SYSTEM = """你是任务录入助手。请根据用户正在填写的标题、描述、分类、优先级和截止时间，输出严格 JSON 对象（不要 markdown 代码块）。
格式如下：
{
  "summary": "一句录入建议总结",
  "metrics": [
    {"label": "指标名", "value": "值", "trend": "up/down/flat", "color": "#hex"}
  ],
  "sections": [
    {
      "title": "区块标题",
      "color": "#hex",
      "items": [
        {"text": "内容", "severity": "high/medium/low/info"}
      ]
    }
  ],
  "actions": [
    {"text": "具体动作", "priority": "high/medium/low"}
  ],
  "autofill": {
    "category": "建议分类",
    "priority": "高/中/低",
    "estimated_minutes": 60,
    "tags": ["标签1", "标签2"],
    "description_refined": "一段不超过90字的执行描述"
  }
}
要求：仅在信息足够时提出补全建议，不要制造不真实的硬约束。"""


# ── QThread 工作线程 ────────────────────────────────────────────────

class AIWorker(QThread):
    """通用 AI 分析工作线程。完成后发射 finished 信号，携带结果文本。"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    _active_workers: set["AIWorker"] = set()

    def __init__(self, system_prompt: str, user_content: str, parent=None):
        super().__init__(None)
        self.system_prompt = system_prompt
        self.user_content = user_content
        self.finished.connect(self._release_reference)
        self.error.connect(self._release_reference)

    def start(self, priority: QThread.Priority = QThread.Priority.InheritPriority) -> None:
        AIWorker._active_workers.add(self)
        super().start(priority)

    def _release_reference(self, *_args) -> None:
        AIWorker._active_workers.discard(self)

    def run(self):
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.user_content},
            ]
            result = _chat_completion(messages)
            self.finished.emit(result)
        except Exception as exc:
            _logger.exception("AI Worker 异常")
            self.error.emit(str(exc))


class KanbanAIWorker(AIWorker):
    """专门用于看板分析的工作线程。"""
    def __init__(self, kanban_snapshot: dict, parent=None):
        context = _build_kanban_context(kanban_snapshot)
        user_msg = f"请分析以下看板数据并给出建议：\n\n{context}"
        super().__init__(KANBAN_SYSTEM, user_msg, parent)


class AnalyticsAIWorker(AIWorker):
    """专门用于深度分析的工作线程。"""
    def __init__(self, analytics_snapshot: dict, tasks: list, parent=None):
        context = _build_analytics_context(analytics_snapshot, tasks)
        user_msg = f"请基于以下真实数据进行深度分析：\n\n{context}"
        super().__init__(ANALYTICS_SYSTEM, user_msg, parent)


class TaskInsightAIWorker(AIWorker):
    def __init__(self, task: Any, children: list[Any], parent=None):
        context = _build_task_detail_context(task, children)
        user_msg = f"请根据以下任务档案给出结构化分析：\n\n{context}"
        super().__init__(TASK_DETAIL_SYSTEM, user_msg, parent)


class TaskDraftAIWorker(AIWorker):
    def __init__(self, payload: dict[str, Any], parent=None):
        context = _build_task_draft_context(payload)
        user_msg = f"请根据以下录入草稿给出结构化建议：\n\n{context}"
        super().__init__(TASK_DRAFT_SYSTEM, user_msg, parent)


# ── 工作台 AI ──────────────────────────────────────────────────────

DASHBOARD_SYSTEM = """你是一个任务管理 AI 助手，专注工作台每日洞察。请用中文，语气简洁、激励性，结合数据具体说话。
返回**严格的 JSON 对象**（不含任何 markdown 代码块标记），格式如下：
{
  "greeting": "一句个性化今日状态判断（25字内，含具体数据和建议）",
  "focus_task": "今天最优先处理的方向（任务名或方向，15字内）",
  "insights": [
    {"text": "洞察内容（具体、有数据支撑）", "color": "#hex颜色", "tag": "风险/建议/进度/习惯"}
  ],
  "actions": [
    {"text": "具体可执行的下一步行动", "priority": "high/medium/low"}
  ]
}
insights 包含 3-4 条精炼洞察，actions 包含 2-3 条建议。请不要泛泛而谈。
"""


def _build_dashboard_context(snapshot: dict) -> str:
    s = snapshot.get("snapshot", {})
    trend = snapshot.get("trend", [])
    weekly = sum(int(item.get("completed", 0)) for item in trend[-7:])
    upcoming = snapshot.get("upcoming_lines", [])
    on_time = snapshot.get("on_time_rate", 100)
    today_str = date.today().strftime("%Y-%m-%d %A")
    lines = [
        f"当前日期: {today_str}",
        f"活跃任务: {s.get('active', 0)} 项",
        f"本周完成: {weekly} 项",
        f"逾期任务: {s.get('overdue', 0)} 项",
        f"今日到期: {s.get('due_today', 0)} 项",
        f"累计专注: {s.get('focus_minutes', 0)} 分钟",
        f"完成率: {s.get('completion_rate', 0)}%",
        f"按期完成率: {on_time}%",
        f"连续活跃: {snapshot.get('hero_hint', '').split('｜')[0]}",
        f"近期到期任务: {'; '.join(upcoming[:3]) if upcoming and not upcoming[0].startswith('暂无') else '暂无'}",
    ]
    return "\n".join(lines)


class DashboardAIWorker(AIWorker):
    """专门用于工作台洞察的工作线程。"""
    def __init__(self, dashboard_snapshot: dict, parent=None):
        context = _build_dashboard_context(dashboard_snapshot)
        user_msg = f"请基于以下数据给出今日工作台洞察：\n\n{context}"
        super().__init__(DASHBOARD_SYSTEM, user_msg, parent)
