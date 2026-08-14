#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
# 正反模式登记检查 — 挂载到 PostToolUse:Edit/Write
# 检测新建/修改正反模式文件时，是否登记了 pattern-usage + 索引（确定性产物，纯机械检查）

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

# 只检查正反模式文件（非索引页）
STEM=$(basename "$CHANGED_FILE" .md)
case "$CHANGED_FILE" in
  *ops/patterns/*)
    [ "$STEM" = "正模式索引" ] && exit 0
    KEY="patterns"; IDX="$KB_ROOT/ops/patterns/正模式索引.md"
    ;;
  *ops/anti-patterns/*)
    [ "$STEM" = "反模式索引" ] && exit 0
    KEY="antipatterns"; IDX="$KB_ROOT/ops/anti-patterns/反模式索引.md"
    ;;
  *)
    exit 0
    ;;
esac

MISSING=0

# 检查 pattern-usage.json 有没有对应条目（grep key，避免 bash 传中文给 python 的编码问题）
if ! grep -q "\"$STEM\":" "$KB_ROOT/raw/sessions/pattern-usage.json" 2>/dev/null; then
  MISSING=1
  echo ""
  echo "⚠️ 正反模式登记缺失：$CHANGED_FILE"
  echo "   pattern-usage.json 无「$STEM」条目，请补登记（count=0, last_used=null）"
fi

# 检查索引有没有登记
if ! grep -q "\[\[$STEM\]\]" "$IDX" 2>/dev/null; then
  MISSING=1
  echo "   索引无「[[$STEM]]」条目，请补登记"
fi

exit 0
