#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
# 会话摘要 YAML 校验 — 挂载到 PostToolUse:Edit/Write
# 检测写入 session 文件时，YAML 是否含 status + summary（G2 要求，纯机械检查）

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

# 只检查 session 文件（raw/sessions/ 的 .md，排除索引页）
case "$CHANGED_FILE" in
  *raw/sessions/*.md)
    ;;
  *)
    exit 0
    ;;
esac

STEM=$(basename "$CHANGED_FILE" .md)
[ "$STEM" = "会话摘要索引" ] && exit 0

# 检查 YAML 是否含 status + summary
MISSING=""
grep -q "^status:" "$CHANGED_FILE" 2>/dev/null || MISSING="$MISSING status"
grep -q "^summary:" "$CHANGED_FILE" 2>/dev/null || MISSING="$MISSING summary"

if [ -n "$MISSING" ]; then
  echo ""
  echo "⚠️ 会话摘要 YAML 缺失字段：$CHANGED_FILE"
  echo "   缺：$MISSING（G2 要求必含 status + summary）"
fi

exit 0
