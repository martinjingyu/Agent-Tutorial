# 📋 Stage 1 简历初筛最终报告

> **候选人**: Jingyu Huang
> **应聘职位**: AI Research & Engineering Intern（AI算法实习生）
> **筛选日期**: 2026-05-24
> **数据来源**: stage1_profile.json + link-verification.md + 学校项目分析报告 + JD

---

## 一、候选人画像

| 项目 | 详情 |
|------|------|
| **姓名** | Jingyu Huang |
| **当前教育** | University of Wisconsin - Madison · Computer Science · BS · GPA 4.0/4.0 |
| **过往教育** | Beijing University of Posts and Telecommunications · Telecommunication with Management · BS · GPA 3.72/4.0 |
| **语言成绩** | IELTS 7.0 / TOEFL 95 |
| **实习经历** | 3 段：Columbia University (SecureFinAI Lab) · SafoLab · Gamma Lab |
| **项目经历** | 5 个：Amazon Nova AI Challenge · MultiTurn Jailbreak Agent · Kaggle Redteaming Challenge · EMIR Specific RAG · SaveWise |
| **论文/报告** | 2 篇（均为非 peer-reviewed 竞赛技术报告） |
| **核心技能域** | LLM Agents, AI Safety, Red Teaming, Multi-turn Reasoning, RAG, RL |
| **链接验证可信度** | ⭐⭐⭐/5（有真实能力，但简历存在夸大） |

---

## 二、JD 匹配度矩阵

### 2.1 硬性门槛（必须满足）

| # | JD 要求 | 候选人情况 | 匹配度 | 证据来源 |
|---|---------|-----------|:-----:|---------|
| 1 | 专业：AI/CS/软件工程类 | UW-Madison CS（当前）+ BUPT 通信工程（过往） | ✅ 达标 | profile.json |
| 2 | 在校成绩前 10% | UW-Madison GPA 4.0/4.0（当前），BUPT GPA 3.72/4.0 | ✅ 达标 | profile.json |
| 3 | 熟练掌握 Python | Multi-Turn-Jailbreaker 和 KaggleChallenge 均为 Python 项目，代码质量不错 | ✅ 达标 | profile.json + link-verification |
| 4 | 熟悉至少一款主流大模型 | 项目涉及 GPT, LLM safety, red-teaming，熟悉主流大模型 | ✅ 达标 | profile.json + link-verification |
| 5 | 热爱AI，不惧怕学习新技术 | 从通信工程转到 CS，参与多个 AI 竞赛和实验室，技术栈跨度大 | ✅ 达标 | 综合判断 |

### 2.2 研究方向偏好（加分项）

| # | JD 研究方向 | 候选人相关经验 | 匹配度 |
|---|------------|--------------|:-----:|
| 1 | Fine-tuning / Post-pretraining | Multi-Turn-Jailbreaker 含 SFT + GRPO (TreeRPO) 训练 pipeline | ✅ 强匹配 |
| 2 | Domain Specific Chatbot / RAG | EMIR-specific RAG（但 fork 无贡献，需面试验证） | ⚠️ 待验证 |
| 3 | Knowledge Graph / GraphRAG | 无直接经验 | ❌ 不匹配 |
| 4 | GNN / GCN / GAT | Gamma Lab 实习涉及 HGAT/GammaGL（但 fork 无贡献） | ⚠️ 待验证 |
| 5 | Multi-agent System (MAS) | Multi-Turn-Jailbreaker 含多智能体设计，Kaggle AutoMTCR | ✅ 强匹配 |
| 6 | LLM Safety / Red Teaming | Amazon Nova AI Challenge 第1名，Kaggle Red Teaming Challenge | ✅ 强匹配 |
| 7 | AI Native Frontend/Backend | savewise Android App（Kotlin），非 AI Native | ⚠️ 弱匹配 |

### 2.3 软性素质（参考项）

| # | 考察项 | 候选人表现 | 评估 |
|---|--------|-----------|:----:|
| 1 | 独立负责项目的能力 | Multi-Turn-Jailbreaker 单人项目，代码工程化程度高 | ✅ 达标 |
| 2 | 学习新技术的能力 | 从通信工程转到 CS，快速进入 LLM Safety 领域 | ✅ 达标 |
| 3 | 解决复杂问题的能力 | Amazon Nova AI Challenge 第1名，涉及多轮 jailbreak 攻击 | ✅ 达标 |

---

## 三、三维度综合评估

### 维度 A: 硬性条件

**评分**: ⭐⭐⭐⭐⭐ / 5

**优势**:
- ✅ UW-Madison CS 专业，GPA 4.0/4.0（满分），远超前 10% 要求
- ✅ 3 段研究型实习经历（Columbia, SafoLab, Gamma Lab），与 AI 高度相关
- ✅ Python 项目经验丰富，代码质量经过验证
- ✅ 语言能力优秀（IELTS 7.0, TOEFL 95）

**不足**:
- ⚠️ 当前为本科一年级（2024年9月入学），学业尚浅
- ⚠️ 简历中未列出编程语言技能（programming_languages 为空数组）
- ⚠️ BUPT 专业为"Telecommunication with Management"，非 CS/AI 核心专业

### 维度 B: 真实性/可信度

**评分**: ⭐⭐⭐/5

**绿旗信号**:
- ✅ Amazon Nova AI Challenge 第1名 — 论文页面存在，内容详实
- ✅ Kaggle Writeup 内容详实，技术深度合理
- ✅ savewise 是真实的 Android 项目（112 commits，渐进式开发）
- ✅ Multi-Turn-Jailbreaker 代码质量不错（类型注解、错误处理、工程化结构）

**红旗信号**:
- 🚩🚩 **emir-specific-rag 严重夸大**：简历说"Developed a RAG system"，实际是 fork 自 FINOS Labs 的项目，零代码贡献
- 🚩 Multi-Turn-Jailbreaker commit 历史异常：73 commits 全部 message 为 "update"，集中在两个时间点
- 🚩 KaggleChallenge commit 历史异常：54 commits 全部在一天内，"Initial commit based on that-repo"
- 🚩 GammaGL/HGAT 贡献存疑：简历说 contributed，但 GitHub 只有 fork

### 维度 C: 学校/项目背景

**评分**: ⭐⭐⭐⭐/5

**匹配点**:
- ✅ UW-Madison CS 全美排名前 20（CSRankings ~#12），AI/ML 方向强势
- ✅ UW-Madison 课程涵盖 Machine Learning, Big Data Systems, Intro to AI
- ✅ UW-Madison 有多个知名 AI 实验室（如 Prof. Yin Li, Prof. Sharon Li 等）

**差距**:
- ⚠️ 候选人仅入学 UW-Madison 不到 2 年，课程完成度有限
- ⚠️ BUPT 通信工程专业与 AI 方向关联度一般
- ⚠️ 学校项目分析报告因 API 限制未能完成深度调研

---

## 四、最终结论

### 判定：🔶 可以考虑

**判定理由**：

Jingyu Huang 是一位**有明显潜力但简历存在夸大嫌疑**的候选人。

**支持通过的正面因素**：
1. **硬性条件优秀**：UW-Madison CS 专业 + GPA 4.0/4.0，远超 JD 要求的前 10%
2. **研究方向高度匹配**：LLM Safety / Red Teaming / Multi-agent System 与 JD 的 Fine-tuning、MAS 方向高度契合
3. **竞赛成绩亮眼**：Amazon Nova AI Challenge Round 2 第1名，有实际成果
4. **代码能力真实**：Multi-Turn-Jailbreaker 和 savewise 的代码质量经过验证，是真实的工程能力

**需要警惕的负面因素**：
1. **🚩🚩 emir-specific-rag 严重夸大**：将 fork 项目声称为自己"Developed"的 RAG 系统，这是诚信问题
2. **🚩 commit 历史异常**：多个项目的 commit 模式暗示非渐进式开发，可能是批量提交
3. **🚩 GammaGL/HGAT 贡献无法验证**：简历声称的贡献在 GitHub 上无迹可寻

**综合判断**：候选人有真实的技术能力（尤其在 LLM Safety 领域），但简历存在夸大和包装过度的问题。建议**给予面试机会**，但必须在面试中重点验证疑点。如果面试中能合理解释这些疑点并展示真实能力，可以转为"直接通过"。

### 关键决策因素

| 因素 | 评估 | 权重 |
|------|:----:|:----:|
| 硬性门槛达标 | ✅ 达标 | 高 |
| 无严重造假信号 | ⚠️ 有🚩🚩级别夸大 | 高 |
| 研究方向匹配 | ✅ 强匹配（LLM Safety, MAS） | 中 |
| 学校背景匹配 | ✅ UW-Madison CS 强势 | 中 |
| 项目经验质量 | ✅ 代码真实，工程化程度高 | 中 |
| 链接验证可信度 | ⚠️ 综合 ⭐⭐⭐/5 | 高 |

---

## 五、面试建议

### 建议追问的方向（按优先级排序）

1. **emir-specific-rag / Columbia 实习贡献** 🚩🚩 — 这是最大的诚信疑点
   - "你在 Columbia SecureFinAI Lab 实习期间具体做了什么？GitHub 上 emir-specific-rag 是 fork 自 FINOS Labs 的项目且没有你的代码贡献，能解释一下吗？"
   - "你说的 'Developed a RAG system' 具体指什么？是你在实习期间开发了但未上传到 GitHub 的版本吗？"
   - "VCBench 是什么？你在其中具体设计了什么任务？"

2. **Multi-Turn-Jailbreaker 开发过程** 🚩 — 验证代码是否本人所写
   - "这个项目的 commit message 全部是 'update'，而且集中在两个时间点。能描述一下你的开发过程吗？"
   - "三阶段 pipeline（generate → SFT → TreeRPO）是你独立设计的吗？遇到了什么挑战？"
   - "TreeRPO 和 verl 项目的关系是什么？你在 TreeRPO 中做了什么修改？"

3. **Gamma Lab 实习贡献** 🚩 — 验证另一段声称的贡献
   - "你在 Gamma Lab 期间对 HGAT 算法做了什么改进？有对应的 PR 链接吗？"
   - "GammaGL 库中哪些代码是你写的？"

4. **KaggleChallenge 代码来源** 🔶
   - "commit message 说 'Initial commit based on that-repo'，这个 'that-repo' 是什么？"
   - "AutoMTCR 框架是你独立实现的还是基于现有工作修改的？"

5. **技术深度验证** — 确认真实水平
   - "请解释一下 GRPO 和 PPO 的区别？你为什么选择 GRPO？"
   - "Multi-turn jailbreak 和 single-turn jailbreak 的核心区别是什么？"
   - "你如何评估 red-teaming agent 的有效性？用了什么指标？"

### 需要验证的疑点

- [ ] emir-specific-rag 的实际贡献（可能是 Columbia 实习期间的工作但代码未公开）
- [ ] Gamma Lab 实习期间对 GammaGL/HGAT 的具体贡献（要求提供 PR 链接）
- [ ] Multi-Turn-Jailbreaker 是否本人独立开发（要求现场 coding 或架构讲解）
- [ ] 时间线合理性：BUPT (2021-2024) → UW-Madison (2024-至今)，但 SafoLab 实习 (Aug 2024-Aug 2025) 和 Columbia 实习 (July 2025-Sept 2025) 与学业重叠
- [ ] 简历中未列出编程语言技能（可能只是解析遗漏）

### 面试建议总结

**建议给予面试机会**，但面试官需要：
1. **前半段重点验证疑点**：尤其是 emir-specific-rag 和 GammaGL 的贡献
2. **后半段考察技术深度**：让候选人讲解 Multi-Turn-Jailbreaker 的架构设计，验证是否真正理解
3. **如果疑点得到合理解释** → 可以转为"直接通过"
4. **如果疑点无法解释或发现更多夸大** → 建议拒绝

**面试时长建议**：45-60 分钟（比常规多 15 分钟用于验证疑点）

---

## 六、信息来源

| 材料 | 路径 | 日期 |
|------|------|------|
| 简历解析数据 | `candidates/1/stage1_profile.json` | 2026-05-24 |
| 链接验证报告 | `candidates/1/link-verification.md` | 2026-05-24 |
| 学校项目分析报告 | `candidates/1/stage1_school_major_research/` | 2026-05-25（诊断文件，未完成调研） |
| 职位描述 JD | `reports/AI算法实习生职位JD_20250506.docx` | 2025-05-06 |

---

*本报告由 stage1-screening-report skill 自动生成。结论基于三份输入材料的综合分析，仅供参考。*
