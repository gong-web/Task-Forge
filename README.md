<div align="center">

<img src="src/assets/header.svg" alt="Task Forge — 本地优先任务管理系统" width="100%">

<br/>

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6.1-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=python&logoColor=white)](https://sqlalchemy.org)
[![SQLite](https://img.shields.io/badge/SQLite-Local--First-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)

[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-0078D4?style=flat-square)](https://github.com)
[![License](https://img.shields.io/badge/License-MIT-F7DF1E?style=flat-square&logo=opensourceinitiative&logoColor=black)](LICENSE)
[![Views](https://img.shields.io/badge/Views-11%20Modes-FF5722?style=flat-square)](src/MainWindow.py)
[![Task Fields](https://img.shields.io/badge/Task%20Fields-19-607D8B?style=flat-square)](src/Task.py)
[![Regression](https://img.shields.io/badge/Tests-15%2B-4CAF50?style=flat-square&logo=pytest&logoColor=white)](tests/)
[![Architecture](https://img.shields.io/badge/Architecture-Local--First%20Monolith-9C27B0?style=flat-square)](src/)

<br/>

**Task Forge** 是一款基于 PyQt6 · SQLAlchemy · SQLite 的本地优先（Local-First）单体桌面任务管理系统。  
数据主权、离线可用、历史可追溯三项特性收敛于一个零部署桌面单体内，  
为个人知识工作者提供完整的任务生命周期管理能力。

</div>

---

## 功能演示

<table>
<tr>
<td width="50%" align="center">

### 今日视图 · 任务树

<img src="docs/demo/01-today-view.svg" alt="今日视图演示" width="100%">

<sub>默认启动视图。<code>forced_visible_ids</code> 确保子任务在受限过滤视图中创建后仍可见。逾期任务红色高亮，今日到期橙色提示。</sub>

</td>
<td width="50%" align="center">

### 任务编辑器 · 上下文注入

<img src="docs/demo/02-create-task.svg" alt="任务编辑器演示" width="100%">

<sub><code>set_context()</code> 三模式注入（独立新建 / 编辑已有 / 创建子任务），<code>_sync_reminder_constraints()</code> 实时校验 $t_{remind} \leq t_{due}$，<code>payload()</code> 统一输出。</sub>

</td>
</tr>
<tr>
<td width="50%" align="center">

### 父子 DAG · 自动归档联动

<img src="docs/demo/03-parent-child-dag.svg" alt="父子联动演示" width="100%">

<sub>全部子节点完成时 <code>_refresh_parent_chain()</code> 自动归档父节点并写入 <code>completed_at</code>；<code>reminder_sent</code> 字段隔离，父节点刷新不干扰已调度的提醒。</sub>

</td>
<td width="50%" align="center">

### 甘特图 · 时间轴进度可视化

<img src="docs/demo/04-gantt-view.svg" alt="甘特图演示" width="100%">

<sub><code>GanttTimeline.paintEvent()</code> 完全自绘。父子任务缩进 18px，百分比进度条实时渲染，数据源 <code>gantt_entries()</code> 与 Task ORM 字段严格一致。</sub>

</td>
</tr>
<tr>
<td width="50%" align="center">

### 看板 · 分析 Hub

<img src="docs/demo/06-kanban-board.svg" alt="看板分析演示" width="100%">

<sub><code>HubView</code> 双标签页：KanbanBoard 四列泳道（待办 / 进行中 / 审核中 / 已完成）+ AdvancedAnalyticsView AI 能力维度分数条与 AI 深度洞察结构化卡片。</sub>

</td>
<td width="50%" align="center">

### 提醒调度 · 防重复弹窗

<img src="docs/demo/08-reminder-dialog.svg" alt="提醒弹窗演示" width="100%">

<sub>Single-shot 定时器 + <code>reminder_sent</code> 防重复互斥锁 + <code>postpone_reminder()</code> 延期补偿，每个提醒只响一次，延期后解锁重新调度。</sub>

</td>
</tr>
<tr>
<td width="50%" align="center">

### 日历 · 月度任务分布

<img src="docs/demo/05-calendar-view.svg" alt="日历视图演示" width="100%">

<sub>月度网格视图，任务密度色块可视化。按月翻页，点击日期格聚焦当日任务列表。</sub>

</td>
<td width="50%" align="center">

### 导入导出 · 数据安全

<img src="docs/demo/10-export-import.svg" alt="导入导出演示" width="100%">

<sub>三格式导出（JSON 全量 / CSV 电子表格 / Markdown 周报），<code>import_data()</code> 含结构校验与 ID 映射恢复。冷启动自动备份 <code>.db → .db.bak</code>。</sub>

</td>
</tr>
<tr>
<td width="50%" align="center">

### 专注计时器 · tracked_minutes

<img src="docs/demo/14-focus-timer.svg" alt="专注计时器演示" width="100%">

<sub>选中任务后启动专注计时，暂停 / 恢复 / 结束后自动累加 <code>tracked_minutes</code>，与分析 Hub 的效率偏差 $T_{actual} - \hat{T}$ 数据直接打通。</sub>

</td>
<td width="50%" align="center">

### 主题切换 · 三套视觉风格

<img src="docs/demo/12-theme-settings.svg" alt="主题切换演示" width="100%">

<sub>深色 / 浅色 / 日出橙三套完整主题，全局 QSS 切换 + <code>StarryDialogShell.set_backdrop_pixmap()</code> 弹窗背景继承，保证所有页面主题一致性。</sub>

</td>
</tr>
</table>

<div align="center">

> [!NOTE]
> README 依赖的演示素材（SVG）统一放置于 `docs/demo/`。本地录制操作步骤见 [`docs/GIF录制操作步骤.md`](docs/GIF录制操作步骤.md)。

</div>

### 截图素材与 README 依赖映射

`docs/demo/` 中已补齐 README 当前使用的全部演示素材，来源于 `screenshot/`：

| README 引用文件 | 来源素材 |
|:---|:---|
| `01-today-view.svg` | `今日任务.png` |
| `02-create-task.svg` | `创建任务.gif` |
| `03-parent-child-dag.svg` | `子任务全部完成父任务自动完成.gif` |
| `04-gantt-view.svg` | `甘特图时间轴.png` |
| `05-calendar-view.svg` | `日历使用.gif` |
| `06-kanban-board.svg` | `工作台任务查阅.gif` |
| `08-reminder-dialog.svg` | `任务提醒.gif` |
| `10-export-import.svg` | `数据持久化展示.gif` |
| `12-theme-settings.svg` | `主题切换.gif` |
| `14-focus-timer.svg` | `专注计时.gif` |

其余补充素材（如 `AI深度分析.gif`、`按日期筛选任务.gif`、`背景图片切换.gif` 等）也已同步到 `docs/demo/`，便于后续继续扩展 README 演示内容。

---

## 快速开始

### 安装与启动

<table style="width:100%;border-collapse:collapse;font-family:serif;background:#fff;border:1px solid #333;">
<tr>
<td style="width:33%;padding:14px 18px;border:1px solid #999;text-align:center;background:#f5f5f5;">
<div style="font-size:11px;color:#999;margin-bottom:6px;">① 安装依赖</div>
<code style="font-size:12px;color:#1a1a1a;">pip install -r requirements.txt</code>
</td>
<td style="width:6%;text-align:center;font-size:20px;color:#333;">→</td>
<td style="width:33%;padding:14px 18px;border:1px solid #999;text-align:center;background:#f5f5f5;">
<div style="font-size:11px;color:#999;margin-bottom:6px;">② 启动应用</div>
<code style="font-size:12px;color:#1a1a1a;">python src/main.py</code>
</td>
<td style="width:6%;text-align:center;font-size:20px;color:#333;">→</td>
<td style="width:33%;padding:14px 18px;border:1px solid #999;text-align:center;background:#f5f5f5;">
<div style="font-size:11px;color:#999;margin-bottom:6px;">③ 运行回归测试</div>
<code style="font-size:12px;color:#1a1a1a;">python tests/editor_regression_suite.py</code>
</td>
</tr>
</table>

### 首次启动自动化流程

首次启动无需手动干预，系统自动完成：

| 步骤 | 函数 | 说明 |
|:---:|:---|:---|
| ① | `_configure_qt_font_directory()` | Qt 字体路径注入 |
| ② | `load_config()` | 加载 `app_config.json` + 日志 |
| ③ | `DB()` | ORM 初始化 + `_ensure_schema()` 自动迁移 |
| ④ | `seed_database_if_empty(db)` | 演示数据植入（幂等） |
| ⑤ | `get_theme_profile()` | 读取主题配置 |
| ⑥ | `apply_theme(...)` | 全局样式装配 |
| ⑦ | `MainWindow().showMaximized()` | 主窗口上屏（默认 today 视图） |
| ⑧ | `app.exec()` | 进入 Qt 事件循环 |

---

## 系统架构总览

### 五区架构

<table style="width:100%;border-collapse:collapse;font-family:serif;background:#fff;border:2px solid #1a1a1a;margin:8px 0;">
<caption style="caption-side:top;text-align:center;padding:8px 0;font-size:13px;font-weight:bold;color:#1a1a1a;letter-spacing:1px;">Task Forge — 五区架构</caption>
<tr>
<td style="width:110px;padding:10px 14px;background:#1a1a1a;color:#fff;font-weight:bold;font-size:12px;text-align:center;border-bottom:1px solid #555;">表现区</td>
<td style="padding:10px 16px;background:#f0f0f0;font-size:11px;color:#1a1a1a;border-bottom:1px solid #ccc;"><code>src/ui/</code> · 25+ UI 模块 · PyQt6 组件树 · 主题装配 · 视觉资产</td>
</tr>
<tr>
<td style="padding:10px 14px;background:#333;color:#fff;font-weight:bold;font-size:12px;text-align:center;border-bottom:1px solid #555;">交互区</td>
<td style="padding:10px 16px;background:#fafafa;font-size:11px;color:#1a1a1a;border-bottom:1px solid #ccc;"><code>MainWindow.py</code> · 事件路由 · <code>switch_view()</code> · <code>refresh_everything()</code> · 提醒调度</td>
</tr>
<tr>
<td style="padding:10px 14px;background:#555;color:#fff;font-weight:bold;font-size:12px;text-align:center;border-bottom:1px solid #888;">领域区</td>
<td style="padding:10px 16px;background:#f5f5f5;font-size:11px;color:#1a1a1a;border-bottom:1px solid #ccc;"><code>task_composer.py</code> · 规则装配 · <code>payload()</code> 验证 · 时间约束联动</td>
</tr>
<tr>
<td style="padding:10px 14px;background:#777;color:#fff;font-weight:bold;font-size:12px;text-align:center;border-bottom:1px solid #aaa;">数据区</td>
<td style="padding:10px 16px;background:#f0f0f0;font-size:11px;color:#1a1a1a;border-bottom:1px solid #ccc;"><code>DB.py</code> · <code>Task.py</code> · <code>Note.py</code> · SQLAlchemy ORM · <code>_ensure_schema</code> · SSOT 唯一写入</td>
</tr>
<tr>
<td style="padding:10px 14px;background:#999;color:#fff;font-weight:bold;font-size:12px;text-align:center;">资源区</td>
<td style="padding:10px 16px;background:#fafafa;font-size:11px;color:#1a1a1a;"><code>src/assets/</code> · 图标 / 主题 / 声效 · 三套配色 · 背景图管理</td>
</tr>
</table>

### 单向数据流

<table style="width:100%;border-collapse:collapse;font-family:serif;background:#fff;border:2px solid #1a1a1a;margin:8px 0;">
<caption style="caption-side:top;text-align:center;padding:8px 0;font-size:13px;font-weight:bold;color:#1a1a1a;">单向数据流 — Task Forge System</caption>
<tr>
<td style="padding:10px 20px;border-bottom:1px solid #ccc;background:#f0f0f0;text-align:center;font-size:11px;color:#1a1a1a;">
<strong>表现区</strong> · PyQt6 · 25+ UI 模块<br>
<code>TodayView | PlanView | TaskTree | HubView | GanttView | Calendar</code>
</td>
</tr>
<tr><td style="text-align:center;padding:4px 0;color:#666;font-size:16px;">↓ UI 事件（点击 / 勾选 / 输入）</td></tr>
<tr>
<td style="padding:10px 20px;border-bottom:1px solid #ccc;background:#fafafa;text-align:center;font-size:11px;color:#1a1a1a;">
<strong>交互区</strong> · MainWindow<br>
<code>switch_view() &nbsp;&nbsp; refresh_everything() &nbsp;&nbsp; check_reminders()</code>
</td>
</tr>
<tr><td style="text-align:center;padding:4px 0;color:#666;font-size:16px;">↓ 领域规则 · 编辑器装配 · 提醒调度</td></tr>
<tr>
<td style="padding:0;border-bottom:1px solid #ccc;background:#fff;">
<table style="width:100%;border-collapse:collapse;">
<tr>
<td style="width:33%;padding:10px 16px;border-right:1px solid #ccc;text-align:center;font-size:11px;color:#1a1a1a;">
<strong>领域区</strong><br><code>规则 · 约束<br>状态验证</code>
</td>
<td style="width:33%;padding:10px 16px;border-right:1px solid #ccc;text-align:center;font-size:11px;color:#1a1a1a;">
<strong>TaskEditorView</strong><br><code>set_context()<br>payload() 装配</code>
</td>
<td style="width:34%;padding:10px 16px;text-align:center;font-size:11px;color:#1a1a1a;">
<strong>提醒调度引擎</strong><br><code>Single-shot Timer<br>reminder_sent 锁</code>
</td>
</tr>
</table>
</td>
</tr>
<tr><td style="text-align:center;padding:4px 0;color:#666;font-size:16px;">↓ DB API Call</td></tr>
<tr>
<td style="padding:10px 20px;border-bottom:1px solid #ccc;background:#f0f0f0;text-align:center;font-size:11px;color:#1a1a1a;">
<strong>数据区</strong> · <code>DB.py</code> (SSOT · SQLAlchemy Session)<br>
<code>create_task | update_task | toggle_task | _refresh_parent_chain | gantt_entries | personal_analytics_snapshot</code>
</td>
</tr>
<tr><td style="text-align:center;padding:4px 0;color:#666;font-size:16px;">↓ → refresh_everything() 广播</td></tr>
<tr>
<td style="padding:10px 20px;background:#fafafa;text-align:center;font-size:11px;color:#1a1a1a;">
<strong>SQLite</strong> · <code>data/task_forge.db</code> + <code>.db.bak</code>（冷启动备份）
</td>
</tr>
</table>

> [!TIP]
> `refresh_everything()` 是**唯一重绘入口**。所有视图均通过此函数获取最新状态，彻底消除「界面先变、写入数据库失败」的 State Drift 竞态问题。

### 核心函数定位点

<table style="width:100%;border-collapse:collapse;font-family:serif;background:#fff;border:2px solid #1a1a1a;margin:8px 0;">
<caption style="caption-side:top;text-align:center;padding:8px 0;font-size:13px;font-weight:bold;color:#1a1a1a;">核心函数调用关系</caption>
<tr>
<td style="width:30%;padding:10px 16px;border:1px solid #ccc;text-align:center;font-size:11px;color:#1a1a1a;background:#f0f0f0;vertical-align:top;">
<div style="font-weight:bold;margin-bottom:4px;">上游触发</div>
<code>switch_view(mode)</code> — 视图路由<br><br>
<code>_refresh_tree()</code> — 任务树重建<br><br>
<code>check_reminders()</code> — 提醒轮询
</td>
<td style="width:40%;padding:14px 20px;border:2px solid #1a1a1a;text-align:center;font-size:12px;color:#1a1a1a;background:#fafafa;vertical-align:middle;">
<div style="font-weight:bold;font-size:14px;margin-bottom:6px;">refresh_everything()</div>
<div style="font-size:10px;color:#666;">MainWindow.py · 唯一重绘入口</div>
</td>
<td style="width:30%;padding:10px 16px;border:1px solid #ccc;text-align:center;font-size:11px;color:#1a1a1a;background:#f0f0f0;vertical-align:top;">
<div style="font-weight:bold;margin-bottom:4px;">下游写入（DB.py）</div>
<code>create_task(payload)</code><br><br>
<code>update_task(id, payload)</code><br><br>
<code>_refresh_parent_chain()</code> — DAG 同步
</td>
</tr>
</table>

---

## 目录结构

```text
Task-Forge/
├─ README.md                         # 项目说明（课程要求）
├─ requirements.txt                  # 依赖列表（课程要求）
├─ src/                              # 源代码（课程要求）
│  ├─ main.py
│  ├─ MainWindow.py
│  ├─ DB.py
│  ├─ Task.py
│  ├─ Note.py
│  ├─ runtime_support.py
│  ├─ assets/
│  └─ ui/
├─ data/                             # 数据文件（课程要求）
│  ├─ app_config.json
│  ├─ categories.json
│  ├─ demo_data.json
│  └─ task_forge.db.bak
├─ docs/                             # AI 使用说明文档（课程要求）
│  ├─ AI使用说明.tex
│  ├─ AI使用说明.pdf
│  ├─ AI使用说明.md
│  ├─ fonts/                         # README/TeX 需要的本地字体
│  │  ├─ NotoSansSC-VF.ttf
│  │  └─ NotoSerifSC-VF.ttf
│  └─ demo/
├─ tests/                            # 回归测试（扩展内容）
├─ scripts/                          # 工具脚本（扩展内容）
└─ screenshot/                       # 演示录屏素材（扩展内容）
```

> [!NOTE]
> 为保证 README 表格和 `docs/AI使用说明.tex` 在不同机器上的中文排版一致性，项目已将所需字体放入 `docs/fonts/`。若本机已安装同名字体，系统会优先使用本机字体。

---

## 数据模型

### Task 实体（19 字段）

> 定义于 [`src/Task.py`](src/Task.py)，SQLAlchemy 2.0 DeclarativeBase 风格，自引用 DAG 外键。

<table>
<tr>
  <th>字段</th><th>SQLAlchemy 类型</th><th>约束</th><th>语义说明</th>
</tr>
<tr><td><code>id</code></td><td><code>Integer</code></td><td>PK · AutoIncrement</td><td>全局唯一标识符</td></tr>
<tr><td><code>title</code></td><td><code>String(120)</code></td><td>NOT NULL</td><td>任务标题</td></tr>
<tr><td><code>category</code></td><td><code>String(60)</code></td><td>default="学习"</td><td>一级分类标签</td></tr>
<tr><td><code>tags</code></td><td><code>Text</code></td><td>default=""</td><td>多标签文本（空格分隔）</td></tr>
<tr><td><code>priority</code></td><td><code>String(10)</code></td><td>枚举：高 / 中 / 低</td><td>任务优先级</td></tr>
<tr><td><code>due_at</code></td><td><code>DateTime</code></td><td>Nullable · Index</td><td>截止时间 $t_{\text{due}}$</td></tr>
<tr><td><code>remind_at</code></td><td><code>DateTime</code></td><td>Nullable</td><td>提醒时间 $t_{\text{remind}}$，约束 $t_{\text{remind}} \leq t_{\text{due}}$</td></tr>
<tr><td><code>progress</code></td><td><code>Integer</code></td><td>default=0</td><td>完成度 $P \in [0, 100]$</td></tr>
<tr><td><code>estimated_minutes</code></td><td><code>Integer</code></td><td>default=0</td><td>预估投入时长 $\hat{T}$</td></tr>
<tr><td><code>tracked_minutes</code></td><td><code>Integer</code></td><td>default=0</td><td>实际累计投入 $T_{\text{actual}}$</td></tr>
<tr><td><code>recurrence_rule</code></td><td><code>String(20)</code></td><td>default="不重复"</td><td>循环规则（每天 / 每周 / 自定义）</td></tr>
<tr><td><code>completed</code></td><td><code>Boolean</code></td><td>default=False</td><td>任务完成态标志</td></tr>
<tr><td><code>completed_at</code></td><td><code>DateTime</code></td><td>Nullable</td><td>完成时间戳，归档时写入</td></tr>
<tr><td><code>reminder_sent</code></td><td><code>Boolean</code></td><td>default=False</td><td>防重复互斥锁，弹窗展示后置 True</td></tr>
<tr><td><code>sort_order</code></td><td><code>Integer</code></td><td>default=0</td><td>同级任务排序权重</td></tr>
<tr><td><code>parent_id</code></td><td><code>Integer</code></td><td>FK(self) · Nullable · CASCADE</td><td>父任务引用，构成 DAG</td></tr>
<tr><td><code>created_at</code></td><td><code>DateTime</code></td><td>default=now</td><td>创建时间戳</td></tr>
<tr><td><code>updated_at</code></td><td><code>DateTime</code></td><td>onupdate=now</td><td>最后修改时间戳</td></tr>
<tr><td><code>description</code></td><td><code>Text</code></td><td>default=""</td><td>任务详情说明</td></tr>
</table>

### 核心字段形式化语义

**父节点进度聚合：**

$$P_{\text{parent}} = \begin{cases} 100 & \forall\, c \in \text{children}(t),\ c.\text{completed} = \texttt{True} \\ \left\lfloor \dfrac{\sum_{c} c.P}{|\text{children}(t)|} \right\rfloor & \text{otherwise} \end{cases}$$

**效率偏差（分析 Hub 核心指标）：**

$$\Delta T = T_{\text{actual}} - \hat{T}$$

**截止与提醒时间约束：**

$$t_{\text{remind}} \leq t_{\text{due}}, \quad \text{由 } \texttt{\_sync\_reminder\_constraints()} \text{ 实时强制执行}$$

### Note 实体（6 字段）

<table style="width:100%;border-collapse:collapse;font-family:serif;background:#fff;border:1px solid #333;">
<tr style="background:#1a1a1a;color:#fff;">
<th style="padding:8px 14px;text-align:left;font-size:11px;border-right:1px solid #555;">字段</th>
<th style="padding:8px 14px;text-align:left;font-size:11px;border-right:1px solid #555;">类型</th>
<th style="padding:8px 14px;text-align:left;font-size:11px;border-right:1px solid #555;">约束</th>
<th style="padding:8px 14px;text-align:left;font-size:11px;">说明</th>
</tr>
<tr style="background:#f5f5f5;">
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>id</code></td>
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>Integer</code></td>
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;">PK</td>
<td style="padding:7px 14px;font-size:11px;">便签唯一 ID</td>
</tr>
<tr>
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>title</code></td>
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>String</code></td>
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;">default="未命名便签"</td>
<td style="padding:7px 14px;font-size:11px;">便签标题</td>
</tr>
<tr style="background:#f5f5f5;">
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>content</code></td>
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>Text</code></td>
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;">Nullable</td>
<td style="padding:7px 14px;font-size:11px;">便签正文</td>
</tr>
<tr>
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>pinned</code></td>
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>Boolean</code></td>
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;">default=False</td>
<td style="padding:7px 14px;font-size:11px;">置顶标志</td>
</tr>
<tr style="background:#f5f5f5;">
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>created_at</code></td>
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>DateTime</code></td>
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;">default=now</td>
<td style="padding:7px 14px;font-size:11px;">创建时间戳</td>
</tr>
<tr>
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>updated_at</code></td>
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>DateTime</code></td>
<td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;">onupdate=now</td>
<td style="padding:7px 14px;font-size:11px;">最后修改时间戳</td>
</tr>
</table>

### 冷启动迁移策略

`DB.py` 内建两种零摩擦迁移机制：

1. **`_ensure_schema()`** — `ALTER TABLE` 追加缺失列（`tags`、`tracked_minutes`、`progress`、`recurrence_rule`），无需手动脚本
2. **`_resolve_db_path()`** — 自动升级历史命名 `task_studio.db → task_forge.db`

---

## 核心机制：父子 DAG 联动

### 内存索引结构

```python
# src/MainWindow.py — 每次 refresh_everything() 后重建
self.task_map:      dict[int, Task]           # O(1) 任务查找
self.children_map:  dict[int, list[Task]]     # 子树枚举与递归计算
```

### DAG 状态转换图

<table style="width:100%;border-collapse:collapse;font-family:serif;background:#fff;border:1px solid #333;margin:8px 0;">
<caption style="caption-side:top;text-align:center;padding:8px 0;font-size:13px;font-weight:bold;color:#1a1a1a;">_refresh_parent_chain — 状态转换</caption>
<tr style="background:#1a1a1a;color:#fff;">
<th style="padding:8px 14px;font-size:11px;border-right:1px solid #555;">状态</th>
<th style="padding:8px 14px;font-size:11px;border-right:1px solid #555;">条件</th>
<th style="padding:8px 14px;font-size:11px;">转换方向</th>
</tr>
<tr style="background:#f5f5f5;">
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;"><strong>未完成</strong></td>
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;"><code>completed=False</code></td>
<td style="padding:8px 14px;font-size:11px;">→ 部分完成（子节点进度 &lt; 100%）</td>
</tr>
<tr>
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;"><strong>部分完成</strong></td>
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;"><code>progress &lt; 100%</code></td>
<td style="padding:8px 14px;font-size:11px;">→ 全部完成（全部子节点 completed=True）</td>
</tr>
<tr style="background:#f5f5f5;">
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;"><strong>全部完成</strong></td>
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;">all children done</td>
<td style="padding:8px 14px;font-size:11px;">→ 父节点归档（<code>completed=True</code>，写入 <code>completed_at</code>）</td>
</tr>
<tr>
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;"><strong>回退</strong></td>
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;">任意子节点取消完成</td>
<td style="padding:8px 14px;font-size:11px;">→ 强制回退 <code>completed=False</code>，向上递归至树根</td>
</tr>
<tr style="background:#f5f5f5;">
<td colspan="3" style="padding:8px 14px;font-size:11px;color:#666;">
<strong>隔离约束：</strong><code>reminder_sent</code> 字段不受父节点刷新影响，保持原有锁状态
</td>
</tr>
</table>

### `_refresh_parent_chain` 三条不变量

位于 [`src/DB.py`](src/DB.py)：

1. **全量完成** → 父节点自动 `completed=True`，写入 `completed_at`
2. **任一子节点未完成** → 父节点强制回退 `completed=False`
3. **向上递归** 直至 `parent_id IS NULL`（树根）为止

### 子任务可见性策略

`forced_visible_ids` 机制解决过滤视图下的可见性断区：

<table style="width:100%;border-collapse:collapse;font-family:serif;background:#fff;border:1px solid #333;margin:8px 0;">
<tr style="background:#1a1a1a;color:#fff;">
<th style="padding:8px 14px;font-size:11px;border-right:1px solid #555;">场景</th>
<th style="padding:8px 14px;font-size:11px;border-right:1px solid #555;">问题</th>
<th style="padding:8px 14px;font-size:11px;">解决方案</th>
</tr>
<tr style="background:#f5f5f5;">
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;">today 视图创建子任务</td>
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;">子任务 <code>due_at=None</code> 被过滤隐藏</td>
<td style="padding:8px 14px;font-size:11px;"><code>forced_visible_ids</code> 强制显示</td>
</tr>
<tr>
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;">plan 视图创建子任务</td>
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;">父任务在不同日期，子任务被过滤</td>
<td style="padding:8px 14px;font-size:11px;">扩展相关分支临时可见</td>
</tr>
<tr style="background:#f5f5f5;">
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;">批量完成后刷新</td>
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;">完成的父任务消失难以确认结果</td>
<td style="padding:8px 14px;font-size:11px;">保留 1 轮渲染周期可见</td>
</tr>
</table>

---

## 核心机制：提醒调度引擎

### 调度时序图

<table style="width:100%;border-collapse:collapse;font-family:serif;background:#fff;border:1px solid #333;margin:8px 0;">
<caption style="caption-side:top;text-align:center;padding:8px 0;font-size:13px;font-weight:bold;color:#1a1a1a;">提醒调度时序</caption>
<tr style="background:#1a1a1a;color:#fff;">
<th style="padding:8px 12px;font-size:11px;text-align:center;border-right:1px solid #555;">提醒定时器<br><code>Single-shot</code></th>
<th style="padding:8px 12px;font-size:11px;text-align:center;border-right:1px solid #555;">MainWindow</th>
<th style="padding:8px 12px;font-size:11px;text-align:center;border-right:1px solid #555;">DB.py</th>
<th style="padding:8px 12px;font-size:11px;text-align:center;border-right:1px solid #555;">声音引擎</th>
<th style="padding:8px 12px;font-size:11px;text-align:center;">提醒弹窗</th>
</tr>
<tr style="background:#f5f5f5;">
<td colspan="5" style="padding:8px 16px;font-size:11px;color:#1a1a1a;">
① <code>timeout()</code> → <code>check_reminders()</code>
</td>
</tr>
<tr>
<td colspan="5" style="padding:8px 16px;font-size:11px;color:#1a1a1a;background:#fafafa;">
② MW → DB: <code>due_reminders(current_time)</code> → 返回待提醒任务列表
</td>
</tr>
<tr style="background:#f5f5f5;">
<td colspan="5" style="padding:8px 16px;font-size:11px;color:#1a1a1a;">
③ [存在待提醒任务] → 声音引擎: <code>_play_reminder_sound()</code> → DB: <code>mark_reminders_sent(task_ids)</code> → 弹窗: <code>_show_reminder_dialog(tasks)</code>
</td>
</tr>
<tr>
<td colspan="5" style="padding:8px 16px;font-size:11px;color:#1a1a1a;background:#fafafa;">
④ [用户选择延期] → DB: <code>postpone_reminder(task_id, minutes)</code>（重置 <code>reminder_sent=False</code>）
</td>
</tr>
<tr style="background:#f5f5f5;">
<td colspan="5" style="padding:8px 16px;font-size:11px;color:#1a1a1a;">
⑤ MW → DB: <code>next_pending_reminder_at()</code> → 定时器: <code>setSingleShot(True); start(delta_ms)</code>
</td>
</tr>
</table>

### `reminder_sent` 状态转换矩阵

<table style="width:100%;border-collapse:collapse;font-family:serif;background:#fff;border:1px solid #333;margin:8px 0;">
<caption style="caption-side:top;text-align:center;padding:8px 0;font-size:13px;font-weight:bold;color:#1a1a1a;">reminder_sent 字段状态转换</caption>
<tr style="background:#1a1a1a;color:#fff;">
<th style="padding:8px 14px;font-size:11px;border-right:1px solid #555;">触发条件</th>
<th style="padding:8px 14px;font-size:11px;border-right:1px solid #555;">变化方向</th>
<th style="padding:8px 14px;font-size:11px;">执行函数</th>
</tr>
<tr style="background:#f5f5f5;">
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;">提醒时间到达，弹窗已展示</td>
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;font-weight:bold;">False → True</td>
<td style="padding:8px 14px;font-size:11px;"><code>mark_reminders_sent()</code></td>
</tr>
<tr>
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;">用户修改 <code>remind_at</code> 字段</td>
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;font-weight:bold;">True → False</td>
<td style="padding:8px 14px;font-size:11px;"><code>update_task()</code> 内部重置</td>
</tr>
<tr style="background:#f5f5f5;">
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;">任务被标记为完成</td>
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;font-weight:bold;">False → True</td>
<td style="padding:8px 14px;font-size:11px;"><code>_set_completion_state()</code></td>
</tr>
<tr>
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;">用户点击「延期」</td>
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;font-weight:bold;">True → False</td>
<td style="padding:8px 14px;font-size:11px;"><code>postpone_reminder()</code></td>
</tr>
<tr style="background:#f5f5f5;">
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;">父节点刷新（<code>_refresh_parent_chain</code>）</td>
<td style="padding:8px 14px;font-size:11px;border-right:1px solid #ccc;color:#666;">无变化（隔离）</td>
<td style="padding:8px 14px;font-size:11px;color:#666;">—</td>
</tr>
</table>

> [!IMPORTANT]
> **架构约束**：严禁绕过 SQLAlchemy Session 直接写 `task_forge.db`。`reminder_sent` 的原子性完全依赖事务——绕过 ORM 将导致提醒重复触发。

---

## 任务编辑器

> 核心类：`TaskEditorView` — [`src/ui/task_composer.py`](src/ui/task_composer.py)

### 三模式上下文注入

```python
# 独立新建任务
set_context(task=None,  preferred_parent_id=None,  parent_title=None)

# 编辑已有任务（回显全部字段）
set_context(task=task,  preferred_parent_id=None,  parent_title=None)

# 创建子任务（fixed_parent_id 锁定，防止提交时解除父子关系）
set_context(task=None,  preferred_parent_id=pid,   parent_title=title)
```

### 提交载荷结构与交互约束

<table style="width:100%;border-collapse:collapse;font-family:serif;background:#fff;border:1px solid #333;margin:8px 0;">
<caption style="caption-side:top;text-align:center;padding:8px 0;font-size:13px;font-weight:bold;color:#1a1a1a;">payload() 输出字段与约束</caption>
<tr>
<td style="width:50%;padding:0;vertical-align:top;border-right:2px solid #1a1a1a;">
<table style="width:100%;border-collapse:collapse;">
<tr style="background:#1a1a1a;color:#fff;">
<th style="padding:8px 14px;font-size:11px;border-right:1px solid #555;">字段</th>
<th style="padding:8px 14px;font-size:11px;">类型</th>
</tr>
<tr style="background:#f5f5f5;"><td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>title</code></td><td style="padding:7px 14px;font-size:11px;"><code>str</code></td></tr>
<tr><td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>priority</code></td><td style="padding:7px 14px;font-size:11px;"><code>"高" | "中" | "低"</code></td></tr>
<tr style="background:#f5f5f5;"><td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>due_at</code></td><td style="padding:7px 14px;font-size:11px;"><code>datetime | None</code></td></tr>
<tr><td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>remind_at</code></td><td style="padding:7px 14px;font-size:11px;"><code>datetime | None</code></td></tr>
<tr style="background:#f5f5f5;"><td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>parent_id</code></td><td style="padding:7px 14px;font-size:11px;"><code>int | None</code></td></tr>
<tr><td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>progress</code></td><td style="padding:7px 14px;font-size:11px;"><code>int [0, 100]</code></td></tr>
<tr style="background:#f5f5f5;"><td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>estimated_minutes</code></td><td style="padding:7px 14px;font-size:11px;"><code>int</code></td></tr>
<tr><td style="padding:7px 14px;font-size:11px;border-right:1px solid #ccc;"><code>tags / category / description</code></td><td style="padding:7px 14px;font-size:11px;"><code>str</code></td></tr>
</table>
</td>
<td style="width:50%;padding:0;vertical-align:top;">
<table style="width:100%;border-collapse:collapse;">
<tr style="background:#1a1a1a;color:#fff;">
<th style="padding:8px 14px;font-size:11px;">实时约束函数</th>
</tr>
<tr style="background:#f5f5f5;"><td style="padding:8px 14px;font-size:11px;"><code>_sync_reminder_constraints()</code><br><span style="color:#666;font-size:10px;">校验 remind_at ≤ due_at，违规自动修正</span></td></tr>
<tr><td style="padding:8px 14px;font-size:11px;"><code>_sync_due_state()</code><br><span style="color:#666;font-size:10px;">截止时间控件启用 / 禁用联动</span></td></tr>
<tr style="background:#f5f5f5;"><td style="padding:8px 14px;font-size:11px;"><code>EditorDateTimeField</code><br><span style="color:#666;font-size:10px;">时 / 分独立滚轮 + 预设时间按钮</span></td></tr>
<tr><td style="padding:8px 14px;font-size:11px;"><code>StarryTagEditor</code><br><span style="color:#666;font-size:10px;">流式标签输入，自动去重</span></td></tr>
</table>
</td>
</tr>
</table>

---

## 多视图体系

### 11 种视图模式

<table style="width:100%;border-collapse:collapse;font-family:serif;background:#fff;border:1px solid #333;margin:8px 0;">
<caption style="caption-side:top;text-align:center;padding:8px 0;font-size:13px;font-weight:bold;color:#1a1a1a;">switch_view(mode) 统一路由 — 11 种视图模式</caption>
<tr>
<td style="width:25%;padding:10px 14px;border:1px solid #ccc;text-align:center;background:#f5f5f5;"><code>today</code><br><span style="font-size:10px;color:#666;">今日聚焦 · 默认启动</span></td>
<td style="width:25%;padding:10px 14px;border:1px solid #ccc;text-align:center;"><code>plan</code><br><span style="font-size:10px;color:#666;">未完成计划树</span></td>
<td style="width:25%;padding:10px 14px;border:1px solid #ccc;text-align:center;background:#f5f5f5;"><code>tasktree</code><br><span style="font-size:10px;color:#666;">全量任务树</span></td>
<td style="width:25%;padding:10px 14px;border:1px solid #ccc;text-align:center;"><code>completed</code><br><span style="font-size:10px;color:#666;">已完成任务归档</span></td>
</tr>
<tr>
<td style="padding:10px 14px;border:1px solid #ccc;text-align:center;background:#f5f5f5;"><code>hub</code><br><span style="font-size:10px;color:#666;">看板 + 分析 Hub</span></td>
<td style="padding:10px 14px;border:1px solid #ccc;text-align:center;"><code>calendar</code><br><span style="font-size:10px;color:#666;">月度任务分布</span></td>
<td style="padding:10px 14px;border:1px solid #ccc;text-align:center;background:#f5f5f5;"><code>gantt</code><br><span style="font-size:10px;color:#666;">时间轴进度图（自绘）</span></td>
<td style="padding:10px 14px;border:1px solid #ccc;text-align:center;"><code>settings</code><br><span style="font-size:10px;color:#666;">设置中心</span></td>
</tr>
<tr>
<td style="padding:10px 14px;border:1px solid #ccc;text-align:center;background:#f0f0f0;"><code>create</code><br><span style="font-size:10px;color:#666;">新建任务编辑器</span></td>
<td style="padding:10px 14px;border:1px solid #ccc;text-align:center;background:#f0f0f0;"><code>edit</code><br><span style="font-size:10px;color:#666;">编辑已有任务</span></td>
<td style="padding:10px 14px;border:1px solid #ccc;text-align:center;background:#f0f0f0;"><code>detail</code><br><span style="font-size:10px;color:#666;">任务详情全屏</span></td>
<td style="padding:10px 14px;border:1px solid #ccc;text-align:center;background:#fafafa;font-size:10px;color:#999;">所有视图均通过 <code>switch_view(mode)</code> 统一路由<br>MainWindow.py</td>
</tr>
</table>

---

## 数据看板与分析

<table>
<tr>
<td width="50%" valign="top">

### DB 聚合接口

| 接口 | 返回描述 |
|:---|:---|
| `dashboard_snapshot()` | 完成率 / 逾期数 / 本周完成 |
| `dashboard_counts()` | 快速计数（完成/未完成/逾期/今日） |
| `weekly_series()` | 近 7 天逐日完成趋势 |
| `gantt_entries()` | 起止区间 / 进度 / 优先级 / 完成态 |
| `personal_analytics_snapshot()` | 效率偏差 · 分类分布 · 热力图数组 |

</td>
<td width="50%" valign="top">

### Hub 视图区次

```text
HubView(QWidget)
└── QTabWidget
    ├── "看板" → KanbanBoard
    │   ├── 待办 | 进行中 | 审核中 | 已完成
    │   └── task_detail_requested = pyqtSignal(int)
    └── "分析" → AdvancedAnalyticsView
        ├── AI 能力维度卡片（7 维度进度条，由 AI ability_profile 驱动）
        └── AI 深度洞察卡片（AICardRenderer 结构化分析文本）
```

<img src="docs/demo/07-analytics-hub.svg" alt="数据分析 Hub 演示" width="100%">

</td>
</tr>
</table>

---

## 导入导出与数据安全

### 导出接口总览

<table style="width:100%;border-collapse:collapse;font-family:serif;background:#fff;border:1px solid #333;margin:8px 0;">
<tr>
<td style="width:33%;padding:12px 18px;border:1px solid #ccc;text-align:center;background:#f5f5f5;vertical-align:top;">
<div style="font-weight:bold;font-size:12px;color:#1a1a1a;margin-bottom:6px;"><code>export_data()</code></div>
<div style="font-size:11px;color:#666;">JSON — 全量任务 + 便签</div>
<div style="font-size:10px;color:#999;margin-top:4px;">含 ID 与父子关系保全</div>
</td>
<td style="width:33%;padding:12px 18px;border:1px solid #ccc;text-align:center;vertical-align:top;">
<div style="font-weight:bold;font-size:12px;color:#1a1a1a;margin-bottom:6px;"><code>export_csv()</code></div>
<div style="font-size:11px;color:#666;">CSV — 电子表格格式</div>
<div style="font-size:10px;color:#999;margin-top:4px;">Excel / Numbers 兼容</div>
</td>
<td style="width:34%;padding:12px 18px;border:1px solid #ccc;text-align:center;background:#f5f5f5;vertical-align:top;">
<div style="font-weight:bold;font-size:12px;color:#1a1a1a;margin-bottom:6px;"><code>export_week_report()</code></div>
<div style="font-size:11px;color:#666;">Markdown — 周报模板</div>
<div style="font-size:10px;color:#999;margin-top:4px;">可直接粘贴提交</div>
</td>
</tr>
</table>

> [!CAUTION]
> `import_data()` 执行覆盖性导入。操作前请先确认 `task_forge.db.bak` 时间戳为最新，或手动执行 `export_data()` 备份当前数据。

---

## 质量保障矩阵

<table>
<tr>
<td width="50%" valign="top">

### 编辑器回归套件

[`tests/editor_regression_suite.py`](tests/editor_regression_suite.py)

| 测试域 | 核心断言 |
|:---|:---|
| 布局可见性 | `set_context()` 后控件可见 |
| 滚动行为 | 长表单滚动后目标控件仍在可视区 |
| 时间约束 | `remind_at > due_at` 时强制修正 |
| 进度回显 | `progress=65` 后 `payload()["progress"]==65` |
| 标签输入 | `StarryTagEditor` 高度规范，重复标签去重 |
| 提醒禁用标签 | 未开启提醒时 `remind_disabled_label` 可见 |
| 子任务预览树 | `parent_title` 注入后预览节点正确展示 |

</td>
<td width="50%" valign="top">

### 主窗口回归套件

[`tests/mainwindow_regression_suite.py`](tests/mainwindow_regression_suite.py)

| 测试域 | 核心断言 |
|:---|:---|
| 树勾选完成联动 | 勾选后 `completed` 持久化 True |
| 完成庆祝动效 | `CelebrationOverlay` 在完成时触发 |
| 单次触发定时器 | `reminder_timer.isSingleShot()==True` |
| 子任务创建可见性 | `forced_visible_ids` 确保创建后可见 |
| 父节点提醒不重置 | 添加子任务不重置父 `reminder_sent` |
| 提醒轮询路径 | 声音→弹窗完整顺序验证 |
| Windows 无 Toast | `_should_show_system_reminder_toast()==False` |
| 甘特图进度同步 | `gantt_entries()` 与 ORM 值一致 |

</td>
</tr>
</table>

---

## AI 协作上下文

### 架构约定（CLAUDE.md 兼容格式）

<table style="width:100%;border-collapse:collapse;font-family:serif;background:#fff;border:1px solid #333;margin:8px 0;">
<caption style="caption-side:top;text-align:center;padding:6px 0;font-weight:bold;font-size:13px;color:#1a1a1a;font-family:serif;">项目协作约定速查</caption>
<tr style="background:#1a1a1a;color:#fff;">
<th style="padding:7px 14px;border:1px solid #555;text-align:left;font-width:34%;">约定项</th>
<th style="padding:7px 14px;border:1px solid #555;text-align:left;width:66%;">说明</th>
</tr>
<tr style="background:#f5f5f5;">
<td style="padding:7px 14px;border:1px solid #ccc;font-weight:bold;">启动指令</td>
<td style="padding:7px 14px;border:1px solid #ccc;"><code>python src/main.py</code></td>
</tr>
<tr>
<td style="padding:7px 14px;border:1px solid #ccc;font-weight:bold;">质量门禁</td>
<td style="padding:7px 14px;border:1px solid #ccc;"><code>python tests/editor_regression_suite.py</code> + <code>mainwindow_regression_suite.py</code></td>
</tr>
<tr style="background:#f5f5f5;">
<td style="padding:7px 14px;border:1px solid #ccc;font-weight:bold;">代码风格</td>
<td style="padding:7px 14px;border:1px solid #ccc;">PEP 8 · snake_case pyqtSignal · 类型注解优先</td>
</tr>
<tr>
<td style="padding:7px 14px;border:1px solid #ccc;font-weight:bold;color:#b00;">架构约束</td>
<td style="padding:7px 14px;border:1px solid #ccc;">禁止 UI 区直接实例化 Session · 所有写操作通过 DB 类接口</td>
</tr>
<tr style="background:#f5f5f5;">
<td style="padding:7px 14px;border:1px solid #ccc;font-weight:bold;">依赖管理</td>
<td style="padding:7px 14px;border:1px solid #ccc;">新增 PyPI 依赖须同步更新 <code>requirements.txt</code> 并版本锁定</td>
</tr>
<tr>
<td colspan="2" style="padding:6px 14px;border:1px solid #ccc;font-size:11px;color:#555;text-align:center;">禁止绕过 ORM 直接写 task_forge.db · DAG 一致性和 reminder_sent 原子性依赖 Session</td>
</tr>
</table>

<details>
<summary><b>验证数据库迁移健壮性</b></summary>
<br>

在缺少 `progress` 列的旧版数据库上运行 `python src/main.py`，
`_ensure_schema()` 会自动执行 `ALTER TABLE tasks ADD COLUMN progress INTEGER DEFAULT 0`，应用正常启动。

</details>

<details>
<summary><b>执行完整回归并解析结果</b></summary>
<br>

```powershell
python tests/editor_regression_suite.py
python tests/mainwindow_regression_suite.py
```

成功判定：输出包含 `editor-regression-suite-passed:N` 与 `mainwindow-regression-suite-passed:M`

</details>

---

## 演进路线图

<table>
<tr>
<td width="33%" valign="top">

**已完成**

- [x] 父子 DAG 递归状态同步
- [x] `reminder_sent` 防重复锁 + 延期补偿
- [x] 编辑器与主窗口双回归套件
- [x] JSON / CSV / Markdown 三格式导出
- [x] 甘特图 / 看板 / 分析 Hub 三视图
- [x] 自动 schema 迁移与历史库兼容
- [x] 三套主题系统（深色/浅色/日出）
- [x] 父子区级缩进甘特图自绘
- [x] 专注计时器 `tracked_minutes`

</td>
<td width="33%" valign="top">

**近期规划**

- [ ] 重复任务规则增强
  - [ ] Cron 表达式解析器
  - [ ] 本地时区校准与规则预览
- [ ] 提醒中心批量处理 UI
- [ ] 回归脚本分组 + HTML 报告输出
- [ ] 循环任务自动续期展示

</td>
<td width="33%" valign="top">

**中长期规划**

- [ ] 插件化扩展点（导入器/统计器）
- [ ] 性能剖析面板（重绘/查询耗时）
- [ ] 基于 $\hat{T}$ 与 $T_{\text{actual}}$ 的效率预测模型
- [ ] 分类级别投入热力图
- [ ] CalDAV 日历协议对接
- [ ] 可选轻量局域网 P2P 同步

</td>
</tr>
</table>

---

## 常见问题

<details>
<summary><b>首次启动为什么会有短暂延迟？</b></summary>
<br>

启动时 `_ensure_schema()` 执行 schema 检查，`seed_database_if_empty()` 在空库情况下植入演示数据。两个操作均为幂等，通常在 1 秒内完成。后续启动仅执行备份操作，速度更快。

</details>

<details>
<summary><b>提醒没有弹出，可能是什么原因？</b></summary>
<br>

1. 检查任务的 `remind_at` 是否正确设置（须早于或等于 `due_at`）
2. 检查 `reminder_sent` 是否已被设置为 `True`（通过重新修改 `remind_at` 来重置）
3. **Windows 平台**：系统通知不会触发（设计行为），提醒通过应用内弹窗展示
4. 确认 `settings` 视图中提醒声音未被禁用

</details>

<details>
<summary><b>父任务完成状态为什么没有自动更新？</b></summary>
<br>

`_refresh_parent_chain` 仅在子任务完成状态通过 `toggle_task()` 或 `batch_toggle_tasks()` 变化时触发。若通过非标准方式（如直接写数据库）完成子任务，父节点不会自动刷新。**请始终通过 `DB` 类接口操作数据。**

</details>

<details>
<summary><b>如何在演示场景下快速重置到初始状态？</b></summary>
<br>

```powershell
# 关闭应用后执行
Remove-Item data/task_forge.db -Force
# 下次启动 seed_database_if_empty() 将自动植入完整演示数据
python src/main.py
```

</details>

---

## 附录

### 附录 A · 主要入口文件速查

| 类别 | 路径 | 说明 |
|:---:|:---|:---|
| 应用启动 | [`src/main.py`](src/main.py) | 8 步启动序列 + 主题装配 |
| 主窗口路由 | [`src/MainWindow.py`](src/MainWindow.py) | 视图切换 + 提醒调度 + 内存索引重建 |
| 数据访问区 | [`src/DB.py`](src/DB.py) | 所有数据操作的 SSOT，唯一写入通道 |
| 任务 ORM | [`src/Task.py`](src/Task.py) | 19 字段 + 自引用 DAG 关系定义 |
| 便签 ORM | [`src/Note.py`](src/Note.py) | 6 字段便签实体 |
| 任务编辑器 | [`src/ui/task_composer.py`](src/ui/task_composer.py) | `TaskEditorView` + `set_context()` + `payload()` |
| 看板与分析 | [`src/ui/hub_view.py`](src/ui/hub_view.py) | `HubView` · `KanbanBoard` · `AdvancedAnalyticsView` |
| 甘特图 | [`src/ui/gantt_view.py`](src/ui/gantt_view.py) | `GanttView` · `GanttTimeline.paintEvent()` |
| 编辑器回归 | [`tests/editor_regression_suite.py`](tests/editor_regression_suite.py) | 7 测试域 |
| 主窗口回归 | [`tests/mainwindow_regression_suite.py`](tests/mainwindow_regression_suite.py) | 8 测试域 |

### 附录 B · 术语表

| 术语 | 含义 |
|:---|:---|
| **Local-First** | 数据优先驻留本地，操作优先本地生效，离线环境完整可用 |
| **SSOT** | Single Source of Truth，单一事实来源（此处为 `DB.py`） |
| **DAG** | Directed Acyclic Graph，有向无环图，保证父子任务引用无循环 |
| **State Drift** | 视图状态与持久化状态不一致的竞态现象 |
| **Debounce Lock** | `reminder_sent` 字段实现的防重复提醒互斥锁 |
| **Payload** | `TaskEditorView.payload()` 装配的任务数据字典，为 DB API 统一入参 |
| **`forced_visible_ids`** | 强制可见集合，防止新建子任务在受限过滤视图中消失 |
| **Single-shot Timer** | `reminder_timer.setSingleShot(True)`，到期后不自动重启，精准调度 |
| $\hat{T}$ | `estimated_minutes`，任务预估投入时长 |
| $T_{\text{actual}}$ | `tracked_minutes`，实际累计专注投入时长 |

---

<div align="center">

**Task Forge — 让每一个任务都有完整的生命周期**

<sub>PyQt6 + SQLAlchemy + SQLite · Local-First · Offline-Complete</sub>

<br/>

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6.1-41CD52?style=flat-square&logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat-square)](https://sqlalchemy.org)
[![MIT License](https://img.shields.io/badge/License-MIT-F7DF1E?style=flat-square)](LICENSE)

</div>


