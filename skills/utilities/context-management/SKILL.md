---
name: context-management
category: utilities
description: 上下文管理最佳实践。指导 agent 在何时以及如何主动 compact 对话历史，避免上下文窗口被冗余 tool 结果污染，保持 LLM 对当前任务的聚焦。
---

# Context Management（上下文管理）

## 何时使用

当对话历史变长、tool 调用结果累积、或即将开始一个与之前任务独立的新任务时，使用本 skill 判断是否需要主动 compact 上下文。

## 核心原则

> **Compact 不是失败，而是主动的认知整理。在开始新任务前清理旧上下文，比等到 token 超阈值再被动 compact 更有效。**

## Pre-loop compact review（新）

`agent.py` 内置了 `_pre_loop_compact_review` 机制，在 **每次 agent loop 开始之前**（即处理用户消息之前）执行：

### 触发条件

1. 历史消息 ≥ 6 条
2. 调用 LLM 判断：**新用户消息是否代表一个与之前对话独立的新任务**

### LLM 判断逻辑

LLM 收到一个 review prompt，包含：
- 对话历史摘要（前部分 + 最近 4 条）
- 新用户消息
- 判断标准：是否 shift 到了新的独立任务/不同层次

### 判断示例

| 之前任务 | 新任务 | 是否 compact |
|---------|-------|------------|
| 调研学校 A | 调研学校 B | ✅ COMPACT |
| 验证候选人 A | 验证候选人 B | ✅ COMPACT |
| 调研学校 | 诊断 restart 问题 | ✅ COMPACT |
| 浏览页面 X | 继续浏览页面 X | ❌ 不 compact |
| 保存报告 | 修改报告 typo | ❌ 不 compact |
| 调研 A | 补充 A 的更多细节 | ❌ 不 compact |

### 失败安全

如果 LLM 调用失败（网络、解析等），**静默跳过**，不进行 compact，保证不会因 review 失败而丢失上下文。

### 与自动 compact 的关系

| 机制 | 触发时机 | 判断方式 | 目的 |
|------|---------|---------|------|
| `_pre_loop_compact_review` | loop 开始前 | LLM 语义判断 | 跨任务边界清理 |
| `_pre_action_compact_check` | tool_calls 执行前 | 硬阈值（数量+token） | 同任务内防溢出 |

两者互补：pre-loop 负责**任务级别的语义压缩**，pre-action 负责**token 级别的防溢出压缩**。

## 自动 compact 机制（原有）

`agent.py` 内置了 `_pre_action_compact_check` 机制，在每次执行 tool_calls 前自动判断：

### 触发条件（同时满足）

1. **tool 结果数量**：上一次 `respond_to_user` 之后累积了 ≥8 个 tool 结果
2. **token 压力**：当前 token 数超过阈值的 60%

### 触发后的行为

- 自动调用 `compact_messages` 压缩中间段历史
- 保留开头 2 条和末尾 12 条消息
- 压缩后的摘要以 `[CONTEXT COMPACTION - REFERENCE ONLY]` 标记

## 手动 compact 场景

除了自动机制，agent 在以下场景应主动调用 `compact_context` tool：

### 场景 1：任务边界明确

当你完成了一个独立的任务单元（如完成了一个学校的调研、生成了一份报告），即将开始下一个独立任务时：

```
✅ 完成学校 A 的调研报告 → compact → 开始学校 B 的调研
✅ 完成 link verification → compact → 开始 stage1 screening report
✅ 完成一轮浏览器调研 → compact → 开始分析结果
```

### 场景 2：tool 结果大量冗余

当连续多轮 tool 调用产生了大量结果，但其中大部分是中间步骤（如多次 browser_navigate 的 snapshot），而核心结论已经得出时：

```
✅ 已经访问了 5 个页面找到了需要的信息 → compact → 开始写报告
✅ 已经验证了 3 个 GitHub repo → compact → 开始交叉验证
```

### 场景 3：LLM 开始"迷失"

当你发现 LLM 的回复开始：
- 重复之前已经做过的操作
- 忽略最近的 tool 结果
- 引用很久以前的信息而不是最新的

这通常是上下文被"稀释"的信号，应主动 compact。

### 场景 4：用户提供了新的指令

当用户在当前 session 中给出了与之前任务无关的新指令时：

```
用户：先调研学校 A
...（多轮交互后完成）
用户：好的，现在看看学校 B
→ 在开始学校 B 的调研前，compact 掉学校 A 的详细 tool 结果
```

### 场景 5：反复遇到相同错误

当你连续 3+ 次遇到**同一个工具、同一类错误**时，不要继续重试。此时问题不是暂时的，而是代码或环境层面的根因。

**正确做法**：

```
第1次报错 → 重试（可能是暂时的）
第2次同类型报错 → 换一种方式再试
第3次同类型报错 → STOP！开始分析源码
```

**分析步骤**：

1. 用 `read_file` 查看相关源码：
   - `research_agent/agent.py` — 主循环逻辑
   - `research_agent/context.py` — compact、token 计算
   - `research_agent/tools/*.py` — 具体工具实现
   - `research_agent/prompts.py` — system prompt
2. 定位错误发生的代码路径
3. 判断是 bug、环境问题、还是设计缺陷
4. 如果是 bug，用 `write_file` 修复
5. 调用 `request_restart(changes=[...])` 请求重启
6. 如果是可复用的教训，保存到 memory 或 skill

**重启机制**（Master-Worker 架构）：

```
┌─ Guardian (master) ─────────────────────┐
│  ① 启动 Worker 子进程                     │
│  ② 监听 Worker 退出码                     │
│  ③ 退出码 42 → 重新 spawn Worker          │
│  ④ 循环直到用户 Ctrl+C                     │
└──────────────────────────────────────────┘
                    │
                    ▼
┌─ Worker (agent) ────────────────────────┐
│  ① 正常执行任务                            │
│  ② 发现 bug → 修改源码                     │
│  ③ 调用 request_restart(changes=[...])    │
│  ④ 自动 sys.exit(42)                     │
│  ⑤ Guardian 检测到 42 → 重启 Worker       │
│  ⑥ 新 Worker 加载修改后的代码               │
└──────────────────────────────────────────┘
```

**使用方式**：

```bash
# 启动时加 --guardian 参数
python run_research_agent.py --guardian "调研学校 A 的 AI 专业"

# Chat 模式也支持
python run_research_agent.py --guardian --chat
```

**示例**：terminal 工具读取中文文件返回 `NoneType` 错误
→ 分析发现是 PowerShell 管道问题
→ 修复：在 system prompt 中强调用 `read_file` 替代 terminal 读文件
→ 调用 `request_restart(changes=["更新 system prompt，强调 read_file 优先"])`
→ 进程退出，Guardian 自动重启
→ 新进程加载了修改后的 prompts.py

## High-Level 调度 Agent 行为红线（2026-06-30 新增）

作为调度 agent，以下行为**严格禁止**：

### 红线 1：Worker 出错时不要自行补救

如果 worker 报错、输出不符合预期、或文件写入失败，**不要自己动手写文件来"补上"**。

```
❌ 错误做法：worker 写 paper_idea.md 失败 → 我自己 write_file 写一份
✅ 正确做法：kanban_show_task 查看错误 → 向用户报告错误详情 → 让用户决定下一步
```

理由：我是调度 agent，不是 worker。自行补救会：
- 掩盖 worker 的真实问题（bug、配置错误、权限问题）
- 让用户误以为 pipeline 正常完成
- 绕过 skill 中定义的质量控制流程

### 红线 2：不要反复读 worker 内部 session 缓存文件

不要用 `read_file` 读 `sessions/kanban/*/workers/*.json` 来轮询 worker 状态。

```
❌ 错误做法：read_file('sessions/kanban/board/workers/t_xxx.json') 反复读
✅ 正确做法：
   1. kanban_show_task(board, task_id) 检查状态
   2. kanban_notify_subscribe(board, events=['pipeline_complete']) 订阅通知
   3. respond_to_user 结束本轮，等通知触发
```

理由：
- 缓存文件是内部实现细节，格式可能变化
- 轮询浪费 token（每次 read_file 结果都进上下文）
- 订阅机制就是为这个场景设计的

### 红线 3：不要空等

任务发起后，不要反复 poll 状态或等待 worker 完成。

```
❌ 错误做法：kanban_dispatch → read_file(worker cache) → 循环
✅ 正确做法：kanban_dispatch → kanban_notify_subscribe → respond_to_user
```

## 不要 compact 的场景

- **正在执行一个连续的任务流**（如正在逐页浏览一个网站），compact 会丢失中间状态
- **即将使用 browser 工具**，compact 后 browser 的 snapshot 引用会失效
- **token 还很充裕**（< 40% 阈值）且 tool 结果不多（< 5 个）
- **用户刚给出了 correction/调整**，compact 会丢失修正上下文

## compact 时的 focus 参数

调用 `compact_context` 时，`focus` 参数告诉 LLM 在压缩时重点保留什么：

| 当前任务 | focus 值 |
|---------|---------|
| 学校调研 | `"学校调研：{学校名} {专业名} 的课程设置、研究方向"` |
| Link verification | `"link verification：候选人的 GitHub/论文/项目真实性验证"` |
| 报告生成 | `"报告生成：基于已有调研数据生成结构化报告"` |
| 多任务切换 | `"新任务：{新任务描述}"` |

## 与 system prompt 的关系

compact 后，system prompt 会重新构建（`build_system_prompt`），确保：
- 最新的 skill index 被包含
- 最新的 memory snapshot 被包含
- 工具定义是最新的

## References

- `research_agent/agent.py` — `_pre_loop_compact_review` 和 `_pre_action_compact_check` 方法实现
- `research_agent/context.py` — `compact_messages` 函数实现
- `research_agent/tools/compact.py` — `compact_context` tool 实现
