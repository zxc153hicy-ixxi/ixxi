# 新用户引导（5 分钟上手）

从「我拿到 ixxi」到「跑通第一个入库」，一步步照着做。

**你需要**：git、Python 3.10+、一个 Agent 环境（Claude Code / Codex / Hermes，本引导以 Claude Code 为例）。

---

## 第 1 步：拿到 ixxi

```bash
git clone <ixxi-repo-url>
cd ixxi
```

拿到的是 `framework/`（开源通用层）。你的个人数据还没有，所以下一步把它变成你自己的实例。

## 第 2 步：初始化（变成你自己的）

```bash
bash ixxi init
```

会问你 3 个问题：

1. **用哪个 Agent**（Claude Code / Codex / Hermes / 全部）—— 选你主用的
2. **数据放哪**（目录名，默认 `personal`）—— 个人数据层，不进 git
3. **是否启用 hooks 护栏**（默认启用）

脚本自动完成 4 件事：挂 upstream（以后 `git pull upstream` 拉框架更新）→ 生成 personal 骨架 → 按你选的 Agent 生成适配层 → 激活护栏。

## 第 3 步：跑通 demo（证明链路通）

用框架自带的演示数据跑一遍，确认没坏：

```bash
# 把演示笔记放进你的个人入库区
cp framework/samples/demo-note.md personal/raw/inbox/
```

然后在 Claude Code 里说 **「入库」** 或 **「ingest」**，触发 kb-ingest。

**预期结果**：`demo-note.md`（高效知识管理三原则）被提炼成 **3 条** wiki，而不是照搬原文。核对点见 `framework/samples/expected-result.md`。

接着说「体检」（kb-lint）看健康度、「这个怎么…」（kb-query）测检索——三个能力组成「入库 → 体检 → 检索」最小闭环。

## 第 4 步：换成你的真实数据

```bash
rm personal/raw/inbox/demo-note.md          # 清掉演示数据
cp 你的资料.md personal/raw/inbox/          # 放你的真实资料
```

再说「入库」。你的资料格式/主题/体量都和 demo 不同，遇到问题按 kb-ingest 的失败处理走。

之后三步「从 demo 到真实」的完整路径（数据替换 / 场景注册 / 写第一个 personal skill），见 [demo 到真实迁移指南](framework/docs/guides/demo到真实迁移指南.md)。

## 判据自检

你的内容「**换个陌生使用者还有用吗**」？

- 有用 → 晋升 `framework/`（走贡献流程）
- 没用 → 留在 `personal/`（默认）

## 遇到问题

- 报错码 `IXXI-E***` → 查 [错误码规范](framework/docs/guides/错误码规范.md)
- 不知道哪些能改 → [用户编辑模型](framework/docs/guides/用户编辑模型.md)
- 想了解能做什么 → [MVP 边界](framework/docs/guides/MVP边界.md)

## 更多

- 能力契约：每个 skill 旁有 `capability.json`，声明 requires（需要什么 agent 能力）+ provides（提供什么能力）
- 演化机制：`framework/docs/evolution/`
