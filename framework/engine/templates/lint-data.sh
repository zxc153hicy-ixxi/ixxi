#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
set -e
# Lint数据采集——输出结构化数据供LLM分析和判断
# 不写文件、不修改任何东西

S="$KB_ROOT"
echo "=== LINT_DATA_START ==="

# 1. CLAUDE.md行数
echo "CLAUDE_LINES: $(wc -l < "$S/CLAUDE.md")"

# 2. YAML格式 (rules/)
echo "YAML_BAD:"
for f in "$S/ops/rules/"*.md; do
  name=$(basename "$f")
  issues=""
  head -1 "$f" | grep -q "^---$" || issues="${issues}OPENING_MISSING "
  sed -n '2,15p' "$f" | grep -q "^---$" || issues="${issues}CLOSING_MISSING "
  for field in "tags:" "summary:" "status:" "confidence:"; do
    head -15 "$f" | grep -q "^$field" || issues="${issues}${field}_MISSING "
  done
  [ -n "$issues" ] && echo "  $name: $issues"
done | grep "." || echo "  ALL_OK"

# 3. Wikilink统计
echo "WIKILINK_ZERO:"
find "$S/engine" "$S/ops" "$S/knowledge" -name "*.md" -type f | while IFS= read -r f; do
  links=$(grep -o '\[\[.*\]\]' "$f" 2>/dev/null | wc -l)
  [ "$links" -eq 0 ] && echo "  $(echo $f | sed "s|$S/||")"
done | grep "." || echo "  ALL_OK"

# 4. Git健康
cd "$S"
last_commit_sec=$(($(date +%s) - $(git log -1 --format=%ct 2>/dev/null || echo 0)))
echo "GIT_LAST_COMMIT_HOURS: $((last_commit_sec / 3600))"
echo "GIT_UNTRACKED: $(git ls-files --others --exclude-standard 2>/dev/null | wc -l)"
echo "GIT_SIZE: $(du -sh .git 2>/dev/null | cut -f1)"

# 5. draft/under-review
echo "DRAFT_COUNT: $(grep -r "status: draft" "$S/ops/" --include="*.md" -l 2>/dev/null | wc -l)"
echo "UNDER_REVIEW_COUNT: $(grep -r "status: under-review" "$S/ops/" --include="*.md" -l 2>/dev/null | wc -l)"
echo "DEPRECATED_COUNT: $(grep -r "status: deprecated" "$S/ops/" --include="*.md" -l 2>/dev/null | wc -l)"

echo "=== LINT_DATA_END ==="
