#!/bin/bash
# install.sh — 把 ixxi 装到全局（之后任何目录打开 Agent，说「加载 ixxi」都能用）
# 用法：bash install.sh
set -e

IXI_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_SKILL="$IXI_DIR/framework/core/skills/load/SKILL.md"

echo "╔══════════════════════════════════╗"
echo "║  ixxi 全局安装                     ║"
echo "╚══════════════════════════════════╝"
echo ""
echo "ixxi 目录: $IXI_DIR"

# ── 1. 装 kb-load 启动器到各 Agent 全局 skill 目录 ──
echo ""
echo "── 装全局启动器（kb-load）──"

# Claude Code: ~/.claude/skills/kb-load/
mkdir -p "$HOME/.claude/skills/kb-load"
cp "$SRC_SKILL" "$HOME/.claude/skills/kb-load/SKILL.md"
echo "✓ Claude 启动器 → ~/.claude/skills/kb-load/"

# Codex: ~/.agents/skills/kb-load/
mkdir -p "$HOME/.agents/skills/kb-load"
cp "$SRC_SKILL" "$HOME/.agents/skills/kb-load/SKILL.md"
echo "✓ Codex 启动器 → ~/.agents/skills/kb-load/"

# Hermes: 直读 SKILL.md + IXXI_HOME 定位，无需装 skill
echo "✓ Hermes 靠 IXXI_HOME 定位，无需装 skill"

# ── 2. 设置 IXXI_HOME 环境变量（持久化，指向 ixxi 目录）──
echo ""
echo "── 设置 IXXI_HOME 环境变量 ──"

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    # Windows（Git Bash）：用 setx 写用户环境变量
    setx IXXI_HOME "$IXI_DIR" >/dev/null 2>&1 \
      && echo "✓ IXXI_HOME=$IXI_DIR（已写入 Windows 用户环境变量，重启终端生效）" \
      || echo "⚠ 无法写环境变量，请手动设置 IXXI_HOME=$IXI_DIR"
    ;;
  *)
    # Mac / Linux：写 shell 配置
    SHELL_RC="$HOME/.bashrc"
    [ -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.zshrc"
    if ! grep -q 'IXXI_HOME' "$SHELL_RC" 2>/dev/null; then
      echo "export IXXI_HOME=\"$IXI_DIR\"" >> "$SHELL_RC"
      echo "✓ IXXI_HOME=$IXI_DIR（已写入 $SHELL_RC，重开终端生效）"
    else
      echo "✓ IXXI_HOME 已设置"
    fi
    ;;
esac

echo ""
echo "╔══════════════════════════════════╗"
echo "║  ✅ 安装完成                       ║"
echo "╚══════════════════════════════════╝"
echo ""
echo "现在任何目录打开 Agent，说「加载 ixxi」就能用。"
echo "卸载：删除 ~/.claude/skills/kb-load、~/.agents/skills/kb-load，并清除 IXXI_HOME。"
