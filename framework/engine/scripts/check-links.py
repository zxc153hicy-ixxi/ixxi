#!/usr/bin/env python3
"""check-links.py -- 链接与索引检查（二合一）

用法:
  python engine/scripts/check-links.py --repo <知识库根目录>
  python engine/scripts/check-links.py --repo . --mode broken   # wikilink 断链
  python engine/scripts/check-links.py --repo . --mode index    # index.md 一致性
  python engine/scripts/check-links.py --repo . --mode all      # 全部（默认）
  python engine/scripts/check-links.py --repo . --json

合并自: check-broken-links.py + check-index-consistency.py
"""

import argparse
import itertools
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKIP_FILES = {"Thumbs.db", ".DS_Store", "desktop.ini", ".gitkeep", ".placeholder"}
SKIP_DIRS = {".git", "__pycache__", ".fix-backup", "node_modules"}
TEMPLATE_DIRS = {"templates", "engine/templates"}
RAW_DIRS = {"raw"}

PLACEHOLDER_TARGETS = {
    "路径", "新名", "旧名", "link", "新页面标题", "旧页面标题",
    "文件名", "新条目", "重复数量", "...", "$name",
    "source", "target", "foo", "bar", "xxx", "yyy",
    "新文件", "旧文件", "引用", "wikilink", "内部链接",
    "新页面", "实际名", "知识库管理", "源质挽歌", "ixxi-agent", "应急预案",
    "syntax like this", "wiki/xxx", "^",
    "G18-工具优先", "G18", "ops/rules/<规则名>",
}

FENCED_CODE_RE = re.compile(r"```[^`]*```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]+`")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]+)?\]\]")


CODE_REGISTERS = {"EAX", "EBX", "ECX", "EDX", "ESP", "EBP", "ESI", "EDI",
                 "EIP", "EFLAGS", "CS", "DS", "SS", "ES", "FS", "GS"}
CODE_KEYWORDS = {"and", "or", "not", "for", "if", "while", "int", "void", "return"}


def _is_code_reference(link: str) -> bool:
    """Detect links that are code references, not wikilinks."""
    stripped = link.strip()
    if not stripped:
        return True
    if stripped in CODE_REGISTERS:
        return True
    for reg in CODE_REGISTERS:
        if stripped.startswith(reg + "+") or stripped.startswith(reg + "-"):
            return True
    if re.match(r"^0x[0-9A-Fa-f]+[\+\-]?\d*$", stripped):
        return True
    if stripped.startswith("${"):
        return True
    return False


def _is_ocr_artifact(link: str) -> bool:
    if not link.strip():
        return True
    if link.startswith("["):
        return True
    for char, group in itertools.groupby(link):
        if len(list(group)) >= 4:
            return True
    return False


def _strip_code(text: str) -> str:
    """Remove fenced code blocks and inline code before extracting wikilinks."""
    text = FENCED_CODE_RE.sub(" ", text)
    text = INLINE_CODE_RE.sub(" ", text)
    return text


def _extract_links(text: str) -> list[str]:
    clean = _strip_code(text)
    links = []
    for m in WIKILINK_RE.finditer(clean):
        target = m.group(1).strip()
        # Strip trailing backslash from table-escaped pipes (e.g., [[a/README\|a]])
        target = target.rstrip("\\")
        if target:
            links.append(target)
    return links


def _should_skip(link: str) -> bool:
    """Check if a link should be skipped entirely (not counted as a link at all)."""
    if link.startswith(("http://", "https://", "mailto:")):
        return True
    if link in PLACEHOLDER_TARGETS:
        return True
    if "${" in link:
        return True
    if _is_ocr_artifact(link):
        return True
    if _is_code_reference(link):
        return True
    return False


def _resolve_wikilink(link: str, current_file: Path, repo_root: Path) -> Path | None:
    if link.startswith(".."):
        candidate = (current_file.parent / link).resolve()
        if candidate.exists():
            return candidate
        candidate_md = (current_file.parent / f"{link}.md").resolve()
        return candidate_md if candidate_md.exists() else None
    # Try repo-root relative first
    candidate = repo_root / f"{link}.md"
    if candidate.exists():
        return candidate
    candidate = repo_root / link
    if candidate.exists() and candidate.is_file():
        return candidate
    # Try current-file-relative (for links like [[subdir/]] within same area)
    candidate = current_file.parent / f"{link}.md"
    if candidate.exists():
        return candidate
    candidate = current_file.parent / link
    if candidate.exists() and candidate.is_file():
        return candidate
    if link.endswith("/"):
        # Try repo root first
        candidate = repo_root / link.rstrip("/")
        if candidate.exists() and candidate.is_dir():
            return candidate
        index_md = repo_root / link.rstrip("/") / "index.md"
        if index_md.exists():
            return index_md
        readme = repo_root / link.rstrip("/") / "README.md"
        if readme.exists():
            return readme
        # Try relative to current file
        candidate = current_file.parent / link.rstrip("/")
        if candidate.exists() and candidate.is_dir():
            return candidate
        index_md = current_file.parent / link.rstrip("/") / "index.md"
        if index_md.exists():
            return index_md
        readme = current_file.parent / link.rstrip("/") / "README.md"
        if readme.exists():
            return readme
        return None
    # Try knowledge/learning/ prefix (imported content often uses shortened paths)
    for learn_prefix in ["knowledge/learning/", "knowledge/projects/"]:
        candidate = repo_root / learn_prefix / f"{link}.md"
        if candidate.exists():
            return candidate
        candidate = repo_root / learn_prefix / link
        if candidate.exists() and candidate.is_file():
            return candidate

    # Fallback: search by filename stem anywhere in repo
    stem = link.split("/")[-1]
    for f in repo_root.rglob(f"{stem}.md"):
        if f.name not in SKIP_FILES:
            return f
    return None


# ── mode: broken ──

def check_broken(repo: Path, files: list[str] | None = None) -> tuple[list[dict], list[dict]]:
    all_links, broken = [], []
    if files is not None:
        candidates = [repo / f for f in files if f.endswith(".md") and (repo / f).is_file()]
    else:
        candidates = sorted(repo.rglob("*.md"))

    for f in candidates:
        if f.name in SKIP_FILES:
            continue
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        rel_path = str(f.relative_to(repo))
        if any(rel_path.startswith(td) for td in TEMPLATE_DIRS):
            continue
        if any(rel_path.startswith(rd) for rd in RAW_DIRS):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for link in _extract_links(text):
            if _should_skip(link):
                continue
            resolved = _resolve_wikilink(link, f, repo)
            entry = {"source": str(f.relative_to(repo)), "target": link,
                     "resolved": str(resolved.relative_to(repo)) if resolved else None}
            all_links.append(entry)
            if resolved is None:
                broken.append(entry)
    return all_links, broken


# ── mode: index ──

def _extract_index_links(index_path: Path) -> list[str]:
    try:
        text = index_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    return [m.group(1).strip() for m in WIKILINK_RE.finditer(text)]


def _collect_actual_files(repo: Path, dirs: list[str]) -> set[str]:
    files = set()
    for d in dirs:
        dpath = repo / d
        if not dpath.exists():
            continue
        for f in dpath.rglob("*.md"):
            if f.name in SKIP_FILES:
                continue
            if any(part in SKIP_DIRS for part in f.parts):
                continue
            rel = str(f.relative_to(repo)).replace("\\", "/")
            stem = rel[:-3] if rel.endswith(".md") else rel
            files.add(stem)
    return files


def _resolve_link_target(link: str, repo: Path) -> str | None:
    cand = repo / f"{link}.md"
    if cand.exists():
        return link.replace("\\", "/")
    stem = link.split("/")[-1]
    matches = list(repo.rglob(f"{stem}.md"))
    if matches:
        rel = str(matches[0].relative_to(repo)).replace("\\", "/")
        return rel[:-3]
    return None


def check_index(repo: Path) -> tuple[list[dict], list[dict]]:
    index_md = repo / "index.md"
    if not index_md.exists():
        return [], [{"type": "missing_index"}]

    index_links = _extract_index_links(index_md)
    # index.md 精选目录只覆盖 projects/ + ops/，不覆盖 learning/（教材自动导入，非索引管辖）
    actual_files = _collect_actual_files(repo, ["knowledge/projects", "ops"])

    # 构建二级索引集：index.md 直接链接 + 子页面链接（支持层级导航）
    indexed = set(index_links)
    for link in index_links:
        target = _resolve_link_target(link, repo)
        if target:
            target_path = repo / f"{target}.md"
            if target_path.exists():
                sub_links = _extract_index_links(target_path)
                indexed.update(sub_links)

    dead_links = []
    unindexed = []

    for link in index_links:
        if _resolve_link_target(link, repo) is None:
            dead_links.append({"link": link})

    for f in sorted(actual_files):
        if f not in indexed:
            name = f.split("/")[-1]
            if name.lower() in ("readme", "index"):
                continue
            unindexed.append({"file": f})

    # 护栏B: 扩展检测——engine/scripts/ 脚本登记 + patterns/anti-patterns 子索引覆盖
    registry_issues = _check_registry_coverage(repo, indexed)
    unindexed.extend(registry_issues)

    return dead_links, unindexed


def _check_registry_coverage(repo: Path, indexed: set) -> list[dict]:
    """护栏B：检测新建脚本/正反模式是否已登记到对应索引页

    - engine/scripts/check-*.py → 是否在 activation.md 有入口（脚本完整清单在 activation.md，index.md 为精选导航）
    - ops/patterns/*.md（非索引页）→ 是否在正模式索引.md 有入口
    - ops/anti-patterns/*.md（非索引页）→ 是否在反模式索引.md 有入口
    """
    issues = []

    # 1. 检查脚本登记
    scripts_dir = repo / "engine" / "scripts"
    activation_text = (repo / "activation.md").read_text(encoding="utf-8", errors="replace") if (repo / "activation.md").exists() else ""
    for py_file in sorted(scripts_dir.glob("check-*.py")):
        name = py_file.stem
        if name not in activation_text:
            issues.append({
                "file": f"engine/scripts/{py_file.name}",
                "type": "script_unregistered",
                "detail": f"脚本未在 activation.md 登记",
            })

    # 2. 检查正模式登记
    patterns_dir = repo / "ops" / "patterns"
    patterns_index = repo / "ops" / "patterns" / "正模式索引.md"
    if patterns_index.exists():
        pi_text = patterns_index.read_text(encoding="utf-8", errors="replace")
        for md_file in sorted(patterns_dir.glob("*.md")):
            if "索引" in md_file.stem:
                continue
            if md_file.stem not in pi_text:
                issues.append({
                    "file": f"ops/patterns/{md_file.name}",
                    "type": "pattern_unregistered",
                    "detail": f"正模式未在索引页登记",
                })

    # 3. 检查反模式登记
    anti_dir = repo / "ops" / "anti-patterns"
    anti_index = repo / "ops" / "anti-patterns" / "反模式索引.md"
    if anti_index.exists():
        ai_text = anti_index.read_text(encoding="utf-8", errors="replace")
        for md_file in sorted(anti_dir.glob("*.md")):
            if "索引" in md_file.stem:
                continue
            if md_file.stem not in ai_text:
                issues.append({
                    "file": f"ops/anti-patterns/{md_file.name}",
                    "type": "antipattern_unregistered",
                    "detail": f"反模式未在索引页登记",
                })

    return issues


# ── main ──

def main(mode: str = "all", repo_path: str = None, json_out: bool = False, files: list[str] | None = None):
    repo = Path(repo_path).resolve() if repo_path else Path(__file__).resolve().parent.parent.parent

    modes_to_run = ["broken", "index"] if mode == "all" else [mode]
    all_results = {}

    for m in modes_to_run:
        if m == "broken":
            all_links, broken = check_broken(repo, files)
            score = max(0, 10 - len(broken))
            all_results["broken"] = {"label": "Wikilink 断链", "total": len(all_links),
                                      "broken": len(broken), "items": broken, "score": score}
        elif m == "index":
            dead_links, unindexed = check_index(repo)
            total_issues = len(dead_links) + len(unindexed)
            # 护栏B（正反模式/脚本未登记，含 type 字段）扣分；普通 unindexed 仅信息展示
            registry_count = sum(1 for u in unindexed if "type" in u)
            score = max(0, 10 - len(dead_links) * 2 - registry_count)
            all_results["index"] = {"label": "index.md 一致性",
                                     "dead_links": dead_links, "unindexed": unindexed,
                                     "total_issues": total_issues, "score": score}

    if json_out:
        output = {"status": "pass", "modes": {}}
        has_issues = False
        for m, data in all_results.items():
            summary = {k: v for k, v in data.items() if k != "items"}
            # 保留详细列表给下游脚本使用
            if m == "index":
                summary["dead_links_count"] = len(data.get("dead_links", []))
                summary["unindexed_count"] = len(data.get("unindexed", []))
            if data.get("score", 10) < 10:
                has_issues = True
            all_results[m]["_summary"] = summary
            output["modes"][m] = summary
        output["status"] = "fail" if has_issues else "pass"
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for m, data in all_results.items():
            print(f"--- {data['label']} ---")
            if m == "broken":
                print(f"  {data['total']} 个链接, {data['broken']} 个断链")
                if data["items"]:
                    for b in data["items"]:
                        print(f"  ❌ {b['source']} → [[{b['target']}]]")
                else:
                    print("  ✅ 无断链")
            elif m == "index":
                dl = data["dead_links"]
                ui = data["unindexed"]
                print(f"  死链: {len(dl)}, 未收录: {len(ui)}")
                if dl:
                    print(f"  ❌ 死链:")
                    for d in dl:
                        print(f"    [[{d['link']}]]")
                if ui:
                    print(f"  ⚠️ 未收录:")
                    for u in ui[:10]:
                        print(f"    {u['file']}")
                    if len(ui) > 10:
                        print(f"    ... 等 {len(ui) - 10} 个")
                if not dl and not ui:
                    print("  ✅ index.md 与实际文件一致")
            print()

    any_issues = any(data.get("score", 10) < 10 for data in all_results.values())
    return 1 if any_issues else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="链接与索引检查（二合一）")
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--mode", type=str, default="all",
                        choices=["all", "broken", "index"])
    parser.add_argument("--files", nargs="*", default=None,
                        help="只检查指定文件（相对仓库根，空格分隔）")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    sys.exit(main(mode=args.mode, repo_path=args.repo, json_out=args.json, files=args.files))
