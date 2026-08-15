#!/usr/bin/env python3
# ============================================================
# 恶意样例 · 类别 6/6：混淆代码（hex 转义 / chr 拼接 / __import__ 拼接）
# 触发规则：exec/eval 参数含 \xNN hex 转义、chr(...)+ 拼接，或
#           __import__ 参数带字符串拼接——动态构造可执行代码的混淆手法
# 对应检测：scan-sensitive.py → detect_obfuscation（攻击面:混淆代码）
# 用途：scan-sensitive 攻击面回归的黄金对比例，禁止混入正常脚本
# ============================================================


def hex_escape_exec():
    # 手法①：exec 参数用 \xNN hex 转义构造 "import os"（攻击面 6）
    exec('\x69\x6d\x70\x6f\x72\x74\x20\x6f\x73')


def chr_concat_eval():
    # 手法②：eval 参数用 chr(...)+ 拼接构造 "os.system('id')"（攻击面 6）
    eval(chr(111) + chr(115) + chr(46) + chr(115) + chr(121) + chr(115) +
         chr(116) + chr(101) + chr(109) + chr(40) + chr(39) + chr(105) +
         chr(100) + chr(39) + chr(41))


def import_concat():
    # 手法③：__import__ 参数带字符串拼接构造 "os"（攻击面 6）
    os_mod = __import__("o" + "s")
    os_mod.system("id")


if __name__ == "__main__":
    hex_escape_exec()
    chr_concat_eval()
    import_concat()
