#!/usr/bin/env python3
"""batch-ocr.py -- 对 0KB 的 .md 文件，回溯源 PDF 并用 marker OCR 重新转换

用法:
  python engine/scripts/batch-ocr.py --dry-run    # 预览配对
  python engine/scripts/batch-ocr.py               # 执行转换（跳过已有内容的文件）
  python engine/scripts/batch-ocr.py --limit 5     # 只转前 5 个
  python engine/scripts/batch-ocr.py --force       # 强制重转（忽略 journal）
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# GBK 终端兜底
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKIP_FILES = {"Thumbs.db", ".DS_Store", "desktop.ini", ".gitkeep", ".placeholder"}
CONFIG_PATH = Path(__file__).resolve().parent / "ocr-sources.json"
BAR_WIDTH = 22


# ---------------------------------------------------------------------------
# 配置加载
# ---------------------------------------------------------------------------

def load_mappings() -> list[dict]:
    """从 ocr-sources.json 加载目标→源映射。"""
    if not CONFIG_PATH.exists():
        sys.exit(f"配置文件不存在: {CONFIG_PATH}")
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"配置文件 JSON 解析失败: {CONFIG_PATH}\n{e}")
    mappings = data.get("mappings", [])
    if not mappings:
        sys.exit(f"配置文件中无 mappings 条目: {CONFIG_PATH}")
    return mappings


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _fmt_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        m, s = divmod(int(seconds), 60)
        return f"{m}分{s:.0f}s"
    else:
        h, rem = divmod(int(seconds), 3600)
        m, s = divmod(rem, 60)
        return f"{h}时{m}分"


def _progress_bar(current: int, total: int, width: int = BAR_WIDTH) -> str:
    filled = int(width * current / total) if total else 0
    bar = "#" * filled + "-" * (width - filled)
    pct = current / total * 100 if total else 0
    return f"[{bar}] {current}/{total} ({pct:.1f}%)"


def _wait_any_key():
    """Windows: 等待任意按键"""
    import msvcrt
    while msvcrt.kbhit():
        msvcrt.getch()
    msvcrt.getch()


def _check_pause() -> bool:
    """检查是否有暂停键按下（p 键）。返回 True 表示需要暂停"""
    try:
        import msvcrt
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key.lower() == b'p':
                while msvcrt.kbhit():
                    msvcrt.getch()
                return True
            while msvcrt.kbhit():
                msvcrt.getch()
    except ImportError:
        pass
    return False


# ---------------------------------------------------------------------------
# journal
# ---------------------------------------------------------------------------

def _journal_path(target: Path) -> Path:
    return target / ".ocr-journal.json"


def load_journal(target: Path) -> dict:
    jp = _journal_path(target)
    if not jp.exists():
        return {}
    try:
        return json.loads(jp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_journal(target: Path, journal: dict) -> None:
    tmp = _journal_path(target).with_suffix(".tmp")
    tmp.write_text(json.dumps(journal, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(_journal_path(target))


# ---------------------------------------------------------------------------
# core
# ---------------------------------------------------------------------------

def build_pdf_index(source_dirs: list[Path]) -> tuple[dict[str, list[Path]], dict[str, list[Path]]]:
    """扫描多个源目录建索引。

    Returns:
        index: {stem: [Path, ...]} — 每个 stem 对应所有匹配 PDF
        conflicts: {stem: [Path, ...]} — 仅包含同名冲突的 stem
    """
    index: dict[str, list[Path]] = {}
    for src in source_dirs:
        if not src.exists():
            continue
        for pdf in sorted(src.rglob("*.pdf")):
            if pdf.name in SKIP_FILES:
                continue
            index.setdefault(pdf.stem, []).append(pdf)
    conflicts = {k: v for k, v in index.items() if len(v) > 1}
    return index, conflicts


def find_zero_md_files(target: Path) -> list[Path]:
    zero = []
    for md in sorted(target.rglob("*.md")):
        if md.name in SKIP_FILES:
            continue
        try:
            if md.stat().st_size == 0:
                zero.append(md)
        except OSError:
            continue
    return zero


# ---------------------------------------------------------------------------
# OCR 转换（marker）
# ---------------------------------------------------------------------------

_converter = None  # 模块级缓存，避免重复加载模型


def _get_converter():
    """惰性加载 marker 模型（仅首次调用时加载）"""
    global _converter
    if _converter is not None:
        return _converter

    from marker.models import create_model_dict
    from marker.config.parser import ConfigParser

    print("加载 OCR 模型（marker-pdf + surya-ocr）...")
    t0 = time.time()
    models = create_model_dict()
    config_parser = ConfigParser({"output_format": "markdown"})
    _converter = config_parser.get_converter_cls()(
        config=config_parser.generate_config_dict(),
        artifact_dict=models,
        processor_list=config_parser.get_processors(),
        renderer=config_parser.get_renderer(),
        llm_service=config_parser.get_llm_service(),
    )
    print(f"模型就绪（{time.time() - t0:.0f}s）")
    return _converter


def _convert_one(pdf_path: Path, md_path: Path) -> tuple[bool, str]:
    """转换单个 PDF → .md（marker OCR），原子写入"""
    from marker.output import text_from_rendered

    converter = _get_converter()

    try:
        rendered = converter(str(pdf_path))
        text, _, _ = text_from_rendered(rendered)
    except Exception as e:
        return False, str(e)

    if not text.strip():
        return False, "OCR 输出为空"

    tmp_path = md_path.with_suffix(".tmp")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(md_path)

    return True, ""


# ---------------------------------------------------------------------------
# 输出
# ---------------------------------------------------------------------------

def _print_auto_selected(selected: list[tuple[str, Path, list[Path]]]):
    """打印同名 PDF 自动选择结果"""
    print(f"\n📋 同名 PDF 自动选择（{len(selected)} 个 stem，均取最大文件）:")
    for stem, chosen, candidates in sorted(selected):
        print(f"  [{stem}]")
        for p in sorted(candidates, key=lambda x: x.stat().st_size if x.exists() else 0, reverse=True):
            size_kb = p.stat().st_size / 1024 if p.exists() else 0
            marker = " ← 已选用" if p == chosen else ""
            print(f"    {size_kb:.0f}KB  {p}{marker}")
    print("\n如需改用其他版本：删除较大文件后重跑，或手动指定源 PDF。")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="marker OCR 批量转换 0KB .md → 回源 PDF OCR"
    )
    parser.add_argument("--dry-run", action="store_true", help="预览配对，不转换")
    parser.add_argument("--limit", type=int, default=0, help="最多转换 N 个")
    parser.add_argument("--force", action="store_true", help="强制重转（忽略 journal）")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent

    # 从 JSON 配置加载映射
    mappings = load_mappings()
    run_pairs = []
    for m in mappings:
        tgt_sub = m["target"]
        src_dirs = m["sources"]
        tgt_full = repo_root / "knowledge" / "learning" / tgt_sub
        src_paths = [Path(d) for d in src_dirs]
        run_pairs.append((src_paths, tgt_full))

    # 阶段 1: 扫描 + 配对
    all_tasks: list[tuple[Path, Path]] = []
    auto_selected: list[tuple[str, Path, list[Path]]] = []
    global_skipped_by_journal = 0

    for src_dirs, tgt in run_pairs:
        print(f"\n{'='*60}")
        print(f"源: {', '.join(str(d) for d in src_dirs)}")
        print(f"目标: {tgt}")

        pdf_index, conflicts = build_pdf_index(src_dirs)
        print(f"PDF 索引: {len(pdf_index)} 个唯一 stem")
        if conflicts:
            # 自动选最大文件
            for stem, paths in conflicts.items():
                chosen = max(paths, key=lambda p: p.stat().st_size if p.exists() else 0)
                auto_selected.append((stem, chosen, paths))
                pdf_index[stem] = [chosen]

        zero_files = find_zero_md_files(tgt)
        print(f"0KB .md: {len(zero_files)} 个")

        for md in zero_files:
            pdf_list = pdf_index.get(md.stem)
            if pdf_list:
                all_tasks.append((pdf_list[0], md))

    if not all_tasks:
        print("\n没有可转换的配对")
        if auto_selected:
            _print_auto_selected(auto_selected)
        return

    if args.limit > 0:
        all_tasks = all_tasks[:args.limit]

    if args.dry_run:
        print(f"\n[Dry Run] 将转换 {len(all_tasks)} 对:")
        for pdf, md in all_tasks:
            print(f"  {pdf.name}  →  {md.relative_to(repo_root)}")
        if auto_selected:
            _print_auto_selected(auto_selected)
        return

    # 阶段 2: 过滤已转换 + 清理残留
    primary_target = run_pairs[0][1]
    journal = {} if args.force else load_journal(primary_target)

    pending = []
    for pdf, md in all_tasks:
        key = str(md)
        if key in journal and journal[key].get("status") == "ok":
            global_skipped_by_journal += 1
        elif md.stat().st_size > 0:
            global_skipped_by_journal += 1
        else:
            pending.append((pdf, md))

    if global_skipped_by_journal:
        print(f"跳过 {global_skipped_by_journal} 个（已转换）")

    # 清理 .tmp
    for _, tgt in run_pairs:
        cleaned = 0
        for tmp in tgt.rglob("*.tmp"):
            tmp.unlink()
            cleaned += 1
        if cleaned:
            print(f"清理 {cleaned} 个残留 .tmp ({tgt})")

    if not pending:
        print("全部完成。")
        if auto_selected:
            _print_auto_selected(auto_selected)
        return

    total = len(pending)
    print(f"\n待转换: {total} 个文件")
    print(_progress_bar(0, total))

    # 阶段 3: 逐文件转换
    ok = 0
    fail = 0
    failed_items: list[tuple[str, str]] = []
    total_start = time.time()
    total_pause_time = 0.0
    file_times: list[float] = []

    for idx, (src_pdf, tgt_md) in enumerate(pending):
        # ---- 暂停检查 ----
        paused_this_turn = False
        while _check_pause():
            if not paused_this_turn:
                paused_this_turn = True
                pause_start = time.time()
                active_time = time.time() - total_start - total_pause_time
                print(f"\n⏸ 暂停中 | 已完成 {ok}/{total} | "
                      f"失败 {fail} | 活跃耗时 {_fmt_time(active_time)}")
                print("  按任意键继续 (再次按 p 保持暂停)...")
            _wait_any_key()
        if paused_this_turn:
            total_pause_time += time.time() - pause_start
            print("▶ 继续\n")

        # ---- 转换 ----
        rel = str(tgt_md.relative_to(primary_target)
                  if primary_target in tgt_md.parents
                  else tgt_md)
        print(f"\n[{idx+1}/{total}] {rel}")
        print(f"  源: {src_pdf}")

        file_start = time.time()
        try:
            success, msg = _convert_one(src_pdf, tgt_md)
        except KeyboardInterrupt:
            print(f"\n中断信号 → 保存 journal ...")
            save_journal(primary_target, journal)
            print("已保存进度，可安全重跑。")
            sys.exit(130)
        except Exception as exc:
            success, msg = False, str(exc)

        file_elapsed = time.time() - file_start

        if success:
            file_times.append(file_elapsed)
            file_kb = tgt_md.stat().st_size / 1024
            ok += 1
            journal[str(tgt_md)] = {
                "status": "ok",
                "elapsed": round(file_elapsed, 1),
                "size_kb": round(file_kb, 1),
            }
            save_journal(primary_target, journal)

            active_time = time.time() - total_start - total_pause_time
            avg_time = sum(file_times) / len(file_times)
            remaining = total - ok - fail
            eta_sec = avg_time * remaining

            print(f"  OK ({_fmt_time(file_elapsed)}, {file_kb:.1f}KB) | "
                  f"累计 {_fmt_time(active_time)} | "
                  f"均速 {_fmt_time(avg_time)} | "
                  f"ETA {_fmt_time(eta_sec)}")
            print(_progress_bar(ok + fail, total))
        else:
            fail += 1
            failed_items.append((rel, msg))
            journal[str(tgt_md)] = {
                "status": "fail",
                "elapsed": round(file_elapsed, 1),
                "error": msg[:300],
            }
            save_journal(primary_target, journal)

            active_time = time.time() - total_start - total_pause_time
            print(f"  FAIL ({_fmt_time(file_elapsed)}): {msg}")
            print(f"  累计 {_fmt_time(active_time)}")
            print(_progress_bar(ok + fail, total))

    # 阶段 4: 收尾
    active_time = time.time() - total_start - total_pause_time

    print(f"\n{'='*60}")
    print(f"  成功: {ok}")
    print(f"  失败: {fail}")
    if total_pause_time > 0:
        print(f"  活跃耗时: {_fmt_time(active_time)}")
        print(f"  暂停耗时: {_fmt_time(total_pause_time)}")
    print(f"  总耗时: {_fmt_time(time.time() - total_start)}")

    if failed_items:
        print(f"\n失败文件 ({len(failed_items)}):")
        for rel, err in failed_items:
            print(f"  - {rel}")
            print(f"    {err}")

    if auto_selected:
        _print_auto_selected(auto_selected)

    # 统计剩余
    remaining = 0
    for _, tgt in run_pairs:
        remaining += sum(
            1 for md in tgt.rglob("*.md")
            if md.name not in SKIP_FILES and md.stat().st_size == 0
        )
    if remaining:
        print(f"\n剩余 0KB 文件: {remaining}")


if __name__ == "__main__":
    main()
