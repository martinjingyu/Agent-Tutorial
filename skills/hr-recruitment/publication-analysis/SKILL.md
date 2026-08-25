---
name: publication-analysis
category: hr-recruitment
description: 基于 profile.json 中的论文/出版物列表，使用浏览器逐一验证真实性，评估学术贡献度，输出 publications.md 到 candidates/{候选人姓名}/ 下。
---

# publication-analysis — 论文/出版物分析

## 何时使用

当 Kanban pipeline 的 `publication` task 被调度时使用。本 skill 指导 agent 如何验证和分析候选人的学术出版物。

## 输入

从 task prompt 中获取：
- **候选人姓名**
- **候选人文件夹**（如 `candidates/Lei Shen/`）

从 `candidates/{候选人姓名}/profile.json` 读取：
- `publications_or_reports[]` — 论文/出版物列表

## 工作流程

### Step 1: 读取输入

1. 使用 `read_file` 读取 `candidates/{候选人姓名}/profile.json`
2. 提取 `publications_or_reports[]` 数组
3. 如数组为空或不存在，直接输出 valid skip 报告

### Step 2: 逐一验证论文

对每篇论文：

1. **访问论文页面**：使用 `browser_navigate` 访问论文链接
2. **验证基本信息**：
   - 标题是否匹配
   - 作者列表中是否有候选人
   - 候选人排第几作者（第1 > 第2 > 第3+）
   - 发表会议/期刊名称
   - 发表年份
3. **评估会议/期刊级别**：
   - 顶会/顶刊（如 NeurIPS, ICML, CVPR, ACL, AAAI 等）
   - 知名会议/期刊
   - Workshop / Challenge proceedings
   - 预印本（arXiv 等）
   - 未发表/在投
4. **下载 PDF 并阅读**（如可获取）：
   - 候选人负责什么模块？
   - 与简历描述是否一致？
   - 论文描述的系统是否有对应 GitHub 仓库？

### Step 3: 综合评估

| 评估维度 | 评分 | 说明 |
|---------|:----:|------|
| 论文数量 | ⭐/⭐⭐/⭐⭐⭐ | 数量 vs 质量 |
| 发表级别 | ⭐/⭐⭐/⭐⭐⭐ | 顶会/知名/普通 |
| 候选人贡献 | ⭐/⭐⭐/⭐⭐⭐ | 作者排名 + 实际贡献 |
| 与简历一致性 | ✅/⚠️/❌ | 简历描述 vs 实际情况 |
| 与代码对应 | ✅/⚠️/❌ | 论文系统 vs GitHub 代码 |

### Step 4: 输出文件

**`candidates/{候选人姓名}/publications.md`** — 论文分析报告

报告结构：
```markdown
# 论文/出版物分析报告

候选人: {姓名}

## 总览
- 论文总数: {count}
- 有实质贡献的论文: {count}
- 整体评估: {summary}

## 各论文详细分析

### 1. {论文标题}
- **链接**: {url}
- **状态**: ✅ 真实 / ⚠️ 部分匹配 / ❌ 不可达
- **发表会议**: {venue}
- **会议级别**: 顶会 / 知名 / Workshop / 预印本
- **作者列表**: {authors}
- **候选人排名**: 第 N 作者
- **与简历一致性**: ✅/⚠️/❌
- **PDF 阅读发现**: {findings}
- **与代码对应**: {code_correlation}

### 2. ...

## 综合评估
- 学术产出质量: {assessment}
- 红旗/绿旗信号
- 面试追问建议
```

### Step 5: 完成

调用 `respond_to_user` 报告完成状态。

## 注意事项

1. **无论文是 valid skip，不是 error** — 直接输出说明即可
2. **区分论文级别**：Challenge proceedings ≠ 顶会论文
3. **作者排名很重要**：第1作者 > 第2作者 > 第3+，通讯作者也加分
4. **arXiv 预印本**：标注为预印本，但如果有后续发表信息则更新
5. **PDF 阅读**：如果 PDF 可获取，务必阅读并提取关键信息
6. **论文与代码的对应**：论文描述的系统如果有 GitHub 仓库，检查代码是否真实实现了论文方法

## References

- `hr-recruitment/cv-link-deep-research` — 链接深度调研（含论文验证清单）
- `utilities/windows-file-operations` — Windows 文件操作最佳实践
