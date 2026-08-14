#!/bin/bash
# desc: 事务性 git 操作——打标签、回滚、清理
# usage: source 此文件后调用函数

# 全局变量：当前操作的临时 tag 名
GIT_BACKUP_TAG=""

# 执行前打备份标签
# 用法: git_backup "create-pattern"
git_backup() {
    local action="$1"
    local ts
    ts=$(date +%Y%m%d-%H%M%S)
    GIT_BACKUP_TAG="auto-before-${action}-${ts}"

    if ! git tag "$GIT_BACKUP_TAG" 2>/dev/null; then
        echo "❌ 无法创建备份标签 $GIT_BACKUP_TAG，请检查 git 状态" >&2
        exit 1
    fi
}

# 回滚到备份标签
# 用法: git_rollback "步骤3失败：写入索引时出错"
git_rollback() {
    local reason="${1:-未知错误}"
    if [ -z "$GIT_BACKUP_TAG" ]; then
        echo "❌ 无备份标签可回滚" >&2
        exit 1
    fi

    echo "↩ 回滚中... 原因: $reason" >&2
    git checkout "$GIT_BACKUP_TAG" -- . 2>/dev/null
    git tag -d "$GIT_BACKUP_TAG" 2>/dev/null
    echo "❌ 操作失败，已回滚到操作前状态" >&2
    exit 1
}

# 成功后清理备份标签
# 用法: git_cleanup
git_cleanup() {
    if [ -n "$GIT_BACKUP_TAG" ]; then
        git tag -d "$GIT_BACKUP_TAG" 2>/dev/null
        GIT_BACKUP_TAG=""
    fi
}

# 获取知识库根目录（脚本所在仓库根）
kb_root() {
    git rev-parse --show-toplevel 2>/dev/null || {
        echo "❌ 不在 git 仓库中" >&2
        exit 1
    }
}
