---
tags: [schema, mcp]
status: active
summary: MCP server 定义 schema——字段 + 接入方式 + 自动调用机制。机制归 framework，具体 server 配置归 personal。
---

# MCP server schema

> 机制（本文件）归 framework，具体 MCP server 数据归 personal 实例。未来有应用场景时，照此 schema 接入。

## 定位

MCP（Model Context Protocol）是「能力层」的一种，和 skill 平行：

| | 是什么 | 怎么用 |
|---|---|---|
| skill | 流程/指令（SKILL.md） | LLM 读指令执行流程 |
| MCP | 外部工具（数据库/API/文件系统等） | LLM 通过协议调用工具 |

## 字段定义

| 字段 | 必填 | 说明 |
|------|:---:|------|
| name | ✓ | MCP server 名（如 `db`、`filesystem`） |
| 连接方式 | ✓ | stdio / sse / http |
| 提供的工具 | ✓ | 工具列表（如 `query`、`read`、`write`） |
| 触发场景 | ✓ | 什么任务会用到（如「查数据库」「读外部文件」） |
| 关键词 | ✓ | 匹配关键词（如「数据库、查询、SQL」） |
| 置信度 | ✓ | 高/中/低（衔接 curator 加载行为：高静默/中提示/低列清单） |

## 自动调用

MCP 与 skill 共用同一套调度机制（G17 + 注册表 + 置信度）：

```
任务 → 查注册表 → 置信度决策（高静默/中提示/低列清单）→ 调用 MCP
```

区别只是「能力类型」从 skill 换成 MCP，调度器不变。

## 接入方式（未来有场景时）

1. 在 personal 实例配置 MCP server（连接方式 + 工具）
2. 在 `ops/rules/mcp注册表.md` 登记（name + 触发场景 + 关键词 + 置信度）
3. sync 生成各 agent 的 MCP 配置（适配层）
