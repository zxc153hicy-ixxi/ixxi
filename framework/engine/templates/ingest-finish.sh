#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
set -e
# Ingest收尾——标记queue/追加log/git commit
# 用法: ingest-finish.sh "变更摘要" "log内容"

SUMMARY="${1:-未提供摘要}"
LOG_ENTRY="${2:-未提供log内容}"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")

cd "$KB_ROOT"

# 1. 标记queue中所有未完成的条目为[x]
# sed -i 在 macOS/BSD 语法不同（需 -i '' 备份后缀），改用临时文件+mv 的可移植写法
sed 's/^\[ \]/[x]/' personal/data/queue.md > personal/data/queue.md.tmp && mv personal/data/queue.md.tmp personal/data/queue.md

# 2. 追加log
echo "$TIMESTAMP | Ingest | $LOG_ENTRY" >> personal/data/log.md

# 3. git commit (显式文件列表，不用 add -A)
# personal/ 实例数据被 .gitignore 排除，只提交 framework/ 通用层变更
git add personal/data/queue.md personal/data/log.md 2>/dev/null || true
git add framework/ 2>/dev/null || true
git commit -m "Ingest: $SUMMARY" 2>&1

echo "✅ Ingest收尾完成"
echo "   Queue已标记 | Log已追加 | Git已提交"
