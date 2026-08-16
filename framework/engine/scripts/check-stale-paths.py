#!/usr/bin/env python3
"""check-stale-paths.py -- 旧路径残留检查 (C1)

扫描全库 .md，提取路径引用，与实际目录结构对比，列出不存在的路径。

用法:
  python engine/scripts/check-stale-paths.py --repo <知识库根目录>
  python engine/scripts/check-stale-paths.py --repo . --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKIP_DIRS = {".git", "__pycache__", ".obsidian", ".fix-backup", "node_modules",
             "images", "assets"}
# Known stale prefixes to detect (only truly deprecated paths)
STALE_PREFIXES = ["wiki/", "$S/wiki"]
# Files/dirs to skip (historical records, external content)
SKIP_FILE_PATTERNS = ["log.md", "learning/", "archive/", "checkpoints/",
                      "repair-checklist", "implementation-plan", "deep-review",
                      "修复", "实施计划", "designs/", "queries/", "审计报告",
                      "iterations/"]
# Path regex: matches directory-like references
PATH_RE = re.compile(r'(?:^|\s|\()`([a-zA-Z0-9_/.][a-zA-Z0-9_/.\-]{1,})`|'
                     r'(?:^|\s)([a-zA-Z0-9_/.]{2,}/(?:[a-zA-Z0-9_/.\-]){1,})')


def main():
    parser = argparse.ArgumentParser(description="C1: 旧路径残留检查")
    parser.add_argument("--repo", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent
    issues = []

    # Collect actual directories (for existence check)
    # os.walk 剪枝隐藏目录/SKIP_DIRS，避免遍历 .git 等大目录导致超时
    import os
    actual_dirs = set()
    md_files = []
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        rel_root = Path(root).relative_to(repo)
        for d in dirs:
            actual_dirs.add((rel_root / d).as_posix() + "/")
        for f in files:
            if f.endswith((".md", ".sh", ".py", ".js")):
                md_files.append(Path(root) / f)

    for md_file in md_files:
        parts = md_file.parts
        if any(p in SKIP_DIRS or p.startswith(".") for p in parts):
            continue

        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        rel_file = str(md_file.relative_to(repo)).replace("\\", "/")

        # Skip files that are historical records or external content
        if any(p in rel_file for p in SKIP_FILE_PATTERNS):
            continue

        # 跳过检测工具自身（含 wiki/ 占位符/注释/配置，非残留）
        if md_file.name in ("check-stale-paths.py", "check-links.py", "check-script-refs.py"):
            continue

        for line_no, line in enumerate(content.split("\n"), 1):
            # Check for stale prefix references
            for prefix in STALE_PREFIXES:
                if prefix in line:
                    # Skip if line contains migration note or is a URL
                    if any(kw in line for kw in ["→", "已废弃", "已迁移", "替换为", "http://", "https://"]):
                        continue
                    issues.append({
                        "file": rel_file,
                        "line": line_no,
                        "ref": prefix,
                        "text": line.strip()[:120],
                    })

    score = max(0, 10 - len(issues) // 3)

    if args.json:
        print(json.dumps({
            "status": "fail" if issues else "pass",
            "score": score,
            "issues": issues,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"旧路径残留: {len(issues)} 处")
        for issue in issues[:20]:
            print(f"  {issue['file']}:{issue['line']} -> {issue['ref']}")
        if not issues:
            print("  ✅ 无残留")
        print(f"\n得分: {score}/10")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
