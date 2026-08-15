#!/bin/bash
# desc: 创建正模式文件，插入索引，重排编号，更新计数
# usage: kb-do.sh create-pattern <名称>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../_lib/git.sh"
source "$SCRIPT_DIR/../_lib/index.sh"

KB_ROOT=$(kb_root)
# 实际布局：正/反模式平铺在 framework/ops/framework-patterns（无独立 patterns/ 目录）
PATTERNS_DIR="$KB_ROOT/framework/ops/framework-patterns"
# framework-patterns 当前无 正模式索引.md，索引维护仅在索引文件存在时执行（不强行新建）
INDEX_FILE="$PATTERNS_DIR/正模式索引.md"

main() {
    if [ $# -lt 1 ]; then
        echo "用法: kb-do.sh create-pattern <名称>" >&2
        echo "示例: kb-do.sh create-pattern 原子化操作" >&2
        exit 1
    fi

    local name="$1"
    local filename="${name}.md"
    local filepath="$PATTERNS_DIR/$filename"
    local today
    today=$(date +%Y-%m-%d)

    # 事务开始
    git_backup "create-pattern"

    # E1: 检查是否已存在
    if [ -f "$filepath" ]; then
        git_rollback "文件已存在: $filepath"
    fi

    # E2: 写入模板文件
    cat > "$filepath" << EOF
---
tags: [正模式]
status: active
summary: $name——（待补充）
created: $today
updated: $today
---

# $name

> 正模式 = 验证有效的做法。

## 是什么


## 为什么有效


## 什么时候用

EOF

    if [ ! -f "$filepath" ]; then
        git_rollback "写入模板文件失败: $filepath"
    fi

    # E3-E5: 索引维护——framework-patterns 无 正模式索引.md 时跳过（不强行新建），仅写文件
    local old_count="" new_count=""
    if [ -f "$INDEX_FILE" ]; then
        old_count=$(count_index_entries "$INDEX_FILE")
        append_index_row "$INDEX_FILE" "[[$name]] | （待补充）"
        renumber_index "$INDEX_FILE"
        new_count=$(count_index_entries "$INDEX_FILE")
        update_main_count "patterns" "正模式索引" "$new_count"
    else
        echo "   ⚠️ 索引文件不存在，跳过索引维护: $INDEX_FILE" >&2
    fi

    # 清理备份标签
    git_cleanup

    # E6: 输出摘要
    echo "📝 kb-do.sh create-pattern $name"
    echo "   创建: framework/ops/framework-patterns/$filename"
    if [ -n "$new_count" ]; then
        echo "   索引: 正模式索引 #$new_count"
        echo "   计数: $old_count → $new_count"
    else
        echo "   索引: 无正模式索引.md，未更新索引"
    fi
}

main "$@"
