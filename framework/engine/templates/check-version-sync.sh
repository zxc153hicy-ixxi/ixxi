#!/bin/bash
# check-version-sync.sh — 检查 CLAUDE.md 与设计方案版本号一致性
set -e
# 纯机械操作，无歧义，不需要 LLM 判断

KB_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CLAUDE_MD="$KB_ROOT/CLAUDE.md"
DESIGN_DIR="$(git rev-parse --show-toplevel)/../知识库方案"

# 1. 读 CLAUDE.md 版本号
CLAUDE_VER=$(head -1 "$CLAUDE_MD" | grep -oP 'V\d+\.\d+\.\d+' | head -1)

if [ -z "$CLAUDE_VER" ]; then
  echo "❌ 无法从 CLAUDE.md 读取版本号"
  exit 1
fi

# 2. 找最新的设计方案目录
LATEST_DIR=$(ls -d "$DESIGN_DIR"/V*-模块化 2>/dev/null | sort -V | tail -1)

if [ -z "$LATEST_DIR" ]; then
  echo "❌ 未找到设计方案目录"
  exit 1
fi

DESIGN_VER=$(basename "$LATEST_DIR" | grep -oP 'V\d+\.\d+\.\d+' | head -1)

# 3. 比对
echo "=== 版本一致性检查 ==="
echo "CLAUDE.md: $CLAUDE_VER"
echo "设计方案:   $DESIGN_VER"

if [ "$CLAUDE_VER" = "$DESIGN_VER" ]; then
  echo "✅ 一致"
  exit 0
else
  echo ""
  echo "⚠️  不一致！建议同步。"
  echo ""
  echo "手动修复: 把设计方案的版本号更新为 $CLAUDE_VER"
  exit 1
fi
