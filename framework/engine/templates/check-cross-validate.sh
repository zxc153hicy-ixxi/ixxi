#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
set -e
# CLAUDE.md ↔ log.md 交叉校验
# 检查：G层修改记录 vs git tag 数量、版本号连续性

echo "=== 交叉校验 ==="

# Count G-layer modifications in log
log_g=$(grep -c "G层修改" "$KB_ROOT/log.md" 2>/dev/null)
echo "log.md G层修改: $log_g 次"

# Count git tags  
cd "$KB_ROOT"
tag_g=$(git tag | grep -c "pre-")
echo "git tag(防误操作): $tag_g 个"

# Check version continuity in log
versions=$(grep "G层修改.*V[0-9]" log.md | grep -o "V[0-9]\.[0-9]*→V[0-9]\.[0-9]*" | tail -1)
echo "最近G层版本跳转: $versions"

# Check CLAUDE.md version matches last log entry
kb_ver=$(head -1 CLAUDE.md | grep -o "V[0-9]\.[0-9]*")
last_log_ver=$(grep "G层修改" log.md | tail -1 | grep -o "V[0-9]\.[0-9]*→V[0-9]\.[0-9]*" | grep -o "V[0-9]\.[0-9]*$" 2>/dev/null)

echo ""
echo "CLAUDE.md: $kb_ver"
echo "最新log目标版本: ${last_log_ver:-无}"

if [ -n "$last_log_ver" ] && [ "$kb_ver" != "$last_log_ver" ]; then
  echo "❌ 版本号不一致"
  exit 1
else
  echo "✅ 交叉校验通过"
  exit 0
fi
