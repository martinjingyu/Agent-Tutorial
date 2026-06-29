# Agent LLM 方向文献综述

> 基于 Kai-Wei Chang (UCLA) 研究方向，对 Agent LLM 领域进行系统性文献综述
> 撰写日期：2026-06-29

---

## 目录

1. [Tool Calling & Function Calling](#1-tool-calling--function-calling)
2. [Planning & Reasoning in Agents](#2-planning--reasoning-in-agents)
3. [Action Trajectory Optimization](#3-action-trajectory-optimization)
4. [Agent Training Methods](#4-agent-training-methods)
5. [Multi-Agent Systems](#5-multi-agent-systems)
6. [Evaluation of Agents](#6-evaluation-of-agents)
7. [Kai-Wei Chang 课题组相关贡献总结](#7-kai-wei-chang-课题组相关贡献总结)
8. [跨方向趋势与开放问题](#8-跨方向趋势与开放问题)

---

## 1. Tool Calling & Function Calling

### 1.1 代表性论文

| 论文 | 发表 | 核心贡献 |
|------|------|----------|
| **Toolformer** (Schick et al., 2023) | arXiv 2023.02 | 首个让 LLM 自监督学习使用工具的方法。模型通过采样 API 调用并评估其是否降低 perplexity 来决定是否调用工具，实现"自学用工具"。 |
| **Gorilla** (Patil et al., 2023) | NeurIPS 2024 | 基于 LLaMA 微调的 API 调用模型，引入检索增强（Retriever-Aware Training），在 1,600+ API 上超越 GPT-4。提出 APIBench 评估集。 |
| **ToolLLM** (Qin et al., 2023) | ACL 2024 | 构建 ToolBench（16,000+ 真实 API），提出 Depth-First Search-based Decision Tree (DFSDT) 推理策略，训练 ToolLlama 模型。 |
| **AnyTool** (Du et al., 2024) | ICML 2024 | 基于 GPT-4 function calling 的分层 API 检索框架，包含 API 检索器、查询分解器和自我反思机制，无需额外训练。 |
| **Chameleon** (Lu et al., 2023) | NeurIPS 2023 | **Kai-Wei Chang 组工作**。即插即用的组合推理框架，LLM 作为控制器动态编排视觉/检索/代码等模块，在 ScienceQA 和 TabMWP 上显著提升。 |

### 1.2 核心贡献总结

- **自监督范式**（Toolformer）：无需人工标注，模型通过 perplexity 信号自主决定何时调用工具
- **检索增强**（Gorilla）：解决 API 文档动态更新问题，避免模型记忆过时 API
- **大规模工程化**（ToolLLM）：从数据构建到模型训练到评估的完整 pipeline，支持 16,000+ API
- **分层架构**（AnyTool, Chameleon）：将工具使用分解为检索→选择→执行→反思的多阶段流程

### 1.3 当前局限与未解决问题

- **API 幻觉**：模型仍会生成不存在或错误的 API 调用，尤其在长尾 API 上
- **工具组合的泛化性**：现有方法在未见过的工具组合上表现不佳
- **多步工具链的鲁棒性**：中间步骤错误会级联放大，缺乏有效的错误恢复机制
- **工具更新的实时性**：API 文档频繁更新，模型需要持续适应
- **安全与权限**：工具调用缺乏细粒度的权限控制和安全性验证

---

## 2. Planning & Reasoning in Agents

### 2.1 代表性论文

| 论文 | 发表 | 核心贡献 |
|------|------|----------|
| **ReAct** (Yao et al., 2022) | ICLR 2023 Oral | 提出推理与行动交错进行的范式，将 Chain-of-Thought 推理与动作执行结合，在 HotpotQA 和 ALFWorld 上显著超越纯推理或纯行动方法。 |
| **Tree of Thoughts (ToT)** (Yao et al., 2023) | NeurIPS 2023 | 将推理过程建模为树状搜索，支持分支探索、评估和回溯。在 Game of 24、创意写作等需要搜索的任务上大幅提升。 |
| **Graph of Thoughts (GoT)** (Besta et al., 2024) | AAAI 2024 | 将推理建模为有向图，支持思维合并、回溯和循环，比 ToT 更灵活。引入 Graph of Operations (GoO) 和 Graph Reasoning State (GRS)。 |
| **Plan-and-Solve (PS)** (Wang et al., 2023) | ACL 2023 | 改进 Zero-shot CoT，将推理分为"制定计划"和"执行计划"两个阶段，解决 CoT 中的 missing-step 错误。 |
| **Understanding the Planning of LLM Agents** (Huang et al., 2024) | arXiv 2024.02 | 系统性综述 LLM-Agent 规划方法，提出任务分解、计划选择、外部模块、反思与记忆的四维度分类法。 |

### 2.2 核心贡献总结

- **ReAct 范式**：奠定了"推理-行动"交错执行的基础架构，成为后续 Agent 框架的标准模式
- **结构化搜索**：从链式（CoT）到树状（ToT）到图状（GoT），推理结构的表达能力逐步增强
- **规划与执行分离**（Plan-and-Solve）：显式分离规划阶段和执行阶段，提高复杂任务的成功率
- **反思机制**：Agent 在执行过程中自我评估和修正计划

### 2.3 当前局限与未解决问题

- **搜索效率**：ToT/GoT 的搜索空间随任务复杂度指数增长，token 开销巨大
- **规划与执行的耦合**：动态环境中计划需要频繁调整，现有方法缺乏高效的 replanning 机制
- **长程规划**：超过 10+ 步的任务中，规划准确率急剧下降
- **评估标准缺失**：缺乏统一的规划质量评估指标
- **世界模型**：Agent 缺乏对环境的内部模型来模拟计划结果

---

## 3. Action Trajectory Optimization

### 3.1 代表性论文

| 论文 | 发表 | 核心贡献 |
|------|------|----------|
| **ETO (Exploration-based Trajectory Optimization)** (Deng et al., 2024) | ACL 2024 | 提出基于探索的轨迹优化框架：先在成功轨迹上做行为克隆（BC），再通过收集失败轨迹进行对比学习，迭代优化 agent 策略。 |
| **DMPO (Direct Multi-Turn Preference Optimization)** (Song et al., 2024) | EMNLP 2024 | 将 DPO 扩展到多轮 agent 任务，解决标准 DPO 在变长轨迹中配分函数无法抵消的问题。在三个多轮 agent 数据集上验证有效性。 |
| **Re-ReST (Reflection-Reinforced Self-Training)** (Yin et al., 2024) | EMNLP 2024 | **Kai-Wei Chang 组工作**。将自我训练与反思机制结合，agent 通过反思失败轨迹生成改进后的训练数据，迭代提升性能。 |
| **RRO (Rising Reward Optimization)** (2025) | arXiv 2025 | 提出 Reward Rising Sampling 方法，动态缩放下一动作的探索过程，优化 agent 策略。 |
| **Policy Optimization with Action Decomposition** (NeurIPS 2024) | NeurIPS 2024 | 将语言 agent 优化从 action 级别分解到 token 级别，为每个 intra-action token 提供更细粒度的监督信号。 |

### 3.2 核心贡献总结

- **行为克隆（BC）**：从专家轨迹中监督学习，是 agent 训练的起点
- **对比学习**（ETO）：同时利用成功和失败轨迹进行对比优化，比纯 BC 更有效
- **偏好优化**（DMPO）：将 DPO 从单轮对话扩展到多轮 agent 轨迹，解决配分函数问题
- **自我训练**（Re-ReST）：agent 自我生成训练数据，减少对人工标注的依赖
- **Token 级优化**：从 action 级到 token 级的细粒度优化，提供更精确的监督

### 3.3 当前局限与未解决问题

- **探索-利用平衡**：agent 轨迹优化中如何有效探索失败轨迹仍是开放问题
- **奖励设计**：多步 agent 任务中稀疏奖励和延迟奖励问题突出
- **分布偏移**：训练时的轨迹分布与推理时的轨迹分布不一致
- **计算成本**：迭代式轨迹优化需要大量 rollout，计算开销大
- **泛化性**：在某个环境/任务上优化的策略难以迁移到新环境

---

## 4. Agent Training Methods

### 4.1 代表性论文

| 论文 | 发表 | 核心贡献 |
|------|------|----------|
| **Agent Lumos** (Yin et al., 2023) | ACL 2024 | **Kai-Wei Chang 组核心工作**。提出统一且模块化的开源 LLM agent 训练框架：(1) 统一数据格式覆盖多种交互任务；(2) 模块化架构（Planning → Grounding → Execution）；(3) 大规模高质量训练标注。在多个 benchmark 上达到与 GPT-4 agent 可比的性能。 |
| **DACO (Data-Centric Optimization)** (Wu et al., 2024) | NeurIPS 2024 (Datasets & Benchmarks) | **Kai-Wei Chang 组工作**。面向数据分析任务的以数据为中心的优化方法，使用 LLM + 代码生成自动产生高质量数据分析数据，降低人工标注成本。 |
| **Dynosaur** (Yin et al., 2023) | ACL 2024 | **Kai-Wei Chang 组工作**。动态指令微调数据生成框架，根据任务需求自动生成多样化的训练数据。 |
| **ToolAlpaca** (Tang et al., 2023) | arXiv 2023.06 | 基于 3,000 个模拟工具用例的广义工具学习框架，使用 Self-Instruct 方法生成训练数据。 |

### 4.2 核心贡献总结

- **模块化训练**（Agent Lumos）：将 agent 能力分解为规划（Planning）、落地（Grounding）、执行（Execution）三个模块，分别训练再组合，支持模块级升级
- **统一数据格式**（Agent Lumos）：跨任务统一训练数据格式，提升泛化能力
- **数据为中心**（DACO）：用 LLM 自动生成高质量训练数据，解决标注成本问题
- **动态数据生成**（Dynosaur）：根据任务需求动态生成指令微调数据

### 4.3 当前局限与未解决问题

- **模块间协同**：模块化训练中模块间的信息传递和协同仍有优化空间
- **数据质量**：自动生成的数据可能存在噪声和偏差
- **任务覆盖**：现有训练数据覆盖的任务类型仍有限
- **计算资源**：模块化训练需要分别训练多个模块，总计算成本高
- **开放域泛化**：在完全未见过的任务类型上泛化能力有限

---

## 5. Multi-Agent Systems

### 5.1 代表性论文

| 论文 | 发表 | 核心贡献 |
|------|------|----------|
| **AutoGen** (Wu et al., 2023) | arXiv 2023.08 | Microsoft 开源的多 agent 对话框架，支持多个 LLM agent 之间通过对话协作完成任务。提出 Assistant Agent 和 User Proxy Agent 的角色分工。 |
| **ChatDev** (Qian et al., 2023) | arXiv 2023.07 | 模拟虚拟软件开发公司，agent 扮演 CEO、CTO、程序员、测试员等角色，通过结构化聊天协作完成软件开发。 |
| **MetaGPT** (Hong et al., 2023) | NeurIPS 2024 | 将标准化操作流程（SOPs）融入多 agent 协作，agent 根据角色输出结构化文档（PRD、设计文档、API 规范等），提升协作效率。 |
| **Magnet** (Chang's Group) | — | **Kai-Wei Chang 组工作**。多 agent 框架，关注 agent 间的通信和协调机制。 |
| **Multi-Agent Collaboration Mechanisms Survey** (Tran et al., 2025) | arXiv 2025.01 | 系统性综述 LLM 多 agent 协作机制，涵盖通信协议、任务分配、共识形成等维度。 |

### 5.2 核心贡献总结

- **对话式协作**（AutoGen）：agent 通过自然语言对话进行协作，降低通信门槛
- **角色分工**（ChatDev, MetaGPT）：引入社会角色和 SOPs，结构化多 agent 协作流程
- **通信拓扑**：从全连接到分层结构，不同拓扑适合不同任务类型
- **共识机制**：多 agent 之间的投票、辩论等共识形成机制

### 5.3 当前局限与未解决问题

- **通信开销**：多 agent 间的对话轮次随 agent 数量平方增长，token 消耗巨大
- **角色冲突**：多个 agent 角色定义不清时容易产生冲突和冗余工作
- **评估困难**：多 agent 系统的整体性能难以归因到单个 agent
- **扩展性**：agent 数量超过一定阈值后，协作效率反而下降
- **安全与对齐**：多 agent 系统中一个 agent 的异常行为可能级联影响整个系统

---

## 6. Evaluation of Agents

### 6.1 代表性论文

| 论文 | 发表 | 核心贡献 |
|------|------|----------|
| **AgentBench** (Liu et al., 2023) | ICLR 2024 | 首个综合性 LLM-as-Agent 评估基准，涵盖 8 个不同环境（操作系统、数据库、网络、游戏等），系统评估 LLM 的长期推理、决策和指令遵循能力。 |
| **WebArena** (Zhou et al., 2023) | ICLR 2024 | 构建了包含完整 Web 应用和真实数据的可复现 Web 环境，812 个任务覆盖购物、论坛、地图等场景。 |
| **SWE-bench** (Jimenez et al., 2024) | ICLR 2024 | 基于 GitHub 真实 issue 的代码修复 benchmark，要求 LLM 根据 issue 描述和代码库生成补丁。 |
| **SafeWorld** (Chang's Group) | — | **Kai-Wei Chang 组工作**。关注 agent 安全性的评估基准。 |
| **METAL** (Chang's Group) | — | **Kai-Wei Chang 组工作**。多 agent 评估框架。 |
| **LongMemEval** (Chang's Group) | — | **Kai-Wei Chang 组工作**。agent 长程记忆能力评估。 |
| **AutoSUIT Bench** (Chang's Group) | — | **Kai-Wei Chang 组工作**。自动化 agent benchmark。 |
| **Evaluation and Benchmarking of LLM Agents Survey** (2025) | arXiv 2025.07 | 提出二维分类法组织 LLM agent 评估方法，涵盖企业级挑战。 |

### 6.2 核心贡献总结

- **综合性评估**（AgentBench）：首个跨环境统一评估框架，揭示 LLM 在 agent 任务上的系统性不足
- **真实环境**（WebArena, SWE-bench）：从简化合成环境转向真实可复现环境，提升评估生态效度
- **多维度评估**：涵盖推理、决策、指令遵循、记忆、安全性等多个维度
- **标准化**：推动 agent 评估从定性展示走向定量标准化

### 6.3 当前局限与未解决问题

- **评估成本**：真实环境评估（如 WebArena）需要大量基础设施，复现成本高
- **评估污染**：benchmark 数据可能被包含在 LLM 训练集中
- **任务多样性不足**：现有 benchmark 覆盖的任务类型仍有限
- **自动化评估可靠性**：自动评估指标与人工判断的一致性有待提高
- **安全评估缺失**：agent 安全性、鲁棒性的系统评估方法仍不成熟

---

## 7. Kai-Wei Chang 课题组相关贡献总结

Kai-Wei Chang (UCLA Associate Professor, Amazon Scholar) 课题组在 Agent LLM 领域有多项重要贡献：

| 方向 | 工作 | 会议/期刊 | 贡献类型 |
|------|------|-----------|----------|
| Tool Calling | **Chameleon** | NeurIPS 2023 | 即插即用组合推理框架 |
| Agent Training | **Agent Lumos** | ACL 2024 | 统一模块化 agent 训练 |
| Agent Training | **DACO** | NeurIPS 2024 | 数据为中心的 agent 优化 |
| Agent Training | **Dynosaur** | ACL 2024 | 动态指令微调数据生成 |
| Trajectory Optimization | **Re-ReST** | EMNLP 2024 | 反思增强的自我训练 |
| Multi-Agent | **Magnet** | — | 多 agent 协作框架 |
| Evaluation | **SafeWorld** | — | Agent 安全评估 |
| Evaluation | **METAL** | — | 多 agent 评估 |
| Evaluation | **LongMemEval** | — | 长程记忆评估 |
| Evaluation | **AutoSUIT Bench** | — | 自动化 agent benchmark |
| Reasoning | **Tree-of-Traversals** | — | 结构化推理 |
| Reasoning | **Ctrl-R** | — | 检索增强的结构化推理 |

**核心特色**：Chang 组的工作强调 (1) 模块化和统一性（Agent Lumos），(2) 数据效率（DACO, Dynosaur），(3) 安全与可信（SafeWorld），(4) 从训练到评估的完整闭环。

---

## 8. 跨方向趋势与开放问题

### 8.1 主要趋势

1. **从单 agent 到多 agent**：研究重心从单 agent 能力提升转向多 agent 协作与通信
2. **从闭源到开源**：Agent Lumos 等开源方案推动 agent 技术的民主化
3. **从人工标注到自动数据生成**：DACO、Dynosaur 等减少对人工标注的依赖
4. **从简化环境到真实环境**：WebArena、SWE-bench 推动评估的真实性
5. **从行为克隆到偏好优化**：训练范式从监督学习转向偏好优化（DPO/DMPO）
6. **从独立模块到端到端**：模块化训练（Agent Lumos）与端到端训练的融合

### 8.2 关键开放问题

1. **Agent 的长期自主性**：如何在开放环境中持续学习而不遗忘
2. **安全与对齐**：如何确保 agent 行为符合人类价值观
3. **可解释性**：agent 的决策过程缺乏透明度和可解释性
4. **泛化能力**：从训练环境到真实世界的零样本迁移
5. **计算效率**：agent 推理的 token 成本和延迟优化
6. **评估标准化**：缺乏统一的、被广泛接受的 agent 评估体系
7. **多模态 agent**：将视觉、语音等多模态信息融入 agent 决策

---

## 参考文献

1. Schick, T., et al. "Toolformer: Language Models Can Teach Themselves to Use Tools." arXiv:2302.04761 (2023).
2. Patil, S., et al. "Gorilla: Large Language Model Connected with Massive APIs." NeurIPS (2024).
3. Qin, Y., et al. "ToolLLM: Facilitating Large Language Models to Master 16000+ Real-World APIs." ACL (2024).
4. Du, Y., et al. "AnyTool: Self-Reflective, Hierarchical Agents for Large-Scale API Calls." ICML (2024).
5. Lu, P., et al. "Chameleon: Plug-and-Play Compositional Reasoning with Large Language Models." NeurIPS (2023).
6. Yao, S., et al. "ReAct: Synergizing Reasoning and Acting in Language Models." ICLR (2023).
7. Yao, S., et al. "Tree of Thoughts: Deliberate Problem Solving with Large Language Models." NeurIPS (2023).
8. Besta, M., et al. "Graph of Thoughts: Solving Elaborate Problems with Large Language Models." AAAI (2024).
9. Wang, L., et al. "Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought Reasoning." ACL (2023).
10. Huang, X., et al. "Understanding the Planning of LLM Agents: A Survey." arXiv:2402.02716 (2024).
11. Deng, X., et al. "Trial and Error: Exploration-Based Trajectory Optimization for LLM Agents." ACL (2024).
12. Song, Y., et al. "Direct Multi-Turn Preference Optimization for Language Agents." EMNLP (2024).
13. Yin, D., et al. "Re-ReST: Reflection-Reinforced Self-Training for Language Agents." EMNLP (2024).
14. Yin, D., et al. "Agent Lumos: Unified and Modular Training for Open-Source Language Agents." ACL (2024).
15. Wu, X., et al. "DACO: Towards Application-Driven and Comprehensive Data Analysis." NeurIPS (2024).
16. Wu, Q., et al. "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation." arXiv:2308.08155 (2023).
17. Qian, C., et al. "ChatDev: Communicative Agents for Software Development." arXiv:2307.07924 (2023).
18. Hong, S., et al. "MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework." NeurIPS (2024).
19. Liu, X., et al. "AgentBench: Evaluating LLMs as Agents." ICLR (2024).
20. Zhou, S., et al. "WebArena: A Realistic Web Environment for Building Autonomous Agents." ICLR (2024).
21. Jimenez, C.E., et al. "SWE-bench: Can Language Models Resolve Real-World GitHub Issues?" ICLR (2024).
22. Tran, et al. "Multi-Agent Collaboration Mechanisms: A Survey of LLMs." arXiv:2501.06322 (2025).
23. Tang, Q., et al. "ToolAlpaca: Generalized Tool Learning for Language Models with 3000 Simulated Cases." arXiv:2306.05301 (2023).
24. "Large Language Model Agent: A Survey on Methodology." arXiv:2503.21460 (2025).
