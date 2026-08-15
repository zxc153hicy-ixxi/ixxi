#!/bin/bash
# desc: 删除文件并清理索引引用，重排编号，更新计数
# usage: kb-do.sh delete <路径>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../_lib/git.sh"
source "$SCRIPT_DIR/../_lib/index.sh"
source "$SCRIPT_DIR/../_lib/link.sh"

KB_ROOT=$(kb_root)

main() {
    if [ $# -lt 1 ]; then
        echo "用法: kb-do.sh delete <路径>" >&2
        echo "示例: kb-do.sh delete ops/patterns/旧模式.md" >&2
        exit 1
    fi

    local path="$1"
    local abs_path="$KB_ROOT/$path"

    # 安全检查：禁止删除目录
    if [ -d "$abs_path" ]; then
        echo "❌ 禁止删除目录: $path" >&2
        exit 1
    fi

    if [ ! -f "$abs_path" ]; then
        echo "❌ 文件不存在: $path" >&2
        exit 1
    fi

    # 安全检查：禁止删除系统关键文件
    local basename
    basename=$(basename "$path")
    local protected="AGENT.md|index.md|queue.md|log.md|session-notes.md"
    if echo "$basename" | grep -qE "^($protected)$"; then
        echo "❌ 禁止删除受保护的系统文件: $basename" >&2
        exit 1
    fi

    git_backup "delete"

    # E1: 扫全量引用（仅用于输出摘要）
    local refs
    refs=$(find_references "$basename" 2>/dev/null || true)

    # E2: 删除文件（先试 git rm，失败则普通 rm）
    if git rm "$path" 2>/dev/null; then
        : # git rm 成功
    elif rm "$abs_path" 2>/dev/null; then
        : # 文件未跟踪，普通 rm 成功
    else
        git_rollback "删除文件失败: $path"
    fi

    # E3: 清理索引引用 + 重排编号 + 更新计数
    local basename_noext="${basename%.md}"

    # 检查正模式索引（实际布局：正/反模式平铺在 framework/ops/framework-patterns，当前无正模式索引.md）
    local pattern_index="$KB_ROOT/framework/ops/framework-patterns/正模式索引.md"
    if [ -f "$pattern_index" ]; then
        if grep -q "\[\[$basename_noext\]\]" "$pattern_index" 2>/dev/null; then
            remove_index_row "$pattern_index" "$basename_noext"
            renumber_index "$pattern_index"
            local pc
            pc=$(count_index_entries "$pattern_index")
            update_main_count "patterns" "正模式索引" "$pc"
        fi
    fi

    # 检查反模式索引（当前无反模式索引.md）
    local anti_index="$KB_ROOT/framework/ops/framework-patterns/反模式索引.md"
    if [ -f "$anti_index" ]; then
        if grep -q "\[\[$basename_noext\]\]" "$anti_index" 2>/dev/null; then
            remove_index_row "$anti_index" "$basename_noext"
            renumber_index "$anti_index"
            local ac
            ac=$(count_index_entries "$anti_index")
            update_main_count "anti-patterns" "反模式索引" "$ac"
        fi
    fi

    # E4: 清理 framework/index.md 中的导航引用
    local main_index="$KB_ROOT/framework/index.md"
    if [ -f "$main_index" ]; then
        if grep -q "\[\[$path\]\]" "$main_index" 2>/dev/null; then
            sed -i "\|\[\[$path\]\]|d" "$main_index"
        fi
    fi

    git_cleanup

    echo "📝 kb-do.sh delete $path"
    echo "   删除: $path"
    echo "   引用: ${refs:-无}"
}

main "$@"
