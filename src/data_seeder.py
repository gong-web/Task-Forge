import logging
from datetime import datetime, timedelta


LOGGER = logging.getLogger("task_forge")


def seed_database_if_empty(db) -> None:  # noqa: ANN001
    """幂等演示数据植入 — 仅在数据库为空时执行。"""
    if db.list_tasks():
        return

    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # ── 时间锚点（相对 "今天" 计算，保证 Gantt / 日历视图始终有内容） ──
    d = lambda days, hour=9, minute=0: today + timedelta(days=days, hours=hour, minutes=minute)  # noqa: E731

    # ═══════════════════════════════════════════════
    #  项目一：Task Forge 课程作业开发
    # ═══════════════════════════════════════════════
    p1 = db.create_task({
        "title": "Task Forge 课程作业",
        "description": "软件工程课程第一次作业：基于 PyQt6 + SQLAlchemy + SQLite 的本地优先个人任务管理系统，需提交源码、README、AI 使用说明及演示材料。",
        "category": "课程",
        "priority": "高",
        "tags": "开发 Python 课程",
        "due_at": d(7, 20),
        "remind_at": d(5, 9),
        "estimated_minutes": 1440,
        "progress": 65,
    })

    # 1-1 需求分析与技术选型 ✓
    c1_1 = db.create_task({
        "title": "需求分析与技术选型",
        "description": "梳理课程作业必须功能清单：GUI、子任务、持久化、提醒、导入导出。确定技术栈：PyQt6 + SQLAlchemy 2.0 + SQLite。",
        "category": "课程",
        "priority": "高",
        "tags": "分析 架构",
        "due_at": d(-8, 18),
        "estimated_minutes": 90,
        "progress": 100,
        "parent_id": p1.id,
    })
    db.update_task(c1_1.id, {"completed": True})

    # 1-2 数据库层与 ORM 设计 ✓
    c1_2 = db.create_task({
        "title": "数据库层与 ORM 设计",
        "description": "设计 Task / Note 实体（19 字段），实现 DB 访问层，支持 _ensure_schema 自动迁移和冷启动自动备份。",
        "category": "开发",
        "priority": "高",
        "tags": "SQLite ORM",
        "due_at": d(-5, 20),
        "estimated_minutes": 180,
        "progress": 100,
        "parent_id": p1.id,
    })
    db.update_task(c1_2.id, {"completed": True})

    # 1-3 核心 UI 框架搭建（进行中 80%）
    c1_3 = db.create_task({
        "title": "核心 UI 框架搭建",
        "description": "主窗口三栏布局、星空主题引擎、侧边导航、任务编辑器组件，以及基础交互路径打通。",
        "category": "开发",
        "priority": "高",
        "tags": "PyQt6 UI",
        "due_at": d(1, 20),
        "remind_at": d(0, 18),
        "estimated_minutes": 360,
        "progress": 80,
        "parent_id": p1.id,
    })

    # 1-3-1 主窗口与导航栏 ✓
    c1_3_1 = db.create_task({
        "title": "主窗口与导航栏",
        "description": "三栏式工作台布局、侧边栏视图切换、无边框窗口与拖拽支持。",
        "category": "开发",
        "priority": "高",
        "tags": "主窗口",
        "due_at": d(-3, 20),
        "estimated_minutes": 120,
        "progress": 100,
        "parent_id": c1_3.id,
    })
    db.update_task(c1_3_1.id, {"completed": True})

    # 1-3-2 任务编辑器组件 ✓
    c1_3_2 = db.create_task({
        "title": "任务编辑器组件",
        "description": "TaskEditorView 三模式注入：独立新建 / 编辑已有 / 创建子任务。payload() 统一输出，实时校验约束。",
        "category": "开发",
        "priority": "高",
        "tags": "编辑器 组件",
        "due_at": d(-2, 20),
        "estimated_minutes": 150,
        "progress": 100,
        "parent_id": c1_3.id,
    })
    db.update_task(c1_3_2.id, {"completed": True})

    # 1-3-3 今日视图与筛选（进行中 50%）
    db.create_task({
        "title": "今日视图与筛选逻辑",
        "description": "TodayView 按日期过滤、forced_visible_ids 机制保证子任务在受限视图下可见，优先级 / 分类多维筛选。",
        "category": "开发",
        "priority": "中",
        "tags": "视图 筛选",
        "due_at": d(0, 22),
        "estimated_minutes": 90,
        "progress": 50,
        "parent_id": c1_3.id,
    })

    # 1-4 多视图模块开发（进行中 40%）
    c1_4 = db.create_task({
        "title": "多视图模块开发",
        "description": "GanttView（自绘时间轴）、CalendarView（月度网格）、KanbanView（拖拽看板）、DashboardView（数据仪表盘）。",
        "category": "开发",
        "priority": "高",
        "tags": "视图 可视化",
        "due_at": d(3, 20),
        "estimated_minutes": 480,
        "progress": 40,
        "parent_id": p1.id,
    })

    # 1-4-1 甘特图自绘渲染 ✓
    c1_4_1 = db.create_task({
        "title": "甘特图自绘渲染",
        "description": "GanttTimeline.paintEvent() 完全 QPainter 自绘，父子层级缩进，进度条实时渲染，横向无限滚动。",
        "category": "开发",
        "priority": "高",
        "tags": "甘特图 QPainter",
        "due_at": d(-1, 20),
        "estimated_minutes": 150,
        "progress": 100,
        "parent_id": c1_4.id,
    })
    db.update_task(c1_4_1.id, {"completed": True})

    # 1-4-2 日历月度视图（进行中 70%）
    db.create_task({
        "title": "日历月度视图",
        "description": "月度任务网格，按月切换，每日任务数量色块标注，点击日期定位任务列表。",
        "category": "开发",
        "priority": "中",
        "tags": "日历 视图",
        "due_at": d(2, 20),
        "estimated_minutes": 120,
        "progress": 70,
        "parent_id": c1_4.id,
    })

    # 1-4-3 看板拖拽视图（未开始）
    db.create_task({
        "title": "看板拖拽视图优化",
        "description": "KanbanBoard 四列泳道（待办 / 进行中 / 审核 / 完成），拖拽更改任务状态，自定义列头样式。",
        "category": "开发",
        "priority": "中",
        "tags": "看板 拖拽",
        "due_at": d(3, 20),
        "estimated_minutes": 120,
        "progress": 0,
        "parent_id": c1_4.id,
    })

    # 1-5 回归测试套件（未开始）
    db.create_task({
        "title": "回归测试套件",
        "description": "编写 editor_regression_suite 与 mainwindow_regression_suite，覆盖编辑器七大约束和主窗口核心路径，pytest 自动化执行。",
        "category": "测试",
        "priority": "中",
        "tags": "pytest 测试",
        "due_at": d(5, 20),
        "estimated_minutes": 180,
        "progress": 0,
        "parent_id": p1.id,
    })

    # 1-6 文档与 README 撰写（进行中 20%）
    db.create_task({
        "title": "文档与 README 撰写",
        "description": "撰写 README（系统架构 / 安装指南 / 功能演示截图），AI 使用说明，演示脚本，并录制功能演示 GIF。",
        "category": "文档",
        "priority": "中",
        "tags": "文档 README",
        "due_at": d(6, 22),
        "estimated_minutes": 240,
        "progress": 20,
        "parent_id": p1.id,
    })

    # ═══════════════════════════════════════════════
    #  项目二：春季读书计划
    # ═══════════════════════════════════════════════
    p2 = db.create_task({
        "title": "春季技术读书计划",
        "description": "4 月重点阅读三本技术经典，每本输出读书笔记并同步到 Obsidian。",
        "category": "学习",
        "priority": "中",
        "tags": "阅读 学习",
        "due_at": d(21, 22),
        "estimated_minutes": 600,
        "progress": 45,
    })

    # 2-1 《人月神话》精读 ✓
    c2_1 = db.create_task({
        "title": "《人月神话》精读与笔记",
        "description": "重点章节：没有银弹、焦油坑、外科手术队。摘录经典论断并结合课程作业实践反思。",
        "category": "学习",
        "priority": "中",
        "tags": "阅读 经典",
        "due_at": d(-4, 21),
        "estimated_minutes": 180,
        "progress": 100,
        "tracked_minutes": 195,
        "parent_id": p2.id,
    })
    db.update_task(c2_1.id, {"completed": True})

    # 2-2 《设计数据密集型应用》第 4 章（进行中 60%）
    db.create_task({
        "title": "DDIA 第 4 章 · 编码与演化",
        "description": "阅读 Thrift / Protocol Buffers / Avro 编码方案，理解前向 / 后向兼容原理，与 Task Forge _ensure_schema 对照理解。",
        "category": "学习",
        "priority": "中",
        "tags": "阅读 DDIA 分布式",
        "due_at": d(7, 21),
        "estimated_minutes": 150,
        "progress": 60,
        "tracked_minutes": 90,
        "parent_id": p2.id,
    })

    # 2-3 《计算机网络：自顶向下》（未开始）
    db.create_task({
        "title": "《计算机网络》第 5-6 章复习",
        "description": "网络层路由算法、链路层 MAC 协议，为考研网络基础部分备考。",
        "category": "学习",
        "priority": "低",
        "tags": "阅读 网络 复习",
        "due_at": d(14, 21),
        "estimated_minutes": 180,
        "progress": 0,
        "parent_id": p2.id,
    })

    # ═══════════════════════════════════════════════
    #  项目三：五月技术分享准备
    # ═══════════════════════════════════════════════
    p3 = db.create_task({
        "title": "五月技术分享：数据库事务与隔离",
        "description": "在组内做一次 40 分钟技术分享，主题：数据库事务隔离级别与 MVCC 实现原理，结合 SQLite WAL 模式展开。",
        "category": "分享",
        "priority": "中",
        "tags": "分享 数据库 事务",
        "due_at": d(22, 16),
        "remind_at": d(20, 9),
        "estimated_minutes": 480,
        "progress": 15,
    })

    # 3-1 选题确认 ✓
    c3_1 = db.create_task({
        "title": "选题确认与范围界定",
        "description": "与导师沟通选题方向，最终锁定：MVCC + 四种隔离级别 + SQLite WAL。",
        "category": "分享",
        "priority": "中",
        "tags": "规划",
        "due_at": d(-2, 18),
        "estimated_minutes": 30,
        "progress": 100,
        "parent_id": p3.id,
    })
    db.update_task(c3_1.id, {"completed": True})

    # 3-2 PPT 制作（进行中 30%）
    db.create_task({
        "title": "技术分享 PPT 制作",
        "description": "slide 结构：背景引入 → 事务四大特性 → 隔离级别演示 → MVCC 原理图 → SQLite WAL 对照 → Q&A。",
        "category": "分享",
        "priority": "中",
        "tags": "PPT 设计",
        "due_at": d(15, 20),
        "estimated_minutes": 240,
        "progress": 30,
        "parent_id": p3.id,
    })

    # 3-3 演讲稿撰写（未开始）
    db.create_task({
        "title": "演讲稿撰写与练习",
        "description": "按 PPT 脉络撰写逐字稿，标注重点停顿与过渡语，录音自我评估至流畅度 ≥ 90%。",
        "category": "分享",
        "priority": "低",
        "tags": "演讲 练习",
        "due_at": d(20, 21),
        "estimated_minutes": 120,
        "progress": 0,
        "parent_id": p3.id,
    })

    # 3-4 彩排与录制（未开始）
    db.create_task({
        "title": "彩排与视频录制",
        "description": "完整彩排两遍，使用 OBS 录制备用版本，导出 MP4 上传内网。",
        "category": "分享",
        "priority": "低",
        "tags": "彩排 录制",
        "due_at": d(21, 20),
        "estimated_minutes": 90,
        "progress": 0,
        "parent_id": p3.id,
    })

    # ═══════════════════════════════════════════════
    #  今日独立任务
    # ═══════════════════════════════════════════════
    db.create_task({
        "title": "撰写本周周报",
        "description": "总结本周进展：Task Forge 核心功能完成 65%，甘特图自绘已上线，日历视图进行中。",
        "category": "工作",
        "priority": "高",
        "tags": "周报输出",
        "due_at": d(0, 18),
        "remind_at": d(0, 14),
        "estimated_minutes": 45,
        "progress": 0,
    })

    db.create_task({
        "title": "回复导师关于课程进度的邮件",
        "description": "汇报 Task Forge 当前进度，说明预计完成节点，附上功能截图。",
        "category": "课程",
        "priority": "高",
        "tags": "邮件 沟通",
        "due_at": d(0, 14),
        "remind_at": d(0, 9, 30),
        "estimated_minutes": 20,
        "progress": 0,
    })

    db.create_task({
        "title": "参加软件工程课程组会",
        "description": "下午 15:30，讨论第二次作业要求，确认演示评分标准。记录要点后更新到任务系统。",
        "category": "课程",
        "priority": "中",
        "tags": "组会 课程",
        "due_at": d(0, 15, 30),
        "estimated_minutes": 60,
        "progress": 0,
        "recurrence_rule": "每周",
    })

    db.create_task({
        "title": "晨跑 5 km",
        "description": "坚持每天有氧运动，配速目标 5:30/km。",
        "category": "健康",
        "priority": "低",
        "tags": "运动健康",
        "due_at": d(0, 7),
        "estimated_minutes": 35,
        "progress": 0,
        "recurrence_rule": "每天",
    })

    # ═══════════════════════════════════════════════
    #  近期计划任务
    # ═══════════════════════════════════════════════
    db.create_task({
        "title": "代码 Review：后端 API 模块",
        "description": "审查同组成员提交的 PR，重点关注接口幂等性、错误码规范、日志格式是否统一。",
        "category": "工作",
        "priority": "中",
        "tags": "代码审查",
        "due_at": d(1, 17),
        "estimated_minutes": 60,
        "progress": 0,
    })

    db.create_task({
        "title": "更新个人简历技术栈描述",
        "description": "加入 PyQt6、SQLAlchemy、本地优先架构等关键词，调整项目经历排序。",
        "category": "个人",
        "priority": "中",
        "tags": "简历 个人",
        "due_at": d(2, 20),
        "estimated_minutes": 40,
        "progress": 0,
    })

    db.create_task({
        "title": "申请数据库集群访问权限",
        "description": "向基础架构组提工单，说明业务需求和数据安全承诺，预计审批 1-2 个工作日。",
        "category": "工作",
        "priority": "高",
        "tags": "权限工单",
        "due_at": d(3, 12),
        "remind_at": d(2, 16),
        "estimated_minutes": 20,
        "progress": 0,
    })

    db.create_task({
        "title": "整理代码注释与 docstring",
        "description": "对 DB.py、task_composer.py 关键方法补充 docstring，删除过时注释，确保 pylance 无类型告警。",
        "category": "开发",
        "priority": "低",
        "tags": "代码质量",
        "due_at": d(4, 20),
        "estimated_minutes": 90,
        "progress": 0,
    })

    db.create_task({
        "title": "购买《Designing Distributed Systems》",
        "description": "O'Reilly 原版，下月精读，重点看分布式锁与领导者选举章节。",
        "category": "个人",
        "priority": "低",
        "tags": "购书阅读",
        "due_at": d(6, 20),
        "estimated_minutes": 15,
        "progress": 0,
    })

    db.create_task({
        "title": "备考：操作系统调度算法复习",
        "description": "复习 FCFS / SJF / 优先级 / 时间片轮转，做 15 道典型习题，标注易错点。",
        "category": "学习",
        "priority": "中",
        "tags": "复习 操作系统",
        "due_at": d(8, 21),
        "estimated_minutes": 120,
        "progress": 0,
    })

    # ═══════════════════════════════════════════════
    #  逾期未完成任务（演示逾期高亮效果）
    # ═══════════════════════════════════════════════
    db.create_task({
        "title": "提交上周组会纪要",
        "description": "上周五的组会记录还未整理成正式纪要，需补发到协作群，已逾期。",
        "category": "工作",
        "priority": "高",
        "tags": "逾期紧急",
        "due_at": d(-3, 17),
        "estimated_minutes": 30,
        "progress": 0,
    })

    db.create_task({
        "title": "修复支付模块空指针异常",
        "description": "生产环境偶发 NullPointerException，stacktrace 指向订单确认回调，需定位根因并热修复。",
        "category": "工作",
        "priority": "高",
        "tags": "BUG 生产",
        "due_at": d(-2, 12),
        "estimated_minutes": 90,
        "progress": 20,
    })

    db.create_task({
        "title": "更新依赖版本并跑完整测试",
        "description": "numpy / pandas 有安全漏洞修复版本，需升级依赖并确保 CI 全绿。",
        "category": "工作",
        "priority": "中",
        "tags": "依赖 安全",
        "due_at": d(-1, 18),
        "estimated_minutes": 60,
        "progress": 0,
    })

    # ═══════════════════════════════════════════════
    #  近期已完成历史任务（演示完成视图 / 热力图）
    # ═══════════════════════════════════════════════
    histories = [
        {"title": "修复登录页面偶发崩溃", "category": "工作", "priority": "高", "tags": "BUG 修复",
         "due": d(-1, 18), "done": d(-1, 15), "mins": 90, "desc": "排查出 JWT 过期后未清除 localStorage 导致的循环跳转，已修复并回归。"},
        {"title": "团队代码评审（第 12 周）", "category": "工作", "priority": "中", "tags": "代码审查",
         "due": d(-2, 17), "done": d(-2, 16, 30), "mins": 50, "desc": "审查 5 个 PR，提出 12 条改进意见，其中 3 条被合并。"},
        {"title": "阅读《重构》第 6 章笔记", "category": "学习", "priority": "中", "tags": "阅读 重构",
         "due": d(-3, 21), "done": d(-3, 20), "mins": 80, "desc": "重点整理了提炼函数、内联函数、以查询取代临时变量三个手法。"},
        {"title": "办理医疗报销手续", "category": "个人", "priority": "低", "tags": "行政 个人",
         "due": d(-4, 17), "done": d(-4, 14), "mins": 30, "desc": "携带发票和病历去财务，审批通过，预计 5 个工作日到账。"},
        {"title": "更新个人主页作品集", "category": "个人", "priority": "中", "tags": "个人 网站",
         "due": d(-5, 22), "done": d(-5, 19), "mins": 60, "desc": "新增 Task Forge 项目卡片，附 Demo GIF 和 GitHub 链接。"},
        {"title": "环境搭建与依赖锁定", "category": "开发", "priority": "中", "tags": "环境 配置",
         "due": d(-6, 20), "done": d(-6, 17), "mins": 45, "desc": "创建 venv，锁定 requirements.txt，验证 PyQt6 在 Windows / macOS 下启动正常。"},
        {"title": "看完 Clean Architecture 精华章节", "category": "学习", "priority": "低", "tags": "阅读 架构",
         "due": d(-7, 21), "done": d(-7, 20, 30), "mins": 100, "desc": "重点阅读依赖倒置原则与边界划分实践，结合 Task Forge 分层架构做对照。"},
    ]
    for h in histories:
        t = db.create_task({
            "title": h["title"],
            "description": h["desc"],
            "category": h["category"],
            "priority": h["priority"],
            "tags": h["tags"],
            "due_at": h["due"],
            "estimated_minutes": h["mins"],
            "tracked_minutes": int(h["mins"] * 0.9),
            "progress": 100,
        })
        db.update_task(t.id, {"completed": True})

    # ═══════════════════════════════════════════════
    #  便签（Notes）
    # ═══════════════════════════════════════════════
    db.create_note(
        "📍 演示流程提示",
        "推荐演示顺序：\n① 今日视图（展示今日到期/逾期高亮）\n② 新建任务 + 设置子任务\n③ 甘特图（展示父子层级缩进）\n④ 日历视图（月度分布）\n⑤ 看板视图（泳道拖拽）\n⑥ 数据分析 Hub（雷达图 + 热力图）\n⑦ 提醒弹窗（修改提醒时间触发）\n⑧ 导出功能（JSON / CSV / Markdown）",
        pinned=True,
    )
    db.create_note(
        "🎯 本周重点",
        "Task Forge 截止 4 月 15 日，优先级：\n1. 完成今日视图筛选逻辑（剩 50%）\n2. 补全看板视图拖拽（未开始）\n3. 回归测试套件（未开始）\n4. README + AI 说明文档",
        pinned=True,
    )
    db.create_note(
        "🔧 技术备忘录",
        "SQLAlchemy Session 不跨线程使用！\n\n甘特图 paintEvent 全量用 QPainter 自绘，\n不要用 QGraphicsItem——后者在高 DPI 屏幕\n坐标变换有问题。\n\n提醒引擎用 QTimer.singleShot，\n不要用 QThread，避免 GIL 竞争。",
        pinned=False,
    )
    db.create_note(
        "📖 书摘：人月神话",
        "\"往一个已落后的软件项目中增加人手，只会使进度更加落后。\"\n\n— Frederick P. Brooks Jr.\n\nBrooks 定律的本质：沟通路径 = n(n-1)/2，\n新人熟悉成本 > 其产出，至少在短期内如此。",
        pinned=False,
    )

    LOGGER.info("演示数据已植入：%d 项任务 + 4 条便签", len(db.list_tasks()))
