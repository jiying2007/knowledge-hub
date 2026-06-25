---
title: 个人开发工具安装指南
doc_type: runbook
knowledge_type: process
maturity: verified
status: active
owner: team-core
created: 2026-05-17
last_updated: 2026-05-17
tags: [dev-tools, bootstrap, shellcheck, shfmt]
related: [team-onboarding-guide.md, ../standards/personal-development-enhancements.md, ../standards/shell-script-style-guide.md]
validation_refs: [../../scripts/bootstrap-dev-tools.sh, ../../scripts/check-tools.sh]
---

# 个人开发工具安装指南

## 1. 目标

统一团队个人开发机上的基础工具，避免知识库门禁在不同成员机器上表现不一致。

## 2. 推荐工具

| 工具 | 用途 |
| --- | --- |
| `shellcheck` | Shell 静态检查 |
| `shfmt` | Shell 格式化 |
| `rg` | 快速文本搜索 |
| `fd` | 快速文件枚举 |
| `jq` | JSON 处理 |
| `yq` | YAML 处理 |
| `tmux` | 长任务终端保持 |
| `direnv` | 按目录加载环境变量 |

## 3. 检查工具状态

```bash
cd "$EMBEDDED_KNOWLEDGE_HOME"
rtk bash scripts/check-tools.sh
```

严格模式：

```bash
rtk bash scripts/check-tools.sh --strict
```

## 4. 一键安装

干跑查看计划：

```bash
rtk bash scripts/bootstrap-dev-tools.sh
```

执行安装：

```bash
rtk bash scripts/bootstrap-dev-tools.sh --install
```

如果无法访问 GitHub release，可跳过 `shfmt/yq` 二进制安装：

```bash
rtk bash scripts/bootstrap-dev-tools.sh --install --no-github
```

## 5. direnv 启用

Bash 用户在 `~/.bashrc` 中加入：

```bash
eval "$(direnv hook bash)"
```

之后在项目目录创建 `.envrc`，例如：

```bash
export EMBEDDED_KNOWLEDGE_HOME="$HOME/embedded/knowledge"
source "$EMBEDDED_KNOWLEDGE_HOME/profiles/pcr02.env"
```

首次进入目录后执行：

```bash
direnv allow
```

## 6. 验证

安装后执行：

```bash
rtk bash scripts/check-tools.sh --strict
rtk bash scripts/check-all.sh
```
