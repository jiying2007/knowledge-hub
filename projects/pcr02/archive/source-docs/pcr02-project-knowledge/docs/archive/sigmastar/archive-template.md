---
title: SigmaStar 归档记录模板
doc_type: archive
knowledge_type: process
maturity: historical
status: archived
owner: team-core
created: 2026-05-15
last_updated: 2026-05-16
tags: [archive, sigmastar, template]
related: [manifest.md, manifest.csv, ../../standards/sigmastar-platform-topic-catalog.md, ../../../tools/sigmastar/archive_sigdoc_artifact.sh]
validation_refs: [manifest.md, manifest.csv]
---

# SigmaStar 归档记录模板

## 1. 归档元信息

- `archive_id`:
- `platform`:
- `snapshot_date`:
- `artifact_uri`:
- `artifact_sha256`:
- `artifact_size_bytes`:
- `artifact_size_human`:
- `artifact_format`:
- `source_version_hint`:
- `operator`:
- `reviewer`:

## 2. 归档范围

- 文档类型：
- 包含目录：
- 排除目录：
- 文件总数：
- 页面总数（`*_zh.html`）：
- 数据体积：

## 3. 来源与证据

- 原始来源描述：
- 目录校验命令：
- 统计命令：
- 关键时间戳：
- 关联提交：
- artifact 可用性验证：

## 4. 知识化产物映射

| 产物类型 | 路径 | 说明 |
| --- | --- | --- |
| architecture |  |  |
| runbook |  |  |
| standard |  |  |

## 5. 质量门禁

- schema 校验：通过/失败
- naming 校验：通过/失败
- links 校验：通过/失败
- 风险备注：

## 6. 后续维护

1. 若原始资料升级，先新增一条 manifest 版本记录。
2. 若主题变化，更新 `sigmastar-platform-topic-catalog.md`。
3. 若新增能力域，补齐架构与流程文档后再对外使用。
