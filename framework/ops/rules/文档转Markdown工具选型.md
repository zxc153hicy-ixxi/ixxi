---
tags: [规则, 工具]
status: active
confidence: high
summary: 文档转Markdown四件套——Pandoc主力+Marker PDF+MarkItDown补漏+Calibre电子书
created: 2026-07-12
updated: 2026-07-20
---

# 文档转 Markdown 工具选型

## 标准流程

**转换前必须先预扫描，不开盲盒：**

```
入站文件 → 预扫描（判断类型）→ 按类型选工具 → 转换 → 检查质量
```

**LLM 执行协议**：
- **单个文件** → `python engine/scripts/auto-import.py <文件>`（自动 prescan + 转换 + 归档到 .inbox/，压缩包自动解压）
- **批量目录** → `python engine/scripts/batch-convert.py <源目录> <目标目录>`（递归转换 .docx/.pdf/.epub/.pptx/.ppt）
- **旧 .doc 文件** → `python engine/scripts/batch-doc-convert.py`（antiword 转换）

回显结果。仅在以下情况暂停确认：
- 依赖缺失（Calibre/LibreOffice/Marker/MinerU 未安装）
- 目标文件已存在（询问覆盖）

### 预扫描（prescan.py）

```bash
python .claudian/prescan.py <文件路径>
```

**覆盖全格式**，输出：格式类型、推荐工具、预估耗时、可直接复制的命令。

PDF 自动采样判断：
- **文字型 PDF（≥80% 采样页有文字）** → MarkItDown，秒级提取文本，无需 OCR
- **混合型 PDF（40%-80%）** → Marker，可能有扫描页/图表
- **扫描件（<40%）** → Marker，需 OCR

其他格式自动识别：
- **.doc** → 提醒 LibreOffice 预转换
- **.ppt** → 提醒 LibreOffice 预转换
- **.mobi/.azw/.azw3** → 提醒 Calibre 预转换
- **图片/扫描 PDF** → 提醒 Marker 首次 1.35GB 模型下载
- **.xyz** → 提示不支持，提需求追加

## 四件套

```
预扫描（prescan.py）
  ↓
Calibre（Kindle → EPUB）
  ↓
Pandoc（DOCX/EPUB/HTML → MD，主力）
  +
Marker（PDF/扫描件 → MD，2026 最佳）
  +
MarkItDown（PPTX/XLSX/音频 → MD，补漏）
```

一句话原则：先扫描再选工具。Pandoc 给结构化文档（**不能读 PDF**），MarkItDown 给 PDF/Office/多媒体，Marker 给扫描件。

## 按格式选工具

### PDF（先扫描再选工具）

| 格式 | 用什么 | 说明 |
|---|---|---|
| **PDF（文字型）** | MarkItDown | 秒级提取，无需模型下载 |
| **PDF（扫描件）** | Marker | 内置 Surya OCR 引擎，首次下载 1.35GB 模型 |
| **PDF（表格/公式多）** | Marker + LLM | `marker --use_llm` 启用 LLM 精修 |

> ⚠️ Pandoc **不能读取 PDF**，只能生成 PDF。

### 电子书

| 格式 | 第一步 | 第二步 | 说明 |
|---|---|---|---|
| **EPUB** | — | Pandoc | 一流支持 |
| **MOBI / AZW / AZW3**（Kindle） | Calibre → EPUB | Pandoc | 都不支持 Kindle 格式 |

### 办公文档

| 格式 | 用什么 | 说明 |
|---|---|---|
| **DOCX** | Pandoc | 表格/公式/图片/脚注完整保留 |
| **PPTX** | MarkItDown | 简单快捷 |
| **旧 .PPT** | LibreOffice → PPTX → MarkItDown | `soffice --headless --convert-to pptx` |
| **XLSX** | MarkItDown | Pandoc 需额外 `xlsx2csv` 步骤 |
| **HTML** | Pandoc | 结构保留更好 |

### 多媒体

| 格式 | 用什么 | 说明 |
|---|---|---|
| **图片（含文字）** | Marker | OCR 精度高于 MarkItDown |
| **音频 / YouTube** | MarkItDown | 语音转文字，独有功能 |

## 备选：MinerU 一体方案

如果想简化，**MinerU** 一个工具覆盖 PDF/DOCX/PPTX/XLSX 全部格式：

```bash
pip install mineru
mineru input.pdf -o output_dir/    # PDF
mineru input.docx -o output_dir/   # DOCX
```

VLM + OCR 双引擎，109 语言，中文专优。缺点：比单工具重。当前推荐四件套组合（各取最强），等 MinerU 更成熟后可考虑替换。

## 安装

```bash
# Pandoc
winget install pandoc

# Marker（PDF，2026 最佳）
pip install marker-pdf

# MarkItDown（Office/多媒体补漏）
pip install 'markitdown[all]'

# Calibre（电子书，可选）
winget install calibre

# LibreOffice（旧 .PPT，可选）
winget install LibreOffice
```

## 常用命令

```bash
# PDF → MD（Marker）
marker input.pdf output_dir/

# EPUB → MD
pandoc book.epub -t markdown -o book.md --extract-media=media

# Kindle → EPUB → MD
ebook-convert book.mobi book.epub
pandoc book.epub -t markdown -o book.md --extract-media=media

# DOCX → MD
pandoc input.docx -t markdown -o output.md --extract-media=media

# PPTX → MD
markitdown input.pptx -o output.md

# XLSX → MD
markitdown input.xlsx -o output.md

# 旧 .PPT → MD
soffice --headless --convert-to pptx input.ppt
markitdown input.pptx -o output.md

# HTML → MD
pandoc input.html -t markdown -o output.md
```

## 实测踩坑（2026-07-12）

### 预扫描脚本（prescan.py）

位于 `.claudian/prescan.py`，转换前先跑：

```bash
python .claudian/prescan.py <文件路径>
```

输出：页数、文字比例、推荐工具、预估耗时、正确命令。

#### 依赖

```bash
pip install PyPDF2 pycryptodome   # 预扫描 + AES 加密 PDF 解密
```

### Marker 首次运行

| 坑 | 现象 | 解决 |
|---|---|---|
| **CLI 不在 PATH** | `marker: command not found` | 找到 marker_single 绝对路径：`pip show marker-pdf \| grep Location`，拼接 `/Scripts/marker_single.exe` |
| **缺 psutil** | `ModuleNotFoundError: No module named 'psutil'` | `pip install psutil` |
| **命令用错** | `marker file.pdf output/` 报错 `Got unexpected extra argument` | `marker` 接受文件夹，单文件用 **`marker_single`** |
| **首次下载模型** | 下载 `model.safetensors` **1.35GB**，约 6-8 分钟 | 模型缓存在 Python 本地数据目录，后续跳过 |
| **AES 加密 PDF** | PyPDF2 报 `PyCryptodome is required for AES algorithm` | `pip install pycryptodome` |

### 正确命令

```bash
# 单文件 PDF
marker_single input.pdf --output_dir output/

# 批量 PDF（marker 接受文件夹）
marker pdf_folder/ --output_dir output/
```

## OCR 兜底（扫描件/图片型 PDF）

初次转换可能产出 **0KB 的 .md**（纯扫描件、图片 PDF、加密 PDF），需回源 PDF 走 OCR 重转：

| 场景 | 脚本 | 引擎 | 说明 |
|------|------|------|------|
| **中文 PDF** | `batch-mineru.py` | MinerU GPU | VLM+OCR 双引擎，109 语言，中文专优 |
| **英文 PDF** | `batch-ocr.py` | marker | Surya OCR 引擎，英文精度高 |

```bash
# 中文扫描件 OCR（MinerU）
python engine/scripts/batch-mineru.py --dry-run    # 预览 0KB 文件
python engine/scripts/batch-mineru.py               # 执行转换

# 英文扫描件 OCR（marker）
python engine/scripts/batch-ocr.py --dry-run
python engine/scripts/batch-ocr.py
```

两个脚本均内置 `TARGET_TO_SOURCE` 映射表（0KB .md 子目录 → 源 PDF 目录），新增映射需编辑脚本。

## 入库流程

1. 用对应工具转成 .md
2. 检查表格和图片是否正常
3. 运行 `python engine/scripts/auto-import.py <文件>` 自动完成转换+归档（源文件→`.inbox/sources/`，.md→`.inbox/converted/`）
4. **OCR 兜底检查**：扫描 `.inbox/converted/` 中 0KB 的 .md → 按语言选工具回源 OCR（见上方 OCR 兜底表）
5. `/ingest` 入库

## 关联
- [[Ingest完整流程]] —— 入库提炼流程
- [[知识库运维规范]] —— 运维操作规范
