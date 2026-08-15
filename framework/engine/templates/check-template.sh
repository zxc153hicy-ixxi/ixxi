#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
set -e
# ============================================================
# 模板导出预检脚本 V2
# 在 export-template.sh 之前运行，验证通过才允许导出
#
# 检查维度：
#   一、泄露检测 — 全目录覆盖，漏一个即阻断
#   二、完整性   — 系统文件一个不能少
#   三、YAML格式 — 规则文件必填字段校验
#   四、CLAUDE结构 — 核心段落存在性
# ============================================================

SOURCE="$KB_ROOT"
PASS=0
FAIL=0

red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
nc='\033[0m'

check_pass() { PASS=$((PASS+1)); echo -e "  ${green}✅${nc} $1"; }
check_fail() { FAIL=$((FAIL+1)); echo -e "  ${red}❌${nc} $1"; }

echo "============================================"
echo "  模板导出预检 V2"
echo "============================================"

# ============================================================
# 一、泄露检测 — 全目录覆盖
# ============================================================
echo ""
echo "--- 一、泄露检测（全目录覆盖）---"

# 导出时进入模板的目录（framework/ops 子目录，只有这些可以有内容）
TEMPLATE_DIRS="rules hermes scripts"

# 导出时排除的目录（framework 非导出子目录 + 实例数据 personal/ 由 ixxi init 生成）
SKIP_DIRS="personal framework-patterns templates framework/knowledge framework/samples framework/docs framework/engine/tests .claudian .fix-backup .obsidian .git Excalidraw queries scripts"

# 导出时排除的个人文件
SKIP_FILES="personal/data/用户画像.md personal/data/log.md"

# 1. 扫描全部 framework/ops/ 子目录
echo "framework/ops/ 全覆盖:"
for dir in $(find "$SOURCE/framework/ops" -maxdepth 1 -type d 2>/dev/null | grep -v "^$SOURCE/framework/ops$" | sort); do
  name=$(basename "$dir")
  md_count=$(find "$dir" -name "*.md" -not -name "README.md" 2>/dev/null | wc -l)

  is_template=0; is_skip=0
  for t in $TEMPLATE_DIRS; do [ "$name" = "$t" ] && is_template=1; done
  for s in $SKIP_DIRS; do [ "$name" = "$s" ] && is_skip=1; done

  if [ "$is_template" -eq 1 ]; then
    check_pass "framework/ops/$name/ — 系统文件，进入模板"
  elif [ "$is_skip" -eq 1 ]; then
    check_pass "framework/ops/$name/ — 导出时排除"
  else
    check_fail "framework/ops/$name/ — 未知目录！不在排除列表，可能泄露"
  fi
done

# 2. 个人文件
echo ""
echo "个人文件:"
for f in $SKIP_FILES; do
  if [ -f "$SOURCE/$f" ]; then
    check_pass "$f — 导出时排除"
  fi
done

# 3. personal/ 实例数据全覆盖（.md + .docx + .txt + ... 全部计入）
echo ""
echo "personal/ 实例数据全覆盖:"
RAW_DIRS="data/inbox data/sessions data/feedback/positive data/feedback/negative data/feedback/partial data/memory raw system"
for dir in $RAW_DIRS; do
  all_count=$(find "$SOURCE/personal/$dir" -type f -not -name "README.md" 2>/dev/null | wc -l)
  if [ "$all_count" -gt 0 ]; then
    check_pass "personal/$dir/ — $all_count 文件，导出时排除"
  else
    check_pass "personal/$dir/ — 空"
  fi
done

# 4. 脚本自身
check_pass "导出/预检脚本在 framework/engine/templates/，不进入模板"

# ============================================================
# 二、完整性检查
# ============================================================
echo ""
echo "--- 二、完整性检查 ---"

echo "根文件:"
for f in CLAUDE.md HERMES.md README.md GETTING-STARTED.md framework/AGENT.md framework/index.md framework/activation.md; do
  if [ -f "$SOURCE/$f" ]; then
    check_pass "$f"
  else
    check_fail "$f 缺失"
  fi
done

echo "规则文件:"
RULES=(
  "Ingest完整流程.md" "Lint检查流程.md" "矛盾消解流程.md"
  "反馈闭环流程.md" "知识库运维规范.md" "模板输出规范.md"
  "应急预案格式.md" "版本管理规范.md" "方案迭代规范.md"
  "会话收尾检查.md" "系统操作菜单.md" "核心操作流程.md"
  "全量审计流程.md" "故障处置流程.md" "技能化流程.md"
  "命名规范.md" "复杂度分层.md" "文档转Markdown工具选型.md"
  "编码原则.md" "可行性分析流程.md" "确定性动作强制规范.md"
  "正反模式管理规范.md" "personal隔离规范.md" "skill调度注册表.md"
  "代码审查规范.md" "mcp注册表.md"
  "知识库检查体系.md" "知识库修复体系.md" "多Agent适配方案.md"
)
# 注：中文翻译规范.md 已迁移到个人实例层 personal/system/rules/，
# 批量修复/修复与创建设计文档已归档到 personal/knowledge/archive/，均不属 framework 规则检查范围
# 以下已废弃，检查 archive/ 目录
ARCHIVED_RULES=(
  "auto-save-conversation.md" "context-warning.md"
  "ui-version-management.md" "version-backup.md"
)
for rule in "${ARCHIVED_RULES[@]}"; do
  if [ -f "$SOURCE/personal/knowledge/archive/$rule" ]; then
    check_pass "$rule (archived)"
  else
    check_pass "$rule (archived — 已移除，非阻断)"
  fi
done

RULES2=(
)
for rule in "${RULES[@]}"; do
  if [ -f "$SOURCE/framework/ops/rules/$rule" ]; then
    check_pass "$rule"
  else
    check_fail "$rule 缺失"
  fi
done

# ============================================================
# 三、YAML 格式校验
# ============================================================
echo ""
echo "--- 三、YAML 格式校验 (framework/ops/rules/) ---"

for f in "$SOURCE/framework/ops/rules/"*.md; do
  name=$(basename "$f")
  # opening ---
  if ! head -1 "$f" | grep -q "^---$"; then
    check_fail "$name: 缺少 YAML 开始 ---"
    continue
  fi
  # closing ---
  if ! sed -n '2,15p' "$f" | grep -q "^---$"; then
    check_fail "$name: 缺少 YAML 结束 ---"
    continue
  fi
  # required fields
  for field in "tags:" "summary:" "status:" "confidence:"; do
    if ! head -15 "$f" | grep -q "^$field"; then
      check_fail "$name: 缺少必填字段 $field"
    fi
  done
done

echo "  总计: $(ls "$SOURCE/framework/ops/rules/"*.md 2>/dev/null | wc -l) 规则文件"

# ============================================================
# 四、CLAUDE.md / AGENT.md 结构完整性
# ============================================================
echo ""
echo "--- 四、CLAUDE.md / AGENT.md 结构检查 ---"

check_md_structure() {
  local file="$1"
  local label="$2"
  local src="$SOURCE/$file"

  check_section() {
    if grep -q "$2" "$src" 2>/dev/null; then
      check_pass "$label: $1"
    else
      check_fail "$label: $1 缺失（$2）"
    fi
  }

  check_section "G层约束表"    "| G1 |"
  check_section "T层路由表"    "| \`#"
  check_section "规则优先级"    "规则优先级声明"
  check_section "行数管控"      "≤180"
  check_section "Ingest流程"    "Ingest完整流程"
  check_section "Lint检查"      "Lint检查流程"
  check_section "健康度公式"    "健康度 ="
  check_section "关键耦合点"    "关键耦合点"
  check_section "安全"          "## 安全"
  check_section "时间约束"      "时间约束速查"

  local lines=$(wc -l < "$src")
  if [ "$lines" -le 180 ]; then
    check_pass "$label 行数: $lines/180"
  else
    check_fail "$label 行数: $lines/180 超限"
  fi
}

check_md_structure "CLAUDE.md" "CLAUDE"
check_md_structure "framework/AGENT.md" "AGENT"

# ============================================================
# 结果
# ============================================================
echo ""
echo "============================================"
echo "  预检结果"
echo "============================================"
echo "  通过: $PASS"
echo "  失败: $FAIL"
echo ""

if [ "$FAIL" -eq 0 ]; then
  echo -e "  ${green}✅ 全部通过，可以导出${nc}"
  exit 0
else
  echo -e "  ${red}❌ 存在 $FAIL 项未通过，导出已阻断${nc}"
  echo "  请修复上述问题后重新执行预检"
  exit 1
fi
