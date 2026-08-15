"""文档预扫描：判断格式类型，推荐最佳转换工具

用法: python prescan.py <文件路径>
支持: PDF / DOCX / DOC / PPTX / PPT / XLSX / EPUB / MOBI / AZW / AZW3 / HTML / PNG / JPG / MP3 / WAV
"""
import sys
import math
from pathlib import Path

# ---------------------------------------------------------------------------
# 格式 → 工具配置
# ---------------------------------------------------------------------------
RULES = {
    ".pdf": {
        "scanner": "scan_pdf",
        "label": "PDF",
        "tools": {
            "text": {
                "name": "MarkItDown",
                "est": "< 10 秒",
                "cmd": 'markitdown "{path}" -o "{output}"',
            },
            "scan_zh": {
                "name": "MinerU",
                "est": "取决于页数（GPU: ~1-2 秒/页）",
                "cmd": '"{mineru}" -p "{path}" -o "{output_dir}/"',
            },
            "scan_en": {
                "name": "Marker",
                "est": "取决于页数（CPU: ~2-4 秒/页）",
                "cmd": '"{marker}" "{path}" --output_dir "{output_dir}/"',
            },
        },
    },
    ".docx": {
        "label": "Word 文档",
        "tool": {
            "name": "Pandoc",
            "est": "< 5 秒",
            "cmd": 'pandoc "{path}" -t markdown -o "{output}" --extract-media=media',
        },
    },
    ".doc": {
        "label": "旧版 Word（需先转换）",
        "tool": {
            "name": "LibreOffice → Pandoc",
            "est": "LibreOffice 转换 5-10 秒 + Pandoc < 5 秒",
            "cmd": 'soffice --headless --convert-to docx "{path}"\npandoc "{stem}.docx" -t markdown -o "{output}" --extract-media=media',
        },
    },
    ".pptx": {
        "label": "PowerPoint",
        "tool": {
            "name": "MarkItDown",
            "est": "< 5 秒",
            "cmd": 'markitdown "{path}" -o "{output}"',
        },
    },
    ".ppt": {
        "label": "旧版 PowerPoint（需先转换）",
        "tool": {
            "name": "LibreOffice → MarkItDown",
            "est": "LibreOffice 转换 5-10 秒 + MarkItDown < 5 秒",
            "cmd": 'soffice --headless --convert-to pptx "{path}"\nmarkitdown "{stem}.pptx" -o "{output}"',
        },
    },
    ".xlsx": {
        "label": "Excel 表格",
        "tool": {
            "name": "MarkItDown",
            "est": "< 5 秒",
            "cmd": 'markitdown "{path}" -o "{output}"',
        },
    },
    ".epub": {
        "label": "EPUB 电子书",
        "tool": {
            "name": "Pandoc",
            "est": "< 10 秒",
            "cmd": 'pandoc "{path}" -t markdown -o "{output}" --extract-media=media',
        },
    },
    ".mobi": {
        "label": "Kindle 电子书（需先转换）",
        "tool": {
            "name": "Calibre → Pandoc",
            "est": "Calibre 转换 10-60 秒 + Pandoc < 10 秒",
            "cmd": 'ebook-convert "{path}" "{stem}.epub"\npandoc "{stem}.epub" -t markdown -o "{output}" --extract-media=media',
        },
    },
    ".azw": {
        "label": "Kindle 电子书（需先转换）",
        "tool": {
            "name": "Calibre → Pandoc",
            "est": "Calibre 转换 10-60 秒 + Pandoc < 10 秒",
            "cmd": 'ebook-convert "{path}" "{stem}.epub"\npandoc "{stem}.epub" -t markdown -o "{output}" --extract-media=media',
        },
    },
    ".azw3": {
        "label": "Kindle 电子书（需先转换）",
        "tool": {
            "name": "Calibre → Pandoc",
            "est": "Calibre 转换 10-60 秒 + Pandoc < 10 秒",
            "cmd": 'ebook-convert "{path}" "{stem}.epub"\npandoc "{stem}.epub" -t markdown -o "{output}" --extract-media=media',
        },
    },
    ".html": {
        "label": "HTML 网页",
        "tool": {
            "name": "Pandoc",
            "est": "< 5 秒",
            "cmd": 'pandoc "{path}" -t markdown -o "{output}"',
        },
    },
    ".png": {
        "label": "图片（含文字）",
        "tool": {
            "name": "Marker",
            "est": "几秒到几十秒",
            "cmd": '"{marker}" "{path}" --output_dir "{output_dir}/"',
        },
    },
    ".jpg": {
        "label": "图片（含文字）",
        "tool": {
            "name": "Marker",
            "est": "几秒到几十秒",
            "cmd": '"{marker}" "{path}" --output_dir "{output_dir}/"',
        },
    },
    ".jpeg": {
        "label": "图片（含文字）",
        "tool": {
            "name": "Marker",
            "est": "几秒到几十秒",
            "cmd": '"{marker}" "{path}" --output_dir "{output_dir}/"',
        },
    },
    ".mp3": {
        "label": "音频",
        "tool": {
            "name": "MarkItDown",
            "est": "取决于时长",
            "cmd": 'markitdown "{path}" -o "{output}"',
        },
    },
    ".wav": {
        "label": "音频",
        "tool": {
            "name": "MarkItDown",
            "est": "取决于时长",
            "cmd": 'markitdown "{path}" -o "{output}"',
        },
    },
}

MARKER_EXE = "C:/Users/29909/AppData/Roaming/Python/Python310/Scripts/marker_single.exe"
MINERU_EXE = "C:/Users/29909/AppData/Roaming/Python/Python310/Scripts/mineru.exe"


def scan_pdf(filepath: str) -> dict:
    """PDF 专用：采样判断文字型/扫描件 + 中/英文分流"""
    import PyPDF2

    reader = PyPDF2.PdfReader(filepath)
    total_pages = len(reader.pages)

    # 采样：前3页 + 中间2页 + 末2页
    sample_indices = set()
    for i in range(min(3, total_pages)):
        sample_indices.add(i)
    for i in [total_pages // 2, total_pages // 2 + 1]:
        if i < total_pages:
            sample_indices.add(i)
    for i in [total_pages - 2, total_pages - 1]:
        if i >= 0 and i < total_pages:
            sample_indices.add(i)

    pages_with_text = 0
    all_text = ""
    for idx in sorted(sample_indices):
        text = (reader.pages[idx].extract_text() or "").strip()
        all_text += text
        if len(text) > 50:
            pages_with_text += 1

    sample_count = len(sample_indices)
    text_ratio = pages_with_text / sample_count if sample_count else 0

    # 语言检测：统计中文字符占比
    cjk_count = sum(1 for c in all_text if '一' <= c <= '鿿' or '㐀' <= c <= '䶿')
    total_chars = len(all_text.replace('\n', '').replace(' ', ''))
    zh_ratio = cjk_count / total_chars if total_chars > 100 else 0

    if text_ratio >= 0.4:
        return {
            "type": "text",
            "total_pages": total_pages,
            "text_ratio": round(text_ratio, 2),
            "reason": f"文字型 PDF（{pages_with_text}/{sample_count} 采样页有文字）",
        }
    else:
        # 扫描件文字太少，用文件名判断语言
        import re
        fname = Path(filepath).name
        has_cjk = bool(re.search(r'[一-鿿]', fname))
        subtype = "scan_zh" if (zh_ratio >= 0.01 or has_cjk) else "scan_en"
        tool = "MinerU" if subtype == "scan_zh" else "Marker"
        return {
            "type": subtype,
            "total_pages": total_pages,
            "text_ratio": round(text_ratio, 2),
            "zh_ratio": round(zh_ratio, 4),
            "reason": f"扫描件/图片型 PDF（仅 {pages_with_text}/{sample_count} 采样页有文字）→ 走 {tool}",
        }


def scan(filepath: str) -> None:
    path = Path(filepath)
    if not path.exists():
        print(f"[错误] 文件不存在: {filepath}")
        return

    ext = path.suffix.lower()
    size_mb = round(path.stat().st_size / 1024 / 1024, 1)
    rule = RULES.get(ext)

    if not rule:
        print(f"[不支持] {ext} 格式暂未收录")
        print(f"  文件: {path.name} | {size_mb}MB")
        print(f"  可以提需求追加到转换规则表")
        return

    label = rule["label"]
    stem = str(path.with_suffix(""))
    output_path = stem + ".md"
    output_dir = path.parent / path.stem

    # --- PDF 需要采样判断 ---
    rtype = None
    if ext == ".pdf" and "scanner" in rule:
        result = scan_pdf(filepath)
        rtype = result["type"]
        tool = rule["tools"][rtype]
        print(f"格式: {label} | {size_mb}MB | {result['total_pages']} 页")
        print(f"类型: {result['reason']}")
        print(f"推荐: {tool['name']} | 预估: {tool['est']}")
        print(f"输出: {output_path}")
        print(f"命令: {tool['cmd'].format(path=filepath, output=output_path, output_dir=output_dir, marker=MARKER_EXE, mineru=MINERU_EXE)}")
    else:
        tool = rule["tool"]
        cmd = tool["cmd"].format(path=filepath, stem=stem, output=output_path, output_dir=output_dir, marker=MARKER_EXE, mineru=MINERU_EXE)
        print(f"格式: {label} | {size_mb}MB")
        print(f"推荐: {tool['name']} | 预估: {tool['est']}")
        print(f"输出: {output_path}")
        print(f"命令:\n  {cmd}")

    # --- 共性问题提醒 ---
    if ext in (".doc", ".ppt"):
        print(f"注意: 旧格式需要 LibreOffice 预转换，确保已安装: winget install LibreOffice")
    if ext in (".mobi", ".azw", ".azw3"):
        print(f"注意: Kindle 格式需要 Calibre 预转换，确保已安装: winget install calibre")
    if ext in (".png", ".jpg", ".jpeg"):
        print(f"注意: 首次使用 Marker 会下载 1.35GB 模型，需等待 6-8 分钟（仅一次）")
    if ext == ".pdf" and rtype and rtype.startswith("scan"):
        if rtype == "scan_zh":
            print(f"注意: MinerU 需 GPU 环境，首次运行可能下载模型文件")
        else:
            print(f"注意: 首次使用 Marker 会下载 1.35GB 模型，需等待 6-8 分钟（仅一次）")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python prescan.py <文件路径>")
        print()
        print("支持格式:")
        for ext, rule in sorted(RULES.items()):
            print(f"  {ext:8s} → {rule['label']}")
        sys.exit(1)

    scan(sys.argv[1])
