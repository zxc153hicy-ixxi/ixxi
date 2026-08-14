#!/usr/bin/env python3
"""fix-broken-links.py -- 批量修复 wikilink 断链

读取 check-links.py --mode broken 的结果，对每条断链尝试自动匹配目标，
生成修复建议供人类确认。

用法:
  python engine/scripts/fix-broken-links.py --repo . --dry-run     # 预览修复建议
  python engine/scripts/fix-broken-links.py --repo . --execute     # 交互式执行
  python engine/scripts/fix-broken-links.py --repo . --auto-accept # 自动接受高置信匹配
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKIP_FILES = {"Thumbs.db", ".DS_Store", "desktop.ini", ".gitkeep", ".placeholder"}


def get_broken_links(repo: Path) -> list[dict]:
    """调用 check-links.py --mode broken 获取断链列表"""
    checker = repo / "engine" / "scripts" / "check-links.py"
    result = subprocess.run(
        [sys.executable, str(checker), "--repo", str(repo), "--mode", "broken", "--json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0 and not result.stdout.strip():
        return []
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    return data.get("modes", {}).get("broken", {}).get("broken", [])


def find_best_match(link_target: str, source_file: Path, repo: Path) -> tuple[str | None, int]:
    stem = link_target.split("/")[-1]

    # 清理 stem 中的特殊字符（OCR 噪声）
    import re as _re
    stem_clean = _re.sub(r'[^\w一-鿿一-鿿\s.-]', '', stem)
    if not stem_clean or len(stem_clean) < 2:
        return (None, 0)

    try:
        # 策略1：在 knowledge/archive/ 中搜索（旧版文件）
        archive_matches = []
        for m in repo.rglob("*.md"):
            if "archive" in str(m).lower() and stem_clean in m.stem:
                archive_matches.append(m)
        if archive_matches:
            best = min(archive_matches, key=lambda p: len(str(p)))
            return (str(best.relative_to(repo))[:-3], 7)

        # 策略2：全库模糊搜索同名文件
        all_matches = list(repo.rglob(f"{stem_clean}.md"))
        all_matches = [m for m in all_matches if m.name not in SKIP_FILES]
        if len(all_matches) == 1:
            return (str(all_matches[0].relative_to(repo))[:-3], 9)
        elif len(all_matches) > 1:
            best = min(all_matches, key=lambda p: len(str(p)))
            return (str(best.relative_to(repo))[:-3], 5)

        # 策略3：目录引用
        try:
            dir_matches = list(repo.rglob(stem_clean))
            dir_matches = [d for d in dir_matches if d.is_dir()]
            if dir_matches:
                best = min(dir_matches, key=lambda p: len(str(p)))
                return (str(best.relative_to(repo)) + "/", 6)
        except Exception:
            pass
    except Exception:
        pass

    return (None, 0)


def fix_link_in_file(file_path: Path, old_target: str, new_target: str) -> bool:
    """在文件中替换一个 wikilink 目标"""
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False

    old_pattern = f"[[{old_target}]]"
    old_pattern_alias = f"[[{old_target}|"

    if old_pattern in text:
        new_text = text.replace(old_pattern, f"[[{new_target}]]")
    elif old_pattern_alias in text:
        new_text = text.replace(old_pattern_alias, f"[[{new_target}|")
    else:
        return False

    tmp = file_path.with_suffix(".tmp")
    tmp.write_text(new_text, encoding="utf-8")
    tmp.replace(file_path)
    return True


def main():
    parser = argparse.ArgumentParser(description="批量修复 wikilink 断链")
    parser.add_argument("--repo", type=str, default=None, help="知识库根目录")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--auto-accept", action="store_true", help="自动接受置信度≥7的匹配")
    parser.add_argument("--min-confidence", type=int, default=5, help="最低置信度阈值")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent

    broken = get_broken_links(repo)
    if not broken:
        print("✅ 无断链，无需修复")
        return 0

    print(f"分析 {len(broken)} 条断链...\n")

    suggestions = []
    auto_fixable = []
    manual_needed = []
    unfixable = []

    for b in broken:
        source = repo / b["source"]
        target = b["target"]

        match, confidence = find_best_match(target, source, repo)

        entry = {
            "source": b["source"],
            "old_target": target,
            "new_target": match,
            "confidence": confidence,
        }

        if match and confidence >= 7:
            auto_fixable.append(entry)
        elif match and confidence >= args.min_confidence:
            suggestions.append(entry)
        else:
            unfixable.append(entry)

    # 输出分析结果
    if auto_fixable:
        print(f"🔧 可自动修复 ({len(auto_fixable)} 条，置信度 ≥7):")
        for s in auto_fixable:
            print(f"  {s['source']}")
            print(f"    [[{s['old_target']}]] → [[{s['new_target']}]] (置信度 {s['confidence']})")

    if suggestions:
        print(f"\n❓ 需确认 ({len(suggestions)} 条，置信度 5-6):")
        for s in suggestions:
            print(f"  {s['source']}")
            print(f"    [[{s['old_target']}]] → [[{s['new_target']}]] (置信度 {s['confidence']})")

    if unfixable:
        print(f"\n❌ 无法匹配 ({len(unfixable)} 条):")
        for u in unfixable:
            print(f"  {u['source']}: [[{u['old_target']}]]")

    if args.json:
        print(json.dumps({
            "auto_fixable": len(auto_fixable),
            "needs_confirmation": len(suggestions),
            "unfixable": len(unfixable),
            "items": auto_fixable + suggestions + unfixable,
        }, ensure_ascii=False, indent=2))
        return 0

    if not args.execute:
        print(f"\n💡 加 --execute 执行修复（高置信自动修 + 中置信交互确认）")
        print(f"   加 --auto-accept 自动接受所有置信度 ≥{args.min_confidence} 的匹配")
        return 0

    # 执行修复
    fixed = 0
    # 自动修复高置信项
    if args.auto_accept:
        fixable = auto_fixable + suggestions
    else:
        fixable = auto_fixable

    for s in fixable:
        source_path = repo / s["source"]
        if fix_link_in_file(source_path, s["old_target"], s["new_target"]):
            print(f"  ✅ {s['source']}: [[{s['old_target']}]] → [[{s['new_target']}]]")
            fixed += 1
        else:
            print(f"  ⚠️ {s['source']}: 替换失败（文本中未找到原始链接）")

    print(f"\n修复完成: {fixed}/{len(fixable)} 条")

    if suggestions and not args.auto_accept:
        print(f"\n还有 {len(suggestions)} 条需确认，加 --auto-accept 自动处理。")

    print(f"\n{len(unfixable)} 条无法自动修复，需人工处理。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
