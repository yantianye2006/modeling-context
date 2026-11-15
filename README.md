# Modeling Context

一个面向数学建模项目的可追溯上下文管理 skill。它帮助你在读取赛题、理解数据、选择模型、运行诊断、回填结果和准备论文交接的过程中，持续维护一套结构化、可验证的建模记录。

## 它解决什么问题

数学建模项目常见的问题不是“不会调用某个模型”，而是：

- 题面、附件和字段含义没有被系统记录；
- 数据口径、单位、时间范围和缺失值处理在项目中途悄悄改变；
- 还没有确认问题结构，就过早冻结模型或开始大规模调参；
- 诊断结果、模型选择和结论之间缺少证据链；
- 上游数据或假设变化后，下游代码、图表和论文结论没有同步失效；
- 代码输出没有登记为可回溯的权威证据。

`modeling-context` 将这些内容组织为一个有阶段、有门禁、有决策历史的建模上下文，适合与 Obsidian、代码仓库和论文写作流程配合使用。

## 核心能力

- 赛题总览、数据理解和统一口径维护
- 问题分析卡与项目设计总览
- 假设、风险、模型候选和淘汰理由记录
- G0、G0.5、G1、G2、G3 阶段门禁
- G0.5 结构诊断、A/B 探针和预登记判据
- 结果、图表、交付物和验证状态登记
- 决策日志与上游变更的下游影响分析
- 向代码、图表和论文阶段交接
- 用脚本初始化、校验、升级预览和生成诊断标准哈希

## 适用场景

它适用于：

1. 开始一个新的数学建模赛题；
2. 恢复一个已有但上下文不完整的建模项目；
3. 在正式建模前判断问题结构和信息是否足够；
4. 记录模型路线、验证方案和结果来源；
5. 当数据规则、假设或目标变化时分析影响；
6. 在代码、图表和论文之间进行可追溯交接。

它不是大规模数值计算框架，也不替代具体模型实现、数据清洗程序或最终论文写作。

## 安装

将本仓库目录复制到 Codex 的 skills 目录，并保留以下结构：

```text
modeling-context/
├── SKILL.md
├── agents/
├── assets/
├── references/
└── scripts/
```

在 Codex 中可使用 `$modeling-context` 触发该 skill。具体安装位置取决于你的 Codex 环境；本机用户级安装目录通常是：

```text
~/.codex/skills/modeling-context/
```

## 基本使用方法

### 1. 初始化项目

准备一个项目目录，例如：

```text
my-contest-project/
├── problem/       # 题面和附件，只读
├── modeling/      # skill 维护的上下文
├── data/          # 工作数据或派生数据
├── code/          # 实现代码
└── outputs/       # 数值产物、图表和报告
```

然后在 Codex 中说明：

```text
使用 modeling-context 初始化这个数学建模项目。请先读取题面和附件，建立赛题总览、数据理解、统一口径和问题分析框架，不要直接选择最终模型。
```

初始化脚本位于：

```text
scripts/init_modeling_context.py
```

### 2. 恢复已有项目

```text
使用 modeling-context 恢复这个项目的建模上下文，先检查当前 stage、status、gate 和未解决事项，再只处理本轮指定的问题。
```

校验脚本：

```bash
python scripts/validate_modeling_context.py --context <project-root>/modeling
```

### 3. 进行结构诊断

当 G0 已通过、需要决定建模路线时：

```text
使用 modeling-context 对问题 2 进行 G0.5 结构诊断。请先登记诊断判据，再设计受限探针，保留条件候选，不要在 G0.5 通过前冻结最终模型。
```

G0.5 判断标准的规范哈希可通过以下脚本生成：

```bash
python scripts/hash_g0_5_criteria.py \
  --context <project-root>/modeling \
  --question 2
```

### 4. 回填代码结果

```text
使用 modeling-context 回填这次实验结果。请登记权威输出、数值来源、验证状态、适用边界，并检查它对问题分析卡和下游交付物的影响。
```

### 5. 分析上游变更

```text
统一口径发生了变化。使用 modeling-context 分析它对假设、模型、验证、图表、代码和论文结论的下游影响，不要覆盖历史决策。
```

## 工作流概览

```text
problem-framing
      │ G0
      ▼
analysis ── G0.5 ──► 路线确定与主模型解锁
      │ G1
      ▼
implementation ── G2 ──► 具体方案、实验或资源输出
      │ G3
      ▼
validation → writing
```

skill 只使用五个 stage：`problem-framing`、`analysis`、`implementation`、`validation`、`writing`。每个 gate 都应有明确的状态、日期和证据；历史决策追加记录，不静默覆盖。

## 目录说明

| 路径 | 用途 |
| --- | --- |
| `SKILL.md` | skill 的入口说明、路由规则和硬边界 |
| `references/` | 工作流、输入路由、诊断、建模护栏和赛事对齐规范 |
| `assets/templates/full/` | 完整项目模板 |
| `assets/templates/minimal/` | 轻量项目模板 |
| `assets/templates/shared/` | 问题章节和通用模板片段 |
| `scripts/init_modeling_context.py` | 初始化建模上下文 |
| `scripts/validate_modeling_context.py` | 校验上下文结构、状态和门禁 |
| `scripts/hash_g0_5_criteria.py` | 生成 G0.5 判断标准哈希 |
| `scripts/preview_modeling_upgrade.py` | 预览旧图表清单迁移或 minimal → full 升级 |

## 设计原则

- 证据优先：不编造字段、数值、公式来源、运行结果或文献。
- 先理解后建模：输入结构、字段语义和问题数量不明确时停止建模。
- 诊断先于冻结：G0.5 通过前只保留条件候选，不冻结主模型。
- 历史可追溯：数据规则、假设、目标、约束、模型和验证改变时追加决策。
- 结果可重算：机器产物是数值权威源，笔记中的数值必须能回溯和重算。
- 探索与交付分离：调试图和探索结果不能直接冒充成稿交付物。

## 开源说明

本仓库主要包含 skill 指令、参考规范、模板和辅助脚本。使用时请根据自己的 Codex 环境调整安装路径；项目中的题面、原始数据、实验结果和个人信息不应提交到本仓库。

## License

待补充。发布前请根据你的预期使用范围选择许可证，例如 MIT、Apache-2.0 或 CC BY 4.0，并在仓库根目录添加对应的 `LICENSE` 文件。
