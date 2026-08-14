#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
# 脚本登记检查 — 挂载到 PostToolUse:Edit/Write
# 检测新建/修改脚本文件时，是否登记了 activation.md + index.md（确定性产物，纯机械检查）

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

# 只检查脚本文件（engine/scripts/ 或 ops/scripts/ 的 .py/.sh）
case "$CHANGED_FILE" in
  *engine/scripts/*|*ops/scripts/*)
    ;;
  *)
    exit 0
    ;;
esac

STEM=$(basename "$CHANGED_FILE" | sed 's/\.\(py\|sh\)$//')

# 检查 activation.md 有没有登记（脚本完整清单在 activation.md，index.md 是精选导航不列所有脚本）
if ! grep -q "$STEM" "$KB_ROOT/activation.md" 2>/dev/null; then
  echo ""
  echo "⚠️ 脚本登记缺失：$CHANGED_FILE"
  echo "   activation.md 无「$STEM」条目，请补登记"
fi

exit 0
