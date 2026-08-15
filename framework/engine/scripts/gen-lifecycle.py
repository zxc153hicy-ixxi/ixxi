#!/usr/bin/env python3
"""gen-lifecycle.py — 给 capability.json 写 lifecycle_class 字段（不变量 I9）

I9：Critical Capability 不允许仅凭 last_used 自动归档。
本脚本给 capability 标注 lifecycle_class：critical（核心，禁止自动归档）/ normal（默认）。

critical 判定：MVP 核心 3 个（kb-ingest / kb-lint / kb-query）+ 显式配置，
其余 normal。后续 critical 集合随真实使用演化（人工裁决，非自动）。

用法：
  python framework/engine/scripts/gen-lifecycle.py          # 写回（幂等）
  python framework/engine/scripts/gen-lifecycle.py --stats  # 只统计
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent.parent  # framework/
SRC = REPO / "core" / "skills"
# MVP 核心 3 个 = Critical（I9：禁止仅凭 last_used 自动归档）
CRITICAL = {"kb-ingest", "kb-lint", "kb-query"}


def main() -> int:
    write = "--stats" not in sys.argv[1:]
    caps = sorted(SRC.rglob("capability.json"))
    stats = {"critical": 0, "normal": 0}
    for cap in caps:
        data = json.loads(cap.read_text(encoding="utf-8"))
        lc = "critical" if data.get("id") in CRITICAL else "normal"
        stats[lc] += 1
        if write and data.get("lifecycle_class") != lc:
            data["lifecycle_class"] = lc
            cap.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"capability 总数: {len(caps)}")
    print(f"lifecycle_class 分布: {stats}")
    if not write:
        print("（--stats 模式，未写回）")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("IXXI-E010 | lifecycle_class 生成失败", file=sys.stderr)
        print(f"修复：检查 core/skills 结构；原始错误：{e}", file=sys.stderr)
        print("参考：engine/scripts/gen-lifecycle.py", file=sys.stderr)
        sys.exit(1)
