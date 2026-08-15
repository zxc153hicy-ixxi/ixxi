# Changelog

> **人读**：看每个版本改了什么。**LLM 读**：定位当前版本 + 判断这版动了哪一层。
> 格式参考 Keep a Changelog，版本号 semver，与 git tag 一一对应。

## [Unreleased]

### 新增

- **kb-load 加载入口**：说「加载 ixxi」触发，读契约 + 首次弹 onboarding 引导（是什么/作用/怎么用）+ 汇报版本/能力/待办
- **冷启动引导**：仓库根 CLAUDE.md/AGENTS.md/HERMES.md 由 sync-agent-md 从 AGENT.md 生成（完整契约，clone 即有，契约内「冷启动引导」段引导跑 init）+ install.sh 全局装（任意目录加载）
- **待办追踪（甲+乙混合）**：未落地清单 = 唯一 backlog，登记约定 + 可选触发条件（`github_remote` 自动判断「现在可做」）+ kb-load 加载时汇报待办计数 + G21 待办必登记

### 修复

- **适配层产物目录统一到仓库根**：5 个 sync 脚本 DST + sync-agent-md + .gitignore 同步改，Claude/Codex 各 Agent 冷启动能扫到 kb-*（原误放 framework/ 导致冷启动读不到）

### G 层修改确认

- ✅ 已确认（2026-08-15）：G21 待办必登记 + 冷启动引导段 + 引擎特定声明章节（用户逐条确认保留）

## [0.1.2] - 2026-08-15

### 新增

- **架构文档**（`framework/docs/架构文档.md`）：分层总览 + 目录/重要文件详解 + 二次开发路径，面向基于 ixxi 做二次开发的开发者
- 贡献回流流程补「版本号由维护者统一递增，贡献者不自带版本号」

## [0.1.1] - 2026-08-15

### 新增

- **版本号机制**：单一版本号 = git tag（semver 三段式），CHANGELOG 人机共读，`version-check.sh` 校验 CHANGELOG ↔ git tag 一致；防混乱三层（规范 semver 递增规则 + pre-commit CHANGELOG↔tag 提醒 + 会话收尾兜底）
- **能力可执行性验证**（不变量 I2/I3/I4）：`capability.json` 补 `tier`（full/reader-only）、`core/agents/supports.json` 声明各 agent 契约子集、`verify-capability.py` dry-run 验证「声明 == 实际」
- **演化飞轮 + telemetry**（I8）：`record-usage.py` 采集使用、`stats --unused` 候选、`docs/evolution/` 四步闭环规则
- **能力契约补全**：`lifecycle_class`（I9，critical 禁止自动归档）、`resources` 补齐、`gen-resources.py`/`gen-lifecycle.py`
- **演化阈值配置化**：`engine/config/evolution-config.yaml`（stale/draft/archive 阈值参数化）
- **遥测隐私声明**：遥测只存 personal 本地、不进贡献包
- **DCO 强制**：`commit-msg` 钩子校验 Signed-off-by
- **判据三问勾选** + PR 审查抽查 + 原创性检查（贡献回流流程）
- 错误码接入 3 处（parity/sync/lint，E202/E311/E201）

### 修复

- **pre-commit 路径 bug**：KB_ROOT 用 `git rev-parse`、engine/scripts 补 `framework/` 前缀（护栏从静默失效恢复生效）
- **护栏 F 误报**：正则排除 URL（`://`）、SKIP_DIRS 补适配层目录
- bandit `shell=True` → `shlex.split` + `shell=False`
- git 索引漂移清理（15 个适配层 capability.json 移除跟踪）
- 分层漏网清除（13MB 语料 + 网络安全预案 + 个人化路径）

### 变更

- `version-check` 停用（版本机制未建立前会误阻断），本版重写接入

## [0.1.0] - 2026-08-14

### 新增

- **能力契约**：`capability.json` schema v1.0.0，72 个 capability（15 管理 + 57 外部）
- **ixxi init** 一键脚本（问 3 问题 + 挂 upstream + personal 骨架 + sync + hooks）
- **neutral 化**：能力源迁入 `core/`（消除 `.claude/` 语义污染，不变量 I1）
- 5 个 sync 脚本（Claude/Codex/Hermes 适配层生成）+ `check-skill-parity` 六项断言
- 安全工具链：`scan-sensitive` 6 类攻击面 + malicious-samples 回归夹具
- 错误码规范（IXXI-E 六段）
- 迁移工具（migrate-tool + schema-migrate）
- 测试金字塔（59 tests）
- 场景注册表 schema 切分（机制 framework / 数据 personal）

### 变更

- 双仓库物理隔离 → **单目录 + 内部分层 + git 隔离**（framework 开源 / personal 私有）
- 老库数据分两层转移（通用 → framework，个人 → personal）

---

## 版本号约定

- **单一事实源 = git tag**（semver）。不在 AGENT.md 标题、设计文档里再写版本号（避免 [[多套版本号并存]] 反模式）。
- `capability.json` 的 `version` 是**对象级**（不变量 I10），管单个能力契约，与框架版本无关，不混。
- 每个版本改什么：看本文件。历史逐条流水：`git log`。
