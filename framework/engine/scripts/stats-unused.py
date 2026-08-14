# -*- coding: utf-8 -*-
"""stats-unused.py — `ixxi stats --unused`：输出 N 天未触发的 capability 清单

未触发报告 v1 最小化交付（不可延后 v2——否则演化闭环空转）。

数据源（优先级从高到低）：
  1. 遥测文件 raw/sessions/skill-usage.json（实例层，skill → {count, first_seen, last_seen, ...}）
  2. core/skills/<技能>/capability.json 的 last_used / triggered 字段（未建立遥测时的兜底）

无遥测数据时不崩溃：输出「暂无遥测数据，使用后由 kb-curator 记录触发」后正常退出（退出码 0）。

判据：遥测是演化决策信号（usage ≠ value），建议（保留 / 归档候选）仅作参考，最终由人工裁决。

用法：
  python framework/engine/scripts/stats-unused.py            # 默认阈值 30 天
  python framework/engine/scripts/stats-unused.py --days 60  # 自定义阈值
"""
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

FRAMEWORK = Path(__file__).resolve().parent.parent.parent  # framework/
REPO_ROOT = FRAMEWORK.parent  # 仓库根（含 personal/ 实例层）
ARCHIVE_DAYS = 90  # 设计阈值：五阶段生命周期 + 90 天归档


def find_telemetry() -> Path | None:
    """定位遥测文件 raw/sessions/skill-usage.json（实例层可能在仓库根或 personal/ 下）。"""
    candidates = [
        REPO_ROOT / "raw" / "sessions" / "skill-usage.json",
        REPO_ROOT / "personal" / "raw" / "sessions" / "skill-usage.json",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def parse_date(value) -> date | None:
    """解析日期字符串，支持 YYYY-MM-DD 与 ISO 时间戳；失败返回 None。"""
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError:
            return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        return None


def load_telemetry(path: Path) -> dict | None:
    """读取 skill-usage.json → {skill名: {"last_seen": date|None, "days_since": int|None}}。解析失败返回 None。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠️ 遥测文件解析失败: {path}（{e}）")
        return None
    entries = {}
    today = date.today()
    for name, rec in data.items():
        if name == "_meta" or not isinstance(rec, dict):
            continue
        last = parse_date(rec.get("last_seen"))
        entries[name] = {"last_seen": last, "days_since": (today - last).days if last else None}
    return entries


def scan_capability_files() -> dict:
    """兜底：从 core/skills/<技能>/capability.json 收集 last_used/triggered 信号。

    仅统计声明了 last_used / triggered 字段的 capability（无遥测信号者不纳入判定）。
    triggered: true（有触发但无日期）→ 跳过；triggered: false 或日期值 → 纳入。
    """
    entries = {}
    src = FRAMEWORK / "core" / "skills"
    if not src.is_dir():
        return entries
    today = date.today()
    for d in sorted(src.iterdir()):
        if not d.is_dir():
            continue
        cap = d / "capability.json"
        if not cap.is_file():
            continue
        try:
            data = json.loads(cap.read_text(encoding="utf-8"))
        except Exception:
            continue
        name = data.get("id") or d.name
        if "last_used" in data:
            last = parse_date(data.get("last_used"))
        elif "triggered" in data:
            t = data.get("triggered")
            if isinstance(t, bool):
                if t:  # 有触发但无日期，无法判定未触发
                    continue
                last = None
            else:
                last = parse_date(t)
        else:
            continue  # 无遥测信号，不纳入判定
        entries[name] = {"last_seen": last, "days_since": (today - last).days if last else None}
    return entries


def disp_w(s: str) -> int:
    """粗略显示宽度：东亚字符计 2 列。"""
    return sum(2 if ord(c) > 0x2E7F else 1 for c in s)


def pad_right(s: str, width: int) -> str:
    return s + " " * max(0, width - disp_w(s))


def main() -> int:
    # 参数解析：--days N（默认 30，非法/<=0 回退 30）
    args = sys.argv[1:]
    days = 30
    i = 0
    while i < len(args):
        if args[i] == "--days" and i + 1 < len(args):
            try:
                days = int(args[i + 1])
            except ValueError:
                days = 30
            i += 2
        else:
            i += 1
    if days < 1:
        days = 30

    # 数据源：遥测文件优先，capability.json 兜底
    entries, source = None, None
    tele = find_telemetry()
    if tele is not None:
        entries = load_telemetry(tele)
        if entries is not None:
            source = tele
    if entries is None:
        entries = scan_capability_files()
        if entries:
            source = "core/skills/**/capability.json（last_used/triggered）"

    if not entries:
        print("暂无遥测数据，使用后由 kb-curator 记录触发。")
        return 0

    # 筛选 N 天未触发（含从未触发）
    unused = []
    for name, rec in sorted(entries.items()):
        ds = rec["days_since"]
        if ds is None or ds >= days:
            unused.append((name, rec["last_seen"], ds))

    print(f"=== ixxi stats --unused（{days} 天未触发）===")
    print(f"数据源: {source}")
    if not unused:
        print(f"\n在 {days} 天内无未触发的 capability（共检查 {len(entries)} 个）。")
        return 0

    w_name = max(disp_w(n) for n, _, _ in unused)
    print(f"\n以下 {len(unused)} 个 capability 在 {days} 天内未触发：")
    for name, last, ds in unused:
        if last is None:
            time_txt, sugg = "从未触发", "归档候选"
        elif ds >= ARCHIVE_DAYS:
            time_txt, sugg = f"最后触发 {last.isoformat()}（距今 {ds} 天）", "归档候选"
        else:
            time_txt, sugg = f"最后触发 {last.isoformat()}（距今 {ds} 天）", "保留"
        print(f"  {pad_right(name, w_name)}  {time_txt}  → 建议：{sugg}")
    print(f"\n汇总: {len(unused)}/{len(entries)} 个 capability 在 {days} 天内未触发。")
    print("说明: 遥测是演化决策信号（usage ≠ value），最终保留/归档由人工裁决。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
