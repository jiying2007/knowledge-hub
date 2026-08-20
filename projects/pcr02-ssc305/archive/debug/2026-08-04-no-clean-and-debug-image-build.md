---
related: []
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-no-clean-debug-image-build-20260804
title: PCR02 no-clean 编译与 debug 镜像体积排障
kind: debug-record
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/archive/debug/2026-08-04-no-clean-and-debug-image-build.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: manual-entry:knowledge-new.sh
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
review_after: '2026-11-04'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- build
- debug-image
- nfs
validation_refs:
- projects/pcr02-ssc305/archive/debug/2026-08-04-no-clean-and-debug-image-build.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/pcr02-ssc305/archive/debug/2026-08-04-no-clean-and-debug-image-build.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-04'
updated_at: '2026-08-04'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-04'
manual_validation_pending: true
summary_zh: 记录陈旧依赖文件导致增量编译失败、debug DWARF 撑爆 customer 卷及 NFS 发布保留边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 no-clean 编译与 debug 镜像体积排障

## 现象

- 使用 debug profile 和 `--no-clean` 编译时，应用构建在 `sensor_obj_all` 失败；串行复现后显示生成的 `.d` 文件仍依赖已移动或删除的显示头文件。
- 应用修复后，debug `prog_pcr02` 携带完整 DWARF，复制到固定大小的 customer 静态 UBI 卷后导致 SquashFS 超过 112 MiB。
- 在失败的 compile 之后直接执行 package 并带 `--skip-defconfig`，会复用旧的 active kernel config，触发 debug profile 缺少 `CONFIG_OVERLAY_FS=y` 的合约检查。

## 影响范围

- 项目：PCR02 / SSC305 / AP6303BH 512 MiB v2.0。
- 场景：开发 debug 镜像的增量编译与 SD 打包准备。
- production release 不需要携带 DWARF，但当前仍需保留 NFS 客户端，支持现场手工 NFS 挂载调试。

## 环境

- Profile：`ap6303bh_512m_v20_debug`。
- 编译策略：允许 dirty、no-clean、no-copy-nfs。
- customer 卷上限：112 MiB；镜像格式为 SquashFS/LZO。

## 时间线

| 时间 | 操作或观察 | 结果 |
| --- | --- | --- |
| 2026-08-04 | 串行重跑应用构建 | 定位到陈旧 `.d` 中的旧显示头文件路径 |
| 2026-08-04 | 清理未跟踪生成 `.d` 并重新构建 | 应用编译和链接通过 |
| 2026-08-04 | 检查 customer 输入体积 | 未裁剪 debug 程序约 229 MiB，静态卷无法容纳 |
| 2026-08-04 | 仅对 customer 中的 debug 副本执行 `--strip-debug` | customer.sqfs 为 66,109,440 字节，完整 compile 通过 |

## 证据

- 修复前负证据：Make 报旧 `modules/sensor/display/user_config.h` 与 `display_control.h` 无规则可生成。
- 修复后 `compile --profile ap6303bh_512m_v20_debug --allow-dirty --no-clean --no-copy-nfs` 退出码为 0。
- active config 含 `CONFIG_PACKET=y`、`CONFIG_INET=y`、`CONFIG_OVERLAY_FS=y`、`CONFIG_NFS_FS=m`。
- customer.sqfs 为 66,109,440 字节，小于 117,440,512 字节上限。
- customer 中 `prog_pcr02` 为 28,607,704 字节，无 `.debug_*` section，仍保留 `.symtab`；SDK/NFS 调试副本为 239,997,388 字节并保留 10 类 `.debug_*` section。
- customer 的 `/config/modules/5.10` 含 grace、sunrpc、lockd、nfs、nfsv3 模块，启动脚本保留 NFS 加载行。

## 假设与排除

| 假设 | 验证动作 | 结果 | 状态 |
| --- | --- | --- | --- |
| 源码缺少显示头文件 | 检查当前 include 与仓库文件 | 头文件已迁移，源码本身可编译 | 排除 |
| `--skip-defconfig` 合约门禁错误 | 完整 compile 重新应用 debug defconfig | active config 随后通过 profile 合约 | 排除；门禁正确 |
| 必须扩大 customer 分区 | 去除镜像副本 DWARF 后重建 | 镜像降至约 63.04 MiB | 排除 |

## 根因

1. 依赖生成只使用 `-MM`，删除或移动头文件后，旧 `.d` 会把不存在的头文件作为无规则 prerequisite；`--no-clean` 会持续命中该陈旧依赖。
2. debug 程序完整 DWARF 被复制进固定大小的静态 customer 卷，造成镜像体积溢出。
3. compile 在应用阶段失败后没有完成 debug 内核配置，package 的 `--skip-defconfig` 按设计复用旧 active config，因此正确拒绝继续打包。

## 修复或规避

- C/C++ 依赖生成增加 `-MP`，为头文件生成空目标，避免后续移动/删除头文件令旧 `.d` 阻断增量编译。
- 一次性删除未跟踪生成 `.d`，保留对象文件和源码，不执行全量 clean。
- 仅对进入 debug customer 镜像的 `prog_pcr02` 副本执行 `strip --strip-debug`；SDK staging/NFS 副本保持完整 DWARF。
- production 不执行该 debug 副本裁剪分支；release NFS 客户端及启动加载路径继续保留，CIFS 仍按 production 合约关闭。
- 不绕过 active kernel config/profile 合约；失败的 compile 之后应先成功重跑 compile，再使用 package `--skip-defconfig`。

## 验证

- 完整 debug compile 退出 0，内核、应用、UBIFS/SquashFS 与尺寸检查全部完成。
- 生成 `.d` 包含头文件空目标，且不再引用两个旧显示头文件路径。
- 主仓库与应用仓库 `git diff --check` 均退出 0。
- 未执行 SD package；本记录只证明 compile 与静态打包前置条件通过。

### 离线待验证（可选）

仅在现场或离线排障先记录、后补验证时保留此块；未验证内容必须留在假设、风险或后续动作中。

```yaml
manual_validation_pending: true
manual_validation_reason: 等待维护者复核后纳入正式构建 runbook
required_followup: rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
owner: leiwenjun
review_after: 2026-11-04
```

## 后续动作

维护者复核后，可把“no-clean 依赖规则”和“debug 镜像符号分层”提升为构建 runbook；当前不提升为强制发布规则，也不代表 SD 包或板端 NFS 挂载已经验证。
