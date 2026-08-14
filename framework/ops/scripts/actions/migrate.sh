#!/bin/bash
# desc: 迁移文件/目录（移动+全库替换+残留验证，原子化）
# usage: kb-do migrate <旧路径> <新路径>
#
# 结构性变更完成定义：移动 → 全库替换旧引用 → 验证残留清零 → 才算完成。
# 用 git mv 保持跟踪，可 git 回滚。

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

OLD="${1:-}"
NEW="${2:-}"

if [ -z "$OLD" ] || [ -z "$NEW" ]; then
  echo "用法: kb-do migrate <旧路径> <新路径>"
  echo "示例: kb-do migrate old-dir new-dir"
  exit 1
fi

# 去掉首尾斜杠，统一格式
OLD="${OLD%/}"; NEW="${NEW%/}"

# 1. 移动（git mv 保持跟踪）
if [ -e "$REPO_ROOT/$OLD" ]; then
  mkdir -p "$(dirname "$REPO_ROOT/$NEW")"
  if git -C "$REPO_ROOT" mv "$OLD" "$NEW" 2>/dev/null; then
    echo "✅ 已移动: $OLD → $NEW"
  else
    mv "$REPO_ROOT/$OLD" "$REPO_ROOT/$NEW"
    echo "✅ 已移动（非 git mv）: $OLD → $NEW"
  fi
else
  echo "⚠️ 源不存在: $OLD（跳过移动，仅做引用替换）"
fi

# 2. 全库替换旧路径引用（.md/.py/.sh/.js，跳过历史记录）
COUNT=0
while IFS= read -r f; do
  case "$f" in
    */.git/*|*/raw/*|*/knowledge/archive/*|*/knowledge/learning/*) continue ;;
  esac
  sed -i "s|$OLD|$NEW|g" "$f" 2>/dev/null && COUNT=$((COUNT+1))
  echo "  ✅ 替换引用: ${f#"$REPO_ROOT"/}"
done < <(grep -rl "$OLD" "$REPO_ROOT" --include="*.md" --include="*.py" --include="*.sh" --include="*.js" 2>/dev/null || true)
echo "替换 $COUNT 个文件"

# 3. 验证残留清零
if grep -rl "$OLD" "$REPO_ROOT" --include="*.md" --include="*.py" --include="*.sh" --include="*.js" 2>/dev/null | grep -v -e '/\.git/' -e '/raw/' -e '/knowledge/archive/' -e '/knowledge/learning/' | head -1 >/dev/null; then
  echo "⚠️ 仍有残留引用，请用 check-stale-paths.py 手动检查"
else
  echo "✅ 残留清零"
fi

echo "📝 migrate 完成: $OLD → $NEW（索引页需手动同步）"
