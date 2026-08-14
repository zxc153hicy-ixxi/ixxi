#!/usr/bin/env python3
"""check-ocr-quality.py -- 内容质量扫描器

检测 5 类 OCR/格式问题:
  1. 乱码字符 (U+FFFD, ����)
  2. 死图片引用 (![](images/) 指向不存在的文件)
  3. 无标题结构 (全文零 # 标题)
  4. 空壳文件 (<200 字节)
  5. 段落断裂 (连续单换行无空行，OCR 典型产物)

用法:
  python engine/scripts/check-ocr-quality.py --repo <知识库根目录>            # 全量扫描
  python engine/scripts/check-ocr-quality.py --repo . --path knowledge/learning/网络安全  # 指定目录
  python engine/scripts/check-ocr-quality.py --repo . --fix                  # 扫描+自动修复
  python engine/scripts/check-ocr-quality.py --repo . --fix --mark-only      # 仅标记不修改正文
  python engine/scripts/check-ocr-quality.py --repo . --json                 # JSON 输出
"""

import argparse
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

try:
    import yaml
except ImportError:
    yaml = None

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# ============================================================
# 检测函数
# ============================================================

def check_garbled(text: str, filepath: Path) -> list[dict]:
    """检测 OCR 乱码字符"""
    issues = []
    for i, line in enumerate(text.splitlines(), 1):
        if '�' in line or '��' in line:
            issues.append({
                "type": "garbled",
                "line": i,
                "detail": line.strip()[:80]
            })
    return issues


def check_dead_images(text: str, filepath: Path) -> list[dict]:
    """检测死图片引用 -- ![](images/hash.jpg) 但 images/ 目录不存在或图片缺失"""
    issues = []
    img_refs = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', text)
    if not img_refs:
        return issues

    file_dir = filepath.parent
    for alt, src in img_refs:
        if src.startswith('images/'):
            img_path = file_dir / src
            if not img_path.exists():
                issues.append({
                    "type": "dead_image",
                    "detail": f"![]({src})"
                })
    return issues


def check_headings(text: str, filepath: Path) -> list[dict]:
    """检测无标题结构"""
    issues = []
    has_heading = bool(re.search(r'^#{1,6}\s', text, re.MULTILINE))
    if not has_heading:
        issues.append({
            "type": "no_headings",
            "detail": "全文无 # 标题，缺少目录结构"
        })
    return issues


def check_empty(text: str, filepath: Path) -> list[dict]:
    """检测空壳文件"""
    issues = []
    size = filepath.stat().st_size
    # 只算正文大小（排除 frontmatter）
    body = re.sub(r'^---\n.*?\n---\n', '', text, count=1, flags=re.DOTALL).strip()
    if size < 200 or len(body) < 100:
        issues.append({
            "type": "empty_shell",
            "detail": f"文件 {size}B, 正文 {len(body)} 字符"
        })
    return issues


def check_broken_paragraphs(text: str, filepath: Path) -> list[dict]:
    """检测段落断裂 -- 连续 5+ 行非空无空行分隔（OCR 特征）"""
    issues = []
    lines = text.splitlines()
    consecutive = 0
    max_consecutive = 0
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and not stripped.startswith('-') \
           and not stripped.startswith('|') and not stripped.startswith('```') \
           and not stripped.startswith('!['):
            consecutive += 1
        else:
            if consecutive > max_consecutive:
                max_consecutive = consecutive
            consecutive = 0
    if consecutive > max_consecutive:
        max_consecutive = consecutive

    if max_consecutive >= 8:
        issues.append({
            "type": "broken_paragraphs",
            "detail": f"最多连续 {max_consecutive} 行无空行分隔（段落断裂特征）"
        })
    return issues


# ============================================================
# 修复函数 (--fix 模式)
# ============================================================

def fix_dead_images(filepath: Path, dry_run: bool = False) -> int:
    """删除死图片引用行"""
    text = filepath.read_text(encoding="utf-8", errors="replace")
    new_lines = []
    removed = 0
    for line in text.splitlines():
        if re.match(r'^!\[\]\(images/[^)]+\)\s*$', line.strip()):
            removed += 1
            continue
        new_lines.append(line)
    if removed > 0 and not dry_run:
        filepath.write_text('\n'.join(new_lines) + '\n', encoding="utf-8")
    return removed


def fix_broken_paragraphs(filepath: Path, dry_run: bool = False) -> int:
    """合并连续断裂段落 -- 跳过 YAML frontmatter，仅处理正文"""
    text = filepath.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    new_lines = []
    buffer = []
    merged = 0

    # 检测 frontmatter 边界（--- 包裹的 YAML 区域）
    in_fm = False
    fm_end = -1
    if lines and lines[0].strip() == '---':
        in_fm = True
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                fm_end = i
                break

    def flush_buffer():
        nonlocal merged
        if buffer:
            if len(buffer) >= 3:
                new_lines.append(' '.join(buffer))
                merged += len(buffer) - 1
            else:
                new_lines.extend(buffer)
            buffer.clear()

    for idx, line in enumerate(lines):
        # Frontmatter 区域：原样保留，不合并
        if idx <= fm_end:
            new_lines.append(line)
            continue

        stripped = line.strip()
        if not stripped or stripped.startswith('#') or stripped.startswith('```') \
           or stripped.startswith('|') or stripped.startswith('- ') \
           or stripped.startswith('![') or stripped == '---':
            flush_buffer()
            new_lines.append(line)
        else:
            buffer.append(stripped)

    flush_buffer()
    if merged > 0 and not dry_run:
        filepath.write_text('\n'.join(new_lines) + '\n', encoding="utf-8")
    return merged


def mark_frontmatter(filepath: Path, issues: list[str]) -> None:
    """安全注入 quality_issues——用 YAML 库解析+dump，杜绝正则破坏"""
    if yaml is None:
        return  # 无 yaml 库，跳过标记

    text = filepath.read_text(encoding="utf-8", errors="replace")

    # 提取 frontmatter 和正文
    fm_match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not fm_match:
        return

    fm_text = fm_match.group(1)
    body = text[fm_match.end():]

    # 安全解析 YAML
    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError:
        return  # 解析失败，不碰文件

    if not isinstance(fm, dict):
        return

    # 更新 quality_issues（去重、排序）
    existing = fm.get("quality_issues", [])
    if isinstance(existing, str):
        existing = [existing]
    merged = sorted(set(list(existing) + issues))
    fm["quality_issues"] = merged

    # 安全 dump 为多行 YAML
    new_fm = yaml.dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False).strip()
    new_text = f"---\n{new_fm}\n---{body}"

    filepath.write_text(new_text, encoding="utf-8")


# ============================================================
# OCR 碎片清理
# ============================================================

def clean_ocr_debris(scan_path: Path) -> dict:
    """清理 OCR 碎片文件（_page_*_Picture_*.jpeg 等）和 .md 中的碎片引用

    返回清理统计 dict。
    """
    debris_patterns = [
        '_page_*_Picture_*.jpeg',
        '_page_*_Figure_*.jpeg',
        '_page_*_Picture_*.jpg',
        '_page_*_Figure_*.jpg',
    ]

    # 1. 查找碎片文件
    debris_files = []
    for pattern in debris_patterns:
        debris_files.extend(scan_path.rglob(pattern))

    # 2. 从 .md 中清除 ![](_page_* 引用
    md_files = list(scan_path.rglob('*.md'))
    refs_cleaned = 0
    for md in md_files:
        try:
            text = md.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue

        # 匹配 ![](_page_NNN_xxx.yyy) 格式的碎片引用
        new_text = re.sub(r'!\[[^\]]*\]\(_page_\d+_[^)]+\)\s*', '', text)
        if new_text != text:
            md.write_text(new_text, encoding='utf-8')
            refs_cleaned += 1

    # 3. 删除碎片文件
    deleted = 0
    for f in debris_files:
        try:
            if f.exists():
                f.unlink()
                deleted += 1
        except OSError:
            pass

    return {
        'debris_files_found': len(debris_files),
        'debris_files_deleted': deleted,
        'refs_cleaned': refs_cleaned,
    }


# ============================================================
# 主逻辑
# ============================================================

CHECKERS = [
    ("garbled", check_garbled),
    ("dead_image", check_dead_images),
    ("no_headings", check_headings),
    ("empty_shell", check_empty),
    ("broken_paragraphs", check_broken_paragraphs),
]

FIXERS = {
    "dead_image": fix_dead_images,
    "broken_paragraphs": fix_broken_paragraphs,
}


def is_llm_reviewed(text: str) -> bool:
    """LLM 已审查通过的文件不再报机械问题"""
    fm_match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not fm_match:
        return False
    fm_text = fm_match.group(1)
    try:
        fm = yaml.safe_load(fm_text) if yaml else {}
    except Exception:
        return False
    if not isinstance(fm, dict):
        return False
    # degraded = LLM 确认内容不可修复
    if fm.get("status") == "degraded":
        return True
    # 无 quality_issues = LLM 审查通过
    if "quality_issues" not in fm:
        return True
    # quality_issues 为空列表 = LLM 已清除
    qi = fm.get("quality_issues", [])
    if isinstance(qi, list) and len(qi) == 0:
        return True
    return False


def scan_file(filepath: Path) -> dict:
    """扫描单个文件，返回问题列表"""
    filepath = filepath.resolve()
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {"file": str(filepath), "issues": [{"type": "unreadable", "detail": "无法读取"}]}

    # 尊重 LLM 审查结果——已审查通过的文件不再报机械问题
    if is_llm_reviewed(text):
        return {"file": str(filepath), "issues": []}

    result = {"file": str(filepath), "issues": []}
    for issue_type, checker in CHECKERS:
        found = checker(text, filepath)
        result["issues"].extend(found)
    return result


def scan_directory(root: Path, path_filter: Path = None) -> list[dict]:
    """递归扫描目录下所有 .md 文件"""
    scan_root = path_filter if path_filter else root
    results = []
    md_files = list(scan_root.rglob("*.md"))
    for fp in md_files:
        r = scan_file(fp)
        if r["issues"]:
            results.append(r)
    return results


def main():
    parser = argparse.ArgumentParser(description="知识库内容质量扫描器")
    parser.add_argument("--repo", required=True, help="知识库根目录")
    parser.add_argument("--path", default=None, help="扫描指定子目录（默认全量）")
    parser.add_argument("--fix", action="store_true", help="自动修复可修复的问题")
    parser.add_argument("--mark-only", action="store_true", help="仅标记 frontmatter，不修改正文")
    parser.add_argument("--clean", action="store_true", help="清理 OCR 碎片文件和引用（_page_*_Picture/Figure_*.jpeg + ![]() 引用）")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    scan_path = repo / args.path if args.path else repo

    # --clean 模式：清理碎片 + 清除引用
    if args.clean:
        clean_result = clean_ocr_debris(scan_path)
        if not args.json:
            print(f"OCR 碎片清理: {scan_path}")
            print(f"  碎片文件: 发现 {clean_result['debris_files_found']}, 已删除 {clean_result['debris_files_deleted']}")
            print(f"  引用清理: {clean_result['refs_cleaned']} 个 .md 文件")
            print()
        if args.json:
            print(json.dumps({"clean": clean_result}, ensure_ascii=False, indent=2))
        if not args.fix:
            return

    if not args.json:
        print(f"扫描目录: {scan_path}")
        print()

    results = scan_directory(repo, scan_path)

    # 统计
    stats = defaultdict(int)
    files_with_issues = 0
    for r in results:
        if r["issues"]:
            files_with_issues += 1
            for issue in r["issues"]:
                stats[issue["type"]] += 1

    if args.json:
        total_scanned = len(list(scan_path.rglob("*.md")))
        # 评分：只计算可修复问题（排除 LLM 已接受的 garbled）
        fixable_issues = sum(v for k, v in stats.items() if k != "garbled")
        if files_with_issues == 0:
            score = 10
        elif fixable_issues == 0:
            score = 9  # 仅有 garbled，LLM 已确认可接受
        elif files_with_issues <= 3:
            score = 7
        else:
            score = max(0, 10 - files_with_issues // 10)

        print(json.dumps({
            "status": "pass" if score >= 7 else "fail",
            "score": score,
            "scanned": total_scanned,
            "files_with_issues": files_with_issues,
            "issue_counts": dict(stats),
            "results": [{**r, "file": r["file"].replace(chr(92), "/")} for r in results]
        }, ensure_ascii=False, indent=2))
        return

    # 非 JSON 输出
    print(f"已扫描: {len(list(scan_path.rglob('*.md')))} 篇")
    print(f"有问题: {files_with_issues} 篇")
    print()
    print("问题分布:")
    type_labels = {
        "garbled": "OCR乱码字符",
        "dead_image": "死图片引用",
        "no_headings": "无标题结构",
        "empty_shell": "空壳文件",
        "broken_paragraphs": "段落断裂(≥8行连续无空行)"
    }
    for t, label in type_labels.items():
        count = stats.get(t, 0)
        indicator = "🔴" if count > 10 else ("🟡" if count > 0 else "🟢")
        print(f"  {indicator} {label}: {count}")

    # --fix 模式
    if args.fix:
        print()
        print("自动修复...")
        total_fixed = 0
        for r in results:
            fp = Path(r["file"])
            issue_types = set(i["type"] for i in r["issues"])
            fixable = issue_types & set(FIXERS.keys())

            if not args.mark_only:
                for ft in fixable:
                    n = FIXERS[ft](fp, dry_run=False)
                    total_fixed += n

            # 标记 frontmatter
            all_types = list(set(i["type"] for i in r["issues"]))
            mark_frontmatter(fp, all_types)

        print(f"  修复项: {total_fixed}")
        print(f"  标记文件: {files_with_issues} 篇已写入 quality_issues 字段")


if __name__ == "__main__":
    main()
