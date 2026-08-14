# 预期 ingest 结果

> 把 `demo-note.md` 放进 raw/ 跑 kb-ingest 后，预期提炼出 3 条 wiki 条目（每条对应一个原则），而非照搬原文。

## 示例：提炼出的第一条

```markdown
---
tags: [知识管理]
status: active
confidence: high
summary: 单一事实源原则——同知识点只存一份，其余引用，避免复制导致漂移
---

# 单一事实源

## 主张
同一知识点只存一份，其余引用它，不复制多份。

## 为什么
复制导致更新时不知道改哪份，内容随时间漂移。

## 关联
- [[边记边提炼]]
- [[定期回看]]
```

## 预期核对点

跑完 kb-ingest 后自检：

1. **条数**：`demo-note.md` 提炼成 3 条（3 个原则），不是 1 条照搬
2. **frontmatter**：每条有 `tags` + `status` + `confidence` + `summary`（非重复标题）
3. **交叉引用**：3 条之间建立了 `[[双向链接]]`
4. **索引更新**：index.md 追加了 3 条入口
5. **git commit**：入库后有一次 commit（kb-ingest 硬闸门 step 7）

> 这就是「入库 → 体检 → 检索」最小闭环里的第一环。下一步跑 kb-lint（体检）、kb-query（检索）。
