#!/usr/bin/env python3
"""fix-activation.py -- 按实际目录结构重写 activation.md

扫描 knowledge/ ops/ engine/ raw/ 等目录，与旧 activation.md 对比，
生成新版文件。

用法:
  python engine/scripts/fix-activation.py --repo . --dry-run
  python engine/scripts/fix-activation.py --repo . --execute
"""

import argparse
import sys
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKIP_FILES = {"Thumbs.db", ".DS_Store", "desktop.ini", ".gitkeep", ".placeholder"}
SKIP_DIRS = {".git", "__pycache__", ".fix-backup", "node_modules", "_external", ".obsidian", ".claudian", ".mineru-tmp"}
SKIP_FULL_DIRS = {".claude/kb/skills", ".claude/kb/agents", ".claude/kb/hooks", "engine/__pycache__"}
SCAN_ROOTS = ["knowledge", "ops", "engine", "raw", ".inbox", ".claude"]
TODAY = date.today().isoformat()


def scan_directory(root: Path, repo_root: Path, prefix: str = "") -> list[str]:
    """递归扫描目录，返回树形列表"""
    entries = []
    try:
        items = sorted(root.iterdir())
    except PermissionError:
        return entries

    dirs = [d for d in items if d.is_dir() and d.name not in SKIP_DIRS]
    files = [f for f in items if f.is_file() and f.name not in SKIP_FILES]

    for d in dirs:
        # 跳过文件极多的外部目录
        rel = str(d.relative_to(repo_root)).replace("\\", "/")
        skip = False
        for sd in SKIP_FULL_DIRS:
            if rel == sd or rel.startswith(sd + "/"):
                skip = True
                break
        if skip:
            continue
        path = f"{prefix}{d.name}/"
        entries.append(path)
        entries.extend(scan_directory(d, repo_root, prefix + "  "))

    for f in files:
        entries.append(f"{prefix}{f.name}")

    return entries


def generate_activation(repo: Path) -> str:
    """生成 activation.md 内容"""
    lines = [
        "# 目录激活清单",
        "",
        f"> 自动生成于 {TODAY}。列出知识库所有目录和关键文件，用于核对完整性。",
        "",
    ]

    for root_name in SCAN_ROOTS:
        root_path = repo / root_name
        if not root_path.exists():
            lines.append(f"## {root_name}/")
            lines.append("> 目录不存在")
            lines.append("")
            continue

        lines.append(f"## {root_name}/")
        entries = scan_directory(root_path, repo)
        for entry in entries:
            lines.append(f"- {entry}")
        lines.append("")

    lines.append("---")
    lines.append(f"最后更新: {TODAY}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="重写 activation.md")
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent
    activation = repo / "activation.md"

    new_content = generate_activation(repo)

    if args.dry_run:
        old_exists = activation.exists()
        if old_exists:
            old_lines = len(activation.read_text(encoding="utf-8").split("\n"))
            new_lines = len(new_content.split("\n"))
            print(f"[DRY RUN] activation.md 重写预览:")
            print(f"  旧文件: {'存在' if old_exists else '不存在'} ({old_lines if old_exists else 0} 行)")
            print(f"  新文件: {new_lines} 行")
            print(f"  差异: {new_lines - (old_lines if old_exists else 0):+d} 行")
        else:
            print(f"[DRY RUN] activation.md 不存在，将新建 ({len(new_content.split(chr(10)))} 行)")
        print(f"\n💡 加 --execute 执行写入。")
    else:
        tmp = activation.with_suffix(".tmp")
        tmp.write_text(new_content, encoding="utf-8")
        tmp.replace(activation)
        print(f"✅ activation.md 已重写 ({len(new_content.split(chr(10)))} 行)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
