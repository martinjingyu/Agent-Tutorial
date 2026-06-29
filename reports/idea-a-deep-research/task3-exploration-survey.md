# LLM Agent 探索策略调研

> 调研日期：2026-06-07 | 覆盖论文时间范围：2023–2026

---

## 1. MCTS-based 方法

Monte Carlo Tree Search (MCTS) 是 LLM Agent 探索策略中最主流的方法之一。其核心思想是将 LLM 作为世界模型和/或策略网络，在推理/决策空间中构建搜索树，通过模拟-选择-扩展-回溯的循环实现结构化探索。

### 1.1 RAP — Reasoning via Planning (EMNLP 2023)

- **论文**: Shibo Hao et al., "Reasoning with Language Model is Planning with World Model", EMNLP 2023
- **链接**: https://arxiv.org/abs/2305.14992
- **核心方法**: 将 LLM 同时作为世界模型（预测状态转移）和推理 agent，在 MCTS 框架下进行战略探索。LLM (agent) 逐步构建推理树，LLM (world model) 提供状态预测，结合任务特定奖励引导搜索。
- **关键贡献**: 首次系统性地将 MCTS 与 LLM 推理结合，在 plan generation 任务上 LLaMA-33B + RAP 超越 GPT-4 + CoT 33%。
- **探索机制**: MCTS 的 UCB 公式天然平衡 exploration vs. exploitation；通过树搜索探索多种推理路径。

### 1.2 SE-Agent — Self-Evolution Trajectory Optimization (NeurIPS 2025)

- **论文**: Jiaye Lin et al., "SE-Agent: Self-Evolution Trajectory Optimization in Multi-Step Reasoning with LLM-Based Agents", NeurIPS 2025
- **链接**: https://arxiv.org/abs/2508.02085
- **核心方法**: 提出自我进化框架，通过三个关键操作（revision、recombination、refinement）对历史轨迹进行迭代优化。扩展搜索空间超越局部最优，利用跨轨迹灵感提升性能。
- **关键贡献**: 在 SWE-bench Verified 上实现最高 55% 相对提升，达到开源 agent SOTA。
- **探索机制**: 通过进化操作（而非传统 MCTS 的随机模拟）实现多样化探索；跨轨迹信息共享避免冗余搜索。

### 1.3 MCTS-AHD — MCTS for Automatic Heuristic Design (ICML 2025)

- **论文**: Zhi Zheng et al., "Monte Carlo Tree Search for Comprehensive Exploration in LLM-Based Automatic Heuristic Design", ICML 2025
- **链接**: https://arxiv.org/abs/2501.08603
- **核心方法**: 用 MCTS 组织所有 LLM 生成的启发式规则为树结构，充分开发暂时表现不佳的启发式的潜力。
- **关键贡献**: 在复杂优化任务（路径规划、任务分配）上生成显著更高质量的启发式规则。
- **探索机制**: MCTS 树结构允许对每个启发式节点进行深入探索，避免 population-based 方法容易陷入局部最优的问题。

### 1.4 MASTER — Multi-Agent System with LLM Specialized MCTS (NAACL 2025)

- **论文**: Bingzheng Gan et al., "MASTER: A Multi-Agent System with LLM Specialized MCTS", NAACL 2025
- **链接**: https://arxiv.org/abs/2501.14304
- **核心方法**: 用 LLM-specialized MCTS 协调多 agent 的招募和通信，根据任务复杂度自动调整 agent 数量。
- **关键贡献**: HotpotQA 76% 准确率，WebShop 80% 准确率，均达 SOTA。
- **探索机制**: MCTS 不仅用于推理路径探索，还用于决定何时招募新 agent 以及 agent 间的通信策略。

### 1.5 PlanU — Planning under Uncertainty (NeurIPS 2025)

- **论文**: Ziwei Deng et al., "PlanU: Large Language Model Reasoning through Planning under Uncertainty", NeurIPS 2025
- **链接**: https://arxiv.org/abs/2510.18442
- **核心方法**: 在 MCTS 中建模每个节点的 return 为分位数分布，提出 Upper Confidence Bounds with Curiosity (UCC) 分数来平衡探索与利用。
- **关键贡献**: 同时处理 LLM 不确定性（随机采样）和环境不确定性（随机状态转移）。
- **探索机制**: UCC 分数结合了不确定性估计和好奇心驱动，比标准 UCB 更适合 LLM 推理场景。

### 1.6 MC-DML — Monte Carlo Planning with Dynamic Memory LLM (ICLR 2025)

- **论文**: "Monte Carlo Planning with Large Language Model for Text", ICLR 2025
- **链接**: https://openreview.net/forum?id=r1KcapkzCt
- **核心方法**: 利用动态记忆引导的 LLM 结合 MCTS 的探索特性进行文本规划。
- **探索机制**: LLM 的先验知识指导 MCTS 中的动作探索，动态记忆机制存储历史探索经验。

---

## 2. UCB / Bandit 方法

基于 bandit 理论的探索方法将 LLM Agent 的决策建模为多臂赌博机问题，通过 UCB、Thompson Sampling 等策略平衡探索与利用。

### 2.1 Efficient Exploration for LLMs (ICML 2024)

- **论文**: Vikranth Dwaracherla et al., "Efficient Exploration for LLMs", ICML 2024
- **链接**: https://arxiv.org/abs/2402.00396
- **核心方法**: 使用 Double Thompson Sampling 生成查询，用 epistemic neural network 表示不确定性。agent 顺序生成查询，同时根据反馈拟合奖励模型。
- **关键贡献**: 高效探索使 LLM 在远少于常规次数的查询下达到高水平性能。
- **探索机制**: Thompson Sampling 通过后验采样自然平衡探索与利用；epistemic neural network 提供不确定性估计。

### 2.2 Can Large Language Models Explore In-Context? (NeurIPS 2024)

- **论文**: Akshay Krishnamurthy et al., "Can large language models explore in-context?", NeurIPS 2024
- **链接**: https://arxiv.org/abs/2403.15371
- **核心方法**: 将 LLM 作为 agent 部署在简单多臂赌博机环境中，环境描述和交互历史完全在上下文中指定。
- **关键发现**: 仅 GPT-4 + chain-of-thought + 外部总结的交互历史才能产生令人满意的探索行为；其他配置均无法鲁棒地探索。
- **启示**: 非平凡的算法干预（如微调或数据集整理）可能是赋予 LLM agent 探索能力的必要条件。

### 2.3 Should You Use Your LLM to Explore or Exploit? (UAI 2026)

- **论文**: Keegan Harris, Aleksandrs Slivkins, "Should You Use Your Large Language Model to Explore or Exploit?", UAI 2026
- **链接**: https://arxiv.org/abs/2502.00225
- **核心方法**: 系统性地将 LLM 的探索和利用能力分开评估，在各种 contextual bandit 任务中测试。
- **关键发现**: 推理模型在 exploitation 任务上最有前景，但成本/速度仍不实用；LLM 在探索具有语义的大动作空间时确实有帮助（通过建议合适的候选动作）。
- **启示**: LLM 更适合辅助探索（缩小候选空间），而非直接执行 bandit 算法。

### 2.4 Toward Efficient Exploration by LLM Agents (ICLR 2026)

- **论文**: Dilip Arumugam, Thomas L. Griffiths, "Toward Efficient Exploration by Large Language Model Agents", ICLR 2026
- **链接**: https://arxiv.org/abs/2504.20997
- **核心方法**: 用 LLM 显式实现 Posterior Sampling for Reinforcement Learning (PSRL) 算法，而非通过微调或 in-context learning 隐式模仿。
- **关键贡献**: 展示了 LLM-based 实现已知数据高效 RL 算法在需要谨慎探索的自然语言任务上的有效性。
- **探索机制**: PSRL 通过维护后验分布并从中采样来平衡探索与利用，是 Thompson Sampling 在 RL 中的推广。

### 2.5 Outcome-based Exploration for LLM Reasoning (2025)

- **论文**: "Outcome-based Exploration for LLM Reasoning", 2025
- **链接**: https://arxiv.org/pdf/2509.06941
- **核心方法**: 基于结果的探索方法，对比 UCB-Con 等策略在 LLM 推理训练中的表现。
- **关键发现**: 探索方法在几乎所有指标上优于基线（pass@k 等），但 UCB-Con 在特定设置下表现不如简单探索。

---

## 3. Intrinsic Motivation 方法

内在动机驱动的探索方法通过设计内在奖励函数，鼓励 agent 探索未知或信息丰富的状态，而非仅追求外部奖励。

### 3.1 IMAGINE — Intrinsic Motivation Guided Exploration (2025)

- **论文**: Jingtong Gao et al., "Navigate the Unknown: Enhancing LLM Reasoning with Intrinsic Motivation Guided Exploration", 2025
- **链接**: https://arxiv.org/abs/2505.17621
- **核心方法**: 提出三种创新：(1) trajectory-aware exploration reward 减少 token 级偏差；(2) error-conditioned reward allocation 在困难样本上促进高效探索；(3) advantage-preserving integration 保持分布完整性。
- **关键贡献**: 在 AIME 2024 上提升 22.23% 性能。
- **探索机制**: 内在动机奖励替代稀疏的外部奖励，提供密集、稳定、高效的探索信号。

### 3.2 MOTIF — Intrinsic Motivation from AI Feedback (ICLR 2024)

- **论文**: Martin Klissarov et al., "Motif: Intrinsic Motivation from Artificial Intelligence Feedback", ICLR 2024
- **链接**: https://arxiv.org/abs/2310.00166
- **核心方法**: 从 LLM 对 caption 对的偏好中构建内在奖励函数，用 RL 训练 agent 最大化该内在奖励。
- **关键贡献**: 仅通过最大化内在奖励就在 NetHack 游戏中获得比直接最大化游戏分数更高的分数；结合环境奖励后显著超越现有方法。
- **探索机制**: LLM 提供先验知识作为内在奖励，无需与环境交互即可引导探索方向。

### 3.3 ONI — Online Intrinsic Rewards from LLM Feedback (RLC 2025)

- **论文**: Qinqing Zheng et al., "Online Intrinsic Rewards for Decision Making Agents from Large Language Model Feedback", RLC 2025
- **链接**: https://arxiv.org/abs/2410.23022
- **核心方法**: 分布式架构同时学习 RL 策略和内在奖励函数。通过异步 LLM server 标注 agent 收集的经验，蒸馏为内在奖励模型。
- **关键贡献**: 在 NetHack Learning Environment 上达到 SOTA，无需大规模离线数据集。
- **探索机制**: LLM 反馈在线蒸馏为内在奖励模型，支持 hashing、classification、ranking 等多种奖励建模方式。

### 3.4 i-MENTOR (2025)

- **论文**: "Enhancing LLM Reasoning with Intrinsic Motivation Guided Exploration" (i-MENTOR variant), OpenReview 2025
- **链接**: https://openreview.net/forum?id=mlzh3jX6gW
- **核心方法**: 使用内在动机引导的探索提供密集探索奖励，增强 LLM 在多种数据集上的推理性能。
- **探索机制**: 与 IMAGINE 类似，通过内在奖励信号替代稀疏外部奖励。

---

## 4. Diversity-based 方法

基于多样性的探索方法通过显式鼓励行为/轨迹/策略的多样性来促进探索，避免陷入局部最优。

### 4.1 ETO — Exploration-based Trajectory Optimization (ACL 2024)

- **论文**: Yifan Song et al., "Trial and Error: Exploration-Based Trajectory Optimization for LLM Agents", ACL 2024
- **链接**: https://arxiv.org/abs/2403.02502
- **核心方法**: 让 agent 从探索失败中学习。探索阶段收集失败轨迹，与成功轨迹形成对比对；训练阶段用 DPO 等对比学习方法更新策略。
- **关键贡献**: 在三个复杂任务上持续超越基线，无需专家轨迹即可提升。
- **探索机制**: 通过探索-训练迭代循环，失败轨迹提供了多样化的负样本，丰富了策略的探索空间。

### 4.2 DPEPO — Diverse Parallel Exploration Policy Optimization (ACL 2026)

- **论文**: Junshuo Zhang et al., "DPEPO: Diverse Parallel Exploration Policy Optimization for LLM-based Agents", ACL 2026
- **链接**: https://arxiv.org/abs/2604.24320
- **核心方法**: 让 agent 同时与多个环境交互并共享跨轨迹经验。设计 Diverse Action Reward 和 Diverse State Transition Reward 主动惩罚行为冗余。
- **关键贡献**: 在 ALFWorld 和 ScienceWorld 上达到 SOTA 成功率。
- **探索机制**: 并行环境探索 + 多样性奖励（动作级和状态转移级）显式鼓励行为多样性。

### 4.3 APP — Adaptive Prompt Pruning for Diversity Control (EMNLP 2025)

- **论文**: KuanChao Chu et al., "Exploring and Controlling Diversity in LLM-Agent Conversation", EMNLP 2025 Findings
- **链接**: https://arxiv.org/abs/2412.21102
- **核心方法**: 通过 Adaptive Prompt Pruning 动态裁剪 prompt 片段（基于注意力分数），用单一参数 λ 控制输出多样性。
- **关键发现**: 所有 prompt 组件都对多样性施加约束，其中 Memory 影响最大；高注意力内容持续抑制输出多样性。
- **探索机制**: 通过减少上下文信息量来增加输出多样性，提供可调节的多样性控制。

### 4.4 Explorer — Scaling Exploration-driven Web Trajectory Synthesis (ACL 2025 Findings)

- **论文**: Vardaan Pahuja et al., "Explorer: Scaling Exploration-driven Web Trajectory Synthesis for Multimodal Web Agents", ACL 2025 Findings
- **链接**: https://arxiv.org/abs/2502.11357
- **核心方法**: 利用大规模 web 探索和精炼获得多样化任务意图，合成 94K+ 成功多模态 web 轨迹。
- **关键贡献**: 覆盖 49K 唯一 URL，每条成功轨迹成本仅 28 美分。
- **探索机制**: 通过探索驱动的方法生成多样化的任务意图和轨迹，数据规模是提升 web agent 能力的关键。

---

## 5. Structured Exploration 方法

结构化/可控的探索方法通过高层策略、元学习、图搜索等方式为探索提供结构化引导。

### 5.1 SGE — Strategy-Guided Exploration (2026)

- **论文**: Andrew Szot et al., "Expanding LLM Agent Boundaries with Strategy-Guided Exploration", 2026
- **链接**: https://arxiv.org/abs/2603.02045
- **核心方法**: 利用 LLM 的语言规划能力，将探索从低层动作空间转移到高层语言策略空间。首先生成简洁的自然语言策略描述，然后基于该策略生成环境动作。
- **关键贡献**: 在 UI 交互、工具调用、编码和具身 agent 环境中一致优于 exploration-focused RL 基线。
- **探索机制**: 策略空间探索（而非动作空间）+ mixed-temperature sampling（并行探索多样策略）+ strategy reflection（基于历史结果调整策略生成）。

### 5.2 Go-Browse — Training Web Agents with Structured Exploration (2025)

- **论文**: Apurva Gandhi, Graham Neubig, "Go-Browse: Training Web Agents with Structured Exploration", 2025
- **链接**: https://arxiv.org/abs/2506.03533
- **核心方法**: 将数据收集建模为图搜索，跨探索 episode 复用信息。在 WebArena 上收集 10K 成功轨迹和 40K 交互步骤。
- **关键贡献**: 7B 模型微调后在 WebArena 上达到 21.7% 成功率，超越 GPT-4o mini 2.4%。
- **探索机制**: 图搜索框架提供结构化探索路径，信息复用避免重复探索已访问节点。

### 5.3 LaMer — Meta-RL Induces Exploration in Language Agents (ICLR 2026)

- **论文**: Yulun Jiang et al., "Meta-RL Induces Exploration in Language Agents", ICLR 2026
- **链接**: https://arxiv.org/abs/2512.16848
- **核心方法**: 通用 Meta-RL 框架，包含 (i) 跨 episode 训练框架鼓励探索和长期奖励优化；(ii) 通过反思进行 in-context 策略适应。
- **关键贡献**: 在 Sokoban (+11%)、MineSweeper (+14%)、Webshop (+19%) 上显著提升。
- **探索机制**: Meta-RL 通过跨 episode 经验学习"如何探索"，使 agent 在测试时能主动探索和适应新环境。

### 5.4 LLM-Explorer — Plug-in RL Policy Exploration Enhancement (NeurIPS 2025)

- **论文**: Qianyue Hao et al., "LLM-Explorer: A Plug-in Reinforcement Learning Policy Exploration Enhancement Driven by Large Language Models", NeurIPS 2025
- **链接**: https://arxiv.org/abs/2505.15293
- **核心方法**: 采样 agent 学习轨迹，用 LLM 分析当前策略学习状态，生成未来策略探索的概率分布。周期性更新分布，形成动态调整的随机过程。
- **关键贡献**: 与 DQN、DDPG、TD3 等广泛 RL 算法兼容，平均性能提升最高 37.27%。
- **探索机制**: LLM 作为探索策略生成器，根据 agent 实时学习状态自适应调整探索分布。

### 5.5 PSRL-LLM — Posterior Sampling for RL with LLMs (ICLR 2026)

- **论文**: Dilip Arumugam, Thomas L. Griffiths, "Toward Efficient Exploration by Large Language Model Agents", ICLR 2026
- **链接**: https://arxiv.org/abs/2504.20997
- **核心方法**: 用 LLM 显式实现 PSRL 算法，将探索问题形式化为后验采样。
- **探索机制**: PSRL 通过贝叶斯后验更新和采样提供原则性的探索策略，LLM 作为实现该算法的计算载体。

---

## 6. 总结与 Idea A 的关联

### 关键发现

| 探索策略类别 | 代表方法 | 核心机制 | 适用场景 | 成熟度 |
|---|---|---|---|---|
| **MCTS-based** | RAP, SE-Agent, MCTS-AHD, PlanU | 树搜索 + UCB/不确定性估计 | 推理、规划、代码生成 | 高（多篇顶会） |
| **UCB/Bandit** | Double TS, PSRL, In-Context Exp | 后验采样、置信区间 | 查询优化、反馈收集 | 中-高 |
| **Intrinsic Motivation** | IMAGINE, MOTIF, ONI | 内在奖励替代/补充外部奖励 | RL 训练、稀疏奖励场景 | 中-高 |
| **Diversity-based** | ETO, DPEPO, APP, Explorer | 对比学习、多样性奖励、并行探索 | 轨迹优化、数据合成 | 中 |
| **Structured Exploration** | SGE, Go-Browse, LaMer, LLM-Explorer | 策略空间探索、图搜索、Meta-RL | Web agent、具身 agent、多步推理 | 中（2025-2026 新兴） |

### 对 Idea A 的启示

1. **MCTS 是最成熟的基础框架**：RAP 和 SE-Agent 证明了 MCTS 在 LLM Agent 探索中的有效性。Idea A 可考虑以 MCTS 为基础骨架，结合其他探索策略增强。

2. **内在动机 + 多样性是重要补充**：IMAGINE 和 DPEPO 表明，仅靠 MCTS 的 UCB 公式可能不足以应对复杂场景。引入内在奖励和多样性惩罚可以显著提升探索质量。

3. **策略空间探索是前沿方向**：SGE 将探索从动作空间提升到策略空间，与 Idea A 可能的高层规划需求高度相关。

4. **Meta-RL 提供长期探索能力**：LaMer 的跨 episode 学习使 agent 能积累探索经验，适合需要多轮交互的复杂任务。

5. **结构化探索降低样本复杂度**：Go-Browse 的图搜索框架和 SGE 的策略引导都显著减少了无效探索，这对计算资源有限的场景尤为重要。

6. **探索与利用的分离评估**：Harris & Slivkins (2025) 的工作提示我们，在设计 Idea A 时应明确区分探索和利用模块，分别优化。

### 推荐的研究方向

- **混合探索框架**：结合 MCTS 的结构化搜索 + 内在动机的密集奖励 + 多样性惩罚，形成三层探索机制。
- **自适应探索策略**：借鉴 LLM-Explorer 的思路，让 agent 根据任务难度和学习阶段动态调整探索策略。
- **探索效率优先**：参考 PSRL-LLM 和 Go-Browse，优先保证探索的统计效率和样本效率。
