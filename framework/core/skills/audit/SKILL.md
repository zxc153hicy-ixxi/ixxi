---
name: kb-audit
description: Use when executing /audit or when the user says "audit" "审计" "回溯" "遗漏" "查漏".
---

# kb-audit

## Overview
翻一遍你的文件夹，看看有没有聊天记录还没整理成知识页面，有的话帮你标记出来，按紧急程度分好类。
技术说明：全量扫描 personal/data/ → 对照 personal/data/queue.md → 发现未入队文件 → 按置信度分级处理。

## Quick Reference

| # | 扫描范围 | 对照依据 | 分级处理 |
|:---:|------|------|------|
| 1 | personal/data/sessions/*.md | personal/data/queue.md | 高→自动标记[x] / 中→自动入队[ ] / 低→仅列出 |
| 2 | personal/data/feedback/*/*.md | personal/data/queue.md | 已写入知识库→高 / 新建→中 |
| 3 | framework/ops/rules/*.md | T层路由表 | 未关联→低 |
| 4 | framework/ops/子目录 | framework/activation.md | 状态不一致→低 |

## 输出
- 审计报告：`personal/knowledge/archive/知识库管理/queries/audit-report-YYYY-MM-DD.md`
- `/audit --dry-run`：仅输出遗漏清单，不修改文件

## 硬闸门
- 新机制上线 → 必须跑一次存量回溯（禁止只管增量）
- T层例外清单修改 → 走 G 层修改流程

## 降级
SKILL 加载失败时，直接读取：`framework/ops/rules/全量审计流程.md`
