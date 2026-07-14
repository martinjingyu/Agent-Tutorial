from __future__ import annotations

SELF_REVIEW_PROMPT = """回顾刚完成的这段对话。

你只能使用 memory、skill 和 self-code 相关工具。

只保存真正能长期沉淀的改进：
- 用户偏好、稳定的 workspace 事实，以及跨任务的通用工具行为，属于 memory。
- 可复用的工作流、checklist、模板，或某类任务的源码模式，属于 skill。
- 当对话暴露出这个 agent 自身实现中一个具体、可复用的 bug 或行为缺口时，对应的narrow修复属于 self-code。
- 不要保存一次性的任务事实、临时的调研发现、会过时的时事类事实，或短暂的环境搭建失败记录。

决策顺序：
1. 当对话暴露出一个具体的 agent bug、缺失的防护机制，或应该在未来运行中改变的实现行为时，patch self-code。
2. 当经验教训适合某个已使用过的 skill 时，更新那个 skill。
3. 否则，如果有合适的现有 umbrella skill，更新它。
4. 只有在没有任何合适的、class 级别的现有 skill 时，才创建新 skill。

Self-code 规则：
- 在 self_code_patch 之前先用 self_code_search 和 self_code_read。
- patch 保持最小化，只限于 research_agent/ 核心源码文件。
- self-review 期间不要重写大范围架构、不要修改 provider 凭据，也不要 patch 无关的行为。

格式规则：
- 对 SKILL.md 的小改动优先用 patch。
- 详细示例、素材列表、checklist 放在 references/ 里。
- 可复用的输出格式放在 templates/ 里。
- 可重复执行的命令或探测脚本放在 scripts/ 里。
- Skill 名称必须是 class 级别、可复用的，不能是一次性的项目名、URL、日期，或 bug 标题。
- Skill frontmatter 必须包含 audience 字段，选择满足需要的最窄角色集合：main、sub_agent、self_review，或 all。

如果没有值得长期保存的内容，就准确地回答：Nothing to save.
"""
