#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
# 正反模式登记检查 — 挂载到 PostToolUse:Edit/Write
# 检测新建/修改正反模式文件时：① scope 字段必填且匹配目录；② framework 无隐私标记；③ 登记 pattern-usage + 索引

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

# 只检查正反模式文件（非索引页），确定 scope + 索引位置
STEM=$(basename "$CHANGED_FILE" .md)
case "$CHANGED_FILE" in
  *framework-patterns/*)
    [ "$STEM" = "正模式索引" ] && exit 0
    KEY="patterns"; SCOPE="framework"; IDX="$KB_ROOT/framework/ops/framework-patterns/正模式索引.md"
    ;;
  *framework-anti-patterns/*)
    [ "$STEM" = "反模式索引" ] && exit 0
    KEY="antipatterns"; SCOPE="framework"; IDX="$KB_ROOT/framework/ops/framework-anti-patterns/反模式索引.md"
    ;;
  *system/patterns/*)
    [ "$STEM" = "正模式索引" ] && exit 0
    KEY="patterns"; SCOPE="personal"; IDX="$KB_ROOT/personal/system/patterns/正模式索引.md"
    ;;
  *system/anti-patterns/*)
    [ "$STEM" = "反模式索引" ] && exit 0
    KEY="antipatterns"; SCOPE="personal"; IDX="$KB_ROOT/personal/system/anti-patterns/反模式索引.md"
    ;;
  *)
    exit 0
    ;;
esac

MISSING=0

# ① scope 字段必填 + 匹配目录
ACTUAL_SCOPE=$(grep -m1 '^scope:' "$CHANGED_FILE" 2>/dev/null | sed 's/scope:[[:space:]]*//')
if [ -z "$ACTUAL_SCOPE" ]; then
  MISSING=1
  echo ""
  echo "⚠️ 正反模式缺 scope 字段：$CHANGED_FILE"
  echo "   请在 frontmatter 加 scope: $SCOPE（framework=通用 / personal=个人）"
elif [ "$ACTUAL_SCOPE" != "$SCOPE" ]; then
  MISSING=1
  echo ""
  echo "⚠️ scope 与目录不符：$CHANGED_FILE"
  echo "   目录要求 scope: $SCOPE，实际 scope: $ACTUAL_SCOPE"
fi

# ② framework 目录无隐私标记
if [ "$SCOPE" = "framework" ]; then
  if grep -q -E '29909|源质挽歌|D:/KnowledgeBase|d:/KnowledgeBase' "$CHANGED_FILE" 2>/dev/null; then
    MISSING=1
    echo "   framework 模式含隐私标记（29909/源质挽歌/旧库路径），应留 personal"
  fi
fi

# ③ pattern-usage.json 有没有对应条目（grep key，避免 bash 传中文给 python 的编码问题）
if ! grep -q "\"$STEM\":" "$KB_ROOT/personal/data/sessions/pattern-usage.json" 2>/dev/null; then
  MISSING=1
  echo "   pattern-usage.json 无「$STEM」条目，请补登记（count=0, last_used=null）"
fi

# ④ 索引有没有登记
if ! grep -q "\[\[$STEM\]\]" "$IDX" 2>/dev/null; then
  MISSING=1
  echo "   索引无「[[$STEM]]」条目，请补登记"
fi

exit 0
