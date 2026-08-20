---
id: firmware-toolchains-x5-ai-toolchain-download-validation-20260805
title: X5 AI Toolchain V1.2.8 下载与完整性验证
kind: validation
domain: projects/firmware-toolchains
path: projects/firmware-toolchains/validation/2026-08-05-x5-ai-toolchain-download.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-project
  from: RDK X5 仓库脱敏下载验证收据；二进制与认证信息已排除
  source_sha256: 865b8278e6b49187df8cf63c3facca3486cc2b4bf017099c5af3f17f7ac64f97
review_after: '2026-11-05'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- x5
- ai-toolchain
- artifact-download
- checksum
- validation
validation_refs:
- projects/firmware-toolchains/validation/2026-08-05-x5-ai-toolchain-download.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/firmware-toolchains/validation/2026-08-05-x5-ai-toolchain-download.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-05'
updated_at: '2026-08-05'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-05'
manual_validation_pending: true
summary_zh: X5 AI Toolchain V1.2.8 全部资产约 19 GiB 已下载，本地 SHA-256 与压缩结构检查通过；发布方签名、官方哈希及功能验证仍待完成。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- X5 AI Toolchain V1.2.8 下载与完整性验证
related:
- projects/firmware-toolchains/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# X5 AI Toolchain V1.2.8 下载与完整性验证

- 验证日期：2026-08-05
- SDK 路径：`X5_LNX_SDK/LNX6.1.83_PL5.1_V1.1.2/ai_toolchain_package`
- 结论：发布说明列出的 9 个文件均已下载，本地 SHA-256 复核与压缩包结构检查通过。
- 边界：本结论只证明当前本地副本可读取且与本地校验基线一致，不证明发布方真实性，也不代表工具链已完成安装、模型转换或开发板运行验证。

## 文件清单

| 文件 | 字节数 | 检查结果 |
| --- | ---: | --- |
| `Ai_Toolchain_Package-release-v1.23.9-OE-v1.2.8.tar.xz` | 389397740 | XZ 完整性通过 |
| `docker_openexplorer_ubuntu_20_x5_cpu_v1.2.8.tar.gz` | 1815507981 | Gzip 完整性通过 |
| `docker_openexplorer_ubuntu_20_x5_gpu_v1.2.8.tar.gz` | 11066222691 | Gzip 完整性通过 |
| `horizon_model_convert_sample.tar.xz` | 4135427688 | XZ 完整性通过 |
| `install_env.sh` | 535 | SHA-256 通过 |
| `manual_deployment_package.tar.gz` | 210984960 | POSIX tar 目录读取通过 |
| `release_note.txt` | 14704 | SHA-256 通过；含认证信息，不得提交或复制到归档 |
| `torch_package.tar.xz` | 1991227756 | XZ 完整性通过 |
| `yolov5s_v2.0.tar.gz` | 38615040 | POSIX tar 目录读取通过 |

目录占用约 19 GiB。完整 SHA-256 基线保存在
`X5_LNX_SDK/LNX6.1.83_PL5.1_V1.1.2/ai_toolchain_package/SHA256SUMS.downloaded-20260805`。

## 验证证据

- 对校验清单执行 `sha256sum --check`，9 个文件全部返回 `OK`。
- 三个 `.tar.xz` 文件执行 XZ 流完整性检查，全部通过。
- CPU、GPU 两个 Docker 压缩包执行 Gzip 流完整性检查，全部通过。
- `manual_deployment_package.tar.gz` 与 `yolov5s_v2.0.tar.gz` 虽使用 `.tar.gz` 后缀，实际识别为未压缩 POSIX tar；分别可列出 6 项和 81 项内容。
- 验证结束后未发现残留下载进程。

## 风险与后续

- 发布方未随当前资料提供官方 SHA-256 或签名，因此本地清单只能作为后续传输和存储复核的基线。
- `release_note.txt` 含访问凭据，仅保留在本地 SDK 原始目录；不得进入 Git、Knowledge Hub、日志或共享包。
- 19 GiB 二进制资产不进入知识归档；归档只保存本收据中的脱敏事实。
- 使用前仍需验证 Docker 镜像导入、工具链安装、样例模型转换及开发板部署流程。

## 复核方式

在 AI 工具链目录中执行：

```bash
sha256sum --check SHA256SUMS.downloaded-20260805
```

预期 9 个条目全部为 `OK`。若任一条目失败，应重新获取对应文件，不应更新基线来掩盖差异。
