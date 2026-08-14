#!/usr/bin/env python3
"""fix-stale-paths.py -- 全库旧路径 → 新路径替换（机械修复）

用法:
  python engine/scripts/fix-stale-paths.py --old <旧路径> --new <新路径> --dry-run
  python engine/scripts/fix-stale-paths.py --old <旧路径> --new <新路径> --execute --backup
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKIP_FILES = {"Thumbs.db", ".DS_Store", "desktop.ini", ".gitkeep", ".placeholder"}
SKIP_DIRS = {".git", "__pycache__", ".fix-backup", "node_modules", "_external"}
SCAN_DIRS = {"knowledge", "ops", "engine", ".claude"}  # 扫描范围
BACKUP_DIR = ".fix-backup"
NOW = datetime.now().strftime("%Y%m%d-%H%M%S")


def backup_file(file_path: Path, repo_root: Path) -> Path:
    """备份文件到 .fix-backup/"""
    backup_root = repo_root / BACKUP_DIR / NOW
    backup_root.mkdir(parents=True, exist_ok=True)
    rel = file_path.relative_to(repo_root)
    dest = backup_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file_path, dest)
    return dest


def find_and_replace(repo_root: Path, old: str, new: str, dry_run: bool, backup: bool) -> dict:
    """扫描并替换"""
    hits = []
    modified = 0

    for f in sorted(repo_root.rglob("*.md")):
        if f.name in SKIP_FILES:
            continue
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        rel = f.relative_to(repo_root)
        if rel.parts[0] not in SCAN_DIRS:
            continue

        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        count = text.count(old)
        if count == 0:
            continue

        hits.append({"file": str(rel), "count": count})

        if not dry_run:
            if backup:
                backup_file(f, repo_root)
            new_text = text.replace(old, new)
            tmp = f.with_suffix(".tmp")
            tmp.write_text(new_text, encoding="utf-8")
            tmp.replace(f)
            modified += 1

    return {"hits": hits, "modified": modified, "total_matches": sum(h["count"] for h in hits)}


def main():
    parser = argparse.ArgumentParser(description="全库路径替换")
    parser.add_argument("--old", type=str, required=True, help="旧路径（要替换的字符串）")
    parser.add_argument("--new", type=str, required=True, help="新路径（替换为的字符串）")
    parser.add_argument("--dry-run", action="store_true", default=True, help="预览模式（默认）")
    parser.add_argument("--execute", action="store_true", help="真实执行")
    parser.add_argument("--backup", action="store_true", help="执行前备份到 .fix-backup/")
    parser.add_argument("--repo", type=str, default=None, help="知识库根目录")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent
    dry_run = not args.execute

    result = find_and_replace(repo, args.old, args.new, dry_run, args.backup)

    if args.json:
        print(json.dumps({
            "status": "dry_run" if dry_run else "executed",
            "old": args.old,
            "new": args.new,
            "files_affected": len(result["hits"]),
            "total_matches": result["total_matches"],
            "modified": result["modified"] if not dry_run else 0,
            "hits": result["hits"],
        }, ensure_ascii=False, indent=2))
    else:
        if dry_run:
            print(f"[DRY RUN] 将替换 {result['total_matches']} 处在 {len(result['hits'])} 个文件中:")
        else:
            print(f"[EXECUTED] 已替换 {result['total_matches']} 处在 {result['modified']} 个文件中:")
            if args.backup:
                print(f"  备份: .fix-backup/{NOW}/")
        for h in result["hits"]:
            print(f"  {h['file']} ({h['count']} 处)")
        if dry_run:
            print("\n加 --execute 执行替换，加 --backup 备份原文件。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
