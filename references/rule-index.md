# 规则索引（维护用，非执行文件）

本文件不参与任何一轮建模工作，执行时不需要读取。它只服务于一件事：**每条规则有且只有一个规范源（normative home），其他位置只能引用，不能重述。**

新增或修改规则前先查本表。若要写的规则已有 home，就改 home，不要在最近的位置补一句——skill 内部的规则副本与交付物中的数值副本是同一种失败，只是不会报错。

`scripts/validate_modeling_context.py` 是这些规范的可执行检查，不是新的 normative home。检查器与本表登记的 home 冲突时，以 home 为准并修复检查器，不得反过来用脚本行为改写规则。

## home 的划分标准

| 规则性质 | home |
| --- | --- |
| 跨阶段纪律：状态枚举、证据层级、冲突、变更传播、决策记录方式 | `references/workflow-rules.md` |
| 每轮必读的模式路由、stage/gate 总表、跨阶段硬边界与完成检查 | `SKILL.md` |
| 流程步骤、阶段推进和各门禁的执行条款 | `references/pipeline.md` |
| G0.5 的结构假设、诊断探针、路线、预登记、manifest 与证据复用 | `references/model-diagnostics.md` |
| 方法细则、题型防错、模型表达要求、方案可行域清单 | `references/modeling-guardrails.md` |
| 题面与附件的读取、停止与提问规则 | `references/input-routing.md` |
| 赛事对齐的来源层级、投影边界与历史评阅信号 | `references/contest-alignment.md` |
| 字段结构、逐项口径取值 | `assets/templates/` |

判定顺序：**先看它是否在每一种模式下都必须成立**——是则进 `SKILL.md` 或 `workflow-rules.md`（两份每轮必读）；属于某一步的执行动作则进 `pipeline.md`，由 SKILL 模式表按步骤条件加载；题型、输入或方法细节进对应 reference。

## 规则登记表

### 跨阶段纪律 → `references/workflow-rules.md`

| 规则 | home | 允许的引用位置 |
| --- | --- | --- |
| `stage` 五值枚举与进入条件 | §2 | `SKILL.md`「Stage 与 gate 总表」指针；`pipeline.md` §5/8/11/12 推进动作；各模板 frontmatter（只取值，不解释） |
| `status` 四值枚举 | §2 | 同上 |
| 手写状态字段的前导状态词判定（允许附加括注） | §2 | 各模板直接书写；`validate_modeling_context.py` 的 `leading_status()` 是唯一实现，新增状态字段一律走它 |
| `stage`×`status` 兼容表（含"离开 problem-framing 后不再有 draft"） | §2 | `SKILL.md`「Stage 与 gate 总表」指针；`pipeline.md` §11 的推进句；`validate_modeling_context.py` 的 `E_STAGE_STATUS` 实现 |
| 假设 / 模型 / 决策的状态词表 | §2 | `03_假设与风险.md`、`模型候选与淘汰.md`、分析卡 §13（只取值） |
| 证据权威与数值副本 | §2「证据权威与数值副本」 | `pipeline.md` §11 指针；`问题N_分析卡.md` §14 指针；共享问题章节；`SKILL.md`「完成检查」一条 |
| 最小充分上下文 | §3 | `SKILL.md`「资源导航」；`input-routing.md`（补读顺序，互补不重复） |
| 冲突处理优先级 | §4 | `pipeline.md` §1「不静默合并」一句 |
| 变更传播与影响分析 | §5 | `pipeline.md` §10 第 3 项 |
| 决策来源、`proposed`/`active`、追加式记录 | §6 | `pipeline.md` §10 指针；`full/决策日志.md` 与 `minimal/03_决策日志.md` 顶部各一行指针 + 条目结构 |
| Obsidian 链接与 callout 约定 | §7 | 各模板的实际用法 |

### 模式路由与硬边界 → `SKILL.md`

| 规则 | home | 允许的引用位置 |
| --- | --- | --- |
| 模式判定、最小上下文和 pipeline 步骤路由 | 「模式路由」 | `pipeline.md` 只声明服从该路由，不复制模式表 |
| stage 五值与 GP/G0/G0.5/G1–G3 作用概览、gate status 通用语义 | 「Stage 与 gate 总表」 | `pipeline.md` 在对应步骤执行推进动作；模板只承载字段结构 |
| 输入、证据、方案、历史、交付物、图表两轨和职责范围的每轮硬边界 | 「跨阶段硬边界」 | pipeline 各步骤可引用，不得改写 |
| 每轮最低完成条件 | 「完成检查」 | —— |

### 执行流程与门禁动作 → `references/pipeline.md`

| 规则 | home | 允许的引用位置 |
| --- | --- | --- |
| 证据盘点、输入理解、初始化和问题框架 | §1–4 | `SKILL.md` 模式表只列步骤编号；`input-routing.md` 补充输入细则 |
| 输出位置（已有 vault 用实际位置）、上下文库文件构成与问题数量判定 | §3 | `init_modeling_context.py` 生成对应文件；`validate_modeling_context.py` 的 `E_REQUIRED_FILE` 执行检查 |
| M1/M2/M3 定义、全项目优先级纪律与预算例外 | §4、§9 | 共享分析卡 §17 承载工作项；决策日志承载例外；项目总览只显示脚本派生摘要 |
| 数据口径、G0.5 执行、模型设计和 G1 推进动作 | §5–8 | `model-diagnostics.md` 与 `modeling-guardrails.md` 补充结构诊断、模型表达和实现接口 |
| 具体方案可行域与 G2 动作 | §9 | `SKILL.md` 保留“可行域未确认不得给方案”的每轮硬边界 |
| 决策、交接、影响分析和结果闭环 | §10–11 | `workflow-rules.md` 定义决策与证据纪律；模板承载字段 |
| 负结果的四类闭环处置及 G3 阻断条件 | §11 | `模型候选与淘汰.md` 承载历史记录；共享分析卡 §14 承载当前闭环字段；§12 执行 G3 检查 |
| 论文前门禁七条与 G3 动作 | §12 | `SKILL.md` 完成检查只保留跨模式最低检查，不复制七条 |

### G0.5 结构诊断 → `references/model-diagnostics.md`

| 规则 | home | 允许的引用位置 |
| --- | --- | --- |
| L1–L5、G0/G0.5/G1 职责边界 | §1 | `SKILL.md` 保留每轮硬边界；`pipeline.md` §6/8 执行动作 |
| 公共骨架、预测类 H0–H5 与探针角色 | §2 | 分析卡 §6.5 承载字段，不复制解释 |
| A/B 两层与 analysis 阶段受限诊断执行例外 | §3 | `pipeline.md` §6 执行；SKILL 保留禁止项 |
| route/reformulation、R4 的 E1–E4 前置审计 | §4–5 | 分析卡 §6.5 承载结论；校验器执行 C1 |
| gate 字段、探针状态、criteria_hash 与 manifest 契约 | §6 | frontmatter、分析卡与决策日志承载字段；初始化和校验脚本执行 C2–C4 |
| 跨问题证据复用 | §7 | 分析卡结果表与模型候选表承载说明；校验器报精确重复、提示同路线复核 |
| G0.5 失效与回滚 | §8 | `workflow-rules.md` §5 是跨阶段传播 home；`pipeline.md` §11 触发执行 |

### 方法细则 → `references/modeling-guardrails.md`

| 规则 | home | 允许的引用位置 |
| --- | --- | --- |
| 模型表达七项（含评价、验证划分、敏感性、失效边界） | 「模型表达」 | `pipeline.md` §7 指针；`问题N_分析卡.md` §11 指针 |
| G0 目标可估性、数据支撑、决策分辨率与分级处置 | 「目标可估性与数据支撑审计」 | `pipeline.md` §5 执行并推进 G0；共享分析卡 §6 承载审计字段 |
| 参数来源、决策敏感性、断点/边界/角点自检及 G3 阻断条件 | 「参数来源与决策敏感性」 | `pipeline.md` §7、§12；共享分析卡 §11.1 承载登记字段 |
| 题型防错（优化 / 评价 / 预测 / 动力学 / 图论） | 「题型防错」 | —— |
| 主模型与辅助模型的职责与结论冲突处理 | 「主模型与辅助模型」 | `pipeline.md` §7 一句 |
| 向实现阶段交付的接口表 | 「实现交接」 | `问题N_分析卡.md` §16 字段结构 |
| 具体实验与方案门禁的可行域清单 | 「具体实验与方案门禁」 | `pipeline.md` §9 指针；`SKILL.md` 保留每轮禁止项；`input-routing.md` §4 指针 |

### 赛事对齐 → `references/contest-alignment.md`

| 规则 | home | 允许的引用位置 |
| --- | --- | --- |
| S1–S4 来源层级、低层级不覆盖高层级 | 「权威层级」 | `pipeline.md` §4 执行；分析卡 §1.3 承载字段 |
| 赛事投影只检查覆盖、交付证据与失分风险 | 「对齐投影」 | `SKILL.md` 资源导航；`pipeline.md` §4 |
| 历史信号不生成模型、创新或完整报告 | 「禁止扩张」 | `SKILL.md` 资源导航；分析卡 §1.3 提示 |

### 交付物口径与字段 → `assets/templates/`

| 规则 | home | 允许的引用位置 |
| --- | --- | --- |
| 图表口径 A 硬断言 / B 验收目标 / C 强制观察的三分、判据与失效机制 | `full/02_统一口径.md` §图表口径 | `pipeline.md` §11、§12 第 4/7 条；`SKILL.md` 图表硬边界；`交付物清单.md` 的 `figure` 专属字段 |
| 交付物核心字段、kind 专属字段、生命周期与 `supersedes` 吸收关系 | `full/交付物清单.md` | `pipeline.md` §4/11/12；minimal 在问题分析卡内嵌同一结构 |
| 交付物骨架、要求—证据追踪与赛事对齐表的字段结构 | `shared/question-sections.md` 的 `requirements` 稳定章节 | `pipeline.md` §4 执行填写、§12 第 1 条检查；`full/交付物清单.md` 与 minimal 交付物区只保留回指关系；`validate_modeling_context.py` 的 `E_DELIVERY_SKELETON` / `E_REQUIREMENT_TRACE` 执行一致性检查 |
| 分析卡章节 ID、顺序、full/minimal 投影 | `shared/question-sections.md` | `full/问题N_分析卡.md` 与 `minimal/02_问题分析卡.md` 只承载包装结构；初始化脚本负责渲染 |
| GP/G0/G0.5/G1–G3 frontmatter 字段结构与 minimal 的逐问题嵌套结构 | `full/00_赛题总览.md`、`full/问题N_分析卡.md`、对应 minimal 模板 | `init_modeling_context.py` 负责渲染；`validate_modeling_context.py` 负责执行检查 |
| 派生门禁台账的显示区域 | `full/项目设计总览.md` | `validate_modeling_context.py --write-summary` 只更新标记区域，不形成第二份权威状态 |
| 跨问题未完成动作的登记位置 | `full/项目设计总览.md` | `pipeline.md` §11 |
| M1/M2/M3 工作项字段结构 | `shared/question-sections.md` 的 `next-actions` 稳定章节 | `pipeline.md` §4/10 定义动作；项目总览的预算状态由校验器派生 |

## 已登记的允许副本

以下副本是有意保留的，不算漂移；但**改动 home 时必须同步改它们**：

| 副本位置 | 复制了什么 | 为什么允许 |
| --- | --- | --- |
| `minimal/01_数据与口径.md` | 图表口径 A/B/C 三分 | minimal 模式没有 `02_统一口径.md`，该节即 minimal 的 home；两套模板不会在同一项目中共存 |
| `minimal/02_问题分析卡.md` | 通用交付物条目字段与生命周期 | 完整语义以 `full/交付物清单.md` 为 home；minimal 只保留可填写结构 |
| `shared/question-sections.md` | full/minimal 分析卡的稳定章节 ID、正文与投影方式 | Python 只解析、选择和渲染，不承载章节正文 |
| `03_假设与风险.md`、`模型候选与淘汰.md`、`决策日志.md` 中的状态取值列表 | `workflow-rules.md` §2 的三张状态词表 | 取值列表属于字段结构，模板需要它才能填；三处都已标注"以 `workflow-rules.md` §2 为准"，只允许复制取值，不允许新增状态或改写含义 |

以上允许副本均不包含问题章节正文；full/minimal 已通过共享章节源消除 Python 与模板之间的正文副本。

## 已知的枚举分层

`status` 存在两个层级，互不覆盖，不得互相套用：

- **文件级**（frontmatter）：`draft | active | validated | superseded`，定义在 `workflow-rules.md` §2；
- **交付物条目级**（`交付物清单.md` 的条目）：`planned | drafted | active | superseded`，定义在 `交付物清单.md`。

条目级的 `planned` / `drafted` 描述的是单个交付物的成熟度，不是文件的流程阶段；条目升 `active` 也不改变所在文件的 `status`。
