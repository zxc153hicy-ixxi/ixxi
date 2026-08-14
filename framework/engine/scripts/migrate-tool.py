#!/usr/bin/env python3
"""migrate-tool.py —— ixxi 迁移工具（Task 4.1：迁移 dry-run + rollback）

MVP 骨架三子命令：
  backup              备份 personal/ → personal/.backup/<时间戳>/（含 meta.json 清单）
  migrate --dry-run   预演迁移：列出 MIGRATION_STEPS 步骤 + 影响文件数，不落盘
  rollback --to <目标> 从 .backup/<时间戳>/ 恢复 personal/；恢复前先把当前状态
                       备份到 .backup/pre-rollback/<时间戳>/，防回退本身失败

实际迁移步骤（数据替换 / 场景注册 / skill 迁移，对齐 docs/guides/demo到真实迁移指南.md）
本版留桩：migrate 逐条打印进度但不动文件。本版保证的是「迁移前能备份、迁移失败
能回退」的可回退护栏（智谱风险 7.1）。

零第三方依赖：仅标准库 argparse / shutil / pathlib / datetime / json。

用法示例：
  python engine/scripts/migrate-tool.py backup
  python engine/scripts/migrate-tool.py backup --personal /path/to/personal
  python engine/scripts/migrate-tool.py migrate --dry-run
  python engine/scripts/migrate-tool.py migrate            # 骨架：逐条执行（留桩，不动文件）
  python engine/scripts/migrate-tool.py rollback --to 2026-08-14_143000 -y
  python engine/scripts/migrate-tool.py rollback           # 列出可用备份
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BACKUP_DIRNAME = ".backup"
PRE_ROLLBACK_DIRNAME = "pre-rollback"
MANIFEST = "meta.json"
SKIP_NAMES = {BACKUP_DIRNAME}  # 备份/清空/恢复时排除（自身）

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_PERSONAL = REPO_ROOT / "personal"


# ── 通用工具 ────────────────────────────────────────
def _personal_path(args) -> Path:
    return Path(args.personal).resolve() if args.personal else DEFAULT_PERSONAL


def _require_personal(personal: Path) -> None:
    if not personal.is_dir():
        print(f"❌ personal 目录不存在：{personal}")
        sys.exit(1)


def _count_files(d: Path) -> int:
    if not d.exists():
        return 0
    return sum(1 for p in d.rglob("*") if p.is_file())


def _copy_contents(src: Path, dest: Path) -> None:
    """把 src 下所有内容复制到 dest，排除 .backup 自身。"""
    dest.mkdir(parents=True, exist_ok=True)
    for item in sorted(src.iterdir()):
        if item.name in SKIP_NAMES:
            continue
        if item.is_dir():
            shutil.copytree(item, dest / item.name)
        else:
            shutil.copy2(item, dest / item.name)


def _clear_personal(personal: Path) -> None:
    """清空 personal/ 下所有内容，保留 .backup。"""
    for item in personal.iterdir():
        if item.name in SKIP_NAMES:
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def _restore_from(src: Path, personal: Path) -> int:
    """从备份目录恢复内容到 personal（跳过 meta.json 清单），返回恢复的文件数。"""
    restored = 0
    for item in sorted(src.iterdir()):
        if item.name == MANIFEST:
            continue
        if item.is_dir():
            shutil.copytree(item, personal / item.name)
            restored += _count_files(item)
        else:
            shutil.copy2(item, personal / item.name)
            restored += 1
    return restored


def _read_manifest(d: Path) -> dict | None:
    m = d / MANIFEST
    if not m.exists():
        return None
    try:
        return json.loads(m.read_text(encoding="utf-8"))
    except Exception:
        return None


def _list_backups(personal: Path) -> list[Path]:
    root = personal / BACKUP_DIRNAME
    if not root.exists():
        return []
    return [d for d in sorted(root.iterdir())
            if d.is_dir() and d.name != PRE_ROLLBACK_DIRNAME]


# ── 迁移步骤定义（骨架，对齐 docs/guides/demo到真实迁移指南.md）─────────
def _est_step1(personal: Path) -> tuple[int, str]:
    inbox = personal / "raw" / "inbox"
    n = _count_files(inbox)
    return n, "数据替换：真实资料放入 raw/inbox 替换演示数据"


def _est_step2(personal: Path) -> tuple[int, str]:
    reg = personal / "scene-registry.md"
    if not reg.exists():
        return 1, "场景注册：创建 scene-registry.md 并登记第一个场景"
    text = reg.read_text(encoding="utf-8", errors="replace")
    entries = sum(1 for ln in text.splitlines() if ln.startswith("| S"))
    return 1, f"场景注册：scene-registry.md 追加 1 行（已有 {entries} 个场景）"


def _est_step3(personal: Path) -> tuple[int, str]:
    skills = personal / ".claude" / "skills" / "personal"
    n = sum(1 for f in skills.rglob("SKILL.md")) if skills.exists() else 0
    return n, f"skill 迁移：登记 {n} 个 personal skill 并跑 sync"


def _stub_execute(personal: Path) -> None:
    print("    [留桩] 本步未实现——骨架阶段仅保证 backup / dry-run / rollback，"
          "实际迁移步骤在后续任务落地")


MIGRATION_STEPS = [
    {"id": "step1", "name": "数据替换", "estimate": _est_step1, "execute": _stub_execute},
    {"id": "step2", "name": "场景注册", "estimate": _est_step2, "execute": _stub_execute},
    {"id": "step3", "name": "skill 迁移", "estimate": _est_step3, "execute": _stub_execute},
]
STEP_IDS = {s["id"] for s in MIGRATION_STEPS}


# ── 子命令实现 ──────────────────────────────────────
def cmd_backup(args) -> int:
    personal = _personal_path(args)
    _require_personal(personal)
    backup_root = personal / BACKUP_DIRNAME
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dest = backup_root / ts
    dest.mkdir(parents=True, exist_ok=True)

    files = []
    for item in sorted(personal.iterdir()):
        if item.name in SKIP_NAMES:
            continue
        if item.is_dir():
            shutil.copytree(item, dest / item.name)
            files.extend(str(p.relative_to(personal)).replace("\\", "/")
                         for p in item.rglob("*") if p.is_file())
        else:
            shutil.copy2(item, dest / item.name)
            files.append(item.name)

    meta = {
        "tool": "migrate-tool.py",
        "command": "backup",
        "backup_time": datetime.now().isoformat(timespec="seconds"),
        "source": str(personal),
        "file_count": len(files),
        "files": sorted(files),
    }
    (dest / MANIFEST).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ backup 完成：{personal} → {dest}")
    print(f"   备份 {len(files)} 个文件（清单 {MANIFEST}）")
    return 0


def cmd_migrate(args) -> int:
    personal = _personal_path(args)
    _require_personal(personal)

    total = 0
    print(f"migrate [{'dry-run 预演' if args.dry_run else '执行'}] —— {len(MIGRATION_STEPS)} 步")
    print("=" * 60)
    for step in MIGRATION_STEPS:
        affected, note = step["estimate"](personal)
        total += affected
        print(f"  {step['id']} {step['name']}")
        print(f"    影响 {affected} 个文件 | {note}")
    print("=" * 60)
    print(f"合计预估影响 {total} 个文件")

    if args.dry_run:
        print("dry-run：仅打印计划，未落盘、未修改任何文件。")
        print("确认后去掉 --dry-run 实际执行（执行前先跑 backup，失败可 rollback）。")
        return 0

    if not _list_backups(personal):
        print("⚠ 未检测到备份，建议先执行 backup 再迁移（迁移失败可 rollback）。")
    print("开始执行迁移步骤（骨架）:")
    for step in MIGRATION_STEPS:
        print(f"  正在执行 {step['id']} {step['name']} ...")
        step["execute"](personal)
    print("✅ migrate 骨架执行完毕——所有步骤均为留桩，未修改任何文件")
    return 0


def _resolve_backup(personal: Path, target: str) -> Path | None:
    root = personal / BACKUP_DIRNAME
    if not root.exists():
        print("❌ 无备份目录（personal/.backup 不存在），无可回退")
        return None
    exact = root / target
    if exact.is_dir():
        return exact
    if target in STEP_IDS:
        print(f"⚠ {target} 是迁移步骤 ID，不是备份时间戳。骨架阶段步骤不产生独立备份，")
        print("  无法按步骤回退。请指定备份时间戳（rollback 无参运行可列出可用备份）。")
        return None
    cands = [b for b in sorted(root.iterdir())
             if b.is_dir() and b.name != PRE_ROLLBACK_DIRNAME
             and b.name.startswith(target)]
    if len(cands) == 1:
        return cands[0]
    if len(cands) > 1:
        print(f"⚠ {target} 匹配多个备份：{[b.name for b in cands]}")
        print("  请指定精确时间戳。")
        return None
    print(f"❌ 未找到备份 {target}")
    return None


def cmd_rollback(args) -> int:
    personal = _personal_path(args)
    _require_personal(personal)
    backup_root = personal / BACKUP_DIRNAME

    if not args.to:
        bks = _list_backups(personal)
        if not bks:
            print("❌ personal/.backup 下无备份，无可回退")
            return 1
        print("可回退备份：")
        for b in bks:
            meta = _read_manifest(b)
            info = f"（{meta['file_count']} 文件，{meta['backup_time']}）" if meta else ""
            print(f"  {b.name}  {info}")
        print("用法：rollback --to <备份名> [--yes]")
        return 1

    src = _resolve_backup(personal, args.to)
    if src is None:
        return 1

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    expected = _count_files(src) - (1 if (src / MANIFEST).exists() else 0)
    print(f"将要回退：personal ← {src.name}")
    print(f"  1. 先备份当前状态 → {backup_root / PRE_ROLLBACK_DIRNAME / ts}（防回退本身失败）")
    print(f"  2. 清空 personal（保留 {BACKUP_DIRNAME}）")
    print(f"  3. 从备份恢复 {expected} 个文件")
    if not args.yes:
        ans = input("确认执行？[y/N]: ").strip().lower()
        if ans not in ("y", "yes"):
            print("已取消")
            return 0

    # 1. 当前状态安全备份（防回退本身失败）
    safety = backup_root / PRE_ROLLBACK_DIRNAME / ts
    safety.mkdir(parents=True, exist_ok=True)
    _copy_contents(personal, safety)
    print(f"  ✓ 当前状态已备份 → {safety}")

    # 2. 清空 personal（保留 .backup）
    _clear_personal(personal)
    print("  ✓ personal 已清空（.backup 保留）")

    # 3. 恢复 + 验证
    restored = _restore_from(src, personal)
    if restored == expected:
        print(f"  ✓ 恢复完成：{restored} 个文件，与备份一致")
        print("✅ rollback 成功")
        return 0
    print(f"  ✗ 恢复数 {restored} != 预期 {expected}——请检查")
    print(f"    回退前状态仍保留在 {safety}，可手工恢复")
    return 1


# ── 入口 ────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(
        description="ixxi 迁移工具：backup / migrate --dry-run / rollback（Task 4.1，迁移可回退护栏）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n"
               "  migrate-tool.py backup\n"
               "  migrate-tool.py migrate --dry-run\n"
               "  migrate-tool.py rollback --to 2026-08-14_143000 --yes\n"
               "零第三方依赖（仅标准库）。",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="子命令")

    p_backup = sub.add_parser("backup", help="备份 personal/ → personal/.backup/<时间戳>/")
    p_backup.add_argument("--personal", type=str, default=None,
                          help="personal 目录（默认：仓库根/personal）")
    p_backup.set_defaults(func=cmd_backup)

    p_migrate = sub.add_parser("migrate",
                               help="迁移：--dry-run 预演；不带 --dry-run 实际执行（骨架留桩）")
    p_migrate.add_argument("--dry-run", action="store_true",
                           help="只打印计划与影响文件数，不执行")
    p_migrate.add_argument("--personal", type=str, default=None)
    p_migrate.set_defaults(func=cmd_migrate)

    p_rollback = sub.add_parser("rollback", help="回退：从 .backup/<时间戳>/ 恢复 personal/")
    p_rollback.add_argument("--to", type=str, default=None,
                            help="备份名（时间戳，支持日期前缀）；省略则列出可用备份")
    p_rollback.add_argument("--personal", type=str, default=None)
    p_rollback.add_argument("-y", "--yes", action="store_true", help="跳过确认")
    p_rollback.set_defaults(func=cmd_rollback)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
