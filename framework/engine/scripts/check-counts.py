#!/usr/bin/env python3
"""check-counts.py -- 计数单一事实源（机制1）

实时计算知识库结构性计数，并与文档中的 <!-- count:xxx=N --> 锚点比对。

计数项分两类：
  - 统计型（参与锚点比对）：patterns, antipatterns, sessions, feedback_pos,
    feedback_neg, skills, scripts —— 由目录/文件实时统计。
  - 解析型（不锚点，供 C3 实时解析）：version, g_rules, t_labels —— 由 AGENT.md
    结构化解析，永远与权威源一致，杜绝基准漂移。

用法:
  python engine/scripts/check-counts.py --repo <知识库根目录>
  python engine/scripts/check-counts.py --repo . --json
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

# 参与锚点比对的统计型 key（解析型不锚点）
ANCHOR_KEYS = {
    "patterns", "antipatterns", "sessions",
    "feedback_pos", "feedback_neg", "skills", "scripts",
}

SKIP_DIRS = {".git", "__pycache__", ".fix-backup", "node_modules"}
# 锚点扫描排除：personal 私有层 + 原始层 + 知识层 + 技能内容（人类写入区不应有计数锚点）
ANCHOR_SKIP_PREFIXES = ("personal/", "raw/", "knowledge/", ".agents/skills/", ".claude/skills/")

ANCHOR_RE = re.compile(r"<!--\s*count:(\w+)=(\d+)\s*-->")


def _count_md(d: Path) -> int:
    if not d.exists():
        return 0
    return sum(1 for f in d.glob("*.md") if f.is_file())


def _collect_counts(repo: Path) -> dict:
    c = {}

    # 正/反模式：减索引页（精确排除，避免误伤"索引定期补全""写文件不更新索引"这类含"索引"字样的模式条目）
    INDEX_PAGES = {"正模式索引", "反模式索引"}
    patterns_dir = repo / "ops" / "patterns"
    c["patterns"] = sum(1 for f in patterns_dir.glob("*.md") if f.stem not in INDEX_PAGES)
    anti_dir = repo / "ops" / "anti-patterns"
    c["antipatterns"] = sum(1 for f in anti_dir.glob("*.md") if f.stem not in INDEX_PAGES)

    # 会话：按日期命名（YYYY-MM-DD-）
    sess_dir = repo / "raw" / "sessions"
    if sess_dir.exists():
        c["sessions"] = sum(
            1 for f in sess_dir.glob("*.md")
            if re.match(r"^20\d{2}-\d{2}-\d{2}-", f.name)
        )
    else:
        c["sessions"] = 0

    # 反馈
    c["feedback_pos"] = _count_md(repo / "raw" / "feedback" / "positive")
    c["feedback_neg"] = _count_md(repo / "raw" / "feedback" / "negative")

    # 技能：所有含 SKILL.md 的目录（递归，含嵌套）
    skills_dir = repo / ".agents" / "skills"
    if skills_dir.exists():
        c["skills"] = sum(1 for _ in skills_dir.rglob("SKILL.md"))
    else:
        c["skills"] = 0

    # 脚本：engine/scripts/*.py + *.sh
    scripts_dir = repo / "engine" / "scripts"
    if scripts_dir.exists():
        c["scripts"] = sum(
            1 for f in scripts_dir.iterdir()
            if f.is_file() and f.suffix in (".py", ".sh")
        )
    else:
        c["scripts"] = 0

    # AGENT.md 结构化解析：version / g_rules / t_labels
    c["version"] = "unknown"
    c["g_rules"] = 0
    c["t_labels"] = 0
    agent_md = repo / "AGENT.md"
    if agent_md.exists():
        text = agent_md.read_text(encoding="utf-8", errors="replace")
        lines = text.split("\n")
        m = re.search(r"V(\d+\.\d+\.\d+)", lines[0] if lines else "")
        c["version"] = m.group(1) if m else "unknown"
        g = t = 0
        section = None
        for line in lines:
            if line.startswith("## G层") or line.startswith("## G 层"):
                section = "g"
                continue
            if line.startswith("## T层") or line.startswith("## T 层"):
                section = "t"
                continue
            if line.startswith("## ") and section in ("g", "t"):
                section = None
                continue
            if section == "g" and re.match(r"^\| G\d+(\.\d+)? \|", line):
                g += 1
            elif section == "t" and line.startswith("| `#"):
                t += 1
        c["g_rules"] = g
        c["t_labels"] = t

    return c


def _parse_anchors(repo: Path) -> list[dict]:
    anchors = []
    for f in repo.rglob("*.md"):
        if f.name.startswith("."):
            continue
        if any(p in SKIP_DIRS for p in f.parts):
            continue
        rel = str(f.relative_to(repo)).replace("\\", "/")
        if any(rel.startswith(p) for p in ANCHOR_SKIP_PREFIXES):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for m in ANCHOR_RE.finditer(text):
            anchors.append({
                "file": rel,
                "key": m.group(1),
                "declared": int(m.group(2)),
                "line": text[:m.start()].count("\n") + 1,
            })
    return anchors


def main():
    parser = argparse.ArgumentParser(description="计数单一事实源（机制1）")
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent

    counts = _collect_counts(repo)
    anchors = _parse_anchors(repo)

    mismatches = []
    unknown_keys = []
    for a in anchors:
        if a["key"] not in ANCHOR_KEYS:
            unknown_keys.append(a)
            continue
        actual = counts.get(a["key"])
        if actual != a["declared"]:
            mismatches.append({**a, "actual": actual})

    has_issue = bool(mismatches) or bool(unknown_keys)

    if args.json:
        print(json.dumps({
            "status": "fail" if has_issue else "pass",
            "counts": counts,
            "anchors_scanned": len(anchors),
            "mismatches": mismatches,
            "unknown_keys": unknown_keys,
        }, ensure_ascii=False, indent=2))
    else:
        print("计数检查（单一事实源）:")
        for k in sorted(counts):
            print(f"  {k}: {counts[k]}")
        print(f"\n锚点: 扫描 {len(anchors)} 处声明")
        if mismatches:
            print(f"  ❌ 不一致 {len(mismatches)} 处:")
            for m in mismatches:
                print(f"    {m['file']}:{m['line']} count:{m['key']} 声明{m['declared']} 实际{m['actual']}")
        else:
            print("  ✅ 无计数漂移")
        if unknown_keys:
            print(f"  ⚠️ 未知锚点 key {len(unknown_keys)} 处")

    return 1 if has_issue else 0


if __name__ == "__main__":
    sys.exit(main())
