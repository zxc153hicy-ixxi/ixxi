# MOC 全局导航（framework）

> framework 是 ixxi 的开源通用层。本导航树只覆盖 framework 通用资产；个人实例的导航 = 本树 + 个人扩展节点（见 personal 实例的 index.md）。

## 契约与入口

- [[AGENT]] —— 多 Agent 行为契约单一事实源（CLAUDE/HERMES/Codex 由它同步生成）
- [[activation]] —— 操作入口注册表（命令/脚本登记护栏目标）
- [[../GETTING-STARTED|GETTING-STARTED]] —— 5 分钟上手

## 规则

- [[ops/rules/系统操作菜单|操作菜单]] —— 所有可执行操作统一入口
- ops/rules/ —— G/R/T 通用规则文件
- [[ops/framework-patterns/|framework-patterns]] —— 可开源的通用工程教训（自正/反模式提炼）

## 引擎

- engine/scripts/ —— 巡检/导入/转换/同步脚本（check-* / batch-* / sync-* / fix-*）
- engine/config/ —— 通用配置（tag-taxonomy 机制、cleanup 受控值域、scene-registry schema）
- engine/templates/ —— export-template.sh（分层导出）+ 模板脚本

## 扩展系统

- core/skills/ —— 框架机制技能 kb-*（ingest/lint/query/audit/curator…）
- core/agents/ —— 审查 agent + 内容处理 agent（registry.json 统一调度）
- core/hooks/ —— 钩子脚本 + registry.json（机械强制护栏）
- core/skills/_external/ —— 外部通用 skill（工程/创作/工具）

## 知识

- knowledge/framework-designs/ —— 通用框架设计文档（双层架构、ixxi 愿景）
- knowledge/learning/ —— 公开参考学习资料

## 样例与文档

- samples/ —— 最小可运行示例（虚构/占位数据，供判据验证与演示）
- docs/evolution/ —— 演化机制公开规则
- docs/guides/ —— 迁移 / 脱敏 / 分享操作指南
