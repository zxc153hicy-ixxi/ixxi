---
tags: [指南]
status: active
summary: demo→真实使用迁移指南——数据替换、场景注册、skill 编写三步，30 分钟从演示切换到真实
---

# demo → 真实使用迁移指南

> 目标：30 分钟内从「演示数据」切换到「你自己的真实数据」。
> 前置：已完成 `./ixxi init`（见 GETTING-STARTED.md）。

## 第 0 步：先跑通 demo（5 分钟）

用 framework 自带的虚构演示数据跑一遍最小闭环，确认链路通：

```bash
# 把演示数据放进你的个人 raw 输入区
cp framework/samples/demo-note.md personal/raw/inbox/

# 按 kb-ingest 流程入库（入库 → 体检 → 检索）
#   入库：framework/core/skills/ingest/SKILL.md
#   体检：framework/core/skills/lint/SKILL.md
#   检索：framework/core/skills/knowledge-query/SKILL.md
```

预期：`demo-note.md` 提炼成 3 条 wiki（三个原则），见 `framework/samples/expected-result.md` 核对。

## 第一步：数据替换（samples → 真实 raw）

把你自己的资料放进 personal 实例，替换演示数据：

```bash
# 清掉演示数据
rm personal/raw/inbox/demo-note.md

# 放进你的真实资料（任意格式：md / txt / 截图 / 笔记导出）
cp ~/你的资料.md personal/raw/inbox/
```

然后重跑 kb-ingest。这一步验证「demo 跑通 ≠ 你的数据跑通」——你的资料格式、主题、体量都不同，遇到问题按 kb-ingest 的失败处理（步骤表「失败处理」列）走。

## 第二步：场景注册（注册第一个个人场景）

打开 `personal/scene-registry.md`，登记你的第一个场景：

```markdown
| 编号 | 场景名 | 状态 | 场景描述 | 主要目录 | 创建时间 |
|------|------|------|------|------|------|
| S1 | 学习笔记 | active | 整理学习资料，提炼知识点 | personal/knowledge/learning | 2026-08-14 |
```

schema 见 `framework/engine/config/scene-registry-schema.md`（字段定义 + 状态机）。domain 值用 `framework/engine/config/tag-taxonomy.yaml` 里的合法词表，越界词由 `check-scene-domain` 校验提示补登。

## 第三步：skill 编写（写第一个个人 skill）

在 `personal/.claude/skills/personal/` 写你的第一个个人 skill（专属你的工作流）：

```markdown
---
name: my-daily-review
description: 我的每日回顾流程——整理当天笔记、更新待办
---

# 每日回顾

## 流程
1. 读今天的 raw/sessions/ 会话记录
2. 提炼 3 条以内的新知识点，跑 kb-ingest 入库
3. 更新 personal/queue.md 待办
4. 跑 kb-lint 体检
```

注意：
- 个人 skill 只放 personal 层，**不进 framework**（framework 是通用层）
- skill 格式参照 framework 的任意 kb-* skill（frontmatter `name` + `description` + 正文流程）
- 写完后跑 `sync-skills-to-claude.py`（或对应 agent 的 sync），让它被加载

## 验收：30 分钟切换到真实

| 检查点 | 达成标志 |
|---|---|
| demo 跑通 | demo-note 提炼成 3 条 + 体检 + 检索通 |
| 数据替换 | 你的真实资料成功入库 |
| 场景注册 | scene-registry.md 有 S1 条目 |
| skill 编写 | personal skill 被 sync 加载 |

全部达成 = 你已从「演示者」变成「真实使用者」。之后的内容默认进 personal 层，满足「换个陌生使用者还有用吗」再晋升 framework。

## 常见问题

- **跑 kb-ingest 报「敏感扫描」阻断**：资料里有密码/密钥等，先脱敏再入库
- **提炼出的条数不对**：对照 `samples/expected-result.md` 的核对点，检查 frontmatter/交叉引用/索引
- **personal skill 没被加载**：确认放在了 `personal/.claude/skills/personal/`，且跑了 sync
