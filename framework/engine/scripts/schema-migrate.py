#!/usr/bin/env python3
"""schema-migrate.py -- 可迁移对象 schema 升级工具（不变量 I10：version + schema + migration strategy）

扫描目标目录（默认 personal/）下所有 .md（skill/规则）与 capability.json，
读取 frontmatter / JSON 的 `version` 字段，按 MIGRATIONS 规则逐版本迁移：

  - version 缺失（v0）      → 迁移到 v1：补 `version: "1.0.0"` + `version_of: "<来源>"`
  - version = "1.0.0"（v1） → 跳过（已最新）
  - version > 最新迁移目标  → 跳过并提示（可能是手动升级，勿覆盖）

迁移只增不删不改已有字段，幂等（重复执行不产生重复字段）。

用法:
  python schema-migrate.py --root <目录>               # dry-run：列出迁移计划，不写入
  python schema-migrate.py --root <目录> --execute     # 实际迁移
  python schema-migrate.py --root <目录> --execute --json   # 执行并输出 JSON 结果（供 hook 消费）

零第三方依赖（仅 pathlib/re/json/argparse）。
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

# 当前 schema 最新版本（迁移目标终点）。升级到 v2 时改为 "2.0.0" 并新增迁移规则。
LATEST_SCHEMA = "1.0.0"

# 扫描时跳过的目录（避免把资产/参考材料/隐藏目录误当迁移对象）
SKIP_DIRS = {".git", "__pycache__", ".idea", ".vscode", "node_modules",
             "assets", "references", "media"}

# 语义版本号解析：X.Y.Z（允许前置 v，忽略 build/label 用于比较）
SEMVER_RE = re.compile(r"^[vV]?(\d+)\.(\d+)\.(\d+)")


def parse_version(v) -> tuple | None:
    """把任意 version 值归一化为可比较元组 (major, minor, patch)。解析失败返回 None。"""
    if v is None:
        return None
    m = SEMVER_RE.match(str(v).strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def version_ge(v, target) -> bool:
    """v 是否 ≥ target（两者均为 '0.0.0' 式字符串）。v 无法解析时视为缺失 → False。"""
    a, b = parse_version(v), parse_version(target)
    if a is None or b is None:
        return False
    return a >= b


# === frontmatter 解析（仅正则，不依赖 PyYAML） ===

FM_OPEN_RE = re.compile(r"\A---[ \t]*\r?\n")
FM_CLOSE_RE = re.compile(r"\r?\n---")


def split_frontmatter(text: str) -> tuple[str | None, str, int, int]:
    """返回 (yaml_block, 开标签之后的正文, body_start, body_end)。
    - 无 frontmatter：返回 (None, text, -1, -1)
    - body_start 指向开标签 `---\n` 之后；body_end 指向闭标签前导换行处
    """
    m = FM_OPEN_RE.match(text)
    if not m:
        return None, text, -1, -1
    body_start = m.end()
    close = FM_CLOSE_RE.search(text, body_start)
    if not close:
        return None, text, -1, -1
    body_end = close.start()
    return text[body_start:body_end], text[body_end:], body_start, body_end


def parse_simple_yaml(block: str) -> dict:
    """解析简化 YAML —— 仅支持顶层 `key: value` 与 `key:` 空值行（本工具所需子集）。"""
    data: dict = {}
    for line in block.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("- ") or ":" not in s:
            continue
        if s.startswith(" ") and ":" not in s.partition(":")[0].strip():
            continue
        key, _, value = s.partition(":")
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if not value:
            data[key] = None
        elif (value.startswith('"') and value.endswith('"')) or \
             (value.startswith("'") and value.endswith("'")):
            data[key] = value[1:-1]
        elif value.lower() in ("true", "false"):
            data[key] = value.lower() == "true"
        else:
            data[key] = value
    return data


def yaml_escape(s: str) -> str:
    """YAML 双引号转义。"""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def from_key(version) -> str:
    """把 version 值归为迁移规则键（MIGRATIONS 的 key）：
    缺失/None → '0'；'X.Y.Z' 取主版本号 → 'X'；无法解析 → '0'。"""
    if version is None:
        return "0"
    m = SEMVER_RE.match(str(version).strip())
    return m.group(1) if m else "0"


# === 扫描 ===

def scan_targets(root: Path) -> list[dict]:
    """递归扫描 root，返回 [{path, kind}]。kind: 'md' | 'capability'"""
    targets: list[dict] = []
    if not root.exists():
        return targets
    for p in sorted(root.rglob("*")):
        if p.is_dir():
            if p.name in SKIP_DIRS or p.name.startswith("."):
                continue
            continue
        if any(part in SKIP_DIRS or part.startswith(".") for part in p.relative_to(root).parts[:-1]):
            continue
        if p.suffix == ".md":
            targets.append({"path": p, "kind": "md"})
        elif p.name == "capability.json":
            targets.append({"path": p, "kind": "capability"})
    return targets


# === 字段读取 ===

def read_md_fields(path: Path) -> dict:
    """读取 .md 的 version / name / 是否含 frontmatter。"""
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception as e:
        return {"error": f"读取失败: {e}"}
    yaml_block, _, _, _ = split_frontmatter(raw)
    data = parse_simple_yaml(yaml_block) if yaml_block is not None else {}
    return {
        "version": data.get("version"),
        "name": data.get("name"),
        "has_fm": yaml_block is not None,
        "raw": raw,
    }


def read_capability_fields(path: Path) -> dict:
    """读取 capability.json 的 version / id。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": f"读取失败: {e}"}
    if not isinstance(data, dict):
        return {"error": "JSON 顶层不是对象"}
    return {"version": data.get("version"), "id": data.get("id")}


def default_version_of(path: Path, data: dict) -> str:
    """为迁移对象计算 version_of 来源标识（人类可读、不含版本号）。
    优先 name / id 字段；SKILL.md 用所在目录名；否则用文件名主干。"""
    if data.get("name"):
        return str(data["name"])
    if data.get("id"):
        return str(data["id"])
    if path.stem.upper() == "SKILL":
        return path.parent.name
    return path.stem


# === 迁移规则 ===
# MIGRATIONS[version_from] -> {to: 目标版本}，单一事实源，决定哪些版本需要迁移。
# 扩展 v1→v2：新增键 "1" -> {"to": "2.0.0"}，并在 _MIGRATORS 中登记转换函数。
MIGRATIONS = {
    "0": {"to": LATEST_SCHEMA},  # version 缺失 = v0 → v1
}


def _migrate_md_v0(path: Path, raw: str, data: dict) -> str:
    version_of = default_version_of(path, data)
    fields = f'version: "{LATEST_SCHEMA}"\nversion_of: "{yaml_escape(version_of)}"\n'
    yaml_block, _, body_start, _ = split_frontmatter(raw)
    if yaml_block is not None:
        # 插入到 frontmatter 顶部（开标签之后），保留原有字段与正文不动
        return raw[:body_start] + fields + raw[body_start:]
    # 无 frontmatter：前置新 frontmatter 块
    return f"---\n{fields}---\n\n" + raw


def _migrate_capability_v0(path: Path, raw: str, data: dict) -> str:
    version_of = data.get("id") or default_version_of(path, data)
    block = f'  "version": "{LATEST_SCHEMA}",\n  "version_of": "{yaml_escape(str(version_of))}",\n'
    i = raw.find("{")
    if i == -1:
        raise ValueError(f"{path}: 找不到 JSON 起始花括号")
    insert_at = i + 1
    if insert_at < len(raw) and raw[insert_at] == "\n":
        insert_at += 1  # 吞掉开括号后的换行，避免产生空行
    elif insert_at < len(raw) and raw[insert_at] not in (" ", "\r"):
        block = "\n" + block
    return raw[:insert_at] + block + raw[insert_at:]


# 迁移函数注册表：kind → {version_from: 转换函数}。转换函数 (path, raw, data) -> 新内容
_MIGRATORS = {
    "md": {"0": _migrate_md_v0},
    "capability": {"0": _migrate_capability_v0},
}


def classify(path: Path, kind: str, fields: dict) -> dict:
    """返回迁移计划条目。action ∈ add-fields / add-frontmatter / skip-latest / skip-newer / error"""
    entry = {
        "path": str(path),
        "kind": kind,
        "version": None,
        "version_from": "0",
        "version_of": None,
        "target": LATEST_SCHEMA,
        "action": "",
        "note": "",
    }
    if "error" in fields:
        entry["action"] = "error"
        entry["note"] = fields["error"]
        return entry

    version = fields.get("version")
    entry["version"] = version

    # 已是当前最新或更新 → 直接跳过（v1 无迁移规则，无需查表）
    if version is not None and version_ge(str(version), LATEST_SCHEMA):
        entry["action"] = "skip-latest"
        entry["note"] = "已是最新或更新版本，跳过"
        return entry

    from_key_v = from_key(version)
    entry["version_from"] = from_key_v

    if from_key_v not in MIGRATIONS:
        entry["action"] = "skip-latest"
        entry["note"] = f"版本 {version} 不在迁移规则表中（可能已手动升级），跳过"
        return entry

    target = MIGRATIONS[from_key_v]["to"]

    # 需迁移（v0 无 version，或版本低于目标）
    entry["target"] = target
    entry["version_of"] = default_version_of(path, fields)
    if version is None and kind == "md" and not fields.get("has_fm"):
        entry["action"] = "add-frontmatter"
        entry["note"] = "无 frontmatter → 前置新 frontmatter 块（v0 → v1）"
    elif version is None:
        entry["action"] = "add-fields"
        entry["note"] = "v0 → v1（补 version + version_of）"
    else:
        entry["action"] = "add-fields"
        entry["note"] = f"{version} → {target}"
    return entry


# === 执行 ===

def apply_migration(entry: dict) -> dict:
    path = Path(entry["path"])
    kind = entry["kind"]
    migrator = _MIGRATORS.get(kind, {}).get(entry["version_from"])
    if migrator is None:
        entry["action"] = "error"
        entry["note"] = f"无 {kind} 类型 {entry['version_from']}→ 的迁移函数"
        return entry
    try:
        if kind == "md":
            raw = path.read_text(encoding="utf-8")
            data = parse_simple_yaml(split_frontmatter(raw)[0] or "")
        else:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
        path.write_text(migrator(path, raw, data), encoding="utf-8")
        entry["action"] = "migrated"
        return entry
    except Exception as e:
        entry["action"] = "error"
        entry["note"] = f"迁移失败: {e}"
        return entry


def main() -> int:
    parser = argparse.ArgumentParser(
        description="可迁移对象 schema 升级工具（v0→v1；MIGRATIONS 可扩展）")
    parser.add_argument("--root", type=str, default=None,
                        help="扫描根目录（默认：<仓库根>/personal）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只列出迁移计划，不写入（默认行为）")
    parser.add_argument("--execute", action="store_true",
                        help="实际执行迁移（写入文件）")
    parser.add_argument("--json", action="store_true",
                        help="JSON 输出（供 hook / 其他工具消费）")
    args = parser.parse_args()

    # 解析根目录
    if args.root:
        root = Path(args.root).resolve()
    else:
        # 本文件位于 <repo>/framework/engine/scripts/ → parents[3] = 仓库根
        root = Path(__file__).resolve().parents[3] / "personal"

    targets = scan_targets(root)
    entries = []
    for t in targets:
        fields = read_md_fields(t["path"]) if t["kind"] == "md" else read_capability_fields(t["path"])
        entries.append(classify(t["path"], t["kind"], fields))

    if not root.exists():
        print(f"[WARN] 扫描目录不存在: {root}", file=sys.stderr)

    migratable = [e for e in entries if e["action"] not in ("skip-latest", "error")]
    skipped = [e for e in entries if e["action"] == "skip-latest"]
    errors = [e for e in entries if e["action"] == "error"]

    # 执行迁移
    if args.execute:
        for e in migratable:
            apply_migration(e)

    # 输出
    if args.json:
        result = {
            "root": str(root),
            "schema_latest": LATEST_SCHEMA,
            "total": len(entries),
            "to_migrate": [e for e in migratable],
            "skipped_latest": skipped,
            "errors": errors,
            "migrated": [e for e in migratable if e["action"] == "migrated"],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if not errors else 1

    mode = "DRY-RUN（未写入）" if not args.execute else "已执行迁移"
    print(f"schema-migrate · 当前 schema 最新版 {LATEST_SCHEMA} · 扫描目录: {root}")
    print(f"模式: {mode}")
    if not entries:
        print("  未发现迁移对象（无 .md / capability.json）")
        return 0

    print(f"\n待迁移（{len(migratable)}）:")
    if migratable:
        for e in migratable:
            tag = "→ migrated" if e["action"] == "migrated" else "→ pending"
            print(f"  [{e['kind']:>10}] {e['path']}")
            print(f"      {e['note']}  version_of: {e.get('version_of')}  {tag}")
    else:
        print("  （无）")

    print(f"\n已最新跳过（{len(skipped)}）:")
    for e in skipped:
        print(f"  {e['path']}  version={e['version']}")

    if errors:
        print(f"\n❌ 错误（{len(errors)}）:")
        for e in errors:
            print(f"  {e['path']}: {e['note']}")

    if not args.execute:
        print("\n提示: 使用 --execute 实际执行迁移（dry-run 未改动任何文件）")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
