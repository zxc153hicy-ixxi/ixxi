#!/usr/bin/env python3
"""record-usage.py — 记录 capability 使用（telemetry 采集，不变量 I8）

遥测是演化决策信号（usage ≠ value），本脚本只负责采集，不做价值判断。

用法：
  python framework/engine/scripts/record-usage.py <skill-name>      # 记录一次使用（count++，last_seen=今天）
  python framework/engine/scripts/record-usage.py --list            # 列出当前遥测
  python framework/engine/scripts/record-usage.py <skill-name> --reset  # 重置该 skill

遥测文件：personal/raw/sessions/skill-usage.json 优先（实例层），
          否则 raw/sessions/skill-usage.json。
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

FRAMEWORK = Path(__file__).resolve().parent.parent.parent  # framework/
REPO_ROOT = FRAMEWORK.parent  # 仓库根


def telemetry_path() -> Path:
    """遥测文件位置：personal 实例层优先，其次仓库根 raw/。"""
    personal = REPO_ROOT / "personal" / "raw" / "sessions" / "skill-usage.json"
    root = REPO_ROOT / "raw" / "sessions" / "skill-usage.json"
    if personal.exists():
        return personal
    if root.exists():
        return root
    # 都不存在 → 默认写入 personal 实例层（遥测属于个人数据，不进 framework）
    return personal


def load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("顶层结构不是对象")
        return data
    except FileNotFoundError:
        return {"_meta": {"created": date.today().isoformat(), "note": "遥测是演化决策信号（usage ≠ value）"}}
    except Exception as e:
        print(f"IXXI-E010 | 遥测数据损坏：{path} 无法读取/解析", file=sys.stderr)
        print(f"修复：检查 {path} 是否为合法 JSON 对象；原始错误：{e}", file=sys.stderr)
        print("参考：engine/scripts/record-usage.py", file=sys.stderr)
        sys.exit(1)


def record(name: str) -> None:
    path = telemetry_path()
    data = load(path)
    today = date.today().isoformat()
    rec = data.get(name, {})
    if not isinstance(rec, dict):
        rec = {}
    rec["count"] = int(rec.get("count", 0)) + 1
    rec["last_seen"] = today
    rec.setdefault("first_seen", today)
    data[name] = rec
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✓ 已记录 {name} 使用（count={rec['count']}，last_seen={today}）")
    print(f"📝 遥测文件：{path}")


def list_usage() -> None:
    path = telemetry_path()
    data = load(path)
    entries = {k: v for k, v in data.items() if k != "_meta" and isinstance(v, dict)}
    if not entries:
        print("暂无遥测数据。使用 skill 后由 kb-curator 调用 record-usage.py 记录。")
        return
    print(f"=== 遥测（{len(entries)} 个 capability）===")
    for name in sorted(entries):
        rec = entries[name]
        print(f"  {name}: count={rec.get('count', 0)} last_seen={rec.get('last_seen', '?')}")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("用法: record-usage.py <skill-name> | --list")
        return 1
    if args[0] == "--list":
        list_usage()
        return 0
    name = args[0]
    if "--reset" in args:
        path = telemetry_path()
        data = load(path)
        data.pop(name, None)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"✓ 已重置 {name}")
        return 0
    record(name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
