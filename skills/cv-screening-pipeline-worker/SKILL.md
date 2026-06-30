---
name: cv-screening-pipeline-worker
description: Execute one task from a candidate-specific CV screening Kanban board. The agent performs the work itself using tools and skills, not by running an external script.
---

# CV Screening Pipeline Worker

## 何时使用

当被分配到一个候选人 Kanban board 上的某个 task 时使用。本 skill 指导 agent 如何 agentic 地完成该 task。

**核心原则**：
- 不要调用外部 repo 的脚本（如 CVScreeningAgent 的 kanban_task_runner.py）
- 所有工作由 agent 自己使用工具完成
- **所有输出文件必须保存到 `candidates/{候选人姓名}/` 下**

## 通用流程

### Step 1: 理解 Task

仔细阅读 task prompt，确认：
- **候选人姓名/标识** — 用于确定文件夹路径
- **候选人文件夹** — `candidates/{候选人姓名}/`
- **输入文件** — 前置 task 输出的文件路径
- **预期输出** — 需要生成的文件列表
- **引用的 skill** — task 的 `skill` 字段指定的 skill 名称

### Step 2: 加载 Skill

如果 task 有 `skill` 字段，使用 `skill_view(name='{skill}')` 加载该 skill，然后按 skill 的步骤执行。

### Step 3: 读取输入

使用 `read_file` 读取所有输入文件：
- `candidates/{候选人姓名}/profile.json` — 结构化简历数据
- 其他前置 task 的输出文件

### Step 4: 执行工作

根据 task 类型和引用的 skill，使用适当的工具完成工作：

| Task ID | 引用 Skill | 主要工具 |
|---------|-----------|---------|
| `ingest-profile` | `hr-recruitment/ingest-profile` | read_file, write_file |
| `school-transcript` | `hr-recruitment/school-transcript` | browser_navigate, google_search, read_file, write_file |
| `publication` | `hr-recruitment/publication-analysis` | browser_navigate, read_file, write_file |
| `work-experience` | `hr-recruitment/work-experience-analysis` | browser_navigate, read_file, write_file |
| `project-awards` | `hr-recruitment/project-awards-analysis` | browser_navigate, read_file, write_file |
| `extra-info` | `hr-recruitment/extra-info-collection` | browser_navigate, google_search, read_file, write_file |
| `final-report` | `hr-recruitment/stage1-screening-report` | read_file, write_file |
| `oa-evaluation` | `hr-recruitment/oa-evaluation` | read_file, write_file, terminal |

### Step 5: 输出文件

**所有输出文件必须保存到 `candidates/{候选人姓名}/` 下。** 不要将候选人报告保存到 `reports/` 目录。

### Step 6: 完成

调用 `respond_to_user` 报告完成状态，包含：
- 状态（completed / blocked / skipped / error）
- 候选人姓名
- 输出文件路径列表（必须是 `candidates/{候选人姓名}/` 下的路径）
- 关键发现摘要
- 阻塞原因（如有）

## 完成报告模板

```text
Status: completed | blocked | skipped | error
Task: <task-id>
Candidate: <姓名>
Output files:
- candidates/{姓名}/<file1>
- candidates/{姓名}/<file2>
Key findings:
- <发现1>
- <发现2>
Blockers (if any):
- <阻塞原因>
```

## 注意事项

1. **不要调用外部脚本** — 所有工作由 agent 自己使用工具完成
2. **所有文件保存在候选人文件夹** — `candidates/{候选人姓名}/`
3. **使用 skill_view 加载参考 skill** — 每个 task 的 `skill` 字段指定了要加载的 skill
4. **valid skip 不是 error** — 如某 task 无数据可分析（如无论文），记录为 skip 即可
5. **文件间通过 Markdown 链接关联** — final-report 中的链接应指向同文件夹下的子报告

## References

- `cv-screening-kanban` — 上游编排 skill
- `hr-recruitment/ingest-profile` — 简历解析 skill
- `hr-recruitment/school-transcript` — 学校/专业调研 skill
- `hr-recruitment/publication-analysis` — 论文分析 skill
- `hr-recruitment/work-experience-analysis` — 工作经历分析 skill
- `hr-recruitment/project-awards-analysis` — 项目/竞赛分析 skill
- `hr-recruitment/extra-info-collection` — 补充信息收集 skill
- `hr-recruitment/cv-link-deep-research` — 链接深度调研
- `hr-recruitment/stage1-screening-report` — 最终筛选报告生成
- `research/university-program-research` — 学校/专业调研
- `utilities/windows-file-operations` — Windows 文件操作最佳实践
