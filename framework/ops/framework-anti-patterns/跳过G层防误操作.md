---
tags: [反模式]
summary: 修改 AGENT.md 的 G 层规则时跳过防误操作流程——直接 Edit 绕过，或混淆 G12 跳过词与 G 层硬闸门
created: 2026-06-25
updated: 2026-08-13
sources: [personal/data/feedback/negative/2026-06-25-跳过G层防误操作.md, personal/data/feedback/negative/2026-06-26-G层跳过确认.md]
scene: [知识整理]
type: 反模式
confidence: high
status: active
scope: framework
---

# 跳过G层防误操作流程

## 现象

修改 AGENT.md 的 G 层规则时跳过防误操作流程，两种触发原因：

1. **直接 Edit 绕过**：把 G 层修改当普通文件编辑，直接用 Edit 跳过警告模板、四项确认清单、git tag 备份、log 记录
2. **混淆跳过词**：把 G12 文件修改确认的跳过关键词（直接改/不用问/继续）误当成 G 层硬闸门的跳过词，用户说「继续」就跳过

## 根因

- 把 G 层修改当作普通文件编辑，忽略 AGENT.md 自身规定的防误操作流程
- 混淆 G12 文件修改确认与 G 层修改流程的硬闸门——G 层修改 ≠ 文件修改，G12 的跳过关键词不适用于 G 层流程

## 纠正（已落地）

- G 层修改流程升级为硬闸门：用户确认前禁止执行
- 条款追加：**即使用户直接指令要求修改 G 层，也必须先走完整流程**
- 每次修改后交叉校验 AGENT.md ↔ log.md 一致性

## 发生次数

2 次（均在同一天被用户指出后修正）

## 关联

- framework/ops/rules/知识库运维规范 —— 运维规范（G9检查完整性、G10版本确认）
- [[personal/knowledge/archive/知识库管理/rules/_G层修改警告模板]] —— G 层修改警告模板
