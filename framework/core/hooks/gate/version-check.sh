#!/bin/bash
# 版本一致性检查 — 挂载到 pre-commit
set -e
# 比对 CLAUDE.md 与设计方案版本号

KB_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
CLAUDE_VER=$(grep -oP 'V\d+\.\d+\.\d+' "$KB_ROOT/CLAUDE.md" | head -1)
# 设计方案目录：环境变量 KB_DESIGN_DIR 优先，默认 KB_ROOT/docs（消除硬编码，可迁移）
DESIGN_DIR="${KB_DESIGN_DIR:-$KB_ROOT/docs}"
# 校验目标：运行结构说明-V*.md（替代旧 V*-模块化 目录，2026-08-02 起）
DESIGN_FILE=$(ls "$DESIGN_DIR"/设计方案-V*.md 2>/dev/null | sort -V | tail -1)

if [ -z "$DESIGN_FILE" ]; then
  echo ""
  echo "⚠️  未找到设计方案文档：$DESIGN_DIR/设计方案-V*.md"
  echo "   请先创建或恢复《运行结构说明》，版本号需与 CLAUDE.md 一致"
  exit 1
fi

DESIGN_VER=$(basename "$DESIGN_FILE" | grep -oP 'V\d+\.\d+\.\d+' | head -1)

if [ "$CLAUDE_VER" != "$DESIGN_VER" ]; then
  echo ""
  echo "⚠️  版本不一致！"
  echo "   CLAUDE.md: $CLAUDE_VER"
  echo "   设计方案:   $DESIGN_VER"
  echo ""
  echo "   建议: 更新设计方案到 $CLAUDE_VER"
  exit 1
fi
