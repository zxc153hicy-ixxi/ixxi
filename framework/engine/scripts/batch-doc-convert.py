#!/usr/bin/env python3
"""batch-doc-convert.py -- 批量转换旧 .doc 文件 → .md（通过 antiword）

用法:
  python engine/scripts/batch-doc-convert.py --dry-run    # 预览
  python engine/scripts/batch-doc-convert.py               # 执行
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ANTIWORD = "D:/git/Git/mingw64/bin/antiword.exe"

SKIP_FILES = {"Thumbs.db", ".DS_Store", "desktop.ini", ".gitkeep", ".placeholder"}


def find_doc_files(root: Path) -> list[Path]:
    """递归查找 .doc 文件（排除 .docx）"""
    files = []
    for entry in sorted(root.rglob("*.doc")):
        if entry.name in SKIP_FILES:
            continue
        if entry.is_file() and entry.suffix.lower() == ".doc":
            files.append(entry)
    return files


def convert_doc(doc_path: Path, md_path: Path) -> tuple[bool, str]:
    """用 antiword 转换 .doc → 纯文本，包装为 .md"""
    try:
        result = subprocess.run(
            [ANTIWORD, "-m", "UTF-8.txt", str(doc_path)],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace",
        )
        if result.returncode != 0:
            return False, f"antiword 错误: {result.stderr.strip() or '返回码 ' + str(result.returncode)}"

        text = result.stdout.strip()
        if not text:
            return False, "antiword 输出为空（可能是加密或损坏的 .doc）"

        # 原子写入：先写 .tmp，再 replace（跨平台原子替换已存在的目标）
        tmp_path = md_path.with_suffix(".tmp")
        md_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.write_text(text, encoding="utf-8")
        tmp_path.replace(md_path)
        size_kb = len(text) / 1024
        return True, f"OK ({size_kb:.1f}KB)"
    except subprocess.TimeoutExpired:
        return False, "antiword 超时"
    except FileNotFoundError:
        return False, f"antiword 未找到: {ANTIWORD}"
    except Exception as e:
        if 'tmp_path' in locals() and tmp_path.exists():
            tmp_path.unlink()
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="批量转换旧 .doc → .md")
    parser.add_argument("source", help="源目录（递归扫描 .doc）")
    parser.add_argument("target", help="目标目录（输出 .md）")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    src = Path(args.source).resolve()
    tgt = Path(args.target).resolve()

    if not src.exists():
        print(f"[错误] 源目录不存在: {src}")
        sys.exit(1)

    # 检查 antiword
    if not Path(ANTIWORD).exists():
        print(f"[错误] antiword 未找到: {ANTIWORD}")
        print("  安装: winget install antiword 或通过 Git for Windows")
        sys.exit(1)

    files = find_doc_files(src)
    print(f"扫描完成: {len(files)} 个 .doc 文件")
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

    ok = 0
    fail = 0
    skipped = 0
    failed_files = []

    for i, f in enumerate(files, 1):
        rel = f.relative_to(src)
        out_name = f"{f.stem}.md"
        out_path = tgt / rel.parent / out_name

        # 去重：已存在且非空则跳过
        if out_path.exists() and out_path.stat().st_size > 0:
            skipped += 1
            continue

        print(f"[{i}/{len(files)}] {rel} ...", end=" ", flush=True)
        success, msg = convert_doc(f, out_path)
        print(msg)

        if success:
            ok += 1
        else:
            fail += 1
            failed_files.append((str(rel), msg))

    print(f"\n--- 批量转换完成 ---")
    print(f"  总计: {len(files)}")
    print(f"  成功: {ok}")
    print(f"  失败: {fail}")
    print(f"  跳过: {skipped}")

    if failed_files:
        print(f"\n失败文件:")
        for name, reason in failed_files[:10]:
            print(f"  - {name}: {reason}")
        if len(failed_files) > 10:
            print(f"  ... 共 {len(failed_files)} 个")


if __name__ == "__main__":
    main()
