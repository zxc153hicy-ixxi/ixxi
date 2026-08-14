# 5 分钟上手

从零到跑通第一个 ingest。

## 1. 拿到 ixxi

```bash
git clone <your-ixxi-repo-url>
cd ixxi
```

## 2. 变成你自己的

```bash
# 建你的 personal/ 实例层（.gitignore 已排除，不随开源分发）
mkdir -p personal
```

## 3. 跑通第一个 ingest

按 framework 里的 kb-ingest skill 流程，跑通「入库 → 体检 → 检索」最小闭环：

- 入库：`framework/core/skills/ingest/SKILL.md`
- 体检：`framework/core/skills/lint/SKILL.md`
- 检索：`framework/core/skills/knowledge-query/SKILL.md`

## 判据自检

你的内容「换个陌生使用者还有用吗」？

- 有用 → 晋升 `framework/`
- 没用 → 留在 `personal/`

## 更多

- 能力契约：每个 skill 旁有 `capability.json`，声明 requires（需要什么 agent 能力）+ provides（提供什么能力）
- 演化机制：`framework/docs/evolution/`
