# docs/evolution/ —— 演化机制（边界随使用演化）

「边界随使用演化」机制的公开规则。演化飞轮四步：**采集 → 候选 → 人工确认 → 归档**。

> 核心不变量：**I8** Telemetry 是决策信号，不是价值事实（usage ≠ value）；**I9** Critical Capability 不允许仅凭 last_used 自动归档。

## 一、演化飞轮四步

| 步 | 动作 | 工具 | 说明 |
|:--:|------|------|------|
| 1 采集 | 记录 capability 使用 | `record-usage.py <name>` | 每次 skill 被调用后记录 count++ / last_seen。由 kb-curator 在 skill 执行后自动调用 |
| 2 候选 | 输出 N 天未触发清单 | `stats-unused.py [--days N]` | 数据源 = 遥测文件 → capability.json last_used 兜底；从未触发 / ≥90 天标「归档候选」 |
| 3 人工确认 | 价值裁决 | 人 | 候选只是信号，最终保留/归档由人工裁决（usage ≠ value，高频不等于有价值、低频不等于没价值） |
| 4 归档 | 移除/降级 capability | `kb-do.sh` | 确认归档后走原子操作，同步 registry / 索引 |

## 二、遥测采集（I8）

- 遥测文件：`personal/data/sessions/skill-usage.json`（实例层，私有，不进 framework）
- 记录字段：`count` / `first_seen` / `last_seen`
- 采集职责：kb-curator 在 skill 执行后调用 `record-usage.py`，LLM 不手工维护此文件
- **纪律**：遥测只存 personal 本地，贡献包不含遥测（P1-6 隐私边界）

## 三、开放注册（R-REG 01-06）

1. 新实体开放注册（不设白名单门槛）
2. 受控词表校验（tag-taxonomy / capability requires 词表）
3. 频次驱动封装（同类 ≥2 次 → 提议封装）
4. 复用封装（同场景直接复用，不重复造）
5. 通用化晋升（「换个陌生使用者还有用吗」判据）
6. 贡献回流（用户自愿，禁止自动导出）

## 四、动态收敛（R-EVO 01-09）

1. 五阶段生命周期（draft → active → stable → deprecated → archived）
2. stale 软信号（长期未触发 → 归档候选，不自动归档）
3. 零引用硬信号（无引用 + 无使用 → 强候选）
4. 规则去重（本质相同 → 合并）
5. frontmatter 生命周期字段（status / lifecycle_class）
6. 阈值自适应（90 天等阈值参数化到实例）
7. 主动沉积（同类 ≥2 次 → 提议正/反模式）
8. 特例降级（通用吸收特例）
9. 使用遥测纪律（一切演化决策以遥测为输入，人工为裁决）

## 关联

- [[../guides/MVP边界]] —— 演化闭环的 MVP 边界
