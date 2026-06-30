---
name: oa-generation
description: 为候选人生成定制化在线编程测试（OA）题包，基于候选人 profile 和 JD 要求设计题目方案，输出完整的 OA 题包文件。
---

# OA Generation (在线编程测试题包生成)

## 何时使用

当需要为候选人**生成**定制化 OA（Online Assessment）编程题包时使用。本 skill 指导 agent 如何：
1. 分析候选人 profile 和 JD 要求，设计 OA 题目方案
2. 生成完整的 OA 题包文件（README.md、source_materials、代码框架、schema、内部评价标准）
3. 使用 Kanban 板编排多任务依赖关系
4. **最终审查确保题包质量，并在审查中闭环修改缺陷**

## 与 oa-evaluation 的区别

| 维度 | oa-generation（本 skill） | oa-evaluation（现有 skill） |
|------|--------------------------|----------------------------|
| 目的 | 为候选人**生成** OA 题目 | **评估**候选人提交的 OA 代码 |
| 输入 | 候选人 profile + JD | 候选人提交的代码文件 |
| 输出 | OA 题包（题目、框架、评价标准） | 评估报告（评分、结论） |
| 阶段 | Stage 2 流程中的出题环节 | Stage 2 流程中的评估环节 |

## 前置条件

- 候选人已完成 Stage 1 筛选（profile.json 存在）
- JD（职位描述）已读取
- 已了解候选人的技术栈、项目经历、竞赛背景

## 目录结构约定

所有 OA 题包文件保存在 `candidates/{候选人姓名}/OA_v3/` 下（v3 表示第三版/定制版，基于内部出题标准）：

```
candidates/{候选人姓名}/
├── profile.json                    # Stage 1 简历数据
├── OA_v3/
│   ├── README.md                   # OA 任务概述（题目、要求、截止时间等）
│   ├── CONTEXT.md                  # 公司背景、情报源描述、业务规则
│   ├── DELIVERABLES.md             # 提交物清单
│   ├── materials/                  # 输入材料（多源情报数据，文本量约20000字）
│   ├── scaffold/                   # 半结构化代码框架
│   ├── SCORING.md                  # 评分标准
│   ├── tests/                      # 测试文件
│   ├── INTERNAL_EVALUATION.md      # 内部评价标准（面试官手册）
│   └── review_report.md            # 最终审查报告
```

## 生成流程

### Step 1: 分析候选人背景与 JD

读取以下材料：
- **profile.json** — 候选人的教育背景、技术栈、项目经历、竞赛获奖
- **JD** — 职位要求、技术栈偏好、工作内容

分析要点：
- 候选人的技术栈与 JD 要求的匹配度
- 候选人的薄弱环节（需要在 OA 中重点考察）
- 候选人的强项（可以在 OA 中适当挑战）
- 题目难度应与候选人水平匹配（不过于简单也不过于困难）

### Step 2: 设计 OA 题目方案

**必须先读取内部出题标准**：加载 `references/oa-design-standards.md`，确保题目设计符合"四不准与三必须"和"三段式题目演进模板"。

设计 2-3 道编程题，覆盖以下维度：
- **Agent/Pipeline 设计直觉**（核心考察点，占 40% 分值）
- **LLM 缺陷控制能力**（幻觉、格式漂移、失控处理，占 25% 分值）
- **工程实现**（代码组织、模块化，允许粗糙，占 15% 分值）
- **输出质量**（准确性、完整性、结构化程度，占 20% 分值）

每道题应包含：
- 题目名称和概述
- 问题描述（中文）
- 输入输出规范
- 示例
- 约束条件
- 考察要点

#### 题目设计原则（基于内部标准）

1. **不是纯算法题** — 考察 Agent/Pipeline 设计能力，而非 LeetCode 风格
2. **不是 Prompt 调优题** — 考察对 LLM 缺陷的控制力，而非 Prompt 语法
3. **不依赖特定框架** — 候选人可以用任何方式实现
4. **不限定唯一路线** — 允许多种实现方案
5. **必须有复杂业务目标与噪声输入** — 模拟真实场景，输入包含冲突/冗余/缺失信息
6. **必须有可量化输出目标** — 输出可客观比对
7. **必须有极大容错空间** — 2小时笔试允许代码粗糙

#### 三段式题目演进

| 段位 | 名称 | 考察点 | 说明 |
|:---:|------|--------|------|
| 1 | 基础闭环 | 已知维度抽取与生成 | 给明确维度，从原始材料提取信息按结构输出 |
| 2 | 动态泛化 | 未知维度自适应 | 不给固定维度，让候选人自主分析并设计大纲 |
| 3 | 极限压测 | 海量异构数据流架构 | 面试讨论环节，非笔试 |

#### raw material 文本量要求

- materials/ 目录下的输入材料总文本量需达到约 **20000 字**
- 材料应包含多源、异构、冲突/冗余/缺失信息
- 模拟真实业务场景中的情报分析任务

### Step 3: 创建 Kanban 板编排任务

#### 3.1 先召开 OA 题目方案设计讨论会

在创建文件生成 pipeline 之前，**必须先召开设计讨论会**，确定题目方案。有两种方式：

**方式 A（推荐）：使用 `kanban_create_meeting_task`**
```python
kanban_create_meeting_task(
    board="oa-design-{候选人姓名}",
    title="OA题目方案设计讨论会 - {候选人姓名}",
    topic="""## 会议目标：为候选人 {姓名} 设计 OA 题包方案

### 候选人背景
{从 profile.json 提取的关键信息}

### JD 要求
{JD 核心要求}

### OA 出题硬性要求（四不准与三必须）
{从 references/oa-design-standards.md 加载}

### 三段式题目演进模板
{从 references/oa-design-standards.md 加载}

### 需要讨论并输出的内容
1. 题目场景设计（什么业务场景）
2. 3道题的详细描述（名称、考察点、输入输出规范）
3. 噪声/冲突/干扰项的设计方案（raw material 文本量需达到约20000字）
4. 评分维度与权重
5. 脚手架代码的故意缺陷设计
""",
    suggested_participants=["张工：资深AI算法面试官，擅长Agent架构设计、LLM评估",
                           "李老师：OA出题专家，擅长编程题设计、考核维度设计",
                           "王工：Agent系统架构师，擅长多智能体系统、Pipeline设计"]
)
```
然后 dispatch 等待完成，读取会议结论。

**方式 B：主 agent 直接调用 meeting 工具**
如果会议比较简单，主 agent 可以直接调用 meeting 工具：
```python
meeting_create_participants(...)
meeting_set_agenda(...)
meeting_chain(...)  # 或 meeting_group_discuss
meeting_conclude(...)
```

#### 3.2 创建文件生成 Kanban pipeline

会议确定题目方案后，使用 `kanban_create_pipeline` 创建 OA 题包生成 Kanban 板，包含以下任务：

1. **生成 README.md** — 基于题目方案生成 OA 任务概述
2. **生成 CONTEXT.md** — 生成公司背景和情报源描述
3. **生成 DELIVERABLES.md** — 生成提交物清单
4. **生成 materials/** — 生成输入材料（多源情报数据，文本量约20000字）
5. **生成 scaffold/** — 生成半结构化代码框架
6. **生成 SCORING.md** — 生成评分标准
7. **生成 tests/** — 生成测试文件
8. **生成 INTERNAL_EVALUATION.md** — 生成内部评价标准

**注意**：文件生成任务如果仅需 write_file/read_file 等基础工具，可以通过 Kanban dispatch 派发给 worker 并行执行。但如果 worker 大量失败，应回退到主 agent 顺序执行（见注意事项 #10）。

### Step 4: 生成各文件

#### README.md
OA 任务概述，包含：
- 候选人姓名
- OA 目的说明
- 题目列表（含每题概述）
- 提交要求（代码规范、截止时间等）
- 评分说明

#### CONTEXT.md
公司背景和情报源描述，包含：
- 公司/组织背景
- 各情报源的描述和格式
- 业务规则和约束

#### DELIVERABLES.md
提交物清单，包含：
- 必需提交文件列表
- 格式要求
- 提交方式
- 提交前检查清单

#### materials/
输入材料，包含多源情报数据文件（JSON、CSV、TXT 等格式），模拟真实场景中的多源数据。

#### scaffold/
半结构化代码框架，包含：
- main.py — 主入口
- config.py — 配置管理
- ingestor.py — 数据读取模块
- analyzer.py — 分析模块
- fuser.py — 融合模块
- reporter.py — 报告生成模块
- llm_client.py — LLM 调用封装
- __init__.py — 包初始化

每个模块包含故意设计的缺陷（如无错误处理、无重试、无格式校验等），供候选人修复。

#### SCORING.md
评分标准，包含：
- 评分维度与权重
- 各维度评分细则
- 评分等级（Strong Pass / Pass / Review / Fail）
- 简历夸大对照表
- 降档与 FAIL 机制
- 评分流程

#### tests/
测试文件，包含：
- sample_output.json — 预期输出示例
- qa_baseline.py — 自动化检查脚本

#### INTERNAL_EVALUATION.md
内部评价标准（面试官手册），包含：
- 各维度评分细则
- 扣分规则
- 加分项
- 结论判定标准
- 面试追问建议

### Step 5: 最终审查 — 闭环修改流程（关键步骤）

这是本 skill 的核心设计。最终审查**不是**一次性的"审查→给结论"，而是**"审查→发现缺陷→修改→再确认"的闭环**。

#### 5.1 审查方式

**必须由主 agent 直接调用 meeting 工具**（而非通过 Kanban dispatch），原因：
- 审查会议的核心是"发现缺陷→修改→再确认"的闭环
- 主 agent 需要在会议过程中直接修改文件（write_file/patch_file）
- 即使 `kanban_create_meeting_task` 预注册了 meeting 工具，worker 也无法在会议中修改主 agent 工作区的文件
- 因此审查会议必须由主 agent 亲自执行

#### 5.2 审查-修改闭环流程

```
Round 1: 专家审查
  ├── 主 agent 调用 meeting_group_discuss 或 meeting_chain
  ├── 各专家审查 OA 题包，提出缺陷/改进建议
  └── 主 agent 收集所有建议，整理为"缺陷清单"

Round 2: 主 agent 修改文件（根据缺陷清单逐一修复）
  ├── 对每个缺陷，使用 write_file/patch_file 修改对应文件
  ├── 记录每次修改的内容和原因
  └── 所有修改完成后，汇总"修改记录"

Round 3: 专家确认修改
  ├── 主 agent 再次调用 meeting_ask_one 或 meeting_group_discuss
  ├── 向专家展示修改记录，请专家确认修改是否到位
  ├── 如有专家认为修改不充分 → 返回 Round 2 继续修改
  └── 所有专家确认通过 → 进入 Round 4

Round 4: 输出最终结论
  ├── 主 agent 调用 meeting_conclude
  ├── 输出审查报告（review_report.md），包含：
  │   ├── 审查概况（参与专家、审查范围）
  │   ├── 发现的缺陷清单（含严重程度）
  │   ├── 修改记录（缺陷→修改→确认）
  │   └── 最终结论（可以交付 / 需要进一步修改）
  └── 会议结束
```

#### 5.3 主 agent 在会议中的角色

在审查会议中，主 agent 承担**双重角色**：
1. **会议主持人** — 调用 meeting 工具组织讨论、收集意见
2. **执行者** — 根据专家意见直接修改文件（write_file/patch_file）

**不要**在会议中创建 Kanban task 来执行修改——主 agent 自己就是执行者。

#### 5.4 缺陷分类与处理优先级

| 严重程度 | 定义 | 处理要求 |
|---------|------|---------|
| 阻断性 | 代码无法运行、核心功能缺失、评分标准矛盾 | 必须修复，否则不能交付 |
| 重要 | 文档不一致、缺陷设计不合理、测试用例错误 | 建议修复 |
| 轻微 | 格式问题、措辞优化、补充说明 | 可选修复，不影响交付 |

#### 5.5 修改记录模板

每次修改后，在 review_report.md 中记录：

```markdown
### 修改记录

| # | 缺陷描述 | 严重程度 | 修改文件 | 修改内容 | 确认状态 |
|---|---------|:-------:|---------|---------|:-------:|
| 1 | llm_client.py 缺少超时模拟 | 重要 | scaffold/llm_client.py | 增加 5% 超时/慢响应模拟 | 已确认 |
| 2 | SCORING.md 降级定义不明确 | 重要 | SCORING.md | 补充降级处理的具体示例 | 已确认 |
```

审查 OA 题包的质量：
- **一致性**：README.md 中的题目描述与 source_materials.txt 一致
- **完整性**：所有文件齐全，无遗漏
- **可运行性**：scaffold 代码的测试用例可运行
- **难度匹配**：题目难度与候选人水平匹配
- **JD 对齐**：题目覆盖 JD 要求的关键技术点

## 题目设计原则

1. **四不准**：不是纯算法题、不是 Prompt 调优题、不依赖特定框架、不限定唯一路线
2. **三必须**：必须有复杂业务目标与噪声输入、必须有可量化输出目标、必须有极大容错空间
3. **三段式演进**：基础闭环 → 动态泛化 → 极限压测
4. **难度梯度**：2-3 道题应有难度梯度（简单/中等/较难）
5. **区分度**：题目应能区分不同水平的候选人
6. **领域相关**：至少 1 道题与 JD 技术栈相关
7. **可评估**：每道题有明确的评分标准
8. **原创性**：避免直接使用 LeetCode 原题，适当改编
9. **时间合理**：总完成时间控制在 2-3 小时内
10. **raw material 文本量**：输入材料总文本量需达到约 20000 字

## 状态查询效率

当用户询问 OA 生成进度（如"现在执行情况"）时：

1. **优先使用 `kanban_list_tasks` 获取概览** — 直接查看各任务状态（todo/in_progress/done/error）
2. **如果大部分任务已完成**，直接汇总结果回复用户，无需逐一读取 worker 日志
3. **仅在任务失败或用户追问细节时**，才读取具体 worker 日志文件
4. **回复格式**：简洁的表格或列表，标明已完成/进行中/失败的任务数量及名称
5. **避免过度读取**：不要一次性读取所有 worker 日志，这会产生大量冗余 tool 调用，用户通常只需要知道"完成了没有"

## 注意事项

1. **题目方案应先设计再生成文件**，确保整体一致性
2. **Kanban 板用于编排依赖关系**，任务间有依赖时需设置 `depends_on`
3. **scaffold 代码应包含可运行的测试用例**，方便候选人验证
4. **SCORING.md 应与 INTERNAL_EVALUATION.md 的维度一致**
5. **最终审查是必要步骤，不要跳过**
6. **OA 题包生成是 Stage 2 流程**，应在 Stage 1 筛选通过后进行

7. **会议执行方式的选择**：OA 生成流程中有两种会议场景，执行方式不同：

   **场景 A：OA 题目方案设计讨论会（Step 2 的会议）**
   - 可以使用 `kanban_create_meeting_task` + `kanban_dispatch` 派发给 worker
   - 原因：`kanban_create_meeting_task` 创建的 task 预注册了 meeting 工具（`extra_tools: ["meeting"]`），worker 可以正常执行会议
   - 流程：创建 meeting task → dispatch → 等待完成 → 读取会议结论

   **场景 B：最终审查会议（Step 5 的会议）**
   - **必须由主 agent 直接调用 meeting 工具**，不能通过 Kanban dispatch
   - 原因：主 agent 需要在会议中直接修改文件（write_file/patch_file），这是审查闭环的核心
   - 流程：主 agent 调用 meeting_create_participants → meeting_set_agenda → meeting_chain/meeting_group_discuss → 发现缺陷 → write_file/patch_file 修改 → 再确认 → meeting_conclude

   **通用原则**：如果会议只需要讨论/输出结论（不需要修改文件），可以用 `kanban_create_meeting_task`。如果会议需要主 agent 在执行过程中修改文件，必须由主 agent 直接调用。

8. **内部出题标准缺失时的处理流程**：如果在 workspace 中搜索不到内部 OA 设计标准（如"四不准"、"三必须"等规则），应按以下顺序处理：
   - ① 检查 skills 和 memory 中是否已有相关规则记录
   - ② 如果仍找不到，直接询问用户（respond_to_user）获取内部标准，而非自行创建会议讨论
   - ③ 只有在用户明确要求讨论时才使用 meeting 工具，且必须由主 agent 直接调用（见注意事项 #7）
   - ④ 将用户提供的内部标准保存到 memory 或 skill 的 references/ 下，供后续 OA 生成复用

9. **Kanban dispatch 的适用性判断**：OA 题包的文件生成任务是否可以通过 `kanban_dispatch` 派发给 worker，取决于 worker 的工具集是否足够：
   - **可 dispatch 的场景**：任务仅需 `write_file`、`read_file`、`search_files` 等基础工具，且 worker 的 prompt 能正确指导文件生成。此时 dispatch 可并行加速。
   - **不可 dispatch 的场景**：任务需要浏览器调研、meeting 工具、或 worker 未注册的其他工具。此时应由**主 agent 直接执行**。
   - **判断方法**：在 dispatch 前检查 `subprocess_worker.py` 中注册的工具列表，确认 worker 具备所需工具。
   - **回退策略**：如果 dispatch 后大量任务失败（如 8/9 失败），应改为由主 agent 顺序执行（见注意事项 #10）。
   - **Kanban 板的核心用途**：编排任务依赖关系（通过 `depends_on` 参数），无论由主 agent 还是 worker 执行。

10. **Kanban pipeline 大量失败时的恢复流程**：如果 Kanban pipeline 中大部分任务报错（如 8/9 失败），应按以下顺序处理：
    - ① 读取失败任务的 worker 日志，分析根因（工具缺失？prompt 错误？worker 崩溃？）
    - ② 如果根因是 Kanban worker 工具集不足，改为由主 agent 直接执行任务
    - ③ 如果根因是任务 prompt 设计问题，修正 prompt 后重新创建 pipeline
    - ④ 如果连续失败且无法定位根因，停止重试，改用主 agent 顺序执行模式（不使用 Kanban）
    - ⑤ 将根因记录到 memory 或 skill 的 references/ 下，避免重复踩坑

11. **最终审查会议必须包含修改闭环**：Step 5 的审查不是一次性的"审查→给结论"，而是"审查→发现缺陷→修改→再确认"的闭环。主 agent 在会议中既是主持人也是执行者，发现缺陷后应立即使用 write_file/patch_file 修改，然后请专家确认。详见 Step 5.2 的闭环流程。

## 相关 Skills

- `hr-recruitment/oa-evaluation` — 评估候选人 OA 提交（本 skill 的后续步骤）
- `hr-recruitment/stage1-screening-report` — Stage 1 筛选报告（OA 生成的前置条件）
- `utilities/windows-file-operations` — Windows 文件操作最佳实践
- `utilities/context-management` — 上下文管理最佳实践

## 内部参考资料

- `references/oa-design-standards.md` — OA 出题内部标准（四不准与三必须、三段式演进模板、评分维度与权重）
