#!/bin/bash
# desc: 创建规则文件，注册到 index.md 导航
# usage: kb-do.sh create-rule <名称>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../_lib/git.sh"

KB_ROOT=$(kb_root)
# 实际布局：规则在 framework/ops/rules，主导航在 framework/index.md（仓库根无 index.md）
RULES_DIR="$KB_ROOT/framework/ops/rules"
MAIN_INDEX="$KB_ROOT/framework/index.md"

main() {
    if [ $# -lt 1 ]; then
        echo "用法: kb-do.sh create-rule <名称>" >&2
        echo "示例: kb-do.sh create-rule 修复与创建规范" >&2
        exit 1
    fi

    local name="$1"
    local filename="${name}.md"
    local filepath="$RULES_DIR/$filename"
    local today
    today=$(date +%Y-%m-%d)

    git_backup "create-rule"

    # E1: 检查是否已存在
    if [ -f "$filepath" ]; then
        git_rollback "文件已存在: $filepath"
    fi

    # E2: 写入模板文件
    cat > "$filepath" << EOF
---
tags: [规则]
status: active
summary: $name
created: $today
updated: $today
---

# $name

## 概述


## 关联

- [[index]] —— 全局导航
EOF

    if [ ! -f "$filepath" ]; then
        git_rollback "写入模板文件失败: $filepath"
    fi

    # E3: 注册到 framework/index.md 的「规则」区块
    if grep -q "^## 规则" "$MAIN_INDEX"; then
        # 找到「## 规则」区块后最后一个 [[ops/rules/ 引用，在其后插入
        local section_line
        section_line=$(grep -n '^## 规则' "$MAIN_INDEX" | head -1 | cut -d: -f1)
        # 往该区块后找最后一个 [[ops/rules/ 引用行
        local last_rule_line
        last_rule_line=$(tail -n +"$section_line" "$MAIN_INDEX" | grep -n '\[\[ops/rules/' | tail -1 | cut -d: -f1)
        if [ -n "$last_rule_line" ]; then
            local target_line=$((section_line + last_rule_line))
            sed -i "${target_line}a- [[ops/rules/${filename%.md}|$name]] —— 待补充" "$MAIN_INDEX"
        else
            # 没有已有规则引用，在「## 规则」下一行插入
            sed -i "${section_line}a- [[ops/rules/${filename%.md}|$name]] —— 待补充" "$MAIN_INDEX"
        fi
    else
        git_rollback "framework/index.md 中未找到「规则」区块，请手动注册"
    fi

    git_cleanup

    echo "📝 kb-do.sh create-rule $name"
    echo "   创建: framework/ops/rules/$filename"
    echo "   注册: framework/index.md 「规则」区块"
}

main "$@"
