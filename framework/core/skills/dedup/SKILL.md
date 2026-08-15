---
name: kb-dedup
description: Use when executing /dedup or the user says "去重" "重复" "查重".
---

# kb-dedup

## Overview
帮你找出知识库里内容差不多的重复页面，告诉你怎么合并，省得同一件事记了好几遍。
技术说明：扫描 framework/ops/ 全页面 → 计算内容相似度 → 输出《重复内容报告》。

## Quick Reference
- 比对范围：framework/ops/ 全部 .md 文件
- 高相似度 → 自动建议合并路径 + log
- 中相似度 → 标注等确认
- 低相似度 → 不告警

## 输出
- 重复内容报告（含合并建议）

## 降级
SKILL 加载失败时，直接读取 Lint #14 定义（`framework/ops/rules/Lint检查流程.md` + `framework/ops/rules/核心操作流程.md`）
