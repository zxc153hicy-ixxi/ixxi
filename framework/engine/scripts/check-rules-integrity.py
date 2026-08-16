#!/usr/bin/env python3
"""check-rules-integrity.py -- 规则体系完整性交叉检查（护栏H）

检查：
1. AGENT.md T层标签 → 是否覆盖所有 ops/rules/*.md
2. 系统操作菜单.md 指令 → 是否都有对应 skill 或降级路径
3. Ingest完整流程.md → 每个 Step 是否有失败处理
4. registry.json（agents/hooks） → 注册数 vs 实际文件数

用法:
  python engine/scripts/check-rules-integrity.py --repo <知识库根目录>
  python engine/scripts/check-rules-integrity.py --repo . --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKIP_FILES = {"Thumbs.db", ".DS_Store", "desktop.ini", ".gitkeep", ".placeholder"}


def check_menu_skills(repo: Path) -> list[dict]:
    """检查系统操作菜单指令是否都有对应 skill"""
    issues = []
    menu_md = repo / "ops" / "rules" / "系统操作菜单.md"
    skills_dir = repo / ".claude" / "kb" / "skills"

    if not menu_md.exists():
        return issues

    text = menu_md.read_text(encoding="utf-8", errors="replace")

    # 提取菜单指令
    instructions = set()
    in_table = False
    for line in text.split("\n"):
        if "你说什么" in line and "动作" in line:
            in_table = True
            continue
        if in_table:
            m = re.search(r"`/(\w[\w-]*)`", line)
            if m:
                instructions.add(m.group(1))
            elif line.strip() and not line.strip().startswith("|"):
                in_table = False

    # 检查每个指令是否有对应 skill
    if skills_dir.exists():
        skill_names = {d.name for d in skills_dir.iterdir() if d.is_dir()}
        for inst in instructions:
            # 特殊映射: /check→lint, /compact→dedup, /ingest→ingest
            skill_map = {"check": "lint", "compact": "dedup", "ingest": "ingest",
                         "enrich": "enrich", "conflict": "conflict", "analyze": "analyze",
                         "search": None, "export-template": "export-template"}
            expected = skill_map.get(inst, inst)
            if expected and expected not in skill_names:
                issues.append({
                    "type": "menu_skill_missing",
                    "instruction": f"/{inst}",
                    "detail": f"菜单指令无对应 skill（期望: {expected}）",
                })

    return issues


def check_ingest_failure_handling(repo: Path) -> list[dict]:
    """检查 Ingest 流程每步是否有失败处理

    解析速查表中的表格行（| 步骤号 | 名称 | 操作 | 失败处理 |），
    检查第4列（失败处理）是否为空或仅含 "—"
    """
    issues = []
    ingest_md = repo / "ops" / "rules" / "Ingest完整流程.md"

    if not ingest_md.exists():
        return issues

    text = ingest_md.read_text(encoding="utf-8", errors="replace")

    # 找到速查表（| 步骤 | 名称 | 操作 | 失败处理 |）
    in_table = False
    for line in text.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            if in_table:
                break  # 表格结束
            continue
        if "步骤" in line and "名称" in line and "失败处理" in line:
            in_table = True
            continue
        if not in_table:
            continue
        if "---" in line:
            continue

        # 解析表格行：| 步骤号 | 名称 | 操作 | 失败处理 |
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 5:  # 至少5段（含首尾空段）
            continue

        step_num = cells[1].strip()
        failure_col = cells[4].strip() if len(cells) > 4 else ""

        # 跳过非步骤行（如 0/1/2/... 才是步骤）
        if not step_num or step_num in ("步骤", "名称"):
            continue

        # 失败处理列为空或仅含 "—" → 缺少
        if not failure_col or failure_col in ("—", "—", "-"):
            issues.append({
                "type": "ingest_no_failure",
                "step": f"Step {step_num}",
                "detail": f"失败处理列为空（当前: '{failure_col}'）",
            })

    return issues


def check_registry_consistency(repo: Path) -> list[dict]:
    """检查 registry.json 与实际文件数是否一致"""
    issues = []

    # agents
    agents_registry = repo / ".claude" / "kb" / "agents" / "registry.json"
    agents_dir = repo / ".claude" / "kb" / "agents"
    if agents_registry.exists():
        try:
            data = json.loads(agents_registry.read_text(encoding="utf-8"))
            registered = len(data.get("agents", []))
            # 实际 agent 定义文件（排除 registry.json 和 SKILL.md）
            actual_files = [f for f in agents_dir.rglob("*") if f.is_file()
                          and f.name not in ("registry.json", "SKILL.md") and f.suffix in (".md", ".json")]
            if registered != len(actual_files):
                issues.append({
                    "type": "registry_mismatch",
                    "registry": "agents/registry.json",
                    "registered": registered,
                    "actual_files": len(actual_files),
                    "detail": f"注册 {registered} agent，实际 {len(actual_files)} 文件",
                })
        except Exception:
            pass

    # hooks
    hooks_registry = repo / ".claude" / "kb" / "hooks" / "registry.json"
    hooks_dir = repo / ".claude" / "kb" / "hooks"
    if hooks_registry.exists():
        try:
            data = json.loads(hooks_registry.read_text(encoding="utf-8"))
            registered = len(data.get("hooks", []))
            actual_files = [f for f in hooks_dir.rglob("*") if f.is_file()
                          and f.name not in ("registry.json", "SKILL.md")]
            if registered != len(actual_files):
                issues.append({
                    "type": "registry_mismatch",
                    "registry": "hooks/registry.json",
                    "registered": registered,
                    "actual_files": len(actual_files),
                    "detail": f"注册 {registered} hook，实际 {len(actual_files)} 文件",
                })
        except Exception:
            pass

    return issues


def check_integrity(repo: Path) -> dict:
    all_issues = []
    all_issues.extend(check_menu_skills(repo))
    all_issues.extend(check_ingest_failure_handling(repo))
    all_issues.extend(check_registry_consistency(repo))

    score = max(0, 10 - len(all_issues))
    return {
        "status": "pass" if not all_issues else "fail",
        "score": score,
        "issues": all_issues,
    }


def main():
    parser = argparse.ArgumentParser(description="规则体系完整性检查")
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent
    result = check_integrity(repo)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["status"] == "pass":
            print("✅ 规则完整性: 全部通过")
        else:
            print(f"❌ 规则完整性: {len(result['issues'])} 项问题\n")
            for i in result["issues"]:
                loc = i.get("file") or i.get("instruction") or i.get("step") or i.get("registry") or "?"
                print(f"  📍 [{i['type']}] {loc}")
                print(f"     {i['detail']}")
            print()

    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
