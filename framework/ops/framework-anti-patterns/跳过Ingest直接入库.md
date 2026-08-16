---
tags: [反模式, 流程违规, Ingest]
scope: framework
confidence: high
scene: [文档导入, auto-import]
created: 2026-07-22
summary: 反模式——跳过 Ingest 流程直接写入知识库，破坏规则一致性
---

# 跳过 Ingest 直接入库

## 问题

`auto-import.py` 转换完成后，直接把 `.inbox/converted/` 中的 .md `cp` 进 `knowledge/`，跳过 Ingest 流程的必备步骤：

- YAML frontmatter 补全
- `check-frontmatter.py` 校验
- git commit + log 记录
- 变更摘要输出

## Why

LLM 默认行为把"文件搬到位"当终点，Ingest 作为独立仪式感步骤容易被忽略。

## How to apply

`auto-import.py` 执行完成后自动提示：「转换完成。下一步：/ingest 入库」，而非直接搬运文件。
