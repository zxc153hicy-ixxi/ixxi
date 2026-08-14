#!/usr/bin/env python3
"""版本清理脚本 —— 扫描多版本文件，保留最新 N 个，删除冗余旧版。

用法:
  python cleanup-versions.py              # dry-run 预览
  python cleanup-versions.py --execute    # 执行删除
  python cleanup-versions.py --json       # JSON 输出（供其他工具消费）
  python cleanup-versions.py --execute -y # 跳过确认直接删除
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# === 配置加载 ===

def load_config(config_path: str) -> dict:
    """从 YAML 文件加载配置。使用内联解析器，不依赖 PyYAML。"""
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
    return parse_simple_yaml(content)


def parse_simple_yaml(content: str) -> dict:
    """解析简化 YAML —— 仅支持本脚本所需的键值对和列表结构。"""
    result = {}
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        i += 1

        # 跳过空行和注释
        if not stripped or stripped.startswith("#"):
            continue

        # 键值对
        if ":" in stripped and not stripped.startswith("- "):
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()

            if value == "":
                # 值为空，检查下一行是否为列表或缩进块
                if i < len(lines) and lines[i].strip().startswith("- "):
                    # 列表值
                    list_values = []
                    while i < len(lines) and lines[i].strip().startswith("- "):
                        list_values.append(lines[i].strip()[2:].strip())
                        i += 1
                    result[key] = list_values
                elif i < len(lines) and lines[i].startswith("  ") and ":" in lines[i]:
                    # 内联字典（缩进键值对）
                    sub_dict = {}
                    while i < len(lines) and lines[i].startswith("  ") and ":" in lines[i]:
                        sk, _, sv = lines[i].strip().partition(":")
                        sk = sk.strip()
                        sv = sv.strip()
                        if sv.isdigit():
                            sub_dict[sk] = int(sv)
                        else:
                            sub_dict[sk] = sv
                        i += 1
                    result[key] = sub_dict
                else:
                    result[key] = ""
            elif value.isdigit():
                result[key] = int(value)
            else:
                # Strip surrounding quotes from YAML string values
                if len(value) >= 2 and (
                    (value.startswith('"') and value.endswith('"'))
                    or (value.startswith("'") and value.endswith("'"))
                ):
                    value = value[1:-1]
                result[key] = value

    return result


def get_repo_root() -> Path:
    """获取知识库仓库根目录（从脚本位置推算）。"""
    return Path(__file__).resolve().parent.parent.parent


# === Frontmatter 解析 ===

FM_PATTERN = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def parse_frontmatter(filepath: str) -> dict:
    """提取文件的 YAML frontmatter。失败返回空字典。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read(4096)  # 只读前 4KB，frontmatter 通常在文件开头
        match = FM_PATTERN.match(content)
        if not match:
            return {}
        return parse_simple_yaml(match.group(1))
    except Exception:
        return {}


# === 版本号解析 ===

SEMVER_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$")
TWO_PART_PATTERN = re.compile(r"^(\d+)\.(\d+)$")
NUMERIC_PATTERN = re.compile(r"^(\d+)$")
TAGGED_PATTERN = re.compile(r"^(\d+)-(.+)$")


def parse_version(version_str: str) -> Optional[tuple]:
    """
    解析版本号为可排序元组 (主版本号, 次版本号, 补丁号, 标签)。
    - 纯数字 "10" → (10, 0, 0, "")
    - 语义版本 "0.6.1" → (0, 6, 1, "")
    - 带标签 "8-完全补完" → (8, 0, 0, "完全补完")
    - 无法解析 → None
    主版本号在第一位确保跨格式的正确排序（v11 > v8-tagged）。
    """
    v = str(version_str).strip()

    # 两段式版本 (如 "2.1", "2.15")
    m = TWO_PART_PATTERN.match(v)
    if m:
        return (int(m.group(1)), int(m.group(2)), 0, "")

    # 语义版本
    m = SEMVER_PATTERN.match(v)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)), "")

    # 纯数字
    m = NUMERIC_PATTERN.match(v)
    if m:
        return (int(m.group(1)), 0, 0, "")

    # 带子标签
    m = TAGGED_PATTERN.match(v)
    if m:
        return (int(m.group(1)), 0, 0, m.group(2))

    return None


def sort_key(file_info: dict) -> tuple:
    """返回用于排序的键。无法解析版本号的文件排到最后。"""
    parsed = file_info.get("_parsed_version")
    if parsed is None:
        return (-1, 0, 0, "")
    return parsed


# === 扫描与分组 ===

def scan_files(config: dict, repo_root: Path) -> list:
    """扫描配置路径，返回包含 version+version_of 的文件信息列表。"""
    results = []
    scan_paths = [repo_root / p for p in config.get("scan_paths", ["knowledge/"])]
    exclude_paths = {repo_root / p for p in config.get("exclude_paths", [])}

    for scan_root in scan_paths:
        if not scan_root.exists():
            print(f"[WARN] 扫描路径不存在: {scan_root}", file=sys.stderr)
            continue
        for md_file in scan_root.rglob("*.md"):
            # 检查是否在排除路径中
            if any(md_file.is_relative_to(ex) for ex in exclude_paths):
                continue

            fm = parse_frontmatter(str(md_file))
            version = fm.get("version")
            version_of = fm.get("version_of")

            if not version or not version_of:
                if version or version_of:
                    # 有其中一个字段但缺另一个
                    print(f"[SKIP] 缺少 version 或 version_of: {md_file}", file=sys.stderr)
                continue

            parsed = parse_version(version)
            if parsed is None:
                print(f"[SKIP] 无法解析版本号 '{version}': {md_file}", file=sys.stderr)
                continue

            results.append({
                "path": str(md_file.relative_to(repo_root)),
                "abspath": str(md_file),
                "version": version,
                "version_of": version_of,
                "status": fm.get("status", ""),
                "_parsed_version": parsed,
            })

    return results


def group_by_chain(files: list, config: dict) -> dict:
    """按 version_of 分组，每组内按版本排序，返回待删和保留清单。"""
    chains = {}
    for f in files:
        vo = f["version_of"]
        if vo not in chains:
            chains[vo] = []
        chains[vo].append(f)

    result = {"chains": {}, "total_delete": 0, "total_keep": 0}

    no_clean = set(config.get("no_clean", []))
    default_keep = config.get("keep_latest", 2)
    per_chain = config.get("per_chain", {})

    for vo, items in chains.items():
        if vo in no_clean:
            result["chains"][vo] = {"keep": items, "delete": [], "keep_count": len(items)}
            result["total_keep"] += len(items)
            continue

        # 按版本排序（降序，最新的在前）
        items.sort(key=sort_key, reverse=True)

        keep_n = per_chain.get(vo, default_keep)
        keep = items[:keep_n]
        delete = items[keep_n:]

        result["chains"][vo] = {
            "keep": keep,
            "delete": delete,
            "keep_count": keep_n,
        }
        result["total_delete"] += len(delete)
        result["total_keep"] += len(keep)

    return result


# === 输出格式化 ===

def print_dry_run(result: dict, config: dict, repo_root: Path):
    """打印 dry-run 预览。"""
    scan_paths = ", ".join(config.get("scan_paths", []))
    print("=== 版本清理预览 ===")
    print(f"扫描目录: {scan_paths}")
    print()

    if not result["chains"]:
        print("未发现可清理的版本链。")
        return

    for vo, chain in result["chains"].items():
        total = len(chain["keep"]) + len(chain["delete"])
        keep_versions = [f["version"] for f in chain["keep"]]
        print(f"[{vo}] ({total}版本) -> 保留 {chain['keep_count']}: {', '.join(keep_versions)} -> 删除 {len(chain['delete'])}")
        for f in chain["delete"]:
            print(f"   [DEL] {f['path']}")
        print()

    print("-" * 40)
    print(f"共 {len(result['chains'])} 条版本链，将删除 {result['total_delete']} 个文件")
    print(f"运行 cleanup-versions.py --execute 执行删除")


def print_json_output(result: dict):
    """输出 JSON 格式（供其他工具消费）。"""
    clean_chains = {}
    for vo, chain in result["chains"].items():
        clean_chains[vo] = {
            "keep": [{"path": f["path"], "version": f["version"]} for f in chain["keep"]],
            "delete": [{"path": f["path"], "version": f["version"]} for f in chain["delete"]],
            "keep_count": chain["keep_count"],
        }
    output = {
        "chains": clean_chains,
        "total_delete": result["total_delete"],
        "total_keep": result["total_keep"],
        "total_chains": len(result["chains"]),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


# === 删除执行 ===

def is_git_tracked(filepath: str) -> bool:
    """检查文件是否被 git 追踪。"""
    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", filepath],
            cwd=os.path.dirname(filepath) or ".",
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def execute_deletion(result: dict, repo_root: Path, skip_confirm: bool = False):
    """执行删除操作。"""
    all_deletes = []
    for chain in result["chains"].values():
        all_deletes.extend(chain["delete"])

    if not all_deletes:
        print("没有需要删除的文件。")
        return

    print(f"将删除 {len(all_deletes)} 个文件:\n")
    for f in all_deletes:
        print(f"  [DEL] {f['path']}")

    # 检查 git 追踪状态
    untracked = []
    for f in all_deletes:
        if not is_git_tracked(f["abspath"]):
            untracked.append(f["path"])

    if untracked:
        print(f"\n[WARN] 以下 {len(untracked)} 个文件不在 git 中，跳过删除:")
        for p in untracked:
            print(f"  [SKIP] {p}")
        all_deletes = [f for f in all_deletes if f["path"] not in untracked]

    if not all_deletes:
        print("\n没有可安全删除的文件（全部被 git 守护拦截）。")
        return

    print(f"\n实际将删除 {len(all_deletes)} 个 git-tracked 文件。")

    # 确认
    if not skip_confirm:
        response = input("\n确认删除? 输入 'yes' 继续: ")
        if response.strip() != "yes":
            print("已取消。")
            return

    # 执行删除
    deleted = []
    failed = []
    for f in all_deletes:
        try:
            os.remove(f["abspath"])
            deleted.append(f)
        except OSError as e:
            print(f"[ERROR] 删除失败: {f['path']} - {e}", file=sys.stderr)
            failed.append(f)

    # 写日志
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "mode": "execute",
        "chains_found": len(result["chains"]),
        "files_deleted": len(deleted),
        "files_failed": len(failed),
        "deleted": [{"path": f["path"], "version": f["version"], "version_of": f["version_of"]} for f in deleted],
        "failed": [{"path": f["path"], "version": f["version"]} for f in failed],
        "kept": [],
    }
    for chain in result["chains"].values():
        for f in chain["keep"]:
            log_entry["kept"].append({"path": f["path"], "version": f["version"], "version_of": f["version_of"]})

    log_path = repo_root / "raw" / "sessions" / "cleanup-log.json"
    existing_logs = []
    if log_path.exists():
        try:
            existing_logs = json.loads(log_path.read_text(encoding="utf-8"))
            if not isinstance(existing_logs, list):
                existing_logs = [existing_logs]
        except Exception:
            existing_logs = []
    existing_logs.append(log_entry)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(existing_logs, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[WARN] 日志写入失败: {e}", file=sys.stderr)

    print(f"\n[DONE] 已删除 {len(deleted)} 个文件")
    if failed:
        print(f"[FAIL] {len(failed)} 个文件删除失败")
    print(f"[LOG] {log_path.relative_to(repo_root)}")


# === 主入口 ===

def main():
    parser = argparse.ArgumentParser(
        description="版本清理脚本 —— 扫描多版本文件，保留最新 N 个，删除冗余旧版"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--execute", action="store_true", help="执行删除（默认 dry-run）")
    group.add_argument("--json", action="store_true", help="JSON 输出模式")
    parser.add_argument("--yes", "-y", action="store_true", help="跳过确认（仅与 --execute 配合）")
    parser.add_argument("--config", default=None, help="配置文件路径")
    parser.add_argument("--scope", default=None, help="仅扫描指定范围")
    parser.add_argument("--keep", type=int, default=None, help="覆盖配置中的保留数量")

    args = parser.parse_args()

    repo_root = get_repo_root()
    config_path = args.config or str(repo_root / "engine" / "config" / "cleanup-config.yaml")

    if not os.path.exists(config_path):
        print(f"[ERROR] 配置文件不存在: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)

    if args.keep is not None:
        config["keep_latest"] = args.keep

    if args.scope:
        config["scan_paths"] = [p for p in config["scan_paths"] if args.scope in p]
        if not config["scan_paths"]:
            print(f"[ERROR] --scope '{args.scope}' 未匹配任何扫描路径", file=sys.stderr)
            sys.exit(1)

    files = scan_files(config, repo_root)
    result = group_by_chain(files, config)

    if args.json:
        print_json_output(result)
    elif args.execute:
        execute_deletion(result, repo_root, skip_confirm=args.yes)
    else:
        print_dry_run(result, config, repo_root)
        if result["total_delete"] > 0:
            sys.exit(1)  # 非零退出码表示有待清理项


if __name__ == "__main__":
    main()
