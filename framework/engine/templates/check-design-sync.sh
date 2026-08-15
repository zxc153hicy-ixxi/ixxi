#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
set -e
# 检查 CLAUDE.md 版本号 vs 设计方案版本号是否一致

KB_VER=$(head -1 "$KB_ROOT/CLAUDE.md" | grep -o "V[0-9]\.[0-9]*")
DESIGN_DIR="$(git rev-parse --show-toplevel)/../知识库方案"
# sort -V 非 POSIX（macOS/BSD 无），改 python 取版本号最大者
DESIGN_VER=$(ls -d "$DESIGN_DIR"/V*-模块化 2>/dev/null | python -c "
import sys, re
vers = []
for l in sys.stdin.read().splitlines():
    m = re.search(r'V[0-9]+(\.[0-9]+)*', l)
    if m:
        vers.append(m.group(0))
if vers:
    print(max(vers, key=lambda v: tuple(int(x) for x in v[1:].split('.'))))
" 2>/dev/null)

echo "KB版本:     $KB_VER"
echo "设计方案:   $DESIGN_VER"

if [ "$KB_VER" = "$DESIGN_VER" ]; then
  echo "✅ 版本一致"
  exit 0
else
  echo "❌ 版本不一致——KB是$KB_VER但设计方案是$DESIGN_VER，需要同步"
  exit 1
fi
