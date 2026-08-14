---
tags: [指南, schema, 版本管理]
status: active
confidence: high
summary: schema 版本规范——可迁移对象（skill/规则/capability.json）的 version 字段格式（semver）、version_of/superseded_by/replaces 生命周期、逐版本迁移策略与工具用法
created: 2026-08-14
---

# schema 版本规范

> 对应不变量 **I10：可迁移对象必须有 `version` + `schema` + `migration strategy`**。
> 机制（本文件）归 framework，数据行归 personal。本规范约束 personal/ 下所有 skill、规则文件与 capability.json。

## 适用范围

凡属于"可迁移对象"（随框架升级需跟随变更的资产）的文件，必须携带版本元数据：

| 对象 | 载体 | version 字段位置 |
|------|------|------|
| skill 指令 | `personal/**/SKILL.md` 等 `.md` | YAML frontmatter `version` |
| 规则文件 | `personal/**/*.md`（规则类） | YAML frontmatter `version` |
| 能力契约 | `personal/**/capability.json` | JSON 顶层 `version` |

非迁移对象（`assets/`、`references/`、`media/` 下的参考材料）**不要求** version 字段，迁移工具默认跳过。

## version 字段格式

- **格式**：语义版本（semver）`X.Y.Z`，如 `"1.0.0"`。允许前置 `v`（`v1.0.0`）。
- **类型**：YAML 中必须用双引号包裹（`version: "1.0.0"`），避免 `1.0` 被解析为浮点数；JSON 中为字符串值 `"version": "1.0.0"`。
- **含义**：`X` 主版本（schema 不兼容变更，需迁移）／`Y` 次版本（兼容新增字段）／`Z` 修订（修复/说明）。
- **缺失即 v0**：无 `version` 字段的对象视为 v0，属于待迁移对象。
- **与整体框架版本的关系**：对象级 schema 版本独立于框架整体版本号（`AGENT.md` 版本），互不绑定。

当前 schema 最新版本：**v1（`1.0.0`）**。框架侧统一以 `framework/engine/scripts/schema-migrate.py` 中的 `LATEST_SCHEMA` 为唯一事实源。

## 生命周期字段

一个版本链内的对象通过三个字段表达"谁取代谁"，构成可追溯的版本生命线：

| 字段 | 类型 | 语义 | 何时设置 |
|------|------|------|------|
| `version_of` | 字符串（人类可读全称） | "这个对象是什么东西的版本"（不含版本号） | 创建/迁移时设置，同链所有版本取值完全一致 |
| `superseded_by` | wikilink | 本对象被哪个新版取代 | 旧版被取代时设置，同时 `status: superseded` |
| `replaces` | wikilink | 本对象取代了哪个旧版 | 新版创建时设置 |

状态机：

```
active（当前生效） → 被新版取代 → superseded（保留 superseded_by 指向新版）
                                    → 清理/归档 → archived（终态）
```

- `version_of` 取值规范见 [[ops/rules/命名规范|命名规范]] 二、Frontmatter 元数据（禁止缩写、禁止含版本号、同链同值）。
- 对 skill：`version_of` 用 frontmatter 的 `name`（如 `my-skill`）；对 capability.json：用 `id`；对规则文件：用文件名主干。
- 生命周期一致性由 `/lint` 检查项 #17（`superseded_by`/`replaces` 断链）与 #18（版本状态不一致）保障。

## 迁移策略

**原则：schema 升级不得破坏用户资产。** 每次升级只增不删不改已有字段；同一对象至多补字段，绝不重写正文。

### 规则

1. **每一条版本变更必须提供迁移函数**，登记在 `schema-migrate.py` 的 `MIGRATIONS` 与 `_MIGRATORS` 中。
2. 迁移函数必须**幂等**：对已是最新版本的对象重复执行不产生任何改动。
3. 升级 v1→v2 的扩展方式（`MIGRATIONS[version_from] -> {to}`，函数按 kind 注册）：

   ```python
   MIGRATIONS = {
       "0": {"to": "1.0.0"},   # v0 → v1：补 version + version_of
       "1": {"to": "2.0.0"},   # 示例：v1 → v2
   }
   _MIGRATORS = {
       "md": {"0": _migrate_md_v0, "1": _migrate_md_v1},
       "capability": {"0": _migrate_capability_v0, "1": _migrate_capability_v1},
   }
   ```

4. **先 dry-run 后 execute**：任何迁移必须先以 `--dry-run` 列出计划核对，确认无误后再 `--execute`。
5. **只允许前向迁移**：工具只识别低于 `LATEST_SCHEMA` 的版本并向上迁移；高于最新版的版本一律跳过并提示（可能是手动升级，禁止覆盖）。

### 工具用法

```bash
# 扫描 personal/（默认根目录），列出迁移计划，不写入
python framework/engine/scripts/schema-migrate.py

# 扫描指定目录（dry-run）
python framework/engine/scripts/schema-migrate.py --root <目录>

# 实际迁移
python framework/engine/scripts/schema-migrate.py --root <目录> --execute

# 供 hook / 其他工具消费的 JSON 输出
python framework/engine/scripts/schema-migrate.py --root <目录> --execute --json
```

`--execute` 的行为：

| 对象状态 | 动作 |
|------|------|
| 无 `version`（v0），含 frontmatter | frontmatter 顶部补 `version: "1.0.0"` + `version_of: "<来源>"` |
| 无 frontmatter | 前置新 frontmatter 块（同上两字段），正文原样保留 |
| `version` 缺失的 capability.json | JSON 顶层补 `"version"` + `"version_of"` |
| `version >= 1.0.0` | 跳过（已最新，含手动升级的更高版本） |

### 升级操作流程

1. 在 `schema-migrate.py` 中把 `LATEST_SCHEMA` 改为新版本，并在 `MIGRATIONS`/`_MIGRATORS` 登记新迁移函数。
2. 更新本规范（version 字段、生命周期表、迁移策略）与框架侧 schema 文档。
3. 以 `--dry-run` 生成迁移计划，人工核对清单。
4. `--execute` 执行迁移。
5. 复验：再次 `--dry-run` 应显示"待迁移（0）"，抽查代表性文件确认字段已补且正文未变（验证驱动完成，G20）。

## 回滚

迁移只做"补字段"，不删除任何已有内容，因此回滚 = 手动移除新补的 `version`/`version_of` 字段即可。如需更稳妥，`--execute` 前可用 `git` 提交当前状态作为恢复点。
