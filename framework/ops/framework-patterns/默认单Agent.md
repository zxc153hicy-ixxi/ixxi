---
tags: [反模式]
type: permanent
status: active
confidence: high
summary: 设计/实现时默认只考虑一个 Agent（如 Claude），忽略框架「多 Agent 平等」核心原则，导致适配层/入口只覆盖单 Agent
created: 2026-08-15
---

# 默认单 Agent

## 发生了什么

在设计「适配层产物目录」「加载入口」等机制时，只盯着 Claude 的 `.claude/skills/`，忽略了 Codex 的 `.agents/skills/`、Hermes 的直读机制。结果：

1. sync 脚本把适配层生成到 `framework/.claude/`，而 Claude Code 实际扫的是仓库根 `.claude/`——单 Agent 视角导致目录错位，clone 后冷启动读不到任何 skill
2. 讨论方案时反复说「改 Claude 的仓库」，被纠正「你默认了 Claude，我只是举例，还有 Codex、Hermes」

## 根因

ixxi 的命根子是「多 Agent 平等」（Claude/Codex/Hermes 一等公民），但设计/实现时大脑默认了「Claude 是默认 Agent」，把「多 Agent」当成了「Claude + 其他」，导致机制只覆盖单 Agent、目录只按 Claude 的发现机制设计。

## 纠正

- 涉及「适配层 / 加载入口 / 发现机制」时，先列三个 Agent（Claude/Codex/Hermes）各自的原生发现方式，逐一对齐，禁止只写 Claude 一个
- 说「改 X 的仓库」前，先问「三个 Agent 都要吗？Codex/Hermes 呢？」
- 用 parity（P2 Claude / P3 Codex / P4 Hermes）当机器检查，任何一端不通即暴露单 Agent 视角

## 关联

- [[多套版本号并存]] —— 同类根因：把「单一」误当成「默认」，丢了其它维度
