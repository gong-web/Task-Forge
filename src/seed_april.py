"""
seed_april.py — 在现有数据库中插入约 250 条 4 月任务，覆盖核心边界情况组合。

用法（从项目根目录执行）：
    python src/seed_april.py

脚本幂等：若已存在以 "[April]" 开头的任务则跳过，避免重复插入。
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timedelta

# ── 路径修正：让 src 目录可被直接 import ──
_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from DB import DB  # noqa: E402

# ════════════════════════════════════════════════════════════════════
#  Helper
# ════════════════════════════════════════════════════════════════════

_BASE = datetime(2026, 4, 1, 9, 0, 0)   # April 2026 基准时刻


def apr(day: int, hour: int = 9, minute: int = 0) -> datetime:
    """返回 2026 年 4 月第 day 天 HH:MM 的 datetime（day 从 1 开始，超过 30 进入 5 月）。"""
    return _BASE + timedelta(days=day - 1, hours=hour - 9, minutes=minute)


def mar(day: int, hour: int = 9) -> datetime:
    """返回 2026 年 3 月第 day 天（三月，即 4 月前，已过期）。"""
    return datetime(2026, 3, day, hour, 0, 0)


def may(day: int, hour: int = 9) -> datetime:
    """返回 2026 年 5 月第 day 天（未来）。"""
    return datetime(2026, 5, day, hour, 0, 0)


CATEGORIES = ["学习", "工作", "生活", "课程", "开发", "健康", "社交", "阅读"]
PRIORITIES = ["高", "中", "低"]

COUNTER = [0]


def _fmt_dt(value: datetime | None) -> str:
    if value is None:
        return "未设置"
    return value.strftime("%Y-%m-%d %H:%M")


def _auto_detail(
    title: str,
    *,
    category: str,
    priority: str,
    due_at: datetime | None,
    remind_at: datetime | None,
    estimated_minutes: int,
    tracked_minutes: int,
    recurrence_rule: str,
    tags: str,
    parent_id: int | None,
    progress: int,
) -> str:
    relation = "子任务" if parent_id is not None else "主任务"
    time_note = "时间正常"
    if due_at is None and remind_at is None:
        time_note = "无时间约束"
    elif due_at is None and remind_at is not None:
        time_note = "仅提醒无截止"
    elif due_at is not None and remind_at is not None and remind_at > due_at:
        time_note = "提醒晚于截止（异常边界）"
    elif due_at is not None and remind_at is not None and remind_at == due_at:
        time_note = "提醒等于截止（边界）"

    lines = [
        f"任务背景：{title}，用于 April 数据回归与视图演示。",
        f"任务属性：{relation}｜类别={category}｜优先级={priority}｜进度={progress}%｜循环={recurrence_rule}。",
        f"时间安排：截止={_fmt_dt(due_at)}｜提醒={_fmt_dt(remind_at)}｜判定={time_note}。",
        f"投入信息：预计 {estimated_minutes} 分钟，已记录 {tracked_minutes} 分钟。",
    ]
    if tags.strip():
        lines.append(f"标签说明：{tags}。")
    return "\n".join(lines)


def _t(
    title: str,
    *,
    category: str = "学习",
    priority: str = "中",
    description: str = "",
    tags: str = "",
    due_at: datetime | None = None,
    remind_at: datetime | None = None,
    progress: int = 0,
    estimated_minutes: int = 60,
    tracked_minutes: int = 0,
    recurrence_rule: str = "不重复",
    parent_id: int | None = None,
    completed: bool = False,
    reminder_sent: bool = False,
) -> dict:
    COUNTER[0] += 1
    if not description:
        description = _auto_detail(
            title,
            category=category,
            priority=priority,
            due_at=due_at,
            remind_at=remind_at,
            estimated_minutes=estimated_minutes,
            tracked_minutes=tracked_minutes,
            recurrence_rule=recurrence_rule,
            tags=tags,
            parent_id=parent_id,
            progress=progress,
        )
    return {
        "title": f"[April] {title}",
        "category": category,
        "priority": priority,
        "description": description,
        "tags": tags,
        "due_at": due_at,
        "remind_at": remind_at,
        "progress": progress,
        "estimated_minutes": estimated_minutes,
        "tracked_minutes": tracked_minutes,
        "recurrence_rule": recurrence_rule,
        "parent_id": parent_id,
        "completed": completed,
        "_reminder_sent": reminder_sent,  # 用于创建后单独 update
    }


# ════════════════════════════════════════════════════════════════════
#  主逻辑
# ════════════════════════════════════════════════════════════════════

def seed_april(db: DB) -> None:
    # 幂等检查：若已有 [April] 前缀任务则跳过
    existing = db.list_tasks()
    if any(t.title.startswith("[April]") for t in existing):
        print("已检测到 [April] 前缀任务，跳过重复插入。")
        return

    created_ids: list[int] = []

    def make(payload: dict, mark_complete: bool = False, reminder_sent: bool = False) -> int:
        """创建任务并返回 id；可选标记完成 / reminder_sent。"""
        _rs = payload.pop("_reminder_sent", False)
        _completed = payload.pop("completed", False) or mark_complete
        task = db.create_task(payload)
        upd: dict = {}
        if _completed:
            upd["completed"] = True
        if _rs or reminder_sent:
            upd["reminder_sent"] = True
        if upd:
            db.update_task(task.id, upd)
        created_ids.append(task.id)
        return task.id

    # ────────────────────────────────────────────────────────────────
    #  GROUP A：独立任务 — 截止日 / 提醒日组合 (共 ~40 条)
    # ────────────────────────────────────────────────────────────────

    # A1: due_at 填，remind_at 为 None（10 条）
    for i in range(1, 11):
        day = i + 1
        make(_t(
            f"A1-{i} 仅截止日-{day}号",
            category=CATEGORIES[i % len(CATEGORIES)],
            priority=PRIORITIES[i % 3],
            due_at=apr(day),
            estimated_minutes=30 + i * 5,
            tags="仅截止",
        ))

    # A2: remind_at 填，due_at 为 None（5 条）
    for i in range(1, 6):
        make(_t(
            f"A2-{i} 仅提醒无截止",
            category=CATEGORIES[(i + 2) % len(CATEGORIES)],
            remind_at=apr(i * 2, hour=8),
            estimated_minutes=45,
            tags="仅提醒",
        ))

    # A3: due_at 和 remind_at 均填，remind_at < due_at（正常，10 条）
    for i in range(1, 11):
        day = i + 5
        make(_t(
            f"A3-{i} 提前提醒-{day}号截止",
            due_at=apr(day, hour=18),
            remind_at=apr(day - 1, hour=9),
            priority=PRIORITIES[i % 3],
            category=CATEGORIES[i % len(CATEGORIES)],
            tags="正常提醒",
            estimated_minutes=60,
        ))

    # A4: remind_at == due_at（边界，5 条）
    for i in range(1, 6):
        day = i + 10
        make(_t(
            f"A4-{i} 提醒等于截止-{day}号",
            due_at=apr(day, hour=14),
            remind_at=apr(day, hour=14),
            tags="边界-提醒=截止",
            estimated_minutes=30,
        ))

    # A5: remind_at > due_at（非正常，5 条；系统应容忍或纠正此边界）
    for i in range(1, 6):
        day = i + 15
        make(_t(
            f"A5-{i} 提醒晚于截止-{day}号",
            due_at=apr(day, hour=10),
            remind_at=apr(day, hour=18),
            tags="异常-提醒>截止",
            estimated_minutes=45,
            priority="低",
        ))

    # A6: due_at 和 remind_at 均为 None（纯待办，5 条）
    for i in range(1, 6):
        make(_t(
            f"A6-{i} 纯待办无时间约束",
            category=CATEGORIES[i % len(CATEGORIES)],
            priority=PRIORITIES[i % 3],
            tags="纯待办",
            estimated_minutes=0,
        ))

    # ────────────────────────────────────────────────────────────────
    #  GROUP B：父子层次结构 (~40 条)
    # ────────────────────────────────────────────────────────────────

    # B1–B8：两级父子（8 个父 × 每个 4 子）
    themes = [
        ("B1 软件工程复习", "学习", "高", ["需求分析", "UML建模", "测试用例", "架构设计", "项目答辩"]),
        ("B2 英语四级备考", "学习", "中", ["词汇背诵", "阅读理解", "写作训练", "听力练习", "模拟考试"]),
        ("B3 健身月计划", "健康", "中", ["周一胸肌", "周三背部", "周五腿部", "拉伸放松", "饮食记录"]),
        ("B4 读书计划-人月神话", "阅读", "低", ["第1章", "第2章", "第3章", "第4章", "做读书笔记"]),
        ("B5 毕设中期准备", "课程", "高", ["文献综述", "算法实现", "实验对比", "论文初稿", "导师汇报"]),
        ("B6 部门周报整理", "工作", "中", ["收集各模块进度", "汇总数据", "撰写报告", "审核校对"]),
        ("B7 家庭事项", "生活", "低", ["缴水电费", "购置生活用品", "预约体检", "整理证件"]),
        ("B8 Python进阶学习", "开发", "高", ["装饰器与元类", "异步编程", "类型系统", "性能优化", "测试实践"]),
        ("B9 社团活动策划", "社交", "中", ["确定主题", "场地预定", "活动流程", "宣传海报", "物资清单"]),
        ("B10 课程作业汇总", "课程", "高", ["数据结构作业", "操作系统实验", "数据库大作业", "编译原理报告"]),
        ("B11 技术博客撰写", "开发", "低", ["选择主题", "整理资料", "撰写草稿", "配图美化", "发布校对"]),
        ("B12 周末旅行规划", "生活", "中", ["确定目的地", "订酒店", "购买车票", "制定行程", "打包行李"]),
        ("B13 数学建模练习", "学习", "中", ["选题分析", "建立模型", "算法编写", "论文撰写", "结果检验"]),
        ("B14 开源项目贡献", "开发", "中", ["阅读贡献指南", "认领Issue", "本地复现", "提交PR", "回复Review"]),
        ("B15 月度财务整理", "生活", "低", ["收入核对", "支出分类", "储蓄计划", "账单归档"]),
    ]

    themes = themes[:8]
    b_day = 1
    for theme_title, cat, pri, subtasks in themes:
        sampled_subtasks = subtasks[:4]
        b_day = (b_day % 28) + 2
        parent_id = make(_t(
            theme_title,
            category=cat,
            priority=pri,
            due_at=apr(b_day + len(sampled_subtasks)),
            remind_at=apr(b_day),
            tags="父任务",
            estimated_minutes=len(sampled_subtasks) * 60,
        ))
        for j, sub in enumerate(sampled_subtasks):
            sub_day = b_day + j
            make(_t(
                f"{theme_title} / {sub}",
                category=cat,
                priority=pri,
                due_at=apr(sub_day + 1, hour=18),
                remind_at=apr(sub_day, hour=9) if j % 2 == 0 else None,
                tags="子任务",
                estimated_minutes=60,
                parent_id=parent_id,
                progress=100 if j < 2 else (50 if j == 2 else 0),
                completed=(j < 2),
            ))
        b_day += len(subtasks) + 1

    # ────────────────────────────────────────────────────────────────
    #  GROUP C：完成状态边界 (~30 条)
    # ────────────────────────────────────────────────────────────────

    # C1: progress=100，completed=False（进度满但未标记完成，10 条）
    for i in range(1, 11):
        make(_t(
            f"C1-{i} 进度100但未完成",
            progress=100,
            completed=False,
            due_at=apr(i + 5),
            tags="进度满未完成",
            category=CATEGORIES[i % len(CATEGORIES)],
        ))

    # C2: progress=0，completed=True（刚标完成但进度为0，5 条）
    for i in range(1, 6):
        make(_t(
            f"C2-{i} 进度0但已完成",
            progress=0,
            due_at=apr(i),
            tags="进度0已完成",
        ), mark_complete=True)

    # C3: progress=50，completed=True（中间进度直接完成，5 条）
    for i in range(1, 6):
        make(_t(
            f"C3-{i} 进度50已完成",
            progress=50,
            due_at=apr(i + 10),
            tags="进度50已完成",
        ), mark_complete=True)

    # C4: 已完成 + completed_at 均有值（正常完成，10 条）
    for i in range(1, 11):
        make(_t(
            f"C4-{i} 正常完成任务-{i}号",
            category=CATEGORIES[i % len(CATEGORIES)],
            priority=PRIORITIES[i % 3],
            due_at=apr(i),
            progress=100,
            tags="正常完成",
        ), mark_complete=True)

    # ────────────────────────────────────────────────────────────────
    #  GROUP D：时间追踪边界 (~20 条)
    # ────────────────────────────────────────────────────────────────

    # D1: estimated=0，tracked>0（没有预估但有记录，5 条）
    for i in range(1, 6):
        make(_t(
            f"D1-{i} 无预估有追踪-{i*10}min",
            estimated_minutes=0,
            tracked_minutes=i * 10,
            due_at=apr(i + 5),
            tags="无预估有追踪",
        ))

    # D2: tracked > estimated（超时，5 条）
    for i in range(1, 6):
        make(_t(
            f"D2-{i} 超时追踪 {i*30}>{i*20}min",
            estimated_minutes=i * 20,
            tracked_minutes=i * 30,
            due_at=apr(i + 8),
            tags="超时追踪",
            priority="高",
        ))

    # D3: estimated=tracked=0（无时间信息，5 条）
    for i in range(1, 6):
        make(_t(
            f"D3-{i} 零时间信息",
            estimated_minutes=0,
            tracked_minutes=0,
            tags="无时间信息",
        ))

    # D4: 极大 estimated（480 分钟=8小时，5 条）
    for i in range(1, 6):
        make(_t(
            f"D4-{i} 大任务8小时",
            estimated_minutes=480,
            tracked_minutes=i * 40,
            due_at=apr(i + 15),
            tags="大任务",
            priority="高",
        ))

    # ────────────────────────────────────────────────────────────────
    #  GROUP E：过期 / 未来 / 重复规则 / reminder_sent (~30 条)
    # ────────────────────────────────────────────────────────────────

    # E1: 过期未完成（due_at 在 3 月，completed=False，10 条）
    for i in range(1, 11):
        make(_t(
            f"E1-{i} 三月过期未完成",
            due_at=mar(i, hour=18),
            remind_at=mar(i - 1, hour=9) if i > 1 else None,
            tags="过期未完成",
            category=CATEGORIES[i % len(CATEGORIES)],
            priority=PRIORITIES[i % 3],
        ))

    # E2: 未来任务（due_at 在 5/6 月，5 条）
    for i in range(1, 6):
        make(_t(
            f"E2-{i} 五月远期任务",
            due_at=may(i * 3),
            remind_at=may(i * 3 - 2) if i % 2 == 0 else None,
            tags="远期计划",
            estimated_minutes=90,
        ))

    # E3: 每天重复规则（5 条）
    for i in range(1, 6):
        make(_t(
            f"E3-{i} 每日重复任务-{i}号",
            recurrence_rule="每天",
            due_at=apr(i, hour=22),
            remind_at=apr(i, hour=8),
            tags="每日重复",
            category="健康",
        ))

    # E4: 每周重复规则（5 条）
    for i in range(1, 6):
        make(_t(
            f"E4-{i} 每周重复任务",
            recurrence_rule="每周",
            due_at=apr(i + 5, hour=20),
            tags="每周重复",
            category="工作",
        ))

    # E5: reminder_sent=True 且 remind_at 在未来（false lock，5 条）
    for i in range(1, 6):
        make(_t(
            f"E5-{i} 已发提醒但时间未到",
            remind_at=apr(i + 20, hour=9),
            due_at=apr(i + 21),
            tags="提醒锁定测试",
            reminder_sent=True,
        ), reminder_sent=True)

    # ────────────────────────────────────────────────────────────────
    #  GROUP F：深层嵌套 3 级 (~21 条)
    # ────────────────────────────────────────────────────────────────

    # F1: 3 层嵌套（3 个顶层，各 2 个二级，各 2 个三级 = 21 条）
    nest_themes = [
        ("F 毕业设计总体", "课程", "高"),
        ("F 实习准备计划", "工作", "高"),
        ("F 竞赛项目开发", "开发", "中"),
        ("F 个人技术积累", "学习", "中"),
        ("F 社区志愿活动", "社交", "低"),
    ]
    f_day = 2
    for theme_title, cat, pri in nest_themes[:3]:
        f_day = (f_day % 20) + 2
        root_id = make(_t(
            f"{theme_title}（根）",
            category=cat,
            priority=pri,
            due_at=apr(f_day + 10),
            tags="3级嵌套-L1",
            estimated_minutes=600,
        ))
        for m in range(1, 3):
            mid_id = make(_t(
                f"{theme_title}-阶段{m}",
                category=cat,
                priority=pri,
                due_at=apr(f_day + m * 3),
                tags="3级嵌套-L2",
                estimated_minutes=240,
                parent_id=root_id,
                progress=50 if m == 1 else 0,
            ))
            for n in range(1, 3):
                make(_t(
                    f"{theme_title}-阶段{m}-子任务{n}",
                    category=cat,
                    priority=PRIORITIES[(m + n) % 3],
                    due_at=apr(f_day + m * 3 - 1, hour=18),
                    tags="3级嵌套-L3",
                    estimated_minutes=60,
                    parent_id=mid_id,
                    progress=100 if (m == 1 and n == 1) else 0,
                    completed=(m == 1 and n == 1),
                ))
        f_day += 12

    # ────────────────────────────────────────────────────────────────
    #  GROUP G：类别 × 优先级矩阵 (~12 条)
    # ────────────────────────────────────────────────────────────────
    g_day = 5
    for cat in CATEGORIES[:4]:
        for pri in PRIORITIES:
            make(_t(
                f"G 分类矩阵 {cat}-{pri}",
                category=cat,
                priority=pri,
                due_at=apr(g_day % 28 + 1, hour=17),
                tags="矩阵覆盖",
                estimated_minutes=45,
            ))
            g_day += 1

    # ────────────────────────────────────────────────────────────────
    #  GROUP H：标题/描述极端值 (~10 条)
    # ────────────────────────────────────────────────────────────────

    # H1: 超长标题（接近 120 字符上限）
    long_title_base = "超长标题测试任务这是一个用来验证标题字段长度边界的任务标题"
    for i in range(1, 6):
        suffix = f"编号{i:03d}后缀"
        title = (long_title_base + suffix)[:115]
        make(_t(
            title,
            due_at=apr(i + 15),
            description="",
            tags="长标题",
        ))

    # H2: 短描述（5 条）
    for i in range(1, 6):
        make(_t(
            f"H2-{i} 无描述任务",
            description="该任务保留最简描述形式，用于验证详情面板在短文本下的展示与折行。",
            due_at=apr(i + 3),
            tags="无描述",
        ))

    # ────────────────────────────────────────────────────────────────
    #  GROUP I：4 月月末边界 (~5 条)
    # ────────────────────────────────────────────────────────────────
    for i in range(1, 6):
        remind = apr(30, hour=8) if i % 2 == 0 else None
        make(_t(
            f"I-{i} 四月月末截止",
            due_at=apr(30, hour=23 - i),
            remind_at=remind,
            priority=PRIORITIES[i % 3],
            category=CATEGORIES[i % len(CATEGORIES)],
            tags="月末边界",
            estimated_minutes=i * 15,
        ))

    # ────────────────────────────────────────────────────────────────
    #  GROUP J：progress 各值边界 (~10 条)
    # ────────────────────────────────────────────────────────────────
    progress_values = [0, 10, 25, 50, 75, 100]
    for i, pv in enumerate(progress_values):
        make(_t(
            f"J-{i+1} 进度={pv}%",
            progress=pv,
            due_at=apr(i + 2),
            tags="进度边界",
            completed=False,
        ))
    # 额外：progress=100 且已完成（4 条）
    for i in range(1, 5):
        make(_t(
            f"J-完成-{i} 进度100已完成",
            progress=100,
            due_at=apr(i),
            tags="进度边界已完成",
        ), mark_complete=True)

    # ────────────────────────────────────────────────────────────────
    #  GROUP K：多标签组合测试 (~10 条)
    # ────────────────────────────────────────────────────────────────
    tag_combos = [
        "工作 紧急 跟进",
        "学习 Python 算法",
        "生活 健康 运动",
        "社交 朋友 聚会",
        "课程 作业 提交",
        "开发 Bug 修复",
        "阅读 技术 深度",
        "开发 重构 代码质量",
        "工作 会议 周报",
        "生活 购物 家务",
    ]
    for i, tags in enumerate(tag_combos):
        make(_t(
            f"K-{i+1} 多标签-{tags.split()[0]}",
            tags=tags,
            due_at=apr((i % 25) + 1, hour=17),
            category=CATEGORIES[i % len(CATEGORIES)],
            priority=PRIORITIES[i % 3],
            estimated_minutes=40,
        ))

    # ────────────────────────────────────────────────────────────────
    #  GROUP L：父子完成状态不一致 (~10 条)
    # ────────────────────────────────────────────────────────────────
    # L1: 父未完成，子已完成（5组 × 2=10条）
    for i in range(1, 6):
        p_id = make(_t(
            f"L1-{i} 父未完成",
            progress=60,
            due_at=apr(i + 5),
            tags="父未完成子完成",
        ))
        make(_t(
            f"L1-{i} 子已完成",
            parent_id=p_id,
            progress=100,
            tags="父未完成子完成",
        ), mark_complete=True)

    # ────────────────────────────────────────────────────────────────
    #  GROUP M：4月1日 / 4月30日 零时/午夜边界 (~10 条)
    # ────────────────────────────────────────────────────────────────
    for i in range(1, 6):
        # 午夜截止
        make(_t(
            f"M-{i} 首日午夜截止-0时",
            due_at=datetime(2026, 4, 1, 0, i, 0),
            tags="时间边界",
            priority=PRIORITIES[i % 3],
        ))
    for i in range(1, 6):
        # 月末23:59截止
        make(_t(
            f"M2-{i} 月末23:59截止",
            due_at=datetime(2026, 4, 30, 23, 59, i),
            remind_at=datetime(2026, 4, 30, 8, 0, 0) if i % 2 == 0 else None,
            tags="时间边界 月末",
        ))

    # ────────────────────────────────────────────────────────────────
    #  GROUP N：sort_order / 兄弟排序测试 (1个父 + 7个子)
    # ────────────────────────────────────────────────────────────────
    sib_parent = make(_t(
        "N 排序压测父任务",
        due_at=apr(20),
        tags="排序测试",
        priority="低",
    ))
    for i in range(1, 8):
        make(_t(
            f"N-子{i:02d} 兄弟排序测试",
            parent_id=sib_parent,
            due_at=apr(i + 5),
            tags="兄弟排序",
            progress=i * 6,  # 6,12,...,90
        ))

    # ────────────────────────────────────────────────────────────────
    #  统计输出
    # ────────────────────────────────────────────────────────────────
    print(f"已插入 {COUNTER[0]} 条 [April] 任务（任务ID范围内约 {len(created_ids)} 条）。")


if __name__ == "__main__":
    db = DB()
    seed_april(db)
