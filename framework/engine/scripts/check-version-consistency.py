#!/usr/bin/env python3
"""check-version-consistency.py -- AGENT.md / log.md / 设计方案 版本号三方交叉校验

用法:
  python engine/scripts/check-version-consistency.py --repo <知识库根目录>
  python engine/scripts/check-version-consistency.py --repo . --json
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

VERSION_RE = re.compile(r"[Vv](\d+\.\d+\.\d+)")


def extract_agent_version(repo: Path) -> tuple[str | None, str]:
    """从 AGENT.md 标题行提取版本号"""
    agent = repo / "AGENT.md"
    if not agent.exists():
        return None, "AGENT.md 不存在"
    try:
        text = agent.read_text(encoding="utf-8")
    except Exception as e:
        return None, f"读取失败: {e}"
    m = VERSION_RE.search(text)
    return (m.group(1), "") if m else (None, "AGENT.md 中未找到版本号")


def extract_log_version(repo: Path) -> tuple[str | None, str]:
    """从 log.md 最新版本记录提取"""
    logf = repo.parent / "personal" / "data" / "log.md"
    if not logf.exists():
        return None, "log.md 不存在"
    try:
        text = logf.read_text(encoding="utf-8")
    except Exception as e:
        return None, f"读取失败: {e}"

    # 找所有版本号，取最后一个
    versions = VERSION_RE.findall(text)
    return (versions[0], "") if versions else (None, "log.md 中未找到版本记录")


def main():
    parser = argparse.ArgumentParser(description="版本号一致性检查")
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent

    agent_ver, agent_err = extract_agent_version(repo)
    log_ver, log_err = extract_log_version(repo)

    issues = []
    versions = {"AGENT.md": agent_ver, "log.md": log_ver}

    if agent_err:
        issues.append(f"AGENT.md: {agent_err}")
    if log_err:
        issues.append(f"log.md: {log_err}")

    if agent_ver and log_ver:
        if agent_ver != log_ver:
            issues.append(f"版本不一致: AGENT.md={agent_ver}, log.md={log_ver}")
    elif agent_ver and not log_ver:
        issues.append("log.md 缺少版本记录")

    score = 10 if not issues else max(0, 10 - len(issues) * 3)

    if args.json:
        print(json.dumps({
            "status": "pass" if not issues else "fail",
            "versions": versions,
            "issues": issues,
            "score": score,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"版本号一致性:")
        print(f"  AGENT.md: {agent_ver or '❌ 未找到'}")
        print(f"  log.md:    {log_ver or '❌ 未找到'}")
        if issues:
            print(f"\n❌ 问题:")
            for i in issues:
                print(f"  - {i}")
        else:
            print("✅ 版本号一致")

    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
