# 📋 候选人链接验证报告

> **候选人**: Jingyu Huang (martinjingyu)
> **应聘职位**: AI算法实习生
> **调研日期**: 2026-05-25
> **存储路径**: `C:\Users\LX034\Code\CVScreeningAgent\ScreeningPipeline\candidates\1\link-verification.md`

### 候选人背景摘要

| 项目 | 详情 |
|------|------|
| **教育** | UW-Madison BS CS (2024-今, GPA 4.0/4.0) + 北邮 电信管理 BS (2021-2024, GPA 3.72/4.0) |
| **GPA** | UW-Madison: 4.0/4.0 (满分) |
| **相关经历** | 3段研究实习: Columbia SecureFinAI Lab (RAG/金融), SafoLab (LLM安全/红队), Gamma Lab (图学习) |
| **技能领域** | LLM Agents, RL, AI Safety, Multi-turn Reasoning, RAG, Adversarial Testing, Red Teaming |

---

## 一、链接清单总览

| # | 类型 | URL | 状态 | 简要结论 |
|---|------|-----|:----:|---------|
| 1 | linkedin | https://www.linkedin.com/in/jingyu-huang-44a5a3346/ | ⚠️ | 需要登录，无法直接验证内容 |
| 2 | github | https://github.com/martinjingyu | ✅ | GitHub Profile 活跃，42个仓库 |
| 3 | paper | https://www.amazon.science/nova-ai-challenge/proceedings/stepwise-multi-turn-jailbreak-attacks-on-code-llms-via-task-decomposition-and-test-time-scaling | ✅ | Amazon Science 正式发表的技术报告 |
| 4 | github | https://github.com/martinjingyu/MultiTurn-JailBreak-Agent | ✅ | 实际仓库 Multi-Turn-Jailbreaker，73 commits |
| 5 | github | https://github.com/martinjingyu/KaggleChallenge | ✅ | 54 commits，含竞赛数据 |
| 6 | kaggle | https://www.kaggle.com/competitions/openai-gpt-oss-20b-red-teaming/writeups/SafoLab-red-teaming-challenge | ✅ | Kaggle Writeup，详细技术报告 |
| 7 | github | https://github.com/martinjingyu/emir-specific-rag | ✅ | FINOS 项目 fork，有实际贡献 |
| 8 | github | https://github.com/martinjingyu/savewise | ✅ | 112 commits，Kotlin Android 项目 |

---

## 二、各链接详细分析

### 1. [LinkedIn]: https://www.linkedin.com/in/jingyu-huang-44a5a3346/

**状态**: ⚠️ 需要登录

**调研发现**:
- LinkedIn 页面存在但需要登录才能查看完整内容
- 从个人主页 (martinjingyu.github.io) 可确认其教育背景和研究经历与简历一致

**与简历对比**:
- 简历描述: 包含 LinkedIn 链接
- 实际情况: 页面存在但内容不可见
- 一致性: ⚠️ 无法完全验证

---

### 2. [GitHub Profile]: https://github.com/martinjingyu

**状态**: ✅ 正常

**调研发现**:
- 用户名: martinjingyu (ChibiYuu)
- Bio: "Ok, everything's cooked : )"
- 42 个公开仓库，3 followers，3 following
- 近一年 65 contributions
- 个人主页: https://martinjingyu.github.io/ — 包含完整的教育、研究经历、项目列表

**与简历对比**:
- 简历描述: "martinjingyu (https://github.com/martinjingyu)"
- 实际情况: 活跃的 GitHub 账号，项目与简历高度匹配
- 一致性: ✅ 完全一致

---

### 3. [Paper - Amazon Science]: https://www.amazon.science/nova-ai-challenge/proceedings/stepwise-multi-turn-jailbreak-attacks-on-code-llms-via-task-decomposition-and-test-time-scaling

**状态**: ✅ 正常

**调研发现**:
- 标题: "Stepwise multi-turn jailbreak attacks on code LLMs via task decomposition and test-time scaling"
- 机构: University of Wisconsin-Madison
- 年份: 2025
- 会议: Amazon Nova AI Challenge Proceedings
- 截至5月13日，在第二回合竞赛中取得 top performance

**与简历对比**:
- 简历描述: "Built multi-turn jailbreak agent; 1st place (Round 2) and finalist presentation at Amazon Seattle HQ"
- 实际情况: 论文确认了 UW-Madison 归属和 top performance
- 一致性: ✅ 完全一致

---

### 4. [GitHub Repo - Multi-Turn-Jailbreaker]: https://github.com/martinjingyu/MultiTurn-JailBreak-Agent

**状态**: ✅ 正常

**调研发现**:
- 实际仓库: https://github.com/martinjingyu/Multi-Turn-Jailbreaker
- 73 commits，项目结构完整
- 三阶段 pipeline: generate (攻击树) → sft (监督微调) → TreeRPO (GRPO-style RL)
- 使用 Python 3.12, vLLM, PyTorch

**与简历对比**:
- 简历描述: "Implemented modular attacker agents and multi-turn planning strategies"
- 实际情况: 仓库实现了完整的 multi-turn jailbreak pipeline
- 一致性: ✅ 一致，且实际实现比简历描述更丰富

---

### 5. [GitHub Repo - KaggleChallenge]: https://github.com/martinjingyu/KaggleChallenge

**状态**: ✅ 正常

**调研发现**:
- 54 commits，含 SafoLab.findings.1-4.json 数据文件
- 与 Kaggle Writeup 直接关联
- 最后更新: 9 months ago

**与简历对比**:
- 简历描述: "Developed AutoMTCR framework with MCTS-guided search"
- 实际情况: 仓库结构与 AutoMTCR 框架对应
- 一致性: ✅ 一致

---

### 6. [Kaggle Writeup]: https://www.kaggle.com/competitions/openai-gpt-oss-20b-red-teaming/writeups/SafoLab-red-teaming-challenge

**状态**: ✅ 正常

**调研发现**:
- 标题: "AutoMTCR: Red Teaming with LLM-Based Attacker Agents and MCTS Multi-Turn Probing"
- 竞赛: Red-Teaming Challenge - OpenAI gpt-oss-20b
- 日期: Aug 27, 2025
- 详细技术报告

**与简历对比**:
- 简历描述: "Contributed to Kaggle Red Teaming Challenge"
- 实际情况: 详细的竞赛 writeup，方法专业深入
- 一致性: ✅ 完全一致

---

### 7. [GitHub Repo - EMIR Specific RAG]: https://github.com/martinjingyu/emir-specific-rag

**状态**: ✅ 正常

**调研发现**:
- Forked from finos-labs/emir-specific-rag (FINOS 基金会)
- 1 commit ahead of upstream，59 commits total
- 项目结构: benchmarking/, result/EMIR/, script/, src/

**与简历对比**:
- 简历描述: "Developed a RAG system tailored for EMIR regulations in the finance domain"
- 实际情况: FINOS 官方项目 fork，有实际贡献
- 一致性: ✅ 一致

---

### 8. [GitHub Repo - SaveWise]: https://github.com/martinjingyu/savewise

**状态**: ✅ 正常

**调研发现**:
- 112 commits，7 branches
- Kotlin Android 项目
- 功能: 语音输入、月度消费洞察、AI 财务助手
- 技术栈: Android SpeechRecognizer API, Whisper, LLM, Firebase Auth

**与简历对比**:
- 简历描述: "Co-developed a mobile budgeting app with voice recognition and LLM assistant"
- 实际情况: 仓库功能完整，技术栈与描述完全匹配
- 一致性: ✅ 完全一致

---

## 三、交叉验证

| 验证项 | 结果 |
|--------|:----:|
| GitHub 项目与论文描述一致性 | ✅ 论文与 Multi-Turn-Jailbreaker 仓库完全对应 |
| 项目时间线合理性 | ✅ SafoLab → Columbia → 持续项目更新，时间合理 |
| 技能在实际代码中的体现 | ✅ LLM Agents, RL, RAG, Adversarial Testing 均有代码实现 |
| 跨链接信息一致性 | ✅ 个人主页、GitHub、Amazon Science、Kaggle 信息高度一致 |
| LinkedIn 与简历一致性 | ⚠️ LinkedIn 需要登录，无法直接验证 |

---

## 四、综合判断

**整体可信度**: 高

**支持的证据**:
- ✅ GitHub Profile 活跃，42 个仓库，持续贡献
- ✅ Amazon Science 官方发表技术报告
- ✅ Kaggle 官方竞赛 writeup，内容专业
- ✅ 个人主页信息与简历完全一致
- ✅ 所有 GitHub 仓库代码结构完整
- ✅ 跨平台信息高度一致
- ✅ UW-Madison CS GPA 4.0/4.0

**需要警惕的方面**:
- ⚠️ LinkedIn 无法直接验证
- ⚠️ EMIR RAG 为 fork 项目，原创贡献比例需面试中了解
- ⚠️ 部分仓库最后更新较早

---

## 五、面试建议

### 建议重点追问的方向

1. **Multi-Turn Jailbreak 技术细节**: TreeRPO (GRPO-style) 实现，SFT+RL 训练流程，竞赛中的挑战
2. **AutoMTCR 框架设计**: MCTS-guided search 实现，response evaluator 设计，deception/sandbagging 检测
3. **EMIR RAG 系统**: 在 FINOS 项目中的具体贡献，金融领域 regulatory QA 的特殊挑战
4. **SaveWise 语音识别**: Whisper 集成细节，语音到结构化数据的转换 pipeline

### 建议考察的信号

| 信号 | 正面表现 | 负面表现 |
|------|---------|---------|
| LLM 安全理解深度 | 能清晰解释 red teaming 方法论、RLHF 与安全对齐 | 仅停留在调用 API 层面 |
| 工程实现能力 | 能描述代码架构设计、训练 pipeline 的工程挑战 | 对项目代码细节模糊 |
| 研究思维 | 能讨论实验设计、评估指标、结果分析 | 仅关注做了什么而非为什么 |
| 跨领域整合 | 能解释 RAG + 金融领域的特殊考量 | 无法说明金融 RAG 与通用 RAG 的区别 |

---

## 六、信息来源

| 来源 | URL | 日期 |
|------|-----|------|
| GitHub Profile | https://github.com/martinjingyu | 2026-05-25 |
| GitHub Repos | https://github.com/martinjingyu?tab=repositories | 2026-05-25 |
| Multi-Turn-Jailbreaker | https://github.com/martinjingyu/Multi-Turn-Jailbreaker | 2026-05-25 |
| ProfRadar | https://github.com/martinjingyu/ProfRadar | 2026-05-25 |
| KaggleChallenge | https://github.com/martinjingyu/KaggleChallenge | 2026-05-25 |
| savewise | https://github.com/martinjingyu/savewise | 2026-05-25 |
| emir-specific-rag | https://github.com/martinjingyu/emir-specific-rag | 2026-05-25 |
| Amazon Science 论文 | https://www.amazon.science/nova-ai-challenge/proceedings/stepwise-multi-turn-jailbreak-attacks-on-code-llms-via-task-decomposition-and-test-time-scaling | 2026-05-25 |
| Kaggle Writeup | https://www.kaggle.com/competitions/openai-gpt-oss-20b-red-teaming/writeups/SafoLab-red-teaming-challenge | 2026-05-25 |
| 个人主页 | https://martinjingyu.github.io/ | 2026-05-25 |
| LinkedIn | https://www.linkedin.com/in/jingyu-huang-44a5a3346/ | 2026-05-25 (需登录) |

---

*本报告基于浏览器调研编写。LinkedIn 页面需要登录才能查看完整内容。*
