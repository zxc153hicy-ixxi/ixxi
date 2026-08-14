# malicious-samples —— 恶意样例回归夹具（Task 1.1）

本目录是 ixxi 安全工具链（Task 1.1，供应链安全防线，智谱风险 3.1/3.2）的**测试夹具**，
用于验证 `scan-sensitive.py` 攻击面检测能力的回归测试，**禁止混入正常脚本**。

## 目录约定

- 每类攻击面一个文件，文件名带序号 + 类别名，用文件头注释标注类别与触发规则。
- 全部文件**故意包含恶意触发模式**，因此：
  - 本目录由 `ci.yml` 的「恶意样例回归」步骤显式引用扫描；
  - 本目录会被 `scan-sensitive.py` 判定为命中（退出码非零）——这是预期行为；
  - semgrep / bandit 等工具在 CI 中通过路径/排除参数跳过本目录，避免夹具污染真实扫描。
- 若将来对全仓库跑 `scan-sensitive.py`，请在本目录之外排除本路径
  （例如把 `engine/scripts/malicious-samples` 加入扫描器的教学目录跳过清单）。

## 清单（5 类攻击面）

| 序号 | 文件 | 攻击面类别 | 触发规则 |
|:--:|------|------|------|
| 1 | `sample-01-base64-backdoor.py` | Base64 解码执行 | 长 base64 串解码后含危险执行模式 |
| 2 | `sample-02-env-exfil.py` | 环境变量外泄 | 环境变量读取与网络请求同现于一行 |
| 3 | `sample-03-path-traversal.py` | 路径穿越 | 相对上级目录序列与文件读写同现 |
| 4 | `sample-04-git-hooks-injection.py` | Git 钩子注入 | 钩子目录路径与写打开操作同现/相邻 |
| 5 | `sample-05-dependency-poisoning.sh` | 依赖投毒 | 依赖源指向非官方地址 |

## 回归验证命令

```bash
python framework/engine/scripts/scan-sensitive.py --repo framework/engine/scripts/malicious-samples
# 期望：5 类攻击面全部命中，退出码非零（1）
```
