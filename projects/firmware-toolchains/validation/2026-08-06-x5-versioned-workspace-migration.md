---
aliases:
- X5 SDK版本化工作区迁移验证
related:
- projects/firmware-toolchains/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: firmware-toolchains-x5-versioned-workspace-migration-20260806
title: X5 SDK版本化工作区迁移验证
kind: validation
domain: projects/firmware-toolchains
path: projects/firmware-toolchains/validation/2026-08-06-x5-versioned-workspace-migration.md
scope: project-specific
visibility: team-internal
status: rejected
owner: leiwenjun
source:
  type: source-project
  from: X5 integration repository
  source_sha256: a4fe4a7a0685ae67975ca1398e69b6072fab6518329921d5215c2a1a68c7fec9
review_after: '2026-11-04'
review_status: human-directed-delegated-retired
content_review_status: accepted
evidence_validation_status: historical
promotion: none
promotion_decision: 初始版本直接采用最终目录布局，撤回不再适用的迁移候选
tags:
- x5
- workspace-layout
validation_refs:
- projects/firmware-toolchains/validation/2026-08-06-x5-versioned-workspace-migration.md
- current-session user confirmation 2026-08-06
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: review-attestation-plus-validation-refs
evidence_refs:
- projects/firmware-toolchains/validation/2026-08-06-x5-versioned-workspace-migration.md
- current-session user confirmation 2026-08-06
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-06'
updated_at: '2026-08-06'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-06'
manual_validation_pending: false
summary_zh: X5 SDK源码工作区由泛化projects目录迁移为workspaces/<release-id>，默认路径随release动态派生，迁移后源码身份和固件哈希复核通过。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# SDK工作区版本化迁移

## 目标布局

源码工作区统一放在`workspaces/<release-id>`，当前版本为：

```text
<x5-root>/workspaces/x5-v1.1.2
```

`integration` CLI会根据`--release`动态派生默认目录。显式传入`--workspace`仍受支持，适合CI或自定义存储位置。

## 从旧目录迁移

先停止构建、同步和烧录相关进程，确认目标不存在且源目录有效：

```bash
test -d <x5-root>/projects
test ! -e <x5-root>/workspaces/x5-v1.1.2
```

源目录与目标目录在同一文件系统时，可直接重命名：

```bash
mkdir -p <x5-root>/workspaces
mv <x5-root>/projects \
  <x5-root>/workspaces/x5-v1.1.2
```

迁移不会修改`.repo`、源码commit或构建产物。不要创建指向旧`projects`路径的长期兼容软链接，否则脚本、日志和人工操作仍会继续依赖含义不明确的名称。

## 迁移验证

```bash
./scripts/x5-sdk.sh doctor --source-ready
./scripts/x5-sdk.sh verify
./scripts/final-ready.sh --with-firmware
```

同时确保外层工作区容器忽略`/workspaces/`，防止`.repo`、源码和固件被父级Git仓误收录。

## 回退

仅在新路径验证失败且旧路径仍是外部系统硬依赖时回退。先停止相关进程并确认旧路径不存在，再将目录原子重命名回`projects`。回退后必须显式使用`--workspace`，并记录尚未迁移的外部依赖。
