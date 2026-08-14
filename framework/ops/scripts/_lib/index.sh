#!/bin/bash
# desc: 索引文件操作——插入行、删除行、重排编号、更新计数
# usage: source 此文件后调用函数

# 重排索引文件中的表格编号（| # | 列 → 1→N 连续）
# 用法: renumber_index "ops/patterns/正模式索引.md"
renumber_index() {
    local index_file="$1"
    if [ ! -f "$index_file" ]; then
        echo "❌ 索引文件不存在: $index_file" >&2
        return 1
    fi

    local tmpfile
    tmpfile=$(mktemp)
    local n=1

    while IFS= read -r line; do
        if echo "$line" | grep -qE '^\| [0-9]+ \|'; then
            echo "$line" | sed -E "s/^\| [0-9]+ \|/| $n |/"
            n=$((n + 1))
        else
            echo "$line"
        fi
    done < "$index_file" > "$tmpfile"

    mv "$tmpfile" "$index_file"
}

# 在索引文件表格末尾追加一行（用占位编号，等待 renumber_index 统一处理）
# 用法: append_index_row "ops/patterns/正模式索引.md" "[[新文件]] | 一句话描述"
append_index_row() {
    local index_file="$1"
    local new_row="$2"

    if [ ! -f "$index_file" ]; then
        echo "❌ 索引文件不存在: $index_file" >&2
        return 1
    fi

    # 找到最后一个表格行，在其后插入新行
    local last_table_line
    last_table_line=$(grep -nE '^\| [0-9]+ \|' "$index_file" | tail -1 | cut -d: -f1)

    if [ -z "$last_table_line" ]; then
        echo "❌ 索引文件中未找到表格行" >&2
        return 1
    fi

    sed -i "${last_table_line}a| 99 | ${new_row}" "$index_file"
}

# 从索引文件中删除匹配 pattern 的行
# 用法: remove_index_row "ops/patterns/正模式索引.md" "原子化操作"
remove_index_row() {
    local index_file="$1"
    local pattern="$2"

    if [ ! -f "$index_file" ]; then
        echo "❌ 索引文件不存在: $index_file" >&2
        return 1
    fi

    sed -i "/^| [0-9]\+ | .*${pattern}.*/d" "$index_file"
}

# 更新 index.md 中正/反模式的计数
# 用法: update_main_count "patterns" "正模式索引" 22
update_main_count() {
    local section="$1"
    local display_name="$2"
    local new_count="$3"

    local main_index
    main_index="$(git rev-parse --show-toplevel 2>/dev/null)/index.md"

    if [ ! -f "$main_index" ]; then
        echo "❌ index.md 不存在" >&2
        return 1
    fi

    # 匹配格式: [[ops/patterns/正模式索引|正模式索引]]（N 条）
    sed -i "s/\(\[\[ops\/${section}\/[^]]*|${display_name}\]\]（\)[0-9]\+\( 条\)/\1${new_count}\2/" "$main_index"
}

# 获取当前索引条目数
# 用法: count_index_entries "ops/patterns/正模式索引.md"
count_index_entries() {
    local index_file="$1"
    grep -cE '^\| [0-9]+ \|' "$index_file" 2>/dev/null || echo 0
}
