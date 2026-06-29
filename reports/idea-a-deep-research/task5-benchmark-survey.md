# Agent 评估基准调研

> 调研日期：2026-06-29
> 目标：系统梳理 LLM Agent 领域主流评估基准，为 Idea A 实验设计提供参考

---

## 1. WebArena

### 基本信息
- **论文**: "WebArena: A Realistic Web Environment for Building Autonomous Agents" (ICLR 2024)
- **作者**: Shuyan Zhou, Frank F. Xu, Hao Zhu 等 (Carnegie Mellon University)
- **代码**: https://github.com/web-arena-x/webarena
- **官网**: https://webarena.dev/

### 环境设计
WebArena 是一个**自托管、可复现的 Web 环境**，包含 4 个完整功能的网站（Docker 容器部署）：

| 网站 | 领域 | 功能 |
|------|------|------|
| OneStopShop | 电商 (E-commerce) | 商品浏览、搜索、购物车、下单 |
| GitLab | 协作开发 (Collaborative Dev) | 仓库管理、Issue、Merge Request |
| WordPress | 内容管理 (CMS) | 文章编辑、页面管理、用户管理 |
| Reddit (模拟) | 论坛讨论 (Forum) | 发帖、评论、投票、搜索 |

此外还集成了工具网站：地图、计算器、草稿本，以及外部知识库（Wikipedia、IDE 使用手册等）。

### 任务集
- **总计 812 个任务**，每个任务是一个高层次的**自然语言指令**
- 任务覆盖 4 个网站 + 跨网站任务
- 任务类型示例：
  - "告诉我 2023 年 3 月我在食品上花了多少钱"
  - "创建一个名为 'NolanFans' 的仓库，在 README 中列出 Nolan 的奥斯卡获奖电影"
- 任务设计强调**长周期 (long-horizon)**、**多样化**、模拟人类日常上网行为

### 评估协议
- **功能正确性 (Functional Correctness)**：通过 validator 程序化验证任务结果是否达成目标
  - 例如：验证仓库中是否包含指定内容，而非比对动作序列
  - 允许多种有效路径达成同一目标
- 不依赖参考动作序列的文本匹配，避免对替代方案的误判

### 基线结果
| 方法 | 成功率 |
|------|--------|
| GPT-4 + ReAct (最佳) | **14.41%** |
| GPT-4 + CoT (推理后行动) | ~10% |
| PaLM-2 | ~8% |
| **人类表现** | **78.24%** |

### 后续发展
- **WebArena Verified** (NeurIPS 2025)：审计全部 812 个任务，修复评估偏差，提出 **WebArena Verified Hard**（137 个高难度子集）
- **WorkArena**：ServiceNow 场景的 Web 基准
- **OSWorld**：扩展到操作系统层面的 Agent 评估

### 计算成本
- 每个任务约需 1 分钟（LLM 调用 + 环境设置 + 评估）
- 完整评估 812 个任务需要大量 API 调用

---

## 2. ALFWorld

### 基本信息
- **论文**: "ALFWorld: Aligning Text and Embodied Environments for Interactive Learning" (ICLR 2021)
- **作者**: Mohit Shridhar, Xingdi Yuan, Marc-Alexandre Côté 等 (University of Washington / Microsoft Research)
- **代码**: https://github.com/alfworld/alfworld
- **官网**: http://alfworld.github.io/

### 环境设计
ALFWorld 是一个**对齐的文本-具身双视图环境**：
- **TextWorld 视图**：抽象文本环境，接收高层文本动作（如 "goto cabinet"）
- **ALFRED 视图**：具身模拟环境（基于 THOR 模拟器），接收低层物理动作（如 "MoveAhead 0.25"）

这种设计允许 Agent 先在抽象文本空间中学习高层策略，再迁移到具身环境执行。

### 任务类型（6 类，源自 ALFRED 数据集）

| 任务类型 | 训练集 | Seen 验证 | Unseen 验证 |
|---------|--------|-----------|------------|
| Pick & Place | 790 | 35 | 24 |
| Examine in Light | 308 | 13 | 18 |
| Clean & Place | 650 | 27 | 31 |
| Heat & Place | 459 | 16 | 23 |
| Cool & Place | 533 | 25 | 21 |
| Pick Two & Place | 813 | 24 | 17 |
| **合计** | **3,553** | **140** | **134** |

### 评估指标
- **任务成功率 (Task Success Rate)**：是否完成最终目标（如 "Put a washed apple in the kitchen fridge"）
- 评估在 held-out 场景（seen/unseen）上进行，测试泛化能力

### 基线结果 (BUTLER Agent)
- BUTLER 先在 TextWorld 中用模仿学习训练，再零样本迁移到具身环境
- 在 TextWorld 训练比直接在具身环境训练**快 7 倍**
- 抽象文本训练提升了在未见场景中的泛化能力

### 与 Idea A 的关联
ALFWorld 是**具身 Agent 评估**的代表性基准，强调从抽象推理到具体执行的迁移。对于评估 Agent 的规划能力和环境适应能力有重要参考价值。

---

## 3. AgentBench

### 基本信息
- **论文**: "AgentBench: Evaluating LLMs as Agents" (ICLR 2024)
- **作者**: Xiao Liu, Hao Yu, Hanchen Zhang 等 (Tsinghua University / Ohio State University / UC Berkeley)
- **代码**: https://github.com/THUDM/AgentBench
- **Star**: 3.5k+

### 环境设计
AgentBench 是**首个多维度的 LLM-as-Agent 评估基准**，包含 **8 个不同环境**，分为三大类：

#### Code 类（代码/系统交互）
| 环境 | 描述 | 任务示例 |
|------|------|---------|
| **Operating System** | Ubuntu bash 终端 | "递归设置目录下所有文件为只读，除了我的文件" |
| **Database** | MySQL API | "将成绩 60 分以上的学生标记为 PASS" |
| **Knowledge Graph** | Freebase API | "明尼苏达出生的诺贝尔奖得主演奏什么乐器？" |

#### Game 类（游戏/推理）
| 环境 | 描述 |
|------|------|
| **Digital Card Game** | Aquawar 双人对战游戏，管理宠物鱼卡牌 |
| **Lateral Thinking Puzzles** | 侧向思维谜题（如 "男人喝龟汤后自杀" 类谜题） |
| **House-Holding** | 基于 ALFRED 的家务任务（"把锅放在餐桌上"） |

#### Web 类（网页交互）
| 环境 | 描述 |
|------|------|
| **Web Shopping** | 基于 WebShop 的购物任务 |
| **Web Browsing** | 基于 Mind2Web 的网页浏览任务 |

### 评估指标
- **Overall Score**：各环境得分的加权综合
- 每个环境使用适合的指标：Success Rate、Reward、F1 Score 等
- 总分范围 0-4

### 主要发现（29 个 LLM 测试结果）

| 模型类型 | 模型 | 总分 |
|---------|------|------|
| API / 商业 | GPT-4 | **4.01** |
| | Claude-3 Opus | 3.11 |
| | GLM-4 | 2.89 |
| | Claude-2 | 2.49 |
| | GPT-3.5-turbo | 2.32 |
| 开源 | CodeLlama-34B | 0.96 |
| | Vicuna-13B | 0.93 |
| | LLaMA-2-70B | 0.78 |
| | LLaMA-2-13B | 0.77 |

**关键发现**：
1. 商业 LLM 平均分 2.32 vs 开源 LLM 平均分 0.51，差距显著
2. 主要失败原因：**长期推理能力差、决策能力不足、指令跟随能力弱**
3. 代码训练对不同 Agent 任务的影响不一致（并非总是正面）
4. 改进指令跟随能力和高质量多轮对齐数据可提升 Agent 性能

### 后续发展
- **AgentBench FC (Function Calling)**：基于 AgentRL 的函数调用版本
- **VisualAgentBench**：引入视觉模态的 Agent 评估

---

## 4. 其他基准

### 4.1 WebShop
- **论文**: "WebShop: Towards Scalable and Realistic Web Shopping with LLM Agents"
- **作者**: Shunyu Yao 等 (Princeton NLP)
- **代码**: https://github.com/princeton-nlp/WebShop
- **环境**: 模拟电商网站，包含 1,600+ 人工演示
- **任务**: 根据自然语言描述搜索和购买商品
- **评估**: 任务完成率、商品匹配准确率
- **特点**: 专注于电商场景，提供在线演示站点

### 4.2 ScienceWorld
- **论文**: "ScienceWorld: Is your Agent Smarter than a 5th Grader?" (EMNLP 2022)
- **作者**: Ruoyao Wang, Peter Jansen 等 (University of Arizona / MSR / AI2)
- **代码**: https://github.com/allenai/scienceworld
- **环境**: 基于文本的交互式科学实验模拟环境
- **任务**: 30 个基准任务，覆盖 10 个主题（热力学、电路、化学、生物等）
- **评估**: 渐进式评分（0.0-1.0），根据子任务完成度打分
- **关键发现**: 1.5M 参数交互式训练 Agent 优于 11B 参数静态训练模型
- **特点**: 测试 Agent 的科学推理和实验设计能力

### 4.3 InterCode
- **论文**: "InterCode: Standardizing and Benchmarking Interactive Coding" (NeurIPS 2023)
- **作者**: John Yang 等 (Princeton NLP)
- **代码**: https://github.com/princeton-nlp/intercode
- **环境**: 轻量级交互式编码框架（RL 环境）
- **任务类型**:
  - **Bash**: 在 Linux shell 中执行命令完成任务
  - **SQL**: 在数据库上执行查询
  - **Python**: Python 编程任务
  - **CTF**: 网络安全夺旗任务
  - **SWE**: 软件工程任务
- **评估**: 执行结果验证（execution-based evaluation）
- **特点**: 标准化交互式编码评估，支持多种编程环境

### 4.4 其他值得关注的基准
| 基准 | 领域 | 特点 |
|------|------|------|
| **OSWorld** | 操作系统 | 跨应用桌面任务，基于 Docker |
| **WorkArena** | 企业工作流 | ServiceNow 平台，日常办公任务 |
| **TheAgentCompany** | 真实工作流 | 模拟真实企业工作环境 |
| **SWE-bench** | 软件工程 | GitHub Issue 修复 |
| **GAIA** | 通用助手 | 多步推理 + 工具使用 |

---

## 5. 评估指标总结

| 指标 | 描述 | 适用基准 |
|------|------|---------|
| **Success Rate (SR)** | 任务是否成功完成（二值） | WebArena, ALFWorld, AgentBench |
| **Task Completion Rate** | 子任务完成比例 | ScienceWorld (渐进式) |
| **Reward / Score** | 累积奖励或综合得分 | AgentBench, InterCode |
| **Efficiency (Steps)** | 完成任务所需步数 | ALFWorld, WebArena |
| **Functional Correctness** | 结果是否达成目标功能 | WebArena (核心指标) |
| **Execution-based Eval** | 执行代码/命令验证结果 | InterCode, SWE-bench |
| **Generalization Gap** | Seen vs Unseen 性能差异 | ALFWorld, ScienceWorld |
| **Cost Efficiency** | API 调用次数 / 推理成本 | 所有基准 |

---

## 6. 对 Idea A 实验设计的建议

### 6.1 基准选择建议
基于调研结果，针对 Idea A（假设为某种 Agent 架构或训练方法），建议：

1. **主要评估基准**：**WebArena**（812 个任务，覆盖 4 个网站，功能正确性评估）
   - 理由：任务多样、评估可靠、社区认可度高（ICLR 2024）
   - 建议使用 **WebArena Verified** 版本以获得更可靠的评估

2. **补充基准**：**AgentBench**（8 环境多维度评估）
   - 理由：覆盖代码/游戏/Web 三大类，可全面评估 Agent 能力
   - 建议使用 **AgentBench FC** 版本

3. **专项评估**：
   - 代码能力：**InterCode**（Bash/SQL/Python）
   - 科学推理：**ScienceWorld**（如需评估推理能力）
   - 具身规划：**ALFWorld**（如需评估规划迁移能力）

### 6.2 评估指标建议
- **主要指标**：Success Rate（与 WebArena/AgentBench 对齐）
- **辅助指标**：
  - 任务完成步数（效率）
  - 泛化能力（seen vs unseen 场景）
  - 成本效率（API 调用次数 / token 消耗）
- **消融实验**：在不同环境子集上分别报告性能

### 6.3 实验设计注意事项
1. **计算成本**：WebArena 812 个任务 × 每个约 1 分钟 = 约 13.5 小时完整评估
   - 建议先在小规模子集（如 WebArena Verified Hard 的 137 个任务）上快速迭代
2. **基线对比**：必须包含 GPT-4 + ReAct 作为强基线
3. **统计显著性**：多次运行取平均，报告标准差
4. **环境复现**：使用 Docker 确保环境一致性
5. **评估公平性**：避免在训练数据中混入评估任务数据

### 6.4 当前 SOTA 参考
| 基准 | 最佳模型 | 性能 |
|------|---------|------|
| WebArena | GPT-4 + ReAct | 14.41% SR |
| AgentBench | GPT-4 | 4.01/4.0 |
| ALFWorld | BUTLER (IL+迁移) | ~60-80% SR (seen) |
| ScienceWorld | DRRN | ~50-60% 渐进得分 |
| InterCode (Bash) | GPT-4 | ~40-50% SR |

> 注：以上数据来自原始论文，最新 SOTA 可能已有提升。建议在实验前查阅各基准最新 leaderboard。

---

*本报告基于 WebArena (ICLR 2024)、ALFWorld (ICLR 2021)、AgentBench (ICLR 2024)、ScienceWorld (EMNLP 2022)、InterCode (NeurIPS 2023) 等论文及官方文档整理。*
