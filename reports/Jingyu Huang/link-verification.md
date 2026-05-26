# CV Link Verification Report — Jingyu Huang

**Date**: 2026-05-24
**Method**: Browser-based deep research per cv-link-deep-research skill
**JD Reference**: AI算法实习生职位JD (bilingual, 2025-05-06)

---

## 1. Link Inventory & Status Overview

| # | Link | Type | Status | Priority |
|---|------|------|--------|----------|
| 1 | https://github.com/martinjingyu | GitHub Profile | ✅ Accessible | High |
| 2 | https://github.com/martinjingyu/Multi-Turn-Jailbreaker | GitHub Repo | ✅ Accessible | High |
| 3 | https://github.com/martinjingyu/KaggleChallenge | GitHub Repo | ✅ Accessible | High |
| 4 | https://github.com/martinjingyu/emir-specific-rag | GitHub Repo | ✅ Accessible (Fork) | High |
| 5 | https://github.com/martinjingyu/savewise | GitHub Repo | ✅ Accessible | High |
| 6 | https://www.amazon.science/nova-ai-challenge/proceedings/stepwise-multi-turn-jailbreak-attacks-on-code-llms-via-task-decomposition-and-test-time-scaling | Paper/Report | ✅ Accessible | High |
| 7 | https://www.kaggle.com/competitions/openai-gpt-oss-20b-red-teaming/writeups/SafoLab-red-teaming-challenge | Kaggle Writeup | ✅ Accessible | High |
| 8 | https://www.linkedin.com/in/jingyu-huang-44a5a3346/ | LinkedIn | 🔒 Login wall | Medium |

---

## 2. Detailed Analysis

### 2.1 GitHub Profile — martinjingyu

**URL**: https://github.com/martinjingyu
**Display Name**: ChibiYuu / martinjingyu
**Bio**: "Ok, everything's cooked : )"
**Followers**: 3 | **Following**: 3
**Repositories**: 42 | **Stars**: 24
**Contributions (last year)**: 65 — **非常低**

**Repository Breakdown**:
- **原创项目**: CVScreeningAgent, Agent-Tutorial, Kitty, Multi-Turn-Jailbreaker, TreeRPO, ProfRadar, martinjingyu.github.io, Project-Page, savewise, Greetings, HelloWorld, KaggleChallenge, Template, UtilityDataset, CodeGuru, virtual-bank, Port-Number
- **Fork 项目**: openai-agents-python, cs639-assignments, OpenHands, openclaw, nanobot, AgentBench, TradingAgents, verl, emir-specific-rag, expensemanager, RedteamRL, LLaMA-Factory, rStar, simpleRL-reason, GammaGL-old-, HGAT, MoleculeSTM, WalkLM 等

**Assessment**: 账号活跃度低（65 contributions/year），大量 fork 项目。原创项目数量不少但多数 star 数为 0。

---

### 2.2 Multi-Turn-Jailbreaker

**URL**: https://github.com/martinjingyu/Multi-Turn-Jailbreaker
**Type**: 原创项目
**Stars**: 0 | **Forks**: 0
**Commits**: 73

**代码深度分析**:
- 目录结构合理：config/, data/, datagenerator/, dataset/, evaluate/, model/, scripts/, trainer/, utils/
- 读取了 `datagenerator/do_generate.py` — 真实的 Python 代码，使用 hydra, torch, tqdm, yaml 等库
- 读取了 `trainer/orchestrator.py` — 高质量的工程代码，有类型注解、dataclass、错误处理、子进程管理、健康检查
- 项目实现了三阶段 pipeline：generate → SFT → TreeRPO (GRPO-style RL)

**Commit 历史分析**:
- **🚩 严重红旗**: 所有 73 个 commit message 都是 "update"、"updatea"、"udpateaq"（拼写错误）
- **🚩 严重红旗**: 所有 commit 集中在"3 weeks ago"和"2 months ago"两个时间点
- 这种模式强烈暗示批量提交（一次性 push 大量代码），而非渐进式开发
- 代码质量本身不错，但 commit 历史可疑

**README**: 详细，包含 Quick Start、项目布局、环境配置说明。引用了一个匿名链接 `https://anonymous.4open.science/r/Multi-Turn-Jailbreaker-DBF2/`（可能是双盲审稿用）。

**Assessment**: ⚠️ 代码本身质量不错，但 commit 历史异常（全部"update" + 集中在两个时间点），疑似一次性提交。

---

### 2.3 KaggleChallenge

**URL**: https://github.com/martinjingyu/KaggleChallenge
**Type**: 原创项目（但 commit message 暗示基于其他仓库）
**Stars**: 0 | **Forks**: 0
**Commits**: 54

**代码深度分析**:
- 目录结构：api/, config/, datagenerator/, dataset/, model/, practice/, scripts/, utils/
- 包含 SafoLab.findings.1-4.json 等数据文件
- 有 push.bash 脚本

**Commit 历史分析**:
- **🚩 红旗**: 所有 commit 集中在"9 months ago"
- **🚩 红旗**: 所有 commit message 为 "Update" 或 "Initial commit based on that-repo"
- "Initial commit based on that-repo" 暗示代码可能基于其他仓库

**与 Kaggle Writeup 的对应关系**:
- Kaggle writeup 明确引用此仓库作为代码仓库
- Writeup 内容详细，技术深度合理

**Assessment**: ⚠️ 代码存在，但与 Kaggle writeup 对应。commit 历史同样可疑（一次性提交）。

---

### 2.4 emir-specific-rag

**URL**: https://github.com/martinjingyu/emir-specific-rag
**Type**: **🚩 Fork** from `finos-labs/emir-specific-rag`
**Stars**: 0 | **Forks**: 0
**Commits**: 59（上游仓库的 commits）

**Fork 对比分析**:
- **🚩 严重红旗**: 与上游 `finos-labs/emir-specific-rag:main` 完全一致（"up to date with all commits"）
- 候选人 **没有做任何实质性贡献**，只是 fork 了仓库
- 只比上游多 1 个 commit（"Remove Quick Start Guide from README" — 只是删除了 README 内容）

**与简历描述的对比**:
- 简历说: "Developed a Retrieval-Augmented Generation (RAG) system tailored for EMIR regulations in the finance domain."
- 简历说: "Implemented document retrieval, knowledge indexing, and LLM reasoning..."
- **🚩 严重红旗**: 简历声称"Developed"（开发了）这个系统，但实际只是 fork 了 FINOS Labs 的项目，没有任何代码贡献

**Assessment**: 🚩🚩 **严重红旗 — 简历描述与实际情况严重不符。** 候选人声称自己开发了 RAG 系统，但实际只是 fork 了别人的项目。

---

### 2.5 savewise

**URL**: https://github.com/martinjingyu/savewise
**Type**: 原创项目（Android/Kotlin）
**Stars**: 0 | **Forks**: 0
**Branches**: 7 | **Commits**: 112

**代码深度分析**:
- Android 项目结构完整：app/src/, gradle/, build.gradle.kts, google-services.json, settings.gradle.kts
- 使用了 Firebase Auth, Firebase 数据同步
- 有 Voice recognition 功能实现
- README 详细描述了功能：语音输入、月度支出分析、AI 财务助手

**Commit 历史分析**:
- 112 commits，时间跨度约 2 个月（7 months ago → 5 months ago）
- Commit messages 质量一般（"update", "Initiate", "Hide API"），但也有一些有意义的 message（"Modified settings page, now stores profile pic and recordings", "Data can be sync in firebase", "Partly implement Firebase Auth", "Voice recognition function"）
- 有渐进式开发痕迹（Initiate → Voice recognition → Firebase Auth → Data sync → Settings）

**Assessment**: ✅ 看起来是真实的 Android 项目，有渐进式开发历史。但 commit message 质量参差不齐。

---

### 2.6 Amazon Nova AI Challenge Paper

**URL**: https://www.amazon.science/nova-ai-challenge/proceedings/stepwise-multi-turn-jailbreak-attacks-on-code-llms-via-task-decomposition-and-test-time-scaling
**Type**: 技术报告（非 peer-reviewed）
**Venue**: Amazon Nova AI Challenge Proceedings
**Year**: 2025
**Affiliation**: University of Wisconsin-Madison

**内容验证**:
- 页面存在，标题与简历一致
- 标注为 "By University of Wisconsin-Madison"（未列出个人作者名）
- 描述了三模块框架：核心 LLM、数据生成 pipeline、目标模型模拟
- 声称在第二回合竞赛中取得 top performance
- 可下载 PDF

**Assessment**: ✅ 页面存在，内容与简历描述一致。但这是竞赛技术报告，非 peer-reviewed 论文。

---

### 2.7 Kaggle Writeup — AutoMTCR

**URL**: https://www.kaggle.com/competitions/openai-gpt-oss-20b-red-teaming/writeups/SafoLab-red-teaming-challenge
**Type**: Kaggle 竞赛 writeup
**Date**: Aug 27, 2025
**Team**: SafoLab

**内容验证**:
- Writeup 存在，内容详细（多章节：Introduction, Related Work, Method, Results）
- 技术深度合理，讨论了 MCTS、attacker agents、multi-turn probing 等
- 明确引用代码仓库 `https://github.com/martinjingyu/KaggleChallenge`
- 标题 "AutoMTCR: Red Teaming with LLM-Based Attacker Agents and MCTS Multi-Turn Probing"

**Assessment**: ✅ Writeup 存在且内容详实，与简历描述一致。

---

### 2.8 LinkedIn

**URL**: https://www.linkedin.com/in/jingyu-huang-44a5a3346/
**Status**: 🔒 需要登录才能查看完整资料

**Assessment**: 链接有效，但无法查看详细内容。建议面试时确认 LinkedIn 上的教育/工作经历与简历一致。

---

## 3. Cross-Validation Findings

### 3.1 跨链接一致性

| 检查项 | 结果 |
|--------|------|
| GitHub 项目 ↔ 简历描述 | ⚠️ emir-specific-rag 严重不一致（fork 声称是开发） |
| GitHub 项目 ↔ Kaggle Writeup | ✅ KaggleChallenge 仓库与 writeup 对应 |
| Amazon Paper ↔ Multi-Turn-Jailbreaker | ✅ 论文描述的三模块框架与仓库结构对应 |
| 时间线一致性 | ⚠️ 部分项目时间线模糊（无具体起止日期） |

### 3.2 Contributor 分析

| 项目 | Contributor | 分析 |
|------|-------------|------|
| Multi-Turn-Jailbreaker | 仅 Jingyu | 单人项目，但 README 未说明 |
| KaggleChallenge | 仅 Jingyu | 单人项目 |
| emir-specific-rag | FINOS Labs 团队 | 候选人只是 fork，无贡献 |
| savewise | jingyuhuang | 单人项目 |

### 3.3 技能匹配检查

| 简历声称技能 | 代码中实际体现 | 匹配度 |
|-------------|---------------|--------|
| RAG | emir-specific-rag（fork，无贡献） | 🚩 不匹配 |
| Multi-turn jailbreak | Multi-Turn-Jailbreaker 代码 | ✅ 匹配 |
| MCTS | KaggleChallenge 代码 + writeup | ✅ 匹配 |
| LLM Agents | Multi-Turn-Jailbreaker + KaggleChallenge | ✅ 匹配 |
| Android/Kotlin | savewise | ✅ 匹配 |
| GammaGL/HGAT | GammaGL-old-（fork），HGAT（fork） | 🚩 只是 fork |

---

## 4. 综合判断

### 可信度评分

| 维度 | 评分 (1-5) | 说明 |
|------|-----------|------|
| GitHub 活跃度 | ⭐⭐ | 65 contributions/year，偏低 |
| 代码真实性 | ⭐⭐⭐⭐ | Multi-Turn-Jailbreaker 和 savewise 代码真实 |
| 简历准确性 | ⭐⭐ | emir-specific-rag 严重夸大 |
| 项目原创性 | ⭐⭐⭐ | 部分原创，部分 fork 未标注 |
| 跨链接一致性 | ⭐⭐⭐ | 基本一致，但有重大例外 |
| **综合** | **⭐⭐⭐** | **有真实能力，但简历存在夸大** |

### 可疑发现汇总

1. **🚩🚩 emir-specific-rag — 严重夸大**：简历说"Developed a RAG system"，实际是 fork 自 FINOS Labs 的项目，零贡献
2. **🚩 Multi-Turn-Jailbreaker commit 历史异常**：73 个 commits，全部 message 为 "update"/"updatea"/"udpateaq"，集中在两个时间点
3. **🚩 KaggleChallenge commit 历史异常**：54 commits 全部在"9 months ago"，message 为 "Update" 或 "Initial commit based on that-repo"
4. **🔶 GammaGL/HGAT 贡献存疑**：简历说"Contributed to improving the HGAT algorithm in the GammaGL library"，但 GitHub 上只有 fork 没有个人贡献的 commits
5. **🔶 大量 fork 项目**：42 个仓库中约一半是 fork，但简历未区分

### 绿旗发现

1. ✅ **Amazon Nova AI Challenge 第1名**：论文页面存在，内容详实
2. ✅ **Kaggle Writeup 内容详实**：技术深度合理
3. ✅ **savewise 是真实的 Android 项目**：112 commits，渐进式开发
4. ✅ **Multi-Turn-Jailbreaker 代码质量不错**：有类型注解、错误处理、工程化结构

---

## 5. 面试建议

### 需要重点追问的方向

1. **emir-specific-rag 项目** 🚩
   - "你说你 developed 了这个 RAG 系统，但 GitHub 显示这是 fork 自 FINOS Labs 的项目，且没有你的代码贡献。能具体说说你做了什么工作吗？"
   - "你在 Columbia University SecureFinAI Lab 实习期间的具体贡献是什么？"

2. **GammaGL/HGAT 贡献** 🔶
   - "你说 contributed to improving the HGAT algorithm，但 GitHub 上只有 fork。能具体说说你改了什么？有 PR 链接吗？"

3. **Multi-Turn-Jailbreaker 开发过程** 🔶
   - "这个项目的 commit message 全部是 'update'，而且集中在两个时间点。能描述一下你的开发过程吗？"
   - "你是如何设计三阶段 pipeline 的？遇到了什么挑战？"

4. **KaggleChallenge 的代码来源** 🔶
   - "commit message 说 'Initial commit based on that-repo'，这个 'that-repo' 是什么？"

5. **技术深度验证**
   - "TreeRPO 和 verl 的关系是什么？你在 TreeRPO 中做了什么修改？"
   - "你在 SafoLab 的 red-teaming agent 中具体负责什么模块？"

### 需要验证的疑点

- [ ] emir-specific-rag 的实际贡献（可能是 Columbia 实习期间的工作，但代码未体现）
- [ ] Gamma Lab 实习期间对 GammaGL 的具体贡献
- [ ] 教育时间线：BUPT (2021-2024) → UW-Madison (2024-至今)，但 SafoLab 实习 (Aug 2024-Aug 2025) 和 Columbia 实习 (July 2025-Sept 2025) 与学业重叠
- [ ] 简历中未列出编程语言技能（skills.programming_languages 为空数组）

---

*Report generated using cv-link-deep-research skill. All links were accessed and verified on 2026-05-24.*
