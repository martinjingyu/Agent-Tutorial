---
name: idea-deep-research
description: Deep research on academic papers, research ideas, or technical topics using browser navigation, PDF reading, and Kanban-based task orchestration. Produces structured research reports with verified findings.
category: research
---

# Idea Deep Research

## 何时使用

当需要对一个学术论文、研究想法、技术主题或创新概念进行深度调研时使用。本 skill 将调研过程拆分为多个 Kanban task，每个 task 由 agent 自己 agentic 地完成。

**典型场景**：
- 调研一篇论文（如 Re-ReST、Self-Training 等）的核心方法、实验设置、代码可用性
- 调研一个研究方向的多个相关工作，对比分析
- 调研一个技术概念（如 CDP、Accessibility API）的原理、实现和最佳实践

## 核心原则

1. **浏览器优先** — 使用 `browser_navigate` 获取论文页面（arXiv、OpenReview、ACL Anthology 等），使用 `read_url_pdf` 获取 PDF 内容
2. **研究笔记压缩** — 每次浏览器/PDF 读取后，使用 `save_research_notes` 将关键发现压缩为简洁要点，避免上下文膨胀
3. **Kanban 编排** — 对于多篇论文或多维度的调研，使用 Kanban board 编排并行/串行任务
4. **源交叉验证** — 同一信息至少从两个独立来源验证（如论文页面 + 官方代码仓库 + 第三方解读）
5. **结构化输出** — 最终产出结构化的 Markdown 研究报告，包含方法对比、实验分析、代码可用性等

## 调研流程

### 单篇论文调研（简单模式）

当只需要调研一篇论文时，直接使用工具链：

```
1. browser_navigate → 论文页面（arXiv/OpenReview/ACL Anthology）
2. 如页面内容不足 → browser_scroll + browser_snapshot（full mode）
3. read_url_pdf → 获取 PDF 全文
4. save_research_notes → 压缩关键发现
5. 重复步骤 1-4 获取补充资料（代码仓库、官方博客等）
6. 输出结构化研究报告
```

### 多篇论文/多维度调研（Kanban 模式）

当需要调研多篇论文或多个维度时，使用 Kanban board 编排：

#### Board 命名

```text
idea-<研究主题或项目标识>
```

示例：
```text
idea-a-deep-research
idea-self-training-survey
```

#### Task 依赖图

```
paper-<论文简称> (调研单篇论文)
    ├── code-<论文简称> (调研代码实现，可选)
    ├── related-<论文简称> (调研相关工作，可选)
    └── comparison (对比分析，依赖所有 paper-* tasks)
```

#### 创建 Pipeline 的模板

```json
{
  "board": "idea-{研究主题}",
  "tasks": [
    {
      "id": "paper-{论文简称1}",
      "title": "调研论文: {论文全称}",
      "prompt": "请深度调研论文 {论文全称}：\n1. 使用 browser_navigate 打开论文页面（arXiv/OpenReview 等）\n2. 使用 read_url_pdf 获取 PDF 全文\n3. 使用 save_research_notes 压缩关键发现\n4. 提取：核心方法、创新点、实验设置、主要结果、局限性\n5. 输出到 reports/{研究主题}/paper-{论文简称1}.md"
    },
    {
      "id": "paper-{论文简称2}",
      "title": "调研论文: {论文全称2}",
      "prompt": "请深度调研论文 {论文全称2}：\n1. 使用 browser_navigate 打开论文页面\n2. 使用 read_url_pdf 获取 PDF 全文\n3. 使用 save_research_notes 压缩关键发现\n4. 提取：核心方法、创新点、实验设置、主要结果、局限性\n5. 输出到 reports/{研究主题}/paper-{论文简称2}.md"
    },
    {
      "id": "comparison",
      "title": "对比分析所有论文",
      "depends_on": ["paper-{论文简称1}", "paper-{论文简称2}"],
      "prompt": "请对比分析 reports/{研究主题}/ 下的所有论文调研报告：\n1. 读取各 paper-*.md 文件\n2. 构建对比矩阵（方法、数据集、指标、结果）\n3. 分析各方法的优缺点和适用场景\n4. 输出 reports/{研究主题}/comparison.md"
    }
  ]
}
```

#### 调度模式

```json
{"board": "idea-{研究主题}", "max_spawn": 2}
```

建议并发度：
- `max_spawn=2` — paper-* tasks 可并行调研
- `max_spawn=1` — 如果浏览器登录状态脆弱或需要共享会话

## 浏览器调研技巧

### 论文页面调研

| 来源 | URL 模式 | 注意事项 |
|------|----------|----------|
| arXiv | arxiv.org/abs/{ID} | 摘要页包含核心信息；PDF 在 arxiv.org/pdf/{ID} |
| OpenReview | openreview.net/forum?id={ID} | 包含审稿意见和作者回复 |
| ACL Anthology | aclanthology.org/{ID} | 包含 PDF 和 BibTeX |
| Semantic Scholar | semanticscholar.org/paper/{ID} | 包含引用关系和影响力指标 |
| Papers With Code | paperswithcode.com/paper/{ID} | 包含代码链接和基准测试结果 |

### PDF 内容获取

使用 `read_url_pdf` 工具直接获取 PDF 文本内容：
```
read_url_pdf(url="https://arxiv.org/pdf/2406.12345.pdf")
```

注意：PDF 内容可能很大，读取后立即使用 `save_research_notes` 压缩。

### 内容隐藏处理

如果 `browser_navigate` 返回的页面内容不完整（如 tab 面板、折叠内容）：

```
1. browser_navigate → 打开页面
2. 如果主要内容缺失 → browser_scroll(direction="down", pixels=800)
3. browser_snapshot → 获取完整快照（full mode 可揭示隐藏内容）
```

## 研究笔记压缩

每次浏览器/PDF 读取后，使用 `save_research_notes` 压缩关键发现：

```
save_research_notes(
    notes="## Key Findings\n\n### Paper: {标题}\n- Core method: ...\n- Key innovation: ...\n- Experimental setup: ...\n- Main results: ...\n- Code available: Yes/No at {URL}\n- Limitations: ..."
)
```

## 输出规范

所有输出文件统一保存在 `reports/{研究主题}/` 下：

| 文件 | 内容 |
|------|------|
| `reports/{研究主题}/paper-{简称}.md` | 单篇论文调研报告 |
| `reports/{研究主题}/code-{简称}.md` | 代码实现调研（可选） |
| `reports/{研究主题}/comparison.md` | 多篇论文对比分析 |
| `reports/{研究主题}/final-report.md` | 综合研究报告 |

### 单篇论文调研报告模板

```markdown
# 论文调研: {论文全称}

## 基本信息
- **作者**: {作者列表}
- **发表**: {会议/期刊, 年份}
- **链接**: {论文链接}
- **代码**: {代码链接或无}

## 核心方法
{方法描述}

## 创新点
1. {创新点1}
2. {创新点2}

## 实验设置
- **数据集**: {数据集列表}
- **基线**: {基线方法}
- **评价指标**: {指标列表}

## 主要结果
{关键结果表格或描述}

## 局限性
{局限性分析}

## 与需求的匹配度
{如用于招聘场景，评估与需求的匹配度}
```

## 注意事项

1. **不要一次性加载过多 PDF** — 每个 PDF 读取后立即压缩，避免上下文膨胀
2. **验证代码可用性** — 如果论文声称有开源代码，使用 `browser_navigate` 验证仓库是否存在、是否活跃
3. **交叉验证** — 同一信息至少从两个独立来源验证
4. **Kanban 通信** — 参考 `cv-screening-kanban` skill 的 `references/kanban-workflow-communication.md` 中的用户沟通模式
5. **文件路径** — 使用 `reports/{研究主题}/` 作为统一输出目录

## References

- `cv-screening-kanban` — Kanban 编排模式（通信模式、调度模式可复用）
- `cv-screening-kanban/references/kanban-workflow-communication.md` — Kanban 工作流用户沟通指南
- `utilities/windows-file-operations` — Windows 文件操作最佳实践
- `utilities/context-management` — 上下文管理最佳实践（含 save_research_notes 使用指导）
