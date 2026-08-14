---
name: kb-session-close
description: Use when session is ending or the user says "结束" "关闭" "再见" "不记了" "今天就这样".
---

# kb-session-close

## Overview
聊完天了帮你收尾：看看你夸过或吐槽过什么、要不要存起来、有没有忘了提交的改动，三件事一次搞定。
技术说明：回溯反馈 → 确认入库 → 写入 sessions/ → 收尾三件套（git commit / 清理 / 归档）。

## Quick Reference

### 反馈收集
| 反馈类型 | 处理 |
|------|------|
| 口述评价 | 回显确认 → 写入 `raw/feedback/` |
| 书面反馈 | 直接引用原文 → 写入 `raw/feedback/` |
| 模糊评价 | 先追问再写入（目标/范围/程度/对比） |
| 无回应 | 仅追加 sessions/，不提炼正/反模式 |

### 收尾流程
| 步骤 | 动作 |
|:---:|------|
| 1 | 回溯会话中所有评价 → 逐条展示确认。同时扫描 `raw/sessions/kb-query-log.jsonl`（如存在），列出 `feedback: pending` 的问答，询问用户快速评价（最多提醒 3 次，之后标记 `expired`） |
| 2 | 用户确认「入库」→ 生成会话摘要 |
| 3 | 写入 `raw/sessions/` → 校验 YAML（status+summary） |
| 4 | 收尾三件套：git commit / 污染清理 / 无遗漏 |
| 5 | 基于正反模式+会话内容，主动提议哪些可写入用户画像 → 用户确认后写入 |

### 子任务完成时
- 回看 TodoWrite 全局清单
- 有未完成项 → 主动提醒 → 等确认
- 全部完成 → 触发收尾流程

## 硬闸门
- **G13**：收到会话结束信号 → 必须先检查反馈收集，禁止跳过
- **G2**：未收到人类明确确认的反馈 → 不得进入 `raw/feedback/`
- 模糊评价必须先追问，禁止猜测

## 例外
- 用户说「今天就这样」「不记了」→ 仅追加 sessions/ 摘要，标注 `[跳过反馈收集]`

## 降级
SKILL 加载失败时，直接读取：`ops/rules/反馈闭环流程.md` + `ops/rules/会话收尾检查.md`
