#!/bin/bash
# sync-agent-md.sh —— 从 AGENT.md 同步到 CLAUDE.md 和 HERMES.md
# 保留各目标文件的 MANUAL 区，仅覆盖 AUTO 区
set -e

FRAMEWORK="$(cd "$(dirname "$0")/../.." && pwd)"   # framework/
REPO_ROOT="$(cd "$FRAMEWORK/.." && pwd)"           # 仓库根（适配层产物落这里，各 Agent 只扫仓库根）
AGENT_MD="$FRAMEWORK/AGENT.md"

if [ ! -f "$AGENT_MD" ]; then
  echo "❌ AGENT.md 不存在: $AGENT_MD"
  exit 1
fi

sync_to() {
  local target="$1"
  local manual_content=""
  local target_name="${target##*/}"      # CLAUDE.md 或 HERMES.md
  local target_base="${target_name%.*}" # CLAUDE 或 HERMES

  # 提取 MANUAL 区（如有）
  if [ -f "$target" ] && grep -q "<!-- MANUAL START -->" "$target"; then
    manual_content=$(sed -n '/<!-- MANUAL START -->/,$p' "$target")
  else
    manual_content="<!-- MANUAL START -->"$'\n'"<!-- MANUAL END -->"
  fi

  # 生成目标文件：AUTO 注释 + AGENT.md 内容（标题替换为对应 Agent 名）+ MANUAL 区
  {
    echo "<!-- AUTO：本文件由 engine/scripts/sync-agent-md.sh 从 AGENT.md 生成，修改请编辑 AGENT.md -->"
    echo "<!-- AUTO START -->"
    # 标题行替换：# AGENT.md → # CLAUDE.md（或 # HERMES.md）
    # 正文中所有 "AGENT.md"/"AGENT" 替换为对应目标名
    if [ "$target_base" = "AGENTS" ]; then
      # AGENTS 含 AGENT 子串，跳过标题二次替换避免 AGENTSS
      sed -e "1s/AGENT\.md/${target_name}/" \
          -e "s/AGENT\.md/${target_name}/g" \
          -e "s/→AGENT变更/→${target_base}变更/g" \
          "$AGENT_MD"
    else
      sed -e "1s/AGENT\.md/${target_name}/" \
          -e "1s/AGENT/${target_base}/g" \
          -e "s/AGENT\.md/${target_name}/g" \
          -e "s/→AGENT变更/→${target_base}变更/g" \
          "$AGENT_MD"
    fi
    echo "<!-- AUTO END -->"
    echo ""
    echo "$manual_content"
  } > "$target"

  echo "✅ 已同步: $target"
}

sync_to "$REPO_ROOT/CLAUDE.md"
sync_to "$REPO_ROOT/HERMES.md"
sync_to "$REPO_ROOT/AGENTS.md"

echo "✅ 同步完成: AGENT.md -> CLAUDE.md + HERMES.md + AGENTS.md"
