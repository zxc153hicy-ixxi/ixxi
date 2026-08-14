---
name: kb-ingest
description: Use when executing /ingest or when the user says "ingest" "入库" "提炼" "整理" "收录".
---

# kb-ingest

## Overview
把聊天记录里的知识点自动整理成 wiki 页面，9 步一条龙搞定。
技术说明：将 raw/ 原始资料提炼为 ops/ 结构化知识，严格按 0→8 步顺序执行。

## Quick Reference

| 步骤 | 名称 | 操作 | 失败处理 |
|:---:|------|------|------|
| 0 | 预检 | 扫描 queue+.inbox/converted/+raw/inbox/ → 敏感扫描 → Lint 过期检查 | 失效标记[!]跳过 |
| 1 | 读取 | 逐条读 raw，提取核心主张 | — |
| 1.5 | 本地解析 | raw/local/→拆分→写入 sessions/ | 移至 _failed/ |
| 2 | 冲突+去重 | 按 scene+type 分桶比对 | 高暂停/中继续+标注/低不告警 |
| 3 | 写入 | 按 confidence→status 新建页 | 重试一次 |
| 3.5 | 对话确认 | medium/low 逐条展示确认 | 确认→active / 跳过→draft |
| 4 | 交叉引用 | active 页面建立双向链接 | — |
| 5 | 校验 | YAML + scene 一致性 | 格式错误自动修复 |
| 6 | 更新索引 | index.md 追加条目 | 冲突→临时文件 |
| 7 | 提交 | queue[x]→log→git commit | git 失败→人工介入 |
| 8 | 变更摘要 | 固定格式输出 | — |

## 硬闸门
- 步骤 3.5：medium/low 置信度内容必须人类确认，禁止自动激活
- 步骤 7：每次 Ingest 必须 git commit
- 批量模式（>30 天未 Ingest）：每批 ≤10 条，标注 `[批量模式: 第N批/共M批]`

## 降级
SKILL 加载失败时，直接读取：`ops/rules/Ingest完整流程.md`
