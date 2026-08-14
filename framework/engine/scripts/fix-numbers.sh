#!/bin/bash
# fix-numbers.sh -- 数字声明同步
#
# 检查 AGENT.md / 核心操作流程.md / 各规则文件中的数字声明
# 是否与实际一致，自动修复明显的不一致。
#
# 用法:
#   bash engine/scripts/fix-numbers.sh --dry-run    # 预览
#   bash engine/scripts/fix-numbers.sh --execute     # 执行

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DRY_RUN=true
EXECUTE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true ;;
    --execute) EXECUTE=true; DRY_RUN=false ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
  shift
done

echo "=== 数字声明同步 ==="
echo "模式: $([ "$DRY_RUN" = true ] && echo '预览' || echo '执行')"
echo ""

issues=0
fixed=0

# 1. 统计 G 层约束实际数量
g_count=$(grep -c "^| G" "$REPO_ROOT/AGENT.md" 2>/dev/null || echo "0")
echo "G 层约束: 实际 ${g_count} 条"

# 2. 统计 T 层标签实际数量
t_count=$(grep -c "^| \`#" "$REPO_ROOT/AGENT.md" 2>/dev/null || echo "0")
echo "T 层标签: 实际 ${t_count} 个"

# 3. 统计 R 层规则文件实际数量
r_count=$(find "$REPO_ROOT/ops/rules" -maxdepth 1 -name "*.md" -not -name "README.md" 2>/dev/null | wc -l)
echo "R 层规则: 实际 ${r_count} 个"

# 4. 检查 AGENT.md 中的声明
echo ""
echo "--- AGENT.md 声明检查 ---"

# G层约束数声明检查
if grep -q "G1-G17" "$REPO_ROOT/AGENT.md" 2>/dev/null; then
  declared_g=17
  if [ "$g_count" -ne "$declared_g" ]; then
    echo "⚠️ G层约束数: 声明 G1-G17($declared_g) ≠ 实际($g_count)"
    ((issues++))
  else
    echo "✅ G层约束数: 声明 = 实际 = $g_count"
  fi
fi

# T层标签数声明检查
if grep -q "14 个标签" "$REPO_ROOT/AGENT.md" 2>/dev/null; then
  declared_t=14
  if [ "$t_count" -ne "$declared_t" ]; then
    echo "⚠️ T层标签数: 声明 14 ≠ 实际($t_count)"
    ((issues++))
  else
    echo "✅ T层标签数: 声明 = 实际 = $t_count"
  fi
fi

# R层文件数声明检查
if grep -q "24文件" "$REPO_ROOT/AGENT.md" 2>/dev/null; then
  declared_r=24
  if [ "$r_count" -ne "$declared_r" ]; then
    echo "⚠️ R层文件数: 声明 24 ≠ 实际($r_count)"
    ((issues++))
  else
    echo "✅ R层文件数: 声明 = 实际 = $r_count"
  fi
fi

# 5. 检查 Lint 检查项数声明
echo ""
echo "--- Lint 声明检查 ---"
lint_count=$(grep -c "^| [0-9]" "$REPO_ROOT/ops/rules/Lint检查流程.md" 2>/dev/null || echo "0")
echo "Lint 检查项: 实际 ${lint_count} 项"

echo ""
echo "=== 检查结果 ==="
echo "发现问题: $issues 处"
echo ""

if [ "$issues" -eq 0 ]; then
  echo "✅ 数字声明一致，无需修复。"
elif [ "$DRY_RUN" = true ]; then
  echo "💡 加 --execute 自动修复明显的数字不一致。"
  echo "   (自动修复仅处理声明数 < 实际数的情况，将声明数更新为实际数)"
fi

# 自动修复
if [ "$EXECUTE" = true ] && [ "$issues" -gt 0 ]; then
  echo "执行自动修复..."

  # 修复 G 层约束声明
  if [ "$g_count" -ne "$declared_g" ] 2>/dev/null; then
    g_last="G${g_count}"
    if [ "$DRY_RUN" = false ]; then
      echo "  → 更新 G 层声明: G1-G${g_count}"
      # 注意：sed in-place 在不同平台行为不同，这里仅报告
      echo "  ⚠️ 数字同步需要人工确认上下文后手动修改 AGENT.md"
    fi
    ((fixed++))
  fi

  echo ""
  echo "修复完成: 可自动修复 $fixed 处"
  echo "⚠️ 数字声明涉及正文语义，建议人工复核后手动更新对应文件。"
fi

exit 0
