#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# ============================================================
# 知识库模板导出脚本
# 从当前知识库根目录导出系统骨架到 <根目录>-Template
# 排除所有个人数据，生成可供第三方安装的干净模板
#
# 用法:
#   ./export-template.sh                默认导出（工程类 skill）
#   ./export-template.sh --with-creative  附加导出创作类 skill
# ============================================================

set -e

SOURCE="$KB_ROOT"
TARGET="$KB_ROOT-Template"
WITH_CREATIVE=false

# 参数解析
for arg in "$@"; do
  case "$arg" in
    --with-creative) WITH_CREATIVE=true ;;
    --help|-h)
      echo "用法: $0 [--with-creative]"
      echo "  (无参数)    默认导出：规则引擎 + 工程类外部 skill"
      echo "  --with-creative  附加导出创作类外部 skill（构思/审查/写作）"
      exit 0
      ;;
  esac
done

echo "============================================"
echo "  知识库模板导出"
echo "  源: $SOURCE"
echo "  目标: $TARGET"
echo "  创作类 skill: $([ "$WITH_CREATIVE" = true ] && echo '✅ 导出' || echo '❌ 跳过（--with-creative 开启）')"
echo "============================================"

# 0. 预检——不通过不导出
echo ""
echo "执行预检..."
bash "$SOURCE/engine/templates/check-template.sh"
if [ $? -ne 0 ]; then
  echo ""
  echo "❌ 预检未通过，导出已取消。请修复上述问题后重试。"
  exit 1
fi
echo ""

# 1. 清空目标目录
if [ -d "$TARGET" ]; then
  echo "清空已有模板目录..."
  rm -rf "$TARGET"
fi

# 2. 创建目录结构
echo "创建目录骨架..."
mkdir -p "$TARGET"/{ops/{rules,patterns,anti-patterns,hermes},knowledge/{projects,learning,archive,notes,reference},engine/{templates,config,scripts},raw/{inbox,sessions,feedback/positive,feedback/negative,feedback/partial,local,web/articles,web/papers,web/references,assets},.inbox/{sources,converted,_extracted,_processed,_failed},.claude/{kb/{skills,hooks,agents},skills/{_archived,_external}}}

# 3. 复制根文件
echo "复制根文件..."
for f in AGENT.md CLAUDE.md HERMES.md index.md queue.md activation.md session-notes.md README.md GETTING-STARTED.md .gitignore .gitattributes log.md; do
  if [ -f "$SOURCE/$f" ]; then
    cp "$SOURCE/$f" "$TARGET/$f"
    echo "  ✅ $f"
  fi
done

# 4. 复制 ops/rules/ 全部规则文件
echo "复制规则文件..."
cp "$SOURCE/ops/rules/"*.md "$TARGET/ops/rules/" 2>/dev/null || true
echo "  ✅ $(ls "$TARGET/ops/rules/"*.md 2>/dev/null | wc -l) 个规则文件"

# 5. 复制 ops/hermes/ 审查团设计+命令翻译表
echo "复制 Hermes 审查团..."
cp "$SOURCE/ops/hermes/"*.md "$TARGET/ops/hermes/" 2>/dev/null || true
echo "  ✅ $(ls "$TARGET/ops/hermes/"*.md 2>/dev/null | wc -l) 个 Hermes 文件"

# 6. 复制 engine/templates/ 下的模板文件（排除自身和运维检查脚本）
echo "复制模板..."
for f in "$SOURCE/engine/templates/"*; do
  name=$(basename "$f")
  if [ "$name" != "export-template.sh" ] && [ "$name" != "check-template.sh" ] && [[ "$name" != check-* ]]; then
    cp -r "$f" "$TARGET/engine/templates/$name" 2>/dev/null && echo "  ✅ engine/templates/$name"
  fi
done

# 7. 复制 engine/scripts/（排除 __pycache__ 和 ocr-sources.json）
echo "复制检查脚本..."
cp -r "$SOURCE/engine/scripts/"* "$TARGET/engine/scripts/" 2>/dev/null || true
rm -rf "$TARGET/engine/scripts/__pycache__" 2>/dev/null || true
rm -f "$TARGET/engine/scripts/ocr-sources.json" 2>/dev/null || true
echo "  ✅ $(find "$TARGET/engine/scripts" -type f | wc -l) 个脚本文件"

# 8. 复制 engine/config/
echo "复制配置文件..."
cp -r "$SOURCE/engine/config/"* "$TARGET/engine/config/" 2>/dev/null || true
echo "  ✅ $(find "$TARGET/engine/config" -type f | wc -l) 个配置文件"

# 9. 复制 ops/scripts/（原子操作脚本）
echo "复制 ops/scripts..."
cp -r "$SOURCE/ops/scripts/"* "$TARGET/ops/scripts/" 2>/dev/null || true
echo "  ✅ $(find "$TARGET/ops/scripts" -type f | wc -l) 个 ops 脚本文件"

# 10. 复制 core/skills/（内部操作 skill）
echo "复制内部 skills..."
cp -r "$SOURCE/core/skills/"* "$TARGET/core/skills/" 2>/dev/null || true
echo "  ✅ $(find "$TARGET/core/skills" -type f | wc -l) 个内部 skill 文件"

# 11. 复制 core/hooks/
echo "复制 hooks..."
cp -r "$SOURCE/core/hooks/"* "$TARGET/core/hooks/" 2>/dev/null || true
echo "  ✅ $(find "$TARGET/core/hooks" -type f | wc -l) 个 hook 文件"

# 12. 复制 core/agents/
echo "复制 agents..."
cp -r "$SOURCE/core/agents/"* "$TARGET/core/agents/" 2>/dev/null || true
echo "  ✅ $(find "$TARGET/core/agents" -type f | wc -l) 个 agent 文件"

# 13. 复制 core/skills/_external/（默认：仅工程类）
echo "复制外部 skills..."
# 工程类总是导出
for dir in "$SOURCE/core/skills/_external/工程-"*; do
  if [ -d "$dir" ]; then
    name=$(basename "$dir")
    cp -r "$dir" "$TARGET/core/skills/_external/$name"
    echo "  ✅ 工程类: $name"
  fi
done
# 创作类：仅 --with-creative 时导出
if [ "$WITH_CREATIVE" = true ]; then
  for dir in "$SOURCE/core/skills/_external/创作-"*; do
    if [ -d "$dir" ]; then
      name=$(basename "$dir")
      cp -r "$dir" "$TARGET/core/skills/_external/$name"
      echo "  ✅ 创作类: $name"
    fi
  done
else
  echo "  ⏭️  创作类 skill 已跳过（--with-creative 开启）"
fi

# 14. 创建空目录占位文件（不覆盖已有 README.md）
echo "创建空目录占位..."
for dir in ops/patterns ops/anti-patterns knowledge/projects knowledge/learning knowledge/archive; do
  if [ ! -f "$TARGET/$dir/README.md" ]; then
    echo "# $dir" > "$TARGET/$dir/README.md"
    echo "  ✅ $dir/README.md"
  fi
done

# 15. raw/ 空目录占位
for dir in inbox sessions local feedback/positive feedback/negative feedback/partial web/articles web/papers web/references assets; do
  if [ ! -f "$TARGET/raw/$dir/README.md" ]; then
    echo "# $dir" > "$TARGET/raw/$dir/README.md"
    echo "  ✅ raw/$dir/README.md"
  fi
done

# 16. 初始化 git
echo "初始化 git..."
cd "$TARGET"
git init
git add -A
git commit -m "知识库模板 · 系统骨架 · $(date +%Y-%m-%d)" 2>/dev/null || echo "  ⚠️  git commit 跳过（可能无变更）"

echo ""
echo "============================================"
echo "  导出完成"
echo "  模板位置: $TARGET"
echo "  文件数: $(find "$TARGET" -type f -not -path '*/.git/*' | wc -l)"
echo "============================================"
echo ""
echo "使用方式（第三方）："
echo "  1. git clone / copy 模板目录"
echo "  2. 安装 Obsidian，打开该目录作为库"
echo "  3. 配置 AI 工具读取 CLAUDE.md"
echo "  4. 说「系统操作」查看可用指令"
echo ""
echo "导出范围说明："
echo "  ✅ 规则引擎 (ops/rules/ + ops/hermes/)"
echo "  ✅ 内部 skills (core/skills/)"
echo "  ✅ hooks + agents (core/hooks/ + agents/)"
echo "  ✅ 原子操作 (ops/scripts/)"
echo "  ✅ 检查脚本 (engine/scripts/)"
echo "  ✅ 配置文件 (engine/config/)"
echo "  ✅ 系统文件 (.gitignore + .gitattributes + log.md)"
echo "  ✅ 外部工程类 skills"
if [ "$WITH_CREATIVE" = true ]; then
  echo "  ✅ 外部创作类 skills"
else
  echo "  ❌ 外部创作类 skills（--with-creative 开启）"
fi
echo "  ❌ 个人数据 (knowledge/ raw/ patterns/ anti-patterns/)"
echo "  ❌ 个人配置 (.claude/settings.json)"
echo "  ❌ 记忆文件 (raw/memory/)"
