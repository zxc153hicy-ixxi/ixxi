#!/bin/bash
# desc: wikilink 扫描与替换——查找所有引用某文件的 .md 文件并批量替换
# usage: source 此文件后调用函数

# 查找所有引用指定文件名的 .md 文件
# 用法: find_references "旧文件名.md"
# 返回: 引用该文件的 .md 文件路径列表（stdout）
find_references() {
    local target="$1"
    local kb_root
    kb_root=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")

    local basename
    basename=$(basename "$target" .md)

    find "$kb_root" -type f -name "*.md" \
        ! -path "*/.git/*" \
        ! -path "*/archive/*" \
        -exec grep -l "\[\[${basename}\]\]\|\[\[${basename}|" {} \; 2>/dev/null
}

# 在所有 .md 文件中替换旧引用为新引用
# 用法: replace_references "旧文件名.md" "新文件名.md"
replace_references() {
    local old_name="$1"
    local new_name="$2"
    local kb_root
    kb_root=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")

    local old_basename="${old_name%.md}"
    local new_basename="${new_name%.md}"

    # 替换四种 wikilink 格式:
    # [[旧名]] → [[新名]]
    # [[旧名|别名]] → [[新名|别名]]
    # [[旧名.md]] → [[新名.md]]
    # [[旧名.md|别名]] → [[新名.md|别名]]
    find "$kb_root" -type f -name "*.md" \
        ! -path "*/.git/*" \
        ! -path "*/archive/*" \
        -exec sed -i \
            -e "s/\[\[${old_basename}\]\]/[[${new_basename}]]/g" \
            -e "s/\[\[${old_basename}|/[[${new_basename}|/g" \
            -e "s/\[\[${old_name}\]\]/[[${new_name}]]/g" \
            -e "s/\[\[${old_name}|/[[${new_name}|/g" \
            {} \;
}
