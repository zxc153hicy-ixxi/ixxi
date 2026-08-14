---
tags: [指南, MVP, ixxi]
created: 2026-08-14
status: active
summary: MVP 边界（v0.1）——3 核心 capability + 1 Agent + 基本演化构成最小闭环；不纳入 v1 清单；未触发报告 v1 交付要求
---

# MVP 边界（v0.1）

> 目的：固定「做到什么程度可发 v0.1」，防止无限膨胀。新增/删除纳入项 = 修改本边界 → 走设计变更流程确认，禁止实现中自行扩界。

## 一句话定位

**ixxi 是 Agent 的使用层，LangChain 是 Agent 的构建层。**

ixxi 不做 agent 本体（Claude/Codex 等），不做重型 harness 底层，只做「个人 Agent 使用层的开源框架」——能力可迁移、可验证、可演化，即插即用，让 agent 更贴合个人使用习惯、资产可随人迁移。知识库（kb）= 内置能力 + 参考实现，证明这套能力可用。

## 纳入 v1（最小闭环）

| 项 | 内容 | 为什么纳入 |
|------|------|------|
| 核心 capability | 3 个：kb-ingest / kb-lint / kb-query | 覆盖「入库→体检→检索」最小闭环，证明框架可用 |
| Agent | 1 个：Claude | 用户主用且能力最全，架构验证成本最低 |
| 基本演化 | 场景注册 + `ixxi stats --unused` | 让演化闭环可运行 |

### 核心 capability 3 个

| capability | 权威源 | 作用 |
|------|------|------|
| kb-ingest | `core/skills/ingest/` | 入库（raw → 提炼 → knowledge/） |
| kb-lint | `core/skills/lint/` | 体检（健康度 / 完整性检查） |
| kb-query | `core/skills/knowledge-query/` | 检索（知识优先回答） |

三者串成「入库 → 体检 → 检索」最小闭环：能进得来、查得出、检得着健康，证明框架机制可用。

### Agent 1 个（先单后多）

- v0.1 只适配 **Claude**（核心 agent），验证架构后再扩展 Hermes / Codex。
- 价值观：多 Agent 平等（一等公民、能力透明、差异可见），实施路径 **先单后多**——先单 Agent MVP 验证架构，再扩展。

### 基本演化

- **场景注册**：开放注册 + 受控词表校验（schema 归 framework，数据行归实例层）。
- **未触发报告**：`ixxi stats --unused`（见下）。

## 未触发报告（v1 必含，不可延后 v2）

**v1 必须含最小化 `ixxi stats --unused`，不可延后 v2——否则演化闭环空转。**

| 项 | 内容 |
|------|------|
| 命令 | `ixxi stats --unused [--days N]`（默认 30 天） |
| 输出 | N 天未触发的 capability 清单：skill 名 + 最后触发时间 + 建议（保留 / 归档候选） |
| 数据源 | 遥测 `raw/sessions/skill-usage.json`（优先）；`core/skills/**/capability.json` 的 last_used/triggered 字段（兜底）；无遥测 → 提示「暂无遥测数据，使用后由 kb-curator 记录触发」 |
| 判据 | 遥测是演化决策信号（usage ≠ value），价值判断保留人工裁决 |
| 实现 | `engine/scripts/stats-unused.py`（Python 标准库，零第三方依赖） |

## 不纳入 v1（明确不做）

| 项 | 说明 |
|------|------|
| 多 Agent 扩展 | Hermes / Codex 适配延后，v0.1 只保 Claude |
| adapter SDK | 第三方 agent 接入 SDK 延后 |
| 商业化 | 授权 / 付费 / 企业服务延后 |
| 测试金字塔全量 | 最小验证即可，不追求全量测试覆盖 |

## 关联

- `index.md` —— MOC 全局导航
- `AGENT.md` —— 多 Agent 行为契约
- `docs/evolution/` —— 演化机制公开规则
- 设计源：ixxi 实施计划「MVP 定义」+ ixxi 完整设计「决策点 6 未触发报告」（位于设计文档，不随 framework 分发）
