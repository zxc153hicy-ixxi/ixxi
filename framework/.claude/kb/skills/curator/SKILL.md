---
name: kb-curator
description: Use when /lint detects skill-ification candidates or the user says "技能化" "封装" "curator" "管家".
---

# kb-curator

## Overview
知识库的"管家"：看哪些活干得多了就自动帮你建个工具、工具用旧了就提醒你清理、新工具刚建好会主动提醒你试用。
技术说明：检测重复操作 → 按置信度加载 skill → 生命周期跟踪 → 归档退役。

## Quick Reference

### 置信度加载
| 置信度 | 条件 | 行为 |
|------|------|------|
| 高 | 精确 `/命令` + `skill_accepted=true` | 静默加载，一行说明 |
| 中 | 关键词匹配 或 `skill_accepted=null`（首次） | 提示确认：「你是不是想...我这边有个专门干这个的工具，要试试吗？」 |
| 低 | 模糊匹配 / 多候选 | 列清单：「这个说法可能指好几件事...你想要哪个？」 |

**接受跟踪**：用户确认加载 → 写入 `skill_accepted: true` + `skill_first_offered`。拒绝 → `skill_accepted: false`。下次同操作检测到 `true` → 走高置信度静默。

### 计数器自动更新
每次执行可封装操作后，自动更新 `raw/sessions/skill-usage.json`：
- `count++`
- `last_seen` = 今天
- `first_seen` = 今天（如果为 null）
- 非破坏性操作，无需用户确认

### 多推荐
命中一个 skill 时附带 1-2 个关联推荐：
- ingest → lint（体检）· audit（查漏）
- lint → audit · health
- audit → lint · ingest
- session-close → ingest · verify
- conflict → promote · compact
- compact → promote · lint

### 自适应阈值

| 阶段 | 条件 | 窗口 | 频次 | 归档 |
|------|------|------|------|------|
| 刚起步 | skill < 4 或 wiki < 80 | 7 天 | ≥2 次 | >90 天 |
| 在用了 | skill 4-8 或 wiki 80-150 | 30 天 | ≥3 次 | >90 天 |
| 用熟了 | skill > 8 且 wiki > 150 | 90 天 | ≥5 次 | >90 天 |

### 生成流程
1. `/lint` 输出《技能化候选清单》
2. 用户确认「封装 <操作名>」
3. LLM 读取对应规则文件 → 生成 SKILL.md（~200词）
4. 写入 `.claude/kb/skills/<操作名>/SKILL.md`（权威源）
5. 更新 CLAUDE.md T 层路由
6. 计数器追加 `skill_active: true`

### 归档流程
- 触发：超期未使用 或 原规则文件已更新
- 动作：移至 `.claude/skills/_archived/`，路由自动回退规则文件
- 回退保护：归档导致 skill 数骤降 → 自动回落冷启动参数

### Skill 调度
技能调度已收敛为跨 agent 单一事实源：见 [[ops/rules/skill调度注册表]]。curator 不再维护 skill 映射表——内部 kb-* 按注册表表 A 调度，外部 skill 由各 Agent 原生 skill 列表路由。

## 硬闸门
- skill 生成必须用户确认（G12）
- 原规则文件保留不动，skill 仅作执行入口
- 归档前提示用户，不自动删除

## 可封装操作
ingest / lint / audit / compact / conflict / session-close / dedup / health / promote / refresh
（stats / verify 已归档——纯机械操作用脚本更可靠）

## 降级
SKILL 加载失败时，直接读取：`ops/rules/技能化流程.md`
