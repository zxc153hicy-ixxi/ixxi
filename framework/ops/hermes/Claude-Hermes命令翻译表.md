---
tags: [翻译表, Hermes]
status: active
summary: Claude Code Skill → Hermes 终端命令翻译表，Hermes 加载 Claude skill 时查此表获取对应命令
created: 2026-07-20
updated: 2026-07-20
---

# Claude Code → Hermes 命令翻译表

> Shared: AGENT.md G-layer, ops/rules/, ops/patterns/, ops/anti-patterns/, engine/scripts/, ops/scripts/
> Claude-only: `.claude/kb/skills/`, `.claude/kb/agents/`, `.claude/kb/hooks/`
> Hermes-only: 本翻译表
> 调度依据：[[ops/rules/skill调度注册表]] —— 单一事实源，任务→skill→各 agent 调用方式

## 知识库操作

| Claude Skill | Hermes 终端命令 | 规则文件 |
|------|------|------|
| `/ingest` | Step 0: `python engine/scripts/check-inbox.py --repo . --mode health` → `python engine/scripts/scan-sensitive.py --repo .`；Steps 1-9: LLM 按 `ops/rules/Ingest完整流程.md` 手动执行；新文件导入: `python engine/scripts/auto-import.py <file>` | [[ops/rules/Ingest完整流程]] |
| `/check` | **主入口**。自动化：`python engine/scripts/check_*.py --repo .` 全部脚本 + LLM 判断全维度 | [[ops/rules/知识库检查体系]] |
| `/check --quick` | 仅运行受影响的 check 脚本 | [[ops/rules/知识库检查体系]] |
| `/check --deep` | 自动化全量 + LLM 全量判断（含 R→G 升层候选 /promote） | [[ops/rules/知识库检查体系]] |
| `/compact` | `--mode lines` 检查 AGENT.md 行数→超 180 行触发四维评分精简；`--mode files` 合并碎片化内容 | HERMES.md 行数管控段 |
| `/search` | `--mode full` 全文搜索；`--mode structured` 结构化检索（index→T层路由→规则文件） | — |
| `/conflict` | LLM 按流程执行：检测矛盾 → 输出《反馈冲突提示》 → 暂停等确认 | [[ops/rules/矛盾消解流程]] |
| `/analyze` | 可行性分析，五维加权评分 | — |
| `/export-template` | 生成可分享的知识库骨架 | — |
| 会话收尾 | 回溯会话评价 → G2/G13 反馈收集 → 写入 sessions/ → 检查正反模式 → git commit | [[ops/rules/会话收尾检查]] [[ops/rules/反馈闭环流程]] |

### 已合并到 /check 的操作

| 原指令 | 现访问方式 | 对应检查项 |
|------|------|:---:|
| `/health` | `/check` | H1 系统健康度 |
| `/lint` | `/check` | 原 Lint 18 项 |
| `/dedup` | `/check` | S3 + S6 |
| `/refresh` | `/check` | H2 + H5 |
| `/promote` | `/check --deep` | R→G 升层 |
| `/audit` | `/check` | 全量审计 |
| `/query` | `/search --mode structured` | 结构化检索 |
| `/merge` | `/compact --mode files` | 文件合并 |

## 原子操作

| 操作 | 命令 |
|------|------|
| 创建正模式 | `bash ops/scripts/kb-do.sh create-pattern <名称>` |
| 创建反模式 | `bash ops/scripts/kb-do.sh create-anti-pattern <名称>` |
| 创建规则 | `bash ops/scripts/kb-do.sh create-rule <名称>` |
| 删除文件 | `bash ops/scripts/kb-do.sh delete <路径>` |
| 重命名 | `bash ops/scripts/kb-do.sh rename <旧路径> <新路径>` |
| 查看全部 | `bash ops/scripts/kb-do.sh list` |

## 修复操作

| 操作 | 命令 |
|------|------|
| 清理 .inbox | `bash engine/scripts/fix-inbox-clean.sh --dry-run`（预览）/ `--execute` |
| 修复断链 | `python engine/scripts/fix-broken-links.py --repo .` |
| 同步索引 | `python engine/scripts/fix-index-sync.py --repo .` |
| 修复过期路径 | `python engine/scripts/fix-stale-paths.py --repo .` |
| 清理旧版 | `python engine/scripts/cleanup-versions.py --json`（检查）/ `--execute`（执行） |
| 同步 Agent 文件 | `bash engine/scripts/sync-agent-md.sh`（AGENT.md → CLAUDE.md + HERES.md AUTO） |

## 文件导入

| 操作 | 命令 |
|------|------|
| 单文件导入 | `python engine/scripts/auto-import.py <文件>` |
| 批量导入 | `python engine/scripts/auto-import.py --batch <目录>` |
| 预演 | `python engine/scripts/auto-import.py --dry-run <文件>` |
| 敏感扫描 | `python engine/scripts/scan-sensitive.py --repo .` |

## 加载规则

Claude Code skill（`.claude/kb/skills/<name>/SKILL.md`）被 Hermes 加载时：
1. 读取 SKILL.md 获取步骤和约束
2. 查本表获取对应的 Hermes 终端命令
3. 规则文件（`ops/rules/`）为共享层，直接读取
4. Skill 中的「降级」路径直接使用（路径完全一致）

## 关联

- [[HERMES]] —— 本表路由入口在 HERMES.md MANUAL 区
- [[ops/rules/系统操作菜单]] —— 知识库操作菜单
- [[ops/rules/多Agent适配方案]] —— 多 Agent 共享数据层设计
