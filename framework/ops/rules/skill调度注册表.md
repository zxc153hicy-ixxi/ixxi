---
tags: [注册表, 调度]
status: active
confidence: high
summary: 跨 agent skill 调度注册表——单一事实源，Claude/Hermes/Codex 三 agent 统一路由依据
created: 2026-08-13
updated: 2026-08-14
---

# Skill 调度注册表

> **单一事实源**：给定任务 → 匹配 skill → 各 agent 调用方式。三 agent（Claude/Hermes/Codex）统一指向本表。
> **维护**：新增/修改 skill 后①更新本表②跑 `sync-skills-to-claude.py`（Claude 平铺）③跑 `sync-skills-to-codex.py`（Codex 平铺）④跑 `sync-skills-to-hermes.py`（Hermes 命令索引）。

## 表 A · 内部管理 skill（15 条，跨 agent 核心）

> 三 agent 均通过原生机制加载：Claude=Skill 注入、Codex=.agents/skills/ 发现、Hermes=SKILL.md 直读 + 命令索引执行。

| skill | 触发场景 | 关键词 | Claude | Hermes | Codex | 规则文件 |
|---|---|---|---|---|---|---|
| kb-ingest | 入库/提炼资料 | ingest、入库、提炼、整理、收录 | Skill: kb-ingest | 直读 SKILL.md+命令索引（见 ops/hermes/Hermes-命令索引.md）：check-inbox.py --mode health + scan-sensitive.py + 10步流水线 | Skill: kb-ingest | [[ops/rules/Ingest完整流程]] |
| kb-lint | 体检/健康度检查 | lint、体检、健康度、检查、有没有毛病 | Skill: kb-lint | 直读 SKILL.md+命令索引（见 ops/hermes/Hermes-命令索引.md）：check_*.py --repo . 全量 55 项 | Skill: kb-lint | [[ops/rules/知识库检查体系]] |
| kb-audit | 全量审计/查漏 | audit、审计、回溯、遗漏、查漏 | Skill: kb-audit | 直读 SKILL.md+命令索引（见 ops/hermes/Hermes-命令索引.md）：全量审计（已并入 /check） | Skill: kb-audit | [[ops/rules/全量审计流程]] |
| kb-compact | 精简/瘦身/合并 | compact、精简、压缩、太长了、合并 | Skill: kb-compact | 直读 SKILL.md+命令索引（见 ops/hermes/Hermes-命令索引.md）：--mode lines 行数精简 / --mode files 合并碎片 | Skill: kb-compact | [[ops/rules/核心操作流程]] |
| kb-conflict | 矛盾/冲突裁决 | 矛盾、冲突、裁决、规则打架 | Skill: kb-conflict | 直读 SKILL.md+命令索引（见 ops/hermes/Hermes-命令索引.md）：LLM 按流程检测矛盾→输出《反馈冲突提示》→暂停 | Skill: kb-conflict | [[ops/rules/矛盾消解流程]] |
| kb-analyze | 可行性评估 | 评估、可行性、打分、值不值得、分析 | Skill: kb-analyze | 直读 SKILL.md+命令索引（见 ops/hermes/Hermes-命令索引.md）：五维加权评分（LLM） | Skill: kb-analyze | [[ops/rules/可行性分析流程]] |
| kb-export-template | 导出/打包/备份 | 导出、打包、备份、迁移 | Skill: kb-export-template | 直读 SKILL.md+命令索引（见 ops/hermes/Hermes-命令索引.md）：bash engine/templates/export-template.sh | Skill: kb-export-template | [[ops/rules/系统操作菜单]] |
| kb-query | 领域精准问答 | 问、怎么、什么是、区别、对比 | Skill: kb-query | 直读 SKILL.md+命令索引（见 ops/hermes/Hermes-命令索引.md）：结构化检索（index→T层路由→规则文件） | Skill: kb-query | [[ops/rules/知识库运维规范]] |
| kb-health | 健康度快照 | health、健康、打分、怎么样 | Skill: kb-health | 直读 SKILL.md+命令索引（见 ops/hermes/Hermes-命令索引.md）：H1 系统健康度（已并入 /check） | Skill: kb-health | [[ops/rules/知识库检查体系]] |
| kb-dedup | 去重/查重 | 去重、重复、查重、dedup | Skill: kb-dedup | 直读 SKILL.md+命令索引（见 ops/hermes/Hermes-命令索引.md）：check-links.py --mode broken/index（已并入 /check） | Skill: kb-dedup | [[ops/rules/知识库检查体系]] |
| kb-refresh | 刷新过时内容 | refresh、刷新、过时、更新 | Skill: kb-refresh | 直读 SKILL.md+命令索引（见 ops/hermes/Hermes-命令索引.md）：H2+H5 过时检测（已并入 /check） | Skill: kb-refresh | [[ops/rules/知识库检查体系]] |
| kb-promote | 规则升层 | promote、升级、升层、晋升 | Skill: kb-promote | 直读 SKILL.md+命令索引（见 ops/hermes/Hermes-命令索引.md）：R→G 升层（已并入 /check --deep） | Skill: kb-promote | [[ops/rules/版本管理规范]] |
| kb-enrich | 富化/补标签 | enrich、富化、补全标签、补充元数据、打标签 | Skill: kb-enrich | 直读 SKILL.md+命令索引（见 ops/hermes/Hermes-命令索引.md）：LLM 读文章补 tags/summary/pt_phase | Skill: kb-enrich | [[ops/rules/核心操作流程]] |
| kb-session-close | 会话收尾 | 结束、关闭、再见、不记了、今天就这样 | Skill: kb-session-close | 直读 SKILL.md+命令索引（见 ops/hermes/Hermes-命令索引.md）：回溯评价→写入 sessions→检查正反模式 | Skill: kb-session-close | [[ops/rules/会话收尾检查]] |
| kb-curator | 技能化/封装 | 技能化、封装、curator、管家 | Skill: kb-curator | 直读 SKILL.md+命令索引（见 ops/hermes/Hermes-命令索引.md）：LLM 按 [[ops/rules/技能化流程]] 执行 | Skill: kb-curator | [[ops/rules/技能化流程]] |

## 表 B · 外部领域 skill（61 条，Claude/Codex 原生）

> 三 agent 原生加载，Hermes 直读 SKILL.md，纯流程型无需命令即完整。本表不重复维护其 description。本表价值：①跨 agent 判断任务归属；②关键词调度与完整性索引。Claude/Codex 列统一为「原生」，不再逐条列出。

### B1 工程/开发类（22 条）

| skill | 触发场景 | 关键词 |
|---|---|---|
| brainstorming | 任何创造性工作前（功能/组件/小说构思）的意图与设计探索 | 设计、方案、架构、新功能、功能开发、构思、brainstorm |
| writing-plans | 有 spec/需求后写多步实施计划 | 实施计划、task 拆分、plan、计划 |
| subagent-driven-development | 按实施计划逐 task 用独立 agent 实现 | 按 plan 实现、逐 task、执行计划、subagent |
| executing-plans | 在独立会话执行已写好的实施计划 | 执行计划、跑 plan |
| prd | 新功能的产品需求文档 | PRD、需求文档、产品需求 |
| ralph | PRD 转 ralph.json 给 Ralph agent 系统 | ralph、prd.json |
| systematic-debugging | 遇到 bug/报错/意外行为先系统排查 | 调试、排查、bug、报错、根因 |
| test-driven-development | 实现功能前先写测试 | TDD、先写测试、测试驱动 |
| verification-before-completion | 声称「完成/修好」前先验证 | 验证、确认有效、跑一下、通过 |
| requesting-code-review | 完成任务/大功能/合并前请求审查 | 请求审查、code review、review |
| receiving-code-review | 收到审查反馈后、实施建议前 | 接收审查、处理 review 意见 |
| finishing-a-development-branch | 实现完成测试通过后决定分支去留 | 完成分支、合并、收尾 branch |
| using-git-worktrees | 需要隔离工作区的功能开发 | worktree、隔离开发、分支隔离 |
| dispatching-parallel-agents | 2+ 无共享状态的独立任务并行 | 并行、分发 agent、多任务并行 |
| planning-with-files | 复杂任务的文件式规划跟踪 | 文件规划、Manus 风格、任务跟踪 |
| planning-with-files-ar | planning-with-files 阿拉伯语变体 | 文件规划、阿拉伯语、任务跟踪 |
| planning-with-files-de | planning-with-files 德语变体 | 文件规划、德语、任务跟踪 |
| planning-with-files-es | planning-with-files 西班牙语变体 | 文件规划、西班牙语、任务跟踪 |
| planning-with-files-zh | planning-with-files 中文变体 | 文件规划、中文、任务跟踪 |
| planning-with-files-zht | planning-with-files 繁体中文变体 | 文件规划、繁体中文、任务跟踪 |
| using-superpowers | 会话开始建立找/用 skill 的方式 | superpowers、技能使用引导 |
| writing-skills | 创建/编辑/验证 skill | 写 skill、创建技能、编辑技能 |

### B2 创作/小说类（34 条）

| skill | 触发场景 | 关键词 |
|---|---|---|
| story-idea-generator | 碰撞两个元素生成故事点子 | 故事点子、灵感、创意、collide |
| scene-idea-generator | 碰撞元素生成场景点子 | 场景点子、场景灵感 |
| logline-generator | 生成 4-7 个故事一句话梗概 | logline、梗概、一句话简介 |
| getting-started-guide | 新小说项目起步七步引导 | 新项目、开新书、起步 |
| novel-writer-workflow-guide | 组织长篇小说写作流程 | 写作流程、长篇、组织 |
| fantasy-world-building | 奇幻魔法体系/世界观构建 | 奇幻、魔法、世界观、fantasy |
| mystery-novel-conventions | 悬疑/侦探/犯罪题材规范 | 悬疑、侦探、犯罪、mystery |
| romance-novel-conventions | 爱情/情感题材规范 | 言情、爱情、情感、romance |
| setting-detector | 自动探测故事设定（题材/时代/主题） | 设定探测、题材、时代背景 |
| style-detector | 探测写作风格需求并加载指南 | 风格探测、文风、口语 |
| requirement-detector | 探测写作规范需求并加载文档 | 规范探测、AI味 |
| character-analysis | 用结构化模板分析角色 | 角色分析、人物分析 |
| character-abstraction | 从小说抽取角色要素（动作/台词/描写） | 角色抽象、人物要素 |
| fiction-abstraction | 从小说抽取段落/对话/情节/场景 | 小说抽象、情节要素 |
| scene-writer | 从场景大纲写完整散文场景 | 写场景、场景正文 |
| scene-brief | 生成单场景自包含简报 | 场景简报、场景上下文 |
| scene-framing | 生成场景框架文档（四类卡片） | 场景框架、卡片 |
| scene-structure-techniques | 场景结构/章节内容规划 | 场景结构、章节规划、sequel |
| scene-audit | 审计已写场景是否符合大纲 | 场景审计、一致性 |
| prose-producer | 编排完整场景草稿 | 场景草稿、生成正文 |
| literary-revision | 按特定文学风格改写散文 | 文学润色、改写、文风 |
| voice-revision | 按特定角色口吻改写 | 角色口吻、声音改写 |
| natural-dialogue-techniques | 写对话场景/角色对话 | 对话、台词、对白 |
| black-book | 把场景拆成结构化 blob 序列 | black book、blob 拆解 |
| stratguide-scribe | 用游戏攻略体拆解场景 | 攻略体、stratguide |
| story-collab | 反复访谈用户敲定故事设定 | 故事访谈、collab、追问 |
| story-consistency-monitor | 章节写作时检查角色/规则一致性 | 一致性检查、角色行为、世界规则 |
| forgotten-elements-reminder | 提醒被遗忘的故事要素 | 遗忘要素、伏笔、提醒 |
| folklore-generator | 为物品/地点生成民俗传说 | 民俗、传说、folklore |
| ruthless-critique | 给出 5-8 条犀利批评 | 犀利批评、critique、毒舌 |
| back-translate | 场景经外语回译检验 | 回译、telephone、检验 |
| humanizer-zh | 中文去 AI 味 | AI味、去机器味、humanize |
| pre-write-checklist | 章节写作前 9 项强制清单 | 写前清单、pre-write |
| webnovel-writing | 中文小说简介→规划/起稿/续写/改写 | 网文、起稿、续写、改写 |

### B3 工具类（2 条）

| skill | 触发场景 | 关键词 |
|---|---|---|
| image-pixelation | 图片转像素画/8-bit 风格 | 像素化、像素画、8-bit、retro |
| image-utilities | 生成/操作图片（色阶、颜色） | 图片生成、shades of、颜色 |

### B4 番茄小说类（2 条）

| skill | 触发场景 | 关键词 |
|---|---|---|
| fanqie-rank | 获取番茄小说榜单数据 | 番茄榜单、新书榜、阅读榜 |
| fanqie-sensitive-detector | 番茄小说敏感词检测 | 敏感词、政治、色情、暴力检测 |

### B5 求职类（1 条）

| skill | 触发场景 | 关键词 |
|---|---|---|
| resume-skills | 简历生成与 JD 匹配工作流（含 7 子技能） | 简历、JD、求职、面试、ATS |
