---
name: kb-enrich
description: Use when the user says "enrich" "富化" "补全标签" "补充元数据" "打标签". Reads article content and supplements frontmatter fields (tags, summary, pt_phase) based on engine/config/tag-taxonomy.yaml.
version: 1.0.0
---

# /enrich —— 元数据自动补全

## 用途

分析知识库文章，自动补全 frontmatter 元数据：
- `tags` 从泛化的 `[学习资料]` 补全为具体领域标签
- `summary` 从重复文件名替换为真实内容概要
- 渗透测试相关文章追加 `pt_phase` 字段

## 用法

```
/enrich <文件路径>          # 单篇补全
/enrich --batch <目录>      # 批量补全（每批 8-12 篇并行）
/enrich --scan-missed       # 全目录扫描 tags:[学习资料] 残留文章，自动补富化
```

## 执行流程

### 1. 读取配置

读 `engine/config/tag-taxonomy.yaml`，获取当前标签体系。三个关键数据源：
- `domains.<key>.subdomains` —— 领域子标签枚举
- `domains.<key>.phases` —— 渗透测试阶段标签（仅网络安全等攻防领域有）
- 全局 `_content_types` + 领域级 `content_types` —— 内容类型标签

### 2. 确定领域

按优先级：
1. **路径推断**（零成本）：取文件路径的上级目录名，匹配 `tag-taxonomy.yaml` 中各 domain 的 `path_key`
2. **无匹配 → 触发领域注册引导**（见下方 [[#新领域引导]]）
3. **内容分析**（路径无法推断时兜底）：LLM 读正文判断属于哪个领域

### 新领域引导

当 `/enrich` 遇到 `path_key` 无法匹配的目录时，**自动执行**：

1. 取目录名作为 `label` 和 `path_key`
2. 扫描目录下所有文章的标题和前 200 行正文，提取高频关键词作为 `subdomains`（≤10 个）
3. 使用全局 `_content_types`
4. 将生成的 domain section 追加到 `engine/config/tag-taxonomy.yaml`
5. 一行告知用户「🆕 已自动注册新领域：<label>（<N> 个子标签）」
6. 继续执行 enrich 流程

### 3. 分析文章

读取全文（>500KB 只读前 5000 行），提取：

| 字段 | 逻辑 | 示例 |
|------|------|------|
| `subdomains` | 从领域的 `subdomains` 列表中选 1-3 个最匹配的 | `[Web安全, 渗透测试]` |
| `content_type` | 从 `_content_types` + 领域 `content_types` 中选 1 个 | `书籍` |
| `summary` | 1-2 句中文概要，说明文章**具体讲了什么**（非重复标题） | `系统讲解 SQL 注入原理、检测方法与防御方案，附带实战示例代码` |
| `pt_phase` | 仅当领域有 `phases` 且文章涉及渗透实战时，选 1-2 个阶段 | `[漏洞利用, 后渗透/提权]` |

### 4. 写入 frontmatter

在现有 YAML 中插入/更新以下字段：

```yaml
tags: [Web安全, 渗透测试, 书籍]
summary: 系统讲解 SQL 注入原理、检测方法与防御方案，附带实战示例代码
pt_phase: [漏洞利用]          # 可选，仅渗透相关
```

**规则**：
- `tags` 格式保持为 YAML 内联数组 `[tag1, tag2, tag3]`
- 不删除已有字段（`status`, `created`, `updated` 等）
- `summary` 替换原值（原值通常是重复的文件名）
- `pt_phase` 仅当匹配到渗透测试内容时才添加
- 如果已有高质量 tags（非 `[学习资料]`），保留并补充而非覆盖

### 5. 交叉引用

enrich 完成后自动执行。逻辑：

1. **收集本领域文章索引**：读当前文件所在目录（非递归）的 README.md 或索引页，获取同域文章列表
2. **tags 匹配**：grep 同域文章 frontmatter，找出与本篇共享 ≥1 个 `tags` 子标签的文章
3. **取 Top 3-5**：按共享标签数排序，取最相关的前 3-5 篇
4. **追加引用段**：在文章末尾追加 `## 相关文章` 段，格式：

```markdown
## 相关文章
- [[示例文章A]] —— 同属 <子标签1>、<子标签2>
- [[示例文章B]] —— 同属 <子标签1>、<标签>
- [[示例文章C]] —— 同属 <子标签1>
```

**规则**：
- 仅链接**已有富化 tags** 的文章（`[学习资料]` 的无用链接跳过）
- 不链接自身
- 如果文章已有 `## 相关文章` 段，替换而非追加
- 匹配不到相关文章时，不添加空段

### 6. 回显

```
/enrich 单篇输出：
  文件: knowledge/learning/网络安全/xxx.md
  tags: [学习资料] → [Web安全, 渗透测试, 书籍]
  summary: 原文件名 → 系统讲解 SQL 注入原理与防御方案
  pt_phase: +[漏洞利用]
```

## 边界条件

| 场景 | 处理 |
|------|------|
| 文件>500KB | 只读前 5000 行 + 标题 |
| 已有高质量 tags | 保留原 tags，只补 summary |
| 不匹配任何领域 | 只补 summary，不强行打领域标签 |
| 纯视频转录文本 | 读前 200 行判断主题 |
| frontmatter 格式损坏 | 报错退出，不修正文 |
| 领域无 phases | 不生成 pt_phase |

## 硬闸门自检（不可跳过）

- 标签必须来自 `engine/config/tag-taxonomy.yaml`，禁止自造领域/子标签（域外目录走新领域引导）
- 不删除已有 frontmatter 字段（status/created/updated 等）
- 领域无 phases → 不生成 pt_phase
- frontmatter 损坏 → 报错退出，禁止修正文
- 例外：用户说「直接按内容打标签」→ 跳过 tag-taxonomy 校验，但仍不删已有字段、不生成非法 pt_phase

### 漏网扫描（--scan-missed）

扫描 `knowledge/learning/` 全目录，找出所有 tags 含 `[学习资料]` 的文章：

- `tags: [学习资料]` + 无 `auto_enriched` → 入库时被跳过的漏网之鱼，自动执行 enrich
- `auto_enriched: true` → 已自动富化但未人工审核，列出清单提示用户审核
- 批量处理，每批 8-12 篇，进度回显

**触发时机**：
- `/enrich --scan-missed` 手动触发
- `/ingest` Step 0 预检自动触发（提示用户后执行）
- `/lint` 日常检查发现 `[学习资料]` 残留时自动触发
