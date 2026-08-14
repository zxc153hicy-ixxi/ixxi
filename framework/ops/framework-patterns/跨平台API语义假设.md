---
tags: [反模式]
status: active
confidence: high
summary: 跨平台 API 语义假设——Python Path.rename() 在 Unix 静默覆盖、Windows 抛 FileExistsError，原子写入应改用 replace()
created: 2026-07-18
updated: 2026-07-20
---

# 跨平台 API 语义假设

## 发生了什么

批处理脚本运行数小时零输出。日志显示每个文件立即失败，但没有明确的错误信息。

排查发现：脚本用 `tmp_path.rename(tgt)` 做原子写入，其中 `tgt` 是之前处理失败留下的 0KB 占位文件。每次调用时，Windows 上的 `rename()` 因目标已存在而抛出 `FileExistsError`，异常处理中删除了 `.tmp` 文件——处理结果在落盘前被丢弃。

## 根因

Python `Path.rename()` 的 POSIX 语义 vs Windows 语义不一致：

| 平台 | `rename()` 行为 | `replace()` 行为 |
|------|----------------|-----------------|
| Unix/Linux | 静默覆盖已存在的目标 | 静默覆盖已存在的目标 |
| Windows | **抛出 `FileExistsError`** | 静默覆盖已存在的目标 |

`os.rename()` / `Path.rename()` 的 Python 文档明确写了：**"On Windows, if dst exists, FileExistsError is raised."**

## 怎么修的

```python
# 错误：假设 Unix 语义
tmp_path.rename(tgt)

# 正确：跨平台原子替换
tmp_path.replace(tgt)
```

`Path.replace()` 在所有平台上行为一致——原子替换已存在的目标，不抛异常。

## 防范

1. Python 文件写入中，任何「先写临时文件再 rename」的原子写入模式，**必须用 `replace()` 不用 `rename()`**
2. 跨平台脚本在 Windows 上实际运行验证，不止读代码审查
3. 去重/占位检查逻辑用 `stat().st_size > 0`，不止 `.exists()`
