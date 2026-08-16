---
tags: [OCR, ingest, 清理]
status: active
scope: framework
name: OCR碎片未在ingest清理
description: OCR转换后残留的图片引用和碎片文件未在导入阶段清除，导致Obsidian中大量空白框，事后批量清理成本高
metadata:
  type: project
  tags: [OCR, ingest, 清理]
  date: 2026-07-21
summary: 反模式——OCR 残留 ![]() 碎片未在 Ingest 阶段清理，事后批量修复成本高
created: 2026-07-21
updated: 2026-07-21
---

# OCR 碎片未在 ingest 清理

## 问题

MinerU 等 OCR 工具转换 PDF 后会残留大量图片碎片文件（`_page_X_Picture_Y.jpeg`）和 markdown 中的 `![]()` 图片引用。这些碎片在 Obsidian 中显示为空白框，严重干扰阅读体验。

本次发现：503 个 JPEG 文件，51 个 md 文件中 13688 行 `![]()` 引用，全部是 OCR 页面布局碎片。

## 为什么是反模式

- 事后批量清理成本高（需 grep 全量 + 脚本处理 + 验证）
- 碎片文件占用磁盘空间（503 个文件）
- Obsidian 图谱视图被污染

## 正确做法

在 Ingest 流程的 Step 2（转换后）增加：删除 `_page_*_Picture_*.jpeg` 等 OCR 碎片图片，并从 md 文件中清除 `![](_page_*` 引用。

## 关联

- [[预检脚本漏检]] —— 检查脚本应有全覆盖意识
- Ingest完整流程 —— Ingest 9 步流水线

## 修复

2026-07-21: `check-ocr-quality.py` 新增 `--clean` 模式，Ingest Step 0 操作列追加第⑧项自动清除。503 个历史碎片 + 13688 行引用已人工清理。
