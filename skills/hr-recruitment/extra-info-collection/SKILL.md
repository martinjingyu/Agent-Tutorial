---
name: extra-info-collection
category: hr-recruitment
description: 收集候选人额外信息（如 GitHub 活跃度、LinkedIn 背景、竞赛详情等），补充到 candidates/{候选人姓名}/ 下。
---

# extra-info-collection — 额外信息收集

## 何时使用

当 Kanban pipeline 的 `extra-info` task 被调度时使用。本 skill 指导 agent 如何收集候选人的额外信息，补充已有的分析。

## 输入

从 task prompt 中获取：
- **候选人姓名**
- **候选人文件夹**（如 `candidates/Lei Shen/`）

从 `candidates/{候选人姓名}/profile.json` 读取：
- `candidate.links[]` — 候选人链接列表

## 工作流程

### Step 1: 读取输入

1. 使用 `read_file` 读取 `candidates/{候选人姓名}/profile.json`
2. 提取所有链接
3. 读取已有的分析报告，了解已覆盖的内容

### Step 2: 收集额外信息

根据已有分析报告的覆盖情况，收集以下额外信息：

1. **GitHub 活跃度**（如未在 project-awards 中详细分析）：
   - 总 stars / forks
   - 近 6 个月提交频率
   - 参与的开源项目
   - 代码质量（README, 文档, 测试）

2. **LinkedIn 背景**（如可访问）：
   - 技能认可
   - 推荐信
   - 人脉网络
   - 与简历的一致性

3. **Kaggle / 竞赛平台**（如有）：
   - 排名
   - 参赛记录
   - 获奖情况

4. **个人博客/技术文章**（如有）：
   - 技术深度
   - 写作能力
   - 知识分享

5. **其他公开信息**：
   - 知乎/CSDN 等技术社区
   - 学术主页
   - 推荐信（如有）

### Step 3: 综合评估

将额外信息与已有分析进行交叉验证：
- 是否有矛盾之处？
- 是否有新的发现？
- 是否有红旗/绿旗信号？

### Step 4: 输出文件

**`candidates/{候选人姓名}/extra-info.md`** — 额外信息收集报告

```markdown
# 额外信息收集报告

候选人: {姓名}

## GitHub 活跃度
- 总 stars: {count}
- 近 6 个月提交: {count}
- 主要项目: {projects}
- 评估: {assessment}

## LinkedIn 背景
- 技能认可: {skills}
- 与简历一致性: ✅/⚠️/❌
- 评估: {assessment}

## 其他信息
- {other_info}

## 交叉验证
- 与已有分析的一致性: ✅/⚠️/❌
- 新发现: {findings}
- 红旗/绿旗信号: {signals}

## 面试追问建议
- {questions}
```

### Step 5: 完成

调用 `respond_to_user` 报告完成状态。

## 注意事项

1. **不要重复已有分析** — 先阅读已有的报告，只收集尚未覆盖的信息
2. **LinkedIn 可能无法直接访问** — 标注"访问受限"即可
3. **GitHub 活跃度是重要指标** — 即使项目不多，持续的贡献也值得关注
4. **交叉验证是关键** — 不同来源的信息应该一致，矛盾是红旗信号

## References

- `hr-recruitment/cv-link-deep-research` — 链接深度调研
- `utilities/windows-file-operations` — Windows 文件操作最佳实践
