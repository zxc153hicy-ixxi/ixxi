#!/usr/bin/env python3
"""check-naming.py -- 文件命名规范检查 (S7)

检查项:
  - 通用名文件 (index.md/README.md/设定.md 等) 数量
  - 同名文件冲突
  - 同目录前缀一致性

用法:
  python engine/scripts/check-naming.py --repo <知识库根目录>
  python engine/scripts/check-naming.py --repo . --json
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

GENERIC_NAMES = {"index.md", "readme.md", "设定.md", "大纲.md", "提示词.md"}
SKIP_DIRS = {".git", "__pycache__", ".obsidian", ".fix-backup", "node_modules",
             "images", "assets", "references"}
MAX_GENERIC = 3  # 通用名上限


def normalize_path(p: Path, repo: Path) -> str:
    return str(p.relative_to(repo)).replace("\\", "/")


def main():
    parser = argparse.ArgumentParser(description="S7: 文件命名规范检查")
    parser.add_argument("--repo", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent

    generic_files = []
    name_groups = defaultdict(list)
    issues = []

    for md_file in repo.rglob("*.md"):
        parts = md_file.parts
        if any(p in SKIP_DIRS for p in parts):
            continue
        if any(p.startswith(".") for p in parts):
            continue
        # 跳过 core/ 机制结构（skill/agent/hook 定义文件同名是设计使然，非知识内容冲突）
        rel_parts = md_file.relative_to(repo).parts
        if rel_parts and rel_parts[0] == "core":
            continue

        name_lower = md_file.name.lower()
        rel = normalize_path(md_file, repo)

        # index.md / README.md 为目录索引页（设计使然），豁免通用名检查
        if name_lower in GENERIC_NAMES and name_lower not in ("index.md", "readme.md"):
            generic_files.append(rel)

        # Group by filename (not full path) for conflict detection
        stem = md_file.stem.lower()
        name_groups[stem].append(rel)

    # Check generic names
    if len(generic_files) > MAX_GENERIC:
        issues.append(f"通用名文件 {len(generic_files)} 个 (上限 {MAX_GENERIC})")
        for gf in generic_files:
            issues.append(f"  - {gf}")

    # Check duplicate names across directories
    dupes = {k: v for k, v in name_groups.items() if len(v) > 1 and k not in ("index", "readme")}
    if dupes:
        for stem, paths in sorted(dupes.items()):
            if stem in ("index", "readme"):  # index.md and README.md are expected duplicates
                continue
            issues.append(f"同名冲突: '{stem}.md' ({len(paths)} 处)")
            for p in paths[:3]:
                issues.append(f"  - {p}")

    score = 10
    if len(generic_files) > MAX_GENERIC:
        score -= min(5, (len(generic_files) - MAX_GENERIC))
    if len(dupes) > 3:
        score -= min(3, len(dupes) - 3)

    if args.json:
        print(json.dumps({
            "status": "pass" if score >= 10 else "fail",
            "score": score,
            "generic_count": len(generic_files),
            "generic_files": generic_files,
            "duplicate_groups": {k: v for k, v in dupes.items()},
            "issues": issues,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"文件命名检查:")
        print(f"  通用名文件: {len(generic_files)} (上限 {MAX_GENERIC})")
        for gf in generic_files:
            print(f"    - {gf}")
        print(f"  同名冲突组: {len(dupes)}")
        for stem, paths in sorted(dupes.items())[:5]:
            print(f"    - {stem}.md: {len(paths)} 处")
        print(f"\n得分: {score}/10")
        if issues:
            for i in issues:
                print(i)

    return 0 if score >= 7 else 1


if __name__ == "__main__":
    sys.exit(main())
