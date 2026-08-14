#!/usr/bin/env python3
"""check-growth.py -- 规模趋势检查 (H6)

统计页面总数和目录大小，与上次快照对比，增幅 >50% 告警。

用法:
  python engine/scripts/check-growth.py --repo <知识库根目录>
  python engine/scripts/check-growth.py --repo . --json
  python engine/scripts/check-growth.py --repo . --snapshot  # 保存快照
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SNAPSHOT_FILE = "engine/scripts/.growth-snapshot.json"
CHECK_DIRS = ["knowledge", "ops"]
WARN_RATIO = 1.5  # 50% 增长告警


def collect_stats(repo: Path) -> dict:
    """Collect current stats."""
    stats = {"date": str(date.today()), "dirs": {}, "total_md": 0, "total_size_mb": 0}

    for d in CHECK_DIRS:
        dpath = repo / d
        if not dpath.exists():
            continue
        md_count = 0
        total_size = 0
        for f in dpath.rglob("*.md"):
            if any(p.startswith(".") for p in f.parts):
                continue
            md_count += 1
            try:
                total_size += f.stat().st_size
            except Exception:
                pass
        stats["dirs"][d] = {"md_count": md_count, "size_mb": round(total_size / (1024 * 1024), 1)}
        stats["total_md"] += md_count
        stats["total_size_mb"] += stats["dirs"][d]["size_mb"]

    stats["total_size_mb"] = round(stats["total_size_mb"], 1)
    return stats


def main():
    parser = argparse.ArgumentParser(description="H6: 规模趋势检查")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--snapshot", action="store_true", help="保存当前快照")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    current = collect_stats(repo)

    if args.snapshot:
        snap_path = repo / SNAPSHOT_FILE
        snap_path.parent.mkdir(parents=True, exist_ok=True)
        snap_path.write_text(json.dumps(current, ensure_ascii=False, indent=2),
                             encoding="utf-8")
        print(f"快照已保存: {snap_path}")
        print(f"  .md 文件: {current['total_md']}")
        print(f"  总大小: {current['total_size_mb']} MB")
        return 0

    # Load previous snapshot
    snap_path = repo / SNAPSHOT_FILE
    previous = None
    if snap_path.exists():
        try:
            previous = json.loads(snap_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    issues = []

    if previous:
        prev_md = previous.get("total_md", 0)
        prev_size = previous.get("total_size_mb", 0)
        md_growth = (current["total_md"] - prev_md) / max(1, prev_md)
        size_growth = (current["total_size_mb"] - prev_size) / max(1, prev_size)

        if md_growth > (WARN_RATIO - 1):
            issues.append(f".md 文件增长 {md_growth:.0%} ({prev_md}→{current['total_md']}) > {((WARN_RATIO-1)*100):.0f}%")
        if size_growth > (WARN_RATIO - 1):
            issues.append(f"总大小增长 {size_growth:.0%} ({prev_size}→{current['total_size_mb']} MB) > {((WARN_RATIO-1)*100):.0f}%")
    else:
        issues.append("无历史快照，无法计算趋势。运行 --snapshot 保存当前快照。")

    score = 10
    if len([i for i in issues if "无历史快照" not in i]) > 0:
        score = 7

    if args.json:
        print(json.dumps({
            "status": "pass" if score >= 10 else "fail",
            "score": score,
            "current": current,
            "previous": previous,
            "issues": issues,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"规模统计:")
        print(f"  .md 文件: {current['total_md']}")
        print(f"  总大小: {current['total_size_mb']} MB")
        for d, s in current["dirs"].items():
            print(f"  {d}/: {s['md_count']} .md, {s['size_mb']} MB")
        if previous:
            print(f"\n上次快照 ({previous.get('date', '?')}):")
            print(f"  .md 文件: {previous.get('total_md', '?')}")
            print(f"  总大小: {previous.get('total_size_mb', '?')} MB")
        if issues:
            print(f"\n⚠️ 问题:")
            for i in issues:
                print(f"  - {i}")
        print(f"\n得分: {score}/10")

    return 0 if score >= 7 else 1


if __name__ == "__main__":
    sys.exit(main())
