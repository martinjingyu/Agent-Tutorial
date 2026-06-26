---
name: school-transcript
category: hr-recruitment
description: 基于 profile.json 中的教育信息，调研候选人所在学校和专业，分析课程设置与 JD 的匹配度，输出 school-report.md 和 transcript-analysis.md 到 candidates/{候选人姓名}/ 下。
---

# school-transcript — 学校/专业调研与成绩分析

## 何时使用

当 Kanban pipeline 的 `school-transcript` task 被调度时使用。本 skill 指导 agent 如何调研候选人的学校和专业背景。

## 输入

从 task prompt 中获取：
- **候选人姓名**
- **候选人文件夹**（如 `candidates/Lei Shen/`）
- **JD 文件路径**（可选，用于匹配度分析）

从 `candidates/{候选人姓名}/profile.json` 读取：
- `education[].institution` — 学校名称
- `education[].major` — 专业名称
- `education[].degree` — 学位
- `education[].gpa` — GPA
- `education[].courses` — 课程列表
- `education[].ranking` — 排名

## 工作流程

### Step 1: 读取输入

1. 使用 `read_file` 读取 `candidates/{候选人姓名}/profile.json`
2. 提取教育信息
3. 如有 JD 文件，读取 JD 了解岗位要求

### Step 2: 学校/专业调研

使用 `university-program-research` skill 进行调研：

1. 调用 `skill_view(name='university-program-research')` 加载该 skill
2. 按 skill 的步骤调研学校排名、专业课程设置、研究方向
3. 学校调研报告保存到 `reports/{学校名}/{专业名}.md`（通用存档）

### Step 3: 分析课程匹配度

将候选人的课程列表与 JD 要求进行对比：

| JD 要求的知识领域 | 候选人相关课程 | 匹配度 |
|-----------------|--------------|:-----:|
| 机器学习/深度学习 | 课程名 | ✅/⚠️/❌ |
| NLP / LLM | 课程名 | ✅/⚠️/❌ |
| 数据结构与算法 | 课程名 | ✅/⚠️/❌ |
| ... | ... | ... |

### Step 4: 分析成绩单（如有）

如果 profile.json 中有详细的课程成绩数据：
1. 计算核心课程的平均成绩
2. 评估成绩趋势（上升/下降/稳定）
3. 标注与 JD 相关的课程成绩

### Step 5: 输出文件

1. **`candidates/{候选人姓名}/school-report.md`** — 学校/专业调研报告
   - 学校排名与声誉
   - 专业课程设置
   - 研究方向与实验室
   - 课程与 JD 匹配度分析
   - 综合评估

2. **`candidates/{候选人姓名}/transcript-analysis.md`**（如有成绩数据）
   - 核心课程成绩
   - 成绩趋势
   - 与 JD 相关的课程表现

### Step 6: 完成

调用 `respond_to_user` 报告完成状态。

## 注意事项

1. **学校调研报告保存两份**：`reports/{学校名}/{专业名}.md`（通用存档）+ `candidates/{候选人姓名}/school-report.md`（候选人专属）
2. **如无详细成绩数据**，transcript-analysis.md 可以跳过，在 school-report.md 中说明即可
3. **不要只看排名** — 名校的弱项专业可能不如普通学校的强项专业
4. **关注课程设置与 JD 的匹配度**，而不是学校名气

## References

- `research/university-program-research` — 学校/专业调研 skill
- `utilities/windows-file-operations` — Windows 文件操作最佳实践
