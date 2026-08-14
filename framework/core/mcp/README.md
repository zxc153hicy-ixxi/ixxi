# core/mcp/

MCP（Model Context Protocol）能力源——外部工具（数据库、API、文件系统等）通过 MCP 协议接入。

> **预留位**：当前无应用场景，schema 和注册表机制已就绪，具体 MCP server 待未来接入。

## 本目录内容

- `schema.md` —— MCP server 定义格式 + 接入方式 + 自动调用机制
- 本 README —— 定位与预留说明
- （注册表在 `ops/rules/mcp注册表.md`，与 skill 注册表并列，属路由层）

## 为什么是「预留」不是「实现」

设计文档决策 3：MCP 缓建（当时无场景）。但「缓建」应保留扩展位，未来有场景时照 schema 直接接入，不用从头设计。

## 自动调用

MCP 与 skill 共用同一套调度（G17 + 注册表 + 置信度），见 schema.md。MCP 属「外部工具」，优先级最高（原设计「外部优先→适配补位→内部兜底」）。
