#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-personal-sync.py — 同步前安全检查：personal 个人数据不推到 public remote

Task 1.4「personal 隔离」护栏（防个人数据泄露，智谱风险 3.5）。
在 git sync / push 之前运行，拦截「个人数据层 + 公开远程仓库」的组合。

检查逻辑（三步）：
  1. 解析候选个人目录：默认 `personal/` + `.gitignore` 中顶层目录条目
     （`personal/` 之外形如 `xxx/` 的行——init Q2 自定义目录名会被追加成这种行）
  2. 检测这些目录是否已存在且含有文件内容
  3. 检测 git remote 的 URL：
       - file:// 或本地路径（/…、./…、../…、~/…、盘符 C:\…）→ 本地，放行
       - 其余非本地 remote（含 github.com / gitlab.com 等公开托管，
         以及未识别 host）→ 按「公开/不可验证」保守处理
  个人目录有内容 + 存在非本地 remote → 阻断（默认退出码 2，拒绝执行 sync/push）。

用法：
  python engine/scripts/check-personal-sync.py            # 检查 + 阻断（默认）
  python engine/scripts/check-personal-sync.py --dry-run  # 只检查不阻断，始终退出 0
  python engine/scripts/check-personal-sync.py --repo <仓库根目录>

错误码：IXXI-E500（git 不可用/执行错误）  IXXI-E501（个人数据阻断）
退出码：0=放行  2=阻断(个人内容+非本地remote)  1=执行错误
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
try:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 已知公开代码托管 host（仅用于提示文案；未识别 host 同样按公开保守阻断）
KNOWN_PUBLIC_HOSTS = {
    "github.com", "gitlab.com", "bitbucket.org", "gitee.com",
    "gitea.com", "codeberg.org", "sourceforge.net", "gitlab.cn",
}

# 本地相对/绝对路径前缀（file:// 与 Windows 盘符另行判断）
LOCAL_PATH_PREFIXES = ("/", "./", "../", "~/")

# Windows 盘符：C:\… 或 C:/…
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")

# scp-like 形式：git@host:path / host:path / user:pass@host:path
SCP_RE = re.compile(r"^([^/@]+@)?([^/:]+):(.+)$")


def run_git(repo: Path, *args):
    """执行 git 命令，返回 (stdout, stderr)；git 不可用返回 (None, 错误信息)"""
    try:
        r = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, errors="replace",
        )
    except FileNotFoundError:
        return None, "git 不可用（未安装或不在 PATH）"
    return (r.stdout.strip() or ""), (r.stderr.strip() or "")


def remote_host(url: str):
    """从 remote URL 提取 host；本地（file:///路径）返回 None"""
    u = url.strip()

    # 带协议 URL（https/http/ssh/git/file）用 urlsplit 解析 host
    if "://" in u:
        parts = urlsplit(u)
        if parts.scheme == "file":
            return None
        if parts.hostname:
            return parts.hostname.lower().rstrip(".")

    # Windows 盘符 / 本地路径
    if WINDOWS_DRIVE_RE.match(u):
        return None
    if u.startswith(LOCAL_PATH_PREFIXES):
        return None

    # scp-like：git@host:path 或 host:path 或 user:pass@host:path
    m = SCP_RE.match(u)
    if m:
        return m.group(2).lower().rstrip(".")

    # host/path 形式（无协议）：github.com/user/repo
    host = u.split("/", 1)[0].split("@")[-1]
    return host.lower().rstrip(".")


def is_local_remote(url: str) -> bool:
    """remote 是否为本地（file:// 或本地路径）→ 放行"""
    return remote_host(url) is None


def personal_dirs(repo: Path) -> set:
    """候选个人目录名：默认 personal/ + .gitignore 顶层目录条目（xxx/ 行）"""
    names = {"personal"}
    gi = repo / ".gitignore"
    if gi.exists():
        for raw in gi.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("!"):
                continue
            # 顶层目录条目：形如 `xxx/`，无 /、无 glob
            if line.endswith("/") and "/" not in line and "*" not in line and "?" not in line:
                names.add(line[:-1])
    return names


def dir_has_content(repo: Path, name: str) -> bool:
    """目录是否存在且递归包含至少一个文件（排除 .git / __pycache__）"""
    d = repo / name
    if not d.is_dir():
        return False
    for p in d.rglob("*"):
        if not p.is_file():
            continue
        if any(part in (".git", "__pycache__") for part in p.parts):
            continue
        return True
    return False


def collect_remotes(repo: Path):
    """收集全部 remote：{name: url}，优先 upstream/origin"""
    out, err = run_git(repo, "remote")
    if out is None:
        return None, err
    names = out.splitlines()
    urls = {}
    for n in names:
        u, _ = run_git(repo, "config", "--get", f"remote.{n}.url")
        if u:
            urls[n] = u
    # upstream / origin 优先展示
    ordered = sorted(urls, key=lambda n: (n != "upstream", n != "origin", n))
    return {n: urls[n] for n in ordered}, ""


def main():
    ap = argparse.ArgumentParser(description="personal 数据同步前安全检查")
    ap.add_argument(
        "--repo",
        default=str(Path(__file__).resolve().parent.parent.parent.parent),
        help="仓库根目录（默认脚本位于 <仓库根>/framework/engine/scripts/ 的上四层）",
    )
    ap.add_argument("--dry-run", action="store_true",
                    help="只检查不阻断，始终退出 0")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()

    # 1) 个人目录
    names = sorted(personal_dirs(repo))
    content_dirs = [n for n in names if dir_has_content(repo, n)]

    # 2) remotes
    remotes, err = collect_remotes(repo)
    if remotes is None:
        print("IXXI-E500 | 执行错误：git 命令不可用（未安装或不在 PATH），无法检查 remote", file=sys.stderr)
        print(f"修复：安装 git 或将其加入 PATH 后重试；原始错误：{err}", file=sys.stderr)
        print("参考：engine/scripts/check-personal-sync.py", file=sys.stderr)
        return 1

    # 3) 非本地 remote = 按公开/不可验证保守处理
    public_remotes = {n: u for n, u in remotes.items() if not is_local_remote(u)}

    print(f"[check-personal-sync] 仓库：{repo}")
    print(f"[check-personal-sync] 候选个人目录：{', '.join(names) if names else '无'}")
    if content_dirs:
        print(f"[check-personal-sync] 含内容：{', '.join(content_dirs)}")
    print(f"[check-personal-sync] remotes：{', '.join(f'{n}={u}' for n, u in remotes.items()) or '无'}")

    # 放行路径
    if not content_dirs:
        print("[check-personal-sync] OK：无个人内容，放行")
        return 0
    if not public_remotes:
        print("[check-personal-sync] OK：个人内容存在，但 remote 均为本地或无 remote，放行")
        return 0

    # 阻断
    print("IXXI-E501 | 个人数据阻断：个人目录含内容，且仓库配置了非本地（可能公开）remote", file=sys.stderr)
    print("修复：将个人数据保留本地，删除或更换公开 remote 后重试 sync/push", file=sys.stderr)
    print("参考：framework/ops/rules/personal隔离规范.md", file=sys.stderr)
    print(f"[check-personal-sync] BLOCK：个人目录 {', '.join(content_dirs)} 含内容，且存在可能公开的 remote：")
    for n, u in public_remotes.items():
        host = remote_host(u)
        kind = "公开托管" if (host and host in KNOWN_PUBLIC_HOSTS) else "未识别host(按公开保守处理)"
        print(f"    {n} = {u}   [{kind}]")
    print("[check-personal-sync] 告警：personal 内容不能同步到 public remote！")

    if args.dry_run:
        print("[check-personal-sync] --dry-run：仅检查不阻断，退出 0")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
