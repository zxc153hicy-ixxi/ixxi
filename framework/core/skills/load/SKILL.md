---
name: kb-load
description: Use when the user says "加载 ixxi" "加载框架" "开始用 ixxi" "load ixxi".
---

# kb-load

## Overview
把 ixxi 框架加载进来，让你进入「ixxi 模式」：知道 ixxi 是什么、能干嘛、怎么用。首次加载会弹一段新手引导，之后不再重复。
技术说明：定位 ixxi（IXXI_HOME/当前目录）→ 检查适配层（未 init 先引导 init）→ 读 AGENT.md 契约 → 读实例导航/画像/操作菜单/正反索引（G8 启动加载）→ 检查 onboarding.json → 读未落地清单（若存在）→ 查 queue/清 session-notes → 汇报。

## Quick Reference

### 加载流程

| 步骤 | 动作 |
|:---:|------|
| 1 | 定位 ixxi：读环境变量 `IXXI_HOME`；未设置则假设当前目录是 ixxi 仓库（含 `framework/`） |
| 2 | 检查适配层：`framework/.claude/skills/` 或仓库根 `.claude/skills/` 有 kb-* 吗？没有 → 引导「先运行 `bash ixxi init`」 |
| 3 | 读 `framework/AGENT.md`，加载行为契约（G/T/R 三层规则） |
| 4 | 读实例导航 `personal/index.md` + 场景注册表 `personal/data/scene-registry.md` + 覆盖层 `personal/CLAUDE.md`（G6 语言边界 / G16 知识优先 / G16.5 强制路由） |
| 5 | 读用户画像 `personal/data/用户画像.md`（空则跳过），注入画像摘要（输出偏好/沟通风格/决策模式） |
| 6 | 读操作菜单 `framework/ops/rules/系统操作菜单.md`（意图→指令映射） |
| 7 | 读 4 个正反模式索引（`framework/ops/framework-patterns/正模式索引.md`、`framework/ops/framework-anti-patterns/反模式索引.md`、`personal/system/patterns/正模式索引.md`、`personal/system/anti-patterns/反模式索引.md`）——只读索引，命中场景时再读正文 |
| 8 | 读 `core/onboarding.json`：`first_load.fired = false` → 展示引导提示 → 标记 `fired = true` |
| 9 | 读未落地清单（`personal/knowledge/projects/知识库管理/未落地清单.md`，维护者实例才有；无则跳过），统计待办 N 项（待环境/待真实使用/后置/约定）；对带「触发条件」信号的项，检测信号是否满足（`github_remote` → `git remote -v` 含 github.com） |
| 10 | 查 `personal/data/queue.md` 待处理项；清空 `personal/data/session-notes.md` |
| 11 | 汇报当前状态（见下方格式，含版本/能力/画像/正反索引/待办 + 现在可做） |

### 汇报格式

```
✅ 已加载 ixxi v{版本}
   能力：{N} 个（管理 {管理数} + 外部 {外部数}，实测 core/skills）
   画像：已注入 / 无（空则跳过）
   正反模式：索引 {正} 正 {反} 反 已加载（命中时再读正文）
   待办：{N} 项（待环境 {X} / 待真实使用 {Y} / 后置 {Z} / 约定 {W}）——仅维护者实例有未落地清单时输出
   ⚡ 现在可做 {M} 项（触发条件满足）：{列出满足的项}    ← 仅当有满足时才输出这行
   下一步：把资料放进 personal/data/inbox/ 说「入库」，或说「体检」看健康度
```

## 硬闸门

- 首次加载（`first_load.fired = false`）必须展示 onboarding 引导，禁止跳过
- 汇报的版本号、能力数必须实测（读 CHANGELOG 最新版本 + 数 core/skills），禁止凭记忆

## 降级

SKILL 加载失败时，直接读取：`framework/AGENT.md` + `README.md`
