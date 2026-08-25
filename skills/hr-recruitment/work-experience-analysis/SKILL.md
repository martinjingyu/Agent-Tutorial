---
name: work-experience-analysis
category: hr-recruitment
description: 基于 profile.json 中的工作经历信息，使用浏览器验证公司背景和候选人描述的真实性，输出 work-experience.md 到 candidates/{候选人姓名}/ 下。
---

# work-experience-analysis — 工作经历分析

## 何时使用

当 Kanban pipeline 的 `work-experience` task 被调度时使用。本 skill 指导 agent 如何验证和分析候选人的工作经历。

## 输入

从 task prompt 中获取：
- **候选人姓名**
- **候选人文件夹**（如 `candidates/Lei Shen/`）

从 `candidates/{候选人姓名}/profile.json` 读取：
- `work_experience[]` — 工作经历列表

## 工作流程

### Step 1: 读取输入

1. 使用 `read_file` 读取 `candidates/{候选人姓名}/profile.json`
2. 提取 `work_experience[]` 数组
3. 如数组为空或不存在，直接输出 valid skip 报告

### Step 2: 逐一验证工作经历

对每段工作经历：

1. **验证公司背景**：
   - 使用 `google_search` 或 `bing_search` 搜索公司信息
   - 确认公司真实存在
   - 了解公司规模、业务方向、行业地位
   - 如果是知名公司（如字节跳动、腾讯、Google等），确认候选人所在部门/团队

2. **验证岗位描述**：
   - 搜索该岗位的典型职责
   - 评估候选人描述的技术栈是否合理
   - 评估候选人描述的贡献是否可信（实习生通常不会独立负责核心模块）

3. **验证时间线**：
   - 检查时间线是否合理（如大二暑假实习、大三寒假实习等）
   - 检查是否有时间重叠
   - 检查是否有不合理的长/短时间

### Step 3: 综合评估

| 评估维度 | 评分 | 说明 |
|---------|:----:|------|
| 公司质量 | ⭐/⭐⭐/⭐⭐⭐ | 大厂/知名/普通 |
| 岗位匹配度 | ⭐/⭐⭐/⭐⭐⭐ | 与 JD 的匹配程度 |
| 描述可信度 | ✅/⚠️/❌ | 描述是否合理 |
| 时间线合理性 | ✅/⚠️/❌ | 是否有矛盾 |
| 技术栈匹配 | ✅/⚠️/❌ | 与 JD 要求的技术栈 |

### Step 4: 输出文件

**`candidates/{候选人姓名}/work-experience.md`** — 工作经历分析报告

```markdown
# 工作经历分析报告

候选人: {姓名}

## 总览
- 工作/实习经历数量: {count}
- 整体评估: {summary}

## 各段经历详细分析

### 1. {公司} - {岗位}
- **时间**: {start_date} ~ {end_date}
- **公司背景**: {company_info}
- **岗位描述验证**: {verification}
- **技术栈匹配**: ✅/⚠️/❌
- **描述可信度**: ✅/⚠️/❌
- **时间线合理性**: ✅/⚠️/❌
- **与 JD 匹配度**: ⭐/⭐⭐/⭐⭐⭐
- **详细分析**: {analysis}

### 2. ...

## 综合评估
- 工作经历质量: {assessment}
- 红旗/绿旗信号
- 面试追问建议
```

### Step 5: 完成

调用 `respond_to_user` 报告完成状态。

## 注意事项

1. **无工作经历是 valid skip，不是 error**
2. **实习生的工作描述通常比较基础** — 如果描述过于夸大（如"独立设计并实现了核心算法"），标记为红旗信号
3. **关注技术栈匹配度** — 即使公司不大，如果技术栈与 JD 高度匹配，也是加分项
4. **时间线矛盾是红旗信号** — 如两段实习时间重叠，或实习时间与学业时间冲突
5. **公司背景调研** — 小公司可能没有公开信息，标注"信息有限"即可

## References

- `utilities/windows-file-operations` — Windows 文件操作最佳实践
