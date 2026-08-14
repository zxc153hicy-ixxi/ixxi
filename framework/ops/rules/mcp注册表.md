---
tags: [注册表, mcp, 调度]
status: active
summary: MCP 调度注册表——任务 → 匹配 MCP server → 调用，与 skill 注册表并列（预留，当前无数据）
created: 2026-08-15
---

# MCP 调度注册表

> **路由层单一事实源**（预留）：给定任务 → 匹配 MCP server → 调用。与 [[skill调度注册表]] 并列。
> **机制**（本表结构 + 置信度规则）归 framework；**数据**（具体 MCP server）归 personal 实例，未来有场景时登记。
> **置信度**：高 = 关键词命中即静默调用；中 = 命中需提示确认；低 = 模糊匹配列清单。

## 表 · MCP server（预留，当前无数据）

| name | 连接方式 | 提供的工具 | 触发场景 | 关键词 | 置信度 |
|---|---|---|---|---|---|
| （实例自填） | stdio/sse/http | （自填） | （自填） | （自填） | 高/中/低 |

## 接入流程（未来有场景时）

1. 在 personal 实例配置 MCP server（连接方式 + 工具）
2. 本表登记一行（name + 触发场景 + 关键词 + 置信度）
3. sync 生成各 agent 的 MCP 配置（适配层）

## 关联

- [[core/mcp/schema]] —— MCP server 定义格式
- [[skill调度注册表]] —— 同构的 skill 调度（共用 G17 + 置信度机制）
