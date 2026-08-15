#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
set -e
# 检查模板是否过期（CLAUDE.md修改时间 vs 模板最后导出时间）

# stat 取 mtime 的可移植写法：Linux/GNU 用 -c %Y，macOS/BSD 用 -f %m
case "$(uname)" in
  Darwin|FreeBSD|NetBSD|OpenBSD) STAT_MTIME="stat -f %m" ;;
  *) STAT_MTIME="stat -c %Y" ;;
esac
KB_TIME=$($STAT_MTIME "$KB_ROOT/CLAUDE.md" 2>/dev/null)
TPL_TIME=$($STAT_MTIME "$KB_ROOT-Template/CLAUDE.md" 2>/dev/null)

if [ -z "$TPL_TIME" ]; then
  echo "⚠️  模板不存在或从未导出，需要执行 /export-template"
  exit 1
fi

if [ "$KB_TIME" -gt "$TPL_TIME" ]; then
  diff_sec=$((KB_TIME - TPL_TIME))
  diff_min=$((diff_sec / 60))
  echo "❌ 模板过期——CLAUDE.md 在 ${diff_min} 分钟前修改，模板未同步"
  echo "   需要执行: bash engine/templates/export-template.sh"
  exit 1
else
  echo "✅ 模板是最新的"
  exit 0
fi
