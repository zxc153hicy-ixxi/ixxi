---
name: kb-export-template
description: Use when executing /export-template or when the user says "导出" "打包" "备份" "迁移".
---

# kb-export-template

## Overview
导出知识库骨架模板（framework 通用层），排除个人数据。私有目录清单 `framework/engine/config/private-paths.txt`（`ixxi init` 生成，单一事实源），export 与预检均读它，个人目录绝不外流。

## Quick Reference
执行脚本: `bash framework/engine/templates/export-template.sh`

导出前自动预检: frontmatter 完整性 / 敏感信息 / 版本一致性。详见 [[framework/ops/rules/系统操作菜单]]。
