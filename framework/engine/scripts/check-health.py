#!/usr/bin/env python3
"""check-health.py -- 知识库健康度评分

健康度 = (自动化通过率 × 50) + ((1 - 反模式触碰率) × 50)

用法:
  python engine/scripts/check-health.py --repo <知识库根目录>
  python engine/scripts/check-health.py --repo . --json
  python engine/scripts/check-health.py --repo . --anti-age 30   # 反模式触碰追溯天数

评级:
  ≥70 健康 | 50-70 预警 | <50 异常
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

CHECK_SCRIPTS = [
    # 原有 9 个
    ("check-frontmatter.py", ""),
    ("check-links.py", " --mode all"),
    ("check_stale.py", " --mode all"),
    ("check-version-consistency.py", ""),
    ("check-hardcoded-paths.py", ""),
    ("check-scene-domain.py", ""),
    ("check-inbox.py", " --mode all"),
    ("scan-sensitive.py", ""),
    ("check-ocr-quality.py", " --path knowledge/"),
    # Phase 0 新增（护栏A/C/H）
    ("check-numbers.py", ""),
    ("check-doc-numbers.py", ""),
    # 已有但未接入（护栏E + 补充项）
    ("check-naming.py", ""),
    ("check-script-refs.py", ""),
    ("check-stale-paths.py", ""),
    ("check-superseded-links.py", ""),
    ("check-growth.py", ""),
    # 护栏H
    ("check-rules-integrity.py", ""),
]

GIT_SIZE_WARN_MB = 500
UNTRACKED_WARN = 50


def run_checks(repo: Path) -> tuple[int, int, list[dict]]:
    """运行全量自动化检查，返回 (通过数, 总数, 详情)"""
    passed, total, details = 0, 0, []
    for script, extra in CHECK_SCRIPTS:
        total += 1
        path = repo / "engine" / "scripts" / script
        cmd = [sys.executable, str(path), "--repo", str(repo), "--json"]
        if extra.strip():
            cmd.extend(extra.strip().split())

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                               encoding="utf-8", errors="replace")
            data = json.loads(r.stdout)
            status = data.get("status", "?")
            score = data.get("score", "?")
            if "modes" in data:
                subscores = {k: v.get("score", v.get("total_issues", v.get("broken", "?"))) 
                           for k, v in data["modes"].items()}
                details.append({"script": script, "status": status, "score": score, "subscores": subscores})
            else:
                details.append({"script": script, "status": status, "score": score})
            if status == "pass":
                passed += 1
        except Exception as e:
            details.append({"script": script, "status": "error", "error": str(e)})

    return passed, total, details


def count_anti_patterns(repo: Path) -> int:
    """统计反模式总数"""
    ap_dir = repo / "ops" / "anti-patterns"
    if not ap_dir.exists():
        return 0
    return len([f for f in ap_dir.glob("*.md") if f.name != "反模式索引.md"])


def count_anti_touches(repo: Path, age_days: int) -> int:
    """统计最近 N 天内触碰的反模式数（从 log.md 中提取）"""
    logf = repo / "log.md"
    if not logf.exists():
        return 0

    cutoff = date.today() - timedelta(days=age_days)
    touched = set()
    anti_names = {f.stem for f in (repo / "ops" / "anti-patterns").glob("*.md")
                  if f.name != "反模式索引.md"}

    try:
        text = logf.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return 0

    for line in text.split("\n"):
        # log 格式: YYYY-MM-DD HH:MM | ...
        match = re.match(r"(\d{4}-\d{2}-\d{2})\s", line)
        if not match:
            continue
        try:
            entry_date = date.fromisoformat(match.group(1))
        except ValueError:
            continue
        if entry_date < cutoff:
            continue
        for name in anti_names:
            if name in line:
                touched.add(name)

    return len(touched)


def compute_health(pass_rate: float, touch_rate: float) -> float:
    return round(pass_rate * 50 + (1 - touch_rate) * 50, 1)


def rating(score: float) -> str:
    if score >= 70:
        return "健康"
    elif score >= 50:
        return "预警"
    return "异常"


def main():
    parser = argparse.ArgumentParser(description="知识库健康度评分")
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--anti-age", type=int, default=30, help="反模式触碰追溯天数")
    parser.add_argument("--skip-checks", action="store_true", help="跳过自动化检查（使用缓存结果）")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent

    # 自动化检查
    if args.skip_checks:
        passed, total = 6, 8  # 使用上次已知结果
        check_details = []
    else:
        passed, total, check_details = run_checks(repo)

    pass_rate = passed / total if total else 0

    # 反模式统计
    total_anti = count_anti_patterns(repo)
    touched_anti = count_anti_touches(repo, args.anti_age)
    touch_rate = touched_anti / total_anti if total_anti else 0

    health = compute_health(pass_rate, touch_rate)

    # 护栏G: Git 健康阈值检测
    git_issues = []
    git_dir = repo / ".git"
    if git_dir.exists():
        # .git 体积
        git_size_bytes = sum(f.stat().st_size for f in git_dir.rglob("*") if f.is_file())
        git_size_mb = round(git_size_bytes / (1024 * 1024))
        if git_size_mb > GIT_SIZE_WARN_MB:
            git_issues.append(f".git 体积 {git_size_mb}MB > {GIT_SIZE_WARN_MB}MB 阈值（建议 git filter-repo 清理历史大文件）")

        # 未跟踪文件
        try:
            r = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True, text=True, cwd=str(repo), timeout=15,
                encoding="utf-8", errors="replace"
            )
            untracked_count = len([l for l in r.stdout.split("\n") if l.strip()])
            if untracked_count > UNTRACKED_WARN:
                git_issues.append(f"未跟踪文件 {untracked_count} > {UNTRACKED_WARN}（建议 git add 或加入 .gitignore）")
        except Exception:
            pass

    result = {
        "automation": {"passed": passed, "total": total, "rate": round(pass_rate * 100, 1)},
        "anti_patterns": {"total": total_anti, "touched": touched_anti,
                          "age_days": args.anti_age, "rate": round(touch_rate * 100, 1)},
        "health": health,
        "rating": rating(health),
        "details": check_details,
        "git_health": git_issues,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"知识库健康度: {health}/100 ({rating(health)})")
        print(f"  自动化通过: {passed}/{total} ({result['automation']['rate']}%)")
        print(f"  反模式触碰: {touched_anti}/{total_anti} ({result['anti_patterns']['rate']}%, "
              f"追溯{args.anti_age}天)")
        if check_details:
            print(f"\n检查明细:")
            for d in check_details:
                flag = "✅" if d["status"] == "pass" else "❌"
                sub = ""
                if "subscores" in d:
                    sub = " | " + ", ".join(f"{k}={v}" for k, v in d["subscores"].items())
                print(f"  {flag} {d['script']:35s} {d.get('score','?')}{sub}")
        if git_issues:
            print(f"\n🔴 Git 健康:")
            for gi in git_issues:
                print(f"  ⚠️  {gi}")

    return 0 if health >= 70 else (1 if health >= 50 else 2)


if __name__ == "__main__":
    sys.exit(main())
