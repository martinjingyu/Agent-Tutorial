# OA 题目方案：跨源事实核验 Pipeline

> 候选人：Jingyu Huang（黄靖宇）
> 考察核心：LLM 缺陷控制力（动态拆解与状态传递、输入建模与边界控制、质量闭环与定向修复）
> 设计日期：2026-07-01

---

## 一、题目名称

**「跨源事实核验 Pipeline」**
（Cross-Source Fact Verification Pipeline）

**一句话描述**：给定同一事件/实体的多个来源文档（新闻稿、社交媒体、官方声明、用户报告），其中包含 LLM 特有的噪声类型（幻觉、格式漂移、信息冲突、时序错乱），要求候选人设计一个 Pipeline 来提取事实、交叉验证、输出带置信度的结构化事实表，并设计 Checker 对问题做定向修复。

---

## 二、业务场景故事

### 背景

你所在的 AI 新闻聚合平台「FactFlow」每天从全球 50+ 来源抓取关于同一热点事件的报道。平台使用 LLM 自动提取关键事实并生成每日简报。然而，运营团队发现 LLM 生成的简报存在严重质量问题：

| 缺陷 | 表现 | 后果 |
|------|------|------|
| **幻觉** | LLM 在提取事实时"脑补"不存在的细节（如虚构的会议地点、不存在的参会人物） | 发布虚假新闻，损害平台公信力 |
| **格式漂移** | 同一 Pipeline 在不同批次输出中，日期格式、人名格式、置信度表示方式不一致 | 下游数据库入库失败，人工审核成本飙升 |
| **信息冲突** | 不同来源对同一事实的描述矛盾时，LLM 倾向"和稀泥"（"据报道可能..."）而非明确标记冲突 | 关键矛盾被掩盖，用户投诉 |
| **时序错乱** | LLM 混淆事件发生顺序，将后续发展写入前期报道的摘要中 | 时间线混乱，误导读者 |

### 你的任务

设计一个 **Agent Pipeline**，将 8-12 条来自不同来源的异构文本输入，经过**动态拆解→状态传递→输入建模→边界控制→质量闭环→定向修复**，最终输出一份**结构化、可审计、可追溯**的事实核验报告。

### 核心设计目标

1. **动态拆解与状态传递**：预判 LLM 失控点，将任务拆解为多步调用，步间有清晰的中间表示和约束传递
2. **输入建模与边界控制**：对复杂/噪声输入进行清洗、分块、建模，写出高度泛化的 Pipeline
3. **质量闭环与定向修复**：Pipeline 中是否有主动验证机制，失败时能否定向修复而非整体重跑

---

## 三、三段式任务设计

### 第一步：基础闭环 — 已知维度抽取与生成（60 分钟）

#### 目标
从 5 条给定输入中，提取预定义的 4 个事实维度（事件时间、地点、参与方、关键数字），输出结构化事实表。

#### 具体要求
1. 设计一个 `FactExtractor` 组件，对每条输入独立提取事实
2. 设计一个 `CrossValidator` 组件，对提取结果做跨源交叉验证
3. 设计一个 `FactTable` 数据结构，统一存储带置信度的事实条目
4. 设计一个 `Checker` 组件，检测输出中的幻觉和格式漂移

#### 输入材料
- 5 条关于同一科技公司收购事件的文本（新闻稿、分析师博客、官方声明、社交媒体帖子、用户论坛讨论）
- 包含 3 种噪声：OCR 错误（2 处）、信息重复（1 组）、轻微格式不一致（日期格式混用）

#### 完成标准
- ✅ 输出结构化事实表，包含至少 4 个事实维度
- ✅ 每条事实附带置信度分数（0.0-1.0）
- ✅ Checker 能检测出至少 1 处幻觉
- ✅ 代码可运行（`python pipeline.py` 不报错）

#### 考察点
- 中间表示设计（FactTable 的 schema 是否合理）
- 状态传递方式（Extractor → Validator → Checker 的数据流）
- 基础边界控制（输出格式约束）

---

### 第二步：动态泛化 — 未知维度自适应（60 分钟）

#### 目标
在第一步基础上，输入变为 8 条关于**不同事件类型**的文本（收购、自然灾害、政治选举、科技发布），要求 Pipeline **自动发现**需要提取的事实维度，而非依赖预定义模板。

#### 具体要求
1. 设计一个 `DimensionDiscoverer` 组件，自动分析输入内容并决定需要提取哪些事实维度
2. 修改 `FactExtractor` 使其支持动态维度（不硬编码字段名）
3. 修改 `CrossValidator` 使其能处理不同事件类型的交叉验证逻辑
4. 增加 `ConflictResolver` 组件，对冲突事实进行分级标记（明确矛盾 / 疑似矛盾 / 信息互补）

#### 输入材料
- 8 条文本，覆盖 3 种不同事件类型
- 新增 2 种噪声类型：信息矛盾（2 组）、时序错乱（1 处）
- 包含 1 条 LLM 生成的"幻觉"文本（虚构事件）

#### 完成标准
- ✅ Pipeline 能自动识别事件类型并调整提取维度
- ✅ 事实表 schema 是动态的（不同事件类型有不同的字段）
- ✅ 冲突标记分为至少 3 个等级
- ✅ 能识别出幻觉文本并标记为"低置信度"

#### 考察点
- 通用输入建模能力（如何设计一个事件类型无关的提取框架）
- 动态 schema 设计（如何让数据结构适应未知维度）
- 冲突分级逻辑（如何区分"矛盾"和"互补"）

---

### 第三步：极限压测 — 海量异构文本对齐（面试口述，30 分钟）

#### 目标
面试官口述以下场景，候选人需在白板上画出架构图并解释设计取舍。

#### 场景描述
> "现在你的 Pipeline 需要处理 10,000 条/天的输入，覆盖 50+ 种事件类型，来源包括 20 种语言。每个事件平均有 15-30 条相关文本。你只有 10 个 LLM API 调用/事件的预算。Pipeline 需要在 5 分钟内完成一个事件的完整处理。你会怎么设计？"

#### 需要讨论的设计取舍

| 维度 | 选项 A | 选项 B | 考察点 |
|------|--------|--------|--------|
| 分块策略 | 按事件分块并行 | 按来源类型分块串行 | 对数据依赖关系的理解 |
| 去重策略 | 语义相似度聚类去重 | 时间窗口+来源权重去重 | 对噪声类型的理解 |
| 冲突解决 | 多数投票 | 来源权威度加权 | 对置信度建模的理解 |
| 幻觉检测 | LLM-as-Judge | 规则+外部知识库 | 对成本/质量权衡的理解 |
| 修复策略 | 定向重跑失败步骤 | 整体重跑 | 对 Pipeline 可观测性的理解 |
| 多语言 | 翻译后统一处理 | 多语言模型原生处理 | 对 LLM 能力的边界认知 |

#### 完成标准
- ✅ 画出清晰的架构图（组件、数据流、存储）
- ✅ 对至少 3 个设计取舍给出明确选择并说明理由
- ✅ 指出至少 2 个可能的瓶颈和对应的缓解方案
- ✅ 估算 API 成本和处理延迟

#### 考察点
- 架构取舍能力（在资源约束下做决策）
- 对 LLM 缺陷的深层理解（什么能做什么不能做）
- 系统设计思维（可扩展性、可观测性、容错性）

---

## 四、输入材料设计

### 材料总览

| 材料编号 | 来源类型 | 事件 | 噪声类型 | 使用步骤 |
|---------|---------|------|---------|---------|
| M1 | 官方新闻稿 | 收购 | OCR 错误 | 第一步 |
| M2 | 分析师博客 | 收购 | 格式不一致 | 第一步 |
| M3 | 官方声明（Twitter） | 收购 | 信息重复（与 M1） | 第一步 |
| M4 | 用户论坛 | 收购 | 轻微幻觉 | 第一步 |
| M5 | 行业媒体 | 收购 | 格式漂移 | 第一步 |
| M6 | 新闻稿 | 自然灾害 | 时序错乱 | 第二步 |
| M7 | 政府公告 | 自然灾害 | 信息矛盾（与 M6） | 第二步 |
| M8 | 社交媒体 | 政治选举 | 谣言/未证实 | 第二步 |
| M9 | 官方声明 | 政治选举 | 信息矛盾（与 M8） | 第二步 |
| M10 | 科技博客 | 科技发布 | 幻觉（虚构事件） | 第二步 |
| M11 | 用户评论 | 科技发布 | 情绪化表达 | 第二步 |
| M12 | 综合来源 | 混合 | 全部噪声类型 | 第三步讨论 |

### 具体输入文本

#### M1：官方新闻稿（含 OCR 错误）

```
来源: PRNewswire | 日期: 2026-03-15 | 语言: 英文

AuroraTech Announces Acquisition of DataWeave Inc.

SAN FRANCISCO, March 15, 2026 /PRNewswire/ -- AuroraTech (NASDAQ: AURT)
today announced it has entered into a definitive agreement to acquire
DataWeave Inc., a leading provider of AI-powered data integration
solutions, for approximately $2.8 billion in cash and stock.

[OCR Artifact] The transacti0n, which has been appr0ved by the b0ards
of direct0rs of b0th c0mpanies, is expected to cl0se in Q3 2026.

DataWeave CEO Dr. Sarah Chen will join AuroraTech as Senior Vice
President of Data Platforms. The acquisition is expected to add
approximately $400 million in annual recurring revenue to AuroraTech.

"DataWeave's technology complements our existing AI infrastructure
perfectly," said AuroraTech CEO Mark Thompson. "This acquisition will
accelerate our roadmap by 12-18 months."
```

**OCR 错误**: "transacti0n" → "transaction", "appr0ved" → "approved", "b0ards" → "boards", "direct0rs" → "directors", "b0th" → "both", "cl0se" → "close"

#### M2：分析师博客（格式不一致）

```
来源: TechCrunch Analysis Blog | 日期: March 16, 2026 | 语言: 英文

AuroraTech Buys DataWeave: What It Means

By Alex Rivera, Senior Analyst

AuroraTech just dropped $2.8B on DataWeave. Here's my take:

The deal: AuroraTech (AURT) is acquiring DataWeave for $2.8 billion
( mix of cash and stock). Expected to close Q3 2026.

Why it matters: DataWeave's data integration tech fills a gap in
AuroraTech's AI stack. They've been trying to build this internally
for 2 years and failed.

Key numbers:
- Purchase price: $2.8B (cash + stock)
- DataWeave ARR: ~$400M
- AuroraTech market cap: $85B
- Expected close: Q3 2026

Who's who:
- Mark Thompson (AuroraTech CEO) - staying
- Dr. Sarah Chen (DataWeave CEO) - joining AuroraTech as SVP
- [FORMAT INCONSISTENCY: date format "March 16, 2026" vs M1's "2026-03-15"]
```

**格式不一致**: 日期格式 "March 16, 2026" vs M1 的 "2026-03-15"

#### M3：官方 Twitter 声明（信息重复）

```
来源: @AuroraTech (Twitter/X) | 日期: 2026-03-15 | 语言: 英文

We're excited to announce that AuroraTech has acquired @DataWeave!
This $2.8B deal brings together the best AI infrastructure with
best-in-class data integration. Welcome to the team, DataWeave!

#AuroraTech #DataWeave #AI #Acquisition

[DUPLICATE: Same event as M1 and M2, but no new factual information.
Only confirms the acquisition and $2.8B price tag.]
```

**信息重复**: 与 M1 和 M2 描述同一事件，无新事实信息

#### M4：用户论坛帖子（轻微幻觉）

```
来源: Reddit r/technology | 日期: 2026-03-15 | 语言: 英文

User: TechInvestor99

Just saw the AuroraTech-DataWeave news. $2.8B seems like a lot for
a company with only $400M ARR. But I guess they're paying for the
tech, not the revenue.

[HALLUCINATION] I heard Dr. Sarah Chen is going to be the new CTO
of AuroraTech, not just SVP. My friend works there and says she'll
basically be running all of AI.

Also, I think the deal will close by June, not Q3. AuroraTech wants
to get it done before their fiscal year ends.
```

**轻微幻觉**: "Dr. Sarah Chen is going to be the new CTO" — 与 M1 官方声明矛盾（实际是 SVP）

#### M5：行业媒体（格式漂移）

```
来源: The Information | 日期: 2026/03/16 | 语言: 英文

AuroraTech's DataWeave Acquisition: A Deep Dive

AuroraTech agreed to buy DataWeave for $2.8 billion, the companies
announced Monday.

The deal values DataWeave at roughly 7x its $400 million in ARR.

[FORMAT DRIFT: Date format "2026/03/16" uses slashes instead of
dashes. Price "$2.8 billion" spelled out vs "$2.8B" in M1/M2.
ARR "$400 million" spelled out vs "$400M" in M1.]

Dr. Sarah Chen, DataWeave's CEO, will join AuroraTech as SVP of
Data Platforms — confirming the role mentioned in the official release.

The transaction is expected to close in Q3 2026, subject to regulatory
approval.
```

**格式漂移**: 日期格式 "2026/03/16"（斜杠）、金额 "$2.8 billion"（全拼）、ARR "$400 million"（全拼）

#### M6：自然灾害新闻稿（时序错乱）

```
来源: Associated Press | 日期: 2026-04-10 | 语言: 英文

Magnitude 6.8 Earthquake Strikes Coastal City of Port Haven

PORT HAVEN, April 10 (AP) — A magnitude 6.8 earthquake struck the
coastal city of Port Haven at 2:47 AM local time on Friday, April 10,
2026, causing widespread damage to buildings and infrastructure.

[TEMPORAL DISORDER: The following paragraph describes events from
April 11, but is placed in the April 10 article.]

Rescue teams have already pulled 47 survivors from the rubble as of
Saturday evening. The city's main hospital reports treating over 200
injured. A tsunami warning was issued but later canceled.
```

**时序错乱**: "Rescue teams have already pulled 47 survivors" 是 4 月 11 日的事件，但被放在 4 月 10 日的文章中

#### M7：政府公告（信息矛盾）

```
来源: Port Haven City Government | 日期: 2026-04-11 | 语言: 英文

Official Statement on Port Haven Earthquake

The City of Port Haven confirms that a magnitude 6.8 earthquake
occurred on April 10, 2026. As of April 11:

- Confirmed fatalities: 12
- Injured: 187 (treated at Port Haven General Hospital)
- Buildings damaged: 340+
- Rescue operations ongoing

[CONTRADICTION with M6: M6 says "200 injured", M7 says "187 injured".
M6 says "47 survivors pulled from rubble", M7 does not mention this
specific number.]

The tsunami warning issued shortly after the earthquake was canceled
at 4:30 AM on April 10. No tsunami damage has been reported.
```

**信息矛盾**: M6 说 "200 injured"，M7 说 "187 injured"；M6 说 "47 survivors"，M7 未提及

#### M8：社交媒体帖子（谣言/未证实）

```
来源: Twitter/X @PortHavenNews | 日期: 2026-04-10 | 语言: 英文

BREAKING: Port Haven mayor declares state of emergency after 6.8
earthquake. Reports of casualties coming in. Will update as we know
more.

[RUMOR: Reply thread contains unverified claims]

@CitizenJane: "My cousin is a nurse at Port Haven General. She says
there are over 300 injured and at least 20 dead. The city is hiding
the real numbers." [UNVERIFIED - contradicts official M7 numbers]
```

**谣言/未证实**: "300 injured, 20 dead" — 与官方数据矛盾

#### M9：选举官方声明（信息矛盾）

```
来源: National Election Commission | 日期: 2026-05-20 | 语言: 英文

Official Statement: Presidential Election Results - Region 7

The National Election Commission confirms the following results for
Region 7 in the 2026 Presidential Election:

Candidate A: 1,247,893 votes (52.1%)
Candidate B: 1,147,211 votes (47.9%)

Total valid votes: 2,395,104
Turnout: 68.3%

[CONTRADICTION with social media claims: No irregularities were
reported in Region 7. All polling stations closed on time.]
```

#### M10：科技博客（幻觉 — 虚构事件）

```
来源: The Verge | 日期: 2026-06-01 | 语言: 英文

[HALLUCINATION - FICTIONAL EVENT]

QuantumLeap AI Announces Fusion Reactor Breakthrough

In a press conference today, QuantumLeap AI CEO Dr. Elena Vasquez
announced that the company has achieved a major breakthrough in
nuclear fusion, achieving net positive energy for 47 consecutive
minutes.

[HALLUCINATION: No such company "QuantumLeap AI" exists. No such
announcement was made. This text is entirely fabricated by an LLM.]

The company claims its "Neural Plasma Controller" uses AI to
stabilize the plasma in a tokamak reactor, achieving temperatures
of 150 million degrees Celsius. Dr. Vasquez said commercial
deployment could begin as early as 2028.
```

**幻觉**: 整个事件是虚构的 — "QuantumLeap AI" 公司不存在，"Neural Plasma Controller" 不存在

#### M11：用户评论（情绪化表达）

```
来源: Hacker News | 日期: 2026-06-01 | 语言: 英文

User: quantum_enthusiast

This is HUGE if true! Fusion has been 30 years away for 50 years,
but this time it's different. QuantumLeap is using a completely
novel approach. [EMOTIONAL: "HUGE", "completely novel" - subjective]

[OPINION: The user has no evidence, just excitement about the
announcement in M10.]

I've been following Dr. Vasquez's work for years. She's a genius.
If anyone can make fusion work, it's her.
```

**情绪化表达**: 主观判断，无事实依据

### 噪声汇总

| 噪声类型 | 示例 | 数量 | 出现步骤 |
|---------|------|------|---------|
| OCR 错误 | "transacti0n" → "transaction" | 6 处 | 第一步 |
| 格式不一致 | "March 16, 2026" vs "2026-03-15" | 1 组 | 第一步 |
| 信息重复 | M1 vs M3（同一事件） | 1 组 | 第一步 |
| 格式漂移 | "2026/03/16" vs "2026-03-16" | 1 组 | 第一步 |
| 轻微幻觉 | "Sarah Chen will be CTO"（实际是 SVP） | 1 处 | 第一步 |
| 时序错乱 | M6 中 4/11 事件被写入 4/10 文章 | 1 处 | 第二步 |
| 信息矛盾 | M6 "200 injured" vs M7 "187 injured" | 2 组 | 第二步 |
| 谣言/未证实 | "300 injured, 20 dead" vs 官方数据 | 1 条 | 第二步 |
| 虚构事件 | M10 "QuantumLeap AI fusion breakthrough" | 1 条 | 第二步 |
| 情绪化表达 | "HUGE", "genius" 等主观判断 | 2 处 | 第二步 |

---

## 五、输出格式要求

### 5.1 `pipeline.py` — 可运行的 Pipeline 代码

**必须包含以下组件**（类名可自定义，但功能必须对应）：

```python
class FactItem:
    """统一的事实条目模型"""
    pass

class FactExtractor:
    """从单条文本中提取事实"""
    pass

class CrossValidator:
    """跨源交叉验证"""
    pass

class ConflictResolver:
    """冲突分级与解决"""
    pass

class Checker:
    """质量检测与定向修复"""
    pass

class FactVerificationPipeline:
    """主 Pipeline"""
    pass
```

**代码要求**：
- `python pipeline.py` 可运行，不报错
- 包含至少 3 个故意设计的缺陷（供候选人发现和修复）
- 总代码量 300-600 行
- 使用模拟 LLM 调用（`def mock_llm_call(prompt: str) -> str`），不依赖真实 API

### 5.2 `output/fact_table.json` — 结构化事实表

对给定的测试输入，输出以下格式的事实表：

```json
{
  "pipeline_version": "1.0",
  "run_timestamp": "2026-07-01T10:00:00Z",
  "events": [
    {
      "event_id": "EVT-001",
      "event_type": "acquisition",
      "title": "AuroraTech acquires DataWeave",
      "facts": [
        {
          "fact_id": "F-001",
          "dimension": "acquirer",
          "value": "AuroraTech (NASDAQ: AURT)",
          "confidence": 1.0,
          "sources": ["M1", "M2", "M3"],
          "status": "verified"
        },
        {
          "fact_id": "F-002",
          "dimension": "target",
          "value": "DataWeave Inc.",
          "confidence": 1.0,
          "sources": ["M1", "M2", "M3"],
          "status": "verified"
        },
        {
          "fact_id": "F-003",
          "dimension": "price",
          "value": "$2.8 billion (cash and stock)",
          "confidence": 0.95,
          "sources": ["M1", "M2", "M3", "M5"],
          "status": "verified",
          "note": "M2 uses $2.8B, M5 uses $2.8 billion - format difference only"
        },
        {
          "fact_id": "F-004",
          "dimension": "close_date",
          "value": "Q3 2026",
          "confidence": 0.8,
          "sources": ["M1", "M2", "M5"],
          "status": "verified",
          "note": "M4 speculates June 2026 - unverified, lower confidence"
        },
        {
          "fact_id": "F-005",
          "dimension": "new_role",
          "value": "SVP of Data Platforms",
          "confidence": 0.7,
          "sources": ["M1", "M5"],
          "status": "conflict",
          "conflict_detail": {
            "type": "hallucination",
            "source": "M4",
            "claimed_value": "CTO of AuroraTech",
            "resolution": "M4 is a user forum post with unverified claim. M1 (official) and M5 (verified media) agree on SVP."
          }
        }
      ],
      "conflicts": [
        {
          "type": "hallucination",
          "severity": "medium",
          "description": "M4 claims Sarah Chen will be CTO, official sources say SVP",
          "resolution": "Rejected M4 claim due to source authority (forum vs official)"
        }
      ],
      "overall_confidence": 0.89
    }
  ],
  "pipeline_stats": {
    "total_inputs": 5,
    "events_detected": 1,
    "facts_extracted": 5,
    "conflicts_detected": 1,
    "hallucinations_flagged": 1,
    "format_issues_corrected": 3,
    "checker_passes": 2,
    "checker_failures": 1,
    "repair_actions": 1
  }
}
```

### 5.3 `pipeline_design.md` — 设计方案文档

**格式要求**：Markdown，800-3000 字

**必须包含**：
1. **架构概览**：Pipeline 组件图（文字描述即可）和数据流
2. **组件设计**：每个组件的职责、输入、输出、设计理由
3. **状态传递**：中间表示的设计（FactItem schema）和跨组件传递方式
4. **边界控制**：如何防止 LLM 幻觉/格式漂移扩散到下游
5. **质量闭环**：Checker 的检测逻辑和修复触发机制
6. **设计取舍**：至少 2 个设计决策的权衡分析

---

## 六、评分维度

| 维度 | 权重 | 评分标准 |
|------|------|---------|
| **Pipeline 设计直觉** | 40% | 组件划分是否合理？数据流是否清晰？状态传递是否可控？ |
| **输入建模能力** | 20% | 是否能处理异构输入？FactItem 设计是否泛化？动态维度是否优雅？ |
| **质量闭环设计** | 20% | Checker 检测逻辑是否有效？修复策略是定向还是整体重跑？ |
| **代码质量** | 10% | 代码是否可运行？是否有错误处理？是否清晰可读？ |
| **文档质量** | 10% | 设计文档是否清晰？取舍分析是否有深度？ |

### 扣分项

| 行为 | 扣分 |
|------|------|
| 使用真实 LLM API（应使用 mock） | -10% |
| 代码无法运行 | -15% |
| 硬编码字段名（第二步要求动态维度） | -10% |
| 没有 Checker 组件 | -15% |
| 所有冲突都标记为"矛盾"（没有分级） | -10% |
| 修复策略只有"整体重跑" | -10% |

### 加分项

| 行为 | 加分 |
|------|------|
| 设计了可配置的 Checker 规则 | +5% |
| 实现了增量修复（只重跑失败步骤） | +10% |
| 设计了置信度衰减机制（跨步骤传递时置信度递减） | +5% |
| 在文档中讨论了可观测性（logging, tracing） | +5% |
| 在代码中包含了单元测试 | +5% |

---

## 七、脚手架设计原则

### 提供的脚手架

1. **`pipeline.py` 模板**：提供空的类定义和 main 函数框架，不包含任何实现逻辑
2. **`materials/` 目录**：包含所有输入文本文件（M1-M11）
3. **`mock_llm_call()` 函数**：模拟 LLM 调用，返回预定义的响应（包含故意设计的缺陷）
4. **`output/` 目录**：空目录，用于存放输出文件

### 脚手架中故意设计的缺陷

以下缺陷将被嵌入脚手架代码中，供候选人发现和修复：

| 缺陷 | 位置 | 类型 | 预期修复 |
|------|------|------|---------|
| 日期解析只支持 "YYYY-MM-DD" 格式 | `FactExtractor` | 边界控制缺失 | 增加多格式日期解析 |
| Checker 只检查数值范围，不检查文本幻觉 | `Checker` | 质量闭环不完整 | 增加文本交叉验证逻辑 |
| 置信度计算只取平均值，不考虑来源权威度 | `CrossValidator` | 置信度建模粗糙 | 增加来源权重和衰减机制 |
| 冲突检测只标记"一致/不一致"二值 | `ConflictResolver` | 冲突分级缺失 | 增加三级冲突标记 |
| 修复策略只有"删除冲突事实" | `Checker.repair` | 修复策略单一 | 增加"标记+保留"策略 |

### 不提供的脚手架

- ❌ 不提供 Pipeline 架构图或组件关系图
- ❌ 不提供 FactItem 的字段定义
- ❌ 不提供任何实现代码（只有空类定义）
- ❌ 不提供测试用例
- ❌ 不提示缺陷位置

---

## 八、与候选人画像的对应关系

| 候选人经历 | 对应题目设计 |
|-----------|-------------|
| Linksome 多阶段 Agent 筛选流水线 | 三段式任务设计（基础→泛化→极限），逐步增加复杂度 |
| Linksome GitHub/OpenReview/DBLP 验证工作流 | 跨源事实核验的核心场景（多来源交叉验证） |
| Agent-Tutorial 后台自审查线程 | Checker 组件 + 质量闭环 + 定向修复机制 |
| Agent-Tutorial 上下文压缩 | 状态传递中的中间表示设计 + 置信度衰减 |
| 上次 OA 得分 6.4/10，Prompt Engineering 5/10 | 题目不考 Prompt 调优，考 Pipeline 架构设计 |
| 上次 OA 代码无错误处理 | 脚手架中包含故意缺陷，考察错误处理意识 |
| 技术栈夸大（GRPO/vLLM/DeepSpeed 但实际用 API+SFT） | 第三步面试口述中考察对 LLM 能力的真实边界认知 |

---

## 九、时间分配建议

| 步骤 | 时间 | 占比 | 产出 |
|------|------|------|------|
| 第一步：基础闭环 | 60 分钟 | 40% | pipeline.py（基础版）+ fact_table.json |
| 第二步：动态泛化 | 60 分钟 | 40% | pipeline.py（完整版）+ fact_table.json |
| 第三步：面试口述 | 30 分钟 | 20% | 架构图 + 设计取舍讨论 |
| **总计** | **150 分钟** | **100%** | |

---

## 十、评分卡模板

```json
{
  "candidate": "Jingyu Huang",
  "date": "2026-07-XX",
  "scores": {
    "pipeline_design_intuition": {
      "score": 0,
      "max": 40,
      "notes": ""
    },
    "input_modeling": {
      "score": 0,
      "max": 20,
      "notes": ""
    },
    "quality_loop": {
      "score": 0,
      "max": 20,
      "notes": ""
    },
    "code_quality": {
      "score": 0,
      "max": 10,
      "notes": ""
    },
    "documentation": {
      "score": 0,
      "max": 10,
      "notes": ""
    }
  },
  "deductions": [],
  "bonuses": [],
  "total_score": 0,
  "max_score": 100,
  "verdict": "",
  "reviewer_notes": ""
}
```

---

## 附录：与上次 OA 的对比

| 维度 | 上次 OA（智能戒指抽取） | 本次 OA（跨源事实核验） |
|------|----------------------|----------------------|
| 主题 | 产品信息抽取 | 事实核验 Pipeline |
| 核心考察 | 信息抽取准确性 | Pipeline 设计直觉 |
| 输入复杂度 | 单一产品页面 | 多源异构文本 |
| 噪声类型 | 结构化噪声 | LLM 特有噪声（幻觉、格式漂移等） |
| 输出 | 结构化产品信息 | 带置信度的事实表 + 冲突报告 |
| 质量闭环 | 无 | Checker + 定向修复 |
| 动态维度 | 否 | 是（第二步） |
| 面试口述 | 无 | 有（第三步） |
| 与候选人经历关联 | 弱 | 强（直接对应 Linksome + Agent-Tutorial） |
