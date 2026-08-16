# ixxi（曦曦）

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/zxc153hicy-ixxi/ixxi/ci.yml?branch=main)](https://github.com/zxc153hicy-ixxi/ixxi/actions)
[![Version](https://img.shields.io/github/v/tag/zxc153hicy-ixxi/ixxi)](https://github.com/zxc153hicy-ixxi/ixxi/releases)

> **一句话**：ixxi 让你在一个 Agent 里攒下的做事能力，换到另一个 Agent 还能接着用——**能力不绑定 Agent**。

---

## 它解决什么问题

你在一个 Agent 里攒下的方法、规则、工作流、沉淀的经验，**换到另一个 Agent 就丢了**——因为能力绑定在特定 Agent 上。而真实使用中，没人只用单一 Agent：不同问题用不同 Agent，能力绑定就是真实损失。

ixxi 把「能力」从「Agent」里抽出来，做成一个可迁移、可验证、可演化的**中间层**：

- **可迁移**：同一个能力，Claude / Codex / Hermes 都能用，一等公民
- **可验证**：「声明能用」和「真能用」分开验证（`check-skill-parity` 六项断言锁死），不靠嘴说
- **可演化**：用得多的留下、没人用的归档，边界随真实使用长出来

> ixxi 是 Agent 的**使用层**，LangChain 是 Agent 的**构建层**——一个回答「怎么把 Agent 用起来、用出自己的资产」，一个回答「怎么把 Agent 造出来」。不冲突、不替代。

**机制开源、内容私有、多 Agent 平等、边界随使用演化。**

---

## 它能帮你干嘛

### 内置知识操作系统（16 个 kb-* 管理 skill）

ixxi 自带一套「知识操作系统」作为参考实现，跑通「把资料变成可查知识」的完整闭环：

| 环节 | 能力 | 一句话 |
|---|---|---|
| **入库** | kb-ingest | 把聊天记录/笔记/文档丢进 inbox，10 步流水线提炼成结构化知识页，medium/low 置信度必须人工确认，每次强制 git commit |
| **体检** | kb-lint / kb-health | 9 维度 55 项全身体检，断链/过时/冲突/版本号，输出健康度评分 |
| **检索** | kb-query | 6 步精准问答，**本地知识优先于训练数据** |
| **收尾** | kb-session-close | 会话结束回溯反馈 → 入库 → 生成会话摘要 |
| **运维** | kb-compact / refresh / dedup / enrich / export-template | 精简、过时检测、查重、打标签、导出迁移 |
| **进化** | kb-curator / kb-promote | 把重复操作自动封装成新 skill；把高频规则晋升为铁律 |

### 领域能力（57 个外部 skill，6 大类）

- **创作**（构思 → 写作 → 审查的原创小说全流水线）：构思 `brainstorming`/`fiction-abstraction`/`scene-framing` · 写作 `scene-writer`/`dialogue-techniques`/`prose-producer` · 审查 `consistency-checker`/`ruthless-critique`/`voice-revision`，含中文网文专用 `Humanizer-zh`/`story-collab`
- **工程**（superpowers 风格工程能力集）：规划 `prd`/`writing-plans` · 开发 `TDD`/`systematic-debugging`/`subagent-driven-development` · 协作 `requesting-code-review`/`using-git-worktrees`

### 可验证的审查团（15 个 agent）+ 机械护栏（8 个 hooks）

- **15 个审查 agent** 分 4 组（内容处理/运维/用户视角/设计），每个带运行遥测（采纳率/准确率），用实际表现度量质量
- **8 个 hooks** 只锁纯机械操作（登记校验、DCO 签名、G 层修改 tag 校验），语义判断仍交给 LLM

---

## 30 秒上手

```bash
git clone https://github.com/zxc153hicy-ixxi/ixxi.git
cd ixxi
bash ixxi init        # 问 3 个问题：用哪个 Agent / 数据放哪 / 是否启用 hooks
```

然后在 Agent 里说「**加载 ixxi**」→ 首次弹引导 → 跑通最小闭环：

```bash
cp framework/samples/demo-note.md personal/data/inbox/   # 放一条演示笔记
# 回 Agent 里说「入库」，看到它把 demo 提炼成结构化知识，就通了
```

完整 5 分钟引导见 [GETTING-STARTED.md](GETTING-STARTED.md)。

---

## 架构：三层分离

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
└──────────────────────────┬───────────────────────────────┘
                           │ 引用（只引用 Capability ID）
┌──────────────────────────▼───────────────────────────────┐
│  能力层  Capability（Agent-neutral · 不绑定任何 Agent）     │
│  framework/core/：skills · agents · hooks · rules          │
│  capability.json：requires（需要什么）+ provides（提供什么）│
└──────────────────────────────────────────────────────────┘
```

**数据流单向**：`core/`（权威源）→ sync 脚本 → 适配层 → 各 Agent 加载。`personal/` 是下游实例，永不回流 framework（除显式贡献回流流程）。

---

## 核心机制

### 入库（Ingest）—— 10 步提炼流水线

预检 → 读取 → 冲突去重 → 写入 → **对话确认（硬闸门）** → 交叉引用 → 校验 → 更新索引 → **git commit（强制）** → 变更摘要。

每步都有失败处理：低置信内容必须人工确认才激活，每页强制 ≥1 条出链，不达标降级为 draft。

### 体检 —— 9 维度 55 项，单一入口 `/check`

结构完整性 / 一致性 / 规则完备性 / 可执行性 / 安全性 / 可维护性 / 用户体验 / 长期健康 / 可移植性。

三层执行：自动化脚本（机械检查）+ LLM 判断（语义检查）+ 人工抽查。健康度公式 `(自动化通过率×50) + ((1-反模式触碰率)×50)`。

### 技能化 —— 能力自己长出来

kb-curator 检测高频重复操作 → 按自适应阈值（刚起步 7 天/≥2 次 → 用熟 90 天/≥5 次）提议封装成新 skill → 跟踪使用 → 归档退役。

### 演化飞轮 —— 边界随使用演化

**采集**（记录每次能力使用）→ **候选**（输出 N 天未触发清单）→ **人工确认**（价值裁决）→ **归档**（原子操作）。

核心纪律：**遥测是决策信号，不是价值事实**（usage ≠ value，高频不等于有价值）；Critical 能力不允许仅凭使用频率自动归档。

---

## 设计哲学

- **AI 帮你做，但不替你决定**：决策三级制「用户 > 规范 > AI」，破坏性操作必确认，贡献回流用户自愿
- **规则让位于机制**：能脚本强制的不靠 LLM 自律——安全/验证/编排下沉为 hooks、deny 规则、检查脚本
- **换个陌生使用者还有用吗**：核心判据，有用进 framework（通用开源），没用留 personal（私有）

---

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

| 方式 | 适合谁 | 怎么做 |
|---|---|---|
| **A 轻量** | 只在 ixxi 目录里用 | `cd ixxi` 后打开 Agent，按提示跑 `bash ixxi init` |
| **B 全局** | 想在**任意目录**说「加载 ixxi」 | 跑 `bash install.sh`，装全局启动器 + 设 IXXI_HOME |

两种方式之后都一样：初始化 → 说「加载 ixxi」→ 首次弹引导 → 开始用。

---

## 设计原理（给二次开发者）

**三个核心抽象**：

- **Capability**：能力对象（instruction + resources + executable + constraints + lifecycle + compatibility）
- **Adapter**：把 Capability 映射到具体 Agent（Claude / Codex / Hermes）
- **Instance**：个人环境中的能力实例

**十个核心不变量（I1-I10）**：

能力源 Agent-neutral（I1）· 能读 ≠ 能执行（I2）· 声明 == 实际（I3/I4）· 路由只引用 Capability ID（I5）· personal 是下游实例（I6）· 显式贡献流程（I7）· telemetry 是信号非事实（I8）· critical 不自动归档（I9）· 可迁移对象有 version（I10）。

想基于 ixxi 做二次开发？每个目录/重要文件干什么 + 怎么扩展，见 [架构文档](framework/docs/架构文档.md)。

## 参与贡献

你用了 ixxi 沉淀出对别人也有用的能力？走**显式贡献回流**：导出贡献包 → 脱敏扫描 → PR → 维护者按「换个陌生使用者还有用吗」判据审核 → 合并进 framework。详见 [贡献回流流程](framework/docs/guides/贡献回流流程.md) 和 [CONTRIBUTING.md](CONTRIBUTING.md)。

## License

MIT

## 作者想说的话

咳咳，我就是小菜鸡嗷，这东西是我用ai辅助我做出来的，而且肯定有bug大佬们见谅。