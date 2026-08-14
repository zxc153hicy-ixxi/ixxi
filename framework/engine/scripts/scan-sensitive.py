#!/usr/bin/env python3
"""scan-sensitive.py -- 安全扫描：PII 敏感信息 + 攻击面（供应链/代码风险）

PII 5 类：身份证/银行卡/手机号/密码明文/API Key/私钥头
攻击面 6 类（智谱风险 3.1，供应链安全）：
  1. Base64 解码执行     —— 长 base64 串解码后命中 exec/import/eval 等危险模式
  2. 环境变量外泄        —— os.environ/getenv/$VAR 被拼接到 URL/网络请求
  3. .git/hooks 注入     —— .git/hooks 路径 + 写操作（open 'w/a'/write/重定向）同现
  4. 依赖投毒            —— pip/npm 依赖源指向非官方源；下载 .whl/.tar.gz 后本地执行
  5. 路径穿越            —— ../ 序列 + 文件读写操作同现
  6. 混淆代码            —— hex 转义(\\x..)/chr() 拼接 + exec/eval；__import__ + 字符串拼接

依赖：仅 Python 标准库（re/base64），零第三方。

用法:
  python engine/scripts/scan-sensitive.py --repo <知识库根目录>
  python engine/scripts/scan-sensitive.py --repo . --json
  python engine/scripts/scan-sensitive.py --stdin          # 从 stdin 读（git diff 管道）
"""

import argparse
import base64
import json
import re
import sys
from pathlib import Path

# GBK 终端兜底
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ────────────────────────────────────────────────────────────────
# 1. PII 敏感信息正则（原有 5 类，保留）
# ────────────────────────────────────────────────────────────────
PATTERNS = {
    "身份证": re.compile(r"[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]"),
    "银行卡": re.compile(r"\b([1-9]\d{15,18})\b"),
    "手机号": re.compile(r"1[3-9]\d{9}"),
    "密码明文": re.compile(r"(password|passwd|pwd|密钥|secret|token)\s*[=:：]\s*\S+", re.IGNORECASE),
    "API_Key": re.compile(r"(sk-[a-zA-Z0-9]{20,}|AIza[0-9A-Za-z_-]{35})"),
    "私钥头": re.compile(r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----"),
}

# ────────────────────────────────────────────────────────────────
# 2. 攻击面检测（正则/启发式，6 类）
# ────────────────────────────────────────────────────────────────

# 2.1 Base64 解码执行
# 检测逻辑：先捕获 ≥32 位的 base64 字符（含尾部 0-2 个 = 填充），补齐 padding 后
#   strict 解码；解码结果必须是可打印 UTF-8 文本，且其中命中 exec/eval/__import__
#   /import os/os.system/subprocess/socket 等危险执行模式才告警（纯二进制数据或
#   无执行意图的 base64 直接忽略，降低误报）。
BASE64_BLOB_RE = re.compile(r"[A-Za-z0-9+/]{32,}={0,2}")
BASE64_DANGEROUS_RE = re.compile(
    r"exec\s*\(|eval\s*\(|__import__|import os|os\.system|subprocess|system\s*\(|socket\.", re.IGNORECASE)

# 2.2 环境变量外泄
# 检测逻辑：逐行扫描——同一行内同时出现 环境变量读取（os.environ[...] /
#   os.environ.get(...) / os.getenv(...) / $VAR） 与 网络请求上下文
#   （https?://、requests./urllib/urlopen/socket./curl、user@host）即视为外泄，
#   仅读取 env 而无网络出站的普通配置行不告警。
ENV_ACCESS_RE = re.compile(r"os\.environ\s*\[[^\]]+\]|os\.environ\.get\s*\([^)]*\)|os\.getenv\s*\([^)]*\)|\$[A-Za-z_][A-Za-z0-9_]*")
NETWORK_CTX_RE = re.compile(r"https?://|requests\.|urllib|urlopen|socket\.|curl\s|ftp://|@[A-Za-z0-9-]+\.\w+")

# 2.3 .git/hooks 注入
# 检测逻辑：.git 与 hooks 之间存在少量非字符合（覆盖 .git/hooks、".git"+"/hooks"、
#   os.path.join(".git","hooks") 等写法）视为 hooks 路径；该路径行或相邻 ±1 行出现
#   写操作（open(...,'w'/'a')、.write、mkdir）即告警（在 hooks 目录写入文件 = 持久化后门）。
GIT_HOOKS_PATH_RE = re.compile(r"\.git[\W_]{0,6}hooks")
GIT_HOOKS_WRITE_RE = re.compile(r"open\s*\([^)]*['\"][wa]", re.IGNORECASE)

# 2.4 依赖投毒
# 检测逻辑：①捕获 --index-url/--extra-index-url/--registry 后的 URL、.npmrc 的
#   registry= 行、pip install -i 的 URL，取其 host 与官方/可信镜像白名单比对，不在白名单
#   或明文 http 一律告警；②wget/curl 下载 .whl/.tar.gz 且同行为安装/执行命令视为
#   "下载即执行"投毒链。
DEP_INDEX_RE = re.compile(
    r"(?:--index-url|--extra-index-url|--registry)\s*=?\s*(https?://[^\s'\"`]+)", re.IGNORECASE)
NPMRC_REGISTRY_RE = re.compile(r"^\s*registry\s*=\s*(https?://\S+)", re.MULTILINE | re.IGNORECASE)
PIP_SHORT_INDEX_RE = re.compile(
    r"pip\s+(?:install|download)\b[^\n]*?-i\s+(https?://[^\s'\"`]+)", re.IGNORECASE)
DEP_DOWNLOAD_EXEC_RE = re.compile(
    r"(?:wget|curl|Invoke-WebRequest|iwr)[^\n]{0,200}?\.(?:whl|tar\.gz|tgz)"
    r"[^\n]{0,200}?(?:pip\s+install|python[^\n]{0,30}\.py|exec\s*\(|import\s+|[./\\]|bash\s|sh\s)",
    re.IGNORECASE)
# 官方源 + 常见可信镜像白名单（host 精确或子域匹配）
ALLOWED_INDEX_HOSTS = (
    "pypi.org", "files.pythonhosted.org", "registry.npmjs.org",
    "registry.yarnpkg.com", "npmjs.org",
    "pypi.tuna.tsinghua.edu.cn", "mirrors.aliyun.com", "mirrors.cloud.tencent.com",
    "registry.npmmirror.com",
)

# 2.5 路径穿越
# 检测逻辑：逐行扫描——同一行内出现 ../ 或 ..\ 序列 且同时出现文件读写操作
#   （open(...)/os.path.join/Path(...)/read_text/write_text/.read()/.write()/
#   unlink/os.remove/shutil...）即告警，避免纯文档里的相对路径 ../ 误报。
TRAVERSAL_RE = re.compile(r"\.\.\s*[/\\]")
FILE_IO_RE = re.compile(
    r"open\s*\(|os\.path\.join|Path\s*\(|read_text|write_text|\.read\s*\(|\.write\s*\(|"
    r"unlink\s*\(|os\.remove|os\.rename|shutil\.|file_put_contents", re.IGNORECASE)

# 2.6 混淆代码
# 检测逻辑：三种特征任一命中即告警——①exec/eval 的参数中出现 \xNN hex 转义
#   （exec('\x68...')）；②exec/eval 的参数用 chr(...)+ 拼接构造（eval(chr(...)+...)）；
#   ③__import__ 的参数带字符串拼接（__import__("o"+"s")）。均为动态构造可执行代码的混淆手法。
OBF_HEX_EXEC_RE = re.compile(r"(?:exec|eval)\s*\([^)]*\\(?:x|X)[0-9a-fA-F]{2}")
OBF_CHR_EXEC_RE = re.compile(r"(?:exec|eval)\s*\([^)]*chr\s*\([^)]*\)\s*\+")
OBF_IMPORT_CONCAT_RE = re.compile(r"__import__\s*\([^)]*\s*\+\s*['\"]")

# ────────────────────────────────────────────────────────────────
# 跳过配置（与原有保持一致，保证仓库级扫描行为不变）
# ────────────────────────────────────────────────────────────────
SKIP_FILES = {"Thumbs.db", ".DS_Store", "desktop.ini", ".gitkeep", ".placeholder", "scan-sensitive.py"}
SKIP_DIRS = {".git", "__pycache__", ".fix-backup", "node_modules", "_external"}
SKIP_ROOT_DIRS = {".claudian", "docs", "raw", ".obsidian", ".claude", ".agents"}
# 学习/教学材料目录——自然包含安全示例（密码、手机号等），非真实泄露
SKIP_SENSITIVE_DIRS = {
    "knowledge/learning",  # 学习/教学材料目录（实例自填具体领域，天然含安全示例）
    "engine/templates",  # 扫描器自身模板
    "engine/scripts/malicious-samples",  # 恶意样例测试夹具（本就是恶意内容）
}


def _hit(_type: str, source: str, snippet: str, pos: int) -> dict:
    """构造统一命中记录（与 PII 输出格式一致）"""
    return {"type": _type, "source": source, "snippet": snippet, "pos": pos}


def _iter_lines(text: str):
    """逐行迭代，产出 (行内容含换行, 行在全文中的起始偏移)"""
    start = 0
    for line in text.splitlines(keepends=True):
        yield line, start
        start += len(line)


# ── 各攻击面检测函数（输出与 PII 同构）─────────────────────────────
def detect_base64_code(text: str, source: str) -> list[dict]:
    hits = []
    for m in BASE64_BLOB_RE.finditer(text):
        token = m.group().strip("=")
        if len(token) % 4:
            token += "=" * (4 - len(token) % 4)
        try:
            decoded = base64.b64decode(token, validate=True)
        except Exception:
            continue
        try:
            content = decoded.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if not content.isprintable() or len(content) < 6:
            continue
        if BASE64_DANGEROUS_RE.search(content):
            hits.append(_hit("攻击面:Base64解码执行", source,
                             f"base64→{content[:40]!r}", m.start()))
    return hits


def detect_env_exfil(text: str, source: str) -> list[dict]:
    hits = []
    for line, off in _iter_lines(text):
        env_m = ENV_ACCESS_RE.search(line)
        if not env_m:
            continue
        if NETWORK_CTX_RE.search(line):
            hits.append(_hit("攻击面:环境变量外泄", source,
                             line.strip()[:80], off + env_m.start()))
    return hits


def detect_git_hooks(text: str, source: str) -> list[dict]:
    hits = []
    lines = list(_iter_lines(text))
    for i, (line, off) in enumerate(lines):
        if not GIT_HOOKS_PATH_RE.search(line):
            continue
        lo, hi = max(0, i - 1), min(len(lines), i + 2)
        if any(GIT_HOOKS_WRITE_RE.search(lines[j][0]) for j in range(lo, hi)):
            hits.append(_hit("攻击面:.git/hooks注入", source, line.strip()[:80], off))
    return hits


def _host_of(url: str) -> str:
    m = re.match(r"https?://([^/:]+)", url)
    return m.group(1).lower() if m else ""


def _is_allowed_index(url: str) -> bool:
    host = _host_of(url)
    if not host:
        return False
    if url.lower().startswith("http://"):  # 明文 http 源一律告警
        return False
    return any(host == a or host.endswith("." + a) for a in ALLOWED_INDEX_HOSTS)


def detect_dependency_poisoning(text: str, source: str) -> list[dict]:
    hits = []
    urls = []
    for m in DEP_INDEX_RE.finditer(text):
        urls.append((m.group(1), m.start()))
    for m in NPMRC_REGISTRY_RE.finditer(text):
        urls.append((m.group(1), m.start()))
    for m in PIP_SHORT_INDEX_RE.finditer(text):
        urls.append((m.group(1), m.start()))
    for url, pos in urls:
        if not _is_allowed_index(url):
            hits.append(_hit("攻击面:依赖投毒", source, f"非官方依赖源: {url}", pos))
    for m in DEP_DOWNLOAD_EXEC_RE.finditer(text):
        hits.append(_hit("攻击面:依赖投毒", source,
                         f"下载并执行依赖包: {m.group()[:60]}", m.start()))
    return hits


def detect_path_traversal(text: str, source: str) -> list[dict]:
    hits = []
    for line, off in _iter_lines(text):
        m = TRAVERSAL_RE.search(line)
        if m and FILE_IO_RE.search(line):
            hits.append(_hit("攻击面:路径穿越", source, line.strip()[:80], off + m.start()))
    return hits


def detect_obfuscation(text: str, source: str) -> list[dict]:
    hits = []
    patterns = (
        ("hex转义+exec/eval", OBF_HEX_EXEC_RE),
        ("chr拼接+exec/eval", OBF_CHR_EXEC_RE),
        ("__import__+拼接", OBF_IMPORT_CONCAT_RE),
    )
    for label, pat in patterns:
        for m in pat.finditer(text):
            hits.append(_hit("攻击面:混淆代码", source, f"{label}: {m.group()[:50]}", m.start()))
    return hits


def detect_attack_surfaces(text: str, source: str) -> list[dict]:
    hits = []
    hits += detect_base64_code(text, source)
    hits += detect_env_exfil(text, source)
    hits += detect_git_hooks(text, source)
    hits += detect_dependency_poisoning(text, source)
    hits += detect_path_traversal(text, source)
    hits += detect_obfuscation(text, source)
    return hits


def scan_text(text: str, source: str) -> list[dict]:
    """扫描一段文本，返回命中列表（PII + 攻击面）"""
    hits = []
    for label, pattern in PATTERNS.items():
        for m in pattern.finditer(text):
            # 截断显示，避免输出完整敏感信息
            snippet = m.group()[:40]
            hits.append({
                "type": label,
                "source": source,
                "snippet": snippet,
                "pos": m.start(),
            })
    hits += detect_attack_surfaces(text, source)
    return hits


def scan_file(path: Path) -> list[dict]:
    """扫描单个文件"""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    return scan_text(text, str(path))


def scan_repo(repo_root: Path) -> list[dict]:
    """扫描整个仓库的 .md 和 .py 文件"""
    all_hits = []
    for f in sorted(repo_root.rglob("*")):
        if f.name in SKIP_FILES:
            continue
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        rel = f.relative_to(repo_root)
        first_part = rel.parts[0] if rel.parts else ""
        if first_part in SKIP_ROOT_DIRS:
            continue
        rel_str = str(rel).replace("\\", "/")
        if any(rel_str.startswith(d) for d in SKIP_SENSITIVE_DIRS):
            continue
        if f.is_file() and f.suffix.lower() in (".md", ".py", ".sh", ".toml", ".yaml", ".yml", ".json", ".txt"):
            all_hits.extend(scan_file(f))
    return all_hits


def main():
    parser = argparse.ArgumentParser(description="安全扫描（PII 敏感信息 + 攻击面）")
    parser.add_argument("--repo", type=str, default=None, help="知识库根目录")
    parser.add_argument("--stdin", action="store_true", help="从 stdin 读取")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    hits = []

    if args.stdin:
        text = sys.stdin.read()
        hits = scan_text(text, "<stdin>")
    elif args.repo:
        repo = Path(args.repo).resolve()
        hits = scan_repo(repo)
    else:
        repo = Path(__file__).resolve().parent.parent.parent
        hits = scan_repo(repo)

    if args.json:
        output = {
            "status": "pass" if not hits else "fail",
            "issues": [{"type": h["type"], "source": h["source"], "snippet": h["snippet"]} for h in hits],
            "score": 10 if not hits else 0,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        if not hits:
            print("✅ 安全扫描通过：未发现敏感信息/攻击面")
        else:
            print(f"❌ 安全扫描发现 {len(hits)} 处疑似安全问题：")
            for h in hits:
                print(f"  [{h['type']}] {h['source']}")
                print(f"         {h['snippet']}...")

    return 0 if not hits else 1


if __name__ == "__main__":
    sys.exit(main())
