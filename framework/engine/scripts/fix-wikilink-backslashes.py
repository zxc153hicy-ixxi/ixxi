#!/usr/bin/env python3
r"""fix-wikilink-backslashes.py -- 批量修复 wikilink 中的反斜杠->正斜杠

问题：导入的学习资料中 wikilink 使用 Windows 反斜杠路径，
check-links.py 无法解析，需统一为 Unix 正斜杠格式。

用法:
  python engine/scripts/fix-wikilink-backslashes.py --repo <知识库根目录>
  python engine/scripts/fix-wikilink-backslashes.py --repo . --dry-run  # 预览不写入
"""

import argparse
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKIP_DIRS = {".git", ".fix-backup", "__pycache__", ".obsidian", "node_modules"}


def fix_wikilinks(text: str) -> tuple[str, int]:
    """替换 wikilink 中的反斜杠为正斜杠，返回 (新文本, 替换数)"""
    count = 0

    def replace_backslash(m):
        nonlocal count
        content = m.group(1)
        # 检查是否包含反斜杠
        if "\\" in content:
            new_content = content.replace("\\", "/")
            count += 1
            return "[[" + new_content + "]]"
        return m.group(0)

    new_text = re.sub(r"\[\[([^\]]+)\]\]", replace_backslash, text)
    return new_text, count


def main():
    parser = argparse.ArgumentParser(description="批量修复 wikilink 反斜杠")
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不写入")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent

    total_fixed = 0
    total_replacements = 0

    for md_file in sorted(repo.rglob("*.md")):
        # 跳过特殊目录
        parts = set(md_file.parts)
        if parts & SKIP_DIRS:
            continue

        try:
            text = md_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        new_text, replacements = fix_wikilinks(text)

        if replacements > 0:
            total_fixed += 1
            total_replacements += replacements
            rel = md_file.relative_to(repo)
            if args.dry_run:
                print(f"  [DRY-RUN] {rel}: {replacements} 处")
            else:
                md_file.write_text(new_text, encoding="utf-8")
                print(f"  ✅ {rel}: {replacements} 处")

    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}修复完成: {total_fixed} 文件, {total_replacements} 处替换")
    return 0


if __name__ == "__main__":
    sys.exit(main())
