# -*- coding: utf-8 -*-
"""sync-skills-to-hermes.py — 知识库 skills → Hermes 命令索引自动生成

权威源（不修改，与 sync-skills-to-codex.py 同源收集逻辑）：
  core/skills/<技能>/                       # 管理技能（16）
  core/skills/_external/<分类>/<技能>/SKILL.md  # 外部技能（跳过分类级 SKILL.md）
  personal/system/skills/<分类>/<技能>/SKILL.md # 个人技能（归外部，覆盖同名）

目标（生成，每次运行整体重建）：
  ops/hermes/Hermes-命令索引.md  # 替代手维护翻译表的 Hermes 命令索引

对每个 skill 解析其 SKILL.md：
  - name / description（frontmatter，作「触发场景」）
  - 引用脚本：正文 engine/scripts|engine/templates|ops/scripts 下的 .py/.sh 文件名（去重，最多 5）
  - 引用规则：正文 ops/rules/*.md 文件名（去 .md 后缀，去重，最多 5）

用法：
  python engine/scripts/sync-skills-to-hermes.py          # 生成命令索引
  python engine/scripts/sync-skills-to-hermes.py --check  # 校验索引包含全部 skill 名
"""
import sys, re
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC_MGMT = REPO / "core/skills"
SRC_EXT = REPO / "core/skills/_external"
SRC_PERSONAL = REPO.parent / "personal/system/skills"
OUT = REPO / "ops/hermes/Hermes-命令索引.md"

# 脚本引用：engine/scripts/*.py|*.sh、engine/templates/*.sh、ops/scripts/*.sh
SCRIPT_RE = re.compile(r"(?:engine/scripts/|engine/templates/|ops/scripts/)([\w.\-*]+\.(?:py|sh))")
# 规则引用：ops/rules/<文件名>，兼容 `ops/rules/xxx.md` 与 wikilink `[[ops/rules/xxx]]`
RULE_RE = re.compile(r"ops/rules/([\w.\-]+)")
MAX_REF = 5


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


def skill_description(sk_md: Path) -> str:
    """从 SKILL.md frontmatter 提取 description 作「触发场景」；兼容块标量 description: |"""
    try:
        t = sk_md.read_text(encoding="utf-8")
        # 块标量：description: |  → 收集后续缩进行
        if re.search(r"^description:\s*\|", t, re.M):
            m = re.search(r"^description:\s*\|(.*?)(?=\n\S)", t, re.M | re.S)
            if m:
                lines = [ln.strip() for ln in m.group(1).splitlines() if ln.strip()]
                return " ".join(lines)
        m = re.search(r"^description:\s*(.+)$", t, re.M)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


def collect_sources() -> list[tuple[str, Path]]:
    """返回 [(技能名, 技能目录路径)]，跳过分类级重复 SKILL.md"""
    skills = {}

    # 管理技能
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


def ref_scripts(sk_md: Path) -> list[str]:
    """正文引用的脚本文件名（去重，最多 5）"""
    try:
        t = sk_md.read_text(encoding="utf-8")
    except Exception:
        return []
    seen, out = set(), []
    for fn in SCRIPT_RE.findall(t):
        if fn not in seen:
            seen.add(fn)
            out.append(fn)
        if len(out) >= MAX_REF:
            break
    return out


def ref_rules(sk_md: Path) -> list[str]:
    """正文引用的规则文件名（去 .md 后缀，去重，最多 5）"""
    try:
        t = sk_md.read_text(encoding="utf-8")
    except Exception:
        return []
    seen, out = set(), []
    for raw in RULE_RE.findall(t):
        name = raw[:-3] if raw.endswith(".md") else raw
        if not name or "*" in name or name in seen:  # 过滤 ops/rules/*.md 泛写与空值
            continue
        seen.add(name)
        out.append(name)
        if len(out) >= MAX_REF:
            break
    return out


def cell(v) -> str:
    """表格单元格：空→—，转义 | 与换行"""
    if not v:
        return "—"
    return str(v).replace("|", "\\|").replace("\n", " ").strip()


def render_table(rows: list[tuple[str, str, Path, list[str], list[str]]]) -> str:
    lines = ["| skill | 触发场景 | SKILL.md 路径 | 引用脚本 | 引用规则 |",
             "|------|------|------|------|------|"]
    for name, desc, sk_md, scripts, rules in rows:
        rel = sk_md.relative_to(REPO.parent).as_posix()
        lines.append(f"| {cell(name)} | {cell(desc)} | {cell(rel)} | "
                     f"{cell(' '.join(scripts))} | {cell(' '.join(rules))} |")
    return "\n".join(lines)


def build_index(mgmt_rows, ext_rows) -> str:
    parts = []
    parts.append("---")
    parts.append("tags: [命令索引, Hermes]")
    parts.append("status: active")
    parts.append("summary: 由 engine/scripts/sync-skills-to-hermes.py 从权威源（core/skills + "
                 "core/skills/_external + personal/system/skills）生成；手改请改 SKILL.md")
    parts.append("---")
    parts.append("")
    parts.append("# Hermes 命令索引")
    parts.append("")
    parts.append("本文件由 engine/scripts/sync-skills-to-hermes.py 生成，替代手维护翻译表；"
                 "Hermes 原生直读 SKILL.md，命令索引只承担语法查找。")
    parts.append("")
    parts.append(f"## 管理 skill（{len(mgmt_rows)}）")
    parts.append("")
    parts.append(render_table(mgmt_rows))
    parts.append("")
    parts.append(f"## 外部 skill（{len(ext_rows)}）")
    parts.append("")
    parts.append(render_table(ext_rows))
    parts.append("")
    parts.append("## 加载规则")
    parts.append("")
    parts.append("- Hermes 加载 skill = 直读 SKILL.md（权威源）+ 查本表命令索引（语法查找）+ "
                 "ops/rules 规则文件共享直读。")
    parts.append("- 命令索引仅承担语法查找，内容以 SKILL.md 为准。")
    parts.append("- 修改本表不生效——请改 SKILL.md 后重新运行 engine/scripts/sync-skills-to-hermes.py。")
    parts.append("")
    return "\n".join(parts)


def main():
    check_only = "--check" in sys.argv[1:]

    sources = collect_sources()
    # 统一口径（与 check-skill-parity.py 一致）：管理=core/skills 顶层，外部=_external + personal/system/skills
    mgmt = [(n, d) for n, d in sources if "_external" not in d.parts and "personal" not in d.parts]
    ext = [(n, d) for n, d in sources if "_external" in d.parts or "personal" in d.parts]
    print(f"收集到技能源: 管理 {len(mgmt)} + 外部 {len(ext)} = {len(sources)} 个")

    if check_only:
        if not OUT.exists():
            print(f"✗ 命令索引不存在: {OUT}")
            return 1
        content = OUT.read_text(encoding="utf-8")
        names = [n for n, _ in sources]
        missing = [n for n in names if n not in content]
        present = [n for n in names if n in content]
        print(f"✔ 通过 {len(present)}/{len(names)} 个 skill 名已收录")
        if missing:
            print(f"✗ 缺失 {len(missing)} 个: {missing}")
            return 1
        print("✔ 校验通过，全部 skill 名已收录。")
        return 0

    mgmt_rows = [(n, skill_description(d / "SKILL.md"), d / "SKILL.md",
                  ref_scripts(d / "SKILL.md"), ref_rules(d / "SKILL.md")) for n, d in mgmt]
    ext_rows = [(n, skill_description(d / "SKILL.md"), d / "SKILL.md",
                 ref_scripts(d / "SKILL.md"), ref_rules(d / "SKILL.md")) for n, d in ext]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_index(mgmt_rows, ext_rows), encoding="utf-8")
    print(f"✔ 已生成: {OUT}  (管理 {len(mgmt_rows)} + 外部 {len(ext_rows)} = "
          f"{len(mgmt_rows) + len(ext_rows)} 条)")


if __name__ == "__main__":
    sys.exit(main())
