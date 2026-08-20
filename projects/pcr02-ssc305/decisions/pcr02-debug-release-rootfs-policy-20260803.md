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
id: pcr02-debug-release-rootfs-policy-20260803
title: PCR02 debug/release rootfs 与 OTA 边界决策
kind: decision
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/decisions/pcr02-debug-release-rootfs-policy-20260803.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: current-session-decision
  source_sha256: 7ce01cdbf3966fc66fbc75c3898372a31cc330dbd363f561e64b2c16eadeb1ed
review_after: '2026-11-03'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- rootfs
- ota
- debug-release
validation_refs:
- projects/pcr02-ssc305/decisions/pcr02-debug-release-rootfs-policy-20260803.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/pcr02-ssc305/decisions/pcr02-debug-release-rootfs-policy-20260803.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-03'
updated_at: '2026-08-03'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-03'
manual_validation_pending: true
summary_zh: PCR02 debug 仅用于开发测试，量产设备只运行 release；当前不统一 rootfs，debug 转 release 使用完整迁移包，release 日常 OTA 按实际变更选择分区，暂不加入硬性 OTA 校验。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 debug/release rootfs 与 OTA 边界决策
---

# PCR02 debug/release rootfs 与 OTA 边界决策

## 背景

2026-08-03 排查发现，开发 debug 镜像通过 OTA 切换到 release 时，如果只更新
kernel/customer 而保留 debug rootfs，会形成混合系统：customer 版本声明为
release，但启动阶段仍执行 debug rootfs 固化的 customer overlay、debugfs 或调试
服务逻辑。进一步确认产品边界后，debug 仅用于开发测试设备，量产设备不会运行
debug。

## 适用范围

- 适用于 PCR02 SSC305 的 kernel、rootfs、customer/miservice 镜像和 OTA 分区策略。
- 适用于开发测试设备从 debug 转为 release，以及量产设备的 release 日常升级。
- 不适用于把量产设备远程切换为 debug；该场景不在当前产品需求内。

## 权威来源

- source_id：manual current-session decision
- source_path：PCR02 SSC305 工作区启动日志、profile、rootfs 与 OTA 配置
- owner：leiwenjun
- source_status：reviewing，板端迁移验证和 owner 复核待完成

## 决策问题

是否为 debug/release 双向切换重构统一 rootfs，以及是否立即为跨 build type OTA
加入硬性拒绝门禁。

## 选项

| 选项 | 影响范围 | 成本 | 风险 |
| --- | --- | --- | --- |
| 保持两套 rootfs | 开发 debug 与量产 release | 改动小 | debug 转 release 必须正确选择分区 |
| 统一 rootfs | 启动链、overlay、调试服务和 OTA 契约 | 改造与验证成本高 | 扩大量产启动链和安全边界 |
| 立即加入硬性 OTA 校验 | build.sh、设备升级脚本 | 中 | 现有开发流程可能被提前阻断 |

## 证据

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| 启动日志审查 | N/A | release customer 与 debug rootfs 可形成混合运行态。 | 当前排障会话 | Project | boot log |
| profile/rootfs 配置审查 | 0 | debug 使用 overlay partition config，release 使用 production squashfs config。 | PCR02 SSC305 workspace | Project | defconfig/rootfs.mk |
| Knowledge Hub capture dry-run/apply | 0 | reviewing 决策候选创建成功，未提升 active、未写 memory。 | 本候选与 registry | Knowledge Hub | transaction record |

## 决策

1. 当前不统一 rootfs。debug 继续作为开发测试镜像，release 继续作为量产镜像；
   量产 rootfs 保持最小化，不引入动态 debug/release 模式选择。
2. 开发设备由 debug 转 release 时，使用包含 kernel、rootfs、customer 和
   miservice 的完整迁移镜像，避免混合系统。
3. 量产设备只执行 release 到 release 升级；rootfs 是否进入 OTA 由真实变更和
   兼容性决定，不因开发模式切换需求强制统一。
4. 按 owner 当前要求，先不加入跨 build type OTA 的硬性校验。本项保留为后续
   风险控制候选，不代表永久取消。

## 当前结论

本记录为 `reviewing` 候选：不统一 rootfs 和暂缓硬性校验是当前实施方向；尚未
提升为 active 规范，也未授权额外代码修改。开发转 release 时携带完整迁移分区
是基于现有两套 rootfs 行为差异得到的风险控制建议，仍需板端验证。

## 生效条件

- owner 明确签收本决策。
- 至少完成一次 debug 到 release 的板端完整迁移验证。
- 确认升级后 `/customer/etc/version.ini`、`/proc/cmdline`、customer 挂载方式和
  调试服务状态均符合 release 预期。

## 回滚条件

- 产品需求变为量产设备必须远程切换 debug/release 时，重新评估统一 rootfs。
- 引入 rootfs A/B、可靠 recovery 或版本化 runtime contract 后，可由新决策
  supersede 本候选。
- 若完整迁移 OTA 在板端不可接受，应重新拆分迁移边界，不能静默省略 rootfs。

## 风险与限制

- 暂无硬性校验意味着仍依赖构建/发布人员正确选择迁移分区，存在人为误用风险。
- 当前没有 debug 到 release 的断电、回滚和批量升级验证证据。
- 本记录不保存完整启动日志、设备标识、内部服务地址、二进制或凭证。
- 若 profile、partition config、rootfs 启动脚本或 OTA 布局变化，应提前复核。

## Review 周期

- owner：leiwenjun
- review_after：2026-11-03
- 下一次复核内容：debug 到 release 板端迁移结果、是否出现混合系统，以及是否
  需要把当前人工约束升级为软提示或硬性校验。

## Archive evidence

- Captured at: 2026-08-03 Asia/Hong_Kong.
- Sanitization: 未保存 raw log、设备唯一标识、凭证、二进制或 runtime state。
- Provenance: 当前会话结论、PCR02 profile、rootfs 打包和 OTA 配置审查。
- Memory candidate: no; reviewing decision only.
- Gate result: candidate captured; owner review and HIL migration validation pending.
