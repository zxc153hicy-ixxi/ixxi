#!/bin/bash
# install.sh — 把 ixxi 装到全局（之后任何目录打开 Agent，说「加载 ixxi」都能用）
# 用法：bash install.sh [--help] [--dry-run]
set -e

IXI_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_SKILL="$IXI_DIR/framework/core/skills/load/SKILL.md"

# ── 选项解析 ──────────────────────────────────────
case "${1:-}" in
  help|-h|--help)
    cat <<'EOF'
用法: bash install.sh [--dry-run]

把 ixxi 装到全局（kb-load 启动器 + IXXI_HOME 环境变量）。

选项:
  -h, --help     显示本帮助并退出
  --dry-run      只打印将执行的 cp 目标路径与 setx 环境变量操作，不实际执行

卸载：删除 ~/.claude/skills/kb-load、~/.agents/skills/kb-load，并清除 IXXI_HOME。
EOF
    exit 0
    ;;
esac

# --dry-run：只预演打印，不落盘
DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

echo "╔══════════════════════════════════╗"
echo "║  ixxi 全局安装                     ║"
echo "╚══════════════════════════════════╝"
echo ""
echo "ixxi 目录: $IXI_DIR"

# ── 1. 装 kb-load 启动器到各 Agent 全局 skill 目录 ──
echo ""
echo "── 装全局启动器（kb-load）──"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "  [dry-run] cp $SRC_SKILL → $HOME/.claude/skills/kb-load/SKILL.md"
  echo "  [dry-run] cp $SRC_SKILL → $HOME/.agents/skills/kb-load/SKILL.md"
else
  # Claude Code: ~/.claude/skills/kb-load/
  mkdir -p "$HOME/.claude/skills/kb-load"
  cp "$SRC_SKILL" "$HOME/.claude/skills/kb-load/SKILL.md"
  echo "✓ Claude 启动器 → ~/.claude/skills/kb-load/"

  # Codex: ~/.agents/skills/kb-load/
  mkdir -p "$HOME/.agents/skills/kb-load"
  cp "$SRC_SKILL" "$HOME/.agents/skills/kb-load/SKILL.md"
  echo "✓ Codex 启动器 → ~/.agents/skills/kb-load/"
fi

# Hermes: 直读 SKILL.md + IXXI_HOME 定位，无需装 skill
echo "✓ Hermes 靠 IXXI_HOME 定位，无需装 skill"

# ── 2. 设置 IXXI_HOME 环境变量（持久化，指向 ixxi 目录）──
echo ""
echo "── 设置 IXXI_HOME 环境变量 ──"

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    # Windows（Git Bash）：用 setx 写用户环境变量
    if [ "$DRY_RUN" -eq 1 ]; then
      echo "  [dry-run] setx IXXI_HOME \"$IXI_DIR\"（写入 Windows 用户环境变量，重启终端生效）"
    else
      setx IXXI_HOME "$IXI_DIR" >/dev/null 2>&1 \
        && echo "✓ IXXI_HOME=$IXI_DIR（已写入 Windows 用户环境变量，重启终端生效）" \
        || echo "⚠ 无法写环境变量，请手动设置 IXXI_HOME=$IXI_DIR"
    fi
    ;;
  *)
    # Mac / Linux：写 shell 配置
    SHELL_RC="$HOME/.bashrc"
    [ -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.zshrc"
    if [ "$DRY_RUN" -eq 1 ]; then
      echo "  [dry-run] 追加 export IXXI_HOME=\"$IXI_DIR\" 到 $SHELL_RC（重开终端生效）"
    elif ! grep -q 'IXXI_HOME' "$SHELL_RC" 2>/dev/null; then
      echo "export IXXI_HOME=\"$IXI_DIR\"" >> "$SHELL_RC"
      echo "✓ IXXI_HOME=$IXI_DIR（已写入 $SHELL_RC，重开终端生效）"
    else
      echo "✓ IXXI_HOME 已设置"
    fi
    ;;
esac

echo ""
if [ "$DRY_RUN" -eq 1 ]; then
  echo "╔══════════════════════════════════╗"
  echo "║  [dry-run] 预演完成，未做任何修改 ║"
  echo "╚══════════════════════════════════╝"
else
  echo "╔══════════════════════════════════╗"
  echo "║  ✅ 安装完成                       ║"
  echo "╚══════════════════════════════════╝"
fi
echo ""
echo "现在任何目录打开 Agent，说「加载 ixxi」就能用。"
echo "卸载：删除 ~/.claude/skills/kb-load、~/.agents/skills/kb-load，并清除 IXXI_HOME。"
