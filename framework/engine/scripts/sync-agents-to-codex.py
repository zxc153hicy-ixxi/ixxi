# -*- coding: utf-8 -*-
"""sync-agents-to-codex.py — 知识库审查团 → Codex agents toml

权威源：core/agents/<group>/<name>.md（Claude subagent 格式）
适配层：.codex/agents/*.toml（项目级，git 版本化）

用法：python engine/scripts/sync-agents-to-codex.py
"""
import sys, re, shutil
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "core/agents"
DST = REPO / ".codex/agents"


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


def main():
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


if __name__ == "__main__":
    main()