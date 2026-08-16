#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
# ============================================================
# ixxi 模板导出预检
# 在 export-template.sh 之前运行，验证通过才允许导出。
#
# 检查维度：
#   一、私有清单泄露检测 —— 读 private-paths.txt，确保私有目录不落导出范围
#   二、完整性           —— 根文件 + 规则文件 + 关键目录存在
#   三、YAML 格式        —— 规则文件 frontmatter 必填字段
#   四、契约结构         —— CLAUDE.md / AGENT.md 核心段落
# ============================================================

SOURCE="$KB_ROOT"
PRIVATE_FILE="$SOURCE/framework/engine/config/private-paths.txt"
PASS=0; FAIL=0

check_pass() { PASS=$((PASS+1)); echo "  ✅ $1"; }
check_fail() { FAIL=$((FAIL+1)); echo "  ❌ $1"; }

echo "============================================"
echo "  ixxi 模板导出预检"
echo "============================================"

# ── 一、私有清单泄露检测 ──────────────────────────────
echo ""
echo "--- 一、私有清单泄露检测（读 private-paths.txt）---"

ROOT_WHITELIST="CLAUDE.md HERMES.md README.md GETTING-STARTED.md LICENSE ixxi install.sh .gitignore .gitattributes"

if [ ! -f "$PRIVATE_FILE" ]; then
  check_fail "私有清单缺失: framework/engine/config/private-paths.txt"
else
  check_pass "私有清单存在"
  PRIVATE_COUNT=0
  while IFS= read -r line; do
    line="$(echo "$line" | sed 's/[[:space:]]*$//')"
    [ -z "$line" ] && continue
    case "$line" in \#*) continue ;; esac
    PRIVATE_COUNT=$((PRIVATE_COUNT+1))

    if [[ "$line" == framework/* ]]; then
      check_fail "私有路径 '$line' 位于 framework/ 内，导出会泄露"
      continue
    fi
    if echo "$ROOT_WHITELIST" | grep -qw "$line"; then
      check_fail "私有路径 '$line' 是根文件，导出会泄露"
      continue
    fi
    if grep -qxF "$line" "$SOURCE/.gitignore" 2>/dev/null; then
      check_pass "私有路径 $line —— 已由 .gitignore 排除，导出范围外"
    else
      check_fail "私有路径 $line —— 未由 .gitignore 排除"
    fi
  done < "$PRIVATE_FILE"
  if [ "$PRIVATE_COUNT" -eq 0 ]; then
    check_fail "私有清单为空或仅注释——personal 将无排除直接泄露！"
  fi
fi

# ── 二、完整性检查 ────────────────────────────────────
echo ""
echo "--- 二、完整性检查 ---"

echo "根文件:"
for f in CLAUDE.md HERMES.md AGENTS.md README.md GETTING-STARTED.md CONTRIBUTING.md MAINTAINERS.md CHANGELOG.md LICENSE framework/AGENT.md framework/index.md framework/activation.md; do
  [ -f "$SOURCE/$f" ] && check_pass "$f" || check_fail "$f 缺失"
done
[ -d "$SOURCE/.github" ] && check_pass ".github/（CI + issue 模板）" || check_fail ".github/ 缺失"

echo "规则文件:"
rules_count=$(ls "$SOURCE/framework/ops/rules/"*.md 2>/dev/null | wc -l)
if [ "$rules_count" -gt 0 ]; then
  check_pass "framework/ops/rules/ —— $rules_count 个规则文件"
else
  check_fail "framework/ops/rules/ 无规则文件"
fi

echo "关键目录:"
for d in framework/core/skills framework/core/hooks framework/core/agents framework/engine/scripts framework/engine/config framework/engine/templates; do
  [ -d "$SOURCE/$d" ] && check_pass "$d/" || check_fail "$d/ 缺失"
done

# ── 三、YAML 格式校验 ─────────────────────────────────
echo ""
echo "--- 三、YAML 格式校验 (framework/ops/rules/) ---"
for f in "$SOURCE/framework/ops/rules/"*.md; do
  [ -f "$f" ] || continue
  name=$(basename "$f")
  head -1 "$f" | grep -q "^---$" || { check_fail "$name: 缺 YAML 开始 ---"; continue; }
  sed -n '2,15p' "$f" | grep -q "^---$" || { check_fail "$name: 缺 YAML 结束 ---"; continue; }
  for field in "tags:" "summary:" "status:" "confidence:"; do
    head -15 "$f" | grep -q "^$field" || check_fail "$name: 缺 $field"
  done
done
check_pass "规则文件 YAML 校验完成（共 $rules_count 个）"

# ── 四、契约结构检查 ──────────────────────────────────
echo ""
echo "--- 四、CLAUDE.md / AGENT.md 结构检查 ---"

check_md_structure() {
  local file="$1" label="$2"
  local src="$SOURCE/$file"
  check_sec() { grep -q "$2" "$src" 2>/dev/null && check_pass "$label: $1" || check_fail "$label: $1 缺失"; }
  check_sec "G层约束表" "| G1 |"
  check_sec "T层路由表" '| `#'
  check_sec "规则优先级" "规则优先级声明"
  check_sec "行数管控" "≤180"
  check_sec "健康度公式" "健康度 ="
  check_sec "关键耦合点" "关键耦合点"
  check_sec "安全" "## 安全"
  local lines
  lines=$(wc -l < "$src")
  [ "$lines" -le 180 ] && check_pass "$label 行数 $lines/180" || check_fail "$label 行数 $lines/180 超限"
}

check_md_structure "CLAUDE.md" "CLAUDE"
check_md_structure "framework/AGENT.md" "AGENT"

# ── 结果 ──────────────────────────────────────────────
echo ""
echo "============================================"
echo "  预检结果"
echo "============================================"
echo "  通过: $PASS"
echo "  失败: $FAIL"
echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "  ✅ 全部通过，可以导出"
  exit 0
else
  echo "  ❌ 存在 $FAIL 项未通过，导出已阻断"
  exit 1
fi
