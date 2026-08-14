---
tags: [规则]
status: active
confidence: high
summary: personal 隔离规范——个人数据层永不进公开仓库；sync/push 前置检查；误推处置（filter-repo/删remote/通知）
created: 2026-08-14
updated: 2026-08-14
---

# personal 隔离规范

Task 1.4「personal 隔离」护栏（防个人数据泄露，智谱风险 3.5）。

## 一、目标与边界

- `personal/`（默认个人目录，init Q2 可自定义目录名）是**个人资产层**：
  数据 + 个人绑定 + 运行状态（用户画像、场景注册、feedback、sessions、queue/log 等）。
- 个人资产层**绝不允许**进入任何公开仓库。
- 本规范与配套检查脚本 `engine/scripts/check-personal-sync.py` 组成 sync/push 前置护栏。
- `.gitignore` 已排除 `personal/`（及自定义目录名），是**第一道防线**；本规范是**第二道**
  ——覆盖 `git add -f`、误配 remote、`git push --force` 等绕过 .gitignore 的路径。

## 二、核心规则

1. **personal/ 永不进公开仓库**
   - 默认个人目录 `personal/`、init 自定义个人目录名均视为个人层。
   - 任何人不得将个人层文件 `git add -f` 强推、或手动挪进 framework 后提交。

2. **sync / push 前置检查（强制）**
   - 任何 git sync / push 操作前，必须先跑：
     ```bash
     python framework/engine/scripts/check-personal-sync.py
     ```
   - 脚本判定「个人目录有内容 + 存在非本地 remote」→ **阻断**，退出码 2，禁止继续。
   - 本地 remote（`file://`、绝对/相对本地路径、盘符路径）→ 放行（本地同步不构成泄露）。
   - 不确定 remote 时按公开保守处理：未知 host 一律视作公开，宁可多拦截不放过。

3. **自定义个人目录名**
   - init 时自定义的目录名会追加为 `.gitignore` 中的 `xxx/` 行；
     脚本从 `.gitignore` 顶层目录条目自动识别，无需手动配置。

## 三、检查脚本用法

```bash
# 检查 + 阻断（默认）：危险组合时非零退出码阻断 sync/push
python framework/engine/scripts/check-personal-sync.py

# 只检查不阻断：始终退出 0，供审计/调试
python framework/engine/scripts/check-personal-sync.py --dry-run

# 指定仓库根目录
python framework/engine/scripts/check-personal-sync.py --repo <仓库根目录>
```

退出码：`0`=放行；`2`=阻断（个人内容 + 非本地 remote）；`1`=执行错误。
阻断时输出「personal 内容不能同步到 public remote！」并给出处置指引。

## 四、误推的处置

已把个人内容推进公开仓库时的处置顺序：

1. **立即止血**
   - 立即 `git remote remove origin`（或删除对应公开 remote），停止一切 push。
   - 涉及托管平台时先设置**私有**或直接删除仓库，阻断新拉取。
2. **历史清理（filter-repo）**
   - 用 `git filter-repo`（或 `filter-branch`）从**全部历史**中剥离个人层：
     ```bash
     git filter-repo --path personal/ --invert-paths
     ```
   - 清理后 `git remote add origin <新/私有URL>` 重新推送。
3. **更换凭据**
   - 若泄露过 token/密钥/个人标识，立即轮换，不止于删文件。
4. **通知**
   - 若仓库曾被他人 clone/fork：**通知相关方**（托管平台、协作者）该仓库含个人敏感数据，
     建议删除 fork / 副本，避免二次扩散。
5. **记录**
   - 在个人层 log 中记录误推事件（时间、内容范围、处置动作），纳入反模式沉淀。

> 说明：`git filter-repo` 需独立安装（`pip install git-filter-repo`），
> 属于零配置知识库之外的第三方工具，误推时按上述流程安装使用。

## 五、边界与兜底

- **本地 remote 放行**：`file://`、`/…`、`./…`、`../…`、`~/…`、`C:\…` 视为本地同步，不构成泄露。
- **未知 host 保守阻断**：非本地 remote 但 host 不在已知公开列表（github/gitlab/gitee/bitbucket/codeberg 等）
  时，按公开保守处理并标注「未识别host」。
- **无 remote**：无 remote 不构成推送风险，放行。
- **无个人内容**：个人目录不存在或为空，无泄露面，放行。
- **hook 化**：可将检查脚本接入 git pre-push hook，push 前自动强制校验
  （参考 `core/hooks/git/`）。

## 相关

- `engine/scripts/check-personal-sync.py`（本护栏脚本，零第三方依赖）
- `../engine/scripts/scan-sensitive.py`（敏感信息扫描，配合使用）
- `编码原则.md`（脚本编码约束）
