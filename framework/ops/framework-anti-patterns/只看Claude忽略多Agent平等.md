---
tags: [反模式, 多Agent, 适配]
scene: [多Agent适配, 能力迁移]
status: active
scope: framework
summary: 讨论 ixxi 能力/skill 适配时只考虑 Claude，忽略三 Agent 平等原则，用户纠正「你不能只看 claude」
created: 2026-08-15
updated: 2026-08-15
sources: [会话-2026-08-15]
---

# 只看 Claude 忽略多 Agent 平等

## 反模式
涉及 ixxi 能力/skill/适配时，惯性以 Claude 为中心，只考虑 Claude 的适配层，忽略 Codex/Hermes。

## 真实案例（本会话）
迁移方案讨论 personal skill 路径时，我只说「Claude 不会自动发现，需要 sync 平铺」。用户纠正「你不能只看 claude」。

## 后果
- 方案只覆盖 Claude，Codex/Hermes 的适配被遗漏
- 违背 ixxi 核心不变量 I1「能力层 Agent 无关」，把「Claude 的入口语法」当成了「能力本身」

## 正确做法
- 用三层分离框架：能力层（Agent 无关）→ 适配层（各 agent 原生语法），三 agent 同时考虑
- 表述 skill/能力/适配时，Claude/Codex/Hermes 三者并列，不默认单一 agent
