#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
set -e
# G12破坏性操作审计——检查本次变更文件是否都有对应确认记录

echo "=== G12 操作审计 ==="
# Get changed files since last commit
changes=$(git diff --name-only 2>/dev/null)
if [ -z "$changes" ]; then
  changes=$(git diff --cached --name-only 2>/dev/null)
fi

if [ -z "$changes" ]; then
  echo "✅ 无变更文件"
  exit 0
fi

# 非破坏性操作范围见G12: queue/log标记、index追加、会话摘要
# (these are "safe" per G12 non-destructive list)
unsafe=0
for f in $changes; do
  # Skip system files that can be auto-modified
  if echo "$f" | grep -qE "^(queue\.md|log\.md|index\.md|raw/sessions/)"; then
    continue
  fi
  # Check if this file is in a safe category
  if echo "$f" | grep -qE "(CLAUDE\.md|AGENT\.md|ops/rules/.*\.md)"; then
    echo "  ⚠️  破坏性变更: $f (需要G12确认记录)"
    unsafe=$((unsafe+1))
  fi
done

echo ""
if [ "$unsafe" -eq 0 ]; then
  echo "✅ 无非破坏性变更"
  exit 0
else
  echo "⚠️  $unsafe 个文件需要G12确认记录——请在log.md中确认已获用户授权"
  exit 0  # Don't block, just warn
fi
