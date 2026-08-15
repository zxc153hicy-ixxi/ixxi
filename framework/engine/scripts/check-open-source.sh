#!/bin/bash
# check-open-source.sh — 开源前检查一键脚本（对应 docs/guides/开源检查流程.md）
# 用法：bash framework/engine/scripts/check-open-source.sh
# 首次开源 / 每次 release / 有外部贡献者加入前跑一遍。

KB_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
FRAMEWORK="$KB_ROOT/framework"

echo "=== 开源前检查 ==="
echo ""

# 1. 个人数据零残留
echo "[1] 个人数据零残留"
PII=$(grep -rn '29909\|源质挽歌\|D:/KnowledgeBase\|C:/Users' "$FRAMEWORK"/ --include='*.md' --include='*.py' --include='*.sh' --include='*.json' --include='*.yaml' 2>/dev/null | grep -v '_external/')
PII_COUNT=$(printf '%s' "$PII" | grep -c . 2>/dev/null || echo 0)
echo "  命中 $PII_COUNT 处（应只含检查标准示例，无真实数据）"
if [ -n "$PII" ]; then echo "$PII" | head -5 | sed 's/^/    /'; fi

# 2. 适配层产物不进 git
echo ""
echo "[2] 适配层产物不进 git"
ADAPTER=$(git -C "$KB_ROOT" ls-files framework/.claude framework/.agents framework/.codex)
ADAPTER_COUNT=$(printf '%s' "$ADAPTER" | grep -c . 2>/dev/null || echo 0)
if [ "$ADAPTER_COUNT" -gt 0 ]; then
  echo "  ❌ $ADAPTER_COUNT 个适配层文件被跟踪（应 git rm --cached）"
  echo "$ADAPTER" | head -5 | sed 's/^/    /'
else
  echo "  ✅ 0 个"
fi

# 3. 敏感信息
echo ""
echo "[3] 敏感信息扫描"
python "$FRAMEWORK/engine/scripts/scan-sensitive.py" --repo "$FRAMEWORK" 2>&1 | grep -E '发现|✅|❌|密钥|密码|身份证' | head -8 | sed 's/^/    /'

# 4. git 工作区干净
echo ""
echo "[4] git 工作区干净"
DIRTY=$(git -C "$KB_ROOT" status --short)
if [ -n "$DIRTY" ]; then
  echo "  ❌ 有未提交改动："
  echo "$DIRTY" | head -10 | sed 's/^/    /'
else
  echo "  ✅ 干净"
fi

# 5. 许可证
echo ""
echo "[5] 许可证"
test -f "$KB_ROOT/LICENSE" && echo "  ✅ LICENSE 存在" || echo "  ❌ 缺 LICENSE"

# 6. README badge 占位
echo ""
echo "[6] README badge"
if grep -q '<owner>' "$KB_ROOT/README.md" 2>/dev/null; then
  echo "  ⚠️ badge 仍是占位（有仓库后替换 <owner>/<repo>）"
else
  echo "  ✅ 无占位"
fi

# 7. 版本一致
echo ""
echo "[7] 版本一致"
bash "$FRAMEWORK/core/hooks/gate/version-check.sh" 2>&1 | sed 's/^/    /'

echo ""
echo "=== 检查完成 ==="
