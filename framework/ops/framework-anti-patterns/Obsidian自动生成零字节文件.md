---
tags: [反模式]
summary: Obsidian重命名或移动文件后自动生成零字节空壳文件，与同名目录冲突且删除后反复出现
created: 2026-07-11
updated: 2026-07-13
sources: [manual]
scene: [知识整理]
type: 反模式
confidence: high
status: active
scope: framework
---

# Obsidian 自动生成零字节文件

## 现象

在 Obsidian 中重命名或移动 .md 文件后，Obsidian 的「自动更新内部链接」功能会在知识库根目录自动创建零字节空壳文件，例如：

- `creative.md`（与 `creative/` 目录同名）
- `projects 1.md`
- `iterations.md`

这些文件：
- 大小为 0 字节
- 无任何内容
- 与同名目录冲突
- 删除后会反复出现

## 根因

Obsidian 在批量更新 `[[内部链接]]` 时，如果目标文件刚被重命名/移动，可能先创建一个空壳占位，然后写入内容。但当操作被 git 或其他进程中断时，空壳残留。

## 修复

```bash
find . -name "*.md" -size 0 -delete
```

定期清理。如果问题持续，在 Obsidian 设置 → 文件与链接 中关闭「自动更新内部链接」。

## 关联
- [[检查偷懒]] —— 废文件容易被忽略，需要定期扫描

- [[反模式索引]]
