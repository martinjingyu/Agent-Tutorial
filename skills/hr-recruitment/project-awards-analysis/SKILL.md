---
name: project-awards-analysis
category: hr-recruitment
description: 基于 profile.json 中的项目/竞赛/奖项信息，使用浏览器验证真实性，评估与 JD 的匹配度，输出 projects-awards.md 到 candidates/{候选人姓名}/ 下。
---

# project-awards-analysis — 项目/竞赛/奖项分析

## 何时使用

当 Kanban pipeline 的 `project-awards` task 被调度时使用。本 skill 指导 agent 如何验证和分析候选人的项目、竞赛和奖项。

## 输入

从 task prompt 中获取：
- **候选人姓名**
- **候选人文件夹**（如 `candidates/Lei Shen/`）

从 `candidates/{候选人姓名}/profile.json` 读取：
- `projects[]` — 项目列表
- `awards[]` — 奖项列表

## 工作流程

### Step 1: 读取输入

1. 使用 `read_file` 读取 `candidates/{候选人姓名}/profile.json`
2. 提取 `projects[]` 和 `awards[]` 数组
3. 如两者都为空，直接输出 valid skip 报告

### Step 2: 逐一验证项目

对每个项目：

1. **验证项目链接**（如有）：
   - 使用 `browser_navigate` 访问项目链接（GitHub、Demo 等）
   - 检查项目是否真实存在
   - 检查项目的活跃度（stars, commits, last update）
   - 检查候选人的贡献（commits, PRs, issues）

2. **评估项目质量**：
   - 项目复杂度（工具库 vs 完整系统 vs 简单 demo）
   - 技术栈是否与 JD 匹配
   - 项目是否有实际用户/应用场景
   - 代码质量（README, 文档, 测试）

3. **评估候选人贡献**：
   - 候选人描述 vs 实际贡献
   - 是独立完成还是团队协作
   - 候选人在项目中的角色

### Step 3: 验证奖项

对每个奖项：

1. **验证奖项真实性**：
   - 使用 `google_search` 或 `bing_search` 搜索奖项信息
   - 确认奖项确实存在
   - 确认候选人在获奖名单中（如可查）

2. **评估奖项级别**：
   - 国家级/省级/校级
   - 竞赛的知名度和竞争激烈程度
   - 奖项与 AI 领域的相关性

### Step 4: 综合评估

| 评估维度 | 评分 | 说明 |
|---------|:----:|------|
| 项目质量 | ⭐/⭐⭐/⭐⭐⭐ | 复杂度、技术栈、实用性 |
| 项目与 JD 匹配 | ✅/⚠️/❌ | 技术栈和方向 |
| 候选人贡献 | ⭐/⭐⭐/⭐⭐⭐ | 实际参与度 |
| 奖项级别 | ⭐/⭐⭐/⭐⭐⭐ | 国家级/省级/校级 |
| 奖项相关性 | ✅/⚠️/❌ | 与 AI 领域相关度 |

### Step 5: 输出文件

**`candidates/{候选人姓名}/projects-awards.md`** — 项目/竞赛/奖项分析报告

```markdown
# 项目、竞赛与奖项分析报告

候选人: {姓名}

## 总览
- 项目数量: {count}
- 奖项数量: {count}
- 整体评估: {summary}

## 各项目详细分析

### 1. {项目名称}
- **链接**: {url}
- **验证状态**: ✅ 真实 / ⚠️ 部分匹配 / ❌ 不可达
- **技术栈**: {tech_stack}
- **与 JD 匹配度**: ✅/⚠️/❌
- **项目质量**: ⭐/⭐⭐/⭐⭐⭐
- **候选人贡献**: {contribution_assessment}
- **详细分析**: {analysis}

### 2. ...

## 各奖项详细分析

### 1. {奖项名称}
- **级别**: 国家级/省级/校级
- **验证状态**: ✅ 真实 / ⚠️ 部分匹配 / ❌ 不可查
- **与 AI 领域相关度**: ✅/⚠️/❌
- **详细分析**: {analysis}

### 2. ...

## 综合评估
- 项目/竞赛质量: {assessment}
- 红旗/绿旗信号
- 面试追问建议
```

### Step 6: 完成

调用 `respond_to_user` 报告完成状态。

## 注意事项

1. **无项目/奖项是 valid skip，不是 error**
2. **GitHub 项目**：关注 stars, forks, commits, last update, README 质量
3. **竞赛奖项**：区分"参赛奖"（参与就有）和"名次奖"（前几名）
4. **项目与 JD 的技术栈匹配**是核心评估维度
5. **如果项目链接不可访问**，标注为"不可达"，不要强行验证

## References

- `hr-recruitment/cv-link-deep-research` — 链接深度调研
- `utilities/windows-file-operations` — Windows 文件操作最佳实践
