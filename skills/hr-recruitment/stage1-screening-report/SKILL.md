---
name: stage1-screening-report
category: hr-recruitment
description: 基于 profile.json、link-verification.md、学校项目分析报告三份材料，结合 JD 要求，生成 Stage 1 最终筛选报告，输出"直接通过/可以考虑/不能通过"三档结论及详细理由。
---

# Stage 1 Screening Report（简历初筛最终报告）

## 何时使用

当需要综合以下三份材料，对候选人做出最终初筛决策时使用：

1. **profile.json** — 简历解析的结构化数据（教育、经历、技能、项目）
2. **link-verification.md** — 链接深度调研验证报告（GitHub、论文、Kaggle 等）
3. **学校项目分析报告** — 候选人所在学校的专业/项目调研报告（课程设置、研究方向、排名等）

输出一份结构化的 **Stage 1 最终筛选报告**，包含：
- 候选人画像摘要
- JD 匹配度矩阵（逐项对比）
- 三档结论：**直接通过 ✅ / 可以考虑 🔶 / 不能通过 ❌**
- 详细理由和面试建议

## 输入材料

### 1. profile.json

由简历解析 pipeline 输出的结构化 JSON，包含：
- `candidate.name` — 候选人姓名
- `education[]` — 教育经历（学校、专业、GPA、课程）
- `work_experience[]` — 工作/实习经历
- `projects[]` — 项目经历（含技术栈、链接）
- `publications_or_reports[]` — 论文/报告
- `skills` — 技能清单

### 2. link-verification.md

由 `cv-link-deep-research` skill 生成的链接验证报告，包含：
- 每个链接的详细分析（代码深度、commit 历史）
- 红旗/绿旗信号
- 交叉验证发现
- 综合可信度评分

### 3. 学校项目分析报告

由 `university-program-research` skill 生成的学校/专业调研报告，包含：
- 学校排名与声誉
- 专业课程设置
- 研究方向与实验室
- 与 JD 的匹配度分析

### 4. JD（职位描述）

JD 文件（.docx 或 .md），包含：
- 岗位职责
- 岗位要求（专业、成绩、技能等）
- 研究方向偏好

## 工作流程

### Step 1: 读取并解析所有输入

使用 `read_file` 读取以下文件：
1. `profile.json` — 候选人结构化数据（位于 `candidates/{id}/` 下）
2. `link-verification.md` — 链接验证报告（位于 `candidates/{id}/` 下）
3. 学校项目分析报告 — 按以下顺序查找：
   - **首选**: `reports/{学校名}/{专业名}.md`（标准报告路径，由 `university-program-research` skill 生成）
   - **备选**: `candidates/{id}/stage1_school_major_research/`（CVScreeningAgent pipeline 输出路径，可能为 `.txt` 诊断文件）
   - **注意**: 如果 pipeline 未配置 API key，诊断文件可能为空（仅含搜索查询计划），此时需根据已有知识补充学校背景信息
4. JD 文件（路径由用户提供或按 `reports/AI算法实习生职位JD_*.docx` 查找）

### Step 2: 构建候选人画像摘要

从 profile.json 提取关键信息，形成简洁摘要：

```
## 候选人画像

| 项目 | 详情 |
|------|------|
| 姓名 | {name} |
| 当前教育 | {institution} · {major} · {degree} · GPA {gpa} |
| 过往教育 | {previous_institution} · {major} · GPA {gpa} |
| 实习经历 | {count} 段 · {companies} |
| 项目经历 | {count} 个 · {project_names} |
| 论文/报告 | {count} 篇 |
| 核心技能域 | {skill_areas} |
| 语言成绩 | {IELTS/TOEFL} |
```

### Step 3: JD 匹配度矩阵

将 JD 要求逐项与候选人背景对比。JD 要求分为三类：

#### 硬性门槛（必须满足）
| JD 要求 | 候选人情况 | 匹配度 | 证据来源 |
|---------|-----------|:-----:|---------|
| 专业：AI/CS/软件工程 | {major} | ✅/⚠️/❌ | profile.json |
| 成绩前10% | GPA {value}/{scale} | ✅/⚠️/❌ | profile.json |
| 熟练掌握 Python | {evidence} | ✅/⚠️/❌ | profile.json + link-verification |
| 熟悉至少一款大模型 | {evidence} | ✅/⚠️/❌ | profile.json + link-verification |

#### 研究方向偏好（加分项）
| JD 研究方向 | 候选人相关经验 | 匹配度 |
|------------|--------------|:-----:|
| Fine-tuning / Post-pretraining | {experience} | ✅/⚠️/❌ |
| RAG / GraphRAG | {experience} | ✅/⚠️/❌ |
| Multi-agent System | {experience} | ✅/⚠️/❌ |
| GNN / GAT | {experience} | ✅/⚠️/❌ |
| ... | ... | ... |

#### 软性素质（参考项）
| JD 要求 | 候选人表现 | 评估 |
|---------|-----------|:----:|
| 热爱AI，不惧怕学习新技术 | {evidence} | ✅/⚠️/❌ |
| 解决别人解决不了的问题 | {evidence} | ✅/⚠️/❌ |

### Step 4: 综合三个维度的评估

#### 维度 A: 硬性条件（来自 profile.json）
- 专业匹配度
- GPA/成绩排名
- 技能匹配度
- 教育背景质量（学校排名、专业相关性）

#### 维度 B: 真实性/可信度（来自 link-verification.md）
- 链接验证整体可信度评分
- 红旗信号数量和严重程度
- 简历描述与实际情况的一致性
- 代码质量与 commit 历史

#### 维度 C: 学校/项目背景（来自学校分析报告）
- 学校在该领域的声誉
- 专业课程设置与 JD 的匹配度
- 学校的研究方向与 JD 的契合度

### Step 5: 三档结论判定

#### 直接通过 ✅
**条件（需同时满足）**：
1. 所有硬性门槛全部达标
2. 链接验证无严重红旗（无🚩🚩级别）
3. 简历描述与实际情况基本一致
4. 研究方向与 JD 有 2+ 个强匹配
5. 学校背景与 JD 要求匹配

**行动**：进入下一轮面试安排

#### 可以考虑 🔶
**条件（满足以下任一）**：
1. 硬性门槛基本达标但有 1-2 项较弱（如 GPA 略低但项目经验丰富）
2. 链接验证有 🚩 级别红旗但可解释（如 fork 但标注了来源）
3. 研究方向有 1 个强匹配 + 若干弱匹配
4. 学校背景一般但个人项目突出
5. 简历有夸大但核心能力真实

**行动**：建议面试进一步验证，标注需要重点追问的疑点

#### 不能通过 ❌
**条件（满足以下任一）**：
1. 硬性门槛不达标（专业不相关、无 Python 能力等）
2. 链接验证有 🚩🚩 级别严重红旗（简历严重造假）
3. 多个链接 404 或无法验证
4. 研究方向与 JD 完全不匹配
5. 学校/专业与 JD 要求差距过大且无相关项目经验弥补

**行动**：拒绝，可附反馈理由

### Step 6: 输出结构化报告

使用 `templates/stage1-screening-report.md` 生成最终报告。

**存储路径规则**：
- **学校项目分析报告** 保存在 `reports/{学校名}/{专业名}.md`（由 `university-program-research` skill 生成）
- **链接验证报告** 保存在 `candidates/{id}/link-verification.md`
- **Stage 1 最终筛选报告** 保存在两个位置：
  1. `reports/{候选人姓名}/stage1-screening.md`（工作区存档）
  2. `candidates/{id}/stage1-screening.md`（CVScreeningAgent pipeline 输出）
- 使用 `terminal` 的 `copy` 命令（Windows）或 `cp`（Linux/Mac）将报告从工作区复制到 candidates 目录

## 判定决策树

```
开始
├─ 硬性门槛全部达标？
│  ├─ 否 → ❌ 不能通过（说明不达标的项）
│  └─ 是 → 继续
│
├─ 链接验证有 🚩🚩 严重红旗？
│  ├─ 是 → ❌ 不能通过（说明造假/夸大证据）
│  └─ 否 → 继续
│
├─ 研究方向有 2+ 强匹配？
│  ├─ 是 → 继续
│  └─ 否 → 继续（看综合）
│
├─ 链接验证有 🚩 级别红旗？
│  ├─ 是 → 🔶 可以考虑（标注疑点）
│  └─ 否 → 继续
│
├─ 学校背景与 JD 匹配？
│  ├─ 是 → ✅ 直接通过
│  └─ 否 → 🔶 可以考虑（看项目经验是否弥补）
│
└─ 输出结论
```

## 注意事项

1. **不要只看学校名气** — 名校生也可能造假，普通学校也可能有优秀候选人。以事实和代码为依据。
2. **区分"不会"和"造假"** — 技能不匹配 ≠ 简历造假。前者是可以培养的，后者是诚信问题。
3. **红旗信号要量化** — 不要说"有点可疑"，要说"73个commit全部是'update'，集中在两个时间点"。
4. **绿旗信号也要记录** — 即使最终结论是不能通过，也要记录候选人的亮点，便于未来其他岗位考虑。
5. **JD 的硬性门槛和偏好方向要分开** — 专业和 Python 是硬性门槛，GNN 经验是偏好方向，权重不同。
6. **时间线合理性检查** — 注意实习时间与学业时间是否重叠、项目时间是否合理。
7. **结论要明确** — 不要模棱两可。直接通过/可以考虑/不能通过，三选一。
8. **给出 actionable 的建议** — 如果是"可以考虑"，要明确说面试时重点问什么。

## References

- `templates/stage1-screening-report.md` — 最终报告模板
- 上游 skill: `hr-recruitment/cv-link-deep-research` — 链接验证报告
- 上游 skill: `research/university-program-research` — 学校项目调研报告
- 通用 skill: `utilities/windows-file-operations` — Windows 文件操作最佳实践（文件读取优先级、编码处理等）
