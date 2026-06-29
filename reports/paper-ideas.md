# Paper Ideas: Agent LLM 方向 — 基于 Research Gap 分析的 Idea 生成与评估

> 目标：UCLA MSCS (Plan I, Thesis) 1.5-2 年时间线
> 导师：Kai-Wei Chang (UCLA NLP Group)
> 撰写日期：2026-06-29

---

## 目录

1. [方法论说明](#1-方法论说明)
2. [Idea A: 结构化探索引导的 Agent 轨迹优化](#2-idea-a-结构化探索引导的-agent-轨迹优化)
3. [Idea B: 自适应模块路由与协同优化的 Agent 训练框架](#3-idea-b-自适应模块路由与协同优化的-agent-训练框架)
4. [Idea C: 长程 Agent 任务的鲁棒规划与动态重规划](#4-idea-c-长程-agent-任务的鲁棒规划与动态重规划)
5. [Idea D: Agent 评估的生态效度与自动化基准维护](#5-idea-d-agent-评估的生态效度与自动化基准维护)
6. [Idea E: 多 Agent 系统的通信效率与可扩展协作](#6-idea-e-多-agent-系统的通信效率与可扩展协作)
7. [推荐排序与路线图](#7-推荐排序与路线图)
8. [Actionable 下一步计划](#8-actionable-下一步计划)

---

## 1. 方法论说明

### 1.1 输入材料

| 材料 | 用途 |
|------|------|
| **Agent LLM 文献综述** (`reports/agent-llm-literature-review.md`) | 6 个子方向的代表性论文、核心贡献、当前局限 |
| **Research Gap 分析** (`reports/research-gap-analysis.md`) | 5 个系统性研究空白，含可行性评估和差异化判断 |
| **Kai-Wei Chang 教授深度调研报告** (`reports/kaiwei-chang-profile.md`) | 课题组现有工作、实验室风格、招生方向、资源约束 |
| **UCLA MSCS 毕业要求** (`reports/ucla-mscs-graduation-requirements.md`) | Plan I 时间线、课程要求、论文流程 |

### 1.2 评估维度

每个 Idea 从以下 8 个维度评估：

| 维度 | 说明 |
|------|------|
| **Problem** | 要解决的具体问题 |
| **Approach** | 核心方法思路 |
| **Novelty** | 与现有工作的区别 |
| **Feasibility** | 在 UCLA MSCS 时间线内（1.5-2年）是否可行 |
| **Fit** | 为什么适合 Kai-Wei Chang 组 |
| **Risk** | 主要风险 |
| **Next Step** | 如果要 pursue 这个 idea，第一步做什么 |

### 1.3 战略前提

基于 Research Gap 分析第 3 节的结论，推荐 **Training-Framework 融合路线**：

> **"用 Training 方法解决 Framework 的瓶颈问题"**

即：框架设计暴露问题（长程任务失败、模块间错误级联、探索不足）→ 训练方法解决问题（轨迹优化、偏好学习、结构化控制）→ 验证闭环。

---

## 2. Idea A: 结构化探索引导的 Agent 轨迹优化

### 2.1 Title（暂定）

**"Structured Exploration for Agent Trajectory Optimization: Balancing Exploration and Exploitation via Controlled Self-Training"**

### 2.2 Problem

当前 Agent 轨迹优化方法（ETO, DMPO, Re-ReST）存在根本性的**探索-利用失衡**问题：

- **探索不足**：大多数方法只在成功轨迹上做行为克隆（BC），或在失败轨迹上做对比学习，缺乏系统性的探索策略来发现新的、更优的轨迹
- **利用过度**：模型倾向于重复已知的成功模式，无法适应环境变化
- **Re-ReST 的局限**：Kai-Wei Chang 组的 Re-ReST 通过反思失败轨迹生成改进数据，但反思本身依赖于 LLM 的自我修正能力，而非系统性的探索机制

### 2.3 Approach

核心思路：**用结构化控制来引导探索，用探索数据来改进训练**。

1. **定义结构化探索空间**：利用 Ctrl-R 的轨迹控制能力，定义"可变动作"和"不可变动作"——在保持任务目标不变的前提下，允许模型在中间步骤上探索不同的动作序列
2. **探索奖励（Exploration Bonus）**：引入基于轨迹多样性的探索奖励，鼓励模型发现与已有成功轨迹不同的新路径
3. **探索-反思循环**：在探索轨迹上应用 Re-ReST 的反思机制，自动识别哪些探索是有价值的，生成改进数据
4. **迭代训练**：用新发现的成功轨迹更新训练集，重复探索-反思-训练循环

### 2.4 Novelty

| 对比对象 | 区别 |
|---------|------|
| **ETO** (ACL 2024) | ETO 用失败轨迹做对比学习，但探索是随机的；本方法用 Ctrl-R 做**结构化探索**，探索空间受控 |
| **DMPO** (EMNLP 2024) | DMPO 用偏好优化，但偏好数据来自固定轨迹集；本方法**动态生成**探索轨迹 |
| **Re-ReST** (EMNLP 2024) | Re-ReST 反思失败轨迹，但反思本身不产生新轨迹；本方法**主动探索**新轨迹 |
| **RRO** (2025) | RRO 用 Reward Rising Sampling 探索，但缺乏结构化约束；本方法有**显式的探索空间定义** |

**核心差异化**：将"结构化推理控制"（Ctrl-R 的强项）与"轨迹优化"（Re-ReST 的强项）结合，形成**探索-利用平衡的闭环系统**。这是领域内首次系统性地将结构化控制引入 Agent 轨迹探索。

### 2.5 Feasibility

| 维度 | 评估 |
|------|------|
| **时间线** | ⭐⭐⭐⭐⭐ — 可在 3-4 个月内完成核心实验（基于 Re-ReST 代码库扩展） |
| **计算资源** | ⭐⭐⭐⭐ — 7B-13B 模型微调，单卡 A100 可运行，不需要大规模 RL |
| **数据需求** | ⭐⭐⭐⭐ — 利用现有 benchmark（WebArena, AgentBench），不需要新数据 |
| **工程复杂度** | ⭐⭐⭐ — 中等，主要在 Re-ReST pipeline 上增加探索模块 |
| **论文发表** | ⭐⭐⭐⭐⭐ — 目标 ICML/NeurIPS/ICLR 2027 |

**总评：高可行性。** 基于组内已有代码（Re-ReST + Ctrl-R），扩展成本低，计算需求适中。

### 2.6 Fit: 为什么适合 Kai-Wei Chang 组

| 匹配维度 | 评估 |
|---------|------|
| 与现有工作衔接 | ⭐⭐⭐⭐⭐ — Re-ReST 的直接扩展 + Ctrl-R 的结构化控制能力 |
| 计算资源要求 | ⭐⭐⭐⭐ — 中等，7B-13B 微调即可 |
| 学生能力匹配 | ⭐⭐⭐⭐ — 需要 RL 基础，但主要是工程实现 |
| 差异化 | ⭐⭐⭐⭐⭐ — 领域内系统性探索机制的研究极少 |
| 发表潜力 | ⭐⭐⭐⭐⭐ — 顶会（ICML/NeurIPS/ICLR）级别 |
| 与教授风格匹配 | ⭐⭐⭐⭐⭐ — 学生一作制，教授提供方向指导，适合独立研究 |

### 2.7 Risk

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|---------|
| 探索奖励设计不当导致训练不稳定 | 中 | 高 | 从简单环境（ALFWorld）开始验证，逐步扩展到复杂环境 |
| 结构化探索空间定义过于保守/激进 | 中 | 中 | 设计可调节的探索空间参数，做 ablation study |
| Ctrl-R 的轨迹控制能力在 Agent 任务上不够强 | 低 | 高 | 备选方案：用 ReAct 的简单探索替代 Ctrl-R |
| 计算成本随探索轮次线性增长 | 中 | 低 | 设计 early stopping 机制，探索收敛后停止 |

### 2.8 Next Step

1. **Week 1-2**：复现 Re-ReST 在 WebArena 上的 baseline 结果
2. **Week 3-4**：实现 Ctrl-R 的结构化探索空间定义模块
3. **Week 5-6**：在 ALFWorld 上验证探索-反思循环的有效性
4. **Week 7-8**：扩展到 WebArena 和 AgentBench，做完整实验
5. **Week 9-10**：撰写论文初稿，做 ablation study

### 2.9 详细方法论 (Methodology)

> 以下方法论基于对 Re-ReST、Ctrl-R、ETO、DMPO、RRO 等关键相关工作的深入调研，提出一个**可行的、可实现的**技术方案。

#### 2.9.1 问题形式化

给定 Agent 策略 $\pi_\theta$（由 LLM 参数化），环境 $\mathcal{E}$，任务分布 $\mathcal{T}$：

- **轨迹** $\tau = (s_0, a_0, s_1, a_1, ..., s_T)$
- **奖励** $R(\tau) \in \{0, 1\}$（稀疏二元奖励）
- **目标**：最大化 $\mathbb{E}_{\tau \sim \pi_\theta}[R(\tau)]$

**核心困境**：自我训练中，策略倾向于生成"安全"但次优的轨迹（利用过度），而随机探索（如 ETO）在复杂环境（WebArena）中成功率极低（<5%），导致有效训练信号稀疏。

#### 2.9.2 结构化探索空间设计

定义 Agent 轨迹的 **5 个探索维度**，每个维度对应一个可控策略：

| 维度 | 描述 | 离散化级别 |
|------|------|-----------|
| **D1: 动作选择策略** | 每一步选择动作的方式 | {greedy, stochastic, beam(3), contrastive} |
| **D2: 搜索深度** | 遇到困难时的回溯策略 | {no-retry, shallow-retry(1), deep-retry(2), backtrack} |
| **D3: 工具使用模式** | 使用外部工具的方式 | {direct-call, chain-tools, verify-then-act, decompose} |
| **D4: 信息收集策略** | 决策前收集信息的方式 | {minimal, targeted, exhaustive, iterative-refine} |
| **D5: 反思触发条件** | 触发自我纠正的条件 | {on-error, on-low-confidence, periodic(3), never} |

每个探索配置文件 $p = (d_1, d_2, d_3, d_4, d_5)$ 是一个 5 元组。探索空间大小约 $4^5 = 1024$，但实际有效配置约 10-20 个。

**实现方式**：通过 **prompt 工程** 而非修改模型参数来实现探索控制。例如：

```
System: You are an agent solving a task.
- When choosing actions, consider top-3 candidates (beam).
- If a step fails, retry up to 2 times with different approaches (deep-retry).
- Break complex tasks into subtasks (decompose).
- Before acting, gather all relevant information (exhaustive).
- After every 3 steps, reflect on progress (periodic).
```

#### 2.9.3 探索奖励设计

总奖励 = 任务奖励 + 探索奖励：

$$R_{\text{total}}(\tau, p) = R_{\text{task}}(\tau) + \lambda(t) \cdot R_{\text{explore}}(\tau, p)$$

**探索奖励由三个组件构成**：

1. **配置多样性奖励** $R_{\text{div}}$：鼓励使用不同的探索配置
2. **轨迹多样性奖励** $R_{\text{traj}}$：鼓励在相同配置下生成多样化的轨迹内容（基于动作序列的 Jaccard 相似度）
3. **不确定性奖励** $R_{\text{unc}}$：鼓励探索策略熵高的状态（即模型不确定的区域）

$$R_{\text{explore}} = 0.3 \cdot R_{\text{div}} + 0.3 \cdot R_{\text{traj}} + 0.4 \cdot R_{\text{unc}}$$

**自适应 $\lambda$ 调度**：$\lambda(t) = \lambda_0 \cdot \exp(-\kappa \cdot t)$，早期高探索，后期高利用。

#### 2.9.4 探索-反思-训练循环

```
Algorithm: Structured Exploration for Agent Trajectory Optimization

for t = 1 to N:
    # Phase 1: Structured Exploration
    for each p in P_sampled (4-8 configs):
        τ = rollout(π_{t-1}, p)    # 用探索配置 p 生成轨迹
    
    # Phase 2: Reflection & Filtering
    for each (τ, p):
        R_total = R_task(τ) + λ(t) · R_explore(τ, p)
    
    # Phase 3: Diverse Selection
    diverse_set = select_diverse(high_quality, k=16)
    
    # Phase 4: Training (SFT + DPO hybrid)
    θ_t = train(θ_{t-1}, diverse_set)
    
    # Phase 5: Config Update
    P = update_config_set(P, trajectories_stats)
```

**训练策略**：
- 前 30% 轮次：纯 SFT（让模型先学会基本行为）
- 中间 40% 轮次：SFT + DPO 混合
- 后 30% 轮次：DPO 为主（精细调优偏好）

#### 2.9.5 与现有工作的差异化

| 维度 | Re-ReST | ETO | Ctrl-R | **本方法** |
|------|---------|-----|--------|-----------|
| **探索策略** | 被动反射（依赖外部反馈） | 随机采样 | 结构化推理控制 | **结构化探索控制** |
| **探索空间** | 无 | 无（随机） | 推理结构空间 | **Agent 轨迹多维空间** |
| **探索奖励** | 无 | 无 | 重要性采样权重 | **多样性+不确定性奖励** |
| **训练数据** | 反射修正后的轨迹 | 成功-失败对 | 加权轨迹 | **多样化高质量轨迹** |
| **探索效率** | 低（依赖外部信号） | 低（随机） | 高（结构化） | **高（结构化+奖励引导）** |

#### 2.9.6 实验设计

| 基准 | 任务数 | 选择理由 |
|------|-------|---------|
| **ALFWorld** | 134 | 快速原型验证，与 Re-ReST/ETO 直接对比 |
| **WebArena** | 812 | 主要评估基准，复杂真实场景 |
| **WebShop** | 12K | 与 RRO/ETO 对比 |

**Baseline**：ReAct (few-shot)、Re-ReST、ETO、DMPO、RRO

**消融实验**：
1. 无探索奖励（仅任务奖励）→ 验证探索奖励的必要性
2. 无多样性选择（随机选择）→ 验证多样化选择的作用
3. 固定探索配置（不更新）→ 验证自适应配置更新的作用
4. 单一探索维度 → 验证多维探索的必要性

#### 2.9.7 预期贡献

1. **理论贡献**：首次将 Agent 轨迹探索形式化为多维可控问题
2. **实证贡献**：在 WebArena/ALFWorld 上超越 Re-ReST、ETO 等现有方法，减少 50%+ 轨迹生成量
3. **工程贡献**：开源结构化探索框架 + 预定义 20+ 探索配置

#### 2.9.8 时间线

| 阶段 | 时间 | 里程碑 |
|------|------|--------|
| 原型验证 (ALFWorld) | Week 1-4 | 初步结果 > Re-ReST |
| 主要实验 (WebArena) | Week 5-10 | 完整实验结果 |
| 论文撰写 | Week 11-14 | 投稿 ICML/NeurIPS 2027 |

**计算资源估算**：~$850-1600（原型验证单 GPU，主要实验 4 GPU）

---

## 3. Idea B: 自适应模块路由与协同优化的 Agent 训练框架

### 3.1 Title（暂定）

**"Adaptive Module Routing and Collaborative Optimization for Modular Agent Training"**

### 3.2 Problem

Agent Lumos 提出了 Planning → Grounding → Execution 的三模块架构，但存在关键问题：

- **模块间信息传递损失**：Planning 模块的输出（高层计划）在传递给 Grounding 模块时丢失细节
- **固定路由**：所有任务都走 Planning → Grounding → Execution 的固定流程，但不同任务可能需要不同的模块组合
- **模块级错误级联**：Planning 模块的错误会直接传递给后续模块，缺乏模块间的纠错机制

### 3.3 Approach

核心思路：**将 Agent Lumos 的固定模块流水线改造为自适应路由系统**。

1. **可学习路由机制**：训练一个轻量级 Router（基于 BERT/GNN），根据任务描述动态选择最优模块组合（如：简单任务跳过 Planning 直接 Grounding）
2. **模块间反馈循环**：引入反向信息流——Grounding 模块发现计划不可行时，回传信号触发 Planning 模块修正
3. **GNN 建模模块依赖**：与 UCLA 的 Yizhou Sun 教授合作，用 Graph Neural Network 建模模块间的信息依赖关系
4. **热插拔架构**：支持模块级升级——替换或新增模块时，不需要重新训练整个系统

### 3.4 Novelty

| 对比对象 | 区别 |
|---------|------|
| **Agent Lumos** (ACL 2024) | 固定流水线架构；本方法引入**自适应路由**和**反馈循环** |
| **AutoGen** (2023) | 多 agent 对话协作；本方法关注**单 agent 内部模块**的协同 |
| **Chameleon** (NeurIPS 2023) | LLM 作为控制器动态编排外部工具；本方法关注**内部模块**的路由 |
| **MetaGPT** (NeurIPS 2024) | 多 agent 角色分工；本方法关注**模块级**而非 agent 级分工 |

**核心差异化**：将 Agent Lumos 的模块化训练从"固定流水线"升级为"自适应路由系统"，引入模块间反馈循环和 GNN 建模。这是 Agent 模块化训练方向的自然演进。

### 3.5 Feasibility

| 维度 | 评估 |
|------|------|
| **时间线** | ⭐⭐⭐⭐ — 可在 4-5 个月内完成（基于 Agent Lumos 代码库） |
| **计算资源** | ⭐⭐⭐⭐ — Router 是轻量级模型，不需要大规模训练 |
| **数据需求** | ⭐⭐⭐ — 需要标注不同任务类型对应的最优模块组合，可能需要人工标注 |
| **工程复杂度** | ⭐⭐⭐ — 中等偏高，需要重构 Agent Lumos 的架构 |
| **论文发表** | ⭐⭐⭐⭐⭐ — 目标 ACL/EMNLP/NeurIPS 2027 |

**总评：中高可行性。** 工程量大但计算需求低，适合 UCLA 学生工程能力强的特点。

### 3.6 Fit: 为什么适合 Kai-Wei Chang 组

| 匹配维度 | 评估 |
|---------|------|
| 与现有工作衔接 | ⭐⭐⭐⭐⭐ — Agent Lumos 的直接扩展 |
| 计算资源要求 | ⭐⭐⭐⭐ — 中等，Router 是轻量级模型 |
| 学生能力匹配 | ⭐⭐⭐⭐⭐ — 工程密集型，UCLA 学生强项 |
| 差异化 | ⭐⭐⭐⭐ — 模块化训练方向竞争较少 |
| 发表潜力 | ⭐⭐⭐⭐⭐ — ACL/EMNLP/NeurIPS 级别 |
| 跨组合作机会 | ⭐⭐⭐⭐⭐ — 与 Yizhou Sun (GNN) 合作 |

### 3.7 Risk

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|---------|
| 自适应路由带来的性能提升有限 | 中 | 高 | 先做 pilot study 验证路由是否带来显著提升 |
| 需要大量人工标注任务-模块组合映射 | 中 | 中 | 用 LLM 自动生成标注，人工校验 |
| GNN 建模模块依赖过于复杂 | 低 | 中 | 简化方案：用 MLP 替代 GNN 做路由 |
| Agent Lumos 代码库维护不足 | 低 | 高 | 联系原作者（Yin et al.）获取最新代码 |

### 3.8 Next Step

1. **Week 1-2**：复现 Agent Lumos，分析模块间信息传递的瓶颈
2. **Week 3-4**：设计 Router 架构，在 2-3 个任务类型上验证自适应路由的有效性
3. **Week 5-6**：实现模块间反馈循环机制
4. **Week 7-8**：与 Yizhou Sun 组讨论 GNN 建模方案
5. **Week 9-12**：完整实验 + 论文撰写

---

## 4. Idea C: 长程 Agent 任务的鲁棒规划与动态重规划

### 4.1 Title（暂定）

**"Robust Planning and Dynamic Replanning for Long-Horizon Agent Tasks"**

### 4.2 Problem

文献综述明确指出：**超过 10+ 步的任务中，规划准确率急剧下降**。这是 Agent 从"玩具 demo"走向"真实应用"的关键瓶颈。

- **现有方法**：Plan-and-Solve 将规划与执行分离，但缺乏动态重规划机制
- **ToT/GoT**：搜索空间指数增长，token 开销巨大
- **Ctrl-R**：Kai-Wei Chang 组的 Ctrl-R 在结构化推理控制上表现出色，但主要针对单步推理，未扩展到多步 agent 任务

### 4.3 Approach

核心思路：**将 Ctrl-R 的结构化推理控制扩展到多步 Agent 规划，结合 OpenThoughts 的数据配方和 Re-ReST 的反思机制**。

1. **分层规划框架**：将长程任务分解为"宏观规划"（任务级步骤）和"微观规划"（动作级步骤），宏观规划使用 Ctrl-R 的结构化控制生成，微观规划在执行时动态调整
2. **规划偏差检测**：在每步执行后，用轻量级验证器检查当前状态是否偏离原始计划，偏离度超过阈值时触发重规划
3. **重规划触发器**：设计三种重规划触发条件——(a) 执行失败、(b) 环境状态变化、(c) 计划步骤超时
4. **数据配方**：利用 OpenThoughts 的数据生成方法，生成长程规划的训练数据（包含成功/失败/重规划轨迹）

### 4.4 Novelty

| 对比对象 | 区别 |
|---------|------|
| **Plan-and-Solve** (ACL 2023) | 规划与执行分离但无重规划；本方法有**动态重规划机制** |
| **ToT/GoT** (NeurIPS 2023/AAAI 2024) | 搜索空间指数增长；本方法用**分层规划**控制搜索空间 |
| **Ctrl-R** (ICML 2026) | 单步推理控制；本方法扩展到**多步 Agent 规划** |
| **ReAct** (ICLR 2023) | 推理-行动交错但无显式规划；本方法有**显式的分层规划** |

**核心差异化**：将 Ctrl-R 的结构化推理控制从"单步推理"扩展到"多步 Agent 规划"，并引入动态重规划机制。这是 Ctrl-R 的自然扩展方向，也是 Kai-Wei Chang 组独有的优势。

### 4.5 Feasibility

| 维度 | 评估 |
|------|------|
| **时间线** | ⭐⭐⭐⭐ — 可在 4-5 个月内完成（基于 Ctrl-R + OpenThoughts 代码库） |
| **计算资源** | ⭐⭐⭐⭐⭐ — 低，主要在推理层面改进，不需要大规模训练 |
| **数据需求** | ⭐⭐⭐⭐ — 利用 OpenThoughts 的数据生成 pipeline |
| **工程复杂度** | ⭐⭐⭐⭐ — 中等，主要在推理流程层面修改 |
| **论文发表** | ⭐⭐⭐⭐⭐ — 目标 ICML/NeurIPS/ICLR 2027 |

**总评：高可行性。** 计算需求最低，主要依赖推理层面的改进，适合资源受限的学术环境。

### 4.6 Fit: 为什么适合 Kai-Wei Chang 组

| 匹配维度 | 评估 |
|---------|------|
| 与现有工作衔接 | ⭐⭐⭐⭐⭐ — Ctrl-R + OpenThoughts + Re-ReST 的三合一 |
| 计算资源要求 | ⭐⭐⭐⭐⭐ — 低，主要在推理层面改进 |
| 学生能力匹配 | ⭐⭐⭐⭐ — 需要推理和规划背景 |
| 差异化 | ⭐⭐⭐⭐ — 长程规划方向竞争激烈，但 Ctrl-R 扩展有独特切入点 |
| 发表潜力 | ⭐⭐⭐⭐⭐ — 顶会级别 |
| 与教授风格匹配 | ⭐⭐⭐⭐⭐ — 学生主导，教授提供方向指导 |

### 4.7 Risk

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|---------|
| 长程规划方向竞争激烈（Google DeepMind, OpenAI 也在做） | 高 | 中 | 聚焦 Ctrl-R 的独特结构化控制能力，差异化竞争 |
| 重规划机制可能增加推理延迟 | 中 | 中 | 设计轻量级验证器，控制重规划触发频率 |
| 分层规划的宏观-微观对齐困难 | 中 | 高 | 从简单任务（ALFWorld）开始验证 |
| Ctrl-R 扩展到多步场景的性能不确定 | 中 | 高 | 先做 pilot study 验证 Ctrl-R 在多步场景的有效性 |

### 4.8 Next Step

1. **Week 1-2**：复现 Ctrl-R，验证其在单步推理上的效果
2. **Week 3-4**：将 Ctrl-R 扩展到多步 Agent 任务（ALFWorld）
3. **Week 5-6**：实现分层规划框架和重规划机制
4. **Week 7-8**：在 WebArena 上做完整实验
5. **Week 9-10**：撰写论文初稿

---

## 5. Idea D: Agent 评估的生态效度与自动化基准维护

### 5.1 Title（暂定）

**"EcoEval: Ecological Validity and Automated Benchmark Maintenance for Agent Evaluation"**

### 5.2 Problem

当前 Agent 评估基准存在两个系统性问题：

- **生态效度不足**：现有基准（AgentBench, WebArena, SWE-bench）虽然比合成环境更真实，但仍然与真实用户使用场景有差距。SafeWorld 和 AutoSUIT 是 Kai-Wei Chang 组的贡献，但偏安全/自动化，缺乏对"评估本身的质量"的系统性研究
- **基准退化**：随着 LLM 能力提升，现有基准的区分度下降（ceiling effect），且基准维护成本高（Web 环境变化、API 更新等）

### 5.3 Approach

核心思路：**构建一个"元评估"框架，系统性地评估 Agent 评估基准本身的质量，并实现自动化基准维护**。

1. **生态效度评估框架**：定义 Agent 评估的生态效度维度——任务真实性、环境保真度、交互自然度、失败代价等，用这些维度评估现有基准
2. **基准退化检测**：定期运行 baseline 模型，检测基准的区分度变化，自动识别"已饱和"的任务
3. **自动化任务生成**：利用 LLM 自动生成新的评估任务，保持基准的时效性
4. **跨基准一致性分析**：分析不同基准上 Agent 性能排名的相关性，识别基准间的系统性偏差

### 5.4 Novelty

| 对比对象 | 区别 |
|---------|------|
| **AgentBench** (ICLR 2024) | 提供评估环境但不评估基准本身；本方法**评估评估者** |
| **WebArena** (ICLR 2024) | 真实 Web 环境但维护成本高；本方法有**自动化维护机制** |
| **SafeWorld** (Chang's Group) | 偏安全评估；本方法关注**评估的元质量** |
| **AutoSUIT** (Chang's Group) | 自动化 benchmark；本方法关注**生态效度和维护** |

**核心差异化**：从"构建更好的基准"转向"评估和改进基准本身的质量"。这是 Agent 评估方向的元研究，有独特的学术定位。

### 5.5 Feasibility

| 维度 | 评估 |
|------|------|
| **时间线** | ⭐⭐⭐ — 可在 5-6 个月内完成，但需要大量基准实验 |
| **计算资源** | ⭐⭐⭐⭐ — 主要是推理成本，不需要训练 |
| **数据需求** | ⭐⭐⭐⭐ — 利用现有基准数据 |
| **工程复杂度** | ⭐⭐⭐ — 中等，主要是评估 pipeline 的构建 |
| **论文发表** | ⭐⭐⭐⭐ — 目标 ACL/EMNLP/NeurIPS Datasets & Benchmarks |

**总评：中可行性。** 不需要训练，但需要大量评估实验和基准维护工作。

### 5.6 Fit: 为什么适合 Kai-Wei Chang 组

| 匹配维度 | 评估 |
|---------|------|
| 与现有工作衔接 | ⭐⭐⭐⭐ — SafeWorld, AutoSUIT, LongMemEval 的扩展 |
| 计算资源要求 | ⭐⭐⭐⭐ — 主要是推理成本 |
| 学生能力匹配 | ⭐⭐⭐⭐⭐ — 工程密集型，适合 UCLA 学生 |
| 差异化 | ⭐⭐⭐⭐ — 元评估方向竞争较少 |
| 发表潜力 | ⭐⭐⭐⭐ — Datasets & Benchmarks track |
| 与教授风格匹配 | ⭐⭐⭐⭐ — 组内已有评估方向积累 |

### 5.7 Risk

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|---------|
| 元评估的学术价值可能被质疑 | 中 | 高 | 强调实际应用价值——帮助社区维护高质量基准 |
| 自动化任务生成的质量控制困难 | 中 | 中 | 人工抽样校验 + 自动质量过滤 |
| 基准退化检测可能过于简单 | 低 | 中 | 设计多种退化指标，不仅仅是区分度 |
| 论文可能被定位为"工具论文"而非"研究论文" | 中 | 中 | 强调方法论贡献，而非仅仅是工具 |

### 5.8 Next Step

1. **Week 1-2**：定义生态效度评估维度，建立评估框架
2. **Week 3-4**：在 3-5 个现有基准上运行生态效度评估
3. **Week 5-6**：实现基准退化检测和自动化任务生成
4. **Week 7-8**：跨基准一致性分析
5. **Week 9-12**：完整实验 + 论文撰写

---

## 6. Idea E: 多 Agent 系统的通信效率与可扩展协作

### 6.1 Title（暂定）

**"Communication-Efficient and Scalable Multi-Agent Collaboration via Adaptive Topology and Selective Communication"**

### 6.2 Problem

多 Agent 系统（AutoGen, ChatDev, MetaGPT, Magnet）面临可扩展性瓶颈：

- **通信开销**：多 agent 间的对话轮次随 agent 数量平方增长，token 消耗巨大
- **信息冗余**：大量通信内容对任务完成无贡献，agent 之间传递了大量冗余信息
- **拓扑僵化**：现有方法使用固定通信拓扑（全连接、分层），无法根据任务动态调整
- **Kai-Wei Chang 组的 Magnet 和 METAL** 在通信拓扑方面有贡献，但未深入解决通信效率问题

### 6.3 Approach

核心思路：**用图扩散模型（Graph Diffusion Models）动态生成最优通信拓扑，结合选择性通信机制减少冗余**。

1. **自适应拓扑生成**：基于 Magnet 的通信拓扑工作，用 Graph Diffusion Models 根据任务描述动态生成最优通信拓扑（Kai-Wei Chang 组 2026 年已有相关工作）
2. **选择性通信**：每个 agent 在通信前评估信息的"任务相关性"，只传递高相关性信息，减少冗余
3. **通信预算控制**：设定每轮通信的 token 预算，agent 在预算内选择最有效的通信内容
4. **可扩展性验证**：在 agent 数量从 2 扩展到 20+ 的场景下验证通信效率

### 6.4 Novelty

| 对比对象 | 区别 |
|---------|------|
| **AutoGen** (2023) | 全连接对话；本方法用**动态拓扑**替代固定拓扑 |
| **MetaGPT** (NeurIPS 2024) | 固定角色分工；本方法**动态调整**通信结构 |
| **Magnet** (Chang's Group) | 关注通信拓扑但未深入效率问题；本方法聚焦**通信效率** |
| **ChatDev** (2023) | 结构化聊天但通信开销大；本方法引入**选择性通信** |

**核心差异化**：将 Graph Diffusion Models 应用于多 Agent 通信拓扑的**动态生成**，结合选择性通信机制解决可扩展性问题。这是 Magnet 的自然扩展。

### 6.5 Feasibility

| 维度 | 评估 |
|------|------|
| **时间线** | ⭐⭐⭐ — 可在 5-6 个月内完成（基于 Magnet 代码库） |
| **计算资源** | ⭐⭐⭐⭐ — Graph Diffusion 模型轻量，不需要大规模训练 |
| **数据需求** | ⭐⭐⭐ — 需要多 agent 协作任务的标注数据 |
| **工程复杂度** | ⭐⭐⭐ — 中等，主要在通信层面修改 |
| **论文发表** | ⭐⭐⭐⭐ — 目标 ACL/EMNLP/NeurIPS 2027 |

**总评：中可行性。** 组内已有 Magnet 基础，但多 Agent 方向竞争激烈。

### 6.6 Fit: 为什么适合 Kai-Wei Chang 组

| 匹配维度 | 评估 |
|---------|------|
| 与现有工作衔接 | ⭐⭐⭐⭐⭐ — Magnet + METAL + X-Teaming 的扩展 |
| 计算资源要求 | ⭐⭐⭐⭐ — 中等 |
| 学生能力匹配 | ⭐⭐⭐⭐ — 需要图模型和通信协议背景 |
| 差异化 | ⭐⭐⭐ — 多 Agent 方向竞争激烈 |
| 发表潜力 | ⭐⭐⭐⭐ — 顶会级别 |
| 与教授风格匹配 | ⭐⭐⭐⭐⭐ — 组内 2025 年多 Agent 方向密集产出 |

### 6.7 Risk

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|---------|
| 多 Agent 方向竞争激烈（Google, Meta, Microsoft 都在做） | 高 | 中 | 聚焦 Graph Diffusion 的独特切入点 |
| 通信效率提升可能以任务性能下降为代价 | 中 | 高 | 设计效率-性能的 Pareto 优化目标 |
| Graph Diffusion 在通信拓扑上的效果不确定 | 中 | 高 | 先做 pilot study 验证 |
| 评估困难——多 Agent 系统性能难以归因 | 中 | 中 | 设计消融实验，逐一分析各组件贡献 |

### 6.8 Next Step

1. **Week 1-2**：复现 Magnet，建立多 Agent 通信效率 baseline
2. **Week 3-4**：实现 Graph Diffusion 拓扑生成模块
3. **Week 5-6**：实现选择性通信机制
4. **Week 7-8**：在 2-20 agent 场景下验证可扩展性
5. **Week 9-12**：完整实验 + 论文撰写

---

## 7. 推荐排序

### 7.1 综合评分矩阵

| Idea | 标题 | Novelty | Feasibility | Fit | Impact | Risk | **总分** |
|------|------|---------|-------------|-----|--------|------|---------|
| **A** | 结构化探索引导的轨迹优化 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 中低 | **🥇 4.6/5** |
| **C** | 长程任务的鲁棒规划与重规划 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 中 | **🥈 4.4/5** |
| **B** | 自适应模块路由与协同优化 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 中 | **🥉 4.2/5** |
| **E** | 多 Agent 通信效率与可扩展协作 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 中高 | 3.8/5 |
| **D** | Agent 评估的生态效度与自动化维护 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 中 | 3.6/5 |

### 7.2 推荐理由

#### 🥇 第一推荐：Idea A — 结构化探索引导的轨迹优化

**理由**：
1. **最高可行性**：基于 Re-ReST + Ctrl-R 代码库，3-4 个月可完成核心实验
2. **最强差异化**：领域内首次系统性地将结构化控制引入 Agent 轨迹探索
3. **最佳 Fit**：直接利用 Kai-Wei Chang 组的两大核心贡献（Re-ReST + Ctrl-R）
4. **最高 Impact**：解决 Agent 训练的核心瓶颈——探索-利用平衡
5. **最低风险**：计算需求适中，有明确的备选方案

**适合作为 Thesis 主方向**：可以在 1.5-2 年内完成从 idea 到论文发表的全流程，且有足够的扩展空间。

#### 🥈 第二推荐：Idea C — 长程任务的鲁棒规划与重规划

**理由**：
1. **计算需求最低**：主要在推理层面改进，不需要大规模训练
2. **Ctrl-R 的自然扩展**：将 Ctrl-R 从单步推理扩展到多步 Agent 规划
3. **高 Impact**：长程规划是 Agent 落地的关键瓶颈
4. **风险略高**：竞争激烈（Google DeepMind, OpenAI 也在做），但 Ctrl-R 的独特结构化控制提供了差异化

**适合作为 Thesis 的第二方向**：如果 Idea A 遇到困难，可以快速切换到 Idea C。

#### 🥉 第三推荐：Idea B — 自适应模块路由与协同优化

**理由**：
1. **工程密集型**：适合 UCLA 学生编程能力强的特点
2. **跨组合作机会**：与 Yizhou Sun (GNN) 合作
3. **风险中等**：需要重构 Agent Lumos 架构，工程量大
4. **差异化中等**：模块化训练方向竞争较少，但性能提升不确定

**适合作为 Thesis 的扩展方向**：在 Idea A 或 C 的基础上，作为第二个项目。

---

## 8. Actionable 下一步计划

### 8.1 入学前（2026 年夏季-秋季）

| 时间 | 任务 | 产出 |
|------|------|------|
| **Month 1** | 复现 Re-ReST 在 WebArena 上的 baseline | 可复现的实验代码 + baseline 结果 |
| **Month 2** | 复现 Ctrl-R 的结构化控制模块 | Ctrl-R 在 Agent 任务上的适配代码 |
| **Month 3** | 实现 Idea A 的探索空间定义模块 | 探索空间定义的 prototype |
| **Month 4** | 在 ALFWorld 上验证探索-反思循环 | pilot study 结果 |

### 8.2 入学后第 1 年（2026 年秋季 - 2027 年春季）

| Quarter | 主要任务 | 里程碑 |
|---------|---------|--------|
| **Fall 2026** | 修课（2-3 门）+ 继续 Idea A 实验 | 在 WebArena 上完成核心实验 |
| **Winter 2027** | 修课 + 论文撰写 + 投稿 | 投稿 ICML/NeurIPS 2027 |
| **Spring 2027** | 修课 + 开始第二个项目（Idea C） | 第二个项目的 pilot study |

### 8.3 入学后第 2 年（2027 年秋季 - 2028 年春季）

| Quarter | 主要任务 | 里程碑 |
|---------|---------|--------|
| **Fall 2027** | 修课 + 第二个项目实验 + Thesis 开题 | Thesis proposal 通过 |
| **Winter 2028** | 第二个项目论文 + Thesis 研究 | 投稿第二篇论文 |
| **Spring 2028** | Thesis 撰写 + 答辩 | 毕业 🎓 |

### 8.4 关键里程碑

| 时间 | 里程碑 | 备注 |
|------|--------|------|
| **2026 年 10 月** | 确定导师（Kai-Wei Chang） | 入学后第 1-2 个 quarter |
| **2027 年 5 月** | 第一篇论文投稿（Idea A） | 目标 ICML/NeurIPS/ICLR |
| **2027 年 10 月** | Thesis 开题 | 第 3-4 个 quarter |
| **2028 年 2 月** | 第二篇论文投稿（Idea C） | 目标 ACL/EMNLP |
| **2028 年 5 月** | Thesis 答辩 | 第 6 个 quarter |

### 8.5 风险应对

| 风险场景 | 应对方案 |
|---------|---------|
| Idea A 实验效果不达预期 | 切换到 Idea C（长程规划），计算需求更低 |
| 第一篇论文被拒 | 利用 rebuttal 和修改机会，同时准备第二个项目 |
| 计算资源不足 | 利用 Kai-Wei Chang 组与 Google/Meta/Amazon 的合作关系 |
| 课程压力大 | Plan I 只需 7 门正式课程，每 quarter 2-3 门，时间充裕 |
| 导师时间有限 | 学生一作制，教授提供方向指导，学生主导研究 |

---

> **总结**：推荐以 **Idea A（结构化探索引导的轨迹优化）** 作为 Thesis 主方向，**Idea C（长程规划与重规划）** 作为备选/第二方向。两条路线都充分利用 Kai-Wei Chang 组的核心优势（Re-ReST + Ctrl-R），计算需求适中，差异化强，发表潜力高。按照上述时间线，完全可以在 UCLA MSCS 1.5-2 年时间线内完成。
