# ixxi（曦曦）

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/zxc153hicy-ixxi/ixxi/ci.yml?branch=main)](https://github.com/zxc153hicy-ixxi/ixxi/actions)
[![Version](https://img.shields.io/github/v/tag/zxc153hicy-ixxi/ixxi)](https://github.com/zxc153hicy-ixxi/ixxi/releases)

> **一句话**：ixxi = 一个「Agent 能力可迁移、可验证、可演化的中间层」。

不是「又一个知识库」，而是让「能力」可迁移、可验证、可演化、不绑定任何 Agent。轻量知识库（kb 系统）是内置能力 + 参考实现，证明这套能力可用。

**机制开源、内容私有、多 Agent 平等、边界随使用演化。**

## 定位一句话

> ixxi 是 Agent 的**使用层**，LangChain 是 Agent 的**构建层**。

## 架构（三层分离）

能力在 `framework/core/` 声明，路由在 skill 调度注册表裁决，适配层把能力挂到具体 Agent——三层解耦，能力不绑定任何 Agent。

```
┌──────────────────────────────────────────────────────────┐
│  适配层  Adapter（具体 Agent）                             │
│  Claude ── Codex ── Hermes                              │
│  经原生机制加载：Skill 注入 / .agents 发现 / SKILL.md 直读  │
└──────────────────────────┬───────────────────────────────┘
                           │ 调用已挂载的能力
┌──────────────────────────▼───────────────────────────────┐
│  路由层  Routing（Skill 调度注册表 · 单一事实源）            │
│  给定任务 → 匹配 skill → 各 Agent 的调用方式                │
│  framework/ops/rules/skill调度注册表.md                    │
└──────────────────────────┬───────────────────────────────┘
                           │ 引用（只引用 Capability ID，不变量 I5）
┌──────────────────────────▼───────────────────────────────┐
│  能力层  Capability（Agent-neutral · 不绑定任何 Agent）     │
│  framework/core/：skills · agents · hooks · rules          │
│  capability.json：requires（需要什么）+ provides（提供什么）│
└──────────────────────────────────────────────────────────┘
```

## ixxi 不是什么

- **不是 LangChain 的替代品**：ixxi 是**使用层**（能力如何被 Agent 调度、验证、演化），LangChain 是**构建层**（能力如何被构建、编排）。两者层面不同，不冲突。
- **不是知识库**：kb 知识库只是内置的一个能力 + 参考实现，用来证明「能力可迁移、可验证、可演化」。ixxi 本身是能力的中间层，不是内容的仓库。
- **不是多 Agent 编排器**：ixxi 不负责多个 Agent 协作完成任务，只保证「同一个能力，换个 Agent 也能用」——能力与 Agent 解耦。

## 目录结构

```
ixxi/
├── ixxi                    # init 一键脚本（把 framework 变成你的实例）
├── framework/              # 开源通用层（机制，git 版本化）
│   ├── core/               #   能力源：skills（16 管理 + 57 外部）+ agents + hooks
│   ├── engine/             #   引擎脚本：check / sync / fix / migrate / scan
│   ├── ops/                #   规则 + framework-patterns（通用教训）+ hermes 命令索引
│   ├── knowledge/          #   framework-designs（框架设计）
│   ├── docs/               #   guides（上手/迁移/规范）+ evolution（演化机制）
│   └── samples/            #   演示数据（跑通 demo 用）
├── personal/               # 私有实例层（你的数据，.gitignore 排除，init 生成）
├── README.md / GETTING-STARTED.md / LICENSE
└── .github/                # CI + CLA + issue/PR 模板
```

## 两种使用方式

拿到 ixxi 后，两种方式二选一：

| 方式 | 适合谁 | 怎么做 |
|---|---|---|
| **A 轻量** | 只在 ixxi 目录里用 | `cd ixxi` 后打开 Agent，它会读到引导文件（CLAUDE.md / AGENTS.md / HERMES.md），按提示跑 `bash ixxi init` 即可 |
| **B 全局** | 想在**任意目录**说「加载 ixxi」 | 跑 `bash install.sh`，把启动器装到全局 + 设 IXXI_HOME |

两种方式之后都一样：初始化 → 说「加载 ixxi」→ 首次弹引导 → 开始用。

## 快速上手

- **5 分钟上手**：从 clone 到跑通第一个 ingest，见 [GETTING-STARTED.md](GETTING-STARTED.md)。
- **demo → 真实**：跑通演示后切换到你自己的真实数据（数据替换 / 场景注册 / skill 编写），见 [demo 到真实迁移指南](framework/docs/guides/demo到真实迁移指南.md)。
- **维护者**：看懂每个目录 + 改什么跑什么 + 疏忽检查清单，见 [维护者手册](framework/docs/maintenance/维护者手册.md)。
- **二次开发**：想基于 ixxi 做二次开发？每个目录/重要文件干什么 + 怎么扩展，见 [架构文档](framework/docs/架构文档.md)。
- **开源发布**：首次开源 / 每次 release 前照清单查一遍（一键脚本），见 [开源检查流程](framework/docs/guides/开源检查流程.md)。

## 核心判据

「**换个陌生使用者还有用吗**」→ 有用进 framework，没用留 personal。

## 三个核心抽象

- **Capability**：能力对象（instruction + resources + executable + constraints + lifecycle + compatibility）
- **Adapter**：把 Capability 映射到具体 Agent（Claude / Codex / Hermes）
- **Instance**：个人环境中的能力实例

## 十个核心不变量（I1-I10）

权威能力源 Agent-neutral（I1）· 能读 ≠ 能执行（I2）· 声明 == 实际（I3/I4）· 路由只引用 Capability ID（I5）· personal 是下游实例（I6）· 显式贡献流程（I7）· telemetry 是信号非事实（I8）· critical 不自动归档（I9）· 可迁移对象有 version（I10）。

## License

MIT
