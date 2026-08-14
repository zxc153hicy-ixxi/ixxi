#!/usr/bin/env python3
# ============================================================
# 恶意样例 · 类别 3/5：路径穿越
# 触发规则：同一行内 ../（或 ..\）序列 与 文件读写操作
#           （open/Path/read_text/.read()/.write() 等）同现
# 对应检测：scan-sensitive.py → detect_path_traversal（攻击面:路径穿越）
# 用途：scan-sensitive 攻击面回归的黄金对比例，禁止混入正常脚本
# ============================================================


def read_etc_passwd():
    # 恶意行为：../ 跳出工作目录读取系统口令文件（攻击面 5）
    data = open("../../../etc/passwd").read()
    return data
