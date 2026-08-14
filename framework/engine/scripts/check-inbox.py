#!/usr/bin/env python3
"""check-inbox.py -- .inbox/ 健康检查 + raw/inbox 入库比对

用法:
  python engine/scripts/check-inbox.py --repo <知识库根目录>
  python engine/scripts/check-inbox.py --repo . --mode health     # .inbox/ 健康（默认）
  python engine/scripts/check-inbox.py --repo . --mode ingest     # raw/inbox → knowledge/ 比对
  python engine/scripts/check-inbox.py --repo . --mode all        # 全部
  python engine/scripts/check-inbox.py --repo . --json
  python engine/scripts/check-inbox.py --repo . --mode ingest --detailed

合并: check-inbox.py (health) + check-inbox-ingest.py (ingest)
"""

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKIP_FILES = {"Thumbs.db", ".DS_Store", "desktop.ini", ".gitkeep", ".placeholder"}
SKIP_PREFIXES = (".", "_")
SOURCE_EXTS = {".pdf", ".docx", ".epub", ".doc", ".ppt", ".pptx"}


def _normalize(name: str) -> str:
    name = os.path.splitext(name)[0]
    name = re.sub(r"^\d+[、.\-_\s]+", "", name)
    name = re.sub(r"^[【\[]?\d+[】\]]?\s*", "", name)
    return name.lower().strip()


# ── mode: health ──

def check_health(repo: Path, max_age: int) -> tuple[list, list, int]:
    inbox = repo / ".inbox"
    if not inbox.exists():
        return [], [], 0

    now = time.time()
    max_age_sec = max_age * 86400
    stale_files, tmp_files, total_size = [], [], 0

    for f in sorted(inbox.rglob("*")):
        if f.name in SKIP_FILES or not f.is_file():
            continue
        size = f.stat().st_size
        total_size += size
        if f.suffix == ".tmp":
            tmp_files.append({"file": str(f.relative_to(repo)), "size_kb": round(size / 1024, 1)})
        elif f.suffix == ".md":
            age_days = (now - f.stat().st_mtime) / 86400
            if age_days > max_age:
                stale_files.append({"file": str(f.relative_to(repo)), "age_days": round(age_days, 1), "size": size})

    return stale_files, tmp_files, total_size


# ── mode: ingest ──

def check_ingest(repo: Path) -> tuple[list, list, list]:
    inbox = repo / "raw" / "inbox"
    knowledge = repo / "knowledge" / "learning"

    sources = []
    if inbox.exists():
        for f in sorted(inbox.rglob("*")):
            if f.name.startswith(SKIP_PREFIXES):
                continue
            if f.is_file() and f.suffix.lower() in SOURCE_EXTS:
                sources.append(f)

    md_index = {}
    if knowledge.exists():
        for f in sorted(knowledge.rglob("*.md")):
            if f.name.startswith(SKIP_PREFIXES) or not f.is_file():
                continue
            key = _normalize(f.name)
            if key:
                md_index[key] = f

    ingested, missing, uncertain = [], [], []
    for src in sources:
        src_key = _normalize(src.name)
        if not src_key:
            missing.append((src, "无法标准化文件名"))
            continue
        if src_key in md_index:
            ingested.append((src, md_index[src_key]))
            continue
        matched = None
        for md_key, md_path in md_index.items():
            if len(src_key) >= 10 and src_key in md_key:
                matched = md_path; break
            if len(md_key) >= 10 and md_key in src_key:
                matched = md_path; break
        if matched:
            uncertain.append((src, matched))
        else:
            missing.append((src, "knowledge/ 中无匹配 .md"))

    return ingested, missing, uncertain


# ── main ──

def main(mode: str = "all", repo_path: str = None, json_out: bool = False,
         max_age: int = 7, detailed: bool = False):
    repo = Path(repo_path).resolve() if repo_path else Path(__file__).resolve().parent.parent.parent

    modes_to_run = ["health", "ingest"] if mode == "all" else [mode]
    all_results = {}

    for m in modes_to_run:
        if m == "health":
            stale, tmp, total_size = check_health(repo, max_age)
            score = 10
            if stale:
                score -= 3
            if tmp:
                score -= 2
            all_results["health"] = {"label": ".inbox/ 健康", "stale_count": len(stale),
                                      "tmp_count": len(tmp), "total_size_mb": round(total_size / 1048576, 1),
                                      "stale": stale, "tmp": tmp, "score": score}
        elif m == "ingest":
            ingested, missing, uncertain = check_ingest(repo)
            total = len(ingested) + len(missing) + len(uncertain)
            rate = round(len(ingested) / total * 100, 1) if total else 0
            all_results["ingest"] = {"label": "raw/inbox → knowledge/ 入库",
                                      "total": total, "ingested": len(ingested),
                                      "missing": len(missing), "uncertain": len(uncertain),
                                      "rate": rate,
                                      "ingested_list": ingested, "missing_list": missing,
                                      "uncertain_list": uncertain,
                                      "score": 10 if not missing else max(0, 10 - len(missing))}

    if json_out:
        output = {"status": "pass", "modes": {}}
        has_issues = False
        for m, data in all_results.items():
            summary = {k: v for k, v in data.items()
                       if k not in ("stale", "tmp", "ingested_list", "missing_list", "uncertain_list", "label")}
            if data.get("score", 10) < 10:
                has_issues = True
            output["modes"][m] = summary
        output["status"] = "fail" if has_issues else "pass"
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for m, data in all_results.items():
            print(f"--- {data['label']} ---")
            if m == "health":
                print(f"  过期: {data['stale_count']}, 残留.tmp: {data['tmp_count']}, "
                      f"大小: {data['total_size_mb']}MB")
                if data["stale"]:
                    for s in data["stale"]:
                        print(f"  ⚠️  {s['file']} ({s['age_days']}天)")
                if data["tmp"]:
                    for t in data["tmp"]:
                        print(f"  ⚠️  {t['file']}")
                if not data["stale"] and not data["tmp"]:
                    print("  ✅ 健康")
            elif m == "ingest":
                print(f"  源文件: {data['total']}, 已入库: {data['ingested']}, "
                      f"未入库: {data['missing']}, 入库率: {data['rate']}%")
                if data["missing_list"]:
                    print(f"  ❌ 未入库 ({len(data['missing_list'])}):")
                    by_dir = defaultdict(list)
                    for src, reason in data["missing_list"]:
                        try:
                            d = str(src.parent.relative_to(repo / "raw" / "inbox"))
                        except ValueError:
                            d = "(根目录)"
                        by_dir[d].append(src.name)
                    for d, files in sorted(by_dir.items()):
                        print(f"    {d}/ ({len(files)})")
                        for f in files[:5]:
                            print(f"      - {f}")
                        if len(files) > 5:
                            print(f"      ... 还有 {len(files) - 5} 个")
                if data["uncertain_list"] and detailed:
                    print(f"  ⚠️  模糊匹配 ({len(data['uncertain_list'])}):")
                    for src, matched in data["uncertain_list"]:
                        print(f"    {src.name} → {matched.relative_to(repo)}")
                if not data["missing_list"]:
                    print("  ✅ 全部已入库")
            print()

    any_issues = any(data.get("score", 10) < 10 for data in all_results.values())
    return 1 if any_issues else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=".inbox/ 健康 + 入库比对")
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--mode", type=str, default="all",
                        choices=["all", "health", "ingest"])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max-age", type=int, default=7)
    parser.add_argument("--detailed", action="store_true")
    args = parser.parse_args()
    sys.exit(main(mode=args.mode, repo_path=args.repo, json_out=args.json,
                  max_age=args.max_age, detailed=args.detailed))
