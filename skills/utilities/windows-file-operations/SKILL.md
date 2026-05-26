---
name: windows-file-operations
category: utilities
description: Windows 环境下文件读写、路径操作的最佳实践。涵盖 read_file 优先原则、文件移动/复制、编码处理等常见场景。
---

# Windows 文件操作最佳实践

## 核心原则

在 Windows 环境下，**优先使用 `read_file` 工具读取文件内容**，而不是通过 `terminal` 启动子进程（PowerShell/cmd）来读取。

## 文件读取优先级

| 优先级 | 方法 | 适用场景 | 可靠性 |
|:-----:|------|---------|:------:|
| 1 | `read_file` | 所有文本文件（.txt/.md/.json/.py/.docx 等） | ✅ 最高 |
| 2 | `terminal` + `cmd /c type` | 仅当 `read_file` 不可用且只需简单查看 | ⚠️ 中 |
| 3 | `terminal` + PowerShell | **避免使用** — 管道 UTF-8 输出会导致 `TypeError` | ❌ 低 |

## 详细说明

### 1. read_file（首选）

```python
# ✅ 推荐 — 直接 Python 文件 I/O，原生支持 UTF-8
read_file(path="reports/某学校/某专业.md")
read_file(path="candidates/1/stage1_profile.json")
read_file(path="C:/Users/.../某文件.docx")  # 也支持 .docx！
```

**优势**：
- 不经过 shell 管道，无编码问题
- 原生支持 UTF-8 中文
- 原生支持 .docx 格式
- 支持绝对路径和相对路径

### 2. terminal + cmd /c type（备选）

```python
# ⚠️ 备选 — 仅当 read_file 不可用时
terminal(command='cmd /c "type C:\\path\\to\\file.txt"')
```

**限制**：
- cmd 的 `type` 命令输出 GBK 编码，中文可能乱码
- 管道读取可能失败返回 `None`
- 仅适合快速查看文件是否存在或行数

### 3. terminal + PowerShell（避免使用）

```python
# ❌ 避免 — 已知问题
terminal(command='powershell -Command "Get-Content file.txt -Encoding UTF8"')
```

**已知问题**：
- PowerShell 输出 UTF-8 文本时，管道读取会返回 `None`
- 触发 `TypeError: 'NoneType' object is not subscriptable`
- 即使加 `-NoProfile`、`chcp 65001` 也无法解决

## 常见场景对照

| 你想做什么 | 正确做法 |
|-----------|---------|
| 读取 JSON 配置文件 | `read_file(path="...json")` |
| 读取 docx 职位描述 | `read_file(path="...docx")` |
| 读取 skill 的 SKILL.md | `read_file(path="skills/.../SKILL.md")` 或 `skill_view(name="...")` |
| 查看文件是否存在 | `list_files(path="...")` 或 `read_file`（失败即不存在） |
| 搜索文件中的关键词 | `search_files(query="...", path="...")` |
| 查看文件行数/大小 | `read_file` 然后数行数，或用 `terminal` + `cmd /c findstr /N` |
| 执行 git 命令 | `terminal(command="git status")` — 这是 terminal 的正确用途 |
| 移动文件（Windows） | `terminal(command='cmd /c move "src" "dst"')` — 用 cmd move，不用 shutil.move |
| 复制文件（Windows） | `terminal(command='cmd /c copy "src" "dst"')` — 用 cmd copy |

## 为什么 terminal 读取文件不可靠

Windows 上 terminal 工具的实现流程：

```
Python subprocess.run() → 启动 cmd.exe/PowerShell → 执行命令
→ stdout 通过管道传回 Python → 工具代码解析 stdout
```

问题出在最后两步：
1. **PowerShell 的 `-Encoding UTF8` 输出带 BOM 的 UTF-16**，与 Python 管道不兼容
2. **管道缓冲区满或编码不匹配时，`result.stdout` 返回 `None`**
3. **工具代码未处理 `None` 情况**，直接下标访问 → `TypeError`

`read_file` 则直接调用 Python 的 `open()`，完全绕过了 shell 管道。

## 记忆要点

> **在 Windows 上，`read_file` 是读文件的唯一可靠方式。`terminal` 只用来执行命令（git、copy、move 等），不要用它读文件内容。**

## References

- `references/file-reading-priority.md` — 详细对照表
