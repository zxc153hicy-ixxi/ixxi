#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
# ============================================================
# ixxi 模板导出脚本
# 复制整个仓库根，剔除个人目录 + 版本库 + 适配层产物，生成可分享的框架模板。
# 适配层（.claude/ .agents/ .codex/）是生成产物，由 ixxi init 的 sync 重新生成，不随模板导出。
#
# 私有目录清单 = framework/engine/config/private-paths.txt（单一事实源）
# 由 ixxi init 的 Q2 生成；export 与 check-template 均读它。
#
# 用法:
#   ./export-template.sh                默认导出（工程类外部 skill）
#   ./export-template.sh --with-creative  附加导出创作类外部 skill
# ============================================================

set -eo pipefail

SOURCE="$KB_ROOT"
TARGET="$KB_ROOT-Template"
PRIVATE_FILE="$SOURCE/framework/engine/config/private-paths.txt"
WITH_CREATIVE=false

# 参数解析
for arg in "$@"; do
  case "$arg" in
    --with-creative) WITH_CREATIVE=true ;;
    --help|-h)
      echo "用法: $0 [--with-creative]"
      echo "  (无参数)         默认导出：整个仓库根（剔除 personal/ + 适配层）+ 工程类外部 skill"
      echo "  --with-creative  附加导出创作类外部 skill（构思/审查/写作）"
      exit 0
      ;;
  esac
done

echo "============================================"
echo "  ixxi 模板导出"
echo "  源: $SOURCE"
echo "  目标: $TARGET"
echo "  私有清单: $PRIVATE_FILE"
echo "  创作类 skill: $([ "$WITH_CREATIVE" = true ] && echo '✅ 导出' || echo '❌ 跳过（--with-creative 未开启）')"
echo "============================================"

# 0. 预检——不通过不导出
echo ""
echo "执行预检..."
bash "$SOURCE/framework/engine/templates/check-template.sh"
echo ""

# 0.5 敏感扫描——framework 通用层必须干净（personal 不在扫描范围，已排除）
echo "敏感扫描（framework 通用层）..."
if ! python "$SOURCE/framework/engine/scripts/scan-sensitive.py" --repo "$SOURCE/framework" >/dev/null 2>&1; then
  echo "❌ 敏感扫描未通过，导出已阻断："
  python "$SOURCE/framework/engine/scripts/scan-sensitive.py" --repo "$SOURCE/framework" || true
  exit 1
fi
echo "  ✅ 敏感扫描通过"
echo ""

# 1. 清空目标目录
if [ -d "$TARGET" ]; then
  echo "清空已有模板目录..."
  rm -rf "$TARGET"
fi
mkdir -p "$TARGET"

# 2. 提取私有排除清单（非注释、非空行；先剥尾随空白/CR，再去尾部斜杠以匹配 tar）
EXCLUDE_LIST="$(mktemp)"
trap 'rm -f "$EXCLUDE_LIST"' EXIT
grep -v '^[[:space:]]*#' "$PRIVATE_FILE" | grep -v '^[[:space:]]*$' | sed -e 's/[[:space:]]*$//' -e 's|/$||' > "$EXCLUDE_LIST"
echo "私有排除清单（导出时排除）："
sed 's/^/  - /' "$EXCLUDE_LIST"

# 3. 复制整个仓库根，剔除私有清单 + 版本库 + 适配层 + 运行垃圾 + 恶意样例
echo ""
echo "复制仓库根（剔除私有/版本库/适配层）..."
tar -C "$SOURCE" -cf - \
    --exclude-from="$EXCLUDE_LIST" \
    --exclude='.git' \
    --exclude='.claude' \
    --exclude='.agents' \
    --exclude='.codex' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='ocr-sources.json' \
    --exclude='.DS_Store' \
    --exclude='malicious-samples' \
    . \
  | tar -C "$TARGET" -xf -

# 4. 创作类外部 skill 默认排除，--with-creative 才保留
if [ "$WITH_CREATIVE" != true ]; then
  rm -rf "$TARGET"/framework/core/skills/_external/创作-*
  echo "  ⏭️  创作类 skill 已跳过（--with-creative 未开启）"
fi

# 4.5 导出后复验——断言产物不含私有路径 + 适配层（统一兜底，覆盖 tar 跨平台差异）
echo ""
echo "导出后复验（断言无个人痕迹）..."
LEAK=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  if [ -e "$TARGET/$line" ]; then
    echo "  ❌ 泄露：产物含私有路径 $line"
    LEAK=1
  fi
done < "$EXCLUDE_LIST"
for d in .claude .agents .codex; do
  if [ -e "$TARGET/$d" ]; then
    echo "  ❌ 泄露：产物含适配层 $d/"
    LEAK=1
  fi
done
if [ "$LEAK" -ne 0 ]; then
  echo "❌ 导出后复验失败，删除产物并中止"
  rm -rf "$TARGET"
  exit 1
fi
echo "  ✅ 无个人痕迹（私有路径 + 适配层均未落盘）"

# 5. 初始化 git
echo ""
echo "初始化 git..."
cd "$TARGET"
git init -q
git add -A
if git diff --cached --quiet; then
  echo "  ⚠️  无变更，跳过 git commit"
else
  git commit -q -m "ixxi 模板 · framework 骨架 · $(date +%Y-%m-%d)" 2>/dev/null || echo "  ⚠️  git commit 失败（检查 git user.name/email）"
fi

echo ""
echo "============================================"
echo "  导出完成"
echo "  模板位置: $TARGET"
echo "  文件数: $(find "$TARGET" -type f -not -path '*/.git/*' | wc -l)"
echo "============================================"
echo ""
echo "导出范围说明："
echo "  ✅ 整个仓库根（framework/ + 契约 + 说明 + CI + LICENSE + ixxi/install.sh）"
echo "  ✅ 私有清单 private-paths.txt（声明默认个人目录，第三方 init 覆盖）"
if [ "$WITH_CREATIVE" = true ]; then
  echo "  ✅ 外部创作类 skills"
else
  echo "  ❌ 外部创作类 skills（--with-creative 未开启）"
fi
echo "  ❌ 适配层（.claude/ .agents/ .codex/）—— 由 ixxi init 重新生成"
echo "  ❌ 个人目录（见 private-paths.txt）—— 由 ixxi init 生成，绝不外流"
echo ""
echo "第三方使用：clone 后跑 bash ixxi init，生成 personal 骨架 + 适配层"
