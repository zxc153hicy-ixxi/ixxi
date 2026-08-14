---
tags: [规则]
status: active
confidence: high
summary: Ingest 10步流水线（0→9）——从原始资料到结构化知识的完整提炼流程
created: 2026-06-24
updated: 2026-07-20
---

# Ingest完整流程

> **前置条件**：入站资料已通过 [[文档转Markdown工具选型]] 转换为 .md 并归档至 `.inbox/converted/`。0KB .md（扫描件/图片 PDF）需先走 OCR 兜底再进入 Ingest。

## 约束

1. 必须严格按 0→9 顺序执行，不可跳步
2. 步骤 3.5（对话确认）为硬闸门：medium/low 置信度内容必须人类确认后才激活
3. 步骤 8（git commit）每次 Ingest 后必须执行
4. 步骤 9（变更摘要）必须输出固定格式
5. queue.md 中已处理条目必须标记 `[x]`
6. 视频文件（.mp4/.mkv/.avi/.mov/.webm/.flv/.wmv/.ts）由 video2text.py 转录为文本后再走正常 Ingest 流程
7. **转换产物必须先入 `.inbox/converted/`**：所有 PDF/docx → .md 转换的输出必须放入 `.inbox/converted/`，禁止直接从 `raw/inbox/` 或转换工具输出目录跳转入 `knowledge/`。Ingest 流程只从 `.inbox/converted/` 读取待处理 .md。跳过此目录直接拷入 knowledge/ 会导致缺失 YAML 元数据、交叉引用、索引更新等步骤

## 视频入库流程（Step 0 子步骤）

Step 0 扫描到视频文件时：
1. LLM 提示用户：「检测到 N 个视频文件，是否转录为文本？」
2. 用户确认后，LLM 执行 `python engine/tools/video2text.py <文件> --move-to-inbox`
3. 转录完成后，`.txt` 文件自动落入 `.inbox/converted/`，原视频移入 `.inbox/sources/`
4. 继续正常 Ingest 流程（Step 1→读取转换后的 txt）

转录耗时参考（RTX 4060 + large-v3）：1 小时视频 ≈ 1-1.5 小时完整转录。建议睡前跑，起床收。

### 断点续传

视频转录支持中断后从断点继续，无需重头开始：

| 操作 | 命令 |
|------|------|
| 查看任务状态 | `python engine/tools/video2text.py --status` |
| 续传（自动检测断点） | `python engine/tools/video2text.py <文件> --resume` |
| 批量续传 | `python engine/tools/video2text.py --batch <目录> --resume` |
| 忽略断点重来 | 加 `--force-restart` |

断点保存间隔：每 30 秒音频时长。中断后输出文件保留已转录部分，续传时从断点位置截取剩余音频继续转录，追加到同一文件。

**下次会话启动**：若 `.inbox/_video_state.json` 中有 paused/processing 状态的任务，LLM 主动提示「上次有 N 个视频转录未完成，是否继续？」

## OCR 兜底检查（Step 0 子步骤）

Step 0 扫描 `.inbox/converted/` 时，若发现 0KB 的 .md 文件：

1. 统计数量，输出提示：「📋 检测到 N 个 0KB .md文件（扫描件/图片 PDF 转换失败），需 OCR 兜底。」
2. 按文档语言提示工具选择：
   - 中文 PDF → `python engine/scripts/batch-mineru.py --dry-run`（MinerU GPU OCR，实测 ~8分/文件）
   - 英文 PDF → `python engine/scripts/batch-ocr.py --dry-run`（marker OCR）
3. 用户确认后执行 OCR，完成后继续 Ingest。
4. 用户回复「跳过」→ 0KB 文件标记 `[!]` 跳过，不阻塞 Ingest。
5. 无 0KB 文件 → 静默跳过。

> OCR 脚本共用 `engine/scripts/ocr-sources.json` 映射配置，详见 [[文档转Markdown工具选型#OCR 兜底（扫描件/图片型 PDF）]]。

## 正例

> LLM 执行 `/ingest` → 按 0-8 步完整走完 → 输出变更摘要 → git commit → queue 标记完成

## 反例

> 只读了 raw 就写 wiki，跳过冲突扫描（步骤 2）→ 可能引入矛盾而不自知
> Ingest 完成后忘记 git commit → 数据无版本保护

## 例外

### 例外1：批量模式
- 触发条件：>30 天未 Ingest
- 例外行为：按时间倒序分批处理，每批 ≤10 条，每批输出进度
- 标志动作：回复中标注 `[批量模式: 第N批/共M批]`

---

## 步骤 0-9 速查表

| 步骤 | 名称 | 操作 | 失败处理 |
|:---:|------|------|------|
| 0 | 预检 | ①扫描queue+.inbox/converted/+raw/inbox/+notes+**视频文件**；②跑scan-sensitive.sh敏感扫描；③上次Lint>7天→提醒；④非.md+0字节→标记[!]跳过；⑤视频文件→提示执行 `python engine/tools/video2text.py <文件> --move-to-inbox`；⑥扫描 `.inbox/converted/` 中 0KB .md→提示 OCR 兜底（[[#OCR 兜底检查（Step 0 子步骤）]]）；⑦新入库文件跑 `python engine/scripts/check-ocr-quality.py --fix --mark-only` 自动修复死图片引用+标记质量问题；⑧跑 `python engine/scripts/check-ocr-quality.py --clean --path <入库目录>` 清除 OCR 碎片文件及 `![](_page_*` 引用；⑨扫描 `knowledge/learning/` 下 `tags: [学习资料]` 且无 `auto_enriched: true` 的漏网文章 → 提示「📋 发现 N 篇未富化文章，是否在本轮 Ingest 中补全？」 | 失效标记[!]跳过；敏感命中→阻断；Lint过期→提醒；视频→提示手动转录；0KB→提示 OCR；质量→自动修复+标记；碎片→自动清除；漏网富化→提示补全 |
| 1 | 读取 | 逐条读 raw，提取核心主张 | 文件不可读→跳过+记录到 failed.log；编码异常→尝试 UTF-8→GBK→latin-1 降级 |
| 1.5 | 本地解析 | raw/local/→拆分→写入 sessions/ | 移至 _failed/ |
| 2 | 冲突+去重扫描 | 按 scene+type 分桶比对（冲突检测+重复检测）。冲突：高→暂停/中→继续+标注/低→不告警。重复：高→自动建议合并路径+log/中→标注等确认/低→不告警 | 高置信度暂停；中继续+标注；低置信度不告警 |
| 3 | 写入 | ①新建页按 confidence→status；②必设 `type` 字段（`literature` 摘录 / `permanent` 自己的理解），默认 `literature`；③自动填入 `updated: YYYY-MM-DD`；④写入后调用 `/kb:enrich <文件路径>` 自动补全领域标签+内容摘要（详见 [[#步骤 3.6：元数据补全]]） | 重试一次；仍失败 log+跳过 |
| 3.5 | 对话确认 | 逐条展示 medium/low 内容 | 确认→active+回补引用；修改→重写后重新展示；跳过/无回应→保留 draft |
| 4 | 交叉引用 | active 页面建立双向链接；**硬性要求：≥1 条出链**，不达标→降为 draft + 标注 `[缺链接]` | 目标页不存在→跳过该引用+记录到 broken-refs.log；≥10%引用失败→暂停+列出失败原因；<10%→继续+标注 |
| 5 | 校验 | YAML 格式 + scene 一致性 | 格式错误自动修复 |
| 6 | 更新索引 | index.md 追加 `- [[路径]] —— summary` | 冲突→临时文件 |
| 7 | 版本清理检查 | 运行 `python engine/scripts/cleanup-versions.py --json`。发现有可清理旧版→输出提醒：「📋 本次 Ingest 发现 N 个可清理旧版（K 条版本链）。运行 \`python engine/scripts/cleanup-versions.py\` 查看详情，回复「现在清理」立即执行，或「跳过」忽略。」无待删→静默跳过。LLM 不自动执行删除。 | 脚本缺失或异常→输出警告但**不阻断** Ingest |
| 8 | 提交 | queue[x]→log→git commit | git失败→人工介入；检测index.lock残留→提示清理 |
| 9 | 变更摘要 | `处理N条(其中.inbox M条, raw/inbox K条) \| 新建X(其中draft A条) \| 更新Y(其中under-review B条) \| 冲突Z \| 富化W(其中跳过S) \| 可清理旧版V` | 摘要格式校验失败→手动填充；写入 log.md 失败→输出到 stdout |

---

## 字段约定

### `type` 字段（Step 3 必设）

区分知识来源，防止「别人的话」和「自己的理解」混在一起：

| 值 | 含义 | 示例 |
|---|---|---|
| `literature` | 摘录/引用的外部知识，未用自己的话重写 | 文章摘要、工具文档、他人观点 |
| `permanent` | 用自己的话重写后的理解，可独立成文 | 你对某个概念的理解、方法论总结 |

默认值为 `literature`。用户明确说「这是我的理解」「我自己总结的」等，才设为 `permanent`。

### `updated` 字段（Step 3 自动填入）

每次 Ingest 写入/修改 wiki 页面时，自动填入或更新 `updated: YYYY-MM-DD`。手动编辑 wiki 页面时用户自行更新。此字段为 Lint #12（内容过时检测）的数据基础。

---

## 步骤 7：版本清理检查

**时机**：在步骤 6（更新索引）之后、步骤 8（git commit）之前执行。

**操作**：
1. 运行 `python engine/scripts/cleanup-versions.py --json`
2. 解析 JSON 输出中的 `total_delete` 字段
3. 若 `total_delete > 0`：输出提醒文本
4. 若 `total_delete == 0` 或脚本异常：静默跳过

**提醒格式**：
```
📋 本次 Ingest 发现 N 个可清理旧版（K 条版本链）。
   运行 `python engine/scripts/cleanup-versions.py` 查看详情。
   回复「现在清理」立即执行，或「跳过」忽略。
```

**LLM 响应规则**：
- 用户回复「现在清理」→ 调用 `python engine/scripts/cleanup-versions.py --execute`，回显结果
- 用户回复「跳过」→ 记录到 log，不清理
- 用户不回复 → 不阻塞 Ingest 完成，仅作提醒
- LLM 严禁在用户未确认的情况下自动执行删除

**失败处理**：
- 脚本文件不存在 → 输出 `[WARN] cleanup-versions.py 未找到，跳过版本检查`
- Python 执行异常 → 输出 `[WARN] 版本检查异常: <error>`，**不阻断** Ingest

---

## 步骤 3.6：元数据补全

**时机**：步骤 3（写入）完成后、步骤 4（交叉引用）之前执行。**此步骤不可跳过。**

**操作**：对刚写入的页面调用 `/kb:enrich <文件路径>`，自动补全：

| 字段 | 来源 | 说明 |
|------|------|------|
| `tags` | `engine/config/tag-taxonomy.yaml` 中对应领域的 `subdomains` + `content_types` | 替换泛化标签 `[学习资料]` 为具体领域标签 |
| `summary` | LLM 分析正文后生成 | 1-2 句中文概要，替换重复文件名的原始值 |
| `pt_phase` | `tag-taxonomy.yaml` 中对应领域的 `phases` | 仅渗透测试相关文章才有，如 `[信息收集, 漏洞扫描]` |
| `auto_enriched` | 写入 `true` | 标记此文章由 Ingest 自动富化，待人工审核 |

**执行规则**：
1. 领域由文件路径自动推断（`knowledge/learning/网络安全/` → `网络安全`），无需 LLM 猜测
2. 已有高质量 tags 的页面保留原值，只补充 summary
3. 非渗透类文章不生成 `pt_phase`
4. 写入后标注 `auto_enriched: true`，供定期扫描发现待审核文章
5. Ingest 完成后回显 `🔖 已富化 N 篇，其中 M 篇待人工审核`，并追加一行 `[Ingest] 标签打得准/不准？`
6. 非破坏性操作，失败不阻断 Ingest

**硬闸门（V4.3 新增）**：步骤 3 写入后、步骤 4 交叉引用前，必须验证：

1. 本次写入的文章中，所有 `tags: [学习资料]` 的文章必须有 `auto_enriched: true`
2. 若发现 `tags: [学习资料]` 但无 `auto_enriched: true` → enrich 被跳过 → **暂停 Ingest，回退到步骤 3.6 重新执行**
3. 验证通过后才可进入步骤 4

此验证为硬闸门，不可跳过。失败处理：重试 enrich 一次，仍失败 → 文章保持 draft + 标注 `[缺富化]`，**不阻断其他文章继续**。

**关联**：
- 标签体系配置：`engine/config/tag-taxonomy.yaml`
- Skill 实现：`core/skills/enrich/SKILL.md`
- 批量模式：`/kb:enrich --batch <目录>` 可对存量文章批量补全
