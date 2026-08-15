# -*- coding: utf-8 -*-
"""sync-agents-to-codex.py — 知识库审查团 → Codex agents toml

权威源：core/agents/<group>/<name>.md（Claude subagent 格式）
适配层：.codex/agents/*.toml（项目级，git 版本化）

用法：
  python engine/scripts/sync-agents-to-codex.py           # 同步（core/agents → .codex/agents/*.toml）
  python engine/scripts/sync-agents-to-codex.py --check   # 校验（只读对比，不写文件）
"""
import sys, re, shutil
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "core/agents"
DST = REPO.parent / ".codex/agents"  # 仓库根 .codex/agents/（Codex 只扫仓库根）


def md_to_toml(md_path: Path) -> tuple[str, str] | None:
    """返回 (toml 文件名, toml 内容)；失败返回 None"""
    t = md_path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", t, re.S)
    if not m:
        return None
    fm, body = m.group(1), m.group(2).strip()
    name = re.search(r"^name:\s*(.+)$", fm, re.M)
    perspective = re.search(r"^perspective:\s*(.+)$", fm, re.M)
    tools = re.search(r"^tools:\s*\[(.*)\]$", fm, re.M)
    role = re.search(r"^role:\s*(.+)$", fm, re.M)

    agent_name = name.group(1).strip().strip('"').strip("'") if name else md_path.stem
    desc = perspective.group(1).strip() if perspective else (role.group(1).strip() if role else f"{agent_name} 审查角色")
    # 清理描述（可能含引号）
    desc = desc.strip().strip('"').strip("'")
    tools_list = [x.strip() for x in tools.group(1).split(",")] if tools else []

    toml = f"""name = "{agent_name}"
description = "{desc}"
developer_instructions = \"\"\"
# {agent_name}

{body}

## 可用工具
{", ".join(tools_list) if tools_list else "（未指定，按需使用）"}
\"\"\"
"""
    return f"{agent_name}.toml", toml


def check_only() -> int:
    """校验 .codex/agents/*.toml 与 core/agents 是否一致；返回 0 一致 / 1 有差异（只读，不写文件）"""
    expected = {}  # toml 文件名 -> 生成内容
    for md in sorted(SRC.rglob("*.md")):
        if md.name == "SKILL.md":
            continue
        res = md_to_toml(md)
        if not res:
            print(f"  !! 解析失败: {md.relative_to(SRC)}")
            continue
        fname, content = res
        expected[fname] = content

    issues = []
    for fname in sorted(expected):
        p = DST / fname
        if not p.exists():
            issues.append(f"缺失 {fname}")
        elif p.read_text(encoding="utf-8") != expected[fname]:
            issues.append(f"需更新 {fname}")
    if DST.exists():
        for p in sorted(DST.iterdir()):
            if p.is_file() and p.suffix == ".toml" and p.name not in expected:
                issues.append(f"多余 {p.name}")
    if issues:
        print(f"❌ 发现 {len(issues)} 处差异（需重跑 sync 同步）:")
        for it in issues:
            print(f"  - {it}")
        return 1
    print(f"✅ 校验通过：{len(expected)} 个 .codex/agents/*.toml 与权威源一致")
    return 0


def main() -> int:
    if "--check" in sys.argv[1:]:
        return check_only()

    DST.mkdir(parents=True, exist_ok=True)
    count = 0
    for md in sorted(SRC.rglob("*.md")):
        if md.name == "SKILL.md":
            continue
        res = md_to_toml(md)
        if not res:
            print(f"  !! 解析失败: {md.relative_to(SRC)}")
            continue
        fname, content = res
        (DST / fname).write_text(content, encoding="utf-8", newline="\n")
        count += 1
        print(f"  ✅ {fname}")
    print(f"共转换 {count} 个角色 -> .codex/agents/")
    return 0


if __name__ == "__main__":
    sys.exit(main())