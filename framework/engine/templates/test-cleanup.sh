#!/bin/bash
set -e
KB_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# 测试文件自动清理
# 读取 .test-manifest → 删除所有标记文件 → 清空清单
MANIFEST="$KB_ROOT/.test-manifest"

if [ ! -f "$MANIFEST" ]; then
  echo "✅ 无测试文件需清理"
  exit 0
fi

echo "=== 测试文件自动清理 ==="
count=0
while IFS= read -r f; do
  [ -z "$f" ] && continue
  # Skip lines starting with # (保留标记)
  if echo "$f" | grep -q "^#"; then
    echo "  ⏭️  保留: ${f#\# }"
    continue
  fi
  # 安全闸门：路径必须在 KB_ROOT 范围内
  real_f=$(realpath "$f" 2>/dev/null || echo "$f")
  case "$real_f" in
    "$KB_ROOT"/*)
      if [ -e "$f" ]; then
        if [ -d "$f" ]; then
          rm -rf "$f" && echo "  🗑️  目录: $f"
        else
          rm -f "$f" && echo "  🗑️  文件: $f"
        fi
        count=$((count+1))
      else
        echo "  ⚠️  不存在: $f"
      fi
      ;;
    *)
      echo "  🚫 拒绝(路径不在KB_ROOT内): $f"
      ;;
  esac
done < "$MANIFEST"

# Clear manifest
> "$MANIFEST"
echo ""
echo "✅ 已清理 $count 项，清单已清空"
