# ixxi（曦曦）

> **一句话**：ixxi = 一个「Agent 能力可迁移、可验证、可演化的中间层」。

不是「又一个知识库」，而是让「能力」可迁移、可验证、可演化、不绑定任何 Agent。轻量知识库（kb 系统）是内置能力 + 参考实现，证明这套能力可用。

**机制开源、内容私有、多 Agent 平等、边界随使用演化。**

## 定位一句话

> ixxi 是 Agent 的**使用层**，LangChain 是 Agent 的**构建层**。

## 目录结构

```
ixxi/
├── framework/   # 开源通用层（机制 + schema + 通用 skill + 通用规则 + 审查团）
├── personal/    # 私有实例层（数据 + 个人绑定 + 运行状态，.gitignore 排除）
├── engine/      # 引擎脚本
└── docs/        # 文档
```

## 快速上手

见 [GETTING-STARTED.md](GETTING-STARTED.md) —— 5 分钟从 clone 到跑通第一个 ingest。

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
