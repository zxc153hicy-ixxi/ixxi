---
name: kb-agent-curator
description: Use when managing review agents or running multi-perspective audits. Triggers on "agent" "审查" "多视角" "review".
---

# kb-agent-curator

## Overview
agent 管家：管理审查 agent 的注册、调度、进化、退役。与技能系统 curator 共享生命周期判断。

## Quick Reference

### 当前 agent（10 审查 + 5 内容处理 = 15，见 registry.json）

| 组 | agent | 阶段 | 查什么 |
|------|------|:---:|------|
| ops | security-agent | 刚起步 | 敏感信息/权限 |
| ops | quality-agent | 刚起步 | 格式/结构/Lint |
| ops | pruner-agent | 在用了 | 重复/过期/冗余 |
| ops | mediator-agent | 在用了 | 矛盾/冲突 |
| user | userview-agent | 刚起步 | 大白话/可读性 |
| user | profile-agent | 在用了 | 画像对齐 |
| user | learning-agent | 用熟了 | 学习效果 |
| design | architect-agent | 用熟了 | 架构/路由 |
| design | forecaster-agent | 用熟了 | 预测/建议 |
| design | data-agent | 用熟了 | 统计/趋势 |

### 自适应部署

| 阶段 | 跑哪些 | 什么时候 | 模型 |
|------|:---:|------|------|
| 刚起步 | 3（安全+质量+用户视角） | 手动或 /ingest 后提议 | 最便宜 |
| 在用了 | 6（+精简+调解+画像） | 每3次 /lint 自动提议 | 便宜 |
| 用熟了 | 10 全部 | 每次 /lint --full 自动跑 | 便宜 |

### 动态提示词组装

角色文件（~20行）只定义「我是谁」——身份、视角、约束。curator 跑 agent 时自动拼接完整审查提示词：

```
[角色文件内容]         ← 我是谁、查什么
[操作上下文]           ← 当前 KB 状态（wiki页数/skill数/阶段/最近改动）
[具体任务]             ← 本次审查范围（全量/增量/指定目录/指定类型）
[输出格式]             ← 统一的结构化报告模板
[参考文件列表]          ← 需要读哪些文件
```

这样设计的好处：
- 角色文件保持简洁，易于维护
- curator 根据当前状态动态调整审查范围
- 同一个角色文件可以用于不同审查场景（全量/增量/专项）
- 参考 Hermes background_review 的 prompt 拼接模式

### 动态视角生成

curator 读 `knowledge/projects/知识库管理/queries/审计提示词-第三方.md` → 提取视角列表 → 对比 registry.json 已有 agent → 缺失视角动态拉起临时 agent。

**流程**：
1. 读审计提示词 → 提取 `## 预置视角` 下列出的所有视角名
2. 读 registry.json → 已有 agent 的 group/stage 字段构成已覆盖集合（registry 无 perspective 字段，用 group/stage 替代）
3. 缺失 = 审计视角 - 已覆盖
4. 每个缺失视角 → 用角色模板动态拼接提示词 → 跑临时 agent
5. 结果写入 `knowledge/projects/知识库管理/queries/agent-temp-<视角>-<日期>.md`
6. 写入 registry.json `temporary_agents` 记录（含 prompt + report 路径 + run_count）

**跨会话恢复**：curator 启动时读 `temporary_agents`，`run_count >= 3` → 提议注册为永久 agent。

### 进化机制

每次 agent 出报告，用户只需回复：接受/拒/漏了X
- 准确率 <80% 连续5次 → 自动优化提示词
- 准确率 <60% 连续3次 → 提议退役
- 某问题被漏3次 → 追加检查项
- 某问题被拒3次 → 标记低置信度

### 硬闸门
- agent 只给读权限（Read/Grep/Glob），不给写
- 用便宜模型，不占主会话上下文
- 只归档不删除（参考 Hermes curator 设计）

## 降级
SKILL 加载失败时，直接读取：`core/agents/registry.json` + 各 agent 文件
