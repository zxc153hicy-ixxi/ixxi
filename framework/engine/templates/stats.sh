#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
set -e
# 知识库统计——页面分布+场景分布+目录完整性
S="$KB_ROOT"

echo "=== KB_STATS ==="
echo "DATE: $(date +%Y-%m-%d)"

# 页面分布（ixxi 结构：framework 通用层 + personal 实例层）
echo "PAGES:"
for dir in "framework/ops/rules" "personal/system/rules" "personal/system/patterns" "personal/system/anti-patterns" "personal/knowledge/projects" "personal/knowledge/learning" "personal/knowledge/archive" "personal/system/queries"; do
  count=$(find "$S/$dir" -name "*.md" -type f 2>/dev/null | wc -l)
  echo "  $dir: $count"
done

# 场景分布
echo "SCENES:"
grep -rh "^scene:" "$S/framework/" "$S/personal/" --include="*.md" 2>/dev/null | sed 's/scene: //' | sort | uniq -c | sort -rn

# 目录完整性 vs activation（framework 操作入口注册表）
echo "DIR_CHECK:"
for dir in $(find "$S" -maxdepth 1 -mindepth 1 -type d -not -name ".*" | sed 's|.*/||' | sort); do
  if grep -q "$dir/" "$S/framework/activation.md" 2>/dev/null; then
    echo "  OK: $dir"
  else
    echo "  MISSING_IN_ACTIVATION: $dir"
  fi
done

# Git概要
cd "$S"
echo "GIT_COMMITS: $(git log --oneline | wc -l)"
echo "GIT_TAGS: $(git tag | wc -l)"
echo "LOG_LINES: $(wc -l < personal/data/log.md)"
echo "QUEUE_PENDING: $(grep -c '^\[ \]' personal/data/queue.md 2>/dev/null || echo 0)"
echo "FEEDBACK_FILES: $(find personal/data/feedback -name '*.md' | wc -l)"
echo "SESSIONS_FILES: $(find personal/data/sessions -name '*.md' | wc -l)"
echo "=== STATS_END ==="
