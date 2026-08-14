#!/usr/bin/env python3
"""batch-convert.py -- 递归批量转换 .docx/.pdf/.epub → .md，直接输出到目标目录

用法:
  python engine/scripts/batch-convert.py <源目录> <目标目录>
  python engine/scripts/batch-convert.py <源目录> <目标目录> --dry-run
  python engine/scripts/batch-convert.py <源目录> <目标目录> --exts .docx,.pdf,.epub
"""

import argparse
import os
import sys
import time
from pathlib import Path

from markitdown import MarkItDown

_md = MarkItDown()

SKIP_FILES = {"Thumbs.db", ".DS_Store", "desktop.ini", ".gitkeep", ".placeholder"}
DEFAULT_EXTS = {".docx", ".pdf", ".epub", ".doc", ".pptx", ".ppt"}
CONVERSION_TIMEOUT = 600  # 秒


def find_files(root: Path, exts: set[str]) -> list[Path]:
    """递归查找可转换文件"""
    files = []
    for entry in sorted(root.rglob("*")):
        if entry.name in SKIP_FILES:
            continue
        if entry.is_file() and entry.suffix.lower() in exts:
            files.append(entry)
    return files


def convert_file(input_path: Path, output_path: Path) -> tuple[bool, str]:
    """转换单个文件，返回 (成功, 消息)，原子写入防中断残留"""
    start = time.time()
    tmp_path = output_path.with_suffix(".tmp")
    try:
        result = _md.convert(str(input_path))
        text = result.text_content
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.write_text(text, encoding="utf-8")
        tmp_path.replace(output_path)  # 跨平台原子替换
        elapsed = time.time() - start
        size_kb = len(text) / 1024
        return True, f"OK ({elapsed:.1f}s, {size_kb:.1f}KB)"
    except Exception as e:
        if tmp_path.exists():
            tmp_path.unlink()
        elapsed = time.time() - start
        return False, f"FAIL ({elapsed:.1f}s): {e}"


def main():
    parser = argparse.ArgumentParser(description="递归批量转换文档为 Markdown")
    parser.add_argument("source", help="源目录路径")
    parser.add_argument("target", help="目标目录路径")
    parser.add_argument("--dry-run", action="store_true", help="只扫描不转换")
    parser.add_argument("--exts", default=".docx,.pdf,.epub,.doc,.pptx",
                        help="逗号分隔的扩展名列表")
    parser.add_argument("--flat", action="store_true",
                        help="平铺输出（不保留子目录结构）")
    args = parser.parse_args()

    src = Path(args.source).resolve()
    tgt = Path(args.target).resolve()

    if not src.exists():
        print(f"[错误] 源目录不存在: {src}")
        sys.exit(1)

    exts = set(e.strip().lower() for e in args.exts.split(","))
    if not exts:
        print("[错误] 未指定扩展名")
        sys.exit(1)

    files = find_files(src, exts)
    print(f"扫描完成: {len(files)} 个文件 ({', '.join(sorted(exts))})")
    print(f"源目录: {src}")
    print(f"目标目录: {tgt}")

    if args.dry_run:
        print("\n[Dry Run] 文件列表:")
        for f in files:
            rel = f.relative_to(src)
            out_name = f"{f.stem}.md"
            print(f"  {rel}  →  {out_name}")
        return

    tgt.mkdir(parents=True, exist_ok=True)

    success = 0
    failed = 0
    skipped = 0
    failed_files = []

    for i, f in enumerate(files, 1):
        rel = f.relative_to(src)
        out_name = f"{f.stem}.md"

        if args.flat:
            out_path = tgt / out_name
        else:
            out_path = tgt / rel.parent / out_name

        # 去重：非空文件跳过，0KB 文件重新转换
        if out_path.exists() and out_path.stat().st_size > 0:
            print(f"[{i}/{len(files)}] SKIP (已存在): {rel}")
            skipped += 1
            continue

        print(f"[{i}/{len(files)}] {f.suffix} {rel} ...", end=" ", flush=True)
        ok, msg = convert_file(f, out_path)
        print(msg)

        if ok:
            success += 1
        else:
            failed += 1
            failed_files.append((str(rel), msg))

    print(f"\n--- 批量转换完成 ---")
    print(f"  总计: {len(files)}")
    print(f"  成功: {success}")
    print(f"  失败: {failed}")
    print(f"  跳过: {skipped}")

    if failed_files:
        print(f"\n失败文件:")
        for name, reason in failed_files:
            print(f"  - {name}: {reason}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
