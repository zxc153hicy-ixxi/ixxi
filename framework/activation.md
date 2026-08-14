# 操作入口注册表（framework 模板）

> 命令 / 脚本 / skill 的统一登记入口。护栏目标：新建即登记（见 framework-patterns/工具建成即登记）。
> 机制（本文件）归 framework；实例的具体登记数据（目录规模、脚本清单、运行快照）归 personal 实例的 activation.md。

## 登记格式

| 入口 | 路径 | 类型 | 说明 |
|------|------|------|------|
| （实例自填） | （实例自填） | 命令/脚本/skill | （实例自填） |

## 登记规则

- 新建脚本 / 工具 / skill → 立即在此登记入口，确保可被发现和复用
- check 脚本（如 check-script-refs）校验脚本是否已登记，未登记 → 提示补登
- 数字为约数，准确值以 index.md 和 `/check` 输出为准

## framework 通用层骨架

| 层 | 路径 | 用途 |
|------|------|------|
| 契约 | AGENT.md | 多 Agent 行为契约单一事实源 |
| 导航 | index.md | 全局导航树（锚点注册） |
| 规则 | ops/rules/ | 通用规则文件（G/R/T 通用条目） |
| 教训 | ops/framework-patterns/ | 可开源的通用工程教训（自正/反模式提炼） |
| 引擎 | engine/scripts/ + engine/config/ | 巡检/导入/转换/同步脚本 + 通用配置 |
| 知识 | knowledge/framework-designs/ | 通用框架设计文档 |
