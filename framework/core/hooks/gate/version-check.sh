#!/bin/bash
# version-check.sh — 版本一致性检查：CHANGELOG 最新版本 ↔ git tag 最新 semver
#
# 单一版本号约定（见 CHANGELOG.md「版本号约定」）：
#   框架版本 = git tag（semver 三段式 vX.Y.Z），CHANGELOG 记录每个版本改了什么。
#   本脚本在发布（打 tag）时手动跑，校验两者一致，避免「多套版本号并存」反模式。
#
# 用法：bash framework/core/hooks/gate/version-check.sh
set -e

KB_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# CHANGELOG 最新版本：## [x.y.z]
CHANGELOG_VER=$(grep -oP '^## \[\d+\.\d+\.\d+\]' "$KB_ROOT/CHANGELOG.md" 2>/dev/null | head -1 | grep -oP '\d+\.\d+\.\d+')

# git tag 最新 semver（vX.Y.Z 三段式，排除 -pre / baseline 等非发布 tag）
TAG_VER=$(git -C "$KB_ROOT" tag -l 2>/dev/null | grep -oP '^v\d+\.\d+\.\d+$' | sed 's/^v//' | sort -V | tail -1)

# 两者都缺失 → 版本机制未建立，跳过
if [ -z "$CHANGELOG_VER" ] && [ -z "$TAG_VER" ]; then
  echo "⚠️  版本机制未建立（无 CHANGELOG 版本、无 semver tag），跳过版本一致性检查"
  exit 0
fi

if [ -z "$CHANGELOG_VER" ]; then
  echo "❌ CHANGELOG 无版本号（## [x.y.z]），但存在 git tag v$TAG_VER"
  echo "   请在 CHANGELOG.md 补版本号"
  exit 1
fi
if [ -z "$TAG_VER" ]; then
  echo "❌ git 无 semver tag（vX.Y.Z），但 CHANGELOG 最新版本 $CHANGELOG_VER"
  echo "   请打: git tag v$CHANGELOG_VER"
  exit 1
fi

if [ "$CHANGELOG_VER" != "$TAG_VER" ]; then
  echo ""
  echo "⚠️  版本不一致！"
  echo "   CHANGELOG 最新: $CHANGELOG_VER"
  echo "   git tag 最新:   $TAG_VER"
  echo ""
  echo "   发布前对齐：更新 CHANGELOG 版本号 或 打对应 git tag"
  exit 1
fi

echo "✅ 版本一致: v$CHANGELOG_VER"
exit 0
