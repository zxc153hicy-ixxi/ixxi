#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
set -e
# 阶段自动检测 — 挂载到 PostToolUse (after /lint)
# 对比 skill 数 + wiki 页数 vs 阈值表，跨阶段时更新 _meta.stage

SKILL_DIR="$KB_ROOT/framework/core/skills"
WIKI_DIR="$KB_ROOT/personal/knowledge"
COUNTER_FILE="$KB_ROOT/personal/data/sessions/skill-usage.json"
# Windows python 需要 Windows 路径（Git Bash 的 /d/ 格式不识别）
COUNTER_FILE_WIN=$(cygpath -m "$COUNTER_FILE" 2>/dev/null || echo "$COUNTER_FILE")

SKILL_COUNT=$(find "$SKILL_DIR" -maxdepth 1 -type d | grep -v _archived | tail -n +2 | wc -l)
WIKI_COUNT=$(find "$WIKI_DIR" -name "*.md" -type f | wc -l)

# 阈值判断
STAGE="startup"
STAGE_LABEL="刚起步"

if [ "$WIKI_COUNT" -ge 80 ] || [ "$SKILL_COUNT" -ge 4 ]; then
  STAGE="in_use"
  STAGE_LABEL="在用了"
fi

if [ "$WIKI_COUNT" -gt 200 ] && [ "$SKILL_COUNT" -gt 10 ]; then
  STAGE="mature"
  STAGE_LABEL="用熟了"
fi

# 更新 JSON（只在变化时）
python -c "
import json
with open('$COUNTER_FILE_WIN', 'r+', encoding='utf-8') as f:
    data = json.load(f)
    old = data['_meta'].get('stage', '')
    if old != '$STAGE':
        data['_meta']['stage'] = '$STAGE'
        data['_meta']['stage_label'] = '$STAGE_LABEL'
        data['_meta']['stage_checked_at'] = '$(date +%Y-%m-%d)'
        data['_meta']['stage_reason'] = f'wiki={$WIKI_COUNT} skill={$SKILL_COUNT}'
        f.seek(0)
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.truncate()
        print(f'STAGE_CHANGED: {old} → $STAGE_LABEL')
" 2>/dev/null
