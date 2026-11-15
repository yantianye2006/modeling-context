<!-- modeling-start:group {"id":"scope","title":"输入、输出与上下游关系"} -->
<!-- modeling-start:group {"id":"evidence","title":"事实、假设与风险"} -->
<!-- modeling-start:group {"id":"model","title":"模型与数学表达"} -->
<!-- modeling-start:group {"id":"validation","title":"约束、验证与敏感性分析"} -->
<!-- modeling-start:group {"id":"decision","title":"当前决策与未决事项"} -->
<!-- modeling-start:group {"id":"results","title":"当前结果与证据"} -->
<!-- modeling-start:group {"id":"execution","title":"实现接口与下一步动作"} -->

<!-- modeling-start:section {"id":"requirements","full_title":"1. 题目要求与交付","minimal_group":"scope","minimal_title":"题目要求与交付","minimal":"include"} -->
用自己的语言描述最终必须交付的结论，不照抄题面；先定义答案的可使用形态，再选择模型。

### 1.1 交付物骨架

<!-- modeling-start:delivery-skeleton:v1:start -->

数值可以留空，但字段、单位、行列或对象粒度、使用方式必须在模型选择前明确。除「结论」外，每行的对应交付物 ID 必须与 `交付物清单.md` 中的条目 ID 一致；G0 通过时校验器逐行核对。

| 交付对象 | 形态 | 字段/结构 | 单位 | 粒度 | 使用方式 | 对应交付物 ID |
| --- | --- | --- | --- | --- | --- | --- |
|  | 图 / 表 / 规则 / 阈值 / 排程 / 方案 / 结论 |  |  |  |  |  |

<!-- modeling-start:delivery-skeleton:v1:end -->

### 1.2 要求—证据追踪

<!-- modeling-start:requirement-trace:v1:start -->

| 题面要求或动词 | 类型 | 对应交付物或必做分析 | 证据位置 | 状态 |
| --- | --- | --- | --- | --- |
|  | 给出 / 分析 / 比较 / 评价 / 优化 |  |  | planned |

状态沿用交付物条目级枚举 `planned / drafted / active`（定义见 `交付物清单.md`）；对应「必做分析」而非交付物的行，在分析完成并有证据后同样记 `active`。G3 通过时不得再有 `planned` 行——要么已经交付，要么在负结果闭环中登记为不交付的理由。

<!-- modeling-start:requirement-trace:v1:end -->

“分析某因素的影响”也要登记为必做分析；要求“给出”分组、规则或方案时，既登记定义，也登记可直接使用的结果。

### 1.3 赛事对齐与已知评阅信号（可选）

用户明确要求赛事对齐或提供评分材料时，按 `references/contest-alignment.md` 填写。只登记能映射到本题要求、交付证据或失分风险的信号；不得用历史偏好覆盖本题题面，不在本节生成模型或创新清单。

| 对齐项 | 来源层级 | 年份与出处 | 对应题目要求 | 需要的交付/证据 | 潜在失分风险 | 处理方式 |
| --- | --- | --- | --- | --- | --- | --- |
|  | S1 / S2 / S3 / S4 |  |  |  |  | 纳入交付 / 纳入必做分析 / 提醒 / 不适用 / 待核实 |
<!-- modeling-start:endsection -->

<!-- modeling-start:section {"id":"inputs","full_title":"2. 已知输入","minimal_group":"scope","minimal_title":"已知输入","minimal":"include"} -->
- 数据文件：
- 上游问题结论：
- 已知参数：
- 单位与可用范围：
<!-- modeling-start:endsection -->

<!-- modeling-start:section {"id":"outputs","full_title":"3. 需要输出","minimal_group":"scope","minimal_title":"需要输出","minimal":"include"} -->
- 数值结果：
- 模型结果：
- 结果表/图表：
- 对后续问题的输出：
<!-- modeling-start:endsection -->

<!-- modeling-start:section {"id":"dependencies","full_title":"4. 与其他问题的关系","minimal_group":"scope","minimal_title":"与其他问题的关系","minimal":"include"} -->
- 依赖：
- 向后传递：
- 仅提供解释、不直接进入计算的内容：
<!-- modeling-start:endsection -->

<!-- modeling-start:section {"id":"difficulty","full_title":"5. 核心困难","minimal_group":"scope","minimal_title":"核心困难","minimal":"anchor"} -->
<!-- modeling-start:endsection -->

<!-- modeling-start:section {"id":"facts","full_title":"6. 事实","minimal_group":"evidence","minimal_title":"事实","minimal":"include"} -->
> [!fact]
>

### G0 目标可估性与数据支撑审计

<!-- modeling-start:g0-audit:v1:start -->

| 项目 | 内容 |
| --- | --- |
| 目标量 | 待检查 |
| 观测机制 | 待检查 |
| 信息坍缩链 | 待检查 |
| 相关结构 | 待检查 |
| 基线难度 | 待检查 |
| 输出分辨率 | 待检查 |
| 判定 | 待检查 |
| 处置 | 待检查 |
| 证据 | 待检查 |

观测机制可写直接观测、删失、截断、代理变量或派生量；信息坍缩链按“数据行数 → 独立个体/单元数 → 有效事件、区间、少数类或对比数”填写；相关结构无则明确写“无”。

<!-- modeling-start:g0-audit:v1:end -->
<!-- modeling-start:endsection -->

<!-- modeling-start:section {"id":"structure-diagnosis","full_title":"6.5. G0.5 结构诊断与建模路线","minimal_group":"evidence","minimal_title":"G0.5 结构诊断与建模路线","minimal":"include"} -->
规则与执行口径见 modeling-start skill 的 `references/model-diagnostics.md`。本节只承载逐题记录；frontmatter 中的 G0.5 gate 是状态权威源。

<!-- modeling-start:g0-5-diagnostic:v1:start -->

### 1. 决策契约

| 项目 | 内容 |
| --- | --- |
| 任务类型 | 预测 / 优化 / 机理 / 仿真 / 评价 / 其他 |
| 目标变量 / 待解释对象 |  |
| 样本单位 |  |
| 官方主指标 |  |
| 实际使用方式 |  |
| 预测 / 决策时点 |  |
| 时点可得字段 |  |
| 数据划分与防泄漏要求 |  |

### 2. 竞争性结构假设

| 假设编号 | 结构解释 | 支持时应观察到什么 | 不支持时转向哪里 |
| --- | --- | --- | --- |
|  |  |  |  |

### 3. 最小诊断探针

`状态` 只用 `planned / executed / not-applicable`。A 层探针是 M1 前置，可在 `stage: analysis` 受限执行；不得冻结主模型或读取锁定测试指标。

| 探针 ID | 探针角色 | 实现候选 | 检验的假设 | 共享划分 | 状态 | 适用性、理由与误判风险 | 是否调参 |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | 平凡基线 / 低容量 / 通用非线性 / 结构专用 / 反演 |  |  |  | planned |  | 否 |

### 4. 预先声明的判断标准

填写后运行 `scripts/hash_g0_5_criteria.py`，并在决策日志追加同时间、同哈希的 `proposed` 预登记条目。观察结果后不得改写。

- 最小有意义增益：
- 最差情形退化容忍度：
- 泛化差距容忍度：
- 方向一致性参考：
- 主指标、辅助指标及优先级：
- 指标冲突时的取舍原则：
- 复杂度升级条件：
- 停止搜索条件：
- registered_at：
- criteria_hash：

### 5. 诊断结果

每个 `executed` 探针一行。产物与 manifest 均填写相对项目根目录、以 `outputs/` 开头的真实路径。

| evidence_id | 探针 ID | 主指标 | 关键辅助指标 | 波动 | 最差情形 | 训练—验证差距 | 相对基线差异 | 权威产物 | run manifest | 共享生成机制 | 本问适用理由 | 反例风险 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |  |  |  |  |

### 6. 可得信息穷尽审计

仅在探针均贴近平凡基线时执行；判定 `information_limited` 前四行结论必须全部为“否”，且保留否决证据。

| 编号 | 结论 | 证据 | 若为是，转向 |
| --- | --- | --- | --- |
| E1 未纳入的可得字段 |  |  | 扩展条件信息 |
| E2 显式构造量 |  |  | 显式特征构造 |
| E3 分组或层级结构 |  |  | 分层或分群路线 |
| E4 目标参与生成过程 |  |  | 反演路线（H5） |

### 7. 路由结论

以下三项须与 frontmatter 中 G0.5 记录一致。

- gate_status：not-checked
- route：
- reformulation：
- 核心证据：
- 多指标取舍与裁决理由：
- 与预登记默认规则的偏离及理由：
- 已否决路线：
- 否决证据：
- 适用边界：
- G1 获准范围：
- 重新开启条件：

<!-- modeling-start:g0-5-diagnostic:v1:end -->
<!-- modeling-start:endsection -->

<!-- modeling-start:section {"id":"assumptions","full_title":"7. 当前假设","minimal_group":"evidence","minimal_title":"假设与风险","minimal":"include"} -->
| 假设 ID | 假设 | 原因 | 验证方式 | 状态 |
| --- | --- | --- | --- | --- |
|  |  |  |  | 待验证 |

完整模式另登记于 `03_假设与风险.md`；minimal 在本节维护。
<!-- modeling-start:endsection -->

<!-- modeling-start:section {"id":"main-model","full_title":"8. 主模型候选","minimal_group":"model","minimal_title":"主模型候选","minimal":"include"} -->
G0.5 通过前，本表只能使用 `候选`，不得写 `主模型`。

| 模型 | 适用原因 | 输入 | 输出 | 目标/指标 | 风险 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  | 候选 |

### 数学表达

- 决策变量/预测对象：
- 目标函数：
- 约束条件：
- 参数与定义域：
- 求解方法与停止条件：
<!-- modeling-start:endsection -->

<!-- modeling-start:section {"id":"auxiliary-model","full_title":"9. 辅助模型候选","minimal_group":"model","minimal_title":"辅助模型及职责","minimal":"include"} -->
只用于机理解释、模型对照、非线性检查或独立验证，不能与主模型职责混淆。
<!-- modeling-start:endsection -->

<!-- modeling-start:section {"id":"model-selection","full_title":"10. 模型选择标准","minimal_group":"model","minimal_title":"模型选择标准","minimal":"anchor"} -->
- 直接回答题目：
- 拟合或优化质量：
- 泛化能力：
- 可解释性：
- 物理/业务约束：
- 计算成本：
- 与后续问题兼容性：
<!-- modeling-start:endsection -->

<!-- modeling-start:section {"id":"validation","full_title":"11. 验证与敏感性分析","minimal_group":"validation","minimal_title":"验证与敏感性分析","minimal":"include"} -->
检验设计要求见 modeling-start skill 的 `references/modeling-guardrails.md`「模型表达」节第 5–7 项（评价与验证划分、敏感性因素与稳健判据、适用边界与失败场景）。

| 检验 | 改变什么 | 观察什么 | 判定标准 | 证据文件 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

### 11.1 参数来源与决策敏感性

<!-- modeling-start:parameter-check:v1:start -->

| 参数 | 取值/范围 | 来源 | 不确定性依据 | 最终答案是否敏感 | 已扰动范围 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
|  |  | 题面 / 文献 / 数据估计 / 校准 / 自定 |  |  |  |  |

- 参数敏感性自检：not-checked
- 角点与断点自检：not-checked

<!-- modeling-start:parameter-check:v1:end -->

### 适用边界与失败场景
<!-- modeling-start:endsection -->

<!-- modeling-start:section {"id":"unresolved","full_title":"12. 尚未解决的问题","minimal_group":"decision","minimal_title":"尚未解决的问题","minimal":"include"} -->
<!-- modeling-start:endsection -->

<!-- modeling-start:section {"id":"decision","full_title":"13. 当前决策","minimal_group":"decision","minimal_title":"当前决策","minimal":"include"} -->
> [!decision]
> 决策来源：题面 | 数据 | 用户确认 | AI建议
> 决策状态：proposed | active | rejected | superseded
> 当前采用：
> 采用原因：
> 未采用方案：
> 结论适用范围：
> 决策证据：
<!-- modeling-start:endsection -->

<!-- modeling-start:section {"id":"results","full_title":"14. 当前结果","minimal_group":"results","minimal_title":"当前结果","minimal":"include"} -->
### 数值来源

按 modeling-start skill 的 `references/workflow-rules.md#证据权威与数值副本` 填写。本表只登记权威文件、可重算的字段与聚合方式，以及当前副本值。

| 数值 | 权威文件 | 字段与聚合方式 | 当前取值 |
| --- | --- | --- | --- |
|  |  |  |  |

> [!result]
> 关键结果：
> 是否通过预设判据：
> 与预期不一致之处：
> 稳健性结论：

### 负结果闭环

<!-- modeling-start:negative-closure:v1:start -->

| 对象 | 负结果或淘汰证据 | 闭环处置 | 最终回答/替代/适用范围 | 阻塞与下一步 | 证据 |
| --- | --- | --- | --- | --- | --- |
|  |  | 替代方案 / 缩小范围 / 负结论即答案 / 未解决 |  |  |  |

- 负结果闭环自检：not-checked

<!-- modeling-start:negative-closure:v1:end -->
<!-- modeling-start:endsection -->

<!-- modeling-start:section {"id":"evidence-files","full_title":"15. 证据文件","minimal_group":"results","minimal_title":"证据文件","minimal":"anchor"} -->
- 原始数据：
- 清洗数据：
- 代码：
- 结果表：
- 图表：
- 运行日志：
- 稳健性报告：
- 文献：
<!-- modeling-start:endsection -->

<!-- modeling-start:section {"id":"code-interface","full_title":"16. 代码实现接口","minimal_group":"execution","minimal_title":"代码实现接口","minimal":"anchor"} -->
| 任务 | 输入 | 输出 | 方法 | 校验 | 回填位置 |
| --- | --- | --- | --- | --- | --- |
| 问题 {{question}} |  |  |  |  | 本文件第 14、15 节 |
<!-- modeling-start:endsection -->

<!-- modeling-start:section {"id":"next-actions","full_title":"17. 下一步动作","minimal_group":"execution","minimal_title":"下一步动作","minimal":"include"} -->
执行者是下游问题的动作，在条目中写明执行问题，避免它只存在于本问。

### 最低交付与预算

<!-- modeling-start:budget-plan:v1:start -->

| 工作 ID | 工作项 | 级别 | 状态 | 对应交付物/证据 | 依赖 | 例外决策 |
| --- | --- | --- | --- | --- | --- | --- |
|  |  | M1 / M2 / M3 | planned |  |  |  |

<!-- modeling-start:budget-plan:v1:end -->

- M1：本问题面的最低完整回答，至少包含主结论、基本验证和可使用的输出形态。
- M2：稳健性、基线、对照和重要敏感性。
- M3：深化、扩展模型、额外解释或更昂贵实验。
<!-- modeling-start:endsection -->
