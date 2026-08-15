# -*- coding: utf-8 -*-
"""sync-skills-to-claude.py — 知识库管理 skills → Claude Code 适配层平铺

权威源（不修改）：
  core/skills/<技能>/          # 16 个管理技能

目标（受控复制，一级平铺供 Claude Code 发现）：
  .claude/skills/kb-<name>/          # Claude Code 只扫一级 .claude/skills/<name>/SKILL.md

背景：Claude Code 只扫描 .claude/skills/ 一级目录、不递归；此前内部技能藏在
  .claude/skills/kb/<name>/SKILL.md（二级嵌套）导致不可见。本脚本把 15 个管理
  技能平铺到一级（kb-<name> 目录），与 sync-skills-to-codex.py 对 Codex 的做法一致。

用法：
  python engine/scripts/sync-skills-to-claude.py            # 同步（复制权威源→目标）
  python engine/scripts/sync-skills-to-claude.py --check    # 校验（只检查，不复制）
  python engine/scripts/sync-skills-to-claude.py --prune    # 同步 + 清理目标中孤儿 kb-* 目录
"""
import sys, shutil, re
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "core/skills"
DST = REPO.parent / ".claude/skills"  # 仓库根 .claude/skills/（Claude Code 只扫仓库根，不是 framework/）


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


def collect_sources() -> dict[str, Path]:
    """返回 {技能名: 技能目录路径}，16 个管理技能"""
    skills = {}
    if SRC.exists():
        for d in sorted(SRC.iterdir()):
            if d.is_dir() and (d / "SKILL.md").exists():
                skills[skill_name(d / "SKILL.md")] = d
    return skills


def check_only(sources: dict[str, Path]) -> int:
    """校验目标中所有 kb-* 平铺目录是否齐全；返回缺失数"""
    missing = []
    for name, src in sources.items():
        dst = DST / name
        if not (dst / "SKILL.md").exists():
            missing.append(name)
    if missing:
        print(f"❌ 缺失 {len(missing)} 个 Claude 平铺入口: {missing}")
        return len(missing)
    print(f"✅ 校验通过：{len(sources)} 个 kb-* 平铺入口齐全")
    return 0


def sync(sources: dict[str, Path], prune: bool) -> None:
    """复制权威源 → 目标（一级平铺）"""
    synced = 0
    if prune:
        wanted = {name for name in sources}
        for d in DST.iterdir():
            if d.is_dir() and d.name.startswith("kb-") and d.name not in wanted:
                shutil.rmtree(d)
                print(f"  [prune] 删除孤儿: {d.name}")

    for name, src in sources.items():
        dst = DST / name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        synced += 1
        print(f"  ✅ {name}")
    print(f"共平铺 {synced} 个管理技能 -> .claude/skills/")


def main():
    args = sys.argv[1:]
    sources = collect_sources()
    print(f"权威源管理技能: {len(sources)} 个")

    if "--check" in args:
        sys.exit(check_only(sources))
    else:
        sync(sources, prune="--prune" in args)
        # 同步后自动校验
        sys.exit(check_only(sources))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("IXXI-E311 | 适配层生成失败：sync core/skills → .claude/skills 出错", file=sys.stderr)
        print(f"修复：检查 core/skills 结构完整后重试；原始错误：{e}", file=sys.stderr)
        print("参考：engine/scripts/sync-skills-to-claude.py", file=sys.stderr)
        sys.exit(1)
