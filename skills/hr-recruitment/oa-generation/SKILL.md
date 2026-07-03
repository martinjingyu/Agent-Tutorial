---
name: oa-generation
description: 为候选人生成定制化在线编程测试（OA）题包，基于候选人 profile 和 JD 要求设计题目方案，输出完整的 OA 题包文件。
audience: main
---

# OA Generation (在线编程测试题包生成)

## 何时使用

当需要为候选人**生成**定制化 OA（Online Assessment）编程题包时使用。本 skill 指导 agent 如何：
1. 分析候选人 profile 和 JD 要求，设计 OA 题目方案
2. 通过设计会议决定 OA 题包的内容框架、考题大纲、目标文件结构和交付方式
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

- 候选人已完成 Stage 1 
- JD（职位描述）已读取
- 已了解候选人的技术栈、项目经历、竞赛背景

## 目标产物约定

不要在加载本 skill 后直接套用固定文件清单、固定代码框架或固定目录结构。OA 题包的具体文件结构、题目组织方式、材料格式、代码框架是否需要生成，都必须由前置设计会议根据候选人背景、JD 和题目方案决定。

默认输出根目录仍建议放在 `candidates/{候选人姓名}/OA/` 下；若该目录已存在，依次尝试 `OA_2/`、`OA_3/` …，使用第一个不存在的名称（用 `list_files` 检查）。但根目录下的具体文件和子目录由设计会议决定。

无论会议决定采用什么结构，最终题包必须覆盖两类内容：

1. **Candidate-facing requirement / 题面**：候选人能看到并据此完成 OA 的说明，包括题目背景、任务目标、输入/输出要求、提交要求、约束和示例等。文件名和拆分方式由会议决定。
2. **Internal evaluation content / 内部评估材料**：面试官或评估流程使用的评分标准、参考答案或评估思路、扣分规则、面试追问建议、风险点等。文件名和拆分方式由会议决定。

## 生成流程

### Step 1: 分析候选人背景与 JD

读取以下材料：
- **stage1_report.md** — 候选人的教育背景、技术栈、项目经历、竞赛获奖
- **JD** — 职位要求、技术栈偏好、工作内容

分析要点：
- 候选人的技术栈与 JD 要求的匹配度
- 候选人的薄弱环节（需要在 OA 中重点考察）
- 候选人的强项（可以在 OA 中适当挑战）
- 题目难度应与候选人水平匹配（不过于简单也不过于困难）



### Step 2: 创建 Kanban 板编排任务

#### 2.1 先召开 OA 题目方案设计讨论会

使用 `kanban_create_meeting_task`**

由 worker 代替你召开会议。你**不需要也不应该**直接调用任何 `meeting_*` 工具。
```python
kanban_create_meeting_task(
    board="oa-design-{候选人姓名}",
    title="OA题目方案设计讨论会 - {候选人姓名}",
    topic="""## 会议目标：为候选人 {姓名} 设计 OA 题包方案

### 候选人背景
{从 profile.json 提取的关键信息}

### JD 要求
{JD 核心要求}

### OA 出题要求


""",
    suggested_participants=[key: value, ...]
)
```
然后 dispatch 等待完成，读取会议结论。**dispatch 完成后直接读结论，无需再做任何 meeting 操作。**
**注意**: OA 题目有两个硬性要求：
1. 默认使用gpt-4o 模型，因为这个性能没那么超模；
2. raw input data待处理文本量必须要很大，要达到10w字以上，应该要分成好几个文件生成

#### 2.2 Review 会议结论并创建一次完整 Kanban pipeline

会议 task 完成后，你必须先 review 会议结论，review 时提取：

1. 题目方案和考察目标
2. 会议建议的题包内容框架和目标文件结构
3. candidate-facing requirement / 题面应包含的内容
4. internal evaluation content / 内部评估材料应包含的内容
5. 需要哪些 subagent 并行或串行生成

然后使用 `kanban_create_pipeline` 创建 OA 题包生成 Kanban 板，安排 subagents 依次完成任务。不要自己开始写具体题包内容。

Kanban pipeline 的任务清单由会议结论决定，不要硬编码为固定文件名或固定目录。每个 worker task 的 prompt 必须明确：

- 输出应写入哪个目标路径或目标文件集合
- 该任务负责的是 candidate-facing 内容、internal evaluation 内容，还是两者之间的一致性检查
- 需要遵守的题目方案、难度、JD 对齐要求和会议结论
- 与其他任务的依赖关系

**注意**：文件生成任务如果仅需 write_file/read_file 等基础工具，可以通过 Kanban dispatch 派发给 worker 并行执行。但如果 worker 大量失败，你可以回退到顺序执行。

**注意**：生成原始input 文本环节，因为要求总原始文本量比较大，一次write_file 一定会失败。你可以在 Kanban pipeline 中拆分为多个 write_file 任务，把一个原始文本拆分成多个小文件，从而达到文本量。

### Step 3: 生成题包内容

具体生成哪些文件、是否生成代码框架、材料拆成几个文件、是否需要测试或 schema，全部以设计会议结论为准。

生成结果必须满足以下最低要求：

#### Candidate-facing requirement / 题面

候选人可见内容必须足够完整，让候选人不依赖内部材料也能完成 OA。通常需要包含：
- 题目背景和业务场景
- 每道题的任务目标
- 输入、输出、提交格式和约束
- 示例或最小可验证样例
- 完成时间、允许使用的工具/库、禁止事项
- 候选人交付物要求

#### Internal evaluation content / 内部评估材料

内部材料必须足够让评估者一致评分。通常需要包含：
- 评分维度与权重
- 参考解法，三档预期答案
- 核心评估思路
- 候选人背景与 JD 对齐点
- 面试追问建议和风险点

#### 一致性检查

必须安排一个 Kanban task 或最终审查步骤检查 candidate-facing 内容和 internal evaluation 内容是否一致，特别是题目目标、输入输出、评分标准、提交物要求和难度预期。

### Step 4: 最终审查 — 闭环修改流程（关键步骤）

在完成所有 OA 题包生成后，必须进入最终审查阶段，该阶段的目标不是简单验收，而是作为一个“Loop Engineer”机制，对整个 OA 题包进行系统级一致性审查与质量控制，并决定是否进入修复循环或直接发布。

首先需要对整个 OA 题包进行统一评审，评审维度包括：JD 对齐度、难度匹配度、题目一致性、可执行性以及可评分性。其中 JD 对齐度用于判断题目是否覆盖岗位要求的核心能力；难度匹配度用于判断题目是否符合候选人当前水平，避免过难或过易；题目一致性用于检查 candidate-facing requirement、internal evaluation content 与 reference solution 三者是否存在冲突，尤其关注输入输出定义、评分标准与题目目标是否一致；可执行性用于判断候选人是否能够在规定时间内完成且不存在隐性依赖或歧义；可评分性用于判断评分标准是否能够稳定区分不同水平候选人，而不是简单的二值对错。

在完成上述评审后，必须输出结构化 Review Scorecard，用于驱动后续决策，格式如下：

{
  "jd_alignment": 0-5,
  "difficulty_match": 0-5,
  "consistency": 0-5,
  "feasibility": 0-5,
  "scorability": 0-5,
  "overall_risk": "low|medium|high",
  "issues": [
    "具体问题1",
    "具体问题2"
  ]
}

基于该 scorecard，需要进入 Loop Decision Engine。该机制用于决定是否需要重新开启设计会议或仅进行局部修复，或直接发布最终 OA 题包。当满足以下任一条件时必须触发重新设计会议（kanban_create_meeting_task），包括 consistency ≤ 3（存在严重一致性问题）、jd_alignment ≤ 3（与岗位要求偏离较大）、feasibility ≤ 2（不可执行）或存在三个及以上结构性问题且无法通过局部修改解决。在此情况下，应回退至 Step 2.1 重新发起 OA 设计会议，重新生成题目方案与结构设计。

如果问题仅为局部缺陷，例如单点描述错误、评分权重不合理或示例不清晰，则不需要重新开会，而应通过 Kanban pipeline 追加 patch task 进行修复，避免破坏整体设计结构。

当所有指标均满足 quality gate（所有评分 ≥ 4 且不存在结构性冲突）时，则认为该 OA 题包可以直接发布。

此外，该 Loop Engineer 机制必须引入迭代上限控制 max_iterations（建议设为 2）。即系统最多允许两轮完整循环：第一轮为初始生成与评审修复，第二轮为最终清理与收敛优化；若超过迭代上限仍未收敛，则强制进入 release 状态，避免无限循环或过度优化导致 pipeline 阻塞。

整个 Step 4 的本质是将 OA generation 从“线性生成流程”升级为具备自校正能力的闭环系统，即 Plan → Build → Review → Decide → Loop / Release，从而确保最终输出的 OA 题包在一致性、可执行性与评估有效性上达到生产级标准。