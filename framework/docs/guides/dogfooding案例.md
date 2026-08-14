---
tags: [指南, dogfooding, 模拟案例]
status: active
confidence: low
summary: 内部 dogfooding 使用案例——模拟 3-5 个真实场景的使用过程，明确标注为模拟、非真实 3-6 月积累；每个案例记录使用中暴露的真实问题与反馈给 framework 的改进点
created: 2026-08-14
---

# 内部 dogfooding 使用案例（模拟）

> **重要声明：本文档全部案例为「模拟案例」，非真实 3-6 月使用积累。**
> 背景：框架尚未经过真实长时间使用（智谱风险 4.4「无真实使用时间」），按实施指示以「简单模拟」方式补齐使用案例文档。内容虚构但场景覆盖作者真实领域（知识库管理 / 学习 / 小说创作 / 求职），每个案例的「发现问题」为可倒逼 framework 改进的合理推演，非实测数据。
> 目的：为演化机制（场景注册 + `ixxi stats --unused`）提供可核对的演示输入，并在正式使用前暴露可预见的框架缺口。

---

## 案例对照表

| # | 场景 | 主要 capability | 核心发现的问题 | 改进点 |
|---|------|------|------|------|
| 1 | 知识库日常管理 | kb-ingest + kb-lint | 批量 ingest 的逐条确认疲劳；lint 技能化候选误报 | 批量确认模式；候选清单人工复核门 |
| 2 | 学习笔记整理 | kb-ingest + kb-enrich + kb-query | 新领域自动注册的 subdomains 质量差；检索方向偏需修正 tags | enrich 自动注册需人工审核；_synonyms 按场景细化 |
| 3 | 小说创作 | kb-ingest + 场景注册 | 场景 domain 词表缺「小说创作」被阻断；创作类内容冲突判定失准 | 场景化 content_types；虚构类场景独立冲突判定 |
| 4 | 求职 | kb-ingest + 个人 skill 编写 + kb-query | 个人 skill 漏登记；面试题检索频繁 L2 降级；简历多版本堆积 | skill 建成即登记护栏；面试题领域细化 |
| 5 | 跨场景演化 | `ixxi stats --unused` + kb-curator | 遥测缺失导致无法决策；capability.json last_used 不更新 | 遥测写入纪律 hook；归档需人工确认 |

---

## 案例 1：知识库日常管理（日常 ingest + lint 体检）

### 场景名与描述

**知识库日常管理**。作者长期使用知识库沉淀笔记，每日把零散记录（会议笔记、临时想法、工具用法）丢进 raw/inbox/，周期性跑 ingest 入库 + lint 体检。核心诉求是「内容能进来、库别烂」。

### 使用的 capability

- `kb-ingest`（入库主流程）
- `kb-lint`（健康体检）

### 使用过程（模拟）

1. 把当天 3 条零散笔记丢进 `raw/inbox/`（会议要点、一条工具用法、一条临时想法）。
2. 执行 `/ingest`。步骤 0 预检发现队列非空，触发敏感扫描（扫到一条含测试 token 的笔记 → 标注 [敏感] 脱敏后继续）。
3. 步骤 1-3 逐条提炼：2 条置信度 high 直接写入 `knowledge/`；1 条 medium 走步骤 3.5 对话确认后激活。
4. 期间间隔了 40 天没跑 ingest，触发批量模式：`[批量模式: 第 1 批/共 2 批]`，每批 10 条。
5. 跑 `/lint` 日常检查（7 项），输出健康度 82（≥70 健康），行动项 2 条：1 条 YAML 格式错误（自动修复）、1 条技能化候选。
6. 每月跑一次 `/lint --full` 深度检查，核对页面矛盾、孤立页面、内容过时。

### 发现的问题（模拟）

- **批量模式下 medium 置信度逐条确认造成确认疲劳**。连续两批共 20 条，其中 7 条 medium 要一条条展示确认，中途用户逐渐「无脑回车」。这违背了步骤 3.5「人类确认」的本意——确认变成机械动作后，等于失去了把关价值。真实使用 3-6 个月必然触发。
- **lint 的「技能化候选」误报**。某次 lint 把「每周归档旧笔记」这种低频操作也列入技能化候选清单，但该操作半年不到 2 次，封装成 skill 纯属浪费（curator 自适应阈值「刚起步 7 天 ≥2 次」在冷启动阶段口径过宽）。
- **git commit 硬闸门（ingest 步骤 7）与 lint 自动修复冲突**。ingest 刚 commit 完，lint 又自动修了一个 YAML 格式错误，产生一个只有 1 行变更的孤立 commit，污染提交历史。

### 反馈给 framework 的改进点

1. **批量确认模式**：批量 ingest 时 medium 内容提供「逐条确认 / 批次整体确认 / 默认 draft 落库后再审」三种模式，避免确认疲劳架空硬闸门。
2. **技能化候选需人工复核门**：lint 输出的候选清单应附操作频次与历史记录，且冷启动阈值下候选需二次人工确认才进 curator 生成流程，降低误报。
3. **ingest 与 lint 的 commit 合并策略**：紧邻的 ingest commit + lint 自动修复应合并为一次提交，或 lint 只产出修复建议不自动 commit。

---

## 案例 2：学习笔记整理（学习资料入库 + query 检索）

### 场景名与描述

**学习笔记整理**。作者学习「大语言模型」等新领域，把书籍笔记、文章摘录、课程材料入库，之后通过 kb-query 检索回顾。核心诉求是「学过的东西能想起来、问得出」。

### 使用的 capability

- `kb-ingest`（学习资料入库）
- `kb-enrich`（元数据补全 / 打标签）
- `kb-query`（知识检索）

### 使用过程（模拟）

1. 把一本 LLM 书籍的读书笔记（约 30 页 md）放进 `raw/inbox/`，跑 `/ingest` 提炼成 15 条 wiki 条目。
2. 入库后发现全部文章 tags 还是泛化的 `[学习资料]`，执行 `/enrich --scan-missed` 批量补全。
3. 步骤 2 确定领域时，`engine/config/tag-taxonomy.yaml` 里没有「大语言模型」这个 domain → 触发 enrich 的新领域引导，自动注册 domain，并从文章标题/正文提取 subdomains。
4. 用 kb-query 提问「注意力机制和 Transformer 的关系」，跑 L1 检索。
5. 回答末尾按 kb-query 反馈模板评价「部分准确」，走反馈处理情况 A（tags 不准）修正涉事文章 tags，并检查 taxonomy 是否缺 subdomain。

### 发现的问题（模拟）

- **enrich 自动注册新领域时 subdomains 提取质量差**。新领域引导自动从文章标题和正文前 200 行提取高频词，结果注册出的 subdomains 是「attention」「transformer」「GPT 文章」这类中英混杂的碎片词，与既有标签体系风格不一致，后续 kb-query 按这些词过滤会漏检。真实使用 3 个月导入多个新领域时必然暴露。
- **kb-query 检索方向偏 + tags 修正链路较长**。问「注意力机制」时 L1 命中 0 → L2 降级到全局全文搜索 → 找到的是一批入门科普而不是核心条目。反馈「部分准确」后走情况 A：定位文章、改 tags、查 taxonomy 缺词、再 grep 同域文章核对是否连锁需要修正——单次修正平均多花 10 分钟。
- **summary 与文件名重复**。部分条目 frontmatter 的 summary 仍是文件名照抄（`# 注意力机制.md` → summary 也是「注意力机制」），enrich 依赖人工触发 `--scan-missed` 才能发现，且「已自动富化但未人工审核」清单（`auto_enriched` 标记）缺乏自动提醒。

### 反馈给 framework 的改进点

1. **enrich 自动注册新领域需人工审核闸门**：自动生成的 subdomains 只能作为候选，必须回显给用户确认后才写入 taxonomy；或提供「碎片词清洗」规则（过滤英文停用词、规范大小写、要求 2-4 字中文词优先）。
2. **_synonyms 应按场景细化并有沉淀入口**：kb-query 每次 L2/L3 降级都应记录到 `kb-query-log.jsonl`，且把「检索词 → 应命中 subdomain」的映射自动沉淀进 `_synonyms`，让检索质量随使用自动变好（当前依赖人工维护）。
3. **enrich 漏网扫描应纳入 lint 周期**：`auto_enriched: true` 未人工审核的清单由 `/lint` 日常检查提示，而不是等用户手动跑 `--scan-missed`。

---

## 案例 3：小说创作（世界观设定入库 + 场景注册）

### 场景名与描述

**小说创作**。作者在写长篇（如源质挽歌类世界观小说），需要把世界观设定（地理/历史/力量体系）、人物卡、章节大纲沉淀成可复用素材库，写新章节时能查回旧设定保持一致。核心诉求是「设定不冲突、不丢失」。

### 使用的 capability

- `kb-ingest`（设定素材入库）
- 场景注册（`personal/scene-registry.md` 登记「小说创作」场景）

### 使用过程（模拟）

1. 在 `personal/scene-registry.md` 追加一行：`| S3 | 小说创作 | active | 世界观设定/人物/章节大纲沉淀 | personal/knowledge/novel | 2026-08-14 |`。
2. 执行 `check-scene-domain` 校验该行的 domain 值。
3. 把世界观设定稿、人物卡丢进 `raw/inbox/`，跑 `/ingest` 入库，按 scene「小说创作」+ type 分桶。
4. 定期把章节创作过程中的新增设定增量入库，并与已有设定比对一致性。
5. 写新章节前用 kb-query 检索「某角色之前设定的能力边界」，防止设定漂移。

### 发现的问题（模拟）

- **场景注册被 domain 受控词表阻断**。`check-scene-domain` 校验「小说创作」行的 domain 值，但 `tag-taxonomy.yaml` 的受控词表里没有这个 domain → 越界词阻断提示补登。补登后 `_content_types`（书籍/教程/文章/笔记…）里也没有适合「设定/人物卡/章节大纲」的内容类型，全局默认类型套在创作素材上语义别扭。
- **创作类内容与普通笔记的冲突判定冲突**。ingest 步骤 2 按 scene+type 分桶比对去重，但创作设定常以「不同版本并存」演进（同一角色能力先弱后强、大纲多版迭代）——被误判为「重复/冲突」而暂停，打断创作流。真实创作场景必然高频触发。
- **lint 把创作草稿误判为 draft 堆积**。章节草稿、废弃大纲落在知识库目录里，lint 的「draft 堆积 >30 天告警」把它们当成待处理草稿误报，需要人工每条说明「这是素材不是待办」。

### 反馈给 framework 的改进点

1. **场景化 content_types**：tag-taxonomy 的 domain 定义允许覆盖全局 `_content_types`（schema 已预留 `content_types` 字段），但注册引导未主动提示；应在新领域引导中根据场景类型推荐内容类型（如「设定/人物卡/大纲」），避免全局默认套用。
2. **虚构创作场景的冲突判定需降敏**：scene 标记为「创作」时，ingest 步骤 2 的重复/冲突判定应改为「版本并存默认不暂停，仅标注 diff」，把「去重」的硬闸门放宽为「提示」，由作者决定是否合并。
3. **lint 的 draft 判定需按 scene 区分**：创作场景下的 `draft` 页面不应计入「draft 堆积」检查项（或单独设创作素材阈值），避免把素材当垃圾误报。

---

## 案例 4：求职（简历构建场景 + 个人 skill 编写）

### 场景名与描述

**求职准备**。作者求职期间，把 JD、项目经历、技术面试题沉淀进知识库，构建一个「面试资料库」，并写一个个人 skill 封装「面试前复习」流程。核心诉求是「面试前快速复习、回答有据」。

### 使用的 capability

- `kb-ingest`（求职资料入库）
- 个人 skill 编写（`personal/.claude/skills/personal/`，非 framework skill）
- `kb-query`（面试题检索）

### 使用过程（模拟）

1. 建求职场景目录 `personal/knowledge/career/`，把 JD、项目经历、刷题记录丢进 `raw/inbox/`，跑 `/ingest` 入库（`_content_types` 里有「面试题」类型，正好覆盖）。
2. 写个人 skill `my-interview-prep`（frontmatter `name` + `description` + 流程：读目标 JD → 拉取该项目/技术栈的已沉淀知识点 → kb-query 检索关联面试题 → 生成复习清单）。
3. 跑 `sync-skills-to-claude.py` 让 skill 被加载。
4. 面试前用 kb-query 提问「简述 JVM 内存模型」，走 L1/L2 检索。
5. 简历改版多次（V1/V2/V3），每次把新版本作为新笔记入库。

### 发现的问题（模拟）

- **个人 skill 建成后漏登记到 activation.md**。`sync-skills-to-claude.py` 把 skill 同步进 `.claude/skills/` 了，但 `activation.md`（操作入口注册表）没登记——按「工具建成即登记」护栏，`check-script-refs` 跑一遍提示漏登记。对真实使用者，「登记」这一步是纯额外负担，极易跳过。
- **「面试题」检索频繁走 L2 降级**。`_content_types` 有「面试题」但 tag-taxonomy 的领域 subdomains 没有按面试维度划分（如「JVM/并发/网络」），kb-query 问具体面试题时经常 L1 零命中 → L2 全文搜索 → 命中太泛。
- **简历多版本在库内堆积，dedup 判定两难**。V1/V2/V3 是同人简历，内容相似度高被 dedup 列为疑似重复；但它们是有意保留的历史版本，不是重复。真实求职场景「版本化 + 去重」的边界模糊，容易误杀或误留。

### 反馈给 framework 的改进点

1. **skill 建成即登记需半自动化**：`sync-skills-to-claude.py` 同步完成后直接追加一行到 `activation.md`（或在同步输出里给出一条可复制的登记行），让「登记」从记忆负担变成复制粘贴，护栏才真正成立。
2. **面试领域需独立 taxonomy 维度**：求职场景的 subdomains 应按「技术栈/主题」划分（JVM、并发、网络…），并让 kb-query 对 `面试题` content_type 优先检索，减少 L2 降级。
3. **版本化内容与 dedup 的边界规则**：带版本标识（如文件名含 `V\d+` 或 frontmatter `version_of`）的页面应跳过 dedup 疑似重复判定，交由 kb-compact 按版本管理规范处理。

---

## 案例 5：跨场景演化（`ixxi stats --unused` 发现未触发的 capability → 归档）

### 场景名与描述

**跨场景演化**。作者用 ixxi 数月后，跑演化命令检查「哪些能力一直没用」，识别可归档的 capability，避免框架膨胀成「注册了一堆但都用不上」。核心诉求是「能力库与真实使用对齐」。

### 使用的 capability

- `ixxi stats --unused`（未触发报告，走 `engine/scripts/stats-unused.py`）
- `kb-curator`（归档流程，自动回落冷启动参数）

### 使用过程（模拟）

1. 跑 `python framework/engine/scripts/stats-unused.py --days 90`。
2. 输出显示若干 capability 在 90 天内未触发：`kb-dedup`（最后触发距今 96 天）、`kb-refresh`（从未触发）、`kb-conflict`（最后触发距今 88 天），建议「归档候选」；`kb-compact`（距今 35 天）建议「保留」。
3. 对照 `raw/sessions/skill-usage.json` 遥测，交叉确认这些 capability 的触发记录确实为空。
4. 逐个人工裁决：`kb-refresh` 归档（从未用过、判据是内容过时刷新，可由 lint 覆盖）；`kb-dedup` 保留（低频但重要保障，usage ≠ value）。
5. 对归档项走 curator 归档流程：移至 `.claude/skills/_archived/`，确认归档后 skill 数未骤降、无需回落冷启动参数。

### 发现的问题（模拟）

- **遥测缺失让演化决策悬空**。早期使用没有可靠写入 `raw/sessions/skill-usage.json`（curator 计数器依赖「每次执行可封装操作后自动更新」，但操作漏跑或不经过 curator 就无记录）→ `stats --unused` 提示「暂无遥测数据」，退化到 capability.json 的 `last_used` 兜底。
- **capability.json 的 `last_used`/`triggered` 字段常不更新**。`stats-unused.py` 的兜底逻辑依赖这些字段，但生成 capability.json 后很少有人回填 `last_used`，兜底信号不可靠 → 未触发报告在无遥测时基本是摆设。这是演化闭环空转的真实风险（MVP 边界文档里已标注「未触发报告不可延后 v2，否则演化闭环空转」，恰好印证）。
- **「未触发 ≠ 无价值」的裁决容易被忽略**。报告输出「建议：归档候选」是机器建议，但 `kb-dedup` 这类低频高保障能力若被机械归档，后续会出问题。stats 脚本只输出一句话「最终保留/归档由人工裁决」，但缺少把裁决结果回写（如确认归档后写回 `_archived` 标记）的闭环。

### 反馈给 framework 的改进点

1. **遥测写入纪律需 hook 强制**：capability 触发时应由 git pre-commit / hook 自动刷新 `skill-usage.json` 的 `count`/`last_seen`，而不是依赖「LLM 记得更新」——参照 `core/hooks/` 现有的机械强制护栏（版本检查、登记检查）补一条遥测检查。
2. **capability.json 兜底字段应允许默认无信号即「未触发」**：`stats-unused.py` 对无 `last_used`/`triggered` 的 capability 应给出「无信号，默认按未触发计」的显式标注，避免静默漏判。
3. **归档需人工确认 + 裁决结果回写闭环**：`stats --unused` 输出归档候选后，应引导用户逐个裁决并把结果写回（保留/归档），归档走 curator 归档流程（含冷启动回落保护），形成「报告 → 裁决 → 执行 → 回写」的完整闭环，而非报告即终点。

---

## 模拟案例的共性结论

以上 5 个模拟案例虽非真实积累，但共同指向框架在真实使用中最可能暴露的三类缺口：

1. **确认类硬闸门在批量/高频场景下失效**（案例 1、3）：批量确认疲劳、冲突判定过严、草稿误判——硬闸门需要随使用形态分级，不能一刀切。
2. **元数据与检索质量依赖人工维护**（案例 2、4）：新领域注册、_synonyms 沉淀、tags 修正链路长——需要更多「使用即自动沉淀」的机制，减少人工负担。
3. **演化闭环依赖遥测纪律**（案例 5）：无遥测 → stats 空转 → 演化决策悬空——遥测写入必须 hook 强制，未触发报告的「报告→裁决→回写」要成闭环。

这些结论可作为 v0.2 迭代的输入，但须经真实 3-6 月使用验证后才能确认优先级（本模拟仅作预判，不做实施依据）。

## 关联

- `framework/docs/guides/demo到真实迁移指南.md` —— 场景注册与 skill 编写的真实操作入口
- `framework/docs/guides/MVP边界.md` —— 未触发报告 v1 交付要求
- `framework/engine/scripts/stats-unused.py` —— 未触发报告实现
- `framework/engine/config/scene-registry-schema.md` —— 场景注册 schema
- `framework/engine/config/tag-taxonomy.yaml` —— domain 受控词表与 _synonyms
