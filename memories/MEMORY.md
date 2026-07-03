§
§
Workspace root: C:\Users\LX034\Code\
Agent-Tutorial subdirectory: C:\Users\LX034\Code\Agent-Tutorial\
Reports directory: C:\Users\LX034\Code\Agent-Tutorial\reports\
JD docx file: C:\Users\LX034\Code\AI算法实习生职位JD_20250506.docx (workspace root)
There is also a copy at Agent-Tutorial\reports\AI算法实习生职位JD_20250506.docx
§
Windows file operations: Python shutil.move may silently fail (no error, no move) in some cases on Windows. Use terminal tool with cmd.exe `move` command instead for reliable file moves.
§
read_file tool natively supports .docx files — no need to convert to .txt first. Works for Chinese/English bilingual docx content.
§
skill_manage patch with Chinese text may fail due to encoding mismatch. Workaround: use skill_manage edit (full rewrite) instead of patch when updating Chinese content in SKILL.md.
§
Windows terminal tool + PowerShell + Chinese UTF-8: executing PowerShell commands that output Chinese UTF-8 text (e.g., `Get-Content ... -Encoding UTF8`) causes `TypeError: 'NoneType' object is not subscriptable` — the pipe/stdout handling breaks. Workaround: use `read_file` instead of terminal to read file contents; or use `cmd /c type` instead of PowerShell for simple file reads.
§
Windows terminal + PowerShell 读取中文 UTF-8 文件时，管道 stdout 返回 None，触发 TypeError: 'NoneType' object is not subscriptable。解决方案：始终用 read_file 读取文件内容，terminal 只用于执行命令（git、copy、move 等）。已创建 utilities/windows-file-operations skill 记录此最佳实践，所有涉及文件读取的 skill 都应引用它。
§
agent.py 新增 _pre_action_compact_check 机制：在每次执行 tool_calls 前，检查上一次 respond_to_user 之后累积的 tool 结果数量（≥8 个）和 token 压力（>60% 阈值），同时满足时自动 compact 上下文。配套 skill: utilities/context-management。BASE_SYSTEM_PROMPT 已更新，告知 agent 此自动机制的存在。
§
Error recovery pattern: 当 agent 连续 3+ 次遇到同一个工具、同一类错误时，应停止重试，转而 review 源码（research_agent/ 目录下的 agent.py、context.py、tools/*.py、prompts.py），定位根因并修复。这个行为指导已加入 BASE_SYSTEM_PROMPT 的 "Error recovery" 段落，以及 utilities/context-management skill 的"场景 5：反复遇到相同错误"。
§
Master-Worker 自更新架构：guardian.py（Master）作为稳定的守护进程，启动 Worker（agent）子进程。Worker 修改源码后调用 request_restart(changes=[...]) tool，然后 sys.exit(42)。Guardian 检测到退出码 42 后重新 spawn Worker，新 Worker 加载修改后的代码。使用 --guardian 参数启动。配套文件：research_agent/guardian.py, research_agent/tools/restart.py。
§
ConsoleUI class (research_agent/ui.py) does NOT have a `status()` method. It only has `event()`, `session_start()`, `model_start()`, `compact()`, and other UI methods. Any code calling `self.ui.status(...)` will raise AttributeError. Use `self.ui.event(label, detail)` instead for status-like messages.
§
Windows CLI: `head` command is not available on Windows. Use `cmd /c "more"` or PowerShell `Select-Object -First N` instead. For `tasklist` filtering, use quoted syntax: `tasklist /fi "PID eq 1234"` (the filter expression must be in quotes). `%PPID%` is not a standard Windows environment variable; use `wmic process where "processid=%PID%" get parentprocessid` or PowerShell to get parent PID.
§
Python __pycache__ stale cache issue: When modifying source code that gets imported by a subprocess (e.g., Guardian spawning a Worker), stale `.pyc` files in `__pycache__` directories can cause the old code to execute instead of the new code. Always clean `__pycache__` directories after modifying source files that are imported by child processes. Use `terminal(command='cmd /c "rmdir /s /q __pycache__"')` or `terminal(command='cmd /c "for /d /r . %d in (__pycache__) do @if exist %d rmdir /s /q %d"')` to recursively clean all `__pycache__` directories.
§
CDP WebSocket URL auto-detection pattern: When writing Python scripts that connect to Chrome via CDP, the standard approach is to fetch http://localhost:9222/json/version to get the WebSocketDebuggerUrl. This fails with urllib.error.URLError (Connection refused) if Chrome isn't running with --remote-debugging-port=9222. Always include a fallback to manual WebSocket URL input. The demo script at workspace/accessibility_api_demo.py shows this pattern.
§
CDP WebSocket 连接 Chrome 时，Chrome 113+ 版本需要加 --remote-allow-origins=* 参数，否则 WebSocket handshake 会返回 403 Forbidden。所有涉及 CDP 连接的 demo/脚本都应在启动命令和文档中包含此参数。
§
browser_navigate snapshot structure: The tool returns a dict with `success` (bool) and `data` (dict containing `title`, `url`, `content` (page text), `refs` (element references like @e5), `elements` (list of element dicts with ref, tag, text, attributes)). The snapshot can be saved as JSON via write_file for offline inspection. This structure is consistent across all browser tools (browser_navigate, browser_click, etc.).
§
browser_snapshot (full mode) can reveal content hidden in tab panels, accordions, or collapsed sections that aren't visible in the initial browser_navigate snapshot. Workflow: navigate → if main content is missing → browser_scroll → browser_snapshot again. This is common on university program pages (e.g., guide.wisc.edu uses tab panels for Overview/Requirements/Outcomes).
§
subprocess_worker.py (Kanban worker) does NOT register meeting tools (register_meeting_tools is missing). This means Kanban workers cannot use meeting_moderator tools (meeting_create_participants, meeting_set_agenda, meeting_ask_one, meeting_chain, meeting_group_discuss, meeting_add_notes, meeting_conclude). If a Kanban task needs to run a meeting, the subprocess_worker.py must be updated to include register_meeting_tools in its tool registration. Alternatively, the main agent should call meeting tools directly instead of dispatching to Kanban.
§
oa-generation skill 的 Step 5 最终审查必须包含"审查→发现缺陷→修改→再确认"的闭环流程，而非一次性的"审查→给结论"。主 agent 在审查会议中承担双重角色：会议主持人（调用 meeting 工具）和执行者（write_file/patch_file 修改文件）。这个闭环流程已写入 oa-generation skill 的 Step 5。
§
skill_manage 的 name 校验 bug 已修复：VALID_NAME_RE 正则从 r"^[a-z0-9][a-z0-9._-]*$" 改为 r"^[a-z0-9][a-z0-9./._-]*$"，增加了斜杠 / 支持。根因是正则不允许 category/name 格式（如 hr-recruitment/oa-generation），而所有 skill 的 name 都天然包含斜杠。修复后 skill_manage 的 create/edit/patch/write_file/remove_file 均可正常处理带斜杠的 name。
§
## 核心身份定位：High-Level 调度 Agent

我不是 worker，我是与用户对话的智能体代理。我的职责是：
1. **High-level 调度** — 发起任务（Kanban pipeline、meeting）、编排依赖关系、订阅完成通知
2. **汇报结果** — 任务完成后向用户汇总，而不是亲自执行具体工作
3. **不要空等** — 任务发起后，立即 set timer（kanban_notify_subscribe）并 respond_to_user，不要反复 poll 状态或等待 worker 完成
4. **不要亲自下场** — 除非任务需要我直接修改文件（如审查闭环中的 write_file/patch_file），否则应通过 Kanban dispatch 派发给 worker 执行
§
Skill 'hr-recruitment/oa-generation' was not found when a Kanban worker tried to load it for task '生成 SCORING.md'. The skill may need to be created or the skill name may be incorrect.
§
Skill 'hr-recruitment/oa-generation' was not found when a Kanban worker tried to load it for task '生成 SCORING.md' on board oa-generation-TianzeXia-v2. The worker proceeded autonomously using the task prompt and existing OA design files (design_conclusion.md, README.md, DELIVERABLES.md). The skill may need to be created or the skill name may be incorrect.
§
Skill 'hr-recruitment/oa-generation' was not found when a Kanban worker tried to load it for task '生成 scaffold/ 代码框架'. The worker proceeded autonomously using the task prompt and design_conclusion.md as guidance.
§
OA题目方案「跨境合规情报融合引擎」已设计完成，保存在 reports/OA题目方案_Agent架构师视角.md。核心设计思路：让候选人设计一个 Agent Pipeline 来控制 LLM 的三大缺陷（幻觉、格式漂移、信息冲突），而非写算法或调 Prompt。输入包含 5 种异构源 + 9 种噪声类型，输出有明确的 JSON schema 要求，40% 分值压在 Pipeline 设计直觉上。
§
## Ctrl-Agent Paper Idea (2026-07-01)

**Core idea**: Bridge Ctrl-R (structured reasoning trajectory control, NeurIPS 2026 Spotlight) with Lumos-style agent tool-use (planning→grounding→execution). 

**Key insight**: No existing work uses structured trajectory control (backtracking, backward chaining, counterfactual exploration, importance-sampled RL) to improve agent planning/grounding/execution in multi-tool environments.

**5 agentic reasoning patterns**: Backtracking, Backward Chaining, Induction, Counterfactual, Recovery.

**Technical approach**: Trajectory Controller (orchestrator) + Agentic GRPO (tool-call rewards) + Magnet-inspired seed data + Self-evolving exploration strategy.

**Jingyu's strengths map**: Multi-agent orchestration → Trajectory Controller; Context management → structured trajectory state graph; RL post-training (GRPO) → Agentic GRPO; Guardian-Worker → Controller-Worker architecture.

**Target venue**: NeurIPS 2027 or ICLR 2027 (methods paper). ACL 2027 as alternative (NLP/agent framing).

**Full report**: reports/novel_paper_idea_ctrlR_agent_tool_use.md
§
## Lesson: High-level agent 行为红线 (2026-06-30)

用户明确禁止的两类行为：
1. **Worker 出错时不要自行补救** — 如果 worker 报错或输出不符合预期，直接向用户报告错误，不要自己动手写文件来"补上"。我是调度 agent，不是 worker。
2. **不要反复读 worker 内部 session 缓存文件** — 不要用 read_file 读 kanban workers/ 下的 JSON 缓存来轮询状态。正确做法：kanban_show_task 检查状态 + kanban_notify_subscribe 订阅 pipeline_complete 事件 + respond_to_user 结束本轮，等通知触发。

关联 skill: utilities/context-management 应该补充这个行为准则。
§
§
用户需要的是 HTML 格式的单元音课件（可直接在浏览器打开和学生一起看），不是 Markdown。当前 pipeline 正在生成 Markdown 版本，完成后需要将其转换为 HTML。
§
OA 题目输入数据量要求：10w+ 字（不是 2w），用于 7.2-HJY 的 OA 设计。
