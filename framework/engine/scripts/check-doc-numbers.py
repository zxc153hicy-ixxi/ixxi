#!/usr/bin/env python3
"""check-doc-numbers.py -- 关键文档硬编码数字检测（护栏C）

扫描 GETTING-STARTED.md、activation.md 中的硬编码数字，
与实际文件系统计数对比。不一致→提示应改为变量引用。

用法:
  python engine/scripts/check-doc-numbers.py --repo <知识库根目录>
  python engine/scripts/check-doc-numbers.py --repo . --json
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

SKIP_FILES = {"Thumbs.db", ".DS_Store", "desktop.ini", ".gitkeep", ".placeholder"}


def count_md(dir_path: Path) -> int:
    if not dir_path.exists():
        return 0
    return len([f for f in dir_path.glob("*.md") if f.name not in SKIP_FILES and "索引" not in f.name])


def get_actuals(repo: Path) -> dict:
    return {
        "rules": count_md(repo / "ops" / "rules"),
        "patterns": count_md(repo / "ops" / "patterns"),
        "anti_patterns": count_md(repo / "ops" / "anti-patterns"),
        "sessions": count_md(repo / "raw" / "sessions"),
        "skills_internal": len(list((repo / ".claude" / "kb" / "skills").glob("*"))) if (repo / ".claude" / "kb" / "skills").exists() else 0,
        "scripts_engine": len([f for f in (repo / "engine" / "scripts").glob("check-*.py") if f.name not in SKIP_FILES]),
        "templates": len(list((repo / "engine" / "templates").glob("*"))) if (repo / "engine" / "templates").exists() else 0,
    }


# 文档中的数字声明模式：(文件, 字段名, 正则, actual_key)
DOC_PATTERNS = [
    # activation.md — 使用目录名+数字的精确匹配
    ("activation.md", "rules数", r"ops/rules/\S*\s*[（(]?(\d+)\s*(个|文件)", "rules"),
    ("activation.md", "patterns数", r"ops/patterns/\S*\s*[（(]?(\d+)\s*(条|个)", "patterns"),
    ("activation.md", "anti-patterns数", r"ops/anti-patterns/\S*\s*[（(]?(\d+)\s*(条|个)", "anti_patterns"),
    ("activation.md", "scripts数", r"engine/scripts/\S*\s*[（(]?(\d+)\s*(个|脚本)", "scripts_engine"),
    ("activation.md", "templates数", r"engine/templates/\S*\s*[（(]?(\d+)\s*(个|模板|脚本)", "templates"),
    # GETTING-STARTED.md — 精确匹配 "N 个规则文件" 等模式
    ("GETTING-STARTED.md", "rules数", r"(\d+)\s*个\s*规则文件", "rules"),
    ("GETTING-STARTED.md", "patterns数", r"正模式[^0-9]*?(\d+)\s*条", "patterns"),
    ("GETTING-STARTED.md", "anti-patterns数", r"反模式[^0-9]*?(\d+)\s*条", "anti_patterns"),
    ("GETTING-STARTED.md", "scripts数", r"(\d+)\s*个\s*检查脚本", "scripts_engine"),
]


def check_docs(repo: Path) -> dict:
    actuals = get_actuals(repo)
    issues = []

    for doc_name, field_name, pattern, actual_key in DOC_PATTERNS:
        doc_path = repo / doc_name
        if not doc_path.exists():
            continue
        text = doc_path.read_text(encoding="utf-8", errors="replace")

        m = re.search(pattern, text)
        if not m:
            continue

        groups = m.groups()
        num_str = next((g for g in groups if g is not None and g.isdigit()), None)
        if num_str is None:
            continue

        claimed = int(num_str)
        actual = actuals.get(actual_key)
        if actual is None:
            continue
        if claimed != actual:
            issues.append({
                "source": doc_name,
                "field": field_name,
                "claimed": claimed,
                "actual": actual,
                "detail": f"建议改为变量引用（如 '参见 index.md'），避免硬编码数字漂移",
            })

    score = max(0, 10 - len(issues) * 2)
    return {
        "status": "pass" if not issues else "fail",
        "score": score,
        "issues": issues,
        "actuals": actuals,
    }


def main():
    parser = argparse.ArgumentParser(description="文档硬编码数字检测")
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent
    result = check_docs(repo)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["status"] == "pass":
            print("✅ 文档数字变量化: 全部一致")
        else:
            print(f"❌ 文档数字变量化: {len(result['issues'])} 处不一致\n")
            for i in result["issues"]:
                print(f"  📍 {i['source']} → {i['field']}: 声称 {i['claimed']} ≠ 实际 {i['actual']}")
                print(f"     {i['detail']}")
            print()
        print(f"实际计数: rules={result['actuals']['rules']}, patterns={result['actuals']['patterns']}, "
              f"anti_patterns={result['actuals']['anti_patterns']}, sessions={result['actuals']['sessions']}")

    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
