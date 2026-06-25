---
title: SigmaStar 资料归档清单（v2）
doc_type: archive
knowledge_type: decision
maturity: historical
status: archived
owner: team-core
created: 2026-05-15
last_updated: 2026-05-16
tags: [archive, sigmastar, manifest, artifact-uri]
related: [archive-template.md, manifest.csv, ../../architecture/sigmastar-platform-internal-overview.md, ../../architecture/sigmastar-platform-capability-matrix.md, ../../runbooks/sigmastar-platform-development-workflow.md, ../../runbooks/sigmastar-archive-artifact-guide.md, ../../standards/sigmastar-platform-topic-catalog.md, ../../../tools/sigmastar/archive_sigdoc_artifact.sh]
validation_refs: [docs/archive/sigmastar/manifest.csv, tools/sigmastar/archive_sigdoc_artifact.sh]
---

# SigmaStar 资料归档清单（v2）

## 1. 归档策略（脱离临时目录）

1. `examples/sigmastar` 视为临时参考，不作为长期引用源。
2. 长期引用统一使用 `archive_id`，通过 `manifest.csv` 反查 `artifact_uri` 与 `artifact_sha256`。
3. `docs/` 仅保存知识化文档与索引，不存放大体积原始站点资源。
4. 归档实体存放在 NAS 或指定路径（`artifact_uri`），支持后续迁移而不改调用方语义。

## 2. 当前有效归档实体

| archive_id | platform | snapshot_date | version | artifact_uri | artifact_sha256 | size_human | file_count | zh_page_count | status |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| sigmastar-ssc305-20260516-v2 | SSC305 | 2026-05-16 | v2 | `nas://embedded/sigmastar/archive/sigmastar-ssc305-20260516-v2.tar.gz` | `a27cfa6e9f72f564953d9e8f25c01e0d34a48aa920a1dc9bd677f0efa479ffe3` | 207M | 1755 | 115 | active |
| sigmastar-ssu9383cm-20260516-v2 | SSU9383CM | 2026-05-16 | v2 | `nas://embedded/sigmastar/archive/sigmastar-ssu9383cm-20260516-v2.tar.gz` | `8e56647092e2fbc7694af648aef94c5e5cd44108208e04c419ae31a2b3cd03a0` | 297M | 1510 | 119 | active |

说明：当前 `artifact_uri` 使用团队制品 URI。若物理存储迁移，仅需更新 `manifest.csv/.md` 的 `artifact_uri` 字段，`archive_id` 保持不变。

## 3. 归档实体生成方式

使用脚本：

```bash
rtk bash tools/sigmastar/archive_sigdoc_artifact.sh \
  --source-dir <sigdoc_dir> \
  --platform <SSC305|SSU9383CM> \
  --snapshot-date <YYYY-MM-DD> \
  --version <vN> \
  --artifact-uri <path|file://path|nas://prefix> \
  [--artifact-path <nas_mount_path>] \
  [--manifest-csv docs/archive/sigmastar/manifest.csv]
```

规则：

1. `artifact-uri` 为本地路径或 `file://` 时，直接写入该目录。
2. `artifact-uri` 为其他 URI（如 `nas://`）时，需提供 `--artifact-path`（NAS 挂载目录）。
3. 优先输出 `tar.zst`，若环境缺少 `zstd` 自动降级为 `tar.gz`。

## 4. 内部知识化映射

| 产物 | 路径 | 覆盖说明 |
| --- | --- | --- |
| 总览架构 | `docs/architecture/sigmastar-platform-internal-overview.md` | 双平台定位、分层、差异主线 |
| 能力矩阵 | `docs/architecture/sigmastar-platform-capability-matrix.md` | 选型决策、风险与验收基线 |
| 开发流程 | `docs/runbooks/sigmastar-platform-development-workflow.md` | 开发到交付的阶段化步骤 |
| 主题索引 | `docs/standards/sigmastar-platform-topic-catalog.md` | 234 个主题索引（115 + 119） |

## 5. 校验记录

- `rtk python3 docs/governance/check_docs_schema.py --changed-only`：通过。
- `rtk python3 docs/governance/check_docs_naming.py --changed-only`：通过。
- `rtk python3 docs/governance/check_docs_links.py --changed-only`：通过。

## 6. 维护规则

1. 每次资料升级新增一条 `archive_id`，禁止覆盖已有归档。
2. `manifest.csv` 作为机器可读单一事实源，`manifest.md` 作为人类可读摘要。
3. 若迁移存储位置（本地 -> NAS），仅改 `artifact_uri`，不改 `archive_id`。
4. 使用前必须校验 SHA256，校验失败禁止作为证据链来源。
