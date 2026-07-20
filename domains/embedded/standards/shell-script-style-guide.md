---
title: Shell 脚本风格规范
doc_type: standard
knowledge_type: guideline
maturity: verified
status: archived
searchable: false
owner: team-core
created: 2026-05-17
last_updated: 2026-05-17
tags: [shell, script, style, shellcheck, shfmt]
related: [personal-development-enhancements.md, knowledge-contribution-guide.md, ../runbooks/dev-tooling-setup-guide.md]
validation_refs: [../../scripts/check-shell-style.sh]
---

# Shell 脚本风格规范

## 1. 基本规则

团队维护的 Shell 脚本默认使用 Bash：

```bash
#!/usr/bin/env bash
set -euo pipefail
```

例外：需要在目标板 BusyBox `sh` 上直接执行的脚本，必须在文件头或 README 中说明兼容范围。

## 2. 路径与目录

仓库内脚本应使用稳定根目录定位：

```bash
ROOT="$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
```

禁止依赖调用者当前目录，除非脚本文档明确要求。

## 3. 变量引用

1. 变量展开默认加双引号。
2. 路径拼接必须显式处理空值。
3. 临时目录用 `mktemp -d`，并配套 `trap` 清理。
4. 不把不可信输入拼进 `eval` 或未转义 shell 命令。

## 4. 格式化

统一使用 `shfmt`：

```bash
rtk bash scripts/check-shell-style.sh
```

脚本缩进遵循 `.editorconfig`：Shell 使用 tab，Markdown/Python/YAML 使用空格。

## 5. ShellCheck 豁免

允许局部豁免，但必须靠近触发行并说明范围：

```bash
# shellcheck disable=SC2012
ls -lh "$APP_DIR" 2>/dev/null | sed -n '1,120p'
```

禁止全文件大范围关闭 ShellCheck，除非该脚本必须兼容特殊 shell 方言，并在 README 中说明原因。

## 6. 验证

提交前至少执行：

```bash
rtk bash scripts/check-all.sh
```

只验证脚本风格：

```bash
rtk bash scripts/check-shell-style.sh --strict
```
