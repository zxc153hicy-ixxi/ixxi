---
tags: [规则, 设计]
status: active
confidence: high
summary: 多 Agent 适配方案 v5——AGENT.md 为单一事实源，sync-agent-md.sh 直接复制同步，pre-commit hook 自动触发
created: 2026-07-20
updated: 2026-07-20
---

# 多 Agent 适配方案 v5

> **一句话**：AGENT.md 是单一事实源，改一处，脚本自动同步到所有 Agent。不翻译、不改编号、纯复制。

---

## 一、模型

```
AGENT.md（人编辑，单一事实源，Agent 无关用语）
      │
      ▼
sync-agent-md.sh（纯复制，零翻译）
      │
      ├──→ CLAUDE.md（自动生成，AUTO 区）
      └──→ HERMES.md（自动生成，AUTO 区）
```

**与 v4 的关键差异**：

| | v4 | v5 |
|------|------|------|
| 事实源 | CLAUDE.md | **AGENT.md**（新建） |
| 同步方式 | Python 脚本逐段解析 + 翻译映射表 | Shell 脚本纯复制 |
| 编号处理 | G→H 前缀替换 | **不变**，G 就是 G |
| 命令处理 | slash command → terminal 命令映射 | 不翻译，操作体系本身是脚本驱动的 |
| 代码量 | ~150 行 Python | ~20 行 Shell |
| 出错点 | 翻译表遗漏、前缀改漏、映射错位 | **零**（无翻译环节） |

---

## 二、AGENT.md 内容

### 2.1 来源

基于当前 CLAUDE.md（V4.2.0），做 7 处措辞调整——去 Claude 特定用语：

| # | 行 | 旧 | 新 |
|:---:|:---:|------|------|
| 1 | 27 | Claude Code 原生默认行为 | **Agent** 原生默认行为 |
| 2 | 29 | Claude Code 默认行为 | **Agent** 默认行为 |
| 3 | 40 | 备份当前 CLAUDE.md | 备份当前 **AGENT.md** |
| 4 | 42 | CLAUDE.md↔log.md一致性 | **AGENT.md**↔log.md一致性 |
| 5 | 43 | 直接编辑 CLAUDE.md | 直接编辑 **AGENT.md** |
| 6 | 102 | CLAUDE.md 总上限 | **AGENT.md** 总上限 |
| 7 | 121 | 人直接编辑 CLAUDE.md | 人直接编辑 **AGENT.md** |

其余内容完全不变：G1-G17 编号不动、T 层路由表不动、规则优先级不变。

### 2.2 Agent 无关性分析

逐段排查当前 CLAUDE.md，确定哪些需改才能放入 AGENT.md：

| 段落 | 当前写法 | 需改？ | 说明 |
|------|------|:---:|------|
| G1-G17 约束 | 已通用（权限、确认、去噪、语言……） | 否 | 对任何 Agent 适用 |
| 规则优先级声明 | 「覆盖 Claude Code 原生默认行为」 | **是** | →「覆盖 Agent 原生默认行为」 |
| T 层路由表 | 全部路径引用（`ops/rules/`） | 否 | 路径对两个 Agent 相同 |
| 扩展系统路由 | `.claude/kb/skills/` 等 | 否 | Hermes 能读同一文件系统 |
| R 层、行数管控 | 纯规则 | 否 | — |
| 核心操作 | `/check`、`/ingest` 等功能描述 | 否 | 操作体系是脚本驱动的，slash command 只是 Claude Code 入口语法，Hermes 用 terminal 命令跑同样脚本 |
| 关键耦合点、安全 | 通用 | 否 | — |

**结论**：90% 内容无需改动。

### 2.3 操作可执行性

所有操作背后均有实际脚本或流程：

| 操作 | 实际执行内容 | 可执行方式 |
|------|------|------|
| `/check` | 调用 `check-*.py`（9 个 active）+ 内联 bash/python + LLM 判断，55 项 | `知识库检查体系.md` 逐项写了命令 |
| `/ingest` | 10 步流水线（0→9） | `Ingest完整流程.md` 步骤 0-9 |
| `/health` | 汇总最近检查报告的评分快照 | 公式在检查体系 H1 |
| `/dedup` | `check-links.py --mode broken` + `--mode index` | 合并自两脚本 |
| `/conflict` | 按 `矛盾消解流程.md` 裁决 | 有完整流程文档 |
| `/compact` | 按行数管控的四维评分精简 | 规则在 AGENT.md 正文 |
| `kb-do.sh` | 原子操作脚本 | `ops/scripts/kb-do.sh` 已建 |

### 2.4 Skill 系统

`.claude/kb/skills/` 下有 56 个 SKILL.md（内部 12 + 外部 44）。Hermes 可从同一路径加载。G17 的「Skill 自动调度」描述的是调度逻辑，与具体加载机制无关。

---

## 三、同步脚本：`sync-agent-md.sh`

### 3.1 逻辑（~20 行）

```
读 AGENT.md
    │
    ├──→ 覆盖 CLAUDE.md 的 AUTO 区（AGENT.md 完整内容）
    │    保留 CLAUDE.md 底部 MANUAL 区（如有）
    │
    └──→ 覆盖 HERMES.md 的 AUTO 区（AGENT.md 完整内容）
          保留 HERMES.md 底部 MANUAL 区（如有）
```

### 3.2 目标文件结构

```markdown
<!-- AUTO START — 由 sync-agent-md.sh 从 AGENT.md 生成，勿手动编辑 -->
（AGENT.md 完整内容，包括 G1-G17、T 层路由、核心操作等全部段落）
<!-- AUTO END -->

<!-- MANUAL START — 本 Agent 专属配置，脚本不覆盖 -->
（Claude 或 Hermes 各自的专属内容）
<!-- MANUAL END -->
```

### 3.3 触发方式

| 时机 | 方式 |
|------|------|
| `git commit`（AGENT.md 在暂存区） | **自动**：pre-commit hook 检测 → 跑脚本 → `git add` 目标文件 |
| 手动触发 | `bash engine/scripts/sync-agent-md.sh` |
| `/check` 检测 | 新增检查项：对比 AGENT.md ↔ CLAUDE.md ↔ HERMES.md 的 AUTO 区 hash，不一致告警 |

---

## 四、pre-commit hook 改动

在现有 `.git/hooks/pre-commit` 中，在 CLAUDE.md 检测**之前**插入：

```bash
# AGENT.md 变更 → 自动同步到 CLAUDE.md + HERMES.md
if git diff --cached --name-only | grep -q "AGENT.md"; then
  bash engine/scripts/sync-agent-md.sh
  git add CLAUDE.md HERMES.md
  echo "✅ AGENT.md → CLAUDE.md + HERMES.md 已同步"
fi
```

插入位置在 CLAUDE.md 检测之前的理由：`sync-agent-md.sh` 会更新 CLAUDE.md，同步后的 CLAUDE.md 继续走原有 tag+log 验证逻辑。

### 完整链路

```
人编辑 AGENT.md → git add → git commit
                                │
                    pre-commit 钩子触发
                                │
                    检测到 AGENT.md 在暂存区
                                │
                    跑 sync-agent-md.sh
                                │
                    git add CLAUDE.md HERMES.md（自动暂存）
                                │
                    继续现有检查（tag + log.md 验证）
                                │
                    全部通过 → 提交
```

---

## 五、回流通路

Hermes 新增约束的回流：

```
Hermes 会话中提议新约束
        │
        ▼
人确认"值得加"
        │
        ▼
人编辑 AGENT.md（走 G 层修改流程）
        │
        ▼
git commit → pre-commit 自动同步到 CLAUDE.md + HERMES.md
```

AGENT.md 始终是唯一编辑入口。不存在双向冲突。

---

## 六、实施清单

| # | 任务 | 产出 | 破坏性 |
|:---:|------|------|:---:|
| 1 | 新建 `AGENT.md` | 基于 CLAUDE.md + 7 处措辞调整 | 无 |
| 2 | 改写 `CLAUDE.md` | 顶部加注释 + AUTO/MANUAL 区标记 | 极低 |
| 3 | 新建 `engine/scripts/sync-agent-md.sh` | ~20 行 Shell 脚本 | 无 |
| 4 | 修改 `.git/hooks/pre-commit` | 插入 AGENT.md 检测段 | 中 |
| 5 | 更新 `多Agent适配方案.md`（本文件） | 替换为 v5 | 无 |

---

## 七、关联

- `AGENT.md` —— 单一事实源（待建）
- `CLAUDE.md` —— Claude Code 指令文件（AUTO 区由脚本维护）
- `HERMES.md` —— Hermes 指令文件（待建，AUTO 区由脚本维护）
- [[知识库检查体系]] —— `/check` 将新增 AUTO 区 hash 比对项
- [[ops/rules/版本管理规范]] —— G 层修改流程（编辑目标改为 AGENT.md）
