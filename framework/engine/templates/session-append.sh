#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
set -e
# 会话追加——边聊边记，每完成一个重要操作即追加到当日会话文件
# 用法: session-append.sh "标题" "内容描述"

SESSION_DIR="$KB_ROOT/raw/sessions"
TODAY=$(date +%Y-%m-%d)
TITLE="${1:-未命名操作}"
CONTENT="${2:-无描述}"
TIMESTAMP=$(date "+%H:%M")

# 查找今日会话文件或创建
SESSION_FILE=$(ls "$SESSION_DIR/${TODAY}-"*.md 2>/dev/null | head -1)
if [ -z "$SESSION_FILE" ]; then
  SESSION_FILE="$SESSION_DIR/${TODAY}-会话.md"
  # 创建新文件+YAML
  cat > "$SESSION_FILE" << EOF
---
created: $TODAY
scene: 知识整理
project: 知识库管理
status: active
summary: ${TODAY}会话记录
type: 会话摘要
---

# ${TODAY} 会话记录

EOF
  echo "📝 新建: $SESSION_FILE"
fi

# 追加操作记录
cat >> "$SESSION_FILE" << EOF

## ${TIMESTAMP} · ${TITLE}

${CONTENT}
EOF

echo "✅ 已追加: ${TIMESTAMP} · ${TITLE} → $(basename $SESSION_FILE)"
