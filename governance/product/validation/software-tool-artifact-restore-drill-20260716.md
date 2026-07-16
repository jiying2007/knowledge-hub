---
id: software-tool-artifact-restore-drill-20260716
title: 软件工具制品隔离恢复演练 2026-07-16
kind: validation
domain: governance
path: governance/product/validation/software-tool-artifact-restore-drill-20260716.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: lab-test
  from: workspace://llm-tools/releases
review_after: '2026-10-16'
created_at: '2026-07-16'
updated_at: '2026-07-16'
promotion: none
promotion_decision: none; isolated restore evidence does not authorize release, evidence-ready status or active promotion
tags:
- knowledge-hub
- software-tool
- validation
- rollback-drill
- artifact-integrity
- ai-generated
- manual-validation-pending
related:
- governance/product/validation/software-tool-evidence-audit-20260715.md
- artifacts/manifests/llm-tools-release-evidence-20260715.jsonl
validation_refs:
- rtk bash ~/knowledge-hub/tools/knowledge-artifact-restore-drill.sh --release-root releases/<tool>/<version> --source-label
  workspace://llm-tools/releases/<tool>/<version> --json
artifact_refs:
- workspace://llm-tools/releases/ota-packager/v1.0.0
- workspace://llm-tools/releases/sigmastar-flasher/v1.0.0
- workspace://llm-tools/releases/mm32spin-validator/v0.1.0
target_version: ota-packager v1.0.0; sigmastar-flasher v1.0.0; mm32spin-validator v0.1.0
test_environment: Linux isolated temporary deployment; source release directories read-only
summary_zh: 在不修改外部 release 目录的前提下，对三套 checksum-bound 软件制品执行源校验、临时部署、故意破坏检测、精确恢复和源不变复核；三套均通过。该证据只证明本地制品集可恢复，不证明远端留存、设备或生产回滚。
review_status: manual-entry-pending-review
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: checked
evidence_strength: direct-command
evidence_refs:
- governance/product/validation/software-tool-evidence-audit-20260715.md
- artifacts/manifests/llm-tools-release-evidence-20260715.jsonl
generated_by_ai: true
ai_role: drafted-and-verified
ai_model_or_tool: Codex
ai_generated_at: '2026-07-16'
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
manual_validation_pending: true
aliases:
- 软件工具制品隔离恢复演练 2026-07-16
---

# 软件工具制品隔离恢复演练 2026-07-16

## 验证目标

验证 `workspace://llm-tools/releases` 中三套已有发布目录能否在不修改 source 的前提下，按 `SHA256SUMS.txt` 完整复制到隔离目录、检测临时副本损坏，并从原发布目录恢复到逐文件 hash 全部一致。

本报告不证明远端或离线备份可用、发布者签名有效、设备回滚成功、生产环境兼容、当前源码可复现全部历史制品，也不构成 owner 发布批准、`evidence-ready` 或 active promotion。

## 验证对象

| 工具 | 版本 | Source Label | 文件数 | 总字节数 |
| --- | --- | --- | ---: | ---: |
| OTA Packager | `v1.0.0` | `workspace://llm-tools/releases/ota-packager/v1.0.0` | 7 | 150132158 |
| SigmaStar Flasher | `v1.0.0` | `workspace://llm-tools/releases/sigmastar-flasher/v1.0.0` | 10 | 158784649 |
| MM32SPIN Validator | `v0.1.0` | `workspace://llm-tools/releases/mm32spin-validator/v0.1.0` | 4 | 42134686 |

精确 release manifest、artifact hash、source commit/snapshot 与既有 provenance 边界见 `software-tool-evidence-audit-20260715.md` 和 `llm-tools-release-evidence-20260715.jsonl`。本报告不重复复制 binary。

## 环境

- date：2026-07-16。
- cwd：`workspace://llm-tools`。
- host：Linux；恢复目标由 Python `TemporaryDirectory` 创建，演练结束后清理。
- source mode：只读读取外部 release 目录；工具输出固定 `read_only_source=true`、`source_written=false`。
- mutation scope：只向临时部署副本追加固定负例字节；不修改 release source、Hub 外部源码或设备。

## 验证命令

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash ~/knowledge-hub/tools/knowledge-artifact-restore-drill.sh --release-root releases/ota-packager/v1.0.0 --source-label workspace://llm-tools/releases/ota-packager/v1.0.0 --json` | 0 | 7 个源文件 hash 通过；临时副本损坏被检测；恢复后 7/7 通过；source 复核未变化。 | 本报告 | Tool | OTA Packager v1.0.0 |
| `rtk bash ~/knowledge-hub/tools/knowledge-artifact-restore-drill.sh --release-root releases/sigmastar-flasher/v1.0.0 --source-label workspace://llm-tools/releases/sigmastar-flasher/v1.0.0 --json` | 0 | 10 个源文件 hash 通过；临时副本损坏被检测；恢复后 10/10 通过；source 复核未变化。 | 本报告 | Tool | SigmaStar Flasher v1.0.0 |
| `rtk bash ~/knowledge-hub/tools/knowledge-artifact-restore-drill.sh --release-root releases/mm32spin-validator/v0.1.0 --source-label workspace://llm-tools/releases/mm32spin-validator/v0.1.0 --json` | 0 | 4 个源文件 hash 通过；临时副本损坏被检测；恢复后 4/4 通过；source 复核未变化。 | 本报告 | Tool | MM32SPIN Validator v0.1.0 |
| `rtk releases/ota-packager/v1.0.0/linux/ota-packager-cli-linux-x64-v1.0.0 --help` | 0 | release 内 Linux CLI 可启动并输出 package/validate/inspect/sample-config 帮助。 | 本报告 | Tool | SHA256 `68dfc3ad…bc8c` |
| `rtk releases/sigmastar-flasher/v1.0.0/linux/sigmastar-flasher-cli-linux-x64-v1.0.0 --help` | 0 | release 内 Linux CLI 可启动并输出 queue/preflight/export 命令帮助。 | 本报告 | Tool | SHA256 `f82f29db…0c30` |

## 结果矩阵

| 工具 | Source checksum | 部署副本 | 损坏检测 | 恢复后 checksum | Source 未变化 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| OTA Packager | 7/7 | 7/7 | pass | 7/7 | pass | pass |
| SigmaStar Flasher | 10/10 | 10/10 | pass | 10/10 | pass | pass |
| MM32SPIN Validator | 4/4 | 4/4 | pass | 4/4 | pass | pass |

## 证据

| 工具 | `SHA256SUMS.txt` SHA256 | Artifact Set SHA256 | 临时破坏路径 SHA256 |
| --- | --- | --- | --- |
| OTA Packager | `3b31f3affa2fcd966d2de351e8f3374cb7b7232877654bb1d4c571d01ffc05aa` | `eafd515575ac331a17bcd503989f3d732bea02b6d89aeb8c6f7f7101e36a6419` | `a5c59141c6e644b64ea9d43db1542f93af6383ca5c6b89c5c69427db26020a62` |
| SigmaStar Flasher | `747f95648f17f99543c604640b8c6db50454c1caf7ee9cd23959494dce8e7dc3` | `b1aa2a3ed9ffd745980ca50585cc5a8ea4061602576312c512552c436e70e1c2` | `07aa4cfd7d9b2a631e42b9b89a93d65acd587cb9db9b63794275b2c8ab3664b4` |
| MM32SPIN Validator | `b5d05c89393239fca6221d869d8c056e25657bfec3946dbcfea170282dad6593` | `df85d13fd92fc8defccec36dac430d6c776ba166966d573043fc8a62a2ce955e` | `a5c59141c6e644b64ea9d43db1542f93af6383ca5c6b89c5c69427db26020a62` |

`Artifact Set SHA256` 是按相对路径与期望文件 SHA256 排序计算的集合身份，不是 binary 内容拼接 hash。工具输出 `remote_retention_verified=false`、`device_rollback_verified=false`、`production_rollback_verified=false`，这些否定边界属于证据的一部分。

## 结论

三套本地 release 制品均完成真实的 checksum-bound 隔离恢复演练，可作为以下四个项目的窄范围 `rollback_ref`：`llm-tools`（三套发布集合）、`ota-packager`、`sigmastar-flasher`、`mm32spin-validator`。引用结果必须写成 `isolated-local-artifact-restore-pass`，不能缩写成“生产回滚通过”。

四个 evidence contract 继续保持 `status=pending`：本报告只补齐可在本机独立核验的 rollback slot，不代签 owner lifecycle。尤其是 MM32SPIN Validator 的历史 Windows 制品仍缺与当前 source snapshot 的可复现等价关系；SigmaStar Flasher 仍缺串口、烧录和设备恢复路径。

## 剩余风险

- release source 仅位于本机 workspace，远端或离线备份的存在性、ACL 和恢复带宽未验证。
- OTA/SigmaStar 仅对 Linux CLI 执行 `--help`；未运行 GUI、Windows installer 或真实任务。
- MM32SPIN Validator 只有 Windows binary，本机未执行该 binary；恢复结论仅覆盖逐文件完整性。
- 三套 Windows executable 均无可在本报告中确认的发布者签名；checksum 不提供发布身份。
- 临时恢复不是生产部署切换，没有覆盖配置迁移、状态数据、用户数据或版本降级兼容。

## 后续动作

```yaml
manual_validation_pending: true
manual_validation_reason: 本地 artifact restore 已通过，但远端留存、owner 发布批准、生产/设备回滚与部分源码可复现性仍未闭环。
required_followup:
  - owner 确认目标发布渠道与长期留存位置
  - 从远端或离线备份重新下载后重复同一 restore drill
  - 对 SigmaStar Flasher 执行带串口与目标设备的失败恢复
  - 为 MM32SPIN Validator 建立可复现 source commit 并重发制品
owner: leiwenjun
review_after: 2026-10-16
```
