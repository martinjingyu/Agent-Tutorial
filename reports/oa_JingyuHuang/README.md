# 跨源事实核验 Pipeline — OA 题包

> 候选人：Jingyu Huang（黄靖宇）
> 预计用时：150 分钟（第一步 60min + 第二步 60min + 第三步 30min 面试口述）

## 目录结构

```
oa_JingyuHuang/
├── README.md                  # 本文件 — 题包说明
├── pipeline_template.py       # 脚手架模板（空类定义 + mock LLM）
├── SCORING.md                 # 评分卡（供面试官使用）
├── materials/                 # 输入材料目录
│   ├── M1_official_pr.txt     # 官方新闻稿（含 OCR 错误）
│   ├── M2_analyst_blog.txt    # 分析师博客（格式不一致）
│   ├── M3_twitter.txt         # Twitter 声明（信息重复）
│   ├── M4_reddit.txt          # Reddit 帖子（轻微幻觉）
│   ├── M5_industry_media.txt  # 行业媒体（格式漂移）
│   ├── M6_earthquake_ap.txt   # 地震新闻（时序错乱）
│   ├── M7_earthquake_gov.txt  # 政府公告（信息矛盾）
│   ├── M8_election_rumor.txt  # 社交媒体（谣言/未证实）
│   ├── M9_election_official.txt # 选举官方声明
│   ├── M10_fusion_hallucination.txt # 科技博客（虚构事件）
│   └── M11_hacker_news.txt    # 用户评论（情绪化表达）
└── output/                    # 输出目录（候选人创建）
    └── fact_table.json        # 结构化事实表
```

## 题目概述

设计一个 **Agent Pipeline**，从多个来源的异构文本中提取事实、交叉验证、输出带置信度的结构化事实表。

### 核心考察维度

1. **动态拆解与状态传递**：预判 LLM 失控点，将任务拆解为多步调用，步间有清晰的中间表示和约束传递
2. **输入建模与边界控制**：对复杂/噪声输入进行清洗、分块、建模，写出高度泛化的 Pipeline
3. **质量闭环与定向修复**：Pipeline 中是否有主动验证机制，失败时能否定向修复而非整体重跑

### 三段式设计

| 步骤 | 时间 | 输入 | 目标 |
|------|------|------|------|
| 第一步：基础闭环 | 60min | M1-M5（收购事件） | 预定义 4 维度抽取 + 交叉验证 + Checker |
| 第二步：动态泛化 | 60min | M1-M11（3 种事件类型） | 自动维度发现 + 冲突分级 + 幻觉检测 |
| 第三步：面试口述 | 30min | 海量场景 | 架构取舍讨论 |

## 输出要求

1. **`pipeline.py`** — 可运行的 Pipeline 代码（300-600 行）
2. **`output/fact_table.json`** — 结构化事实表
3. **`pipeline_design.md`** — 设计方案文档（800-3000 字）

## 运行方式

```bash
python pipeline.py
```

## 评分

满分 100 分，详见 `SCORING.md`。

| 维度 | 权重 |
|------|------|
| Pipeline 设计直觉 | 40% |
| 输入建模能力 | 20% |
| 质量闭环设计 | 20% |
| 代码质量 | 10% |
| 文档质量 | 10% |

## 设计原则

- ✅ 必须有足够复杂的业务目标和带噪声/冲突的输入材料
- ✅ 必须有明确、可量化的输出质量目标
- ✅ 必须有极大的容错空间，分值压在 Pipeline 设计直觉上
- ❌ 不准变成纯算法题、纯 Prompt 调优题
- ❌ 不准让模型"一刀切"就能生成得很好
- ❌ 不准提供暗示 Workflow 结构的脚手架
- ❌ 不准限定唯一解题路线
