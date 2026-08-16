#!/usr/bin/env python3
"""check-version-consistency.py -- CHANGELOG.md 最新版本 ↔ git tag 最新 semver 交叉校验

版本号单一事实源 = git tag（见 CHANGELOG.md「版本号约定」），AGENT.md 不写版本号。

用法:
  python engine/scripts/check-version-consistency.py --repo <framework 目录>
  python engine/scripts/check-version-consistency.py --repo . --json
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

CHANGELOG_RE = re.compile(r"\[([0-9]+\.[0-9]+\.[0-9]+)\]")
TAG_RE = re.compile(r"^v([0-9]+\.[0-9]+\.[0-9]+)$")


def extract_changelog_version(repo: Path) -> str | None:
    """从仓库根 CHANGELOG.md 匹配第一个「## [x.y.z]」标题（跳过 [Unreleased]）"""
    changelog = repo.parent / "CHANGELOG.md"
    if not changelog.exists():
        return None
    try:
        text = changelog.read_text(encoding="utf-8")
    except Exception:
        return None
    m = CHANGELOG_RE.search(text)
    return m.group(1) if m else None


def get_latest_git_tag(repo: Path) -> str | None:
    """在仓库根取最新 semver git tag（vX.Y.Z，排除 -pre / baseline 等非发布 tag）"""
    result = subprocess.run(
        ["git", "-C", str(repo.parent), "tag", "-l"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        return None
    versions = [m.group(1) for t in result.stdout.splitlines() if (m := TAG_RE.match(t.strip()))]
    if not versions:
        return None
    return max(versions, key=lambda v: tuple(int(x) for x in v.split(".")))


def main():
    parser = argparse.ArgumentParser(description="版本号一致性检查（CHANGELOG ↔ git tag）")
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent

    changelog_ver = extract_changelog_version(repo)
    tag_ver = get_latest_git_tag(repo)

    issues = []

    # 两者都缺失 → 版本机制未建立，跳过
    if changelog_ver is None and tag_ver is None:
        pass
    elif changelog_ver is None:
        issues.append(f"CHANGELOG.md 未找到版本号（## [x.y.z]），但存在 git tag v{tag_ver}")
    elif tag_ver is None:
        issues.append(f"git 无 semver tag（vX.Y.Z），但 CHANGELOG 最新版本 {changelog_ver}")
    elif changelog_ver != tag_ver:
        issues.append(f"版本不一致: CHANGELOG={changelog_ver}, git tag={tag_ver}")

    score = 10 if not issues else max(0, 10 - len(issues) * 3)

    if args.json:
        print(json.dumps({
            "status": "pass" if not issues else "fail",
            "changelog": changelog_ver,
            "git_tag": tag_ver,
            "issues": issues,
            "score": score,
        }, ensure_ascii=False, indent=2))
    else:
        consistent = changelog_ver is not None and changelog_ver == tag_ver
        print("版本一致性（CHANGELOG ↔ git tag）:")
        print(f"  CHANGELOG 最新: {changelog_ver or '❌ 未找到'}")
        print(f"  git tag 最新:   {tag_ver or '❌ 未找到'}")
        print(f"  是否一致: {'✅ 是' if consistent else '❌ 否'}")
        if issues:
            print("\n❌ 问题:")
            for i in issues:
                print(f"  - {i}")

    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
