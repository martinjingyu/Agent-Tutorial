# Kai-Wei Chang 教授深度调研报告

> 调研日期：2025-06-29
> 信息来源：UCLA CS 主页、Publications 页面、Google Scholar、Members 页面、Samueli 工程学院页面

---

## 1. 个人背景与学术地位

| 项目 | 内容 |
|------|------|
| **职称** | Associate Professor, UCLA Computer Science (2022.7–至今) |
| **曾任** | Assistant Professor, UCLA CS (2017–2022) |
| **博士** | University of Illinois at Urbana-Champaign (UIUC) |
| **实验室** | UCLA NLP Group (Co-director, UCLA DataX AI Technology Center) |
| **荣誉** | 2021 Sloan Research Fellow; 2024 IEEE AI's 10 to Watch (Top 10 Rising Stars in AI) |
| **学术服务** | Vice President-Elect (2024), VP (2025), President (2026) of ACL; JAIR/JMLR/TACL Action Editor |

---

## 2. 核心研究方向

Kai-Wei Chang 的研究横跨 **自然语言处理、多模态 AI、AI 安全与推理**，主要方向如下：

### 2.1 Trustworthy NLP / AI Safety（可信 AI）
- **性别偏见检测与消除**：NeurIPS 2016 关于词嵌入性别偏见的开创性工作（高引）
- **偏见放大**：EMNLP 2017 Best Long Paper
- **LLM Unlearning**：使大模型"遗忘"特定知识（2024–2025 多篇论文）
- **Customized Guardrails**：为 LLM 定制安全护栏
- **SafeWorld**：LLM Agent 安全框架
- **Over-refusal 缓解**：解决 LLM 过度拒绝合理请求的问题

### 2.2 Vision-Language / Multimodal AI（视觉-语言/多模态）
- **VisualBERT**：多模态预训练模型
- **GLIP**：CVPR 2022 Best Paper Finalist（图文定位）
- **VideoCon / VideoPhy**：视频理解与物理常识推理
- **OpenVLThinker**：开源多模态推理模型（2025）
- **MathVista / MathVerse**：数学视觉推理基准

### 2.3 LLM Reasoning & Agents（LLM 推理与智能体）
- **Chameleon**：即插即用的组合式推理框架
- **Agent Lumos**：基于 LLM 的开放世界 Agent 学习（2024）
- **Embodied Web Agents**：具身化网页 Agent（2025）
- **Ctrl-R**：结构化推理轨迹控制（ICML 2026 Spotlight, top 2.2%）
- **OpenThoughts**：推理模型的数据配方（ICLR 2026 Oral, top 1.8%）
- **DACO**：分治推理（Divide-and-Conquer Reasoning）

### 2.4 AI for Math（AI 数学）
- **MathVista**：广泛使用的数学视觉推理基准（1800+ 引用）
- **MathVerse**：数学推理评测
- **HAGeo**：金牌级几何解题系统
- **expMath**：DARPA $5M 合同项目
- **AI4Math Moonshot**：与陶哲轩（Terence Tao）合作

### 2.5 其他方向
- **Information Extraction**：PolicyQA, TextEE, SPEED, KPEval, MetaKP
- **Constrained Generation**：语义概率层、可控生成

---

## 3. 最近 2 年（2024–2026）论文列表

### 2026 年
| 论文 | 会议/期刊 | 备注 |
|------|-----------|------|
| Ctrl-R: Learning Structured Reasoning via Tractable Trajectory Control | **ICML 2026 Spotlight** | top 2.2% |
| OpenThoughts: Data Recipes for Reasoning Models | **ICLR 2026 Oral** | top 1.8% |
| Training LLMs for Divide-and-Conquer Reasoning | — | Agent/推理方向 |
| Dynamic Generation of Multi LLM Agents Communication Topologies with Graph Diffusion Models | — | 多 Agent 通信 |
| BRIEF-Pro: Universal Context Compression for Multi-Hop Reasoning | — | 长上下文推理 |
| AutoSUIT Bench | — | Agent 评测 |
| ContextNav | — | 具身 Agent |
| Structured World Knowledge for LLM | — | 知识推理 |
| KungFu: Structured Control for LLM Reasoning | — | 推理控制 |

### 2025 年
| 论文 | 方向 | 备注 |
|------|------|------|
| OpenVLThinker: Open-source Multimodal Reasoning | 多模态推理 | 开源 |
| Embodied Web Agents | 具身 Agent | 网页交互 |
| Magnet: Multi-agent Communication | 多 Agent | 通信拓扑 |
| METAL: Multi-agent Learning | 多 Agent | 协作学习 |
| QLASS: Quality Assessment | 评测 | LLM 输出质量 |
| LongMemEval: Long Context Evaluation | 长上下文 | 评测基准 |
| MuirBench: Multimodal Reasoning Benchmark | 多模态 | 推理基准 |
| Customized Guardrails for LLMs | AI 安全 | 定制护栏 |
| LLM Unlearning (Jin et al.) | AI 安全 | 模型遗忘 |
| X-Teaming: Multi-agent Teaming | 多 Agent | 团队协作 |
| LUME: LLM Unlearning | AI 安全 | 遗忘方法 |
| Structured Knowledge for LLM Reasoning | 推理 | 知识结构化 |

### 2024 年
| 论文 | 方向 | 备注 |
|------|------|------|
| Agent Lumos: Learning Open-world Agent with LLMs | Agent | 开放世界学习 |
| MathVista | AI 数学 | NeurIPS 2024, 高引 |
| MathVerse | AI 数学 | 数学推理 |
| SafeWorld: Safety in LLM Agents | AI 安全 | Agent 安全 |
| Re-ReST: Reasoning Self-Training | 推理 | 自训练 |
| DACO: Divide-and-Conquer Reasoning | 推理 | 分治推理 |
| JourneyBench | 评测 | 多步推理 |
| Control LLMs via Divide and Conquer | 可控生成 | 分治控制 |
| QUDSELECT | 信息抽取 | 查询选择 |
| Tree-of-Traversals | 推理 | 树遍历 |

---

## 4. 实验室规模与风格（UCLA NLP Group）

### 4.1 当前成员（2025）
**博士生（活跃）**：
- Christina Chance, Cheng-Fu Yang, Amita Kamath, Di Wu, Elaine Wan, Rui Sun, Xueqing Wu, Bryan Zhou, Wenbo Hu, Eric Jiang, Xiao Liang, Steven Swee

**博士后/访问学者**：
- James Zhecan Wang, Yining Hong, Yiwei Wang, Pan Lu, Kareem Ahmed, Kuan-Hao Huang, Md. Rizwan Parvez, Ziniu Hu

**知名校友（学术界）**：
- **Jieyu Zhao** → Assistant Professor @ University of Virginia
- **Muhao Chen** → Assistant Professor @ UC Davis
- **Hritik Bansal** → 博士后/研究员
- **Fan Yin, Wade Yin** → 学术界/工业界

**规模**：约 15–20 名活跃成员

### 4.2 实验室文化特征
1. **开放源代码**：GitHub 组织 [uclanlp](https://github.com/uclanlp) 活跃维护，几乎所有论文都有配套代码
2. **多学科交叉**：成员来自 CS、语言学、工程等背景
3. **高产出**：每年 10+ 篇顶会论文（ACL/NeurIPS/ICML/ICLR/CVPR）
4. **合作网络**：与工业界（Google, Meta, Amazon）和学术界（陶哲轩等）广泛合作

---

## 5. 指导学生风格分析

### 5.1 从论文作者列表推断
- **学生一作制**：绝大多数论文的第一作者是博士生/博士后，说明教授给予学生充分的独立研究空间
- **多人合作**：论文通常有 3–6 位共同作者，多位学生共同参与，体现协作式实验室文化
- **跨组合作**：常与外部机构（UIUC, USC, 工业界）合作，学生有机会拓展学术网络

### 5.2 培养成果
- 多位 alumni 进入顶尖高校任教（UVA, UC Davis）
- 学生获得多项最佳论文奖（EMNLP 2017 Best Long Paper, CVPR 2022 Best Paper Finalist）
- 学生主导的 MathVista 获得 1800+ 引用，成为领域标准基准

### 5.3 风格总结
> **"高自主性 + 强支持"**：教授提供方向指导和资源支持，学生主导研究项目。实验室注重开放科学（代码开源、数据公开），鼓励学生建立自己的学术声誉。

---

## 6. 当前招生项目/方向

### 6.1 招生渠道
- **申请页面**：https://web.cs.ucla.edu/~kwchang/application
- **Google Form**：用于初步联系
- **申请信息 PDF**：详细说明申请流程

### 6.2 招生方向（基于研究活跃度推断）
1. **LLM Reasoning & Agents**（最活跃方向，2025–2026 论文最多）
   - 结构化推理（Ctrl-R, OpenThoughts）
   - 多 Agent 系统（Magnet, X-Teaming）
   - 具身 Agent（Embodied Web Agents, ContextNav）
2. **Trustworthy AI / AI Safety**
   - LLM Unlearning
   - Customized Guardrails
   - Agent Safety（SafeWorld）
3. **Multimodal AI**
   - 视频理解（VideoCon, VideoPhy）
   - 多模态推理（OpenVLThinker）
4. **AI for Math**
   - MathVista 系列
   - expMath（DARPA 项目）

### 6.3 适合的申请者画像
- 有 NLP/CV/ML 研究经验
- 对 **LLM Agent、AI 安全、多模态推理** 有浓厚兴趣
- 有顶会论文发表经验优先
- 编程能力强（Python, PyTorch）
- 愿意参与开源项目

---

## 7. 关键链接汇总

| 资源 | URL |
|------|-----|
| 个人主页 | http://web.cs.ucla.edu/~kwchang/ |
| Google Scholar | https://scholar.google.com/citations?user=fqDBtzYAAAAJ |
| 论文列表 | https://web.cs.ucla.edu/~kwchang/publications/ |
| 实验室成员 | https://web.cs.ucla.edu/~kwchang/members/ |
| 申请页面 | https://web.cs.ucla.edu/~kwchang/application |
| GitHub | https://github.com/uclanlp |
| Twitter/X | https://twitter.com/kaiwei_chang |
| LinkedIn | https://linkedin.com/in/kai-wei-chang-41239040 |

---

## 8. 总结

Kai-Wei Chang 是 UCLA CS 的 Associate Professor，领导 UCLA NLP Group，研究方向涵盖 **LLM 推理与 Agent、可信 AI/安全、多模态 AI、AI 数学** 四大板块。2024–2026 年处于高产期，在 ICML/ICLR/NeurIPS 等顶会发表多篇 Spotlight/Oral 论文。实验室规模约 15–20 人，学生一作制，开放科学文化浓厚。目前正在招收博士生，重点方向为 LLM Agent、AI 安全、多模态推理。

> **对 AI 算法实习生岗位的参考价值**：Kai-Wei Chang 的研究方向（LLM Agent、多模态推理、AI 安全）与当前 AI 行业热点高度契合。如果候选人有相关研究经验或论文，匹配度会很高。
