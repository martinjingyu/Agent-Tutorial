---
name: cv-screening-kanban
description: Create one Kanban board per candidate and orchestrate all CV screening stage-1 research/report tasks as an agentic dependency graph. Each task is executed by the agent itself (not by an external pipeline script).
---

# CV Screening Kanban Orchestration

## 何时使用

当需要对一个或多个候选人执行完整的 Stage 1 简历初筛流程时使用。本 skill 将整个流程拆分为多个 Kanban task，每个 task 由 agent 自己 agentic 地完成（不依赖外部 pipeline 脚本）。

**核心设计原则**：
- 每个候选人一个 Kanban board
- 每个 task 通过 `skill` 字段引用对应的专用 skill，worker 加载 skill 后按步骤执行
- 不调用任何外部 repo 的脚本（如 CVScreeningAgent 的 kanban_task_runner.py）
- **所有输出文件统一保存在 `candidates/{候选人姓名}/` 下**

## Board 命名

```text
cv-candidate-<候选人姓名或标识>
```

示例：
```text
cv-candidate-LeiShen
cv-candidate-zhangsan
```

## 候选人 Task 依赖图

```
ingest-profile (解析简历 → profile.json)
    ├── school-transcript (学校/专业调研 + 成绩分析)
    ├── publication (论文/出版物分析)
    ├── work-experience (工作/实习经历分析)
    └── project-awards (项目/竞赛分析)
            └── extra-info (补充信息搜索)
                    └── final-report (综合筛选报告)
```

### 各 Task 说明

| Task ID | 标题 | 依赖 | 引用 Skill | 输出文件（均在 `candidates/{姓名}/` 下） |
|---------|------|------|-----------|----------------------------------------|
| `ingest-profile` | 简历解析 | 无 | `hr-recruitment/ingest-profile` | `profile.json`, `profile-summary.md` |
| `school-transcript` | 学校/专业调研 | ingest-profile | `hr-recruitment/school-transcript` | `school-report.md`, `transcript-analysis.md` |
| `publication` | 论文/出版物分析 | ingest-profile | `hr-recruitment/publication-analysis` | `publications.md` |
| `work-experience` | 工作/实习经历分析 | ingest-profile | `hr-recruitment/work-experience-analysis` | `work-experience.md` |
| `project-awards` | 项目/竞赛分析 | ingest-profile | `hr-recruitment/project-awards-analysis` | `projects-awards.md` |
| `extra-info` | 补充信息搜索 | school-transcript, publication, work-experience, project-awards | `hr-recruitment/extra-info-collection` | `extra-info.md` |
| `final-report` | 综合筛选报告 | school-transcript, publication, work-experience, project-awards, extra-info | `hr-recruitment/stage1-screening-report` | `stage1-screening.md`, `stage1-verdict.json` |

## 创建 Pipeline 的模板

使用 `kanban_create_pipeline` 创建 task 链。**每个 task 的 `skill` 字段引用对应的专用 skill**，worker 会自动加载 skill 并按步骤执行。

```json
{
  "board": "cv-candidate-{候选人姓名}",
  "tasks": [
    {
      "id": "ingest-profile",
      "title": "解析简历并生成结构化 profile.json",
      "skill": "hr-recruitment/ingest-profile",
      "prompt": "候选人: {姓名}\n简历文件路径: {简历文件路径}\n候选人文件夹: candidates/{姓名}/\n\n请按 ingest-profile skill 的步骤执行：\n1. 使用 read_file 读取简历文件\n2. 提取结构化信息\n3. 输出 candidates/{姓名}/profile.json\n4. 可选：输出 candidates/{姓名}/profile-summary.md"
    },
    {
      "id": "school-transcript",
      "title": "调研学校/专业并分析成绩",
      "skill": "hr-recruitment/school-transcript",
      "depends_on": ["ingest-profile"],
      "prompt": "候选人: {姓名}\n候选人文件夹: candidates/{姓名}/\n\n请按 school-transcript skill 的步骤执行：\n1. 读取 candidates/{姓名}/profile.json\n2. 调研学校和专业\n3. 分析课程与 JD 匹配度\n4. 输出 candidates/{姓名}/school-report.md\n5. 如有成绩数据，输出 candidates/{姓名}/transcript-analysis.md"
    },
    {
      "id": "publication",
      "title": "分析论文/出版物",
      "skill": "hr-recruitment/publication-analysis",
      "depends_on": ["ingest-profile"],
      "prompt": "候选人: {姓名}\n候选人文件夹: candidates/{姓名}/\n\n请按 publication-analysis skill 的步骤执行：\n1. 读取 candidates/{姓名}/profile.json\n2. 提取论文/出版物列表\n3. 逐一验证论文真实性\n4. 评估学术贡献度\n5. 输出 candidates/{姓名}/publications.md\n6. 如无论文，记录 valid skip"
    },
    {
      "id": "work-experience",
      "title": "分析工作/实习经历",
      "skill": "hr-recruitment/work-experience-analysis",
      "depends_on": ["ingest-profile"],
      "prompt": "候选人: {姓名}\n候选人文件夹: candidates/{姓名}/\n\n请按 work-experience-analysis skill 的步骤执行：\n1. 读取 candidates/{姓名}/profile.json\n2. 提取工作/实习经历\n3. 验证公司/岗位真实性\n4. 评估经历深度与 JD 匹配度\n5. 输出 candidates/{姓名}/work-experience.md\n6. 如无经历，记录 valid skip"
    },
    {
      "id": "project-awards",
      "title": "分析项目与竞赛",
      "skill": "hr-recruitment/project-awards-analysis",
      "depends_on": ["ingest-profile"],
      "prompt": "候选人: {姓名}\n候选人文件夹: candidates/{姓名}/\n\n请按 project-awards-analysis skill 的步骤执行：\n1. 读取 candidates/{姓名}/profile.json\n2. 提取项目经历和竞赛/奖项\n3. 验证项目链接真实性\n4. 评估项目质量和奖项含金量\n5. 输出 candidates/{姓名}/projects-awards.md\n6. 如无项目/奖项，记录 valid skip"
    },
    {
      "id": "extra-info",
      "title": "搜索补充信息",
      "skill": "hr-recruitment/extra-info-collection",
      "depends_on": ["school-transcript", "publication", "work-experience", "project-awards"],
      "prompt": "候选人: {姓名}\n候选人文件夹: candidates/{姓名}/\n\n请按 extra-info-collection skill 的步骤执行：\n1. 读取 candidates/{姓名}/ 下所有前置 task 的输出文件\n2. 识别信息缺口\n3. 搜索补充信息\n4. 输出 candidates/{姓名}/extra-info.md"
    },
    {
      "id": "final-report",
      "title": "生成最终筛选报告",
      "skill": "hr-recruitment/stage1-screening-report",
      "depends_on": ["school-transcript", "publication", "work-experience", "project-awards", "extra-info"],
      "prompt": "候选人: {姓名}\n候选人文件夹: candidates/{姓名}/\nJD 文件路径: {JD 文件路径}\n\n请按 stage1-screening-report skill 的步骤执行：\n1. 读取 candidates/{姓名}/ 下所有前置 task 的输出文件\n2. 读取 JD 文件\n3. 构建候选人画像\n4. 生成 JD 匹配度矩阵\n5. 三维度综合评估\n6. 输出 candidates/{姓名}/stage1-screening.md\n7. 可选：输出 candidates/{姓名}/stage1-verdict.json"
    }
  ]
}
```

## 调度模式

```json
{"board": "cv-candidate-{姓名}", "max_spawn": 1}
```

建议并发度：
- `max_spawn=1` — 如果浏览器状态或登录状态脆弱
- `max_spawn=2` — ingest-profile 完成后，school-transcript/publication/work-experience/project-awards 可并行

## 最终报告验证规则

final-report task 完成后必须验证：
1. `candidates/{姓名}/stage1-screening.md` 存在
2. 报告包含 Markdown 链接引用各子报告（如 `[学校调研](school-report.md)`）
3. 缺失的可选部分明确标注（如"无论文发表"）
4. 结论明确：直接通过 ✅ / 可以考虑 🔶 / 不能通过 ❌

## 注意事项

1. **不要调用外部 pipeline 脚本** — 所有 task 由 agent 自己使用工具（read_file、write_file、browser_navigate、skills 等）完成
2. **所有文件统一保存在候选人文件夹下** — `candidates/{候选人姓名}/`
3. **每个 task 引用专用 skill** — 使用 `skill` 字段引用对应的 skill，worker 会自动加载
4. **task 之间通过文件传递数据** — 前置 task 的输出文件是后置 task 的输入
5. **使用 `kanban_dispatch` 推进 pipeline** — 每次调用会检查哪些 task 的依赖已满足并启动它们
6. **Kanban 不限于 CV screening** — 本 skill 的通信模式和调度模式（list→show→dispatch）同样适用于其他多步骤调研任务（如学校/教授调研、文献综述等）。只需调整 task 定义中的 `skill` 和 `prompt` 即可复用。对于学术论文/研究想法的深度调研，参见 `research/idea-deep-research` skill。

## 用户沟通模式

当用户询问进度（"完成了几个？"）时，参考 `references/kanban-workflow-communication.md` 中的标准流程和回答模板。核心原则：先 `kanban_list_tasks` 查看状态，如有 ready 任务再 `kanban_dispatch` 启动，并向用户清晰解释两个工具的不同角色。

## References

- `references/kanban-workflow-communication.md` — Kanban 工作流用户沟通指南
- `hr-recruitment/ingest-profile` — 简历解析 skill
- `hr-recruitment/school-transcript` — 学校/专业调研 skill
- `hr-recruitment/publication-analysis` — 论文分析 skill
- `hr-recruitment/work-experience-analysis` — 工作经历分析 skill
- `hr-recruitment/project-awards-analysis` — 项目/竞赛分析 skill
- `hr-recruitment/extra-info-collection` — 补充信息收集 skill
- `hr-recruitment/cv-link-deep-research` — 链接深度调研（被 project-awards-analysis 引用）
- `hr-recruitment/stage1-screening-report` — 最终筛选报告 skill
- `research/university-program-research` — 学校/专业调研（被 school-transcript 引用）
- `utilities/windows-file-operations` — Windows 文件操作最佳实践
