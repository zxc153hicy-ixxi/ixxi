---
tags: [反模式]
status: active
scope: framework
summary: 有现成 docx 时 LLM 默认走 python-docx 修改，不走 pandoc 重建，导致段落漂移+多轮修正
created: 2026-07-17
severity: medium
updated: 2026-07-20
---

# docx 修改优先于重建

## 发生了什么

网络安全岗简历需要导出 Word 版。运维版 v4 docx 已有蓝色排版，LLM 选择拿它当模板，用 python-docx 逐段替换内容。

结果：
- runs 无法完全清除嵌套文本（多 run 结构 `run.text = ''` 漏清）
- 段落索引在多次增删后漂移，角色跑到标题前面、bullet 丢失
- 补缺失段落需要手捏 XML（`etree.SubElement` 构造 `w:r`/`w:rPr`/`w:t`）
- **4 轮修正才稳定，总计约 15 分钟**

而正确做法是 Markdown → pandoc → docx，再套样式模板，**3-5 倍快且不漂移**。

## 根因

LLM 看到"现成的 docx 有漂亮排版"，默认走"保护现有格式 → 修改内容"的路径。没有先判断：这次改动的量（几乎全量替换）和代价（修改 vs 重建哪个更快）。

人类直觉是"复用"，但对 docx 这种二进制格式，"复用排版"和"复用文件"是两个概念——排版应该抽象为模板（reference.docx），文件本身不应该被复用。

## 怎么修的

> Markdown → pandoc → docx + 样式模板 —— 当内容改动 > 30% 时走这条线。
> 仅当必须保留原文档的精确排版（颜色/字体/间距已精心调整）且改动 < 30%，才走 python-docx 修改。

| 方案 | 适用场景 | 速度 |
|------|------|:---:|
| Markdown → pandoc → docx + 样式模板 | 从零生成、内容为主的简历 | 快 |
| 修改他人 docx（python-docx + XML） | 必须保留原排版且改动小 | 慢，易漂移 |

## 识别特征

- LLM 提议"用现成的 docx 改一下"或"基于之前的 docx 替换内容"
- 实际改动量 > 全文 30%
- 讨论中出现 python-docx、lxml、XML 直修等关键词
- 重复出现"改完发现段落不对""多 run 结构"
- **判定标准**：改动量 > 30% 或目标文件有对应的 Markdown 源 → 坚决走重建管线

## 关联
- [[2026-07-15-简历构建与真实性校准]] —— 来源会话
- ../rules/文档转Markdown工具选型 —— pandoc 工具链
