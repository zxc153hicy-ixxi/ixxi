---
tags: [指南, hooks]
status: active
confidence: high
summary: hooks 边界说明——git hooks 与 runtime hooks 的区别，纠偏「git hooks 已统一一切」的误解
created: 2026-08-14
---

# hooks 边界说明

ixxi 里有两类「hooks」，名称相近、机制完全不同。本文说明两者的边界，纠偏「git hooks 统一一切」的误解。口径与 [[ops/rules/多Agent适配方案]]「七、hooks 边界澄清」一致。

## 对照表

| 维度 | git hooks | runtime hooks |
|---|---|---|
| 触发时机 | git 操作 | 每次工具调用 |
| 覆盖范围 | commit / push / merge | 会话内行为 |
| 归属 | 三 agent 共享（一份） | 各 agent 各自机制（互不相同） |
| 实现 | core/hooks/ + .git/hooks（委托链） | 各引擎 settings（Claude settings.json / Codex .codex/hooks 等） |
| 代表 | pre-commit 委托链做机械验证 | settings.json PostToolUse / Stop、Codex hooks.json |

## 常见误解

- **误解：「hooks 已被统一」「git hooks 统一一切」** → 错。git hooks 只覆盖 git 操作，管不到会话内每次工具调用。
- **误解：三 agent 的自动化是一套机制** → 错。git 层 hooks 三 agent 共享一份；runtime hooks 各 agent 用各自引擎的原生机制，互不相同。
- **误解：runtime hooks 可以靠 git hooks 代理实现** → 错。git 层对会话内调用不可见、不可代理。
- **误解：Hermes 没有 hooks 就是自动化缺失** → 错。Hermes 的自动化等价物 = git pre-commit 委托链 + 脚本直跑，护栏效果一致；缺失的是 runtime hooks 层的虚假对等承诺。

## 正确理解

- **git 层 hooks 三 agent 共享，runtime hooks 各 agent 原生**，两者不可混淆。
- **机械验证（计数 / 断链 / 版本）** → 走 git pre-commit 委托链，一次落实、三 agent 共享生效。
- **行为验证（语义判断）** → 走各 agent 自身机制 + LLM 纪律，git 层管不到。
