from __future__ import annotations

COMPACT_MODE_PROMPT = """上下文压缩模式：
你偶尔会在对话末尾收到一条 <runtime_control mode="compact"> 指令。收到时，严格按照它执行，
并用要求的 checkpoint 内容调用 compact_checkpoint 工具。除此之外任何时候都不要调用
compact_checkpoint——在压缩模式之外调用没有任何效果。该指令本身会携带完整的规则和输出格式要求。
"""
