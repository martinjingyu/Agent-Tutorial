# Kanban Workflow Communication Guide

## 背景

当用户看到 agent 连续调用 `kanban_list_tasks` 然后 `kanban_dispatch` 时，可能会问"为什么执行了两个工具调用？"或"为什么先 list 再 dispatch？"

## 核心解释模板

这两个工具的角色完全不同：

| 工具 | 角色 | 副作用 |
|------|------|--------|
| `kanban_list_tasks` | **只读检查** — 返回当前 board 的快照（哪些 done、哪些 ready、哪些 running） | 无 |
| `kanban_dispatch` | **调度执行** — 检查所有 `status: ready` 且 `parents` 都已 done 的任务，启动它们 | 有（spawn 子进程） |

## 标准回答模板

> **`kanban_list_tasks` 只是查看状态**，它不会触发任何任务执行。它返回的是当前 board 的快照，告诉你哪些任务 done、哪些 ready、哪些 running。
>
> **`kanban_dispatch` 才是真正调度任务的工具**。它的作用是：
> 1. 检查所有 `status: ready` 且 `parents` 都已 done 的任务
> 2. 启动这些任务（spawn worker 进程）
> 3. 返回哪些任务被启动了
>
> 所以流程是：先 list 看状态 → 发现 ready 任务 → dispatch 启动它们。

## 用户问"完成了几个"时的标准流程

```
用户: 现在完成了几个了？
agent:
  1. kanban_list_tasks  → 查看当前 board 状态
  2. 如果发现 ready 任务 → kanban_dispatch 启动它们
  3. 向用户报告：已完成 X 个，Y 个正在运行，Z 个待启动
```

### 进阶：有 running 任务时的深度检查

当 board 中有 running 任务且用户追问进度时，可以进一步检查 running 任务的状态：

```
用户: 继续看看
agent:
  1. kanban_list_tasks  → 查看当前 board 状态
  2. 如果结果过大被截断 → read_file 读取缓存文件
  3. kanban_show_task(task_id)  → 查看 running 任务的具体进度
  4. 如果发现新的 ready 任务 → kanban_dispatch 启动它们
  5. 向用户报告：已完成 X 个，Y 个正在运行（含进度摘要），Z 个待启动
```

注意：`kanban_list_tasks` 结果可能因内容过大被自动保存到 `.tool_cache/`，此时需要用 `read_file` 读取缓存文件获取完整结果。

## 注意事项

- 不要在一次回答中同时调用 `kanban_list_tasks` 和 `kanban_dispatch` 而不解释原因 — 用户会困惑
- 如果用户只问状态（"完成了几个"），先 list 看状态，然后解释"还有 X 个 ready 任务，我 dispatch 启动它们"
- 如果 board 上没有 ready 任务（所有任务要么 done 要么 running），则不需要 dispatch，直接报告状态即可
