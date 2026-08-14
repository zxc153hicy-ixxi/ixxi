#!/bin/bash
# desc: 重命名文件并自动替换全量引用（wikilink + 路径）
# usage: kb-do.sh rename <旧路径> <新路径>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../_lib/git.sh"
source "$SCRIPT_DIR/../_lib/link.sh"

KB_ROOT=$(kb_root)

main() {
    if [ $# -lt 2 ]; then
        echo "用法: kb-do.sh rename <旧路径> <新路径>" >&2
        echo "示例: kb-do.sh rename ops/rules/旧名.md ops/rules/新名.md" >&2
        exit 1
    fi

    local old_path="$1"
    local new_path="$2"

    # 支持相对路径：确保以仓库根为基准
    local old_abs="$KB_ROOT/$old_path"
    local new_abs="$KB_ROOT/$new_path"

    if [ ! -f "$old_abs" ]; then
        echo "❌ 旧文件不存在: $old_path" >&2
        exit 1
    fi

    if [ -f "$new_abs" ]; then
        echo "❌ 新文件已存在: $new_path" >&2
        exit 1
    fi

    git_backup "rename"

    # E1: git mv
    if ! git mv "$old_path" "$new_path"; then
        git_rollback "git mv 失败"
    fi

    # E2-E3: 扫描并替换全量引用
    local old_basename
    old_basename=$(basename "$old_path" .md)
    local new_basename
    new_basename=$(basename "$new_path" .md)

    replace_references "$old_basename.md" "$new_basename.md"

    # 同时替换路径引用（如 ops/rules/旧名.md → ops/rules/新名.md）
    find "$KB_ROOT" -type f -name "*.md" \
        ! -path "*/.git/*" \
        ! -path "*/archive/*" \
        -exec sed -i "s|${old_path}|${new_path}|g" {} \;

    git_cleanup

    # 统计替换了多少文件
    local ref_count
    ref_count=$(find_references "$new_basename.md" 2>/dev/null | wc -l)

    echo "📝 kb-do.sh rename $old_path → $new_path"
    echo "   重命名: $old_path → $new_path"
    echo "   引用: 约 ${ref_count} 处引用已更新"
}

main "$@"
