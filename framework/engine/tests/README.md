# engine/tests —— ixxi 测试金字塔

回归可自动发现的目标防线（智谱风险 7.5：核心逻辑无回归护栏）。

## 运行

在仓库根 `/d/ixxi`：

```bash
python -m unittest discover -s framework/engine/tests -v
```

或（tests 目录在框架内相对可解析时）：

```bash
python -m unittest discover engine/tests
```

单文件运行：

```bash
python -m unittest framework.engine.tests.test_unit
```

要求：仅 Python 标准库（unittest / tempfile / importlib.util / io / contextlib），
**不引入 pytest**，无网络、无外部服务、无第三方依赖，测试彼此隔离、可重复。

## 三层金字塔

| 层 | 文件 | 范围 | 特性 |
|------|------|------|------|
| 单元 | `test_unit.py` | 核心纯函数 | 多而快，无文件系统副作用 |
| 集成 | `test_integration.py` | sync 流程 | tempfile 临时目录模拟 core/skills → 适配层，测试后清理 |
| e2e | `test_e2e.py` | 完整使用路径 | 模拟 init 骨架 + 复制 demo + 扫敏感信息，最慢最少 |

金字塔原则：底层单元测试多而快，越往上越少越慢。回归发生时单元层最先暴露，
定位成本最低；集成层验证跨模块组合（collect → sync → 校验）；e2e 层守住
「clone 下来能跑通最小闭环」的端到端底线。

## 覆盖内容

- **单元**：
  - `scan-sensitive` 6 类攻击面 `detect_*`（base64 解码执行 / 环境变量外泄 /
    .git/hooks 注入 / 依赖投毒 / 路径穿越 / 混淆代码），各含命中与不命中样例；
    另含 `scan_text` 的 PII 检测
  - `stats-unused` 日期筛选逻辑：`parse_date`（格式/非法输入）、
    `load_telemetry`（days_since 计算、_meta/非 dict 跳过、坏文件）、
    `main` 的 N 天筛选 → 「归档候选 / 保留」分类（30 天与 90 天阈值切换）
  - `sync-skills-to-claude` 的 `skill_name` / `collect_sources` / `sync` / `check_only` / prune
  - `sync-skills-to-hermes` 的 `ref_scripts` / `ref_rules` / `skill_description` /
    `collect_sources`（跳过分类级 SKILL.md）/ `build_index`
  - `check-skill-parity` 的 `check_p1`..`check_p6` 六项可达性断言
- **集成**：核心/skills（含外部 `_external/<分类>/`）→ `.claude/skills` 一级平铺
  sync 流程 + Hermes 命令索引生成，断言收集数 / 产物存在 / 内容一致
- **e2e**：init 生成 personal 骨架 → 复制 `framework/samples/demo-note.md` →
  跑 `scan-sensitive --repo` 通过；反证样例（private 数据藏密码）→ 扫描报失败

## 覆盖率目标

单元 + 集成层覆盖核心逻辑 ≥ 60%（按行计）；e2e 层不计入覆盖率。
可用 coverage.py（可选，非依赖）验证：

```bash
coverage run -m unittest discover -s framework/engine/tests
coverage report -m framework/engine/scripts/*.py
```

## 维护约定

- 不改生产脚本签名：测试用 `importlib.util.spec_from_file_location` 按文件加载脚本，
  对需要重定向的模块级路径常量（`SRC`/`DST`/`OUT`/`REPO`/`REPO_ROOT`）monkeypatch，
  用 `addCleanup` 恢复，避免测试间串扰、不触碰真实仓库。
- 所有临时文件走 `tempfile.TemporaryDirectory()`，测试结束自动清理。
- 新增 `detect_*` / 核心函数或改动筛选阈值时，同步补/改对应单元测试；
  新增脚本可参照现有文件补充测试。
- 生产脚本顶部 `sys.stdout.reconfigure(...)` 在加载时执行，测试运行环境需可写 stdout
  （本机 Python 3.10 控制台验证通过）。
