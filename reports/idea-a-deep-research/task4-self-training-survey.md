# Agent 自我训练方法调研

> 调研日期：2025-06-29
> 范围：2022-2025 年主要论文，重点关注 LLM Agent 的自我训练与迭代训练方法

---

## 1. Self-Training 方法

### 1.1 STaR: Self-Taught Reasoner (NeurIPS 2022)

- **论文**: Zelikman et al., "STaR: Bootstrapping Reasoning With Reasoning"
- **链接**: https://arxiv.org/abs/2203.14465
- **核心思想**: 通过一个简单的循环实现自我训练：(1) 用少量 rationale 示例 prompt 模型生成推理链；(2) 如果答案错误，用正确答案作为 hint 重新生成 rationale；(3) 在所有最终得到正确答案的 rationale 上 fine-tune；(4) 重复。
- **关键贡献**: 首次提出"自举推理"范式，让模型从自己的正确推理中学习，无需大规模人工标注 rationale 数据。
- **局限性**: 依赖最终答案的正确性作为过滤信号，中间推理步骤的质量无法保证。

### 1.2 ReST: Reinforced Self-Training (DeepMind, 2023)

- **论文**: Gulcehre et al., "Reinforced Self-Training (ReST) for Language Modeling"
- **链接**: https://arxiv.org/abs/2308.08998
- **核心思想**: 受 growing batch RL 启发，提出 Grow 和 Improve 两阶段循环：(1) **Grow 阶段**：当前 policy 生成样本数据集；(2) **Improve 阶段**：用离线 RL 算法在过滤后的高质量数据集上 fine-tune policy。
- **关键贡献**: 将 self-training 与离线 RL 统一，数据可复用，比在线 RLHF 更高效。在机器翻译任务上验证有效。
- **后续发展**: ReSTEM (Singh et al., 2024) 将其扩展到数学推理任务。

### 1.3 Re-ReST: Reflection-Reinforced Self-Training (EMNLP 2024)

- **论文**: Dou et al., "Reflection-Reinforced Self-Training for Language Agents"
- **链接**: https://arxiv.org/abs/2406.01495
- **核心思想**: 在 self-training 中引入 **reflector**（反射模型），利用环境反馈（如单元测试结果、执行成功/失败）来改进低质量样本，而非直接丢弃。
- **关键贡献**:
  - 在 HotpotQA 上 self-training 提升 7.6%，Re-ReST 额外提升 2.0%
  - 在 AlfWorld 上 self-training 提升 28.4%，Re-ReST 额外提升 14.1%
  - 提出无需 ground-truth 反馈的推理时 reflection 方法
- **对 Agent 的意义**: 直接针对语言 Agent 的 self-training，利用环境交互反馈（执行结果）来提升样本质量，是 Agent 自我训练的重要范式。

### 1.4 SPIN: Self-Play Fine-Tuning (ICML 2024)

- **论文**: Chen et al., "Self-Play Fine-Tuning Converts Weak Language Models to Strong Language Models"
- **链接**: https://arxiv.org/abs/2401.01335
- **核心思想**: 基于博弈论中的 self-play 机制，LLM 通过与自身历史版本"对弈"来提升能力。模型生成训练数据，然后区分自生成响应与人类标注数据。
- **理论保证**: 证明训练目标函数的全局最优仅在 LLM policy 与目标数据分布一致时达到。
- **关键贡献**: 无需额外人工标注或更强模型，仅通过 self-play 即可持续提升模型能力，甚至超越使用 GPT-4 偏好数据的 DPO 训练。

### 1.5 ReST-MCTS*: LLM Self-Training via Process Reward Guided Tree Search (NeurIPS 2024)

- **论文**: Zhang et al., "ReST-MCTS*: LLM Self-Training via Process Reward Guided Tree Search"
- **链接**: https://arxiv.org/abs/2406.03816
- **核心思想**: 将 **MCTS* 树搜索** 与 **process reward** 结合，自动推断每步的 process reward（通过估计该步导向正确答案的概率），同时用于：(1) 作为 value target 训练 PRM；(2) 选择高质量轨迹用于 policy self-training。
- **关键贡献**:
  - 无需人工逐步骤标注即可训练 process reward model
  - 树搜索 policy 在相同搜索预算下优于 Best-of-N 和 Tree-of-Thought
  - 多轮迭代持续提升，优于 ReSTEM 和 Self-Rewarding LM
- **对 Agent 的意义**: 将 process reward 与 tree search 结合，为 Agent 的多步决策提供了细粒度训练信号。

---

## 2. Iterative DPO / RLHF

### 2.1 Self-Rewarding Language Models (Meta, ICML 2024)

- **论文**: Yuan et al., "Self-Rewarding Language Models"
- **链接**: https://arxiv.org/abs/2401.10020
- **核心思想**: 语言模型同时扮演两个角色：(1) instruction-following 模型生成响应；(2) LLM-as-a-Judge 提供自己的奖励。通过 **Iterative DPO** 框架，模型在每次迭代中自生成偏好数据并训练。
- **关键发现**: 在 Iterative DPO 训练过程中，不仅指令遵循能力提升，模型提供高质量奖励的能力也同步提升。
- **成果**: Llama 2 70B 经过 3 轮迭代后，在 AlpacaEval 2.0 上超越 Claude 2、Gemini Pro 和 GPT-4 0613。

### 2.2 Enhancing LLM Reasoning with Iterative DPO (COLM 2025)

- **论文**: Tu et al., "Enhancing LLM Reasoning with Iterative DPO: A Comprehensive Empirical Investigation"
- **链接**: https://arxiv.org/abs/2503.12854
- **核心思想**: 系统研究 DPO 在 post-training 中的效果，提出 **DPO-VP**（Verifiable Reward + DPO）：
  - 单轮 DPO + 粗粒度过滤即可显著提升数学推理能力
  - 设计迭代增强框架，generator 和 reward model 在多轮 DPO 中相互提升
  - 用简单可验证奖励（verifiable rewards）达到 RL 级别性能，计算开销大幅降低
- **关键贡献**: 证明 DPO 是 RL 的可扩展、低成本替代方案，在资源受限场景下实用。

### 2.3 Iterative Tool Usage Exploration for Multimodal Agents (NeurIPS 2025)

- **论文**: "Iterative Tool Usage Exploration for Multimodal Agents via..."
- **核心思想**: 针对多模态 Agent 的工具使用，提出迭代式偏好学习框架，减少对人类标注的依赖。
- **关键贡献**: 将 iterative DPO 扩展到多模态 Agent 的工具使用场景。

### 2.4 Building Math Agents with Multi-Turn Iterative Preference Learning

- **论文**: "Building Math Agents with Multi-Turn Iterative Preference Learning"
- **核心思想**: 提出多轮迭代 DPO 和 KTO 训练框架，有效提升模型在多轮推理任务上的能力。
- **关键贡献**: 将偏好学习从单轮扩展到多轮交互场景，适用于 Agent 的多步推理。

---

## 3. Self-Improvement 方法

### 3.1 Agent-R: Training Language Model Agents to Reflect via Iterative Self-Training (ByteDance, 2025)

- **论文**: Yuan et al., "Agent-R: Training Language Model Agents to Reflect via Iterative Self-Training"
- **链接**: https://arxiv.org/abs/2501.11425
- **核心思想**: 提出迭代自训练框架，使 Agent 学会在交互过程中**即时反思和纠错**：
  - 使用 MCTS 构建训练样本，从错误轨迹中恢复正确轨迹
  - 模型引导的 critique 构建机制：actor 模型识别失败轨迹中的第一个错误步骤，将其与相邻的正确路径拼接
  - 迭代式改进错误纠正能力和数据集构建
- **关键贡献**: 在三个交互式 Agent 环境中取得 +5.59% 的改进，使 Agent 学会主动识别和纠正错误动作，避免陷入循环。

### 3.2 Self-Generated In-Context Examples Improve LLM Agents (NeurIPS 2025)

- **论文**: "Self-Generated In-Context Examples Improve LLM Agents"
- **核心思想**: Agent 通过从自身成功经验中学习来自动改进，无需人工干预。提出轨迹 bootstrapping 和示例筛选框架。
- **关键贡献**: 利用 Agent 自身的成功轨迹作为 in-context examples，实现无需人类参与的持续改进。

### 3.3 Strategist: Self-Improvement of LLM Decision Making via Bi-Level Optimization (ICLR 2025)

- **论文**: "Strategist: Self-improvement of LLM Decision Making via Bi-Level Optimization"
- **核心思想**: 通过双层优化实现 LLM 决策能力的自我改进，STRATEGIST-based agents 在决策任务上优于传统 RL 方法和其他 LLM agent 方法。
- **关键贡献**: 将 self-improvement 形式化为双层优化问题，上层优化策略，下层优化执行。

### 3.4 Large Language Models Can Self-Improve At Web Agent Tasks

- **论文**: Patel et al., "Large Language Models Can Self-Improve At Web Agent Tasks"
- **链接**: https://openreview.net/forum?id=jwME4SY0an
- **核心思想**: 在 WebArena 基准上，通过合成数据 fine-tune 实现 Web Agent 的自我改进。
- **关键贡献**: 证明 self-improvement 范式在 Web Agent 任务上有效，模型可以通过迭代式自我改进持续提升。

### 3.5 WEBRL: Training LLM Web Agents via Self-Evolving Online RL (ICLR 2025)

- **论文**: "WEBRL: Training LLM Web Agents via Self-Evolving Online RL"
- **链接**: https://proceedings.iclr.cc/paper_files/paper/2025/file/c66e1fcc9691aae706250638f36f681b-Paper-Conference.pdf
- **核心思想**: 通过自演化的在线 RL 训练 Web Agent，将 Llama-3.1-8B 转化为熟练的 Web Agent。
- **关键贡献**: 将 self-evolving RL 应用于 Web Agent 训练，验证了自我改进在复杂交互环境中的有效性。

---

## 4. Process Reward / Outcome Reward 方法

### 4.1 AgentPRM: Process Reward Models for LLM Agents (Cornell, 2025)

- **论文**: Choudhury, "Process Reward Models for LLM Agents: Practical Framework and Directions"
- **链接**: https://arxiv.org/abs/2502.10325
- **核心思想**: 提出 **AgentPRM** 框架，遵循轻量级 actor-critic 范式：
  - **自动 PRM 标注**: 使用异步 Monte Carlo rollouts 计算 reward targets
  - **迭代训练**: PRM 和 policy 联合迭代训练，相互提升
  - **InversePRM**: 从专家演示中直接学习 process reward，无需显式结果监督
- **关键成果**: 3B 模型用 AgentPRM 和 InversePRM 训练后，在 ALFWorld 上超越 GPT-4o baseline。
- **对 Agent 的意义**: 专门为 Agent 场景设计的 PRM 框架，解决了长程决策中的 credit assignment 问题。

### 4.2 ReST-MCTS* (NeurIPS 2024) — 已在 1.5 节详述

- 通过 MCTS* 自动推断 process reward，无需人工逐步骤标注
- 将 process reward 同时用于 PRM 训练和高质量轨迹筛选

### 4.3 Process Reward Agents for Steering Knowledge-Intensive Tasks (2025)

- **论文**: "Process Reward Agents for Steering Knowledge-Intensive Tasks"
- **链接**: https://arxiv.org/html/2604.09482v1
- **核心思想**: 提出 Process Reward Agents (PRA)，一种 test-time 方法，为冻结 policy 提供领域相关的在线逐步骤奖励。
- **关键贡献**: 将 process reward 从训练阶段扩展到推理阶段，实现 test-time 的细粒度引导。

### 4.4 Principle Process Reward for Search Agents

- **论文**: "Principle Process Reward For Search Agents"
- **核心思想**: 训练基于原则的 reward model，提高过程评估的透明度和可靠性，并引入 Reward Normalization (ReNorm)。
- **关键贡献**: 将原则（principle）引入 process reward，使奖励信号更具可解释性。

### 4.5 VersaPRM: Multi-Domain Process Reward Model (ICML 2025)

- **论文**: "VersaPRM: Multi-Domain Process Reward Model via..."
- **核心思想**: 跨领域通用的 process reward model，通过增强推理时计算来提升数学推理能力。
- **关键贡献**: 将 PRM 从单领域扩展到多领域，提升泛化能力。

---

## 5. 总结与 Idea A 的关联

### 5.1 关键发现

| 维度 | 核心发现 |
|------|---------|
| **Self-Training 范式** | STaR → ReST → Re-ReST → ReST-MCTS* 逐步演进，从简单过滤到 reflection 增强再到 process reward 引导 |
| **Iterative DPO** | DPO 可作为 RL 的低成本替代，Self-Rewarding LM 和 DPO-VP 证明多轮迭代 DPO 可达到 RL 级别性能 |
| **Self-Improvement** | Agent-R 证明 Agent 可通过 MCTS 构建纠错训练数据实现自我改进；WEBRL 证明在线 self-evolving RL 有效 |
| **Process Reward** | AgentPRM 为 Agent 场景提供专用 PRM 框架；ReST-MCTS* 实现无需人工标注的 process reward 推断 |
| **Scaling 性质** | 多轮迭代训练普遍有效，但存在收益递减；process reward 比 outcome reward 提供更高效的训练信号 |

### 5.2 对 Idea A 的启示

1. **Self-Training 作为基础框架**: Idea A 可以采用 ReST 风格的 Grow-Improve 循环作为基础框架，Agent 在环境中交互收集数据，然后自我训练。

2. **Reflection 机制**: Re-ReST 和 Agent-R 都表明 reflection（反思）是 Agent 自我训练的关键组件。Idea A 应包含让 Agent 反思自身错误并从中学习的机制。

3. **Process Reward 优于 Outcome Reward**: AgentPRM 和 ReST-MCTS* 证明，在长程 Agent 任务中，process reward（每步奖励）比 outcome reward（最终结果奖励）提供更高效的训练信号。Idea A 应考虑引入 process reward。

4. **Iterative DPO 作为轻量级方案**: 如果 Idea A 的计算资源有限，Iterative DPO（如 DPO-VP）可作为 RL 的低成本替代方案。

5. **MCTS 用于数据构建**: ReST-MCTS* 和 Agent-R 都使用 MCTS 来构建高质量训练数据，这是 Agent 自我训练中数据质量保证的有效手段。

6. **Self-Play 潜力**: SPIN 和 Self-Rewarding LM 表明 self-play 机制可以让模型持续自我提升，Idea A 可考虑引入 Agent 与自身历史版本的对抗训练。

### 5.3 推荐研究方向

基于以上调研，推荐 Idea A 重点关注以下方向：
- **AgentPRM + ReST 融合**: 将 process reward 引入 self-training 循环，实现细粒度的 Agent 训练
- **Iterative DPO with Verifiable Rewards**: 利用 Agent 环境中的可验证反馈（如任务完成率）作为奖励信号，进行多轮 DPO 训练
- **Reflection-Augmented Self-Training**: 结合 Re-ReST 的 reflection 机制和 Agent-R 的即时纠错能力

---

## 参考文献

1. Zelikman et al., "STaR: Bootstrapping Reasoning With Reasoning", NeurIPS 2022
2. Gulcehre et al., "Reinforced Self-Training (ReST) for Language Modeling", 2023
3. Dou et al., "Re-ReST: Reflection-Reinforced Self-Training for Language Agents", EMNLP 2024
4. Chen et al., "Self-Play Fine-Tuning Converts Weak Language Models to Strong Language Models", ICML 2024
5. Zhang et al., "ReST-MCTS*: LLM Self-Training via Process Reward Guided Tree Search", NeurIPS 2024
6. Yuan et al., "Self-Rewarding Language Models", ICML 2024
7. Tu et al., "Enhancing LLM Reasoning with Iterative DPO", COLM 2025
8. Yuan et al., "Agent-R: Training Language Model Agents to Reflect via Iterative Self-Training", 2025
9. Choudhury, "Process Reward Models for LLM Agents: Practical Framework and Directions", 2025
10. Patel et al., "Large Language Models Can Self-Improve At Web Agent Tasks", 2024
11. "WEBRL: Training LLM Web Agents via Self-Evolving Online RL", ICLR 2025
12. "Strategist: Self-improvement of LLM Decision Making via Bi-Level Optimization", ICLR 2025
