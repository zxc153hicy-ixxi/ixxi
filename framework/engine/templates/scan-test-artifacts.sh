#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
set -e
# 测试文件扫描——找出可能的测试残留
# 不自动删除，仅列清单
S="$KB_ROOT"

echo "=== 测试文件扫描 ==="

# 1. 目录名含测试关键词
echo "【测试目录】"
find "$S" -type d -iname "*test*" -not -name "test-cleanup.sh" -not -name "scan-test-artifacts.sh" -not -name ".test-manifest" -o -iname "*模拟*" -o -iname "*demo*" -o -iname "*dry*run*" 2>/dev/null | grep -v ".git" | while read d; do
  count=$(find "$d" -type f | wc -l)
  echo "  $d ($count 文件)"
done | grep "." || echo "  无"

# 2. 文件名含测试关键词
echo "【测试文件】"
find "$S" -type f -not -name "scan-test-artifacts.sh" \( -iname "*test*" -not -name "test-cleanup.sh" -not -name "scan-test-artifacts.sh" -not -name ".test-manifest" -o -iname "*模拟*" -o -iname "*dry*run*" -o -iname "*demo*" \) -not -path "*/.git/*" 2>/dev/null | while read f; do
  echo "  $f"
done | grep "." || echo "  无"

# 3. 桌面测试文件  
echo "【桌面残留】"
DESKTOP="$HOME/Desktop"
find "$DESKTOP" -maxdepth 1 -name "*test*" -o -name "*precheck*" -o -name "*模拟*" 2>/dev/null | while read f; do
  echo "  $f"
done | grep "." || echo "  无"

# 4. 0字节.md文件
echo "【0字节文件】"
find "$S" -name "*.md" -size 0 -not -path "*/.git/*" 2>/dev/null | while read f; do
  echo "  $f (空文件)"
done | grep "." || echo "  无"

echo ""
echo "=== 扫描完成 ==="
