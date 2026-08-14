#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
set -e
# 知识库统计——页面分布+场景分布+目录完整性
S="$KB_ROOT"

echo "=== KB_STATS ==="
echo "DATE: $(date +%Y-%m-%d)"

# 页面分布
echo "PAGES:"
for dir in anti-patterns architecture creative decisions iterations patterns projects queries rules templates; do
  count=$(find "$S/ops/ $S/knowledge/ $S/engine/$dir" -name "*.md" -type f 2>/dev/null | wc -l)
  echo "  ops/$dir: $count"
done

# 场景分布
echo "SCENES:"
grep -rh "^scene:" "$S/ops/ $S/knowledge/ $S/engine/" --include="*.md" 2>/dev/null | sed 's/scene: //' | sort | uniq -c | sort -rn

# 目录完整性 vs activation
echo "DIR_CHECK:"
for dir in $(find "$S" -maxdepth 1 -mindepth 1 -type d -not -name ".*" | sed 's|.*/||' | sort); do
  if grep -q "$dir/" "$S/activation.md" 2>/dev/null; then
    echo "  OK: $dir"
  else
    echo "  MISSING_IN_ACTIVATION: $dir"
  fi
done

# Git概要
cd "$S"
echo "GIT_COMMITS: $(git log --oneline | wc -l)"
echo "GIT_TAGS: $(git tag | wc -l)"
echo "LOG_LINES: $(wc -l < log.md)"
echo "QUEUE_PENDING: $(grep -c '^\[ \]' queue.md 2>/dev/null || echo 0)"
echo "FEEDBACK_FILES: $(find raw/feedback -name '*.md' | wc -l)"
echo "SESSIONS_FILES: $(find raw/sessions -name '*.md' | wc -l)"
echo "=== STATS_END ==="
