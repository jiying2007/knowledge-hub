---
title: SigmaStar 归档实体生成与引用指南
doc_type: runbook
knowledge_type: process
maturity: verified
status: active
owner: team-core
created: 2026-05-16
last_updated: 2026-05-16
tags: [sigmastar, archive, artifact, nas]
related: [../archive/sigmastar/manifest.md, ../archive/sigmastar/manifest.csv, ../archive/sigmastar/archive-template.md, sigmastar-platform-development-workflow.md, ../../tools/sigmastar/archive_sigdoc_artifact.sh]
validation_refs: [tools/sigmastar/archive_sigdoc_artifact.sh, docs/archive/sigmastar/manifest.csv]
---

# SigmaStar 归档实体生成与引用指南

## 1. 目标

1. 将临时 `sigdoc` 目录打包为可长期保存的归档实体。
2. 用 `archive_id + artifact_uri + sha256` 建立可追溯引用链。
3. 支持本地路径、NAS 挂载路径、以及自定义 URI 前缀。

## 2. 脚本入口

脚本路径：

`tools/sigmastar/archive_sigdoc_artifact.sh`

核心参数：

1. `--source-dir`：sigdoc 原始目录。
2. `--platform`：`SSC305` 或 `SSU9383CM`。
3. `--snapshot-date`：快照日期。
4. `--version`：版本号，如 `v2`。
5. `--artifact-uri`：归档目标路径或 URI。
6. `--artifact-path`：当 URI 非 `file://` 时，本地/NAS 挂载写入路径。
7. `--manifest-csv`：输出机器可读记录文件。

## 3. 常见用法

本地路径：

```bash
rtk bash tools/sigmastar/archive_sigdoc_artifact.sh \
  --source-dir examples/sigmastar/SSC305_sigdoc \
  --platform SSC305 \
  --snapshot-date 2026-05-16 \
  --version v2 \
  --artifact-uri nas://embedded/sigmastar/archive \
  --artifact-path /mnt/nas/embedded/sigmastar/archive \
  --manifest-csv docs/archive/sigmastar/manifest.csv
```

NAS URI + 挂载目录：

```bash
rtk bash tools/sigmastar/archive_sigdoc_artifact.sh \
  --source-dir <sigdoc_dir> \
  --platform <platform> \
  --snapshot-date <YYYY-MM-DD> \
  --version <vN> \
  --artifact-uri nas://embedded/sigmastar/archive \
  --artifact-path /mnt/nas/embedded/sigmastar/archive \
  --manifest-csv docs/archive/sigmastar/manifest.csv
```

## 4. 生成产物

每次执行会生成：

1. 归档包：`<archive_id>.tar.zst` 或 `<archive_id>.tar.gz`。
2. 摘要文件：`<archive_id>.<ext>.sha256`。
3. 元数据：`<archive_id>.<ext>.json`。
4. 可选：向 `manifest.csv` 追加条目。

## 5. 引用规范

1. 业务文档只引用 `archive_id`，不直接依赖临时目录路径。
2. 追溯时通过 `manifest.csv` 查 `artifact_uri` 与 `artifact_sha256`。
3. 使用前执行 SHA256 校验，不通过则禁止作为证据源。

## 6. 迁移规范

1. 本地演示路径迁移到 NAS 时，仅更新 `artifact_uri` 字段。
2. 迁移后 `archive_id` 保持不变，防止引用断裂。
3. 新版本新增记录，不覆盖历史行。
