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
Windows terminal + PowerShell 读取中文 UTF-8 文件时，管道 stdout 返回 None，触发 TypeError: 'NoneType' object is not subscriptable。解决方案：始终用 read_file 读取文件内容，terminal 只用于执行命令（git、copy、move 等）。已创建 utilities/windows-file-operations skill 记录此最佳实践，所有涉及文件读取的 skill 都应引用它。
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
[Needs re-verification] subprocess_worker.py (Kanban worker) may not register meeting tools (register_meeting_tools). If confirmed still true, Kanban workers cannot use meeting_moderator tools (meeting_create_participants, meeting_set_agenda, meeting_ask_one, meeting_chain, meeting_group_discuss, meeting_add_notes, meeting_conclude) — the main agent should call meeting tools directly instead of dispatching to Kanban for meeting-dependent tasks.
