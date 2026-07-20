---
related:
- projects/mcu/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
target_version: null
test_environment: null
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
aliases:
- MCU NAS 发布制品与契约验证 2026-07-15
id: mcu-release-evidence-audit-20260715
title: MCU NAS 发布制品与契约验证 2026-07-15
kind: validation
domain: projects/mcu
path: projects/mcu/validation/2026-07-15-nas-release-evidence-audit.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: current-session read-only NAS release evidence audit under auth-20260715-knowledge-hub-terminal-maturity-full-closeout
  source_sha256: 21383d3c228cbf679e64e8ec1ed7ec35de74b1486fd8cf8889b7599425569f30
review_after: '2026-10-15'
review_status: human-reviewed-accepted
content_review_status: accepted
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- mcu
- release
- validation
- artifact-sha256
- manual-validation-pending
validation_refs:
- projects/mcu/validation/2026-07-15-nas-release-evidence-audit.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: reviewing-validation-pending
evidence_refs:
- projects/mcu/validation/2026-07-15-nas-release-evidence-audit.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-15'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-15'
manual_validation_pending: true
summary_zh: 核验 GD32L235、HC32F072、MM32SPIN023C 最新 NAS 发布目录的 manifest、逐文件 SHA256 与当前 firmware-release-tools 兼容性；三包 checksum
  通过，MM32 契约通过，GD32/HC32 旧 schema 待兼容，实机与回滚仍未验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# MCU NAS 发布制品与契约验证 2026-07-15

## 验证目标

核验 GD32L235、HC32F072、MM32SPIN023C 三个 MCU 项目在 NAS 上最新版本目录的发布记录、逐文件 SHA256 完整性，以及发布包与当前 `firmware-release-tools` 契约的兼容性。

本报告只证明已列命令在指定环境中的结果。它不证明固件功能正确、设备烧录成功、量产可用、现场发布成功或回滚有效，也不构成 owner 批准。

## 验证对象

验证工具为 `firmware-release-tools` commit `60da54f1cef463d8ca87952f29297a557f28c071`。验证对象为：

| 项目 | 版本 | NAS 发布目录 | 发布状态 |
|---|---|---|---|
| GD32L235 | `1.1.35` | `/mnt/mcu-release-nas/robot/mcu/gd32l235_设备/gd32l235_firmware_bundle_v1.1.35_20260629-142306` | `published`，`2026-06-29 14:23:14+08:00` |
| HC32F072 | `1.1.6` | `/mnt/mcu-release-nas/robot/mcu/hc32f072_充电桩/hc32f072_firmware_bundle_v1.1.6_20260629-142306` | `published`，`2026-06-29 14:23:15+08:00` |
| MM32SPIN023C | `0.4.9` | `/mnt/mcu-release-nas/robot/mcu/mm32spin023c_电机/mm32spin023c_firmware_bundle_v0.4.9_20260708-174609` | `published`，`2026-07-08 17:46:11+08:00` |

## 环境与边界

- 日期：2026-07-15。
- 主机：Knowledge Hub 当前受控执行主机。
- NAS：`/mnt/mcu-release-nas` 已挂载；凭证文件和发布根目录存在。报告不记录凭证内容。
- 工具：在干净的 `firmware-release-tools` Git HEAD 上执行；工具仓工作树未被修改。
- 设备：未连接或操作任何板卡、调试器、烧录器、产线工装或现场设备。
- 运行范围：只读检查 NAS 制品与 manifest；未发布、覆盖、删除或修改 NAS 内容。

## 验证命令

下表中的 `<bundle>` 分别替换为“验证对象”表中的三个绝对目录；每个命令均独立执行。

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash scripts/setup-nas-mount.sh --check` | 0 | NAS mount、凭证路径和 release root 检查通过。 | `workspace://firmware-release-tools/scripts/setup-nas-mount.sh` | Tool / Storage | 三个 NAS bundle |
| `rtk sha256sum -c checksums.sha256.txt`（GD32L235 bundle） | 0 | 清单内全部文件返回 `OK`。 | GD32L235 bundle 的 `checksums.sha256.txt` | Artifact | GD32L235 `1.1.35` |
| `rtk sha256sum -c checksums.sha256.txt`（HC32F072 bundle） | 0 | 清单内全部文件返回 `OK`。 | HC32F072 bundle 的 `checksums.sha256.txt` | Artifact | HC32F072 `1.1.6` |
| `rtk sha256sum -c checksums.sha256.txt`（MM32SPIN023C bundle） | 0 | 清单内全部文件返回 `OK`。 | MM32SPIN023C bundle 的 `checksums.sha256.txt` | Artifact | MM32SPIN023C `0.4.9` |
| `rtk bash scripts/firmware-release.sh check-package <bundle>`（GD32L235） | 3 | `[ERROR] unsupported schemaVersion`；旧包契约不兼容当前工具。 | GD32L235 bundle 的 `package_manifest.json` | Tool / Contract | GD32L235 `1.1.35` |
| `rtk bash scripts/firmware-release.sh check-package <bundle>`（HC32F072） | 3 | `[ERROR] unsupported schemaVersion`；旧包契约不兼容当前工具。 | HC32F072 bundle 的 `package_manifest.json` | Tool / Contract | HC32F072 `1.1.6` |
| `rtk bash scripts/firmware-release.sh check-package <bundle>`（MM32SPIN023C） | 0 | package manifest 与 checksums 契约均有效。 | MM32SPIN023C bundle 的 `package_manifest.json` | Tool / Contract | MM32SPIN023C `0.4.9` |

## 结果矩阵

| 项目 | 发布记录 | 文件完整性 | 当前契约兼容性 | 实机验证 | 回滚验证 | 综合结论 |
|---|---|---|---|---|---|---|
| GD32L235 | 有 | 通过 | 失败：旧 `schemaVersion` 不受支持 | 未执行 | 未执行 | 部分通过；不得标记 evidence-ready |
| HC32F072 | 有 | 通过 | 失败：旧 `schemaVersion` 不受支持 | 未执行 | 未执行 | 部分通过；不得标记 evidence-ready |
| MM32SPIN023C | 有 | 通过 | 通过 | 未执行 | 未执行 | 制品层通过；项目整体仍不得标记 evidence-ready |

## 制品身份

以下 SHA256 是 manifest 或 checksum 清单文件自身的身份，用于后续引用绑定；它们不能替代逐文件校验结果。

| 项目 | `package_manifest.json` SHA256 | `release_manifest.json` SHA256 | `checksums.sha256.txt` SHA256 | Source digest |
|---|---|---|---|---|
| GD32L235 | `4dc1ef77ad50c86e674bb9bef7b49c04b053e0b22092d14f05b093765a4a26e4` | `515b5e3e0aa499e11fc0fe6681a37d2b059aead581692636b79cb30ca6ef318a` | `215690c281d801af12cec184281e0fa251a4251d105989c3c1e8401dd1ed273e` | `8001ea…a783` |
| HC32F072 | `016c9f54c0d6e34d38719314c6732f3ed39bf4728086d719714c6e8a32fee1be` | `b30730c4b3aa66894f12c5f518e4a56e8eb8969caff0ec744a4f05ed9d9b5a4e` | `50d428c26f9c4f3f4857ad796309b265982c1a3bf1f12a8ad5c5a1426e6bb1f3` | `c7c222…e0a` |
| MM32SPIN023C | `6460228e4de4f85a523e4480c4242801bf95c1d03bdbf5ccc8a9b2bb3bcb0afd` | `215361a080ba3e409f5c19d6e2f672b5509925cac9f71f251c9139c18739f487` | `d7f8d6e90658fe755dd206bda7808251c4c7893193f6795393392542e9aa4c52` | `bc1fb0…6076` |

Source digest 在本次控制台证据中只保留了首尾摘要，因此本报告不把它登记为精确 source 引用；项目 source identity 继续以各自 validation contract 中已解析的 Git commit 为准。

## 精确源码快照构建补充验证

为区分“旧 NAS 制品契约不兼容”和“当前源码无法构建”，本轮又对 GD32L235、HC32F072 的已登记精确 commit 执行了隔离构建。根仓与工具链分别由 `git archive` 生成，工具链固定为 gitlink commit `caeb712d508274c6539f693ea4efe7e15a607ce3`；源仓已有未提交内容不进入快照。

| Cwd | Command | Exit Code | 结果摘要 | Layer | Related Artifact |
|---|---|---:|---|---|---|
| `/tmp/kh-terminal-evidence-20260715-1045/gd32l235` | `rtk bash scripts/codex-check.sh --full` | 0 | 19 个 `Tools/tests` 契约检查完成；Stage0、Stage1、App 共 65 个构建步骤完成；build/package/check 均为 `PASS`。 | Project / Tool | source `555eded00292581755cdbad6baad343066f46a6a` |
| `/tmp/kh-terminal-evidence-20260715-1045/hc32f072` | `rtk bash scripts/codex-check.sh --full` | 0 | HC32 App 共 44 个构建步骤完成；build/package/check 均为 `PASS`。 | Project / Tool | source `b4a6d396e607669ddcc22cdf309af7a6968652d9` |
| `workspace://firmware-release-tools` | `rtk bash scripts/firmware-release.sh check-package /tmp/kh-terminal-evidence-20260715-1045/gd32l235/build/gcc-ninja/package/gd32l235_firmware_bundle` | 3 | 当前源码重新生成的 package 仍无受支持的 `schemaVersion`，返回 `[ERROR] unsupported schemaVersion`。 | Tool / Contract | 临时 GD32L235 `1.1.35` package |
| `workspace://firmware-release-tools` | `rtk bash scripts/firmware-release.sh check-package /tmp/kh-terminal-evidence-20260715-1045/hc32f072/build/gcc-ninja/package/hc32f072_firmware_bundle` | 3 | 当前源码重新生成的 package 仍无受支持的 `schemaVersion`，返回 `[ERROR] unsupported schemaVersion`。 | Tool / Contract | 临时 HC32F072 `1.1.6` package |

构建结果显示：源码构建与各仓内部 package/check 门禁通过，但两个仓自身生成的 `package_manifest.json` 与独立 `firmware-release-tools` 当前契约仍不兼容。该问题不是只存在于旧 NAS 副本，而是当前两个源码仓的 package schema 与集中发布工具之间存在真实 contract drift。

### 临时构建制品身份

| 项目 | 临时 package manifest SHA256 | 临时 ZIP SHA256 | 临时 checksum 清单 SHA256 |
|---|---|---|---|
| GD32L235 | `338beb0704fe8a57c1aa6d364117e72f2e97846e839573d9f2ae728f5e3f6a33` | `b0ef4b75feaee2828fdd042bc285a9f646471e2b801037d8963df80f3ee5bf07` | `8ffe5a379578812ada994ecb6e3b2fa076e5316434d0e1db75dc101b7378280d` |
| HC32F072 | `dfa2b4edd508aa1b556296ec698444f2243ed05f360ca0c9d14c88cfe9a94ba7` | `e99adefcf515f88c4ff5ecd042aabeca82ddca9b5b8282b4f1b7b779727b3f64` | `3f536d343e1107fc70f344b771bef3ebb0bb9725b4832513cf1743f8536ae0db` |

这些制品位于临时验证目录，脚本执行完成后不作为正式 artifact 或 release record。GD32L235 构建保留官方库 allowlist 内的 `-Wtautological-compare` warning；HC32F072 构建包含 `unused parameter`、非标准 `main` 返回类型、signedness comparison 等 warning。退出码为 0 不代表这些 warning 已被消除。

## 结论

本轮结论为“部分通过”：

- 三个 NAS 发布目录均有 `published` release record，且逐文件 SHA256 校验通过，可作为真实 artifact 与 release 证据候选。
- MM32SPIN023C `0.4.9` 的发布包通过当前工具契约检查，可作为制品层 validation 证据候选。
- GD32L235 `1.1.35` 与 HC32F072 `1.1.6` 的精确源码 commit 均通过仓内 full build/package/check；这是真实软件构建证据，但不是设备证据。
- GD32L235 与 HC32F072 的旧 NAS manifest 及当前源码重新生成的 manifest 都未提供集中发布工具支持的 `schemaVersion`，契约检查返回 3；在两个源码仓修正 package schema 并复验之前，不得声明集中发布契约通过。
- 三个项目均缺本轮实机执行和 rollback drill，因此项目级 evidence contract 仍不能进入 `ready`。

## 剩余风险与待验证项

- 需要 owner 决定 GD32L235、HC32F072 是采用受控旧 schema 兼容验证，还是从已发布 source/artifact 重建新契约包；本报告不代签该决定。
- 需要在准确记录设备型号、硬件版本、工具链、操作者、固件 hash 和日志的前提下执行实机验证。
- 需要执行可恢复的 rollback drill，并记录恢复目标、步骤、返回码和恢复后验证。
- NAS 上存在制品不等于该制品已被真实设备或生产环境采用。

```yaml
manual_validation_pending: true
manual_validation_reason: 三个项目均未完成实机与回滚；GD32L235、HC32F072 还存在旧 schema 兼容阻塞。
required_followup:
  - 为 GD32L235、HC32F072 形成 owner 批准的旧 schema 兼容或重打包方案
  - 补齐三个项目的 device-run 与 rollback-drill 证据
  - 重跑项目 readiness evaluator 与 full terminal gate
owner: leiwenjun
review_after: 2026-10-15
```
