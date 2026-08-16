#!/usr/bin/env python3
"""check-frontmatter.py -- YAML frontmatter 格式校验 + 字段完整性检查

用法:
  python engine/scripts/check-frontmatter.py --repo <知识库根目录>
  python engine/scripts/check-frontmatter.py --repo . --json
  python engine/scripts/check-frontmatter.py --repo . --fix   # 自动补填 updated 字段
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

# GBK 终端兜底
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    import yaml
except ImportError:
    sys.exit("需要 PyYAML: pip install pyyaml")

SKIP_FILES = {"Thumbs.db", ".DS_Store", "desktop.ini", ".gitkeep", ".placeholder", "README.md"}
SKIP_DIRS = {".git", "__pycache__", ".fix-backup", "node_modules", "assets", "media"}
# archive/ 为历史快照，允许无 frontmatter
SKIP_PATH_PREFIXES = ("personal/data/", "personal/system/", "personal/knowledge/archive/", "framework/core/skills/", "framework/core/agents/", "framework/core/hooks/", "framework/samples/")
SCAN_DIRS = {"framework", "personal"}  # 双目录结构

VALID_STATUS = {"active", "draft", "superseded", "deprecated", "archived", "degraded"}
TODAY = date.today().isoformat()


def parse_frontmatter(text: str) -> tuple[dict | None, str, str]:
    """解析 YAML frontmatter。返回 (data, error, body)"""
    if not text.startswith("---"):
        return None, "缺少 frontmatter（不以 --- 开头）", text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, "frontmatter 格式不完整", text

    yaml_str = parts[1]
    body = parts[2]

    try:
        data = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        return None, f"YAML 解析失败: {e}", body

    if data is None:
        return {}, "", body  # 空 frontmatter
    if not isinstance(data, dict):
        return None, f"frontmatter 不是字典类型（是 {type(data).__name__}）", body

    return data, "", body


def validate_frontmatter(data: dict, file_path: Path) -> list[str]:
    """校验 frontmatter 字段，返回问题列表"""
    issues = []
    rel = str(file_path).replace("\\", "/")

    # tags 字段
    if "tags" not in data:
        issues.append("缺少 tags 字段")
    elif not isinstance(data["tags"], list):
        issues.append(f"tags 应为数组，实际为 {type(data['tags']).__name__}")

    # status 字段
    if "status" in data:
        if data["status"] not in VALID_STATUS:
            issues.append(f"status 值无效: {data['status']}（合法值: {VALID_STATUS}）")

    # summary 字段 — learning/ 目录下为必填，其他为推荐
    if "summary" not in data or not data.get("summary"):
        if "knowledge/learning/" in rel:
            issues.append("缺少 summary 字段（learning/ 目录下为必填）")
        else:
            issues.append("缺少 summary 字段")

    # pt_phase 字段 — learning/ 目录下为必填
    if "pt_phase" not in data or not data.get("pt_phase"):
        if "knowledge/learning/" in rel:
            issues.append("缺少 pt_phase 字段（learning/ 目录下为必填）")

    # 日期字段
    for field in ["created", "updated", "review_date"]:
        if field in data and data[field] is not None:
            try:
                date.fromisoformat(str(data[field]))
            except (ValueError, TypeError):
                issues.append(f"{field} 不是合法日期: {data[field]}")

    return issues


def check_quality(data: dict, file_path: Path) -> list[dict]:
    """护栏D：检测 frontmatter 质量问题（不影响评分，仅输出清单）

    返回 quality_issues 列表，每项 {level, field, detail}
    level: "warning" | "info"
    """
    issues = []
    stem = file_path.stem

    # summary 质量
    summary = data.get("summary", "")
    if summary and isinstance(summary, str):
        if summary.strip() == stem:
            issues.append({
                "level": "warning",
                "field": "summary",
                "detail": f"summary = 文件名 '{stem}'（空壳摘要）",
            })
        elif len(summary.strip()) < 10:
            issues.append({
                "level": "info",
                "field": "summary",
                "detail": f"summary 仅 {len(summary.strip())} 字符: '{summary}'",
            })

    # tags 为空
    tags = data.get("tags", [])
    if isinstance(tags, list) and len(tags) == 0:
        issues.append({
            "level": "warning",
            "field": "tags",
            "detail": "tags 数组为空",
        })

    return issues


def check_file(file_path: Path, fix: bool = False) -> dict:
    """检查单个文件，返回结果。fix=True 时自动补全缺失的 frontmatter。"""
    rel = str(file_path)
    try:
        raw = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"file": rel, "status": "error", "issues": [f"读取失败: {e}"]}

    data, parse_err, body = parse_frontmatter(raw)

    # fix: 完全缺失 frontmatter → 自动生成最小 frontmatter
    if fix and parse_err and "不以 --- 开头" in parse_err:
        stem = file_path.stem
        new_fm = f"---\ntags: [学习资料]\nstatus: active\nsummary: \"{stem}\"\ncreated: {TODAY}\nupdated: {TODAY}\n---\n\n"
        tmp = file_path.with_suffix(".tmp")
        tmp.write_text(new_fm + raw, encoding="utf-8")
        tmp.replace(file_path)
        return {"file": rel, "status": "pass", "issues": [f"✅ 已自动生成 frontmatter"]}

    if parse_err:
        return {"file": rel, "status": "fail", "issues": [parse_err]}

    issues = validate_frontmatter(data or {}, file_path)

    # 护栏D: 质量检测（不影响评分，仅输出清单）
    quality_issues = check_quality(data or {}, file_path)

    # fix: 自动补填 updated 或 tags
    if fix and data is not None:
        lines = raw.split("\n")
        dashes = 0
        end_idx = None
        for i, line in enumerate(lines):
            if line.strip() == "---":
                dashes += 1
                if dashes == 2:
                    end_idx = i
                    break
        if end_idx is not None:
            fixed_any = False
            if "updated" not in data:
                lines.insert(end_idx, f"updated: {TODAY}")
                end_idx += 1
                issues = [i for i in issues if "updated" not in i]
                fixed_any = True
            if "tags" not in data:
                tag = "学习资料" if "learning" in str(file_path) else "知识库"
                lines.insert(end_idx, f"tags: [{tag}]")
                issues = [i for i in issues if "tags" not in i]
                fixed_any = True
            # 补 summary（learning/ 目录下，取文件名做兜底摘要）
            if "summary" not in data and "learning" in str(file_path):
                stem = file_path.stem
                lines.insert(end_idx, f"summary: \"{stem}\"")
                end_idx += 1
                issues = [i for i in issues if "summary" not in i]
                fixed_any = True
            # 补 pt_phase（learning/ 目录下，默认"待分类"）
            if "pt_phase" not in data and "learning" in str(file_path):
                lines.insert(end_idx, "pt_phase: 待分类")
                end_idx += 1
                issues = [i for i in issues if "pt_phase" not in i]
                fixed_any = True
            if fixed_any:
                new_raw = "\n".join(lines)
                tmp = file_path.with_suffix(".tmp")
                tmp.write_text(new_raw, encoding="utf-8")
                tmp.replace(file_path)
                issues.append("✅ 已自动补填字段")

    return {
        "file": rel,
        "status": "pass" if not issues else "fail",
        "issues": issues,
        "quality_issues": quality_issues,
    }


def main():
    parser = argparse.ArgumentParser(description="YAML frontmatter 校验")
    parser.add_argument("--repo", type=str, default=None, help="知识库根目录")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--fix", action="store_true", help="自动补填 updated 字段")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent.parent

    results = []
    for f in sorted(repo.rglob("*.md")):
        if f.name in SKIP_FILES:
            continue
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        # 跳过 data/ 运行数据目录
        if "data" in f.parts:
            continue
        # 仅扫描 knowledge/ 和 ops/ 根目录下的文件
        rel = f.relative_to(repo)
        first_part = rel.parts[0] if rel.parts else ""
        if first_part not in SCAN_DIRS:
            continue
        if len(rel.parts) <= 2:
            continue
        rel_str = str(rel).replace("\\", "/")
        if any(rel_str.startswith(p) for p in SKIP_PATH_PREFIXES):
            continue
        results.append(check_file(f, fix=args.fix))

    passed = [r for r in results if r["status"] == "pass"]
    failed = [r for r in results if r["status"] != "pass"]
    error_count = sum(len(r["issues"]) for r in failed)

    # 护栏D: 汇总质量问题（不影响评分）
    quality_bad = [r for r in results if r.get("quality_issues")]
    quality_count = sum(len(r.get("quality_issues", [])) for r in quality_bad)
    quality_warnings = sum(
        1 for r in quality_bad for qi in r.get("quality_issues", []) if qi.get("level") == "warning"
    )

    score = max(0, 10 - error_count)  # 每问题扣1分，最低0分

    if args.json:
        output = {
            "status": "pass" if not failed else "fail",
            "total": len(results),
            "passed": len(passed),
            "failed": len(failed),
            "issues": [
                {"file": r["file"], "issues": r["issues"]}
                for r in failed
            ],
            "score": score,
            # 护栏D: 质量清单（不影响 status/score）
            "quality": {
                "files_affected": len(quality_bad),
                "total_issues": quality_count,
                "warnings": quality_warnings,
                "top_issues": [
                    {"file": r["file"], "quality_issues": r.get("quality_issues", [])}
                    for r in quality_bad[:20]  # JSON 仅前20条
                ],
            },
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"YAML frontmatter 校验: {len(passed)}/{len(results)} 通过")
        if failed:
            print(f"\n❌ {len(failed)} 个文件有问题 ({error_count} 项):")
            for r in failed:
                print(f"  {r['file']}")
                for issue in r["issues"]:
                    print(f"    - {issue}")
        else:
            print("✅ 全部通过")

        # 护栏D: 质量告警
        if quality_bad:
            print(f"\n🟡 质量问题 ({quality_count} 项, 涉及 {len(quality_bad)} 文件):")
            print(f"   🟠 summary空壳: {quality_warnings} 项")
            for r in quality_bad[:10]:  # 仅显示前10条
                for qi in r.get("quality_issues", []):
                    print(f"   [{qi['level']}] {r['file']}: {qi['detail']}")
            if len(quality_bad) > 10:
                print(f"   ... 等 {len(quality_bad)} 个文件（完整清单见 --json quality 字段）")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
