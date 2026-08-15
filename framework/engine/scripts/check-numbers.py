#!/usr/bin/env python3
"""check-numbers.py -- 数字一致性自动对比

对比文档中声称的数字 vs 实际文件系统计数。数字漂移是复发率最高的问题类，
本脚本作为护栏A：每次 /check 自动运行，发现不一致立即告警。

用法:
  python framework/engine/scripts/check-numbers.py --repo <知识库根目录>
  python framework/engine/scripts/check-numbers.py --repo . --json
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


def count_md(dir_path: Path) -> int:
    """统计目录下 .md 文件数（排除索引页和跳过文件）"""
    if not dir_path.exists():
        return 0
    return len([f for f in dir_path.glob("*.md")
                if f.name not in SKIP_FILES and "索引" not in f.name])


def count_sessions(repo: Path) -> int:
    """统计 personal/data/sessions 下日期命名的会话文件（排除 ixxi-agent-* 文档与索引页）"""
    sdir = repo.parent / "personal" / "data" / "sessions"
    if not sdir.exists():
        return 0
    return len([f for f in sdir.glob("*.md")
                if re.match(r"^\d{4}-\d{2}-\d{2}", f.name)])


def count_dir_files(dir_path: Path, pattern: str = "*.md") -> int:
    """统计目录下匹配文件数"""
    if not dir_path.exists():
        return 0
    return len([f for f in dir_path.rglob(pattern) if f.name not in SKIP_FILES])


def extract_claimed(text: str, pattern: str) -> list[tuple[str, int]]:
    """从文本中提取声称数字，返回 [(上下文, 数字), ...]"""
    results = []
    for m in re.finditer(pattern, text):
        num = int(m.group(1))
        ctx = m.group(0)[:80].replace("\n", " ")
        results.append((ctx, num))
    return results


def check_numbers(repo: Path) -> dict:
    """主检查逻辑"""
    issues = []

    # === 实际计数 ===
    actual = {
        "g_count": 0,          # G1-GN 中的 N
        "t_tags": 0,           # T层标签行数
        "rules": count_md(repo / "ops" / "rules"),
        "patterns": count_md(repo.parent / "personal" / "system" / "patterns"),
        "anti_patterns": count_md(repo.parent / "personal" / "system" / "anti-patterns"),
        "sessions": count_sessions(repo),
        "scripts_engine": count_dir_files(repo / "engine" / "scripts", "*.py"),
    }

    # === AGENT.md 解析 ===
    agent_md = repo / "AGENT.md"
    if agent_md.exists():
        text = agent_md.read_text(encoding="utf-8", errors="replace")

        # G层约束数: G1-G{N}
        g_nums = re.findall(r"\| G(\d+) \|", text)
        if g_nums:
            actual["g_count"] = max(int(n) for n in g_nums)

        # T层标签数: 统计 T层 表中标签行（以 | # 开头）
        in_t_table = False
        t_rows = 0
        for line in text.split("\n"):
            if "T层" in line and ("路由" in line or "标签" in line):
                in_t_table = True
                continue
            if in_t_table:
                if line.strip().startswith("|") and re.search(r"#\w+", line):
                    t_rows += 1
                elif line.strip() and not line.strip().startswith("|"):
                    in_t_table = False
        actual["t_tags"] = t_rows

        # AGENT.md 中声称的 rules 数
        rules_claimed = re.findall(r"(\d+)\s*文件", text)
        # ops/rules 数量在 "存放于`ops/rules/`（27文件）" 之类的位置
        rules_match = re.search(r"ops/rules/\S*\s*[（(](\d+)\s*(文件|规则)", text)
        if rules_match:
            claimed_rules = int(rules_match.group(1))
            if claimed_rules != actual["rules"]:
                issues.append({
                    "source": "AGENT.md",
                    "field": "ops/rules/ 文件数",
                    "claimed": claimed_rules,
                    "actual": actual["rules"],
                })

    # === index.md 解析 ===
    index_md = repo / "index.md"
    if index_md.exists():
        text = index_md.read_text(encoding="utf-8", errors="replace")

        checks = [
            (r"正模式索引[^）)]*[（(](\d+)\s*条", "正模式数", actual["patterns"]),
            (r"反模式索引[^）)]*[（(](\d+)\s*条", "反模式数", actual["anti_patterns"]),
            (r"会话摘要索引[^）)]*[（(](\d+)\s*次", "会话数", actual["sessions"]),
            (r"(\d+)\s*项.*检查体系|检查体系[^0-9]*(\d+)\s*项", "检查体系项数", None),
            (r"Ingest[^0-9]*(\d+)\s*步", "Ingest步骤数", None),
        ]

        for pattern, field_name, actual_val in checks:
            m = re.search(pattern, text)
            if m:
                groups = m.groups()
                num_str = next(g for g in groups if g is not None)
                claimed = int(num_str)
                if actual_val is not None and claimed != actual_val:
                    issues.append({
                        "source": "index.md",
                        "field": field_name,
                        "claimed": claimed,
                        "actual": actual_val,
                    })

    # === 系统操作菜单.md 解析 ===
    menu_md = repo / "ops" / "rules" / "系统操作菜单.md"
    if menu_md.exists():
        text = menu_md.read_text(encoding="utf-8", errors="replace")
        # frontmatter 或正文中的项数声明
        m = re.search(r"(\d+)\s*项", text.split("---")[2] if text.count("---") >= 2 else text)
        if m:
            claimed = int(m.group(1))
            # 实际数：意图→指令映射表中的行数（| 你说什么 | 动作 | 指令 | 做什么 |）
            in_table = False
            rows = 0
            for line in text.split("\n"):
                if "你说什么" in line and "动作" in line:
                    in_table = True
                    continue
                if in_table:
                    if line.strip().startswith("|") and "---" not in line and line.strip() != "|":
                        rows += 1
                    elif line.strip() and not line.strip().startswith("|"):
                        in_table = False
            if rows > 0 and rows != claimed:
                issues.append({
                    "source": "系统操作菜单.md",
                    "field": "菜单项数",
                    "claimed": claimed,
                    "actual": rows,
                })

    # === activation.md 解析 ===
    activation_md = repo / "activation.md"
    if activation_md.exists():
        text = activation_md.read_text(encoding="utf-8", errors="replace")
        # 提取关键数字声明
        field_patterns = [
            (r"ops/rules/\S*\s*[（(]?(\d+)\s*(个规则|文件)", "activation: rules数", actual["rules"]),
            (r"ops/patterns/\S*\s*[（(]?(\d+)\s*条", "activation: 正模式数", actual["patterns"]),
            (r"ops/anti-patterns/\S*\s*[（(]?(\d+)\s*条", "activation: 反模式数", actual["anti_patterns"]),
        ]
        for pattern, field_name, actual_val in field_patterns:
            m = re.search(pattern, text)
            if m:
                claimed = int(m.group(1))
                if claimed != actual_val:
                    issues.append({
                        "source": "activation.md",
                        "field": field_name,
                        "claimed": claimed,
                        "actual": actual_val,
                    })

    # === 评分 ===
    score = max(0, 10 - len(issues) * 2)
    status = "pass" if len(issues) == 0 else "fail"

    return {
        "status": status,
        "score": score,
        "issues": issues,
        "actual": actual,
    }


def main():
    parser = argparse.ArgumentParser(description="数字一致性自动对比")
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent
    result = check_numbers(repo)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["status"] == "pass":
            print("✅ 数字一致性: 全部通过")
        else:
            print(f"❌ 数字一致性: {len(result['issues'])} 处不一致\n")
            for i in result["issues"]:
                print(f"  📍 {i['source']}")
                print(f"     {i['field']}: 声称 {i['claimed']} → 实际 {i['actual']}")
            print()

        print(f"实际计数:")
        for k, v in result["actual"].items():
            print(f"  {k}: {v}")

    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
