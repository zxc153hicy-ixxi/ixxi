# -*- coding: utf-8 -*-
"""sync-skills-to-codex.py — 知识库 skills → Codex 适配层受控同步

权威源（不修改）：
  core/skills/<技能>/          # 15 个管理技能
  core/skills/_external/<分类>/<技能>/  # 61 个领域技能（跳过 6 个分类级重复 SKILL.md）

目标（受控复制，每次运行镜像更新）：
  1. 知识库根 .agents/skills/        # Codex 仓库级发现（git 版本化）
  2. ~/.agents/skills/               # Codex 用户级发现（全局兜底）

用法：
  python engine/scripts/sync-skills-to-codex.py [--target user|repo|all] [--prune]
"""
import sys, shutil, re
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC_MGMT = REPO / "core/skills"
SRC_EXT = REPO / "core/skills/_external"
TARGET_REPO = REPO / ".agents/skills"
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

    # 管理技能（15）
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

    return sorted(skills.items())


def sync_to(target: Path, sources: list[tuple[str, Path]], prune: bool):
    target.mkdir(parents=True, exist_ok=True)
    synced, skipped = [], []

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


def main():
    args = [a for a in sys.argv[1:]]
    prune = "--prune" in args
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

    if sel in ("repo", "all"):
        sync_to(TARGET_REPO, sources, prune)
    if sel in ("user", "all"):
        sync_to(TARGET_USER, sources, prune)

    # 输出清单
    print("\n技能清单（写 AGENTS.md 用）:")
    for name, src in sources:
        src_label = "领域" if "_external" in src.parts else "管理"
        print(f"  - {name} [{src_label}]")


if __name__ == "__main__":
    main()