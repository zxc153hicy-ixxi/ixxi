---
tags: [规则, 设计]
status: active
confidence: high
summary: 多 Agent 适配方案 v6——三层分离（能力/路由/适配）+ 三 agent 平等（Claude/Codex/Hermes 一等公民），6 个 sync 脚本 + parity 六项断言
created: 2026-07-20
updated: 2026-08-14
---

# 多 Agent 适配方案 v6

> **一句话**：能力层 Agent 无关（权威源），路由层 Agent 无关（唯一），适配层每 agent 各用原生语法——三 agent 一等公民，谁来都能用得好，能力不缩水。

## 一、三层分离（平等的地基）

```
能力层 Capability（Agent 无关，单一事实源，唯一）
  SKILL.md 权威源 / ops/rules/ / engine+ops scripts /
  core/agents/registry.json / core/hooks/（git 层）
        ▼
路由层 Routing（Agent 无关，唯一）
  skill调度注册表.md —— 任务→能力匹配，同一套逻辑三 agent 共用
        ▼
适配层 Adaptation（每 agent 原生加载通道，只此层有差异）
  Claude: .claude/skills/kb-* + .claude/agents/*.md + settings.json hooks
  Codex : .agents/skills/ + .codex/agents/*.toml + .codex/hooks
  Hermes: SKILL.md 原生直读 + ops/hermes/命令索引（脚本生成）
```

**平等的地基定义**：对任意能力 C，三 agent 的适配层都能**完整加载** C，加载方式各用各的原生语法，但加载到的内容是**同一个**（同一份 SKILL.md、同一个脚本、同一份规则文件）。

## 二、能力路由（可达性，替代降级翻译表）

对每个能力给三列路由，**三列地位相等**，Hermes 列不是「降级产物」而是「Hermes 原生方式」：

| 能力 | Claude 原生访问 | Codex 原生访问 | Hermes 原生访问 |
|---|---|---|---|
| 契约 + 路由 | CLAUDE.md AUTO 区 | AGENTS.md AUTO 区 | HERMES.md AUTO 区（G 编号不变） |
| 内部管理 skill（15） | `Skill: kb-*`（一级平铺） | `Skill: kb-*`（.agents/skills/ 发现） | 直读 SKILL.md + 命令索引执行 |
| 外部领域 skill（57） | `Skill: <name>`（_external 注入） | `Skill: <name>`（.agents/skills/ 镜像） | 直读 SKILL.md，纯流程型无需命令即完整 |
| 审查团（15） | `.claude/agents/*.md` 原生 subagent | `.codex/agents/*.toml` 原生 agent | 读 registry.json 提示调度 |
| 自动化强制 | settings.json gate | .codex/hooks + git pre-commit | git pre-commit 委托链共享 + 脚本直跑 |
| 机械脚本 | find + Bash 跑 engine/scripts/ | 同左 | 同左（零翻译） |

> **可达性 ≠ 等价性**：LLM 非确定性下「行为等价」不可验证。parity 只校验「可达性」（能力能否被该 agent 调用），不承诺「等价性」。平等是治理原则（一等公民、能力透明、差异可见），不是「实现完全相同」的技术约束。

## 三、同步脚本（6 个，能力层 → 适配层）

| 脚本 | 权威源 → 适配层 |
|---|---|
| `sync-agent-md.sh` | AGENT.md → CLAUDE/HERMES/AGENTS（AUTO 区） |
| `sync-skills-to-claude.py` | core/skills → .claude/skills/kb-*（平铺） |
| `sync-skills-to-codex.py` | core/skills + _external → .agents/skills（镜像） |
| `sync-skills-to-hermes.py` | 同上 → ops/hermes/Hermes-命令索引.md（脚本生成） |
| `sync-agents-to-claude.py` | core/agents → .claude/agents/*.md（原生 subagent） |
| `sync-agents-to-codex.py` | core/agents → .codex/agents/*.toml（原生 agent） |

**适配层产物不入 git**：`.claude/skills/kb-*/`、`.agents/`、`.claude/agents/` 由 sync 脚本从能力层生成，`.gitignore` 排除；clone 后跑 sync 重新生成。权威源（能力层）是唯一 git 版本化的 skill/agent 定义。

## 四、能力不缩水验证（check-skill-parity.py）

对每个 skill 六项断言（P1-P6）：

| 断言 | 检查 | 失败含义 |
|---|---|---|
| P1 权威源 | 能力层 SKILL.md 存在 | 能力层缺源 |
| P2 Claude 可达 | .claude/skills/ 平铺或 _external 注入存在 | Claude 缩水 |
| P3 Codex 可达 | .agents/skills/ 镜像存在 | Codex 缩水 |
| P4 Hermes 可达 | Hermes-命令索引.md 含条目且非「不运行」 | Hermes 缩水 |
| P5 引用资源 | SKILL.md 引用脚本/规则文件存在 | 能力层断链 |
| P6 注册表覆盖 | skill调度注册表.md 三列均有条目 | 路由层缺列 |

运行：`python engine/scripts/check-skill-parity.py`，六项全过 = 能力不缩水。

## 五、各 agent 适配层要点

- **Claude**：`.claude/agents/*.md` 启用原生 subagent（工具权限隔离）；MANUAL 区声明 statusline 与敏感降级通道。
- **Codex**：`.codex/agents/*.toml` 原生 agent；`.agents/skills/` 仓库级发现；hooks 以 git pre-commit 委托链落实机械验证。
- **Hermes**：SKILL.md 原生直读（文件系统共享，非 Claude 专属）+ 命令索引执行脚本；自动化等价物 = git pre-commit 委托链 + 脚本直跑（不引入事件 hook 的虚假对等承诺）。

## 六、敏感内容与自动化边界声明

- **敏感内容**：本地 LLM 适合敏感内容，云端 LLM 仅非敏感。敏感内容降级通道 = 本地 Hermes 原生占优，云端 Claude/Codex 处理时跳过或移交本地——诚实声明为「共享分工」，非能力缩水。
- **自动化边界**：事件 hooks、原生 subagent 为 Claude/Codex 引擎原生；Hermes 的自动化等价物 = git pre-commit 委托链（护栏效果一致）+ 脚本直跑。明确标注「机制不同，能力等价」，不给虚假对等承诺。

## 七、hooks 边界澄清

> **一句话纠偏**：「hooks 已被统一」是误解。正确的是——**git 层 hooks 三 agent 共享，runtime hooks 各 agent 原生**，两者不可混淆。

ixxi 有两类「hooks」，名称相近、机制完全不同：

| 维度 | git hooks | runtime hooks |
|---|---|---|
| 触发时机 | git 操作 | 每次工具调用 |
| 覆盖范围 | commit / push / merge | 会话内行为 |
| 归属 | 三 agent 共享（一份） | 各 agent 各自机制（互不相同） |
| 实现 | core/hooks/ + .git/hooks（委托链） | 各引擎 settings（Claude settings.json / Codex .codex/hooks 等） |
| 代表 | pre-commit 委托链做机械验证 | settings.json PostToolUse / Stop、Codex hooks.json |

**断言**：
- git hooks 不能统一 runtime hooks：git pre-commit 只在 git 事件时触发，管不到会话内工具调用；runtime hooks 由各 agent 引擎自身机制执行，git 层不可见、不可代理。
- 机械验证（计数 / 断链 / 版本）→ 走 git pre-commit 委托链，一次落实三 agent 共享生效。
- 行为验证（语义判断）→ 走各 agent 自身机制 + LLM 纪律，git 层管不到。
- Hermes 无事件 hook 等价物，其自动化等价物 = git pre-commit 委托链 + 脚本直跑（见「五、各 agent 适配层要点」），不承诺 runtime hooks 层面的虚假对等。

## 八、关联

- `AGENT.md` —— 契约单一事实源
- `skill调度注册表.md` —— 路由层单一事实源
- `Hermes-命令索引.md` —— Hermes 适配层命令索引（脚本生成）
- [[知识库检查体系]] —— /check 纳入 parity 检查项
- [[ops/rules/版本管理规范]] —— G 层修改流程（编辑目标 = AGENT.md）
