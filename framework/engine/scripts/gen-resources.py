#!/usr/bin/env python3
"""gen-resources.py — 从 SKILL.md 提取引用资源，写回 capability.json 的 resources 字段

清单 #13：capability resources 字段补齐（原 76 个全留空 []）。

提取规则：SKILL.md 正文中引用的 engine/ 或 ops/ 文件路径（.py/.sh/.md/.yaml），
去重后写入 capability.json 的 resources。resources 供 verify-capability dry-run（I4）
做可执行性验证，也为 parity P5 提供声明侧锚点。

用法：
  python framework/engine/scripts/gen-resources.py          # 写回（幂等）
  python framework/engine/scripts/gen-resources.py --stats  # 只统计不写回
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent.parent  # framework/
SRC = REPO / "core" / "skills"
# 引用路径：engine/ 或 ops/ 开头，文件后缀 .py/.sh/.md/.yaml
REF_RE = re.compile(r"(?:engine|ops)/[A-Za-z0-9_.\-/]+\.(?:py|sh|md|yaml)")


def extract_refs(skill_md: Path) -> list[str]:
    text = skill_md.read_text(encoding="utf-8")
    refs = set()
    for m in REF_RE.finditer(text):
        rel = m.group(0).strip().strip("`").strip("[]").split("#", 1)[0]
        if rel:
            refs.add(rel)
    return sorted(refs)


def main() -> int:
    write = "--stats" not in sys.argv[1:]
    caps = sorted(SRC.rglob("capability.json"))
    total_refs = 0
    filled = 0
    missing = []  # 引用但文件不存在的路径
    for cap in caps:
        skill_md = cap.parent / "SKILL.md"
        if not skill_md.exists():
            continue
        refs = extract_refs(skill_md)
        # 只保留实际存在的引用（断链不写入 resources，避免 dry-run 误报）
        valid = [r for r in refs if (REPO / r).exists()]
        missing.extend((cap.parent.name, r) for r in refs if not (REPO / r).exists())
        if write:
            data = json.loads(cap.read_text(encoding="utf-8"))
            if data.get("resources") != valid:
                data["resources"] = valid
                cap.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if valid:
            filled += 1
            total_refs += len(valid)

    print(f"capability 总数: {len(caps)}")
    print(f"含 resources 的 capability: {filled}")
    print(f"resources 总引用: {total_refs}")
    if missing:
        print(f"\n断链引用（未写入 resources）: {len(missing)} 条")
        for name, r in missing[:10]:
            print(f"  - {name}: {r}")
    if not write:
        print("\n（--stats 模式，未写回）")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("IXXI-E010 | resources 生成失败", file=sys.stderr)
        print(f"修复：检查 core/skills 结构；原始错误：{e}", file=sys.stderr)
        print("参考：engine/scripts/gen-resources.py", file=sys.stderr)
        sys.exit(1)
