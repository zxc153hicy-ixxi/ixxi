#!/usr/bin/env python3
"""fix-index-sync.py -- 修复 index.md 与实际文件的一致性

读取 check-links.py --mode index 的结果：
- 死链 → 移除或替换
- 未收录文件 → 追加到 index.md

用法:
  python engine/scripts/fix-index-sync.py --repo . --dry-run
  python engine/scripts/fix-index-sync.py --repo . --execute
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]+)?\]\]")


def get_index_issues(repo: Path) -> dict:
    """调用 check-links.py --mode index 获取问题"""
    checker = repo / "engine" / "scripts" / "check-links.py"
    result = subprocess.run(
        [sys.executable, str(checker), "--repo", str(repo), "--mode", "index", "--json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if not result.stdout.strip():
        return {"dead_links": [], "unindexed": []}
    try:
        data = json.loads(result.stdout)
        idx = data.get("modes", {}).get("index", {})
        return {"dead_links": idx.get("dead_links", []), "unindexed": idx.get("unindexed", [])}
    except json.JSONDecodeError:
        return {"dead_links": [], "unindexed": []}


def remove_dead_link(index_path: Path, dead_target: str) -> bool:
    """从 index.md 中移除一条死链"""
    try:
        lines = index_path.read_text(encoding="utf-8").split("\n")
    except Exception:
        return False

    new_lines = []
    removed = False
    for line in lines:
        if f"[[{dead_target}]]" in line or f"[[{dead_target}|" in line:
            removed = True
            continue
        new_lines.append(line)

    if removed:
        tmp = index_path.with_suffix(".tmp")
        tmp.write_text("\n".join(new_lines), encoding="utf-8")
        tmp.replace(index_path)

    return removed


def add_index_entry(index_path: Path, file_path: str, repo: Path) -> bool:
    """向 index.md 追加一条新条目"""
    # 读取文件 frontmatter 获取 summary
    f = repo / f"{file_path}.md"
    summary = ""
    if f.exists():
        try:
            raw = f.read_text(encoding="utf-8", errors="replace")
            if raw.startswith("---"):
                parts = raw.split("---", 2)
                if len(parts) >= 3:
                    import yaml
                    data = yaml.safe_load(parts[1]) or {}
                    summary = data.get("summary", "")
        except Exception:
            pass

    # 确定应该插入到哪个区域
    text = index_path.read_text(encoding="utf-8")
    entry = f"- [[{file_path}]]"
    if summary:
        entry += f" —— {summary}"

    # 简单策略：追加到「样例与文档」节之前
    if "## 样例与文档" in text:
        text = text.replace("## 样例与文档", f"{entry}\n\n## 样例与文档")
    else:
        text += f"\n{entry}\n"

    tmp = index_path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(index_path)
    return True


def main():
    parser = argparse.ArgumentParser(description="index.md 一致性修复")
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent
    index_md = repo / "index.md"

    issues = get_index_issues(repo)
    dead = issues.get("dead_links", [])
    unindexed = issues.get("unindexed", [])

    # 过滤：只处理 framework/ 和 personal/ 下的文件，跳过 archive/
    unindexed = [u for u in unindexed
                 if u["file"].startswith(("framework/", "personal/"))
                 and "archive" not in u["file"]
                 and not u["file"].split("/")[-1].lower() in ("readme", "")]

    if args.json:
        print(json.dumps({
            "dead_links": len(dead),
            "unindexed": len(unindexed),
            "dead_details": dead,
            "unindexed_details": unindexed,
        }, ensure_ascii=False, indent=2))
        return 0

    print(f"index.md 修复分析:")
    print(f"  死链: {len(dead)} 条")
    print(f"  未收录: {len(unindexed)} 个 (过滤后)")

    if dead:
        print(f"\n死链 (将移除):")
        for d in dead:
            print(f"  ❌ [[{d['link']}]]")

    if unindexed:
        print(f"\n未收录 (将追加，最多显示 10 个):")
        for u in unindexed[:10]:
            print(f"  + {u['file']}")
        if len(unindexed) > 10:
            print(f"  ... 等 {len(unindexed) - 10} 个")

    if not args.execute:
        print(f"\n💡 加 --execute 执行修复。")
        return 0

    # 执行修复
    removed = 0
    for d in dead:
        if remove_dead_link(index_md, d["link"]):
            print(f"  ✅ 已移除: [[{d['link']}]]")
            removed += 1

    added = 0
    for u in unindexed:
        if add_index_entry(index_md, u["file"], repo):
            added += 1

    print(f"\n修复完成: 移除 {removed} 条死链, 追加 {added} 条新条目")
    print("⚠️ 请手动检查 index.md 的条目位置是否合理，必要时调整分组。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
