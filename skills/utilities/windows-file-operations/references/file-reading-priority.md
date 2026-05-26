# 文件读取优先级对照表

## 速查表

| 场景 | 正确工具 | 示例 |
|------|---------|------|
| 读 .txt / .md / .json / .py | `read_file` | `read_file(path="file.txt")` |
| 读 .docx | `read_file` | `read_file(path="file.docx")` |
| 读 SKILL.md | `read_file` 或 `skill_view` | `skill_view(name="skill-name")` |
| 搜索文件内容 | `search_files` | `search_files(query="关键词")` |
| 列出目录文件 | `list_files` | `list_files(path=".")` |
| 执行 git 命令 | `terminal` | `terminal(command="git status")` |
| 移动/复制文件 | `terminal` + `cmd /c move/copy` | `terminal(command='cmd /c move "a" "b"')` |
| 读文件（terminal） | ❌ 避免 | PowerShell 管道会崩溃 |

## 已知错误模式

### 错误模式 1：PowerShell 读文件

```python
# ❌ 会崩溃
terminal(command='powershell -Command "Get-Content file.txt -Encoding UTF8"')
# → TypeError: 'NoneType' object is not subscriptable
```

### 错误模式 2：cmd type 读中文文件

```python
# ⚠️ 可能乱码，也可能崩溃
terminal(command='cmd /c "type file.txt"')
# → 中文输出为 GBK，管道可能返回 None
```

### 正确做法

```python
# ✅ 永远用 read_file
read_file(path="file.txt")
```
