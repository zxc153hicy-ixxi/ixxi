#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
set -e
# 检查 session-notes.md 状态
SN="$KB_ROOT/session-notes.md"
if [ -f "$SN" ]; then
  size=$(wc -c < "$SN")
  if [ "$size" -gt 1 ]; then
    echo "⚠️  session-notes.md 有内容 ($size bytes)，上次会话可能未正常清空"
    exit 1
  else
    echo "✅ session-notes.md 已清空"
    exit 0
  fi
fi
