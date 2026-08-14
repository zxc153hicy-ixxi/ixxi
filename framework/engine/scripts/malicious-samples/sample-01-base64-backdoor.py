#!/usr/bin/env python3
# ============================================================
# 恶意样例 · 类别 1/5：Base64 解码执行后门
# 触发规则：≥32 位 base64 串解码后为可打印文本，且包含
#           exec/eval/__import__/os.system/subprocess/socket 等危险执行模式
# 对应检测：scan-sensitive.py → detect_base64_code（攻击面:Base64解码执行）
# 用途：scan-sensitive 攻击面回归的黄金对比例，禁止混入正常脚本
# ============================================================

import base64

# 恶意载荷：解码后为 exec("import os; os.system('id')")，可在目标机执行任意命令
payload = "ZXhlYygiaW1wb3J0IG9zOyBvcy5zeXN0ZW0oJ2lkJykiKQ=="


def execute_remote():
    # 后门入口：把 base64 载荷解码后交给 exec 动态执行（攻击面 1）
    exec(base64.b64decode(payload))


if __name__ == "__main__":
    execute_remote()
