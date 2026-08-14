#!/usr/bin/env python3
"""check-scene-domain.py -- YAML scene/domain 字段与文件所在目录一致性

用法:
  python engine/scripts/check-scene-domain.py --repo <知识库根目录>
  python engine/scripts/check-scene-domain.py --repo . --json
"""

import argparse
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    import yaml
except ImportError:
    sys.exit("需要 PyYAML: pip install pyyaml")

SKIP_FILES = {"Thumbs.db", ".DS_Store", "desktop.ini", ".gitkeep", ".placeholder"}
SKIP_DIRS = {".git", "__pycache__", ".fix-backup", "node_modules", "assets", "media"}
# archive/ 中文件已冻结，无 scene/domain 不视为问题
SKIP_PATH_PREFIXES = (
    "knowledge/archive/",
    "knowledge/projects/",  # 项目文件 scene 描述项目领域，非目录位置
    "ops/patterns/",        # scene 描述模式所属领域，非文件位置
    "ops/anti-patterns/",   # scene 描述反模式所属领域，非文件位置
    "ops/hermes/",          # Hermes 专属内容
)
SCAN_DIRS = {"knowledge", "ops"}


def check_file(file_path: Path, repo: Path) -> dict | None:
    rel = str(file_path.relative_to(repo))
    try:
        raw = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    if not raw.startswith("---"):
        return None

    parts = raw.split("---", 2)
    if len(parts) < 3:
        return None

    try:
        data = yaml.safe_load(parts[1]) or {}
    except Exception:
        return None

    if not isinstance(data, dict):
        return None

    scene = data.get("scene")
    domain = data.get("domain")
    if not scene and not domain:
        return None  # 无这些字段则跳过

    # 从路径推断 scene/domain
    parts_list = list(file_path.relative_to(repo).parts)
    # 场景通常是第一级子目录
    inferred_scene = parts_list[0] if len(parts_list) > 0 else None
    # domain 通常是第二级
    inferred_domain = parts_list[1] if len(parts_list) > 1 else None

    issues = []
    if scene and inferred_scene and scene != inferred_scene:
        issues.append(f"scene 不一致: YAML={scene}, 目录={inferred_scene}")
    if domain and inferred_domain and domain != inferred_domain:
        issues.append(f"domain 不一致: YAML={domain}, 目录={inferred_domain}")

    return {"file": rel, "issues": issues} if issues else None


def main():
    parser = argparse.ArgumentParser(description="scene/domain 一致性")
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent

    results = []
    for f in sorted(repo.rglob("*.md")):
        if f.name in SKIP_FILES:
            continue
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        rel = f.relative_to(repo)
        if rel.parts[0] not in SCAN_DIRS:
            continue
        rel_str = str(rel).replace("\\", "/")
        if any(rel_str.startswith(p) for p in SKIP_PATH_PREFIXES):
            continue
        r = check_file(f, repo)
        if r:
            results.append(r)

    score = max(0, 10 - len(results))

    if args.json:
        print(json.dumps({
            "status": "pass" if score >= 10 else "fail",
            "mismatches": len(results),
            "issues": results,
            "score": score,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"scene/domain 一致性: {len(results)} 处不匹配")
        if results:
            for r in results:
                print(f"  {r['file']}")
                for issue in r["issues"]:
                    print(f"    - {issue}")
        else:
            print("✅ 全部一致")

    return 0 if not results else 1


if __name__ == "__main__":
    sys.exit(main())
