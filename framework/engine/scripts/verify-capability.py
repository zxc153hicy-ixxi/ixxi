#!/usr/bin/env python3
"""verify-capability.py — 能力可执行性验证（不变量 I2/I3/I4 + 盲区 P0-8）

parity 只证明「可达」（文件存在），本脚本补上「能用」（可执行性）。三个动作：

  1. tier 推导：capability.requires → 档位（full = 含 execute_script/filesystem_write；reader-only = 其余）
  2. supports 校验（I3）：capability.requires ⊆ agent.supports（每个 agent 独立声明子集，接受部分覆盖）
  3. dry-run 可执行性（I4）：SKILL.md 引用的脚本做 py_compile / bash -n 验证「声明 == 实际」

用法：
  python framework/engine/scripts/verify-capability.py                 # 档位分布 + supports 校验
  python framework/engine/scripts/verify-capability.py --write-tier    # 把 tier 写回各 capability.json
  python framework/engine/scripts/verify-capability.py --dry-run       # 追加脚本可执行性验证
"""
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent.parent  # framework/
SRC_MGMT = REPO / "core/skills"
SRC_EXT = REPO / "core/skills/_external"
SUPPORTS = REPO / "core/agents/supports.json"

# 档位推导：requires 含执行/写能力 → full；否则 reader-only
EXEC_CAPS = {"execute_script", "filesystem_write"}


def tier_of(requires: list[str]) -> str:
    return "full" if (set(requires) & EXEC_CAPS) else "reader-only"


def collect_capabilities() -> list[Path]:
    # 只从 SRC_MGMT 递归（SRC_EXT 是其子目录，避免重复计数）
    caps = []
    if SRC_MGMT.exists():
        caps = sorted(SRC_MGMT.rglob("capability.json"))
    return caps


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    args = set(sys.argv[1:])
    write_tier = "--write-tier" in args
    do_dry_run = "--dry-run" in args

    supports = load_json(SUPPORTS)
    agents = supports["agents"]
    caps = collect_capabilities()
    print(f"能力总数: {len(caps)}（含 tier 字段 {sum(1 for c in caps if 'tier' in load_json(c))}）")

    # 1. tier 推导 + 写回
    tier_stats = {}
    for cap in caps:
        data = load_json(cap)
        tier = tier_of(data.get("requires", []))
        tier_stats[tier] = tier_stats.get(tier, 0) + 1
        if write_tier and data.get("tier") != tier:
            data["tier"] = tier
            cap.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"档位分布（推导）: {tier_stats}")

    # 2. supports 校验（I3）
    print("\n=== supports 校验（I3：capability.requires ⊆ agent.supports）===")
    all_ok = True
    for agent_name, agent_info in agents.items():
        agent_supports = set(agent_info["supports"])
        missing = []
        for cap in caps:
            data = load_json(cap)
            requires = set(data.get("requires", []))
            if not requires.issubset(agent_supports):
                missing.append((data["id"], sorted(requires - agent_supports)))
        if missing:
            print(f"[{agent_name}] 无法执行 {len(missing)}/{len(caps)} 个能力（缺契约）:")
            for cid, miss in missing[:10]:
                print(f"  - {cid}: 缺 {miss}")
            if len(missing) > 10:
                print(f"  ... 其余 {len(missing) - 10} 个")
        else:
            print(f"[{agent_name}] 全部 {len(caps)} 个能力可执行 ✓")
        # 部分覆盖是「一等公民」（I3/I4），不算失败，仅如实报告

    # 3. dry-run 可执行性（I4）：capability.resources 声明的脚本 py_compile / bash -n
    # 注：resources 字段当前多为空（B 组 #13 补齐），空转时如实报告，非 bug。
    if do_dry_run:
        print("\n=== dry-run 可执行性（I4：capability.resources 脚本 py_compile / bash -n）===")
        ok = fail = skipped = 0
        for cap in caps:
            data = load_json(cap)
            for res in data.get("resources", []):
                p = REPO / res
                if not p.exists():
                    fail += 1
                    print(f"  ❌ {data['id']}: {res} 不存在")
                    continue
                if p.suffix == ".py":
                    try:
                        subprocess.run([sys.executable, "-m", "py_compile", str(p)],
                                       capture_output=True, check=True)
                        ok += 1
                    except Exception as e:
                        fail += 1
                        print(f"  ❌ {data['id']}: {res} 编译失败（{e}）")
                elif p.suffix == ".sh":
                    try:
                        subprocess.run(["bash", "-n", str(p)], capture_output=True, check=True)
                        ok += 1
                    except Exception as e:
                        fail += 1
                        print(f"  ❌ {data['id']}: {res} 语法错误（{e}）")
                else:
                    skipped += 1  # .md 等无「可执行」概念，跳过
        print(f"  dry-run: {ok} 通过 / {fail} 失败 / {skipped} 跳过（非脚本）")
        if fail:
            return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"IXXI-E203 | 能力可执行性验证执行失败", file=sys.stderr)
        print(f"修复：检查 core/skills 与 core/agents/supports.json 是否完整；原始错误：{e}", file=sys.stderr)
        print("参考：engine/scripts/verify-capability.py", file=sys.stderr)
        sys.exit(1)
