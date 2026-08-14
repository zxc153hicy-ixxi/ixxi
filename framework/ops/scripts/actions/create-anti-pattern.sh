#!/bin/bash
# desc: 创建反模式文件，插入索引，重排编号，更新计数
# usage: kb-do.sh create-anti-pattern <名称>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../_lib/git.sh"
source "$SCRIPT_DIR/../_lib/index.sh"

KB_ROOT=$(kb_root)
ANTI_PATTERNS_DIR="$KB_ROOT/ops/anti-patterns"
INDEX_FILE="$ANTI_PATTERNS_DIR/反模式索引.md"

main() {
    if [ $# -lt 1 ]; then
        echo "用法: kb-do.sh create-anti-pattern <名称>" >&2
        echo "示例: kb-do.sh create-anti-pattern 索引忘记更新" >&2
        exit 1
    fi

    local name="$1"
    local filename="${name}.md"
    local filepath="$ANTI_PATTERNS_DIR/$filename"
    local today
    today=$(date +%Y-%m-%d)

    git_backup "create-anti-pattern"

    # E1: 检查是否已存在
    if [ -f "$filepath" ]; then
        git_rollback "文件已存在: $filepath"
    fi

    # E2: 写入模板文件
    cat > "$filepath" << EOF
---
tags: [反模式]
status: active
summary: $name——（待补充）
created: $today
updated: $today
---

# $name

> 反模式 = 踩过的坑。

## 发生了什么


## 根因


## 怎么修的

EOF

    if [ ! -f "$filepath" ]; then
        git_rollback "写入模板文件失败: $filepath"
    fi

    # E3: 追加到索引
    local old_count
    old_count=$(count_index_entries "$INDEX_FILE")
    append_index_row "$INDEX_FILE" "[[$name]] | （待补充）"

    # E4: 重排编号
    renumber_index "$INDEX_FILE"

    # E5: 更新 index.md 计数
    local new_count
    new_count=$(count_index_entries "$INDEX_FILE")
    update_main_count "anti-patterns" "反模式索引" "$new_count"

    git_cleanup

    # E6: 输出摘要
    echo "📝 kb-do.sh create-anti-pattern $name"
    echo "   创建: ops/anti-patterns/$filename"
    echo "   索引: 反模式索引 #$new_count"
    echo "   计数: $old_count → $new_count"
}

main "$@"
