---
related:
- indexes/obsidian-home.md
target_version: null
test_environment: null
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
aliases:
- 软件工具干净源码验证审计 2026-07-15
id: software-tool-evidence-audit-20260715
title: 软件工具干净源码验证审计 2026-07-15
kind: validation
domain: governance
path: governance/product/validation/software-tool-evidence-audit-20260715.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: manual-entry:knowledge-new.sh
  source_sha256: 21383d3c228cbf679e64e8ec1ed7ec35de74b1486fd8cf8889b7599425569f30
review_after: '2026-10-15'
review_status: human-reviewed-accepted
content_review_status: accepted
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- knowledge-hub
- software-tool
- validation
- clean-source
- manual-validation-pending
validation_refs:
- governance/product/validation/software-tool-evidence-audit-20260715.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: reviewing-validation-pending
evidence_refs:
- governance/product/validation/software-tool-evidence-audit-20260715.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-15'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-15'
manual_validation_pending: true
summary_zh: 核验五个软件工具精确 Git commit、MM32SPIN Validator 无 HEAD source snapshot 及三套本地 release 目录；测试和 checksum 结果可审计，但远端留存、回滚、设备采用及
  Validator 的发布源码 provenance 仍待补齐。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# 软件工具干净源码验证审计 2026-07-15

## 摘要与适用范围

本报告记录 5 个软件工具精确 Git commit，以及 1 个尚无 Git HEAD 的 source snapshot 的单元测试、结构检查或本地 release build 门禁。Git 项目采用干净 archive 快照；`agent-dev-kit` 因完整测试依赖 Git 元数据和相邻生态仓，另在确认工作树干净的真实 source workspace 上复跑。`mm32spin-validator` 以 46 个源文件的 SHA256 inventory 固定输入，不把未提交工作区伪装成 commit。

这些结果可证明所列 commit 在本机软件环境中的对应门禁结果，但不证明用户已经采用、现场设备可用或回滚有效。后续审计还发现 `workspace://llm-tools/releases` 下有三套受 `SHA256SUMS.txt` 保护的 release 目录：它们可作为本机发布记录与 artifact integrity 证据，但目录位于 Hub 外部、远端留存未经验证，不能等同于正式发布渠道可恢复性。

## 验证对象

| 项目 | 精确 commit | 本轮验证入口 |
|---|---|---|
| `firmware-release-tools` | `60da54f1cef463d8ca87952f29297a557f28c071` | Python tests |
| `firmware-toolchains` | `20119aec7c8e47bc5325a1a0a3fbdc6ca9c1a5cf` | structure 与工具版本检查 |
| `agent-dev-kit` | `0d25f3da7ac1f141a5172d62cfc7b6f4bfbd93b1` | 完整 `devkit.sh test` |
| `ota-packager` | `fe4355b9a3cb1b9de4de12c852b39950e0a52dea` | 48 tests、GUI/CLI release build |
| `sigmastar-flasher` | `379b9534b192413e2b260c9b7c8046b6d845cc6f` | 45 tests、无串口 GUI/CLI release build |
| `mm32spin-validator` | 无 HEAD；source snapshot `4cc8860e18ae19c442ff937f933efd24313868ddec6f226d53f578137b644cf6` | 19 tests、release check、GUI/CLI build 与 smoke |

## 环境

- 日期：2026-07-15。
- 快照根：`/tmp/kh-terminal-evidence-20260715-1045/<project>`；由精确 commit 的 `git archive` 解包，避免使用源仓未提交内容。
- `agent-dev-kit` 完整复跑目录：`workspace://agent-dev-kit`；复跑前确认工作树干净且 HEAD 与表中 commit 一致。
- GUI/CLI build 环境：Linux、Python `3.8.10`、PyInstaller `6.21.0`、PySide6 `6.6.3.1`。
- 本地 release 审计根：`workspace://llm-tools/releases`；只读核验 manifest 与 checksum，未复制 binary 到 Hub，也未修改 `llm_tools` 源仓。
- `firmware-toolchains` 观察到 GNU Arm GCC `9.2.1` 与 OpenOCD `0.12.0+dev1.13.1-01850-geb6f2745b-dirty`。
- 未连接串口、板卡、烧录器、产线工装或现场环境；未修改任何源项目 tracked 文件。

## 验证与证据

| Cwd | Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---:|---|---|---|---|
| `/tmp/kh-terminal-evidence-20260715-1045/firmware-release-tools` | `rtk python3 -m pytest -q -p no:cacheprovider` | 0 | `18 passed in 0.81s`，发布工具单元测试通过。 | 本报告 | Tool | commit `60da54f1…c071` |
| `/tmp/kh-terminal-evidence-20260715-1045/firmware-toolchains` | `rtk bash scripts/codex-check.sh --versions` | 0 | structure、GCC/OpenOCD 探测和总门禁均为 `PASS`。 | 本报告 | Tool | commit `20119aec…a5cf` |
| `/tmp/kh-terminal-evidence-20260715-1045/agent-dev-kit` | `rtk bash scripts/devkit.sh test` | 1 | archive 中 49 通过、3 失败；失败均来自缺 `.git` 或缺相邻生态仓，证明 archive 环境不满足完整门禁前置条件。 | 本报告 | Tool / Negative Evidence | commit `0d25f3da…93b1` |
| `workspace://agent-dev-kit` | `rtk bash scripts/devkit.sh test` | 0 | 在干净真实 source workspace 中 `tests=52 pass=52 fail=0`。 | 本报告 | Project / Tool | commit `0d25f3da…93b1` |
| `/tmp/kh-terminal-evidence-20260715-1045/ota-packager` | `rtk bash scripts/release_check.sh` | 0 | 48 tests 通过；GUI 与 CLI 均由 PyInstaller 构建完成；release check 返回通过。 | 本报告 | Tool | commit `fe4355b9…2dea`；临时 binary 未保留 |
| `/tmp/kh-terminal-evidence-20260715-1045/sigmastar-flasher` | `rtk env SIGMASTAR_RELEASE_REQUIRE_SERIAL=0 bash scripts/release_check.sh` | 0 | 45 tests 通过；GUI 与 CLI 构建完成；明确跳过串口强制条件的软件门禁返回通过。 | 本报告 | Tool | commit `379b9534…cc6f`；临时 binary 未保留 |
| `/tmp/kh-terminal-evidence-20260715-1045/mm32spin-validator` | `rtk bash scripts/release_check.sh` | 0 | 19 tests 通过；协议、replay、preflight、targets、manual stop、无串口阻断、run-suite 和 GUI smoke 通过。 | 本报告 | Tool | source snapshot `4cc8860e…cf6` |
| `/tmp/kh-terminal-evidence-20260715-1045/mm32spin-validator` | `rtk bash scripts/build_gui_linux.sh` | 0 | PyInstaller GUI 构建完成，脚本内 offscreen smoke 返回 0。 | 本报告 | Tool | 临时 GUI binary |
| `/tmp/kh-terminal-evidence-20260715-1045/mm32spin-validator` | `rtk bash scripts/build_cli_linux.sh` | 0 | PyInstaller CLI 构建完成，脚本内 `protocol-info --json` 返回 0。 | 本报告 | Tool | 临时 CLI binary |
| `/tmp/kh-terminal-evidence-20260715-1045/mm32spin-validator` | `rtk ./dist/mm32spin-validator-gui --smoke-test` | 0 | 最终 GUI binary 报告 `ok=true`、version `0.1.0`。 | 本报告 | Tool | SHA256 `c3d75e46…e5f3`，59219624 bytes |
| `/tmp/kh-terminal-evidence-20260715-1045/mm32spin-validator` | `rtk ./dist/mm32spin-validator-cli protocol-info --json` | 0 | 最终 CLI binary 报告 `result=PASS`、version `0.1.0`。 | 本报告 | Tool | SHA256 `0dea4d18…600e`，5291456 bytes |

### `agent-dev-kit` archive 失败解释

archive 首次运行的 3 项失败为：

- `test_file_modes`：archive 不含 `.git`，无法读取 Git file mode。
- `test_product_maturity`：archive 不含 `.git`，无法枚举 tracked files。
- `test_agent_ecosystem_standards`：archive 环境缺 OpenSpec、vibeflow、planning-with-files、scale-engine 等相邻生态仓。

同一 commit 在完整、干净 source workspace 中 52 项全部通过，因此本报告把首次结果保留为环境边界证据，不把它归类为源码缺陷，也不删除该负证据。

### `firmware-toolchains` 制品清单身份

`firmware-toolchains` 的精确 commit 内直接保存 Linux/Windows 交叉编译器与调试器树，并由 `manifest.json` 声明平台、版本和入口：

- `manifest.json` SHA256：`6f40fc1a5c11994cac83d186f11aed2f0c4f40243d78c49aab7bdcaa299782bd`。
- `metadata/source-archives.sha256` SHA256：`fa2856dbde9d20c7cbe2c651e8593b329775556c3b750845b0d52b28e5aca307`。
- 默认 GNU Arm GCC：`9.2.1-1.1`；默认 OpenOCD：`0.12.0-6`。
- HEAD 没有指向该 commit 的 Git tag；因此 manifest 可作为当前 commit 的 artifact identity，但不能据此生成正式 `release_ref`。

### `mm32spin-validator` 无 HEAD source snapshot

该工作区是 unborn Git repository，全部 46 个 source/config/doc/test/tooling 文件尚未形成 commit。为避免把当前工作区描述成可复现 Git 版本，本轮先生成只含路径、大小和 SHA256 的清单：

- 清单：`artifacts/manifests/mm32spin-validator-source-snapshot-20260715.jsonl`。
- 清单 SHA256：`4cc8860e18ae19c442ff937f933efd24313868ddec6f226d53f578137b644cf6`。
- 文件数：46；无重复路径；扫描未发现文件名含 `.env`、secret、token、password 或 credential 的候选。
- 快照复制到 `/tmp` 后验证；构建输出没有写回源工作区。

GUI binary SHA256 为 `c3d75e46e9ecd1ac908bedb0052e3c10681b73327f26e5e65c8453a094fde5f3`，CLI binary SHA256 为 `0dea4d189d2ba4f75e7038a11e8b2eb9abcc53a82063b980bf3c4dd6e0b8600e`。二者是本轮临时构建身份，不应与 2026-05-29 的历史 Windows release artifact 混为同一制品。

### `llm_tools/releases` 本地发布目录审计

本轮对三个现存 release 目录分别执行 `rtk sha256sum -c SHA256SUMS.txt`，结果均为 0。精确引用统一固化在 `artifacts/manifests/llm-tools-release-evidence-20260715.jsonl`，Hub 只保存元数据、hash、source 边界和风险，不复制大型 binary。

| 工具 / 版本 | checksum | release manifest SHA256 | source 对齐 | 证据边界 |
|---|---|---|---|---|
| `ota-packager v1.0.0` | 7/7 OK | `bf14b052…ba3c` | release 记录的 clean HEAD 前缀与当前 root `805cc7e35…de2f`、child `fe4355b9…2dea` 精确 commit 一致 | `v1.0.0` tag 位于父 commit `b380c85`；release 记录还包含随后 Linux CLI commit，不能把 tag 当作全部制品的唯一 source identity |
| `sigmastar-flasher v1.0.0` | 10/10 OK | `142505c6…751` | release 记录的 clean HEAD 前缀与当前 root `805cc7e35…de2f`、child `379b9534…cc6f` 精确 commit 一致 | `v1.0.0` tag 位于父 commit `ef89aa1`；无串口构建和 checksum 不证明设备烧录路径 |
| `mm32spin-validator v0.1.0` | 4/4 OK | `7b7c24fb…536f` | 不可证明 | release 时 root 有 8 个 tracked change 和 2 个 untracked file，child 无 commit 且有 46 个 untracked file；历史 artifact 真实存在，但不能证明等价于本轮 `4cc8860e…cf6` source snapshot |

三套目录的 `release-manifest.json`、`commit-manifest.md` 和 `SHA256SUMS.txt` 自身 hash 均写入同一 Hub manifest。该证据支持填充本地 `artifact_refs` / `release_ref`，但契约必须保持 `pending`：远端留存、签名、回滚演练和真实采用均未验证；Validator 另有 source provenance 缺口。

## 当前结论

- 5 个精确 commit 和 1 个无 HEAD source snapshot 均取得与各自门禁范围匹配的直接命令证据。
- `firmware-toolchains` 的版本清单和来源校验清单具有精确 SHA256，可绑定为 commit 内 artifact 证据；正式 release record 仍缺失。
- `ota-packager` 与 `sigmastar-flasher` 的本轮临时 release build 仍不是长期 artifact；但已发现并核验 2026-05-19 本地 release 目录，可绑定为“本地发布目录 checksum 通过”的 artifact/release 证据，不代表远端发布或可恢复性。
- `sigmastar-flasher` 使用 `SIGMASTAR_RELEASE_REQUIRE_SERIAL=0`，只能证明无硬件软件门禁，不能填充 `device_refs`。
- `mm32spin-validator` 的 source snapshot 与软件门禁可绑定为当前 source/validation 证据；历史 v0.1.0 Windows artifact checksum 也可绑定，但 release 时源仓未提交，二者不可声称等价或可复现。
- 所有项目仍缺本轮 owner attestation 与 rollback drill；本地 release 目录的远端留存也未验证，因此 evidence contract 必须保持 `pending`。

## 风险与限制

- 两个 PySide6 构建均出现 OpenSSL build/runtime 版本不兼容提示；虽然 PyInstaller 返回 0，仍需在实际发布目标系统运行 smoke test。
- `sigmastar-flasher` 构建日志包含针对其他操作系统串口库的缺失 warning；无串口模式未覆盖真实枚举、擦写、重试和失败恢复。
- `mm32spin-validator` GUI 构建同样出现其他操作系统串口库缺失 warning；本轮未连接真实电机或串口，危险写命令只验证了 fail-closed 阻断。
- `firmware-toolchains` 的 OpenOCD 版本带 `dirty` 标识；本轮只记录实际工具版本，不将其解释为可复现的正式工具链发布。
- `workspace://llm-tools/releases` 是 Hub 外部的本地目录；虽然逐文件 checksum 已通过，仍需验证远端或离线备份位置、访问权限与恢复路径。
- OTA 与 SigmaStar 的 Windows executable 均记录 `Authenticode: NotSigned`；checksum 只证明当前目录内容完整，不提供发布者身份认证。
- Validator 历史 release 的 source provenance 不完整；在形成 commit 并重发前，禁止把 v0.1.0 artifact 描述为当前 snapshot 的可复现构建。

## Review 与后续动作

```yaml
manual_validation_pending: true
manual_validation_reason: 尚缺远端制品留存、rollback drill、真实采用；SigmaStar 尚缺串口和设备路径验证；Validator 历史 release 尚缺可复现 source provenance。
required_followup:
  - 由 owner 确认各工具目标版本和发布目标
  - 将本地 release manifest/checksum 与远端或离线备份位置绑定并验证恢复
  - 在隔离环境执行 rollback drill
  - 对 SigmaStar flasher 执行有串口和目标设备的 strict preflight
  - 为 MM32SPIN Validator 建立 Git commit，并从该 commit 重发可复现制品
owner: leiwenjun
review_after: 2026-10-15
```
