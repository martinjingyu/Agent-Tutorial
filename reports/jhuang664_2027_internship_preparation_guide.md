# Jingyu Huang — 2027 Summer Internship 面试准备完全指南

> **目标角色**: AI/ML/LLM Agent Engineer Intern  
> **背景**: UW-Madison BS CS → UCLA MS CS | LLM Agent + RL Red-teaming + RAG  
> **准备周期**: 2026年6月 – 2027年2月

---

## 目录
1. [面试类型总览](#1-面试类型总览)
2. [各公司面试流程详解](#2-各公司面试流程详解)
3. [Coding 准备](#3-coding-准备)
4. [ML/DL 基础知识准备](#4-mldl-基础知识准备)
5. [LLM / Agent 专项准备](#5-llm--agent-专项准备)
6. [ML System Design 准备](#6-ml-system-design-准备)
7. [Behavioral 面试准备](#7-behavioral-面试准备)
8. [项目深度讨论准备](#8-项目深度讨论准备)
9. [量化公司专项准备](#9-量化公司专项准备)
10. [推荐学习资源清单](#10-推荐学习资源清单)
11. [每周学习计划](#11-每周学习计划)
12. [面试 Checklist](#12-面试-checklist)

---

## 1. 面试类型总览

对于你的背景和目标，面试主要分为以下 **5 种类型**：

| 类型 | 占比 | 难度 | 准备重点 |
|------|------|------|----------|
| **Coding / Algorithm** | 40% | ⭐⭐⭐ | LeetCode Medium-Hard, 数据结构与算法 |
| **ML/DL Fundamentals** | 25% | ⭐⭐⭐⭐ | Transformers, RL, Loss Functions, Training |
| **LLM / Agent 专项** | 15% | ⭐⭐⭐⭐ | RAG, Multi-agent, Tool-use, RLHF |
| **ML System Design** | 10% | ⭐⭐⭐⭐⭐ | 分布式训练, 推理优化, 数据流水线 |
| **Behavioral / Project Deep Dive** | 10% | ⭐⭐ | STAR 法则, 项目故事线, 动机 |

---

## 2. 各公司面试流程详解

### 🔴 Amazon SDE Intern (Austin)
| 轮次 | 时长 | 内容 | 难度 |
|------|------|------|------|
| OA (Online Assessment) | 90min | 2-3 coding + 行为问卷 | ⭐⭐ |
| Phone Screen | 45min | 1 coding (Medium) + LP | ⭐⭐⭐ |
| Final Round (3轮) | 3h | 2 coding (Medium) + 1 LP deep dive | ⭐⭐⭐ |

**特点**:
- **Leadership Principles (LP)** 是核心！每个回答都要体现 LP
- 高频 LP: Customer Obsession, Ownership, Deliver Results, Think Big, Dive Deep
- 你的 Amazon Nova Challenge 1st Place 是巨大加分项——面试中一定要讲这个故事
- AI/ML 团队可能额外问 ML 基础

**准备重点**:
- LeetCode: Arrays, Strings, HashMaps, Trees, Graphs, DP (Medium)
- LP 准备: 每个 LP 准备 1-2 个故事，用 STAR 格式
- 项目故事: Amazon Nova Challenge 完整叙述

---

### 🔴 Google SWE/ML Intern (Austin)
| 轮次 | 时长 | 内容 | 难度 |
|------|------|------|------|
| OA | 60min | 2 coding | ⭐⭐⭐ |
| Phone Screen | 45min | 1 coding (Medium-Hard) | ⭐⭐⭐⭐ |
| Virtual Onsite (2-3轮) | 2-3h | 2 coding + 1 Googleyness | ⭐⭐⭐⭐ |

**特点**:
- **窗口极窄**（10月中开放2-4周），必须提前准备好
- Coding 难度高于 Amazon，侧重算法和数据结构
- ML Intern 会有额外 ML 轮次
- Googleyness: 领导力、团队合作、模糊问题处理

**准备重点**:
- LeetCode: Trees, Graphs, DP, Strings (Medium-Hard)
- 时间复杂度分析要非常熟练
- 准备 "Why Google" + "Why Austin" 的回答

---

### 🟡 Meta AI/ML Intern (Austin)
| 轮次 | 时长 | 内容 | 难度 |
|------|------|------|------|
| OA | 70min | 2 coding | ⭐⭐⭐ |
| Phone Screen | 45min | 1 coding (Medium) | ⭐⭐⭐ |
| Virtual Onsite (3-4轮) | 3-4h | 1-2 coding + 1 ML system design + 1 behavioral | ⭐⭐⭐⭐ |

**特点**:
- ML 轮次会问: Transformer 架构、Attention 机制、Loss 函数选择、训练稳定性
- Coding 侧重: Arrays, Strings, DP (不常考 Graph)
- Behavioral: "Why Meta?" + 团队合作 + 冲突处理

**准备重点**:
- ML 基础: Transformer 从零推导、Self-attention 复杂度、Layer Norm vs Batch Norm
- Coding: 重点刷 Arrays/Strings/DP
- 准备 Meta 产品理解: Llama, AI Studio, 广告系统

---

### 🟡 Tesla AI/Autopilot Intern (Austin)
| 轮次 | 时长 | 内容 | 难度 |
|------|------|------|------|
| Phone Screen | 45min | 技术背景 + 动机 | ⭐⭐ |
| Technical Round 1 | 60min | Coding (Python/C++) | ⭐⭐⭐⭐ |
| Technical Round 2 | 60min | ML/RL deep dive | ⭐⭐⭐⭐⭐ |
| Final Round | 45min | Behavioral + Values fit | ⭐⭐⭐ |

**特点**:
- **最匹配你的背景**（RL + LLM Agent）
- Coding 非常 practical，可能涉及自动驾驶场景
- ML 轮次会深挖 RL 算法: PPO, Q-learning, Reward Design
- Tesla 文化: 极度注重 impact, "move fast", 动手能力

**准备重点**:
- RL 深入: PPO 完整推导、Reward Hacking、Exploration vs Exploitation
- Coding: Python 实战题（不是纯 LeetCode，可能是实现某个算法）
- 准备 Tesla 产品理解: Autopilot, FSD, Optimus, Dojo

---

### 🟡 Apple ML/AI Intern (Austin)
| 轮次 | 时长 | 内容 | 难度 |
|------|------|------|------|
| Phone Screen | 30min | 背景 + 动机 | ⭐⭐ |
| Technical Round 1 | 60min | Coding (Python OK) | ⭐⭐⭐ |
| Technical Round 2 | 60min | ML 项目 deep dive | ⭐⭐⭐⭐ |
| Technical Round 3 | 60min | Domain-specific (NLP/CV) | ⭐⭐⭐⭐ |

**特点**:
- 非常看重 **端到端 ML 项目经验**——你的 Linksome + SafoLab 经验是核心
- 会要求你完整讲述一个 ML 项目: 问题定义 → 数据处理 → 模型选择 → 训练 → 部署
- 注重细节: 为什么选这个模型？为什么这个 learning rate？遇到过什么坑？

**准备重点**:
- 准备 2-3 个项目的完整故事线（Linksome, SafoLab, Columbia RAG）
- ML 基础: 分类/回归/序列模型的完整知识
- Apple 产品理解: Siri, Core ML, Apple Intelligence

---

### 🟡 Nvidia AI/ML Intern (Austin)
| 轮次 | 时长 | 内容 | 难度 |
|------|------|------|------|
| Phone Screen | 45min | 技术背景 | ⭐⭐ |
| Technical Round 1 | 60min | Coding (C++/Python) | ⭐⭐⭐⭐ |
| Technical Round 2 | 60min | ML/DL 基础 + CUDA | ⭐⭐⭐⭐ |
| System Design | 60min | 分布式训练/推理系统 | ⭐⭐⭐⭐⭐ |

**特点**:
- CUDA/GPU 知识是加分项（你有 DeepSpeed + multi-GPU 经验）
- 分布式训练: Data Parallelism, Model Parallelism, Pipeline Parallelism
- 推理优化: TensorRT, vLLM, 量化

**准备重点**:
- CUDA 基础: 线程层次、内存层次、Kernel 编写
- 分布式训练: DeepSpeed 原理、ZeRO 优化、混合精度训练
- ML 基础: Transformer 训练/推理优化

---

### 🟡 OpenAI / Anthropic (Dream Companies)
| 轮次 | 时长 | 内容 | 难度 |
|------|------|------|------|
| Phone Screen | 30min | 背景 + 动机 | ⭐⭐ |
| Research Deep Dive | 60min | 你的论文/项目完整讨论 | ⭐⭐⭐⭐⭐ |
| Coding | 60min | Python, 算法 | ⭐⭐⭐⭐ |
| ML Fundamentals | 60min | Transformers, Scaling Laws, RLHF | ⭐⭐⭐⭐⭐ |

**特点**:
- **Research-oriented**: 你的 Multi-Turn-Jailbreaker 论文是核心
- 会深挖你的研究: 为什么做这个？方法创新在哪？失败尝试？
- ML 基础要求极高: Transformer 从零推导、Scaling Laws、RLHF 完整流程
- Anthropic 额外关注 AI Safety: Constitutional AI, Interpretability

**准备重点**:
- 论文准备: 能完整讲述 30 分钟 + 回答任何细节问题
- Transformer: 完整推导（Attention, Multi-head, Positional Encoding）
- RLHF: 从 Reward Model 到 PPO 的完整流程
- Safety: Red-teaming 方法论、Alignment 技术

---

### 🟢 Databricks ML/DL Intern
| 轮次 | 时长 | 内容 | 难度 |
|------|------|------|------|
| OA | 90min | Coding + ML | ⭐⭐⭐ |
| Phone Screen | 45min | Coding (Python) | ⭐⭐⭐ |
| Virtual Onsite (3轮) | 3h | Coding + ML + System Design | ⭐⭐⭐⭐ |

**特点**:
- Spark/分布式数据处理是加分项
- ML 轮次侧重: 特征工程、模型评估、实验设计
- System Design: ML 数据流水线、模型部署

---

### 🔵 Jane Street / Citadel (Quant)
| 轮次 | 时长 | 内容 | 难度 |
|------|------|------|------|
| OA | 60min | 概率 + 数学 + 编码 | ⭐⭐⭐⭐ |
| Phone Screen | 45min | 概率题 + 脑经急转弯 | ⭐⭐⭐⭐ |
| Virtual Onsite (3-5轮) | 4-6h | 概率/统计 + Coding (Hard) + 交易游戏 | ⭐⭐⭐⭐⭐ |

**特点**:
- **完全不同的面试风格**，需要单独准备
- 概率/统计: 期望值、条件概率、随机过程
- 心算: 快速加减乘除、分数比较
- Coding: LeetCode Hard, 侧重 C++/Python

---

## 3. Coding 准备

### 刷题策略

```
第一阶段（6-7月）：基础巩固
├── Arrays & Strings: 30题
├── HashMaps & Sets: 15题
├── Linked Lists: 10题
├── Stacks & Queues: 10题
└── 总计: ~65题

第二阶段（8-9月）：进阶提升
├── Trees & Graphs: 25题
├── Dynamic Programming: 25题
├── Recursion & Backtracking: 15题
├── Binary Search: 10题
└── 总计: ~75题

第三阶段（10-11月）：冲刺 + 模拟
├── Company-specific 高频题: 30题
├── Mock interviews: 10次
├── Time/Space complexity 专项
└── 总计: ~30题 + 模拟
```

### 按公司分类的高频题型

| 公司 | 高频题型 | 难度 | 特别关注 |
|------|----------|------|----------|
| **Amazon** | Arrays, Strings, Trees, HashMaps | Medium | Two Sum 变体, LRU Cache, 股票问题 |
| **Google** | Graphs, DP, Strings, Trees | Medium-Hard | 拓扑排序, 并查集, 区间问题 |
| **Meta** | Arrays, Strings, DP | Medium | 回文, 括号, 子数组问题 |
| **Tesla** | Python 实战, 矩阵, 模拟 | Medium-Hard | 矩阵旋转, 路径规划, 数值计算 |
| **Apple** | Arrays, Strings, Trees | Medium | 字符串处理, 树遍历 |
| **Nvidia** | C++/Python, 矩阵, 并行 | Medium-Hard | 矩阵运算, 并行算法 |
| **OpenAI** | Python, 算法设计 | Medium-Hard | 实现 ML 算法（KNN, K-means） |
| **Quant** | 概率, DP, 数学 | Hard | 随机算法, 组合数学 |

### 推荐刷题资源

| 资源 | 用途 | 链接 |
|------|------|------|
| **LeetCode Premium** | 公司高频题 + 模拟面试 | leetcode.com |
| **NeetCode 150 / 300** | 按模式分类的精选题 | neetcode.io |
| **Cracking the Coding Interview** | 系统性复习 | 书 |
| **Blind 75** | 最经典 75 题 | teamblind.com |
| **CodeTop** | 公司高频题汇总 | codetop.cc |

### 你的 Python 刷题重点

鉴于你的背景（Python 主力），刷题时注意：

```python
# 1. 熟练掌握 Python 内置数据结构和技巧
# - collections.defaultdict, Counter, deque
# - heapq (优先队列)
# - itertools (permutations, combinations)
# - functools.lru_cache (DP 记忆化)
# - bisect (二分查找)

# 2. 常见算法模板
# - 二分搜索模板
# - DFS/BFS 模板
# - 并查集 (Union-Find)
# - 拓扑排序 (Kahn's Algorithm)
# - Dijkstra / Floyd-Warshall
# - KMP / Rabin-Karp (字符串匹配)

# 3. 时间复杂度分析
# - 每次写完都要分析 TC 和 SC
# - 能说出最优解和最差解
```

---

## 4. ML/DL 基础知识准备

### 核心知识图谱

```
1. 监督学习
├── 线性回归 / Logistic 回归
├── SVM (核函数)
├── 决策树 / Random Forest / GBDT / XGBoost
└── KNN

2. 深度学习基础
├── MLP: 反向传播推导, 梯度消失/爆炸
├── CNN: 卷积, Pooling, 经典架构 (ResNet)
├── RNN / LSTM / GRU: 序列建模
└── Transformer: ⭐⭐⭐⭐⭐ (重中之重!)
    ├── Self-attention: 公式推导, 复杂度 O(n²)
    ├── Multi-head Attention
    ├── Positional Encoding (Sinusoidal vs Learned)
    ├── Layer Norm vs Batch Norm
    ├── Feed-Forward Network
    └── Encoder-Decoder 架构

3. 强化学习 (你的强项!)
├── MDP, Bellman Equation
├── Value-based: Q-Learning, DQN
├── Policy-based: Policy Gradient, REINFORCE
├── Actor-Critic: A2C, A3C
├── PPO: ⭐⭐⭐ (完整推导, Clip 机制)
├── Reward Design, Reward Hacking
└── Exploration vs Exploitation

4. 训练优化
├── Optimizers: SGD, Adam, AdamW, RMSprop
├── Learning Rate Scheduling: Cosine, Warmup, Step Decay
├── Regularization: Dropout, Weight Decay, Label Smoothing
├── Normalization: Batch, Layer, Instance, Group
├── Loss Functions: Cross-Entropy, MSE, Contrastive, Triplet
└── Evaluation Metrics: Accuracy, Precision/Recall, F1, AUC-ROC, Perplexity

5. 分布式训练
├── Data Parallelism (DDP)
├── Model Parallelism
├── Pipeline Parallelism
├── Tensor Parallelism
├── ZeRO (DeepSpeed): Stage 1/2/3
├── Mixed Precision Training (FP16, BF16)
└── Gradient Accumulation / Checkpointing
```

### 高频面试题（按公司）

**Amazon / Google / Meta 通用**:
- 解释 Transformer 的 Self-attention 机制
- 为什么需要 Positional Encoding？
- Batch Norm vs Layer Norm 的区别和适用场景
- 梯度消失/爆炸的原因和解决方案
- 过拟合的检测和解决方法
- 如何选择 Learning Rate？

**Meta 特别关注**:
- 推导 Transformer 的参数量
- Self-attention 的复杂度优化（Flash Attention）
- 对比 Meta 的 Llama 和 OpenAI 的 GPT 架构差异

**Tesla 特别关注**:
- PPO 算法的完整推导
- Reward 设计中的常见陷阱
- 多模态模型（视觉 + 语言）的融合方式
- 仿真环境 vs 真实世界数据的差异

**OpenAI/Anthropic 特别关注**:
- Scaling Laws: 模型大小、数据量、计算量的关系
- RLHF 完整流程: SFT → Reward Model → PPO
- 推理时 Scaling: Chain-of-Thought, Tree-of-Thought
- AI Safety: Alignment, Constitutional AI, Interpretability

---

## 5. LLM / Agent 专项准备

这是你的 **核心竞争力** 所在，必须准备到能深入讨论 30 分钟以上的程度。

### 你的项目准备（每个项目准备 5 分钟 Elevator Pitch + 15 分钟 Deep Dive）

#### 1. Linksome — LLM Agent Engineer
**Elevator Pitch**:
> "At Linksome, I built a multi-agent pipeline for automated content generation. I designed a context management system that handles long conversation histories, implemented tool-use agents that can browse the web and interact with APIs, and optimized the orchestration layer for reliability."

**Deep Dive 准备**:
- 多 Agent 之间如何通信？同步还是异步？
- Context 管理策略是什么？Token 预算如何分配？
- 如何处理 Agent 失败/超时？Retry 策略？
- Tool-use 的架构设计？Function Calling 还是 ReAct？
- 如何评估 Agent 性能？准确率？延迟？

#### 2. SafoLab — LLM Red-teaming (RL)
**Elevator Pitch**:
> "At SafoLab, I researched LLM red-teaming using reinforcement learning. I built a multi-turn jailbreaker that uses RL to find adversarial prompts, trained on multi-GPU clusters with DeepSpeed, and submitted a paper on the findings."

**Deep Dive 准备**:
- 为什么用 RL 而不是监督学习来做 red-teaming？
- Reward 如何设计？如何避免 Reward Hacking？
- PPO 的具体实现细节？KL 惩罚项的作用？
- Multi-GPU 训练的经验？ZeRO Stage 选择？
- 论文的主要贡献和发现？

#### 3. Columbia — RAG Research
**Elevator Pitch**:
> "At Columbia, I worked on Retrieval-Augmented Generation systems, focusing on improving retrieval quality and integrating retrieved knowledge into LLM generation."

**Deep Dive 准备**:
- Chunking 策略？固定长度还是语义分块？
- Embedding 模型选择？Dense vs Sparse？
- 检索后如何融合到生成中？Concatenate？Cross-attention？
- 如何处理检索噪声？Re-ranking？
- RAG 的评估指标？Faithfulness, Relevance？

#### 4. AgentBrowser (CDP-based)
**Elevator Pitch**:
> "I built AgentBrowser, a browser automation agent using Chrome DevTools Protocol. It can navigate web pages, extract content, and interact with elements — all driven by LLM decision-making."

**Deep Dive 准备**:
- CDP 的核心原理？WebSocket 通信？
- 如何将 DOM 结构转化为 LLM 可理解的格式？
- 如何处理动态加载的内容？等待策略？
- 与 Playwright/Selenium 的对比？优势在哪？

#### 5. Amazon Nova AI Challenge — 1st Place
**Elevator Pitch**:
> "I won 1st place in the Amazon Nova AI Challenge by building [具体项目]. This demonstrates my ability to deliver production-quality AI solutions under competition constraints."

**Deep Dive 准备**:
- 问题是什么？你的解决方案？
- 与其他参赛者的差异化？
- 学到了什么？如果重来会怎么做？

### LLM/Agent 高频面试题

**基础概念**:
1. 什么是 LLM Agent？和普通 LLM 的区别？
2. ReAct 框架的原理？Thought → Action → Observation 循环
3. Function Calling / Tool-use 的实现方式
4. Multi-agent 架构的优缺点？如何协调？
5. Agent 的长期记忆和短期记忆如何管理？

**进阶**:
1. 如何防止 Agent 陷入死循环？
2. Agent 的安全性考虑（Prompt Injection, Tool Misuse）
3. Agent 的评估框架（成功率、效率、安全性）
4. RAG 中检索质量对生成的影响有多大？
5. Context Window 限制下的策略（Sliding Window, Summary, RAG）

**LLM 训练**:
1. SFT (Supervised Fine-Tuning) 的数据构建
2. RLHF 的完整流程和挑战
3. DPO (Direct Preference Optimization) vs PPO
4. LoRA / QLoRA 的原理
5. 数据配比（Pretrain vs SFT vs RLHF data）

---

## 6. ML System Design 准备

### 常见题目

| 题目 | 考察点 | 适用公司 |
|------|--------|----------|
| 设计一个推荐系统 | 召回 → 排序 → 重排, 特征工程 | Meta, Amazon, Google |
| 设计一个 LLM 推理服务 | 推理优化, 批处理, 缓存 | OpenAI, Anthropic, Nvidia |
| 设计一个分布式训练系统 | 并行策略, 通信优化 | Nvidia, Meta |
| 设计一个搜索 + RAG 系统 | 索引, 检索, 排序, 生成 | Google, Apple |
| 设计一个广告点击率预测 | 特征工程, 模型选择, 实时性 | Meta, Google |
| 设计一个异常检测系统 | 时间序列, 无监督学习 | Tesla, Apple |

### 回答框架

```
1. 明确问题范围
   - Functional requirements
   - Non-functional requirements (latency, throughput, accuracy)
   - Constraints (data size, budget)

2. 数据设计
   - 数据来源和格式
   - 数据存储方案
   - 数据流水线 (ETL)

3. 模型设计
   - 模型选择 (为什么选这个？)
   - 特征工程
   - 训练方案 (数据分割, 评估)

4. 系统架构
   - 整体架构图
   - 各组件职责
   - 数据流

5. 部署与监控
   - Serving 架构
   - A/B Testing
   - Monitoring & Alerting

6. 扩展与优化
   - 瓶颈分析
   - 优化方案
   - 未来工作
```

### 推荐学习资源

| 资源 | 说明 |
|------|------|
| **chiphuyen/machine-learning-systems-design** | ML 系统设计圣经 |
| **"Designing Machine Learning Systems" (Chip Huyen)** | 书，全面覆盖 |
| **"Designing Data-Intensive Applications" (Martin Kleppmann)** | 分布式系统基础 |
| **Google ML System Design Interview Guide** | 搜索 "google ml system design interview" |

---

## 7. Behavioral 面试准备

### STAR 法则

```
S - Situation: 背景是什么？
T - Task: 你的任务是什么？
A - Action: 你具体做了什么？
R - Result: 结果如何？有什么量化指标？
```

### 必须准备的故事（每个公司 5-8 个）

| # | 故事主题 | 对应项目 | 体现的能力 |
|---|----------|----------|------------|
| 1 | 技术挑战 | Linksome 多 Agent 协调 | 问题解决, 技术深度 |
| 2 | 团队合作 | SafoLab 研究合作 | 协作, 沟通 |
| 3 | 领导力 | Amazon Nova Challenge 带队 |  Ownership, 领导力 |
| 4 | 失败与学习 | 某个项目中的失败经历 | 成长心态, 韧性 |
| 5 | 冲突解决 | 团队中的技术分歧 | 沟通, 妥协 |
| 6 | 创新 | AgentBrowser 的设计创新 | 创造力, 主动性 |
| 7 | 数据驱动决策 | RAG 中的检索优化 | 分析能力, 数据思维 |
| 8 | 客户/用户导向 | Linksome 产品需求 | 用户思维 |

### 公司 Behavioral 重点

| 公司 | 核心考察点 | 典型问题 |
|------|------------|----------|
| **Amazon** | Leadership Principles | "Tell me about a time you took ownership of a project" |
| **Google** | Googleyness | "Tell me about a time you handled ambiguity" |
| **Meta** | Move Fast | "Tell me about a time you shipped something quickly" |
| **Tesla** | Mission-driven | "Why do you want to work at Tesla?" |
| **Apple** | Attention to detail | "Tell me about a project where you obsessed over quality" |
| **OpenAI** | Research passion | "What's the most exciting AI paper you've read recently?" |

---

## 8. 项目深度讨论准备

对于 AI/ML 岗位，面试官会花大量时间讨论你的项目。准备以下内容：

### 每个项目的 "One-Page Summary"

```
项目名称: [Linksome Multi-Agent Pipeline]
时间: [2025.06 - 2026.01]
团队: [X 人]
我的角色: [LLM Agent Engineer]

问题:
[用 2-3 句话描述要解决的问题]

方法:
[技术方案概述, 关键设计决策]

我的贡献:
[具体做了什么, 技术细节]

技术栈:
[Python, LLM APIs, Playwright, etc.]

结果:
[量化指标: 准确率 X%, 延迟降低 Y%]

学到的教训:
[最大的挑战和如何克服]

如果重来:
[会做什么不同]
```

### 准备 3 个层次的讲述

```
Level 1 (5分钟): 高层概述
- 适合: 电话初筛, 非技术面试官
- 内容: 问题 → 方案 → 结果

Level 2 (15分钟): 技术细节
- 适合: 技术面试官
- 内容: 架构设计, 关键决策, 技术挑战

Level 3 (30分钟): 深度讨论
- 适合: 研究岗, 资深面试官
- 内容: 论文级细节, 失败尝试, 理论分析
```

---

## 9. 量化公司专项准备

如果你考虑 Jane Street / Citadel / HRT，需要额外准备：

### 概率与统计

```
核心主题:
├── 条件概率 / Bayes 定理
├── 期望值计算
├── 随机变量分布 (Normal, Binomial, Poisson)
├── 大数定律 / 中心极限定理
├── 随机过程 (Markov Chain, Martingale)
└── 蒙特卡洛模拟

推荐资源:
├── "A Practical Guide to Quantitative Finance Interviews" (Xinfeng Zhou)
├── "Heard on the Street" (Timothy Crack)
├── "Fifty Challenging Problems in Probability" (Mosteller)
└── quantquestions.app (1200+ 真实题目)
```

### 心算

```
练习内容:
├── 两位数 × 两位数
├── 分数比较 (3/7 vs 4/9)
├── 百分比计算
├── 平方根近似
└── 单位换算

练习工具:
├── quantquestions.app 的心算模块
├── 每天 10 分钟心算练习
```

### 脑经急转弯

```
经典题型:
├── 天平称重问题
├── 过桥问题
├── 生日问题
├── 赌徒破产问题
└── 逻辑推理题

策略:
├── 不要急于给出答案
├── 边想边说 (Think out loud)
├── 从简单情况开始推理
└── 检查边界条件
```

---

## 10. 推荐学习资源清单

### 📚 书籍

| 书名 | 用途 | 优先级 |
|------|------|--------|
| **Cracking the Coding Interview** | Coding 面试系统复习 | 🔴 必读 |
| **Designing Machine Learning Systems** (Chip Huyen) | ML System Design | 🔴 必读 |
| **Deep Learning** (Goodfellow) | DL 理论基础 | 🟡 参考 |
| **Reinforcement Learning: An Introduction** (Sutton & Barto) | RL 圣经 | 🟡 参考 |
| **Speech and Language Processing** (Jurafsky & Martin) | NLP/LLM 基础 | 🟡 参考 |
| **Designing Data-Intensive Applications** (Kleppmann) | 分布式系统 | 🟢 选读 |
| **A Practical Guide to Quantitative Finance Interviews** | 量化面试 | 🟢 选读 |

### 🎓 在线课程

| 课程 | 平台 | 用途 |
|------|------|------|
| **CS229: Machine Learning** (Andrew Ng) | Stanford/YouTube | ML 基础复习 |
| **CS231n: CNNs for Visual Recognition** | Stanford/YouTube | DL 基础 |
| **CS224n: NLP with Deep Learning** | Stanford/YouTube | NLP/Transformer |
| **CS285: Deep Reinforcement Learning** (Sergey Levine) | UC Berkeley | RL 深入 |
| **Full Stack Deep Learning** | fullstackdeeplearning.com | ML 工程实践 |

### 🌐 网站 & 博客

| 资源 | 用途 |
|------|------|
| **The Annotated Transformer** (Harvard NLP) | Transformer 逐行实现 |
| **Lilian Weng's Blog** (OpenAI) | LLM, Agent, RLHF 综述 |
| **Jay Alammar's Blog** | ML 可视化讲解 |
| **Sebastian Raschka's Blog** | DL 实践 |
| **Distill.pub** | ML 交互式讲解 |
| **HuggingFace NLP Course** | Transformers 实战 |
| **代码随想录 (programmercarl.com)** | 2026 LLM 面经汇总 |

### 💻 GitHub Repos

| Repo | Stars | 用途 |
|------|-------|------|
| **alirezadir/Machine-Learning-Interviews** | 8.4k | ML 面试完整指南 |
| **chiphuyen/machine-learning-systems-design** | 10.4k | ML System Design |
| **neetcode-gh/leetcode** | 5k+ | 按模式分类的 LeetCode |
| **kamranahmedse/developer-roadmap** | 300k+ | 学习路线图 |

---

## 11. 每周学习计划

### Phase 1: 基础巩固 (6月 – 7月)

```
周一: LeetCode (Arrays + Strings) — 3题
周二: ML 基础复习 — Transformer 架构
周三: LeetCode (HashMaps + Linked Lists) — 3题
周四: 项目准备 — Linksome 故事线完善
周五: LeetCode (Stacks + Queues) — 3题
周六: ML System Design — 推荐系统
周日: Behavioral 故事准备 + 休息

每周目标: 12-15 LeetCode + 1 ML topic + 1 project prep
```

### Phase 2: 进阶提升 (8月 – 9月)

```
周一: LeetCode (Trees + Graphs) — 3题
周二: LLM/Agent 专项 — RAG 深入
周三: LeetCode (DP) — 3题
周四: ML System Design — LLM 推理服务
周五: LeetCode (Recursion + Backtracking) — 3题
周六: Mock Interview (Coding)
周日: 项目准备 + 公司研究

每周目标: 12-15 LeetCode + 1 LLM topic + 1 system design
```

### Phase 3: 冲刺阶段 (10月 – 11月)

```
周一: 公司高频题 (Amazon/Google) — 3题
周二: ML 面试模拟
周三: 公司高频题 (Meta/Tesla) — 3题
周四: Behavioral 模拟
周五: 公司高频题 (Apple/Nvidia) — 3题
周六: Full Mock Interview (Coding + ML + Behavioral)
周日: 复习薄弱环节 + 休息

每周目标: 9-12 LeetCode + 2 mock interviews
```

### Phase 4: 面试实战 (12月 – 2月)

```
根据面试安排动态调整:
├── 面试前3天: 专注该公司高频题
├── 面试前1天: 复习项目故事 + Behavioral
├── 面试当天: 放松, 早睡, 提前测试设备
└── 面试后: 记录问题, 复盘改进
```

---

## 12. 面试 Checklist

### 面试前 1 个月
- [ ] 完成该公司的 LeetCode 高频题（至少 20 题）
- [ ] 准备好 5 个 STAR 故事
- [ ] 复习 ML 基础知识
- [ ] 准备 2 个项目的完整 Deep Dive

### 面试前 1 周
- [ ] 研究该公司最新产品和技术博客
- [ ] 准备 "Why this company?" 的回答
- [ ] 准备 3 个想问面试官的问题
- [ ] 模拟面试至少 1 次

### 面试前 1 天
- [ ] 确认面试时间和链接
- [ ] 测试摄像头、麦克风、网络
- [ ] 准备白板/纸笔（如果需要）
- [ ] 早睡

### 面试当天
- [ ] 提前 10 分钟进入会议室
- [ ] 准备好水、笔记本
- [ ] 关闭所有通知
- [ ] 深呼吸，自信！

### 面试后
- [ ] 24 小时内发 Thank-you email
- [ ] 记录面试问题（用于后续准备）
- [ ] 复盘：哪些答得好？哪些需要改进？
- [ ] 继续准备下一家

---

## 附录：你的个人优势总结

```
你的核心竞争力:
├── ✅ LLM Agent 实战经验 (Linksome) — 市场上最稀缺的技能
├── ✅ RL Red-teaming 研究 (SafoLab) — 论文级深度
├── ✅ RAG 研究经验 (Columbia) — 热门方向
├── ✅ Amazon Nova Challenge 1st Place — 可验证的成就
├── ✅ 多 GPU 分布式训练经验 (DeepSpeed)
├── ✅ GPA 4.0 + UCLA MS CS — 学术背景过硬
└── ✅ 完整的 Agent 项目 (AgentBrowser, Agent-Tutorial)

需要加强的:
├── ⚠️ LeetCode 刷题量 (目标: 150-200题)
├── ⚠️ ML System Design (目标: 5-8个设计题)
├── ⚠️ 量化面试 (如果考虑量化方向)
└── ⚠️ 行为面试故事 (目标: 8个高质量STAR故事)

你的差异化定位:
"LLM Agent Engineer with RL research background"
— 这个组合在市场上非常稀缺，是你的最大优势！
```

---

> **最后建议**: 你的背景非常强，但面试准备需要系统性和纪律性。从今天开始，每周坚持 15-20 小时的学习和练习。**7月初 Amazon 就开放了，时间紧迫！** 加油！🚀
