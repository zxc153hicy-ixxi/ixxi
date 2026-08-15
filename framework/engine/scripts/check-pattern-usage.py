#!/usr/bin/env python3
"""check-pattern-usage.py -- 正反模式使用统计报告（⑤退役）

读 pattern-usage.json，报告「写了但没用」（count=0 或长期没触发）的正反模式。
让「写了没用」显形：该删的删（过时）、该升级的升级（该用没触发 → 建护栏）。

用法:
  python engine/scripts/check-pattern-usage.py --repo <知识库根目录>
  python engine/scripts/check-pattern-usage.py --repo . --json
"""

import argparse
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

USAGE_FILE = "personal/data/sessions/pattern-usage.json"


def main():
    parser = argparse.ArgumentParser(description="正反模式使用统计报告（⑤退役）")
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent
    usage_path = repo.parent / USAGE_FILE

    if not usage_path.exists():
        print(json.dumps({"status": "error", "detail": "pattern-usage.json 不存在"},
                         ensure_ascii=False, indent=2))
        return 1

    try:
        data = json.loads(usage_path.read_text(encoding="utf-8"))
    except Exception:
        print(json.dumps({"status": "error", "detail": "pattern-usage.json 解析失败"},
                         ensure_ascii=False, indent=2))
        return 1

    unused = []
    total = 0
    for key in ("patterns", "antipatterns"):
        for name, info in data.get(key, {}).items():
            total += 1
            if info.get("count", 0) == 0:
                unused.append({"type": key[:-1], "name": name, "count": 0})

    if args.json:
        print(json.dumps({
            "status": "ok",
            "total": total,
            "unused_count": len(unused),
            "unused": unused,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"正反模式使用统计：共 {total} 条，{len(unused)} 条「写了没用」（count=0）")
        for u in unused:
            print(f"  [{u['type']}] {u['name']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
