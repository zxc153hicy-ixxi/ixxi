#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
# 规则登记检查 — 挂载到 PostToolUse:Edit/Write
# 检测新建/修改规则文件时，是否登记了 index.md（确定性产物，纯机械检查）

CHANGED_FILE="${1:-}"

# 解析文件路径（$1 或 stdin JSON，兼容 Codex）
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

# 只检查规则文件（ops/rules/ 的 .md）
case "$CHANGED_FILE" in
  *ops/rules/*.md)
    ;;
  *)
    exit 0
    ;;
esac

STEM=$(basename "$CHANGED_FILE" .md)

# 检查 index.md 有没有登记
if ! grep -q "$STEM" "$KB_ROOT/index.md" 2>/dev/null; then
  echo ""
  echo "⚠️ 规则登记缺失：$CHANGED_FILE"
  echo "   index.md 无「$STEM」条目，请补登记"
fi

exit 0
