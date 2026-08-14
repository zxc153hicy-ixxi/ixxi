#!/bin/bash
KB_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
set -e
# 敏感信息扫描——在Ingest前运行
# 检测：身份证/银行卡/手机号/邮箱/密码/API密钥/JWT/AWS Key

SOURCE="$KB_ROOT/raw"
HITS=0

echo "=== 敏感信息扫描 ==="

# 身份证 (18位)
id_hits=$(grep -rPn "[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]" "$SOURCE" --include="*.md" --include="*.txt" 2>/dev/null | wc -l)
[ "$id_hits" -gt 0 ] && echo "  ⚠️  身份证号: $id_hits 处" && HITS=$((HITS + id_hits))

# 银行卡 (16-19位)
bank_hits=$(grep -rPn "[3-6]\d{15,18}" "$SOURCE" --include="*.md" --include="*.txt" 2>/dev/null | wc -l)
[ "$bank_hits" -gt 0 ] && echo "  ⚠️  疑似银行卡号: $bank_hits 处" && HITS=$((HITS + bank_hits))

# 手机号 (中国)
phone_hits=$(grep -rPn "1[3-9]\d{9}" "$SOURCE" --include="*.md" --include="*.txt" 2>/dev/null | wc -l)
[ "$phone_hits" -gt 0 ] && echo "  ⚠️  手机号: $phone_hits 处" && HITS=$((HITS + phone_hits))

# 邮箱
email_hits=$(grep -rPn "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" "$SOURCE" --include="*.md" --include="*.txt" 2>/dev/null | wc -l)
[ "$email_hits" -gt 0 ] && echo "  ⚠️  邮箱: $email_hits 处" && HITS=$((HITS + email_hits))

# API密钥 (sk-开头)
key_hits=$(grep -rPn "sk-[a-zA-Z0-9]{20,}" "$SOURCE" --include="*.md" --include="*.txt" 2>/dev/null | wc -l)
[ "$key_hits" -gt 0 ] && echo "  ⚠️  API密钥(sk-): $key_hits 处" && HITS=$((HITS + key_hits))

# JWT Token
jwt_hits=$(grep -rPn "eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+" "$SOURCE" --include="*.md" --include="*.txt" 2>/dev/null | wc -l)
[ "$jwt_hits" -gt 0 ] && echo "  ⚠️  JWT Token: $jwt_hits 处" && HITS=$((HITS + jwt_hits))

# AWS Key
aws_hits=$(grep -rPn "AKIA[0-9A-Z]{16}" "$SOURCE" --include="*.md" --include="*.txt" 2>/dev/null | wc -l)
[ "$aws_hits" -gt 0 ] && echo "  ⚠️  AWS Access Key: $aws_hits 处" && HITS=$((HITS + aws_hits))

# 密码字段
pwd_hits=$(grep -rPn "(password|passwd|secret|token|密码)\s*[:=]\s*\S+" "$SOURCE" --include="*.md" --include="*.txt" -i 2>/dev/null | wc -l)
[ "$pwd_hits" -gt 0 ] && echo "  ⚠️  密码/Token明文: $pwd_hits 处" && HITS=$((HITS + pwd_hits))

echo ""
if [ "$HITS" -eq 0 ]; then
  echo "✅ 未发现敏感信息"
  exit 0
else
  echo "❌ 发现 $HITS 处敏感信息，Ingest前需确认"
  exit 1
fi
