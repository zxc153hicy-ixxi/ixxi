---
name: kb-load
description: Use when the user says "加载 ixxi" "加载框架" "开始用 ixxi" "load ixxi".
---

# kb-load

## Overview
把 ixxi 框架加载进来，让你进入「ixxi 模式」：知道 ixxi 是什么、能干嘛、怎么用。首次加载会弹一段新手引导，之后不再重复。
技术说明：读 AGENT.md 契约 → 检查 onboarding.json（first_load 首次弹引导）→ 汇报版本/能力/下一步。

## Quick Reference

### 加载流程

| 步骤 | 动作 |
|:---:|------|
| 1 | 读 `framework/AGENT.md`，加载行为契约（G/T/R 三层规则） |
| 2 | 读 `core/onboarding.json`：`first_load.fired = false` → 展示引导提示 → 标记 `fired = true` |
| 3 | 汇报当前状态（见下方格式） |

### 汇报格式

```
✅ 已加载 ixxi v{版本}
   能力：{N} 个（管理 {管理数} + 外部 {外部数}，实测 core/skills）
   下一步：把资料放进 personal/raw/inbox/ 说「入库」，或说「体检」看健康度
```

## 硬闸门

- 首次加载（`first_load.fired = false`）必须展示 onboarding 引导，禁止跳过
- 汇报的版本号、能力数必须实测（读 CHANGELOG 最新版本 + 数 core/skills），禁止凭记忆

## 降级

SKILL 加载失败时，直接读取：`framework/AGENT.md` + `README.md`
