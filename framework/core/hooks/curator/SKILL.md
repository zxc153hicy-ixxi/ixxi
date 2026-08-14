---
name: kb-hook-curator
description: Use when managing hook lifecycle or when hooks are added/removed/updated. Triggers on "hook" "钩子" "curator".
---

# kb-hook-curator

## Overview
钩子管家：管理所有自动化钩子的注册、触发、跟踪和归档。

## Quick Reference

### 当前钩子（8个，纯机械操作）

| 钩子 | 类型 | 挂载点 | 做什么 |
|------|:---:|------|------|
| stage-check | 🔄 自动 | Stop | 阶段自动检测 |
| version-check | 🛑 拦停 | pre-commit | 版本不一致就拦 |
| deprecate-move | 🛑 拦停 | Edit 后 | 废弃文件提示搬家 |
| pattern-registration-check | 🔄 自动 | Edit/Write 后 | 正反模式文件检查登记 |
| script-registration-check | 🔄 自动 | Edit/Write 后 | 脚本文件检查登记 activation |
| rule-registration-check | 🔄 自动 | Edit/Write 后 | 规则文件检查登记 index |
| session-metadata-check | 🔄 自动 | Edit/Write 后 | session 文件检查 YAML 字段 |
| pre-commit | 🛑 拦停 | pre-commit | G层修改验证 tag+log |

> 计数器更新仍由 LLM 手动执行——钩子无法判断当前是什么操作，属于语义判断范畴。

### 生命周期
- 检测：当前钩子均为手工创建，后续通过 curator 检测重复操作→建议加钩子
- 跟踪：registry.json 记录每个钩子的触发次数
- 归档：钩子对应的操作已有 skill 覆盖或脚本不再存在→标记 deprecated

### 硬闸门
- 钩子可执行文件必须经过测试，不能阻断正常操作流程
- 拦停型钩子失败时给出明确文字提示，不输出堆栈

## 降级
SKILL 加载失败时，直接读取：`core/hooks/registry.json` + 各脚本源码
