---
name: ingest-profile
category: hr-recruitment
description: 解析候选人简历文件（.docx/.pdf/.txt），提取结构化信息并输出 profile.json 和 profile-summary.md 到 candidates/{候选人姓名}/ 下。
---

# ingest-profile — 简历解析与结构化

## 何时使用

当 Kanban pipeline 的 `ingest-profile` task 被调度时使用。本 skill 指导 agent 如何从简历文件中提取结构化信息。

## 工作流程

### Step 1: 读取简历文件

从 task prompt 中获取：
- **候选人姓名**（如 "Lei Shen"）
- **简历文件路径**（如 `C:\Users\LX034\Code\简历.docx`）
- **候选人文件夹**（如 `candidates/Lei Shen/`）

使用 `read_file` 读取简历文件。支持 .docx（原生支持）、.txt、.pdf 格式。

### Step 2: 提取结构化信息

从简历中提取以下信息，组织成 JSON 格式：

```json
{
  "candidate": {
    "name": "候选人姓名（中英文）",
    "emails": ["邮箱地址"],
    "links": [
      {"type": "github", "url": "https://github.com/...", "label": "GitHub"},
      {"type": "linkedin", "url": "https://linkedin.com/in/...", "label": "LinkedIn"}
    ]
  },
  "education": [
    {
      "institution": "学校全名",
      "major": "专业名称",
      "degree": "学士/硕士/博士",
      "gpa": "3.8/4.0",
      "gpa_scale": 4.0,
      "ranking": "前10% 或 具体排名",
      "ranking_description": "排名描述原文",
      "courses": ["相关课程1", "相关课程2"],
      "start_date": "2021-09",
      "end_date": "2025-06（或 至今）"
    }
  ],
  "work_experience": [
    {
      "company": "公司名称",
      "position": "岗位名称",
      "location": "地点",
      "start_date": "2024-06",
      "end_date": "2024-09",
      "description": "工作描述",
      "highlights": ["亮点1", "亮点2"],
      "tech_stack": ["Python", "PyTorch"]
    }
  ],
  "projects": [
    {
      "name": "项目名称",
      "description": "项目描述",
      "contributions": ["贡献1", "贡献2"],
      "tech_stack": ["技术1", "技术2"],
      "links": ["https://github.com/...", "https://..."]
    }
  ],
  "publications_or_reports": [
    {
      "title": "论文标题",
      "authors": ["作者列表"],
      "venue_or_context": "会议/期刊名称",
      "link": "https://...",
      "peer_reviewed": true,
      "candidate_position": "第1作者/第2作者/..."
    }
  ],
  "skills": {
    "编程语言": ["Python", "C++", "Java"],
    "框架/库": ["PyTorch", "TensorFlow", "Transformers"],
    "工具": ["Git", "Docker", "Linux"],
    "语言": ["中文（母语）", "英语（IELTS 7.0）"]
  },
  "awards": [
    {
      "name": "奖项名称",
      "level": "国家级/省级/校级",
      "date": "2024"
    }
  ],
  "languages": [
    {"name": "英语", "score": "IELTS 7.0", "date": "2024-08"}
  ]
}
```

### Step 3: 输出文件

1. **`candidates/{候选人姓名}/profile.json`** — 结构化 JSON 数据
   - 使用 `write_file` 写入
   - 确保 JSON 格式正确、可解析

2. **`candidates/{候选人姓名}/profile-summary.md`**（可选）— 简历摘要
   - Markdown 格式
   - 包含关键信息的表格摘要
   - 便于后续 task 快速浏览

### Step 4: 完成

调用 `respond_to_user` 报告完成状态。

## 注意事项

1. **字段完整性**：尽量提取所有字段，缺失的字段用 `null` 或空数组 `[]`，不要省略
2. **GPA 标准化**：统一使用 `X.X/4.0` 格式，如果原始是百分制，转换为 4.0 制
3. **日期格式**：统一使用 `YYYY-MM` 格式
4. **链接去重**：同一个 URL 出现在多个位置时，只在最相关的位置保留
5. **中英文双语**：候选人姓名保留中英文，学校/公司名称使用官方名称
6. **技能分类**：将技能按类别分组（编程语言、框架、工具、语言），不要平铺

## References

- `utilities/windows-file-operations` — Windows 文件操作最佳实践
