#!/usr/bin/env python3
"""check-hardcoded-paths.py -- 扫描 .md 正文中的硬编码绝对路径

用法:
  python engine/scripts/check-hardcoded-paths.py --repo <知识库根目录>
  python engine/scripts/check-hardcoded-paths.py --repo . --json
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
SKIP_DIRS = {".git", "__pycache__", ".fix-backup", "node_modules", "assets", "media", "_external", ".claude", ".agents", ".codex"}
# archive/ 为历史快照，允许含旧路径
SKIP_PATH_PREFIXES = (
    "knowledge/archive/",
    "knowledge/projects/",      # 项目文件引用历史路径
    "knowledge/reference/",     # 参考资料中的路径示例
    "knowledge/learning/",      # 导入学习资料可能含原始路径
    "engine/templates/",
    "raw/",                     # 会话摘要记录操作路径
    "docs/",                    # 使用规范/维护手册中的路径示例（脱敏示例、检查标准）
    "ops/rules/",               # 规则定义中含检查标准示例路径（T1/C2自引用）
    "ops/queries/checkpoints/", # 检查报告记录发现的问题路径
    "ops/anti-patterns/",       # 反模式文档引用的路径示例
    "ops/framework-patterns/",  # 正模式文档引用的路径示例
)
SKIP_INDIVIDUAL_FILES = {
    "log.md",                   # 操作日志记录历史路径变更
}
SCAN_DIRS = {"knowledge", "ops", "engine/scripts"}  # 检查 .md 正文（非脚本内）

# 硬编码模式——检查任何绝对路径（而非特定机器的路径）
PATTERNS = [
    (re.compile(r"[A-Za-z]:[/\\]Users[/\\]"), "用户目录（C:/Users/）"),
    (re.compile(r"[A-Za-z]:[/\\](?![/\\])"), "Windows 盘符绝对路径"),
    (re.compile(r"/(?:home|Users|mnt)/"), "Unix 绝对路径"),
]


def main():
    parser = argparse.ArgumentParser(description="硬编码路径检查")
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent

    hits = []
    for f in sorted(repo.rglob("*.md")):
        if f.name in SKIP_FILES:
            continue
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        rel = str(f.relative_to(repo))
        rel_norm = rel.replace("\\", "/")
        if any(rel_norm.startswith(p) for p in SKIP_PATH_PREFIXES):
            continue
        if rel_norm in SKIP_INDIVIDUAL_FILES:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        for pattern, label in PATTERNS:
            for m in pattern.finditer(text):
                # 跳过代码块内的路径（``` 之间）
                line_start = text.rfind("\n", 0, m.start()) + 1
                line = text[line_start:text.find("\n", m.start())]
                hits.append({
                    "file": rel,
                    "pattern": label,
                    "line": line.strip()[:120],
                })

    score = max(0, 10 - len(hits) // 5)

    if args.json:
        print(json.dumps({
            "status": "pass" if score >= 10 else "fail",
            "count": len(hits),
            "issues": hits,
            "score": score,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"硬编码路径检查: {len(hits)} 处")
        if hits:
            for h in hits:
                print(f"  {h['file']}")
                print(f"    [{h['pattern']}] {h['line']}")
        else:
            print("✅ 无硬编码绝对路径")

    return 0 if not hits else 1


if __name__ == "__main__":
    sys.exit(main())
