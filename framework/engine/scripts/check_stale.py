#!/usr/bin/env python3
"""check_stale.py -- 内容时效检查（三合一）

用法:
  python engine/scripts/check_stale.py --repo <知识库根目录>
  python engine/scripts/check_stale.py --repo . --mode content    # 过时 active 页面 (>90天)
  python engine/scripts/check_stale.py --repo . --mode drafts     # 滞留 draft (>30天)
  python engine/scripts/check_stale.py --repo . --mode field      # 缺失 updated 字段
  python engine/scripts/check_stale.py --repo . --mode all        # 全部（默认）
  python engine/scripts/check_stale.py --repo . --json
  python engine/scripts/check_stale.py --repo . --mode field --fix  # 自动补填 updated

合并自: check-stale-content.py + check-stale-drafts.py + check-updated-field.py
"""

import argparse
import json
import sys
from datetime import date, datetime
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
SCAN_DIRS = {"knowledge", "ops"}
TODAY = date.today()


def _load_evolution_config(repo: Path) -> dict:
    """读 engine/config/evolution-config.yaml（R-EVO 06 阈值配置化），失败返回空 dict 用默认值。"""
    cfg_path = repo / "engine" / "config" / "evolution-config.yaml"
    try:
        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _parse_frontmatter(file_path: Path) -> dict | None:
    """提取 YAML frontmatter，失败返回 None"""
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
    return data if isinstance(data, dict) else None


def _scan_md_files(repo: Path):
    """遍历 knowledge/ + ops/ 下所有 .md，跳过黑名单"""
    for f in sorted(repo.rglob("*.md")):
        if f.name in SKIP_FILES:
            continue
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        rel = f.relative_to(repo)
        if rel.parts[0] not in SCAN_DIRS:
            continue
        yield f


# ── mode: content ──

def check_content(repo: Path, max_age: int) -> list[dict]:
    """status=active 且 updated > max_age 天"""
    stale = []
    for f in _scan_md_files(repo):
        data = _parse_frontmatter(f)
        if not data or data.get("status") != "active":
            continue
        updated_str = data.get("updated", "")
        try:
            updated = datetime.strptime(str(updated_str), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue
        age = (TODAY - updated).days
        if age > max_age:
            rel = str(f.relative_to(repo))
            stale.append({"file": rel, "updated": str(updated), "age_days": age,
                          "title": data.get("summary", "")})
    return stale


# ── mode: drafts ──

def check_drafts(repo: Path, max_age: int) -> list[dict]:
    """status=draft 且滞留 > max_age 天"""
    stale = []
    for f in _scan_md_files(repo):
        data = _parse_frontmatter(f)
        if not data or data.get("status") != "draft":
            continue
        updated_str = data.get("updated", "")
        try:
            updated = datetime.strptime(str(updated_str), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            updated = datetime.fromtimestamp(f.stat().st_mtime).date()
        age = (TODAY - updated).days
        if age > max_age:
            rel = str(f.relative_to(repo))
            stale.append({"file": rel, "updated": str(updated), "age_days": age})
    return stale


# ── mode: field ──

def check_field(repo: Path, fix: bool = False) -> list[dict]:
    """status=active 且缺少 updated 字段"""
    results = []
    today_str = TODAY.isoformat()
    for f in _scan_md_files(repo):
        rel = str(f.relative_to(repo))
        data = _parse_frontmatter(f)
        if not data:
            results.append({"file": rel, "status": "skip", "issues": []})
            continue
        if data.get("status") != "active":
            results.append({"file": rel, "status": "pass", "issues": []})
            continue

        if "updated" not in data:
            if fix:
                # 自动补填
                try:
                    raw = f.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    results.append({"file": rel, "status": "error", "issues": ["读取失败"]})
                    continue
                lines = raw.split("\n")
                dashes = 0
                end_idx = None
                for i, line in enumerate(lines):
                    if line.strip() == "---":
                        dashes += 1
                        if dashes == 2:
                            end_idx = i
                            break
                if end_idx is not None:
                    lines.insert(end_idx, f"updated: {today_str}")
                    tmp = f.with_suffix(".tmp")
                    tmp.write_text("\n".join(lines), encoding="utf-8")
                    tmp.replace(f)
                    results.append({"file": rel, "status": "pass",
                                    "issues": [f"✅ 已自动补填 updated: {today_str}"]})
                else:
                    results.append({"file": rel, "status": "fail", "issues": ["缺少 updated 字段（无法自动修复）"]})
            else:
                results.append({"file": rel, "status": "fail", "issues": ["缺少 updated 字段"]})
        else:
            results.append({"file": rel, "status": "pass", "issues": []})
    return results


# ── main ──

def main(mode: str = "all", repo_path: str = None, json_out: bool = False,
         max_age: int = None, fix: bool = False):
    repo = Path(repo_path).resolve() if repo_path else Path(__file__).resolve().parent.parent.parent

    # 演化阈值从配置读（R-EVO 06），实例层可覆盖
    evo = _load_evolution_config(repo)
    stale_days = evo.get("stale_days", 90)
    draft_days = evo.get("draft_days", 30)
    if max_age is None:
        max_age = draft_days

    modes_to_run = ["content", "drafts", "field"] if mode == "all" else [mode]
    all_results = {}

    for m in modes_to_run:
        if m == "content":
            items = check_content(repo, max_age=stale_days)  # content 阈值来自 evolution-config
            all_results["content"] = {"label": f"内容过时 (>90天)", "items": items,
                                       "score": max(0, 10 - max(0, (len(items) - 10) // 5))}
        elif m == "drafts":
            items = check_drafts(repo, max_age=max_age)
            all_results["drafts"] = {"label": f"draft 滞留 (>{max_age}天)", "items": items,
                                      "score": max(0, 10 - (len(items) // 5))}
        elif m == "field":
            items = check_field(repo, fix=fix)
            failed = [r for r in items if r["status"] == "fail"]
            all_results["field"] = {"label": "updated 字段", "items": failed,
                                     "total_active": sum(1 for r in items if r["status"] != "skip"),
                                     "score": max(0, 10 - len(failed))}

    if json_out:
        output = {"status": "pass", "modes": {}}
        has_issues = False
        for m, data in all_results.items():
            output["modes"][m] = {k: v for k, v in data.items() if k != "items"}
            output["modes"][m]["count"] = len(data["items"])
            if len(data["items"]) > 0 and data["score"] < 10:
                has_issues = True
        output["status"] = "fail" if has_issues else "pass"
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for m, data in all_results.items():
            print(f"--- {data['label']}: {len(data['items'])} 个 ---")
            if m == "field":
                active = data.get("total_active", 0)
                failed = len(data["items"])
                print(f"  {active - failed}/{active} active 页面有 updated 字段")
                if failed:
                    for r in data["items"]:
                        print(f"  ❌ {r['file']}")
                else:
                    print("  ✅ 全部有 updated 字段")
            else:
                if data["items"]:
                    for s in sorted(data["items"], key=lambda x: x["age_days"], reverse=True):
                        print(f"  [{s['age_days']}天] {s['file']}")
                else:
                    print("  ✅ 无问题")
            print()

    any_issues = any(len(data["items"]) > 0 and data["score"] < 10 for data in all_results.values())
    return 1 if any_issues else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="内容时效检查（三合一）")
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--mode", type=str, default="all",
                        choices=["all", "content", "drafts", "field"])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max-age", type=int, default=30)
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args()
    sys.exit(main(mode=args.mode, repo_path=args.repo, json_out=args.json,
                  max_age=args.max_age, fix=args.fix))
