---
tags: [schema]
status: active
summary: 场景注册表 schema——字段定义 + 状态机 + domain 受控词表机制。机制归 framework，数据行归 personal。
---

> **纯参考文档**：字段定义/状态机/domain 受控词表机制以本文档为准；**实现以 `check-scene-domain.py` 为准**（脚本仅做 scene/domain 与目录路径的一致性校验，不读取本 schema，本文件无程序化消费者）。

# 场景注册表 schema

> 机制（本文件）归 framework，数据行归 personal。新实例在此 schema 下登记自己的场景。

## 字段定义

| 字段 | 必填 | 说明 |
|------|:---:|------|
| 编号 | ✓ | S1、S2… 递增 |
| 场景名 | ✓ | 人类可读 |
| 状态 | ✓ | active / suspended / deprecated / archived |
| 场景描述 | ✓ | 这个场景做什么 |
| 主要目录 | ✓ | 场景数据落位 |
| 创建时间 | ✓ | first_seen |
| 关联入口 | 否 | 场景入口 wikilink |

## 状态机

| 状态 | 含义 | 迁移 |
|------|------|------|
| active | 活跃使用 | 默认 |
| suspended | 暂停（不活跃但保留） | active ↔ suspended |
| deprecated | 废弃（不再使用） | → archived |
| archived | 归档 | 终态 |

## domain 受控词表

每个场景声明其合法的 domain 值（受控），`check-scene-domain` 校验越界词并阻断提示补登。

| 场景 | domain 值 | 说明 |
|------|------|------|
| （实例自填） | （实例自填） | （实例自填） |

## 注册流程（R-REG-01/02）

新场景 → 追加一行 → 受控词表校验（check-scene-domain）→ 完成注册。
