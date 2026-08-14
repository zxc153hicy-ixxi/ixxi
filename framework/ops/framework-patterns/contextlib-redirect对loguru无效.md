---
tags: [反模式, Python, 日志]
status: active
created: 2026-07-20
version: 1.0.0
summary: contextlib.redirect_stderr 无法拦截 loguru 日志——loguru 初始化时捕获 sys.__stderr__ 引用
updated: 2026-07-20
---

# contextlib.redirect_stderr 对 loguru 无效

## 现象

用 `contextlib.redirect_stderr(log_file)` 包裹第三方库调用，预期抑制其日志输出。但 loguru 的日志仍然出现在终端，不受 redirect_stderr 控制。

## 根因

```python
# loguru 内部（简化）
import sys
_original_stderr = sys.__stderr__  # 或 sys.stderr 的引用快照

def _write(message):
    _original_stderr.write(message)  # 走原始句柄，不走 sys.stderr
```

`contextlib.redirect_stderr` 只替换 `sys.stderr`，但 loguru 在 `import` 时就捕获了原始 stderr 文件描述符的引用。之后 redirect 修改 `sys.stderr` 对它无效。

## 为什么 redirect_stdout 对 tqdm 有效

tqdm 默认写 `sys.stderr`（非 `sys.__stderr__`），每次迭代时读取当前 `sys.stderr` 引用，所以 redirect 生效。loguru 的快照机制是根本差异。

## 正确做法

**方案 1：在 loguru import 之前移除 handler**
```python
from loguru import logger
logger.remove()  # 移除默认 stderr handler
logger.add("app.log", level="INFO")  # 输出到文件
```

**方案 2：环境变量禁用（部分库支持）**
```python
os.environ["LOGURU_LEVEL"] = "WARNING"
```

**方案 3：os.dup2 重定向文件描述符（最彻底）**
```python
import os
old_stderr = os.dup(2)
with open("app.log", "w") as f:
    os.dup2(f.fileno(), 2)  # fd 2 → log file
    try:
        third_party_call()
    finally:
        os.dup2(old_stderr, 2)
        os.close(old_stderr)
```

## 适用场景

任何基于 loguru 的第三方库（MinerU、vllm 等）——它们 import 时 loguru 已初始化 handler，后续 redirect_stderr 无效。实测：此类库的 INFO/DEBUG 日志仍写入终端，而基于 `sys.stderr` 的进度条库（如 tqdm）会被 redirect_stdout 正确抑制。

## 通用启示

- 重定向/捕获输出前，先确认目标库是「运行时读取当前引用」还是「初始化时快照引用」，两种机制的拦截方式完全不同。
- 对「快照引用」类库，文件描述符层（`os.dup2`）重定向比替换 `sys.stderr` 更彻底。
