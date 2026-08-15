# -*- coding: utf-8 -*-
"""check-skill-parity.py — 能力层→适配层 六项可达性断言校验（P1-P6）

判据是「可达性」（capability 能否被该 agent 调用），不是「等价性」。
每个 skill 统一按 skill 名作 key：优先取 SKILL.md frontmatter 的 name，失败用父目录名。

权威源（不修改）：
  core/skills/<技能>/                 # 16 个管理技能
  core/skills/_external/<分类>/<技能>/   # 领域技能（跳过无 SKILL.md 的资源目录）

六项断言：
  P1 权威源    权威源 SKILL.md 存在（collect 已保证，恒真）
  P2 Claude 可达  管理 skill → .claude/skills/<name>/SKILL.md 平铺（sync-skills-to-claude.py 的 DST）
                  外部 skill → 权威源即注入源，SKILL.md 存在即算可达
  P3 Codex 可达    .agents/skills/<name>/SKILL.md 镜像存在
  P4 Hermes 可达   ops/hermes/Hermes-命令索引.md 含 name 条目且该行不含「不运行」
  P5 引用资源      SKILL.md 正文引用的 engine/scripts/*.py|.sh、ops/scripts/*.sh、ops/rules/*.md 实际存在
  P6 注册表覆盖    ops/rules/skill调度注册表.md 出现 name；管理 skill 另要求 Claude/Hermes/Codex 三列非空

说明：适配层（.claude/skills/ 平铺、.agents/、Hermes 索引）可能尚未生成，
      对应断言如实报 0/N，不崩溃、不假设就绪。

用法：
  python engine/scripts/check-skill-parity.py          # 校验（只读，不写任何文件）
  python engine/scripts/check-skill-parity.py --check  # 同上，显式 --check（本脚本天然只读）
  python engine/scripts/check-skill-parity.py --verbose  # 逐 skill 打印每项断言明细

退出码：存在任何失败 → 1，全部通过 → 0。
"""
import json
import sys, re
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

SRC_MGMT = REPO / "core/skills"
SRC_EXT = REPO / "core/skills/_external"
SRC_PERSONAL = REPO.parent / "personal/system/skills"
DST_CLAUDE = REPO.parent / ".claude/skills"  # 管理 skill 一级平铺目标（sync-skills-to-claude.py 输出）
DST_CODEX = REPO.parent / ".agents/skills"   # Codex 镜像目标（sync-skills-to-codex.py 输出）
HERMES_IDX = REPO / "ops/hermes/Hermes-命令索引.md"
REGISTRY = REPO / "ops/rules/skill调度注册表.md"

# P5 引用资源提取：engine/scripts|ops/scripts|ops/rules 下的 .py/.sh/.md 相对路径
REF_RE = re.compile(r"(?:engine/scripts|ops/scripts|ops/rules)/[A-Za-z0-9_.\-]+\.(?:py|sh|md)")
# P4 索引条目匹配：以整个 name 作词元（skill 名含连字符，\b 对非字母数字断开有效）
def name_token(name: str) -> re.Pattern:
    return re.compile(rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])")


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


def collect_sources() -> list[tuple[str, Path, bool]]:
    """返回 [(skill名, 技能目录路径, is_mgmt)]，逻辑照抄 sync-skills-to-codex.py"""
    skills = {}
    if SRC_MGMT.exists():
        for d in sorted(SRC_MGMT.iterdir()):
            if d.is_dir() and (d / "SKILL.md").exists():
                skills[skill_name(d / "SKILL.md")] = (d, True)
    if SRC_EXT.exists():
        for cat in sorted(SRC_EXT.iterdir()):
            if not cat.is_dir():
                continue
            for sub in sorted(cat.iterdir()):
                if sub.is_dir() and (sub / "SKILL.md").exists():
                    skills[skill_name(sub / "SKILL.md")] = (sub, False)
    # personal 技能（覆盖同名，personal 优先，is_mgmt=False 领域）
    if SRC_PERSONAL.exists():
        for cat in sorted(SRC_PERSONAL.iterdir()):
            if not cat.is_dir():
                continue
            for sub in sorted(cat.iterdir()):
                if sub.is_dir() and (sub / "SKILL.md").exists():
                    skills[skill_name(sub / "SKILL.md")] = (sub, False)
    return [(n, p, m) for n, (p, m) in sorted(skills.items())]


def read_index_rows() -> dict[str, list[str]]:
    """解析注册表：name → 该行单元格列表（用于 P6）。解析失败返回 {}。"""
    rows = {}
    try:
        text = REGISTRY.read_text(encoding="utf-8")
    except Exception as e:
        print(f"⚠️ 无法读取注册表 {REGISTRY}: {e}")
        return rows
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        # 表头/分隔行跳过
        if not cells or not cells[0] or cells[0] in ("skill", "---") or set(cells[0]) <= {"-"}:
            continue
        rows[cells[0]] = cells
    return rows


def check_p1(name: str, src: Path) -> tuple[bool, str]:
    """权威源存在。collect 已过滤，通常恒真。"""
    return (src / "SKILL.md").exists(), ""


def check_p2(name: str, src: Path, is_mgmt: bool) -> tuple[bool, str]:
    """Claude 可达：管理 skill 看平铺；外部 skill 权威源即注入源。"""
    if is_mgmt:
        dst = DST_CLAUDE / name / "SKILL.md"
        if dst.exists():
            return True, ""
        return False, f"缺少 .claude/skills/{name}/SKILL.md（平铺未生成？）"
    return (src / "SKILL.md").exists(), ""


def check_p3(name: str) -> tuple[bool, str]:
    """Codex 可达：.agents/skills/<name>/SKILL.md 镜像。"""
    dst = DST_CODEX / name / "SKILL.md"
    if dst.exists():
        return True, ""
    return False, f"缺少 .agents/skills/{name}/SKILL.md（Codex 镜像未生成？）"


def check_p4(name: str, idx_text: str | None) -> tuple[bool, str]:
    """Hermes 可达：索引含 name 条目且该行不含「不运行」。"""
    if idx_text is None:
        return False, "Hermes-命令索引.md 缺失"
    pat = name_token(name)
    ok, reasons = False, []
    for line in idx_text.splitlines():
        if pat.search(line):
            if "不运行" in line:
                reasons.append("索引条目标注「不运行」")
            else:
                ok = True
    if ok:
        return True, ""
    return False, "; ".join(reasons) if reasons else f"索引无 {name} 条目"


def check_p5(src: Path) -> tuple[bool, str]:
    """引用资源存在：优先读 capability.json resources，兜底从 SKILL.md 提取。"""
    refs = set()
    cap = src / "capability.json"
    if cap.exists():
        try:
            data = json.loads(cap.read_text(encoding="utf-8"))
            refs = set(data.get("resources", []))
        except Exception:
            refs = set()
    if not refs:
        # 兜底：从 SKILL.md 提取（resources 未补齐时的兼容路径）
        try:
            text = (src / "SKILL.md").read_text(encoding="utf-8")
        except Exception as e:
            return False, f"SKILL.md 读取失败: {e}"
        for m in REF_RE.finditer(text):
            p = m.group(0).strip().strip("`").strip("[]").split("#", 1)[0]
            if p:
                refs.add(p)
    missing = []
    for rel in sorted(refs):
        if not (REPO / rel).exists():
            missing.append(rel)
    if missing:
        return False, "引用资源缺失: " + ", ".join(missing)
    return True, ""


def check_p6(name: str, is_mgmt: bool, rows: dict[str, list[str]]) -> tuple[bool, str]:
    """注册表覆盖：name 出现；管理 skill 另要求 Claude/Hermes/Codex 三列非空。"""
    cells = rows.get(name)
    if cells is None:
        return False, f"注册表无 {name} 条目"
    if is_mgmt:
        if len(cells) < 6:
            return False, f"注册表条目列数不足（{len(cells)}列，需 7 列含三 agent 列）"
        blanks = [i for i, col in enumerate((cells[3], cells[4], cells[5])) if not col]
        if blanks:
            names = ["Claude", "Hermes", "Codex"]
            colnames = "、".join(names[i] for i in blanks)
            return False, f"Claude/Hermes/Codex 三列存在空值（{colnames}）"
        return True, ""
    return True, ""


def main() -> int:
    args = set(sys.argv[1:])
    if "-h" in args or "--help" in args:
        print(__doc__)
        return 0
    verbose = "--verbose" in args
    if "--check" in args:
        pass  # 本脚本天然只读，--check 为显式声明

    sources = collect_sources()
    print(f"权威源技能总数: {len(sources)}（管理 {sum(1 for _, _, m in sources if m)} / 外部 {sum(1 for _, _, m in sources if not m)}）")

    # 只读一次依赖文件
    hermes_text = None
    if HERMES_IDX.exists():
        try:
            hermes_text = HERMES_IDX.read_text(encoding="utf-8")
        except Exception as e:
            print(f"⚠️ 无法读取 Hermes 索引 {HERMES_IDX}: {e}")
    else:
        print(f"⚠️ Hermes 索引缺失: {HERMES_IDX}（P4 将全量判失败）")
    rows = read_index_rows()

    results = []  # (name, is_mgmt, [p1, p2, p3, p4, p5, p6], [reasons])
    for name, src, is_mgmt in sources:
        res = [
            check_p1(name, src),
            check_p2(name, src, is_mgmt),
            check_p3(name),
            check_p4(name, hermes_text),
            check_p5(src),
            check_p6(name, is_mgmt, rows),
        ]
        results.append((name, is_mgmt, [ok for ok, _ in res], [why for _, why in res if why]))

    # 逐 skill 输出
    for name, is_mgmt, oks, whys in results:
        tag = "管理" if is_mgmt else "外部"
        flags = "".join("✓" if ok else "✗" for ok in oks)
        line = f"[{tag}] {name:<32} {flags}"
        if verbose and whys:
            line += "  「" + " | ".join(whys) + "」"
        print(line)

    # 分 P 汇总
    total = len(results)
    print("\n=== 分项汇总 ===")
    summary = []
    for pi in range(6):
        passed = sum(1 for _, _, oks, _ in results if oks[pi])
        summary.append(f"P{pi + 1} 通过 {passed}/{total}")
    print("、".join(summary))

    # 失败清单（按 skill 列出哪些 P 失败）
    failed_any = [r for r in results if not all(r[2])]
    if failed_any:
        print("\n=== 失败清单 ===")
        for name, is_mgmt, oks, whys in failed_any:
            fails = [f"P{i + 1}" for i, ok in enumerate(oks) if not ok]
            tag = "管理" if is_mgmt else "外部"
            print(f"[{tag}] {name}: 失败 {','.join(fails)} — " + " | ".join(whys))
        n_ok = sum(1 for _, _, oks, _ in results if all(oks))
        print(f"\n结论: {n_ok}/{total} 个 skill 六项全过（适配层未生成的项属预期，如实计数）")
        return 1

    print(f"\n结论: {total}/{total} 个 skill 六项全过")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("IXXI-E202 | 能力可达性校验执行失败（parity P1-P6 断言）", file=sys.stderr)
        print(f"修复：检查 core/skills 与适配层是否完整，重跑 python framework/engine/scripts/check-skill-parity.py；原始错误：{e}", file=sys.stderr)
        print("参考：engine/scripts/check-skill-parity.py", file=sys.stderr)
        sys.exit(1)
