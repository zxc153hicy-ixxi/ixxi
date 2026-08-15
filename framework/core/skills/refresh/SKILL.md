---
name: kb-refresh
description: Use when executing /refresh or the user says "refresh" "刷新" "过时" "更新".
---

# kb-refresh

## Overview
找出放了很久没更新的页面，告诉你哪些内容可能过时了、该翻新一下了。
技术说明：active 页面 updated >90 天 → 与近期新知识比对 → 输出《刷新建议》。

## Quick Reference
| 检测项 | 阈值 | 动作 |
|------|------|------|
| 页面过时 | updated >90 天 | 与近期新规则/知识比对 |
| 规则失效 | 引用指向已归档页面 | 建议更新引用 |
| 标签废弃 | 标签 >90 天零匹配 | 建议废弃标签 |

## 输出
- 《刷新建议》：逐条列出过期页面 + 与新知识的差异

## 降级
直接读取 Lint #12 定义（`framework/ops/rules/核心操作流程.md`）
