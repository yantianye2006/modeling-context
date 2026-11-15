---
name: modeling-context
description: 数学建模分析阶段的 Obsidian 上下文工作流。用于读取赛题与附件，初始化或持续维护赛题总览、数据理解、统一口径、赛事对齐与评阅信号、G0.5 结构诊断、假设风险、问题分析卡、模型候选淘汰、决策日志和项目设计总览；适用于开始建模、恢复长项目上下文、用预实验判定建模路线、更新模型决策、回填计算结果、分析上游变更影响，以及向代码、图表和论文阶段交接。
---

# 数学建模上下文管理

围绕可追溯证据维护建模上下文。先识别模式和当前状态，只读取最小充分材料，再更新与本轮任务直接相关的文件。

## 资源导航

- 每轮先读 `references/workflow-rules.md`；它是 stage、status、证据权威、冲突、变更传播和决策记录的唯一规范源。
- 再按下表只读 `references/pipeline.md` 指定步骤；不要默认加载完整流程。
- 读取题面或附件、输入不清或解析失败时，读 `references/input-routing.md`。
- 用户明确要求赛事对齐、评审偏好、得分点或提供了评分规则时，读 `references/contest-alignment.md`；它只投影任务覆盖、交付证据和失分风险，不生成候选模型或创新清单。
- 通过 G0 后选择建模路线、设计 A/B 层诊断探针、预登记判据、判定信息不足或检查 G0.5→G1 解锁时，读 `references/model-diagnostics.md`。
- 选择模型、设计验证、检查具体方案可行域或准备代码交接时，读 `references/modeling-guardrails.md`。
- 完整项目用 `assets/templates/full/`，用户明确要求轻量结构时用 `assets/templates/minimal/`；问题章节由 `assets/templates/shared/question-sections.md` 同源渲染。
- 初始化用 `scripts/init_modeling_context.py`；恢复上下文和阶段交接时运行 `scripts/validate_modeling_context.py --context <project-root>/modeling`。
- 填写 G0.5 判断标准后，用 `scripts/hash_g0_5_criteria.py --context <project-root>/modeling --question <N>` 生成规范哈希，再预登记并启动探针。
- 旧《图表清单》迁移或 minimal → full 升级前运行 `scripts/preview_modeling_upgrade.py`；它只预览，不写文件。
- `references/rule-index.md` 仅供维护 skill，不参与建模任务。

## 模式路由

只读取表中列出的 pipeline 步骤和额外 reference。恢复旧项目时先执行 §1，再按实际任务进入相应模式。

| 模式 | 触发场景 | 只读 pipeline | 额外必读 | 主要动作 |
| --- | --- | --- | --- | --- |
| 初始化 | 新赛题、尚无建模笔记 | §1–5 | `input-routing.md` | 核实输入，创建上下文并建立问题框架 |
| 结构诊断 | G0 已通过、需要确定建模路线 | §1、§6 | `model-diagnostics.md` | 预登记并运行受限探针，通过 G0.5 或保留未决 |
| 分析更新 | 完善某问、调整模型或口径 | §1、§5–10 | `model-diagnostics.md`、`modeling-guardrails.md` | 更新事实、路线、模型、验证、门禁和决策 |
| 结果回填 | 已有代码输出、结果表或图表 | §1、§10–11 | 按产物类型读取模板 | 登记权威证据、结果、验证和失效边界 |
| 影响分析 | 上游数据、假设、目标或模型改变 | §1、§10–11 | `model-diagnostics.md` 与受影响对象 | 回滚失效路线并更新下游问题、代码、产物和结论 |
| 项目收敛 | 各问结果已稳定 | §11–12 | 交付物与图表口径模板 | 通过论文前门禁并准备交接 |

不要因 skill 被触发就重建全部文件。先检查现有状态，只创建缺失文件，只更新本轮相关章节。

## Stage 与 gate 总表

只使用 `problem-framing → analysis → implementation → validation → writing` 五个 stage。进入条件、推进责任和 stage×status 兼容表以 `workflow-rules.md` §2 为准；推进 stage 时同时把文件 status 提到允许值，不能用 `draft` 兜底。

| gate | 作用域 | 通过后允许 | 详细动作 |
| --- | --- | --- | --- |
| GP | 项目 | 初始化上下文 | pipeline §2–3 |
| G0 | 问题 | `problem-framing → analysis` | pipeline §5 |
| G0.5 | 问题 | 在 `analysis` 内确定结构路线并解锁主模型冻结 | pipeline §6 |
| G1 | 问题 | `analysis → implementation` | pipeline §8 |
| G2 | 问题 | 输出具体实验、优化、调度或资源方案；不推进 stage | pipeline §9 |
| G3 | 问题 | `validation → writing` | pipeline §12 |

gate status 只允许 `not-checked | blocked | passed | waived`。`not-checked` 不带日期、阻塞或证据；`blocked` 记录日期与 blocker；`passed` 记录日期与 evidence。只有确无具体方案类交付时 G2 可 `waived`，并记录日期、理由和确认依据；其他 gate 不得豁免。G0.5 的 `route`、`reformulation` 与 `diagnosis_version` 只在 `passed` 时有值，G1 的 `unlocked_by` 必须匹配当前诊断版本。

## 跨阶段硬边界

- 无法确认子问题数量、关键公式、字段语义或附件结构时停止建模并请求解释；不得猜测补全。原始 PDF、Excel 和其他输入只读，临时解析与渲染文件只放 `<project-root>/tmp/`。
- 不编造字段、数值、文献、公式来源、运行结果或证据。机器产物是数值权威源，笔记和交付物中的副本必须可回溯并可重算。
- G0.5 通过前只记录条件候选，不冻结主模型，不通过 G1。A/B 层探针是 `analysis` 阶段的受限诊断执行例外，只写诊断或 pilot 目录，不读取锁定测试指标、不大规模调参、不充当最终交付。
- 探针均贴近平凡基线时先完成 E1–E4 可得信息穷尽审计；四项全为“否”才可判 `information_limited`。不因算法跨问重复而否决，只检查每问的独立证据或共享证据登记。
- 可行域未确认前，不给具体点位、最优条件或可执行方案，也不把模型极值直接写成方案。
- 代码不能替代尚未完成的建模定义。本 skill 维护模型设计与上下文，不承担大规模实现，不写最终论文正文。
- 每次改变数据规则、假设、模型、目标、约束、验证或方案都追加决策并分析下游影响；不覆盖历史决策。
- 交付物统一登记在 `交付物清单.md`。只有 `status: active` 的条目可进入最终交付；旧 `图表清单.md` 仅作兼容输入，未经预览不得改名或合并。
- 图类严格分离探索/调试轨与成稿轨。探索图不限量但不进入交付；成稿图必须对应 `kind: figure` 条目、满足数量预算、通过口径实测并实际渲染回看。
- 深度学习候选保持独立，只在证据充分或用户确认后把有效结论回填问题分析卡，不改写传统模型候选树。
- 冲突、状态推进、证据层级和最小充分上下文一律执行 `workflow-rules.md`；方法和题型防错执行 `modeling-guardrails.md`，不要在就近位置建立规则副本。

## 完成检查

本轮结束前确认：

- 只修改了相关文件与章节；当前状态、未解决项和下一步动作已更新。
- 新结论有证据，假设有验证状态，模型选择或淘汰有理由，上游变化的下游影响已列出。
- G0.5 通过时，适用探针均有完整数值、真实 `outputs/` 产物与 manifest；预登记早于运行开始且判据哈希一致；`information_limited` 已通过 E1–E4 审计。
- G0.5 未通过时没有冻结主模型，G1 未通过；诊断契约或路线失效后已回退 `analysis`、清空旧解锁并标记下游失效项。
- 最终交付物均有状态一致的登记；未登记文件未进入交付，成稿图已回看且没有用机械断言代替视觉检查。
- 每个写入数值都在分析卡「数值来源」中登记，且与权威产物重算结果一致。
- stage、status、updated 和 gate 记录相容；门禁台账已由脚本刷新，跨问题动作已登记到项目设计总览。
- 输入理解门禁已通过；具体方案具备已确认可行域；原始输入未修改，临时文件未混入建模目录。
- 没有静默覆盖用户内容或删除历史决策。
- `validate_modeling_context.py` 已运行且无错误；警告已逐条判断并记录必要处置。
