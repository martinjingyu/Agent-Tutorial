# 📋 Stage 1 简历初筛最终报告

> **候选人**: {name}
> **应聘职位**: AI Research & Engineering Intern（AI算法实习生）
> **筛选日期**: {date}
> **数据来源**: profile.json + link-verification.md + 学校项目分析报告 + JD
> **存储路径**: `candidates/{name}/stage1-screening.md`（所有候选人报告统一保存在 candidates/ 下）

---

## 一、候选人画像

| 项目 | 详情 |
|------|------|
| **姓名** | {name} |
| **当前教育** | {institution} · {major} · {degree} · GPA {gpa}/{scale} |
| **过往教育** | {previous_institution} · {major} · GPA {gpa}/{scale} |
| **语言成绩** | {language_scores} |
| **实习经历** | {count} 段：{company_list} |
| **项目经历** | {count} 个：{project_list} |
| **论文/报告** | {count} 篇 |
| **核心技能域** | {skill_areas} |
| **链接验证可信度** | {trust_score}/5 |

---

## 二、JD 匹配度矩阵

### 2.1 硬性门槛（必须满足）

| # | JD 要求 | 候选人情况 | 匹配度 | 证据来源 |
|---|---------|-----------|:-----:|---------|
| 1 | 专业：AI/CS/软件工程类 | {major} | {match} | profile.json |
| 2 | 在校成绩前 10% | GPA {value}/{scale} | {match} | profile.json |
| 3 | 熟练掌握 Python | {evidence} | {match} | profile.json + link-verification |
| 4 | 熟悉至少一款主流大模型 | {evidence} | {match} | profile.json + link-verification |
| 5 | 热爱AI，不惧怕学习新技术 | {evidence} | {match} | 综合判断 |

### 2.2 研究方向偏好（加分项）

| # | JD 研究方向 | 候选人相关经验 | 匹配度 |
|---|------------|--------------|:-----:|
| 1 | Fine-tuning / Post-pretraining | {experience} | {match} |
| 2 | Domain Specific Chatbot / RAG | {experience} | {match} |
| 3 | Knowledge Graph / GraphRAG | {experience} | {match} |
| 4 | GNN / GCN / GAT | {experience} | {match} |
| 5 | Multi-agent System (MAS) | {experience} | {match} |
| 6 | LLM Safety / Red Teaming | {experience} | {match} |
| 7 | AI Native Frontend/Backend | {experience} | {match} |

### 2.3 软性素质（参考项）

| # | 考察项 | 候选人表现 | 评估 |
|---|--------|-----------|:----:|
| 1 | 独立负责项目的能力 | {evidence} | {match} |
| 2 | 学习新技术的能力 | {evidence} | {match} |
| 3 | 解决复杂问题的能力 | {evidence} | {match} |

---

## 三、三维度综合评估

### 维度 A: 硬性条件

**评分**: ⭐⭐⭐⭐⭐ / 5

**优势**:
- ✅ {strength_1}
- ✅ {strength_2}

**不足**:
- ⚠️ {weakness_1}
- ⚠️ {weakness_2}

### 维度 B: 真实性/可信度

**评分**: ⭐⭐⭐⭐⭐ / 5

**绿旗信号**:
- ✅ {green_flag_1}
- ✅ {green_flag_2}

**红旗信号**:
- 🚩 {red_flag_1}
- 🚩 {red_flag_2}

### 维度 C: 学校/项目背景

**评分**: ⭐⭐⭐⭐⭐ / 5

**匹配点**:
- ✅ {match_point_1}
- ✅ {match_point_2}

**差距**:
- ⚠️ {gap_1}
- ⚠️ {gap_2}

---

## 四、最终结论

### 判定：✅ 直接通过 / 🔶 可以考虑 / ❌ 不能通过

**判定理由**：

{reasoning_paragraph}

### 关键决策因素

| 因素 | 评估 | 权重 |
|------|:----:|:----:|
| 硬性门槛达标 | ✅/⚠️/❌ | 高 |
| 无严重造假信号 | ✅/⚠️/❌ | 高 |
| 研究方向匹配 | ✅/⚠️/❌ | 中 |
| 学校背景匹配 | ✅/⚠️/❌ | 中 |
| 项目经验质量 | ✅/⚠️/❌ | 中 |
| 链接验证可信度 | ✅/⚠️/❌ | 高 |

---

## 五、面试建议

### 建议追问的方向（按优先级排序）

1. **{topic_1}** — {reasoning}
   - 追问问题：{questions}

2. **{topic_2}** — {reasoning}
   - 追问问题：{questions}

3. **{topic_3}** — {reasoning}
   - 追问问题：{questions}

### 需要验证的疑点

- [ ] {doubt_1}
- [ ] {doubt_2}
- [ ] {doubt_3}

### 面试建议总结

{interview_advice}

---

## 六、信息来源

| 材料 | 路径 | 日期 |
|------|------|------|
| 简历解析数据 | `candidates/{name}/profile.json` | {date} |
| 链接验证报告 | `candidates/{name}/link-verification.md` | {date} |
| 学校项目分析报告 | `reports/{学校名}/{专业名}.md` | {date} |
| 职位描述 JD | `{jd_path}` | {date} |

---

*本报告由 stage1-screening-report skill 自动生成。结论基于三份输入材料的综合分析，仅供参考。*
