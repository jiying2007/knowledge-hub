---
related:
- indexes/obsidian-home.md
- governance/product/validation/project-readiness.md
- governance/product/validation/knowledge-hub-terminal-closure-validation-20260718.md
- projects/mcu/validation/2026-07-15-nas-release-evidence-audit.md
- governance/product/validation/software-tool-artifact-restore-drill-20260716.md
target_version: Knowledge Hub 6edda6ff1bf6c46f9fff3bcea0f2e135b1629754 及本报告列明的精确项目提交
test_environment: Linux；精确 Git archive；锁定 toolchain gitlink；源仓只读；隔离 build/package/check
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
aliases:
- Knowledge Hub 真实项目证据与反馈波次 2026-07-26
id: knowledge-hub-real-evidence-feedback-wave-20260726
title: Knowledge Hub 真实项目证据与反馈波次 2026-07-26
kind: validation
domain: governance
path: governance/product/validation/knowledge-hub-real-evidence-feedback-wave-20260726.md
scope: team-general
visibility: team-internal
status: draft
owner: leiwenjun
source:
  type: manual
  from: 2026-07-26 current-session exact Git archive builds, package validation, read-only remote ref audit and retrieval
    interactions
  source_sha256: 21383d3c228cbf679e64e8ec1ed7ec35de74b1486fd8cf8889b7599425569f30
review_after: '2026-08-26'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- knowledge-hub
- project-evidence
- retrieval-feedback
- validation
- manual-validation-pending
validation_refs:
- governance/product/validation/knowledge-hub-real-evidence-feedback-wave-20260726.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- governance/product/validation/knowledge-hub-real-evidence-feedback-wave-20260726.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-26'
updated_at: '2026-07-27'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-26'
manual_validation_pending: true
summary_zh: 记录 30 项项目证据漂移审计、4 个干净源仓的精确 archive 构建与制品校验、远端 ref 只读回读，以及已由用户确认并写入账本的 10 条真实检索反馈；不把 dry-run、用户口述 CI 或单条授权伪装成实机或异地恢复证据。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# Knowledge Hub 真实项目证据与反馈波次 2026-07-26

## 验证目标

本报告推进两类终态阻塞：

- 重新发现 30 个登记项目的 canonical workspace，核对 evidence contract 绑定的 source identity 是否漂移。
- 对当前可安全复验的干净源仓执行精确 Git archive 构建、测试、打包和远端 ref 只读回读。
- 固化 10 次服务于本次证据审计的真实检索 interaction，并按实际使用者逐条确认写入 `found` 或 `not-found`。

本报告不证明以下事项：

- 用户口述“CI 已过”不等于本机已取得 SHA 绑定的 CI artifact。
- build/package/check 或烧录脚本 `--dry-run` 不等于真实设备烧录、回读、HIL 或生产回滚。
- 一个远端分支、tag 或本地 package 不自动构成 NAS/正式 release record。
- 一条“授权推进”不等于 10 条真实检索反馈；本轮反馈以实际使用者逐条确认和 feedback ledger 为准。
- 本报告是 `draft` evidence candidate，不提升 active，不改变 30 个 readiness contract 的 lifecycle `status`。

## 当前终态基线

`knowledge-final-gate.sh --final-profile product --regression-suite full --reuse-engineering-evidence --summary-json`
在 Knowledge Hub `6edda6ff1bf6c46f9fff3bcea0f2e135b1629754` 上返回：

| 字段 | 结果 |
| --- | --- |
| `gate_status` | `pass` |
| `platform_productization_complete` | `true` |
| `local_delivery_complete` | `true` |
| `remote_published` | `false` |
| `offsite_restore_verified` | `false` |
| `adoption_ready` | `false` |
| `terminal` | `false` |
| 项目 evidence-ready | `0/30` |
| 项目字段完整 | `4/30` |
| 采用观测 | 389 次 invocation、12 天、0 条 feedback |

终态仍有 4 个真实证据阻塞：项目证据、远端发布、异地恢复、真实采用。

## 30 项 source 漂移审计

### Canonical workspace 发现

`knowledge-workspace-discover.sh --apply --first-party-only --json` 只写 ignored
`local/workspaces.json`，不写源项目和 tracked registry。结果为：

- 29/29 registered remote 均命中本地工作区，scan error 为 0。
- 30/30 项目的 workspace state 为 `all-mapped-and-present`；`mcu` 为 aggregate group。
- 16 个 remote key 存在多个本地副本。证据只使用 registry 选定的 canonical path，alternate path 不参与 source identity。
- 28 个 Git 项目中，20 个当前 HEAD 与 contract 绑定 SHA 精确一致，8 个 HEAD 向前演进；`mcu` 为 aggregate，`mm32spin-validator` 为受治理 snapshot。

### 向前演进的 8 个项目

| 项目 | contract SHA | 当前 canonical HEAD | 演进 | 工作区 | 本轮处理 |
| --- | --- | --- | ---: | --- | --- |
| `gd32l235` | `555eded…a6a` | `6fd343d…be6` | 34 commits | clean | 精确 archive full build/package/check |
| `hc32f072` | `b4a6d39…2d9` | `a1208cf…f65` | 14 commits | clean | 精确 archive full build/package/check |
| `mm32spin023c` | `b0857ae…bda` | `84b6afe…b41` | 1 commit | clean | 精确 archive + 外部输入 hash + package gate |
| `firmware-release-tools` | `60da54f…071` | `a2e0ce6…96b` | 3 commits | clean | 精确 archive 25/25 tests |
| `codex` | `a27c022…c1c` | `cd62431…c88` | 4 commits | dirty | 不生成新 evidence |
| `llm-agent` | `150fdee…94` | `8a4a3ee…132` | 9 commits | dirty | 不生成新 evidence |
| `agent-dev-kit` | `0d25f3d…3b1` | `54a4d7f…e78` | 15 commits | dirty | 不生成新 evidence |
| `knowledge-hub` | `349198e…760` | `6edda6f…754` | 27 commits | clean | 使用当前 full gate 与 restore 证据 |

8 个旧 SHA 均仍是当前 HEAD 的祖先，没有发现历史重写。旧 contract SHA 绑定旧验证结果，
不能机械替换为新 HEAD；只有本报告中已执行的验证可作为新证据候选。

## 本轮真实项目证据

### 传输、权限和脱敏边界

- 远端传输只使用各源仓既有 Git `origin` 执行 `ls-remote`；不读取或打印 remote URL、token、私钥。
- 输出只保留 ref 与 SHA；不执行 push、tag、release、merge、rebase 或源项目写入。
- 构建输入来自精确 Git archive；GD32/HC32 toolchain 固定为 gitlink
  `caeb712d508274c6539f693ea4efe7e15a607ce3`。
- 临时快照、二进制和 raw build log 不进入 Hub；正文只保留命令、退出码、版本、摘要和 SHA256。
- 未连接或操作板卡、调试器、烧录器、NAS 发布目录或现场环境。

## 验证命令

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `knowledge-workspace-discover.sh --apply --first-party-only --json` | 0 | 29/29 remote mapped，30/30 workspace present，16 个重复 remote 被隔离为 alternate | ignored local mapping | Knowledge Hub | source identity matrix |
| `knowledge-project-readiness.sh --check --json` | 0 | 30 projects / 30 contracts / changed 0 | current registry and contracts | Knowledge Hub | readiness structure |
| `knowledge-final-gate.sh ... --summary-json` | 0 | 工程门禁 pass；terminal false；4 个真实证据 blocker | signature-bound local snapshot | Knowledge Hub | `6edda6f…754` |
| `python3 -m unittest discover -s tests -v` | 0 | `firmware-release-tools` 25/25 tests PASS | exact source archive | Project / Tool | `a2e0ce6…96b` |
| `bash scripts/codex-check.sh full` | 0 | GD32L235：34 个静态契约检查；66 步 Release build；package/check PASS | exact source + toolchain archives | Project | `6fd343d…be6` / `v1.1.39` |
| `bash scripts/codex-check.sh full` | 0 | HC32F072：3 个静态契约检查；44 步 Release build；package/check PASS | exact source + toolchain archives | Project | `a1208cf…f65` / package `1.1.8` |
| `release-mm32spin023c.sh --repo <isolated-repo>` | 0 | package/check、3 个生成脚本 dry-run、HEX/BIN compare、split-full 全部通过 | exact source archive + hash-bound external inputs | Project / Tool | `84b6afe…b41` / package `0.4.9` |
| `git ls-remote origin <exact refs>` | 0 | GD32/HC32/MM32/firmware-release-tools 分支实时回读；仅 GD32 当前 HEAD 有匹配 release tag | remote refs | Project / Release | 下方远端矩阵 |

补充说明：

- date：`2026-07-26`
- source scope：4 个 clean project repository，全部只读
- write scope：Knowledge Hub report candidate、ignored telemetry/local mapping、隔离临时目录
- deny path：源项目、设备、NAS、tag、release、remote mutation、memory

## 结果矩阵

| 项目 | 精确输入 | 本轮结果 | 远端身份 | 可支持的结论 | 仍不可声明 |
| --- | --- | --- | --- | --- | --- |
| `firmware-release-tools` | commit `a2e0ce699c09cb18d7a6fb999a0ab244c4a6e96b` | 25/25 tests；CLI help PASS | `origin/master` 精确匹配 HEAD | 当前工具软件层验证通过 | artifact/release/rollback |
| `gd32l235` | commit `6fd343dbab7413e35d4d3d621dffd64824802be6` + locked toolchain | full build/package/check PASS；warning 30/30 均在 vendor allowlist；容量门禁通过 | `origin/master` 与 `v1.1.39^{}` 均精确匹配 HEAD | source、build、local artifact、Git release identity | device run、flash/readback、生产 rollback、NAS 留存 |
| `hc32f072` | commit `a1208cff6b24fc49dc04debdd583842113f25365` + locked toolchain | full build/package/check PASS；warning 4/5，均在 allowlist；容量门禁通过 | `origin/master` 匹配 HEAD；`v1.1.8^{}` 指向前一提交 `c36c396…209` | 当前 source/build/local artifact | 当前 HEAD 的 immutable release、device、rollback |
| `mm32spin023c` | commit `84b6afe861474a81f0c1a8b8c2fa9d61da033b41` + boot/app SHA256 | package/check/dry-run/compare/split PASS | `origin/master` 匹配 HEAD；远端无 `v0.4.9` tag | source、输入、local artifact contract | immutable Git release、真实烧录/回读、rollback |
| `knowledge-hub` | commit `6edda6ff1bf6c46f9fff3bcea0f2e135b1629754` | full engineering/final gate 与本地 HEAD restore PASS | 用户报告 CI PASS，但 artifact 未摄入 | local delivery complete | remote published、offsite restore |

## Artifact SHA256

以下均为隔离构建结果；制品二进制不进入 Hub。`source archive` 用于证明验证输入，
不能替代 remote release 或长期制品留存。

| 项目 | 对象 | SHA256 |
| --- | --- | --- |
| `firmware-release-tools` | source archive | `da9cbd97bb108aa7d19b24b4db3acedcfe1de750b5577c939c1361bfa065aeca` |
| `gd32l235` | source archive | `4644b0ed3e3991af7457d10023a0a2c823349bc1b35a8441598b381f9c6c4e62` |
| `gd32l235` | package ZIP | `a159e9a57e33745d6882aa31c479c7231512fcb846bf2bb574498602589cc9f5` |
| `gd32l235` | `package_manifest.json` | `70603452ec8a87de17eec9683d88ac01179719acffbdef4368a84dca4e8334ea` |
| `gd32l235` | `checksums.sha256.txt` | `f7f4ccbfb96f0aa746ce2b627217ccac1615affb4788920302a1c7120ea2998d` |
| `hc32f072` | source archive | `4ed95b7dc9245f05f97146e42600175ebdce9a3025524b010f7cb77f93c21fc2` |
| `hc32f072` | package ZIP | `922a11532aea446324e49b8502bfaa766692df423cfea21a91101b8493bee758` |
| `hc32f072` | `package_manifest.json` | `693ed00a7a679a9c21078892971d5be591dede3f9b4b0f62c525f0a9ddd55969` |
| `hc32f072` | `checksums.sha256.txt` | `698e9a536ae01df4fa1d07f4a628dedc9170dfc21a7856d773d47c18757ba461` |
| `mm32spin023c` | source archive | `1cd7e3ec967e42f46f462f375161ca54f1136b61705274b244c23bcfa0ea1849` |
| `mm32spin023c` | boot input | `ba61947b3022a9a23cef84f680d5d8c70846d4983f112510091c944b1ac8ad22` |
| `mm32spin023c` | app input | `29d671a96801f030046c3e97d91639861a9655ffa5bbd8baea8f950be7fd0670` |
| `mm32spin023c` | package ZIP | `2a4faf26abf86b270a08f15ea61b8e370947a97a56912ca244c74bbc7fe5c428` |
| `mm32spin023c` | `package_manifest.json` | `972fe1b1cbfe74a0571e283c788447da5e4809999837c5bee14090406a909939` |
| `mm32spin023c` | `checksums.sha256.txt` | `2156cca03e61006e13054ad7ee3b3e60fe9ae37176991b4d607046bb2e188929` |

## 远端只读回读

| 项目 | ref | 远端 SHA | 判定 |
| --- | --- | --- | --- |
| `firmware-release-tools` | `refs/heads/master` | `a2e0ce699c09cb18d7a6fb999a0ab244c4a6e96b` | 当前 HEAD 已发布到分支 |
| `gd32l235` | `refs/heads/master` | `6fd343dbab7413e35d4d3d621dffd64824802be6` | 当前 HEAD 已发布到分支 |
| `gd32l235` | `refs/tags/v1.1.39^{}` | `6fd343dbab7413e35d4d3d621dffd64824802be6` | release tag 与当前 HEAD 精确一致 |
| `hc32f072` | `refs/heads/master` | `a1208cff6b24fc49dc04debdd583842113f25365` | 当前 HEAD 已发布到分支 |
| `hc32f072` | `refs/tags/v1.1.8^{}` | `c36c396542c01e8ce0d5b85180335dbb8e113209` | tag 早于当前 HEAD，不合并解释 |
| `mm32spin023c` | `refs/heads/master` | `84b6afe861474a81f0c1a8b8c2fa9d61da033b41` | 当前 HEAD 已发布到分支 |
| `mm32spin023c` | `refs/tags/v0.4.9^{}` | 无 | 当前 package 不是远端 tag 证据 |

## CI 证据边界

用户在本轮明确报告“CI 已过”。该信息可作为取证入口，但在取得并验证
`knowledge-hub-quality-evidence` artifact 之前，门禁仍必须保持：

- `remote_published=false`
- `offsite_restore_verified=false`

需要摄入的文件至少包括：

- `.cache/knowledge-hub/restore-drill-head.json`
- `.cache/knowledge-hub/final-gate-product-full.json`
- `.cache/knowledge-hub/engineering-quality.json`

其中 `restore-drill-head.json` 必须同时满足：

- `source_revision=6edda6ff1bf6c46f9fff3bcea0f2e135b1629754`
- `execution_environment.provider=github-actions`
- `execution_environment.event=push`
- `execution_environment.runner_environment=github-hosted`
- `remote_published_ref_verified=true`
- `offsite_environment_verified=true`
- `status=pass`

当前会话没有 GitHub connector、`gh` 或可用 API token，因此未下载 artifact；不使用本机 restore 结果冒充。

## 10 条真实反馈确认结果

下表中的检索均已实际执行并写入 telemetry，实际使用者随后逐条确认，Codex 已将结果写入
feedback ledger。`selected_id` 均来自对应 interaction 的结果；两个 zero-hit 交互保持
`not-found` 且未填写 `selected_id`。

| # | 精确 query | 本次真实结果 | 确认 outcome | selected_id |
| ---: | --- | --- | --- | --- |
| 1 | `Knowledge Hub 终态门禁 远端发布 异地恢复` | 3 hits；首位为终态验证 | `found` | `knowledge-hub-terminal-closure-validation-20260718` |
| 2 | `30 项目 evidence contract 真实证据 readiness 缺口` | 3 hits；readiness 总入口在结果中 | `found` | `knowledge-hub-readiness-validation-20260713` |
| 3 | `PCR02 SSC305 发布 回滚 实机证据` | 3 hits；首位为 v1.1.33 NAS 审计 | `found` | `pcr02-soc-v1-1-33-nas-release-audit-20260715` |
| 4 | `MCU 固件 NAS 发布证据 GD32 HC32 MM32` | 3 hits；首位为 MCU NAS 证据审计 | `found` | `mcu-release-evidence-audit-20260715` |
| 5 | `software-tool-artifact-restore-drill-20260716 checksum rollback` | 3 hits；首位为软件工具隔离恢复 | `found` | `software-tool-artifact-restore-drill-20260716` |
| 6 | `LLM Agent 精确源码 full gate 远端恢复` | 3 hits；首位为 portable full gate | `found` | `llm-agent-portable-full-gate-remediation-20260717` |
| 7 | `Knowledge Hub 真实采用反馈 门槛` | 1 hit；readiness 总入口 | `found` | `knowledge-hub-readiness-validation-20260713` |
| 8 | `项目 lifecycle status ready owner attestation` | 3 hits；首位为 Owner Review 规范 | `found` | `knowledge-hub-owner-review-rules` |
| 9 | `Knowledge Hub CI GITHUB_SHA 发布证据` | 0 hit | `not-found` | — |
| 10 | `runtime-route-candidate 0 alias shim fallback compatibility` | 0 hit | `not-found` | — |

实际使用者已确认 1–8 找到所需内容、9–10 未找到。写入后 metrics 为：
`feedback_count=10`、`found_count=8`、`not_found_count=2`、`found_rate=0.8`，
`adoption.ready=true`。两个 `not-found` 保持真实缺口语义，不为达标改写。

## 2026-07-27 终态执行检查点

### 目标与防卡死边界

- `goal_statement`：在不合成 owner、设备、发布、回滚、CI 或异地证据的前提下，使当前终态条件逐项闭环。
- `current_stage`：S1 授权、并发变更、review queue 与 30 项 evidence contract 审计。
- `retry_budget`：每类外部动作最多 2 次；同类失败两次后回到计划审查，不盲目重试。
- `staleness_threshold`：工程与恢复证据最长 24 小时，且 `as_of` 必须为 `2026-07-27`。
- `heartbeat`：2026-07-27；远端基线、workspace mapping、review queue 和 evidence matrix 已重新读取。
- `stop_condition`：本地可验证项继续；真实设备、生产回滚、内容复核确认、远端 CI 或独立环境不可访问时转为 `replan`，不得改写为 pass。

### 当前基线

| 项目 | 当前证据 |
| --- | --- |
| 本地 HEAD | `ab7815eb6c44c0e558eb33a290ca7b3dd21a148f` |
| fresh fetch 的 `origin/master` | `6edda6ff1bf6c46f9fff3bcea0f2e135b1629754` |
| 分叉与祖先关系 | `origin/master...HEAD = 0 1`；远端是本地 HEAD 祖先 |
| workspace discovery | 34/34 登记 remote 已定位；30 个项目 workspace 均 present；17 个 remote 存在多副本 |
| review queue | 2 项：本报告与 PCR02 MCU/SoC 电机 UART 时间戳同步方案；均要求整文件 hash-bound 人工复核 |
| 采用度 | 10 条反馈，8 found、2 not-found，`found_rate=0.8`，`adoption.ready=true` |

### 30 项 evidence contract 审计

| 分组 | 数量 | 当前真实缺口 |
| --- | ---: | --- |
| `pcr02-ssc305`、GD32、HC32、MM32 | 4 | 已有 source/artifact/release 证据，但缺真实 device run 与 rollback |
| xcrz 主仓、10 个 PCR02 模块、4 个 app | 15 | 缺 artifact、device、release、rollback；现有负向构建或设计材料不能改写为通过 |
| firmware-release-tools、firmware-toolchains、Codex、LLM Agent、ADK、Knowledge Hub | 6 | 分别缺 artifact/release/rollback 或 release/rollback；当前 source HEAD 演进时必须重绑精确版本 |
| llm-tools、SigmaStar Flasher、MM32SPIN Validator、OTA Packager | 4 | 合同字段完整但仍声明 `pending`；证据只证明本地制品与隔离恢复，明确不证明远端留存或生产回滚 |
| MCU aggregate | 1 | 必须等待成员项目 ready，不能独立提前声明 |

现有权威材料明确记录：

- PCR02 v1.1.33 NAS 审计不证明目标设备已安装、启动、长稳运行或回滚成功。
- GD32/HC32/MM32 发布链不证明真实板级烧录、flash 回读或 HIL 通过。
- 三套软件工具 release manifest 的 `remote_retention` 与生产 `rollback_status` 为未验证；隔离本地恢复只能作为窄范围 rollback evidence。
- workspace discovery 只证明当前源码可定位；17 个多副本 remote 继续要求 canonical workspace + exact SHA，不能把副本混拼为一个 source identity。

因此本检查点不能把 `evidence_ready_count` 从 0 机械改成 30。后续只有取得同一 source/version/environment 的真实外部证据后才回填；否则完成声明固定为 `needs-fix`。

## 结论

本轮结论为“真实证据已推进，但终态尚未闭环”：

- 30 项 canonical workspace 映射已刷新，8 项 source 向前演进已显式识别，避免静默漂移。
- 4 个 clean 源仓完成精确、可复现的本机软件层复验；GD32 当前 HEAD 另有匹配远端 release tag。
- dirty 的 `codex`、`llm-agent`、`agent-dev-kit` 没有被错误吸收为新 source evidence。
- 10 个真实检索 interaction 已由用户逐条确认并写入 feedback ledger；采用度门禁已通过。
- CI 通过尚缺 artifact 摄入，实机/生产回滚仍缺外部环境证据。
- 本报告不改变 30 个 evidence contract 的 `pending` 状态。

## 剩余风险

- 16 个 remote 的多工作区副本可能继续产生 source identity 漂移；必须坚持 canonical path + exact SHA。
- GD32/HC32 构建存在受 allowlist 管理的 compiler warning；退出码 0 不表示 warning 消失。
- HC32 当前 HEAD 晚于 `v1.1.8` tag，MM32 当前 `0.4.9` package 没有远端 tag，不得扩写为 immutable release。
- MM32 的三个烧录/回读命令只执行 `--dry-run`，没有真实硬件结果。
- 反馈采用度已达门槛，但仍需取得 CI artifact，并补项目 device/rollback 证据；否则 `terminal` 必须保持 false。

## 后续动作

1. 提供或挂载与 `6edda6f…754` 绑定的 `knowledge-hub-quality-evidence` artifact；只读验证其 schema、SHA 和 GitHub-hosted push 环境。
2. 将本报告中可长期解析的项目证据按 source/version 边界回填对应 contract；不跨版本拼接 source、artifact 和 release。
3. 设备 owner 分别补 GD32、HC32、MM32 和 PCR02 的 device run 与 rollback drill。
4. 重跑 project readiness、full engineering、candidate/HEAD restore 和 strict terminal gate。

```yaml
manual_validation_pending: true
manual_validation_reason: SHA 绑定 CI artifact、真实设备与生产回滚尚未全部取得
required_followup:
  - 摄入 knowledge-hub-quality-evidence artifact
  - 补齐项目 device-run 与 rollback-drill
owner: leiwenjun
review_after: 2026-08-26
```
