#!/usr/bin/env python3
"""auto-import.py -- 资料一键导入：压缩包解压 → 预扫描 → 转换 → 归档

用法:
  python engine/scripts/auto-import.py <文件>              # 单文件导入
  python engine/scripts/auto-import.py --batch <目录>       # 批量导入
  python engine/scripts/auto-import.py --json <文件>        # JSON 输出（供 LLM 解析）
  python engine/scripts/auto-import.py --dry-run <文件>     # 预演（只扫描不转换）
  python engine/scripts/auto-import.py --dry-run --json <文件>
"""

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# MarkItDown Python API（CLI 不可用时自动降级）
try:
    from markitdown import MarkItDown as _MarkItDown
    _MARKITDOWN_API = _MarkItDown()
    _MARKITDOWN_API_AVAILABLE = True
except ImportError:
    _MARKITDOWN_API = None
    _MARKITDOWN_API_AVAILABLE = False

# 检查 CLI 工具可用性
_MARKITDOWN_CLI = shutil.which("markitdown")

# ============================================================================
# 常量
# ============================================================================

# 7z 路径：环境变量 SEVEN_ZIP 优先 → PATH 自动探测 → 命令名 fallback（消除硬编码）
SEVEN_ZIP = os.environ.get("SEVEN_ZIP") or shutil.which("7z") or shutil.which("7z.exe") or "7z"
MAX_RECURSION_DEPTH = 3
CONVERSION_TIMEOUT = 600  # 秒
MAX_STEM_LENGTH = 100

ARCHIVE_EXTENSIONS = {
    ".zip", ".7z", ".rar", ".tar", ".gz", ".bz2",
    ".tar.gz", ".tar.bz2", ".tar.xz", ".tgz", ".tbz2", ".txz",
    ".iso", ".cab", ".wim",
}

# 视频格式——由 video2text.py 处理，auto-import 仅检测+标注，不自动转换
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".ts"}

# Magic bytes: (offset, bytes) -> format name
MAGIC_BYTES = [
    (0, b"PK\x03\x04", "ZIP"),
    (0, b"Rar!\x1a\x07", "RAR"),
    (0, b"7z\xbc\xaf'\x1c", "7Z"),
    (0, b"\x1f\x8b", "GZ"),
    (0, b"BZh", "BZ2"),
    (257, b"ustar", "TAR"),
]

SKIP_FILES = {"Thumbs.db", ".DS_Store", "desktop.ini", ".gitkeep", ".placeholder"}


# ============================================================================
# 工具函数
# ============================================================================

def get_repo_root() -> Path:
    """从脚本位置推断仓库根目录"""
    return Path(__file__).resolve().parent.parent.parent


def get_inbox_dirs(repo_root: Path) -> dict[str, Path]:
    """获取 .inbox/ 子目录路径，不存在则创建"""
    inbox = repo_root / ".inbox"
    dirs = {
        "sources": inbox / "sources",
        "converted": inbox / "converted",
        "extracted": inbox / "_extracted",
        "processed": inbox / "_processed",
        "failed": inbox / "_failed",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def deduplicate_name(dest_dir: Path, name: str) -> str:
    """文件名去重：存在则追加 _1, _2 ..."""
    stem, ext = os.path.splitext(name)
    candidate = name
    counter = 1
    while (dest_dir / candidate).exists():
        candidate = f"{stem}_{counter}{ext}"
        counter += 1
    return candidate


def safe_stem(filepath: Path) -> str:
    """截断过长文件名（Windows MAX_PATH 防护）"""
    stem = filepath.stem
    if len(stem) > MAX_STEM_LENGTH:
        return stem[:MAX_STEM_LENGTH]
    return stem


def is_safe_path(base_dir: Path, member_path: str) -> bool:
    """检测路径穿越攻击"""
    resolved = (base_dir / member_path).resolve()
    return resolved.is_relative_to(base_dir.resolve())


def format_size(size_bytes: int) -> str:
    """人类可读的文件大小"""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ============================================================================
# 压缩包检测与解压
# ============================================================================

def is_archive(filepath: Path, RULES: Optional[dict] = None) -> bool:
    """判断文件是否为压缩包（扩展名 + magic bytes 双重检测）

    注意：.docx/.pptx/.xlsx 等 Office 格式本质是 ZIP，但其扩展名已在
    prescan RULES 中，不会被误判为压缩包。
    """
    # 扩展名检测（处理 .tar.gz 等双后缀）
    name_lower = filepath.name.lower()
    for ext in ARCHIVE_EXTENSIONS:
        if name_lower.endswith(ext):
            return True
    # 如果扩展名已在可转换规则中，不进行 magic bytes 检测
    # （防止 .docx/.pptx/.xlsx 等 ZIP-based Office 格式被误判）
    if RULES is not None and filepath.suffix.lower() in RULES:
        return False
    # Magic bytes 兜底（无扩展名或未知扩展名）
    try:
        with open(filepath, "rb") as f:
            header = f.read(512)
        for offset, magic, _fmt in MAGIC_BYTES:
            if header[offset:offset + len(magic)] == magic:
                return True
    except (IOError, OSError):
        pass
    return False


def detect_archive_type(filepath: Path) -> str:
    """返回压缩包格式名（用于报告）"""
    name_lower = filepath.name.lower()
    ext_map = [
        (".tar.gz", "TAR.GZ"), (".tar.bz2", "TAR.BZ2"), (".tar.xz", "TAR.XZ"),
        (".tgz", "TAR.GZ"), (".tbz2", "TAR.BZ2"), (".txz", "TAR.XZ"),
        (".zip", "ZIP"), (".7z", "7Z"), (".rar", "RAR"), (".tar", "TAR"),
        (".gz", "GZ"), (".bz2", "BZ2"), (".iso", "ISO"),
        (".cab", "CAB"), (".wim", "WIM"),
    ]
    for ext, fmt in ext_map:
        if name_lower.endswith(ext):
            return fmt
    # Magic bytes fallback
    try:
        with open(filepath, "rb") as f:
            header = f.read(512)
        for offset, magic, fmt in MAGIC_BYTES:
            if header[offset:offset + len(magic)] == magic:
                return fmt
    except (IOError, OSError):
        pass
    return "未知"


def list_archive_contents(archive_path: Path) -> tuple[bool, list[str], Optional[str]]:
    """用 7z l 列出压缩包内容，返回 (成功, 文件路径列表, 错误信息)"""
    cmd = [SEVEN_ZIP, "l", str(archive_path), "-ba", "-sccUTF-8"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "password" in stderr.lower() or "encrypted" in stderr.lower():
                return False, [], "加密文件，请先解密后再导入"
            return False, [], stderr or "7z 列出内容失败"
        paths = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            # 7z l -ba 输出格式: "....D ....          123  2024-01-01  file.txt"
            # 路径在最后一列（第6列之后）
            parts = line.split()
            if len(parts) >= 6:
                filepath_in_archive = parts[-1]
                if filepath_in_archive and not filepath_in_archive.endswith("/"):
                    paths.append(filepath_in_archive)
        return True, paths, None
    except subprocess.TimeoutExpired:
        return False, [], "7z 列出内容超时"
    except FileNotFoundError:
        return False, [], f"7z.exe 未找到: {SEVEN_ZIP}"


def extract_archive(archive_path: Path, output_dir: Path) -> tuple[bool, Optional[str]]:
    """用 7z x 解压到 output_dir，返回 (成功, 错误信息)"""
    cmd = [SEVEN_ZIP, "x", str(archive_path), f"-o{output_dir}", "-y", "-bso0", "-bse0"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "password" in stderr.lower() or "encrypted" in stderr.lower():
                return False, "加密文件，请先解密后再导入"
            # 7z 有时返回 1 表示警告（部分文件未解压），但仍成功
            if result.returncode == 1 and output_dir.exists():
                return True, None
            return False, stderr or f"7z 解压失败，返回码: {result.returncode}"
        return True, None
    except subprocess.TimeoutExpired:
        return False, "解压超时（>300s）"
    except FileNotFoundError:
        return False, f"7z.exe 未找到: {SEVEN_ZIP}"


def check_zip_bomb(archive_path: Path) -> tuple[bool, Optional[str]]:
    """检查压缩炸弹：压缩比 > 100:1 且未压缩 > 100MB"""
    cmd = [SEVEN_ZIP, "l", str(archive_path), "-ba", "-sccUTF-8"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return True, None  # 无法检测，放行
        total_compressed = 0
        total_uncompressed = 0
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 5:
                try:
                    compressed = int(parts[2])
                    uncompressed = int(parts[3])
                    total_compressed += compressed
                    total_uncompressed += uncompressed
                except (ValueError, IndexError):
                    pass
        if total_compressed > 0 and total_uncompressed > 0:
            ratio = total_uncompressed / total_compressed
            if ratio > 100 and total_uncompressed > 100 * 1024 * 1024:
                return True, f"压缩比 {ratio:.0f}:1，未压缩 {format_size(total_uncompressed)}，可能是压缩炸弹，继续解压？"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return True, None  # 检测失败，放行


# ============================================================================
# 预扫描规则加载
# ============================================================================

def load_prescan_rules() -> tuple[dict, str, str, callable]:
    """动态加载 .claudian/prescan.py，返回 (RULES, MARKER_EXE, MINERU_EXE, scan_pdf)"""
    import importlib.util
    repo_root = get_repo_root()
    prescan_path = repo_root / ".claudian" / "prescan.py"
    if not prescan_path.exists():
        sys.stderr.write(f"[错误] prescan.py 未找到: {prescan_path}\n")
        sys.exit(1)
    spec = importlib.util.spec_from_file_location("prescan", str(prescan_path))
    if spec is None or spec.loader is None:
        sys.stderr.write(f"[错误] 无法从 {prescan_path} 加载 prescan 模块\n")
        sys.exit(1)
    prescan = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(prescan)
    except ModuleNotFoundError as e:
        sys.stderr.write(f"[错误] 缺少依赖: {e}\n")
        sys.stderr.write("  安装: pip install PyPDF2 pycryptodome\n")
        sys.exit(1)
    return prescan.RULES, prescan.MARKER_EXE, prescan.MINERU_EXE, prescan.scan_pdf


# ============================================================================
# 文件分类与转换
# ============================================================================

def find_convertible_files(directory: Path, RULES: dict, depth: int = 0) -> list[Path]:
    """递归扫描目录，找出所有可转换文件（含视频——由 video2text.py 处理）"""
    files = []
    try:
        for entry in sorted(directory.iterdir()):
            if entry.name in SKIP_FILES:
                continue
            if entry.is_file():
                ext = entry.suffix.lower()
                if ext in RULES or ext in VIDEO_EXTENSIONS:
                    files.append(entry)
                elif is_archive(entry, RULES) and depth < MAX_RECURSION_DEPTH:
                    files.append(entry)  # 嵌套压缩包
            elif entry.is_dir() and not entry.name.startswith("_"):
                files.extend(find_convertible_files(entry, RULES, depth))
    except PermissionError:
        pass
    return files


def classify_file(filepath: Path, RULES: dict, scan_pdf_func: callable) -> dict:
    """分类文件，返回 {type, tool_name, est, cmd, pages, ...}"""
    ext = filepath.suffix.lower()

    # 视频文件 → 标注为 video 类型，由 video2text.py 处理
    if ext in VIDEO_EXTENSIONS:
        return {
            "type": "video",
            "label": f"视频 ({ext})",
            "tool_name": "video2text (faster-whisper large-v3)",
            "est": f"~{filepath.stat().st_size / 1024 / 1024:.0f}MB, GPU≈0.6x实时, CPU≈0.2x实时",
            "cmd": f"python engine/tools/video2text.py \"{filepath}\"",
            "pages": 0,
            "output_stem": safe_stem(filepath),
            "output_path": f"{safe_stem(filepath)}_transcript.txt",
            "note": "视频转录耗时长（1h视频≈1.5h GPU），需确认后手动执行",
        }

    rule = RULES.get(ext)
    if not rule:
        return {"type": "unknown", "reason": f"不支持的格式: {ext}"}

    label = rule["label"]
    output_stem = safe_stem(filepath)
    output_path = f"{output_stem}.md"

    if ext == ".pdf" and "scanner" in rule:
        result = scan_pdf_func(str(filepath))
        rtype = result["type"]
        tool = rule["tools"][rtype]
        return {
            "type": "pdf",
            "subtype": rtype,
            "label": label,
            "tool_name": tool["name"],
            "est": tool["est"],
            "cmd": tool["cmd"],
            "pages": result.get("total_pages", 0),
            "output_stem": output_stem,
            "output_path": output_path,
            "reason": result.get("reason", ""),
        }
    else:
        tool = rule["tool"]
        return {
            "type": "single",
            "label": label,
            "tool_name": tool["name"],
            "est": tool["est"],
            "cmd": tool["cmd"],
            "pages": 0,
            "output_stem": output_stem,
            "output_path": output_path,
        }


def build_command(cmd_template: str, filepath: str, output: str, output_dir: str, marker_exe: str, mineru_exe: str) -> str:
    """填充命令模板中的占位符"""
    stem = os.path.splitext(filepath)[0]
    return cmd_template.format(
        path=filepath,
        stem=stem,
        output=output,
        output_dir=output_dir,
        marker=marker_exe,
        mineru=mineru_exe,
    )


def _markitdown_api_convert(input_path: Path, output_path: Path) -> tuple[bool, str, str]:
    """使用 MarkItDown Python API 直接转换，返回 (成功, stdout, stderr)"""
    if not _MARKITDOWN_API_AVAILABLE:
        return False, "", "MarkItDown Python 模块未安装，且 CLI 也不可用。安装: pip install 'markitdown[all]'"
    try:
        start = time.time()
        result = _MARKITDOWN_API.convert(str(input_path))
        text = result.text_content
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        elapsed = time.time() - start
        return True, f"API 转换完成（{elapsed:.1f}s, {len(text)} 字符）", ""
    except Exception as e:
        return False, "", str(e)


def run_conversion(command: str, cwd: str = None) -> tuple[bool, str, str]:
    """执行转换命令，返回 (成功, stdout, stderr)"""
    try:
        result = subprocess.run(
            shlex.split(command),
            shell=False,
            capture_output=True,
            text=True,
            timeout=CONVERSION_TIMEOUT,
            cwd=cwd,
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", f"转换超时（>{CONVERSION_TIMEOUT}s）"


def find_marker_output(expected_file: Path, stem: str) -> Optional[Path]:
    """处理 Marker 的输出：可能在 <dir>/<stem>/<stem>.md 子目录下"""
    if expected_file.exists():
        return expected_file
    # Marker 模式: <parent_dir>/<stem>/<stem>.md
    marker_pattern = expected_file.parent / stem / f"{stem}.md"
    if marker_pattern.exists():
        return marker_pattern
    return None


# ============================================================================
# 核心处理逻辑
# ============================================================================

def process_single(
    filepath: Path,
    inbox_dirs: dict[str, Path],
    RULES: dict,
    scan_pdf_func: callable,
    marker_exe: str,
    mineru_exe: str,
    dry_run: bool = False,
    json_output: bool = False,
    recursion_depth: int = 0,
) -> dict:
    """处理单个文件：压缩包检测 → 分类 → 转换 → 归档"""
    if not filepath.exists():
        return {"success": False, "error": f"文件不存在: {filepath}"}

    # --- Step A: 压缩包检测 ---
    if is_archive(filepath, RULES):
        return process_archive(
            filepath, inbox_dirs, RULES, scan_pdf_func, marker_exe, mineru_exe,
            dry_run, json_output, recursion_depth,
        )

    # --- Step B: 分类 ---
    ext = filepath.suffix.lower()
    if ext not in RULES and ext not in VIDEO_EXTENSIONS:
        return {
            "success": False,
            "error": f"不支持的格式: {ext}",
            "supported_formats": sorted(set(RULES.keys()) | VIDEO_EXTENSIONS),
        }

    # 视频文件：标记为需手动处理，不做自动转换
    if ext in VIDEO_EXTENSIONS:
        info = classify_file(filepath, RULES, scan_pdf_func)
        return {
            "success": False,
            "skip": True,
            "type": "video",
            "file": str(filepath),
            "label": info["label"],
            "tool": info["tool_name"],
            "est": info["est"],
            "note": info.get("note", ""),
            "action": "视频转录耗时较长，请手动执行: python engine/tools/video2text.py <文件>",
        }

    info = classify_file(filepath, RULES, scan_pdf_func)
    if info["type"] == "unknown":
        return {"success": False, "error": info.get("reason", "无法分类")}

    # --- Dry run: 只输出结果 ---
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "file": str(filepath),
            "tool": info["tool_name"],
            "est": info["est"],
            "pages": info.get("pages", 0),
            "output": str(inbox_dirs["converted"] / info["output_path"]),
        }

    # --- Step C: 检查输出冲突 ---
    output_file = inbox_dirs["converted"] / info["output_path"]
    output_dir = inbox_dirs["converted"]
    if output_file.exists():
        new_name = deduplicate_name(output_dir, info["output_path"])
        info["output_path"] = new_name
        output_file = output_dir / new_name
        info["output_stem"] = os.path.splitext(new_name)[0]

    # --- Step D: 多步转换 → 先复制源文件 ---
    cwd = None
    source_dest = inbox_dirs["sources"] / filepath.name
    is_multistep = ext in (".doc", ".ppt", ".mobi", ".azw", ".azw3")
    if is_multistep:
        source_dest = inbox_dirs["sources"] / deduplicate_name(
            inbox_dirs["sources"], filepath.name
        )
        if not dry_run:
            shutil.copy2(str(filepath), str(source_dest))
        cwd = str(inbox_dirs["sources"])
        cmd = build_command(info["cmd"], str(source_dest),
                            str(output_file), str(output_dir), marker_exe, mineru_exe)
    else:
        cmd = build_command(info["cmd"], str(filepath),
                            str(output_file), str(output_dir), marker_exe, mineru_exe)

    # --- Step E: 执行转换（MarkItDown CLI 不可用时自动走 Python API）---
    if info["tool_name"] == "MarkItDown" and not _MARKITDOWN_CLI:
        # CLI 不在 PATH，降级到 Python API
        success, stdout, stderr = _markitdown_api_convert(filepath, output_file)
        if success:
            info["tool_name"] = "MarkItDown (API)"  # 标记实际使用的路径
    else:
        success, stdout, stderr = run_conversion(cmd, cwd=cwd)

    # --- Step F: 处理结果 ---
    if not success:
        return {
            "success": False,
            "error": "转换失败",
            "stderr": stderr[:500] if stderr else "(无输出)",
            "tool": info["tool_name"],
            "source": str(filepath),
            "warnings": [],
        }

    # 处理 Marker 子目录输出
    actual_output = find_marker_output(output_file, info["output_stem"])
    if actual_output is None:
        return {
            "success": False,
            "error": "未找到输出文件",
            "expected": str(output_file),
            "tool": info["tool_name"],
            "source": str(filepath),
            "warnings": [],
        }

    if actual_output != output_file and actual_output.exists():
        shutil.move(str(actual_output), str(output_file))
        # 清理 Marker 留下的空子目录
        sub_dir = actual_output.parent
        if sub_dir != output_dir:
            try:
                for f in sub_dir.iterdir():
                    f.rename(output_dir / f.name)
                sub_dir.rmdir()
            except (OSError, PermissionError):
                pass

    # 源文件留在原地，不动用户文件
    return {
        "success": True,
        "source": str(source_dest),
        "converted": str(output_file),
        "tool": info["tool_name"],
        "pages": info.get("pages", 0),
        "warnings": [],
    }


def process_archive(
    filepath: Path,
    inbox_dirs: dict[str, Path],
    RULES: dict,
    scan_pdf_func: callable,
    marker_exe: str,
    mineru_exe: str,
    dry_run: bool = False,
    json_output: bool = False,
    recursion_depth: int = 0,
) -> dict:
    """处理压缩包：安全检测 → 解压 → 递归扫描 → 逐个转换"""
    if recursion_depth >= MAX_RECURSION_DEPTH:
        return {"success": False, "error": f"压缩包嵌套深度超过 {MAX_RECURSION_DEPTH} 层"}

    archive_format = detect_archive_type(filepath)
    stem = safe_stem(filepath)

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "type": "archive",
            "archive_format": archive_format,
            "file": str(filepath),
            "action": "解压到 .inbox/_extracted/ 后逐个转换",
        }

    # --- 安全检查 ---
    ok, paths, err = list_archive_contents(filepath)
    if not ok:
        return {
            "success": False,
            "type": "archive",
            "archive_format": archive_format,
            "error": err or "列出内容失败",
            "source": str(filepath),
        }

    # 路径穿越检测
    extract_dir = inbox_dirs["extracted"] / stem
    for p in paths:
        if not is_safe_path(extract_dir, p):
            return {
                "success": False,
                "type": "archive",
                "error": f"压缩包含不安全路径: {p}",
                "source": str(filepath),
            }

    # --- 炸弹检测 ---
    ok, bomb_warning = check_zip_bomb(filepath)
    if bomb_warning:
        # 不阻断，但在结果中警告
        pass

    # --- 解压 ---
    extract_dir.mkdir(parents=True, exist_ok=True)
    ok, err = extract_archive(filepath, extract_dir)
    if not ok:
        return {
            "success": False,
            "type": "archive",
            "archive_format": archive_format,
            "error": err or "解压失败",
            "source": str(filepath),
        }

    # --- 递归扫描解压内容 ---
    convertible = find_convertible_files(extract_dir, RULES, depth=recursion_depth)
    if not convertible:
        shutil.rmtree(extract_dir, ignore_errors=True)
        return {
            "success": False,
            "type": "archive",
            "error": "解压后无可转换文件",
            "source": str(filepath),
        }

    # --- 对每个解压文件执行转换 ---
    results = []
    for f in convertible:
        result = process_single(
            f, inbox_dirs, RULES, scan_pdf_func, marker_exe, mineru_exe,
            dry_run=False, json_output=True, recursion_depth=recursion_depth + 1,
        )
        results.append(result)

    # --- 汇总 ---
    success_count = sum(1 for r in results if r.get("success"))
    fail_count = sum(1 for r in results if not r.get("success"))

    warnings_list = []
    if bomb_warning:
        warnings_list.append(bomb_warning)

    return {
        "success": True,
        "type": "archive",
        "archive_format": archive_format,
        "source": str(source_dest),
        "extracted_to": str(extract_dir),
        "files_found": len(convertible),
        "files_converted": success_count,
        "files_failed": fail_count,
        "files_skipped": 0,
        "warnings": warnings_list,
        "results": results,
    }


def process_batch(
    directory: Path,
    inbox_dirs: dict[str, Path],
    RULES: dict,
    scan_pdf_func: callable,
    marker_exe: str,
    mineru_exe: str,
    dry_run: bool = False,
    json_output: bool = False,
) -> dict:
    """批量处理目录中的所有文件"""
    if not directory.is_dir():
        return {"success": False, "error": f"不是目录: {directory}"}

    files = sorted([
        f for f in directory.iterdir()
        if f.is_file() and f.name not in SKIP_FILES
    ])

    if not files:
        return {"success": True, "summary": {"total": 0, "success": 0, "failed": 0}, "results": []}

    results = []
    for f in files:
        result = process_single(
            f, inbox_dirs, RULES, scan_pdf_func, marker_exe, mineru_exe,
            dry_run=dry_run, json_output=json_output,
        )
        results.append(result)

    success = sum(1 for r in results if r.get("success"))
    failed = sum(1 for r in results if not r.get("success"))

    return {
        "success": failed == 0,
        "summary": {"total": len(files), "success": success, "failed": failed},
        "results": results,
    }


# ============================================================================
# 输出
# ============================================================================

def print_json_output(result: dict) -> None:
    """输出 JSON 格式结果"""
    print(json.dumps(result, ensure_ascii=False, indent=2))


def print_human(result: dict) -> None:
    """人类可读输出"""
    if result.get("dry_run"):
        print(f"[DRY RUN] {result.get('file', '?')}")
        print(f"  工具: {result.get('tool', result.get('action', '?'))}")
        if result.get("est"):
            print(f"  预估: {result['est']}")
        if result.get("output"):
            print(f"  输出: {result['output']}")
        return

    if result.get("skip") and result.get("type") == "video":
        print(f"[视频] {result.get('file', '?')}")
        print(f"  类型: {result.get('label', '?')}")
        print(f"  工具: {result.get('tool', '?')}")
        print(f"  预估: {result.get('est', '?')}")
        print(f"  ⚠ {result.get('note', '需手动处理')}")
        print(f"  → {result.get('action', '')}")
        return

    if result.get("type") == "archive":
        print(f"[压缩包] {result.get('archive_format', '?')} -> {result.get('source', '?')}")
        print(f"  解压到: {result.get('extracted_to', '?')}")
        print(f"  转换: {result.get('files_converted', 0)}/{result.get('files_found', 0)} 成功"
              + (f", {result.get('files_failed', 0)} 失败" if result.get('files_failed') else ""))
        for w in result.get("warnings", []):
            print(f"  [WARN] {w}")
        for r in result.get("results", []):
            if r.get("success"):
                print(f"    OK  {r.get('converted', r.get('file', '?'))}")
            else:
                print(f"    FAIL  {r.get('file', r.get('source', '?'))}: {r.get('error', '?')}")
        return

    if result.get("success"):
        print(f"[OK] {result.get('source', '?')}")
        print(f"  工具: {result.get('tool', '?')}"
              + (f" ({result.get('pages', 0)} 页)" if result.get('pages') else ""))
        print(f"  输出: {result.get('converted', '?')}")
    else:
        print(f"[FAIL] {result.get('file', result.get('source', '?'))}")
        print(f"  错误: {result.get('error', '?')}")
        if result.get("stderr"):
            print(f"  详情: {result['stderr']}")


def print_batch_summary(batch_result: dict) -> None:
    """批量处理摘要"""
    s = batch_result.get("summary", {})
    print(f"\n--- 批量导入完成 ---")
    print(f"  总计: {s.get('total', 0)}")
    print(f"  成功: {s.get('success', 0)}")
    print(f"  失败: {s.get('failed', 0)}")


# ============================================================================
# 主入口
# ============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="资料一键导入：压缩包解压 → 预扫描 → 转换 → 归档到 .inbox/",
    )
    parser.add_argument(
        "target",
        help="文件路径（或 --batch 模式下的目录路径）",
        nargs="?",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="批量模式：处理目录中所有文件",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON 输出（供 LLM 解析）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预演模式：只扫描不转换",
    )

    args = parser.parse_args()

    if not args.target:
        parser.print_help()
        sys.exit(1)

    target = Path(args.target).resolve()
    repo_root = get_repo_root()
    inbox_dirs = get_inbox_dirs(repo_root)

    # 加载预扫描规则
    RULES, marker_exe, mineru_exe, scan_pdf_func = load_prescan_rules()

    # 检查 7z
    seven_zip_available = Path(SEVEN_ZIP).exists()

    if args.batch:
        result = process_batch(
            target, inbox_dirs, RULES, scan_pdf_func, marker_exe, mineru_exe,
            dry_run=args.dry_run, json_output=args.json,
        )
        if args.json:
            print_json_output(result)
        else:
            for r in result.get("results", []):
                print_human(r)
            print_batch_summary(result)
    else:
        # 单文件：检查是否是需解压的压缩包
        if is_archive(target, RULES) and not seven_zip_available:
            print(f"[错误] 文件是压缩包，但 7z.exe 未找到: {SEVEN_ZIP}")
            print(f"  请安装 7-Zip 或将文件手动解压后重新导入")
            sys.exit(1)

        result = process_single(
            target, inbox_dirs, RULES, scan_pdf_func, marker_exe, mineru_exe,
            dry_run=args.dry_run, json_output=args.json,
        )
        if args.json:
            print_json_output(result)
        else:
            print_human(result)

    # 退出码
    if isinstance(result, dict) and not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
