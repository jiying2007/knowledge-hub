---
related:
- projects/pcr02-ssc305/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
decision_status: null
decision_date: null
id: pcr02-release-nfs-client-retention-20260804
title: PCR02 release 暂时保留 NFS 客户端
kind: decision
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/decisions/2026-08-04-release-nfs-client-retention.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 用户工程决策与仓库静态配置证据
  source_sha256: 7ce01cdbf3966fc66fbc75c3898372a31cc330dbd363f561e64b2c16eadeb1ed
review_after: '2026-10-31'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02-ssc305
- release
- nfs-client
validation_refs:
- projects/pcr02-ssc305/decisions/2026-08-04-release-nfs-client-retention.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/pcr02-ssc305/decisions/2026-08-04-release-nfs-client-retention.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-04'
updated_at: '2026-08-04'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-04'
manual_validation_pending: true
summary_zh: PCR02 production/debug 暂时保留 NFSv3 客户端及 grace、SUNRPC、LOCKD 依赖，仅供可信内网手工调试挂载；不自动挂载，production 继续关闭 CIFS 与 NFSD。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 release 暂时保留 NFS 客户端
---

# PCR02 release 暂时保留 NFS 客户端

## 背景

PCR02 production 内核裁剪曾关闭 NFS/CIFS，但开发与现场定位仍需通过可信
内网手工挂载 NFS 导出目录。关闭 NFS 会破坏这一既有调试方式，因此 NFS
客户端暂不纳入 production 文件系统裁剪范围。

## 适用范围

- 项目：PCR02 SSC305，production 与 debug profile。
- 能力：仅 NFS 客户端，当前展开为 NFSv2/NFSv3 模块。
- 使用方式：由调试人员在可信内网手工挂载；系统不配置自动挂载。
- 非目标：不启用 production CIFS、NFSD、NFSv4 或 NFS root。

## 决策

production/debug defconfig 保留 `CONFIG_NFS_FS=m`。production 继续显式关闭
`CONFIG_NFSD` 和 `CONFIG_CIFS`。构建静态契约同时检查 NFS 客户端配置以及
`grace.ko`、`sunrpc.ko`、`lockd.ko`、`nfs.ko`、`nfsv3.ko` 模块白名单，
避免后续裁剪回归。

该候选只记录用户已明确的工程决策，不代表量产安全 owner 已完成签收。

## 证据

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| Kconfig `conf --defconfig`（production/debug，临时输出） | 0 | 两个 profile 均展开 `NFS_FS/NFS_V3/GRACE_PERIOD/LOCKD/SUNRPC=m`；production 的 NFSD/CIFS 关闭 | project working tree | Project | kernel config |
| `rtk bash build.sh verify --profile ap6303bh_512m_v20 --allow-dirty --no-sync-sources` | 0 | production NFS 客户端与模块白名单契约通过 | project working tree | Project | build contract |
| `rtk bash build.sh verify --profile ap6303bh_512m_v20_debug --allow-dirty --no-sync-sources` | 0 | debug NFS 客户端契约通过 | project working tree | Project | build contract |
| `rtk rg -n '^CONFIG_CIFS=m$' <production-defconfig>` | 1 | 负向断言：production 未启用 CIFS | project working tree | Project | kernel config |

## 生效条件

- 源码变更完成提交，并在正式构建中通过 active `.config` 契约检查。
- 实机确认目标 NFS 服务可以用 `nolock` 方式挂载、读写和卸载。
- production 镜像确认不包含或加载 CIFS/NFSD。

## 回滚条件

当现场调试不再依赖 NFS，或 production 安全基线禁止网络文件系统客户端时，
删除 production 的 NFS 配置及模块白名单；debug 是否继续保留另行评估。

## 风险与限制

- 本次按范围只做静态配置验证，尚未构建镜像或执行设备端挂载。
- NFS 不提供传输机密性，使用范围限于受控可信内网，不记录具体服务器地址、
  导出路径或访问凭据。
- 候选保持 `reviewing/manual-validation-pending`，不能作为已完成量产放行的证据。

## Review 周期

- owner：leiwenjun
- review_after：2026-10-31
- 下一次复核：现场是否仍依赖 NFS、实机挂载结果、production 安全基线与镜像模块清单。
