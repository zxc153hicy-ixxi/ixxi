#!/usr/bin/env python3
"""check-superseded-links.py -- superseded_by/replaces 断链检查 (C7)

验证 YAML frontmatter 中 superseded_by 和 replaces 字段的 wikilink 目标是否存在。

用法:
  python engine/scripts/check-superseded-links.py --repo <知识库根目录>
  python engine/scripts/check-superseded-links.py --repo . --json
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

try:
    import yaml
except ImportError:
    print("需要 PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

SKIP_DIRS = {".git", "__pycache__", ".obsidian", ".fix-backup", "node_modules"}
FM_RE = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)
WIKILINK_RE = re.compile(r'\[\[([^\]|#]+)')


def find_target(repo: Path, name: str) -> bool:
    """Search for a target file matching the wikilink name."""
    # Direct match
    target = repo / f"{name}.md"
    if target.exists():
        return True
    # Subdirectory search (limited depth)
    for d in ["ops", "knowledge", "raw", ".claude", "engine"]:
        for f in (repo / d).rglob(f"{name}.md"):
            if not any(p.startswith(".") for p in f.parts):
                return True
    return False


def main():
    parser = argparse.ArgumentParser(description="C7: superseded_by/replaces 断链检查")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    issues = []

    for md_file in repo.rglob("*.md"):
        parts = md_file.parts
        if any(p in SKIP_DIRS or p.startswith(".") for p in parts):
            continue

        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        # Quick skip
        if "superseded_by" not in content and "replaces" not in content:
            continue

        fm_match = FM_RE.match(content)
        if not fm_match:
            continue

        try:
            fm = yaml.safe_load(fm_match.group(1))
        except Exception:
            continue

        if not isinstance(fm, dict):
            continue

        rel_file = str(md_file.relative_to(repo)).replace("\\", "/")

        for field in ["superseded_by", "replaces"]:
            val = fm.get(field)
            if not val:
                continue
            if isinstance(val, str):
                val = [val]
            if not isinstance(val, list):
                continue

            for link in val:
                m = WIKILINK_RE.search(str(link))
                if not m:
                    continue
                target_name = m.group(1).strip()
                if not find_target(repo, target_name):
                    issues.append({
                        "file": rel_file,
                        "field": field,
                        "target": target_name,
                    })

    score = max(0, 10 - len(issues) * 2)

    if args.json:
        print(json.dumps({
            "status": "pass" if score >= 10 else "fail",
            "score": score,
            "issues": issues,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"superseded_by/replaces 断链: {len(issues)} 处")
        for issue in issues:
            print(f"  ❌ {issue['file']}: {issue['field']}=[[{issue['target']}]] -> 目标不存在")
        if not issues:
            print("  ✅ 无断链")
        print(f"\n得分: {score}/10")

    return 0 if score >= 10 else 1


if __name__ == "__main__":
    sys.exit(main())
