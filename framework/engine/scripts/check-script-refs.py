#!/usr/bin/env python3
"""check-script-refs.py -- 检查脚本中的路径引用是否存在 (S4)

用法:
  python engine/scripts/check-script-refs.py --repo <知识库根目录>
  python engine/scripts/check-script-refs.py --repo . --json
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

SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".fix-backup"}
# 已知顶层目录（wiki/ 残留由 check-residue.py 统一处理，不在此列）
TOP_DIRS = ("engine/", "ops/", "knowledge/", "raw/", ".claude/", ".inbox/")


def _is_placeholder(p: str) -> bool:
    """跳过占位符/glob/运行时生成文件，避免误报。"""
    low = p.lower()
    if any(tok in low for tok in ("xxx", "yyyy", "<", ">", "*", "placeholder",
                                  "__pycache__", "_video_state")):
        return True
    if p.endswith("-"):
        return True  # glob 或路径截断残留
    return False


def find_path_refs(content: str, script_name: str, repo: Path) -> list[dict]:
    """Extract path-like strings and verify existence.

    覆盖三类引用：带引号路径、变量拼接（$S/wiki）、裸路径（bash wiki/x.sh）。
    """
    issues = []
    seen = set()

    patterns = [
        # 带引号的 repo 相对路径
        re.compile(r'["\']([a-zA-Z0-9_/.][a-zA-Z0-9_/.\-]{2,})["\']'),
        # 带前缀的脚本引用：engine/scripts/xxx.py 或 ops/scripts/xxx.sh
        re.compile(r'\b((?:engine/scripts|ops/scripts)/[A-Za-z0-9_.\-]+\.(?:py|sh))\b'),
        # 裸 check 脚本名（可能省略 engine/scripts/ 前缀）
        re.compile(r'\b(check-[a-z0-9_.\-]+\.py)\b'),
    ]

    for pat in patterns:
        for m in pat.finditer(content):
            p = m.group(1).strip()
            # 跳过「合并自」历史记录（脚本 docstring 说明合并来源，非死引用）
            line_text = content.split("\n")[content[:m.start()].count("\n")]
            if "合并" in line_text or "merge" in line_text.lower():
                continue
            # 跳过「待建/规划」脚本（规划中尚未实现的引用，非死引用）
            if "待建" in line_text or "TODO" in line_text or "规划" in line_text:
                continue
            # 裸 check 名补全前缀（仅 .py，.sh 的 check-* 在 templates/ 下）
            if p.startswith("check-") and "/" not in p and p.endswith(".py"):
                p = "engine/scripts/" + p
            p = p.rstrip(".,;:)!?）】』，。；：")
            if not p or _is_placeholder(p):
                continue
            if not any(p.startswith(d) for d in TOP_DIRS):
                continue
            if p in seen:
                continue
            seen.add(p)

            target = repo / p.rstrip("/")
            if not target.exists():
                issues.append({"script": script_name, "ref": p,
                               "line": content[:m.start()].count("\n") + 1})

    return issues


def main():
    parser = argparse.ArgumentParser(description="S4: 脚本引用文件存在性检查")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    scripts_dir = repo / "engine" / "scripts"
    ops_scripts_dir = repo / "ops" / "scripts"

    all_issues = []
    checked = 0

    scan_targets = [
        (scripts_dir, (".py", ".sh")),
        (ops_scripts_dir, (".py", ".sh")),
        (repo / "engine" / "templates", (".sh", ".js")),
        (repo / "ops" / "rules", (".md",)),
    ]
    for scan_dir, suffixes in scan_targets:
        if not scan_dir.exists():
            continue
        for f in scan_dir.rglob("*"):
            if f.is_dir() or any(p in SKIP_DIRS for p in f.parts):
                continue
            if f.name == "check-script-refs.py":
                continue  # 跳过自身（TOP_DIRS 常量故意含 wiki/）
            if f.suffix not in suffixes:
                continue
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            rel_name = str(f.relative_to(repo)).replace("\\", "/")
            issues = find_path_refs(content, rel_name, repo)
            all_issues.extend(issues)
            checked += 1

    score = max(0, 10 - len(all_issues) // 3)

    if args.json:
        print(json.dumps({
            "status": "fail" if all_issues else "pass",
            "score": score,
            "issues": all_issues,
            "checked": checked,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"脚本引用检查: {checked} 个脚本, {len(all_issues)} 处问题")
        for issue in all_issues:
            print(f"  ❌ {issue['script']}:{issue['line']} -> {issue['ref']}")
        if not all_issues:
            print("  ✅ 全部引用有效")
        print(f"\n得分: {score}/10")

    return 1 if all_issues else 0


if __name__ == "__main__":
    sys.exit(main())
