# -*- coding: utf-8 -*-
"""sync-agents-to-claude.py — 知识库审查团 → Claude Code subagents 适配层

权威源：core/agents/<group>/<name>.md（Claude subagent 格式前件，Agent 无关）
适配层：.claude/agents/<agent-name>.md（Claude Code 原生 subagent，一级平铺）

三层分离：同一能力源（core/agents）两个生成器各产出引擎原生语法——
  sync-agents-to-codex.py → .codex/agents/*.toml（Codex）
  sync-agents-to-claude.py → .claude/agents/*.md（Claude，本脚本）

用法：
  python engine/scripts/sync-agents-to-claude.py            # 同步（生成 .claude/agents/*.md）
  python engine/scripts/sync-agents-to-claude.py --check    # 校验（只检查，不生成，缺一返回非 0）
"""
import sys, re
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "core/agents"
DST = REPO.parent / ".claude/agents"  # 仓库根 .claude/agents/（Claude Code 只扫仓库根）


def md_to_agent(md_path: Path) -> tuple[str, str] | None:
    """返回 (agent 文件名, agent.md 内容)；frontmatter 缺失返回 None

    解析逻辑与 sync-agents-to-codex.py 的 md_to_toml 同构：re 提取
    name/perspective/role/tools；group/stage 忽略不写。
    """
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
    # description 优先级：perspective → role → 「<name> 审查角色」
    desc = perspective.group(1).strip() if perspective else (role.group(1).strip() if role else f"{agent_name} 审查角色")
    desc = desc.strip().strip('"').strip("'").replace('"', '\\"')
    tools_list = [x.strip() for x in tools.group(1).split(",")] if tools else []

    agent = f"""---
name: {agent_name}
description: "{desc}"
tools: "{", ".join(tools_list)}"
---

{body}
"""
    return f"{agent_name}.md", agent


def collect() -> dict[str, tuple[Path, str]]:
    """返回 {agent_name: (源 md 路径, 生成内容)}；跳过 SKILL.md（registry.json 非 md 天然跳过）"""
    out = {}
    if not SRC.exists():
        return out
    for md in sorted(SRC.rglob("*.md")):
        if md.name == "SKILL.md":
            continue
        res = md_to_agent(md)
        if not res:
            print(f"  !! 解析失败: {md.relative_to(SRC)}")
            continue
        fname, content = res
        out[fname.removesuffix(".md")] = (md, content)
    return out


def check_only(agents: dict[str, tuple[Path, str]]) -> int:
    """校验 .claude/agents/ 下每个权威源 agent 都有对应 <name>.md；返回缺失数"""
    missing = [name for name in agents if not (DST / f"{name}.md").exists()]
    if missing:
        print(f"❌ 缺失 {len(missing)} 个 Claude subagent: {missing}")
        return len(missing)
    print(f"✅ 校验通过：{len(agents)} 个 Claude subagent 齐全")
    return 0


def sync(agents: dict[str, tuple[Path, str]]) -> None:
    """权威源 → 目标（一级平铺生成 .claude/agents/*.md）"""
    DST.mkdir(parents=True, exist_ok=True)
    for name, (_, content) in agents.items():
        (DST / f"{name}.md").write_text(content, encoding="utf-8", newline="\n")
        print(f"  ✅ {name}")
    print(f"共生成 {len(agents)} 个角色 -> .claude/agents/")


def main():
    args = sys.argv[1:]
    agents = collect()
    print(f"权威源 agent: {len(agents)} 个")

    if "--check" in args:
        sys.exit(check_only(agents))
    else:
        sync(agents)
        # 同步后自动校验
        sys.exit(check_only(agents))


if __name__ == "__main__":
    main()
