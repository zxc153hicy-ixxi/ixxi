#!/bin/bash
# fix-inbox-clean.sh -- 清理 .inbox/ 过期文件和残留 .tmp
#
# 用法:
#   bash engine/scripts/fix-inbox-clean.sh --dry-run    # 预览
#   bash engine/scripts/fix-inbox-clean.sh --execute     # 执行清理
#   bash engine/scripts/fix-inbox-clean.sh --max-age 7   # 自定义过期天数

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
INBOX_DIR="$REPO_ROOT/.inbox"
MAX_AGE=7
DRY_RUN=true
EXECUTE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true ;;
    --execute) EXECUTE=true; DRY_RUN=false ;;
    --max-age) MAX_AGE="$2"; shift ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
  shift
done

if [ ! -d "$INBOX_DIR" ]; then
  echo "✅ .inbox/ 不存在，无需清理"
  exit 0
fi

echo "=== .inbox/ 清理 ==="
echo "目录: $INBOX_DIR"
echo "过期阈值: ${MAX_AGE} 天"
echo "模式: $([ "$DRY_RUN" = true ] && echo '预览' || echo '执行')"
echo ""

# 1. 清理残留 .tmp 文件
tmp_count=0
while IFS= read -r -d '' f; do
  if [ "$DRY_RUN" = true ]; then
    echo "[预览] 残留 .tmp: $f"
  else
    rm -f "$f"
    echo "[已删除] $f"
  fi
  ((tmp_count++))
done < <(find "$INBOX_DIR" -name "*.tmp" -print0 2>/dev/null || true)

# 2. 清理过期 .md 文件（>MAX_AGE 天未修改）
stale_count=0
while IFS= read -r -d '' f; do
  if [ "$DRY_RUN" = true ]; then
    echo "[预览] 过期文件: $f"
  else
    rm -f "$f"
    echo "[已删除] $f"
  fi
  ((stale_count++))
done < <(find "$INBOX_DIR" -name "*.md" -mtime "+${MAX_AGE}" -print0 2>/dev/null || true)

# 3. 清理空目录
empty_dir_count=0
if [ "$DRY_RUN" = false ]; then
  find "$INBOX_DIR" -type d -empty -delete 2>/dev/null || true
fi

echo ""
echo "=== 清理结果 ==="
echo "残留 .tmp: ${tmp_count} 个"
echo "过期 .md (>${MAX_AGE}天): ${stale_count} 个"
echo ""

if [ "$DRY_RUN" = true ]; then
  echo "💡 加 --execute 执行实际清理。"
else
  echo "✅ 清理完成。"
fi
