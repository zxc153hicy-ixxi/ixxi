# samples/

最小可运行示例（虚构数据），供「判据验证」与「演示」使用，非真实个人数据。

## 内容

- `demo-note.md` —— 一篇虚构的演示笔记（raw 输入，供 kb-ingest 演示）
- `expected-result.md` —— 预期 ingest 结果（提炼成 3 条 wiki 的核对点）

## 用途

1. 干净环境 clone 后，用 `demo-note.md` 从零跑通 kb-ingest → kb-lint → kb-query，验证「无个人数据下可独立运行」。
2. 作为「demo → 真实使用」的起点，见 `framework/docs/guides/demo到真实迁移指南.md`。
