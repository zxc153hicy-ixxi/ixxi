#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
set -e
# 检查 CLAUDE.md 版本号 vs 设计方案版本号是否一致

KB_VER=$(head -1 "$KB_ROOT/CLAUDE.md" | grep -o "V[0-9]\.[0-9]*")
DESIGN_DIR="$(git rev-parse --show-toplevel)/../知识库方案"
DESIGN_VER=$(ls -d "$DESIGN_DIR"/V*-模块化 2>/dev/null | sort -V | tail -1 | grep -o "V[0-9]\.[0-9]*")

echo "KB版本:     $KB_VER"
echo "设计方案:   $DESIGN_VER"

if [ "$KB_VER" = "$DESIGN_VER" ]; then
  echo "✅ 版本一致"
  exit 0
else
  echo "❌ 版本不一致——KB是$KB_VER但设计方案是$DESIGN_VER，需要同步"
  exit 1
fi
