---
tags: [反模式]
status: active
scope: framework
summary: Workflow处理enrich任务——31 agent/70万token只分析了30文件无任何写入
created: 2026-07-21
updated: 2026-07-21
---

# Workflow 低效浪费

## 触发场景

用 Workflow 多 agent 并行处理需要"读取→分析→写入"的任务时，agent 只返回分析结果不执行写入，导致大量 token 消耗无产出。

## 典型案例

`enrich-knowledge-base` workflow：31 个 agent 并行分析 30 篇安全文章，每个 agent 正确读取内容并返回 JSON（tags/summary），但**没有任何文件被实际修改**。消耗 70 万 token，产出为 0。

失败原因：agent 被设计为"分析并返回结果"，但没有在 pipeline 中执行写入步骤。

## 根因

- Workflow 适合纯分析/审查任务，不适合需要修改文件的读写混合任务
- agent 返回结构化数据没问题，但写回文件的步骤缺失
- 批量小文件修改的最优方式不是 Workflow fan-out，而是单 agent 串行快过 agent 启动开销

## 预防

1. 批量文件修改（读→分析→写回）：**LLM 自己串行处理**，不用 Workflow
2. Workflow 专用于：纯分析、审查、验证、对账——不需要写回文件的任务
3. 如果非要用 Workflow 写文件，pipeline 必须包含独立的写入 stage

## 关联
- [[不安全操作无保护]] —— 批量操作的另一类风险
