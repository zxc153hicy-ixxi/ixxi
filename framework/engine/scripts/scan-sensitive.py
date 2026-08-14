#!/usr/bin/env python3
"""scan-sensitive.py -- 敏感信息扫描：身份证/银行卡/手机号/密码/API Key

用法:
  python engine/scripts/scan-sensitive.py --repo <知识库根目录>
  python engine/scripts/scan-sensitive.py --repo . --json
  python engine/scripts/scan-sensitive.py --stdin          # 从 stdin 读（git diff 管道）
"""

import argparse
import json
import re
import sys
from pathlib import Path

# GBK 终端兜底
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 敏感信息正则模式
PATTERNS = {
    "身份证": re.compile(r"[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]"),
    "银行卡": re.compile(r"\b([1-9]\d{15,18})\b"),
    "手机号": re.compile(r"1[3-9]\d{9}"),
    "密码明文": re.compile(r"(password|passwd|pwd|密钥|secret|token)\s*[=:：]\s*\S+", re.IGNORECASE),
    "API_Key": re.compile(r"(sk-[a-zA-Z0-9]{20,}|AIza[0-9A-Za-z_-]{35})"),
    "私钥头": re.compile(r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----"),
}

SKIP_FILES = {"Thumbs.db", ".DS_Store", "desktop.ini", ".gitkeep", ".placeholder"}
SKIP_DIRS = {".git", "__pycache__", ".fix-backup", "node_modules", "_external"}
SKIP_ROOT_DIRS = {".claudian", "docs", "raw", ".obsidian", ".claude", ".agents"}  # .agents=Codex技能适配层副本（源.claude已跳过）  # 跳过根目录下的这些目录
# 学习/教学材料目录——自然包含安全示例（密码、手机号等），非真实泄露
SKIP_SENSITIVE_DIRS = {
    "knowledge/learning/网络安全",
    "knowledge/learning/华为数通-HCIP",
    "knowledge/learning/系统架构设计师",
    "knowledge/learning/HCIA-Cloud-Service",
    "engine/templates",  # 扫描器自身模板
}


def scan_text(text: str, source: str) -> list[dict]:
    """扫描一段文本，返回命中列表"""
    hits = []
    for label, pattern in PATTERNS.items():
        for m in pattern.finditer(text):
            # 截断显示，避免输出完整敏感信息
            snippet = m.group()[:40]
            hits.append({
                "type": label,
                "source": source,
                "snippet": snippet,
                "pos": m.start(),
            })
    return hits


def scan_file(path: Path) -> list[dict]:
    """扫描单个文件"""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    return scan_text(text, str(path))


def scan_repo(repo_root: Path) -> list[dict]:
    """扫描整个仓库的 .md 和 .py 文件"""
    all_hits = []
    for f in sorted(repo_root.rglob("*")):
        if f.name in SKIP_FILES:
            continue
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        rel = f.relative_to(repo_root)
        first_part = rel.parts[0] if rel.parts else ""
        if first_part in SKIP_ROOT_DIRS:
            continue
        rel_str = str(rel).replace("\\", "/")
        if any(rel_str.startswith(d) for d in SKIP_SENSITIVE_DIRS):
            continue
        if f.is_file() and f.suffix.lower() in (".md", ".py", ".sh", ".toml", ".yaml", ".yml", ".json", ".txt"):
            all_hits.extend(scan_file(f))
    return all_hits


def main():
    parser = argparse.ArgumentParser(description="敏感信息扫描")
    parser.add_argument("--repo", type=str, default=None, help="知识库根目录")
    parser.add_argument("--stdin", action="store_true", help="从 stdin 读取")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    hits = []

    if args.stdin:
        text = sys.stdin.read()
        hits = scan_text(text, "<stdin>")
    elif args.repo:
        repo = Path(args.repo).resolve()
        hits = scan_repo(repo)
    else:
        repo = Path(__file__).resolve().parent.parent.parent
        hits = scan_repo(repo)

    if args.json:
        output = {
            "status": "pass" if not hits else "fail",
            "issues": [{"type": h["type"], "source": h["source"], "snippet": h["snippet"]} for h in hits],
            "score": 10 if not hits else 0,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        if not hits:
            print("✅ 敏感扫描通过：未发现敏感信息")
        else:
            print(f"❌ 敏感扫描发现 {len(hits)} 处疑似敏感信息：")
            for h in hits:
                print(f"  [{h['type']}] {h['source']}")
                print(f"         {h['snippet']}...")

    return 0 if not hits else 1


if __name__ == "__main__":
    sys.exit(main())
