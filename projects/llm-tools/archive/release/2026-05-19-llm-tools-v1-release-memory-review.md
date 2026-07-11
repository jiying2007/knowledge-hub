# llm_tools v1.0.0 发布记忆审计历史 2026-05-19

## 摘要

本文从旧 Codex archive `memory-curation` 选择性迁移而来，保留 `llm_tools` 2026-05-19 v1.0.0 发布审计中的长期可用结论。本文是 archive-only 历史记录，不代表当前发布版本、当前构建产物或当前签名状态。

## 历史发布基线

- v1.0.0 是当时的第一版正式发布基线。
- 发布材料强调 PDF-first 文档，同时保留 HTML/Markdown 便于浏览和 diff。
- Windows 发布目标为 x64 portable 与 installer；x86 不作为默认产物。
- Authenticode 状态只针对可执行文件和安装器等二进制产物，不把文档或压缩包误判为签名对象。
- 私有 package index、PFX、证书密码、release secret 不进入仓库、Hub 正文或 memory。
- 发布布局需要保留可审计 manifest、hash、版本说明和平台边界。

## 历史边界

- 本记录不保存 release binary、installer、PDF 原文、wheelhouse、token、cookie、private key、PFX 或签名凭据。
- 本记录不声明 legal/security/signing review 已完成。
- 本记录不替代当前 release checklist 或 Windows 构建机 runbook。

## 迁移边界

| Field | Value |
| --- | --- |
| source_path | `domains/codex/archive/codex-archive/memory-curation/20260519-221757-llm-tools-v1-release-memory-review.md` |
| source_sha256 | `3fdf9dbb73b860a16a775ffea94f3f0367441f724b6103657be52ad50b012234` |
| source_lines | `93` |
| source_size | `5310 bytes` |
| migrated_at | `2026-07-11` |
| coverage_manifest | `artifacts/manifests/codex-archive-memory-curation-coverage-20260711.md` |

## 风险与后续

- 当前 v1.x 发布状态必须以当前源仓、当前 release artifact、当前构建机和当前签名配置为准。
- 如需重新发布或回滚，应使用 current runbook，而不是旧 memory-curation 审计。
- 旧正文删除只由独立授权、tombstone 和验证命令证明；本记录本身不是删除授权。
