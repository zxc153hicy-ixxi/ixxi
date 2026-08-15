# -*- coding: utf-8 -*-
"""sync-skills-to-codex.py — 知识库 skills → Codex 适配层受控同步

权威源（不修改）：
  core/skills/<技能>/          # 16 个管理技能
  core/skills/_external/<分类>/<技能>/  # 外部技能（跳过分类级重复 SKILL.md）
  personal/system/skills/<分类>/<技能>/ # 个人技能（归外部，覆盖同名）

目标（受控复制，每次运行镜像更新）：
  1. 知识库根 .agents/skills/        # Codex 仓库级发现（git 版本化）
  2. ~/.agents/skills/               # Codex 用户级发现（全局兜底）

用法：
  python engine/scripts/sync-skills-to-codex.py [--target user|repo|all] [--prune]
  python engine/scripts/sync-skills-to-codex.py --check  # 只读校验（对比源/目标，不写文件）
"""
import sys, shutil, re
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC_MGMT = REPO / "core/skills"
SRC_EXT = REPO / "core/skills/_external"
SRC_PERSONAL = REPO.parent / "personal/system/skills"
TARGET_REPO = REPO.parent / ".agents/skills"  # 仓库根 .agents/skills/（Codex 只扫仓库根）
TARGET_USER = Path.home() / ".agents/skills"


def skill_name(sk_md: Path) -> str:
    """从 SKILL.md frontmatter 提取 name，失败用父目录名"""
    try:
        t = sk_md.read_text(encoding="utf-8")
        m = re.search(r"^name:\s*(.+)$", t, re.M)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    except Exception:
        pass
    return sk_md.parent.name


def collect_sources() -> list[tuple[str, Path]]:
    """返回 [(技能名, 技能目录路径)]，跳过分类级重复 SKILL.md"""
    skills = {}

    # 管理技能（16）
    if SRC_MGMT.exists():
        for d in sorted(SRC_MGMT.iterdir()):
            if d.is_dir() and (d / "SKILL.md").exists():
                skills[skill_name(d / "SKILL.md")] = d

    # 外部技能（子目录，跳过分类级 SKILL.md）
    if SRC_EXT.exists():
        for cat in sorted(SRC_EXT.iterdir()):
            if not cat.is_dir():
                continue
            for sub in sorted(cat.iterdir()):
                if sub.is_dir() and (sub / "SKILL.md").exists():
                    skills[skill_name(sub / "SKILL.md")] = sub

    # personal 技能（personal/system/skills 分类/技能，覆盖同名，personal 优先）
    if SRC_PERSONAL.exists():
        for cat in sorted(SRC_PERSONAL.iterdir()):
            if not cat.is_dir():
                continue
            for sub in sorted(cat.iterdir()):
                if sub.is_dir() and (sub / "SKILL.md").exists():
                    skills[skill_name(sub / "SKILL.md")] = sub

    return sorted(skills.items())


def check_only(sources: list[tuple[str, Path]]) -> int:
    """校验仓库根 .agents/skills/ 中所有镜像是否齐全；返回缺失数（只读，不写文件）"""
    missing = []
    for name, _src in sources:
        dst = TARGET_REPO / name
        if not (dst / "SKILL.md").exists():
            missing.append(name)
    if missing:
        print(f"❌ 缺失 {len(missing)} 个 Codex 镜像: {missing}")
        return len(missing)
    print(f"✅ 校验通过：{len(sources)} 个 Codex 镜像齐全")
    return 0


def sync_to(target: Path, sources: list[tuple[str, Path]], prune: bool):
    target.mkdir(parents=True, exist_ok=True)
    synced, skipped = [], []

    # 事务化：先备份目标，半途失败还原（P1-C 失败恢复）
    import tempfile
    backup_dir = None
    if target.exists() and any(target.iterdir()):
        backup_dir = Path(tempfile.mkdtemp(prefix="ixxi-sync-backup-"))
        shutil.copytree(target, backup_dir / "target")

    try:
        # 镜像：删除目标中不再属于源技能的目录（prune 模式）
        if prune:
            wanted = {name for name, _ in sources}
            for d in target.iterdir():
                if d.is_dir() and d.name not in wanted and not d.name.startswith("."):
                    shutil.rmtree(d)
                    print(f"  [prune] 删除: {d.name}")

        for name, src_dir in sources:
            dst = target / name
            # 复制目录（覆盖）
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src_dir, dst)
            synced.append(name)

        print(f"  -> {target}  (技能 {len(synced)} 个)")
        # 生成 README（说明产物性质 + 计数口径，统一口径 = 管理 16 / 外部 62）
        write_readme(target, len(synced),
                     sum(1 for _, s in sources if "_external" in s.parts or "personal" in s.parts))
    except Exception:
        # 回滚：还原备份
        if backup_dir is not None and (backup_dir / "target").exists():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(backup_dir / "target", target)
        print("  ✗ 同步失败，已回滚到备份状态", file=sys.stderr)
        raise
    finally:
        if backup_dir is not None:
            shutil.rmtree(backup_dir, ignore_errors=True)


def write_readme(target: Path, total: int, external: int):
    mgmt = total - external
    readme = target / "README.md"
    readme.write_text(
        f"# .agents/skills —— Codex 适配层（生成产物，别手改）\n\n"
        f"本目录由 `sync-skills-to-codex.py` 从 `core/skills/` 自动生成，"
        f"共 {total} 个技能（管理 {mgmt} / 外部 {external}）。\n\n"
        f"- 权威源：`core/skills/`（改只改 core，别手改这里，会被下次 sync 覆盖）\n"
        f"- 重新生成：`python framework/engine/scripts/sync-skills-to-codex.py`\n"
        f"- 本目录被 .gitignore 排除，clone 后跑 sync 重新生成\n",
        encoding="utf-8",
    )


def main() -> int:
    args = [a for a in sys.argv[1:]]
    prune = "--prune" in args
    check = "--check" in args
    targets = {"repo": TARGET_REPO, "user": TARGET_USER}
    sel = "all"
    for a in args:
        if a.startswith("--target="):
            sel = a.split("=", 1)[1]

    sources = collect_sources()
    print(f"收集到技能源: {len(sources)} 个")
    names = [n for n, _ in sources]
    dup = {n for n in names if names.count(n) > 1}
    if dup:
        print(f"⚠️ 重名: {dup}")

    if check:
        return check_only(sources)

    if sel in ("repo", "all"):
        sync_to(TARGET_REPO, sources, prune)
    if sel in ("user", "all"):
        sync_to(TARGET_USER, sources, prune)

    # 输出清单（个人归外部，与 parity 口径一致）
    print("\n技能清单（写 AGENTS.md 用）:")
    for name, src in sources:
        src_label = "外部" if ("_external" in src.parts or "personal" in src.parts) else "管理"
        print(f"  - {name} [{src_label}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())