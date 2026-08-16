#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
set -e
# 废弃搬家提示 — 挂载到 PostToolUse:Edit
# 检测到 status→deprecated 的文件仍在活跃目录时，输出提示

CHANGED_FILE="${1:-}"

# Codex 适配：PostToolUse 输入为 stdin JSON（snake_case），从 tool_input 解析文件路径
if [ -z "$CHANGED_FILE" ] || [ ! -f "$CHANGED_FILE" ]; then
  CHANGED_FILE=$(python -c "import sys,json
try:
    d=json.load(sys.stdin)
    ti=d.get('tool_input',{})
    print(ti.get('file_path') or ti.get('path') or '')
except Exception:
    print('')" 2>/dev/null)
fi

if [ -z "$CHANGED_FILE" ] || [ ! -f "$CHANGED_FILE" ]; then
  exit 0
fi

# 检查文件是否在 ops/rules/ 或 ops/anti-patterns/ 下且含 deprecated
if echo "$CHANGED_FILE" | grep -qE "(framework/ops/rules|personal/system/(rules|anti-patterns))/"; then
  if grep -q "status: deprecated" "$CHANGED_FILE" 2>/dev/null; then
    DIR=$(dirname "$CHANGED_FILE")
    echo ""
    echo "💡 检测到废弃文件仍留在活跃目录: $CHANGED_FILE"
    echo "   建议移至: personal/knowledge/archive/$(basename "$DIR")/"
  fi
fi
