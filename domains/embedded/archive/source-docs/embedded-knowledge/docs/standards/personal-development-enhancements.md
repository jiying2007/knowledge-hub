---
title: 个人开发增强建议
doc_type: standard
knowledge_type: guideline
maturity: verified
status: active
owner: team-core
created: 2026-05-17
last_updated: 2026-05-17
tags: [personal-dev, workflow, productivity]
related: [../runbooks/team-onboarding-guide.md, ../runbooks/dev-tooling-setup-guide.md, knowledge-contribution-guide.md, shell-script-style-guide.md]
validation_refs: []
---

# 个人开发增强建议

## 1. 基础环境

建议每个开发者本机固定配置：

```bash
export EMBEDDED_KNOWLEDGE_HOME="$HOME/embedded/knowledge"
git config --global core.editor vim
git config --global pull.ff only
git config --global fetch.prune true
```

## 2. 提交前检查

每个 knowledge clone 启用本地 hook：

```bash
cd "$EMBEDDED_KNOWLEDGE_HOME"
git config core.hooksPath .githooks
```

如果机器安装了 `shellcheck` 与 `shfmt`，可以运行更严格的脚本检查：

```bash
rtk bash scripts/check-shell-style.sh --strict
```

检查推荐工具状态：

```bash
rtk bash scripts/check-tools.sh --strict
```

## 3. 个人知识沉淀

建议把个人一次性笔记分三类处理：

1. 可复用 runbook：整理后提交到 `docs/runbooks/`。
2. 长期标准：整理后提交到 `docs/standards/`。
3. 临时草稿：保留在个人目录，不进入团队仓库。

## 4. Codex 使用建议

1. 每个业务项目只保留项目强绑定文档。
2. 通用排障结论优先沉淀到本知识库。
3. 修改公共脚本、profile、skill 后必须运行 `rtk bash scripts/check-all.sh`。
4. 输出结论时附验证命令，避免只保存主观判断。

## 5. 推荐本机工具

- `shellcheck`：Shell 静态检查。
- `shfmt`：Shell 格式检查。
- `ripgrep`：快速搜索。
- `fd`：快速文件枚举。
- `jq`：JSON 处理。
- `yq`：YAML 处理。
- `tmux`：长任务终端保持。
- `direnv`：按项目自动加载环境变量。

这些工具不是知识库门禁硬依赖；缺失时 `scripts/check-all.sh` 不会失败。

安装方式见 `docs/runbooks/dev-tooling-setup-guide.md`。
