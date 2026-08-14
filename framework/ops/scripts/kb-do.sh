#!/bin/bash
# kb-do.sh · 原子操作入口
# 用法: kb-do.sh <action> [args...]
#       kb-do.sh list      列出所有可用操作
#
# LLM 通过此入口调用所有原子操作，禁止直接调 actions/ 下的脚本。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ACTIONS_DIR="$SCRIPT_DIR/actions"

# --- list 命令 ---
list_actions() {
    echo "可用操作："
    local found=false
    for script in "$ACTIONS_DIR"/*.sh; do
        if [ -f "$script" ]; then
            found=true
            local name
            name=$(basename "$script" .sh)
            local desc
            desc=$(grep '^# desc:' "$script" | head -1 | sed 's/^# desc: //')
            local usage
            usage=$(grep '^# usage:' "$script" | head -1 | sed 's/^# usage: //')
            printf "  %-35s %s\n" "$usage" "$desc"
        fi
    done
    if [ "$found" = false ]; then
        echo "  （暂无可用操作，将 .sh 脚本放入 actions/ 目录即可注册）"
    fi
}

# --- 主入口 ---
main() {
    if [ $# -eq 0 ]; then
        echo "用法: kb-do.sh <action> [args...]"
        echo "      kb-do.sh list"
        echo ""
        list_actions
        exit 1
    fi

    local action="$1"
    shift

    case "$action" in
        list)
            list_actions
            ;;
        *)
            local action_script="$ACTIONS_DIR/$action.sh"
            if [ -f "$action_script" ]; then
                bash "$action_script" "$@"
            else
                echo "❌ 未知操作: $action"
                echo "运行 'kb-do.sh list' 查看可用操作"
                exit 1
            fi
            ;;
    esac
}

main "$@"
