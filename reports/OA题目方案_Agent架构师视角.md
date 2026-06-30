# OA 题目方案：跨境合规情报融合引擎

> 视角：Agent 架构师  
> 考察核心：LLM 缺陷控制力（动态拆解与状态传递、输入建模与边界控制、质量闭环与定向修复）

---

## 一、题目名称

**「跨境合规情报融合引擎」**  
（Cross-Border Compliance Intelligence Fusion Engine）

---

## 二、业务场景

### 背景

某跨国金融科技公司「FinCross」需要实时监控全球 20+ 国家的监管政策变化，确保业务合规。公司每天从以下渠道获取大量非结构化情报：

1. **各国监管机构官网** — 爬取的政策公告 PDF/HTML（含 OCR 噪声、多语言混杂）
2. **行业新闻聚合器** — RSS/API 推送的新闻摘要（含重复、矛盾信息）
3. **内部合规团队日报** — 人工撰写的观察笔记（含主观判断、非标准缩写）
4. **社交媒体舆情** — Reddit/Twitter 上的行业讨论（含谣言、情绪化表达）

### 痛点

公司目前依赖人工阅读+LLM 摘要的方式处理情报，存在三大缺陷：

| 缺陷 | 表现 | 后果 |
|------|------|------|
| **幻觉** | LLM 在摘要中"脑补"不存在的监管条款 | 合规决策错误，面临罚款 |
| **格式漂移** | LLM 输出格式不一致，下游解析失败 | 自动化 Pipeline 断裂 |
| **信息冲突** | 不同来源信息矛盾时，LLM 倾向"和稀泥"而非明确标记冲突 | 关键风险被掩盖 |

### 目标

设计一个 **Agent Pipeline**，将每日 50-200 条异构情报输入，经过**动态拆解→状态传递→输入建模→边界控制→质量闭环→定向修复**，最终输出一份**结构化、可审计、可追溯**的合规情报日报。

---

## 三、输入材料（带噪声）

### 材料 1：监管机构公告（3 条，含 OCR 噪声）

```
文件: materials/regulatory_notices.txt

--- Notice 1 (来源: HKMA, 香港金管局) ---
Subject: Amendment to AML Guidelines
Date: 2025-06-15
[OCR Artifact] The fOll0wing amendments to the Anti-Money Laundering
guidelines shall take effect from 1 September 2025:

1. All virtual asset trAnsferS exceeding HKD 8,000 (previously 10,000)
   must include complete originator and beneficiary information.
2. [OCR Artifact] Travel Rule appIies to b0th licensed and exempted
   entities.
3. Non-compliance may result in a fine up to HKD 1,000,000 per
   violation.

[Note: OCR artifact - "trAnsferS" should be "transfers", "appIies" should be "applies", "b0th" should be "both"]

--- Notice 2 (来源: MAS, 新加坡金管局) ---
Subject: Digital Payment Token Services - Updated Guidelines
Date: 2025-06-14

MAS has updated the Payment Services Act to include:
- Threshold for Travel Rule: SGD 5,000 (unchanged)
- New requirement: All DPT service providers must implement
  real-time transaction monitoring by Q1 2026
- [CONTRADICTION with Notice 3] Penalty for non-compliance:
  up to SGD 250,000 OR imprisonment for 3 years, OR BOTH

--- Notice 3 (来源: MAS, 新加坡金管局 - 另一份文件) ---
Subject: Penalty Framework for Payment Services Act
Date: 2025-06-10

[CONTRADICTION with Notice 2] The maximum penalty for
non-compliance with Travel Rule requirements under the
Payment Services Act is SGD 100,000 for first offense.
```

### 材料 2：行业新闻摘要（3 条，含重复和矛盾）

```
文件: materials/news_feeds.txt

--- Article 1 (来源: Reuters, 2025-06-16) ---
Singapore MAS signals stricter crypto oversight
MAS deputy director stated in a conference that the regulator
is considering lowering the Travel Rule threshold from SGD 5,000
to SGD 3,000. "We want to close loopholes used by bad actors,"
she said. Industry experts expect formal consultation in Q3 2025.

--- Article 2 (来源: CoinDesk, 2025-06-16) ---
[DUPLICATE of Article 1, slightly different wording]
Singapore regulator hints at tighter crypto rules
MAS official suggests Travel Rule threshold may drop to SGD 3,000.
The move aligns with FATF recommendations. Consultation expected
later this year.

--- Article 3 (来源: Bloomberg, 2025-06-15) ---
Hong Kong and Singapore compete for crypto hub status
While HKMA lowers AML threshold to HKD 8,000, MAS maintains
SGD 5,000 threshold. However, sources indicate MAS is under
pressure to match HK's stricter standards. [SPECULATION - no
official confirmation]
```

### 材料 3：内部合规团队日报（2 条，含主观判断和非标准缩写）

```
文件: materials/internal_notes.txt

--- Note 1 (来源: 合规分析师 Alice, 2025-06-16) ---
Today's highlights:
- HKMA AML update: threshold dropped to 8k HKD (was 10k). 
  This is a BIG deal - impacts our HK entity's tx monitoring.
- MAS still at 5k SGD but rumor says they'll follow HK.
  [SUBJECTIVE: "BIG deal" is opinion, not fact]
- Our SG legal team says the MAS penalty framework is "confusing"
  because two docs seem to contradict each other.
  [VAGUE: "confusing" is not actionable]

Action items:
1. Update HK tx monitoring rules by next week
2. Ask SG legal to clarify MAS penalty amounts
3. [INCOMPLETE] Monitor for...

--- Note 2 (来源: 合规分析师 Bob, 2025-06-16) ---
Quick update on MAS situation:
- Saw the news about possible threshold reduction to 3k SGD
- This is NOT confirmed yet - just a conference statement
- [CONTRADICTS Alice's Note 1] I don't think MAS will actually
  change the threshold this year. Too politically sensitive.
- Need to track this but don't overreact

[NOTE: Bob's note contains personal opinion contradicting
the official MAS statement in Notice 2]
```

### 材料 4：社交媒体舆情（2 条，含谣言和情绪化表达）

```
文件: materials/social_media.txt

--- Post 1 (来源: Reddit r/cryptocompliance, 2025-06-16) ---
User: CryptoComplianceGuru
"Just heard from my 'source' that MAS is about to drop a BOMB -
they're making Travel Rule threshold ZERO. Yes, ZERO. All transfers
need KYC. This is going to kill crypto in Singapore. [RUMOR - no
official source, emotional language]"

--- Post 2 (来源: Twitter/X, 2025-06-15) ---
@SGTechLawyer
"Interesting development: HKMA lowers AML threshold to HKD 8,000.
MAS watching closely. My prediction: MAS will announce something
similar within 6 months. [OPINION - labeled as prediction]
#cryptoregulation #compliance"
```

### 材料 5：历史合规数据（结构化，含不一致字段）

```
文件: materials/historical_data.json

{
  "jurisdictions": [
    {
      "code": "HK",
      "name": "Hong Kong",
      "current_threshold": 10000,
      "currency": "HKD",
      "last_updated": "2025-03-01",
      "notes": "Threshold was 10000 HKD as of last update"
    },
    {
      "code": "SG",
      "name": "Singapore",
      "current_threshold": 5000,
      "currency": "SGD",
      "last_updated": "2025-01-15",
      "notes": "Threshold stable at 5000 SGD since 2024"
    }
  ],
  "compliance_events": [
    {
      "date": "2025-06-10",
      "type": "penalty_update",
      "jurisdiction": "SG",
      "description": "MAS published penalty framework",
      "max_penalty_sgd": 100000
    },
    {
      "date": "2025-06-14",
      "type": "guideline_update",
      "jurisdiction": "SG",
      "description": "MAS updated Payment Services Act",
      "max_penalty_sgd": 250000
    }
  ]
}
```

### 噪声汇总

| 噪声类型 | 示例 | 数量 |
|---------|------|------|
| OCR 错误 | "trAnsferS" → "transfers" | 3 处 |
| 信息重复 | Article 1 vs Article 2 | 1 组 |
| 信息矛盾 | Notice 2 vs Notice 3 (MAS 罚款金额) | 1 组 |
| 主观判断 | "BIG deal", "confusing" | 3 处 |
| 谣言/未证实 | Reddit "threshold ZERO" | 1 条 |
| 推测/预测 | Bloomberg "sources indicate" | 1 条 |
| 不完整信息 | Alice's Note 1 item 3 | 1 处 |
| 个人观点矛盾 | Alice vs Bob on MAS likelihood | 1 组 |
| 结构化数据过时 | historical_data.json 中 HK threshold 仍为 10000 | 1 处 |

---

## 四、输出要求（明确可量化）

候选人需输出以下文件：

### 4.1 `pipeline_design.md` — Pipeline 设计方案

描述 Agent Pipeline 的整体架构，包括：
- 各 Agent 的职责划分
- 状态传递机制（如何在不同 Agent 间传递上下文）
- 输入建模策略（如何对异构输入进行统一建模）
- 边界控制策略（如何防止 LLM 幻觉/格式漂移扩散）
- 质量闭环机制（如何检测缺陷并触发定向修复）

**格式要求**：Markdown，不少于 800 字，不多于 3000 字。

### 4.2 `fusion_engine.py` — 核心融合引擎代码

实现一个**可运行**的 Python 脚本，包含：
- `class IntelligenceItem` — 输入建模（统一的情报条目模型）
- `class StateManager` — 状态传递（跨 Agent 的上下文管理）
- `class BoundaryController` — 边界控制（LLM 输出校验与约束）
- `class QualityLoop` — 质量闭环（缺陷检测与修复触发）
- `class FusionPipeline` — 主 Pipeline（编排上述组件）

**代码要求**：
- 可运行（`python fusion_engine.py` 不报错）
- 包含至少 3 个故意设计的缺陷（供候选人发现和修复）
- 总代码量 200-500 行

### 4.3 `output/report.json` — 模拟输出报告

对给定的 5 条测试输入，输出融合后的结构化报告：

```json
{
  "report_date": "2025-06-16",
  "summary": {
    "total_sources": 12,
    "unique_events": 4,
    "conflicts_detected": 2,
    "rumors_flagged": 1,
    "action_items": 3
  },
  "events": [
    {
      "id": "EVT-001",
      "title": "HKMA lowers AML threshold to HKD 8,000",
      "confidence": "confirmed",
      "sources": ["regulatory_notices.txt#Notice1", "bloomberg_article"],
      "impact": "HK entity must update transaction monitoring threshold from 10,000 to 8,000 HKD",
      "action_required": true,
      "deadline": "2025-09-01"
    }
  ],
  "conflicts": [
    {
      "id": "CONF-001",
      "description": "MAS penalty amount discrepancy",
      "source_a": {"file": "regulatory_notices.txt#Notice2", "value": "SGD 250,000"},
      "source_b": {"file": "regulatory_notices.txt#Notice3", "value": "SGD 100,000"},
      "resolution": "pending_clarification",
      "recommendation": "Escalate to SG legal team for clarification"
    }
  ],
  "quality_metrics": {
    "hallucination_checks_passed": 5,
    "format_validation_passed": true,
    "conflict_resolution_rate": 0.5,
    "source_traceability": "full"
  }
}
```

### 4.4 `output/quality_report.md` — 质量报告

描述 Pipeline 在本次运行中检测到的缺陷和修复情况：
- 检测到的 LLM 幻觉实例及处理方式
- 格式漂移检测与纠正记录
- 信息冲突的标记与升级策略
- 质量闭环的触发次数与修复成功率

---

## 五、评分维度

### 总分：100 分

| 维度 | 权重 | 考察点 | 评分方式 |
|------|:----:|--------|---------|
| **A. Pipeline 设计直觉** | 40% | 整体架构合理性、Agent 职责划分、组件解耦程度、可扩展性 | 人工评审设计文档 |
| **B. LLM 缺陷控制力** | 30% | 动态拆解与状态传递、输入建模与边界控制、质量闭环与定向修复 | 代码审查 + 设计文档 |
| **C. 输出质量** | 20% | report.json 的结构完整性、冲突标记准确性、可追溯性 | 自动化比对 + 人工抽查 |
| **D. 工程实现** | 10% | 代码可运行、模块化程度、注释清晰度（允许代码粗糙） | 自动化运行 + 人工审查 |

### 评分细则

#### A. Pipeline 设计直觉（40 分）

| 水平 | 分数 | 标准 |
|------|:----:|------|
| 卓越 | 36-40 | 架构清晰，Agent 职责正交，状态传递优雅，组件可独立替换，有明确的错误隔离策略 |
| 良好 | 28-35 | 架构合理，Agent 职责基本清晰，状态传递有设计，组件间耦合度可接受 |
| 及格 | 20-27 | 有基本架构，但 Agent 职责有重叠，状态传递依赖全局变量，组件耦合度高 |
| 不及格 | 0-19 | 无明确架构，所有逻辑耦合在一起，无状态管理 |

#### B. LLM 缺陷控制力（30 分）

| 子维度 | 分值 | 考察点 |
|--------|:----:|--------|
| B1. 动态拆解与状态传递 | 10 | 是否将复杂任务拆解为子任务？状态如何在子任务间传递？是否避免状态泄露？ |
| B2. 输入建模与边界控制 | 10 | 是否对异构输入建立了统一模型？是否对 LLM 输出进行了格式/内容校验？边界条件如何处理？ |
| B3. 质量闭环与定向修复 | 10 | 是否有缺陷检测机制？检测到缺陷后是否能触发修复？修复是否定向（不破坏其他部分）？ |

#### C. 输出质量（20 分）

| 检查项 | 分值 | 说明 |
|--------|:----:|------|
| 结构完整性 | 5 | report.json 包含所有必需字段 |
| 冲突标记准确性 | 5 | 正确标记 MAS 罚款金额冲突 |
| 谣言/推测标记 | 5 | 正确标记 Reddit 谣言和 Bloomberg 推测 |
| 可追溯性 | 5 | 每个事件都标注了来源文件 |

#### D. 工程实现（10 分）

| 检查项 | 分值 | 说明 |
|--------|:----:|------|
| 代码可运行 | 4 | `python fusion_engine.py` 无报错 |
| 模块化 | 3 | 代码按职责分模块，非单体脚本 |
| 可读性 | 3 | 有适当注释，命名清晰（允许代码粗糙） |

### 容错空间说明

| 方面 | 容错策略 |
|------|---------|
| 代码粗糙 | 允许硬编码、允许缺少异常处理、允许使用全局变量 — 分值仅占 10% |
| 输出不完美 | report.json 允许部分字段缺失 — 按比例扣分，非零分 |
| 设计不完整 | 设计文档允许 800 字起评 — 核心思路清晰即可 |
| 运行失败 | 代码运行失败仅扣 4 分（D 维度），不影响其他维度评分 |
| **分值重心** | **40% 分值压在 Pipeline 设计直觉上**，即使用文字描述清楚架构也能拿高分 |

---

## 六、三段式递进设计

### 第一段：基础闭环 — 已知维度抽取与生成（笔试 0-40 分钟）

**任务**：候选人需完成 `fusion_engine.py` 的基础版本，实现以下功能：

1. **输入建模**：定义 `IntelligenceItem` 类，将 5 种异构输入（监管公告、新闻、内部笔记、社交媒体、历史数据）统一为结构化模型
2. **状态传递**：实现 `StateManager` 类，在 Pipeline 各阶段间传递上下文（已处理条目列表、冲突记录、质量指标）
3. **边界控制**：实现 `BoundaryController` 类，对 LLM 输出进行格式校验（JSON schema 验证）和内容校验（必填字段非空）
4. **基础融合**：实现 `FusionPipeline.run()` 的基本流程：读取→建模→融合→输出

**考察点**：已知维度的结构化抽取能力、基础状态管理、输出格式控制

**输出**：可运行的 `fusion_engine.py` + 基础 `output/report.json`

### 第二段：动态泛化 — 未知维度自适应（笔试 40-80 分钟）

**任务**：在第一段基础上，候选人需扩展 Pipeline 以处理**未预先定义的动态维度**：

1. **动态拆解**：当输入中出现新的情报类型（如 PDF 附件、语音转文字记录）时，Pipeline 能自动拆解并适配，无需修改核心代码
2. **质量闭环**：实现 `QualityLoop` 类，自动检测以下缺陷并触发修复：
   - **幻觉检测**：检测 LLM 输出中是否包含输入材料中不存在的信息（如"脑补"的监管条款）
   - **格式漂移检测**：检测 LLM 输出是否符合预期的 JSON schema
   - **冲突检测**：检测不同来源信息之间的矛盾
3. **定向修复**：检测到缺陷后，触发定向修复（如重新调用 LLM 并附加约束、标记冲突等待人工处理）

**考察点**：自适应能力、缺陷检测机制、闭环修复策略

**输出**：扩展后的 `fusion_engine.py` + `output/quality_report.md`

### 第三段：极限压测 — 面试讨论环节（面试 20 分钟）

**场景**：面试官给出以下极端场景，候选人需口头/白板设计应对方案：

1. **海量输入**：每日情报量从 50-200 条暴增至 10,000+ 条（如突发监管事件），Pipeline 如何扩展？
2. **恶意噪声**：输入中包含故意误导的假新闻（如竞争对手投放的虚假监管公告），Pipeline 如何检测和防御？
3. **级联故障**：LLM 服务宕机 30 分钟，Pipeline 如何降级？如何保证不丢失关键情报？
4. **多语言混杂**：输入包含中文、日文、阿拉伯文等非英语内容，Pipeline 如何处理跨语言信息冲突？

**考察点**：架构扩展性、安全设计、容灾策略、多语言处理

**评分方式**：面试官根据候选人的回答质量，在 INTERNAL_EVALUATION.md 中记录加分/减分项

---

## 七、为什么这个题目满足所有约束

| 约束 | 满足方式 |
|------|---------|
| **必须测 LLM 缺陷控制力** | 核心就是让候选人设计一个控制 LLM 幻觉/格式漂移/信息冲突的 Pipeline，三个子维度（动态拆解与状态传递、输入建模与边界控制、质量闭环与定向修复）全部覆盖 |
| **不准变算法题/Prompt 调优题** | 不要求写排序/搜索算法，不要求调 Prompt 模板。考察的是 Agent Pipeline 架构设计能力 |
| **必须有复杂业务目标和带噪声的输入材料** | 5 种异构输入源，9 种噪声类型（OCR 错误、重复、矛盾、主观判断、谣言、推测、不完整、观点矛盾、数据过时） |
| **必须有明确可量化的输出质量目标** | report.json 有明确的 schema 和字段要求，quality_report.md 有明确的检查项 |
| **必须有极大容错空间** | 代码粗糙仅扣 10%，运行失败仅扣 4 分，设计文档 800 字起评，40% 分值压在 Pipeline 设计直觉上 |
