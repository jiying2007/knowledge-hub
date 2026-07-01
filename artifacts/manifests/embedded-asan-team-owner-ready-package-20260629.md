# Embedded ASAN Team Owner Ready Package 2026-06-29

## 结论

本包把团队级 ASAN 调试方法论候选整理成 team-core 可复核材料。2026-06-29 用户已明确授权“可升 active，自动闭环”，因此本包的 review-ready 阻塞作用已由 `artifacts/manifests/embedded-asan-active-promotion-20260629.md` 消解。

- 不再作为 active promotion 的阻塞 gate。
- 不提升到 `domains/embedded/standards/`。
- 不修改 PCR02 或其他源项目。
- 不把 PCR02 构建变量、程序名、部署路径或 `libasan` 布局写成团队默认。
- 不写 `~/.codex/memories`。

当前团队级 runbook 已提升为 `active`；本包保留为 active promotion 的前置审查证据。

## Review Target

| 字段 | 值 |
| --- | --- |
| target_item | `embedded-asan-debug-guide-20260629` |
| target_path | `domains/embedded/runbooks/asan-debug-guide.md` |
| owner | `team-core` |
| current_status | `active` |
| requested_decision | `active-team-runbook`（已由 2026-06-29 用户授权闭环） |
| review_after | `2026-09-29` |

## 历史 Owner 需要确认的问题

本包形成时，team-core review 至少需要回答以下问题。2026-06-29 用户明确授权 active promotion 后，这些问题已作为风险接受和前置审查证据保留，不再作为当前 active gate：

1. 该方法论是否足够跨项目，不依赖 PCR02 的构建变量、二进制名、路径、固件布局或动态库部署方式。
2. `-fsanitize=address`、`ASAN_OPTIONS`、BuildID、离线符号化、首发错误优先和复现闭环是否适合作为团队级默认方法。
3. 是否需要至少一个非 PCR02 项目的 ASAN 实操验证记录后再升 `active`。
4. 是否允许把该 runbook 保持在 `domains/embedded/runbooks/`，而不是提升到 `domains/embedded/standards/`。

## 必填 owner 字段

正式 owner decision JSONL 如需落地，必须由 owner 填写：

- `owner_decision`
- `target_decision`
- `reviewed_by`
- `reviewed_at`
- `review_after`
- `target_status`
- `team_scope_statement`
- `non_pcr02_evidence_status`
- `promotion_decision`
- `evidence_refs`
- `open_items`
- `status_reason`

## 历史 Hard Gate

以下条件是本包形成时的 active promotion hard gate。后续 `artifacts/manifests/embedded-asan-active-promotion-20260629.md` 已按授权完成 active promotion；本节保留为历史审查依据：

- 正文仍包含 PCR02-only 构建变量、程序名、部署路径、动态库路径或项目命令。
- owner 未确认 team scope。
- owner 未确认是否接受缺少非 PCR02 实战证据的风险。
- 目标指向 `domains/embedded/standards/` 但缺少标准级 review。
- evidence refs 只包含历史 PCR02 split 证据，没有当前团队 runbook 和去项目化验证证据。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk rg -n "DEBUG=256|prog_pcr02|/customer|release/bin/prog_pcr02|libs/3rdparty/libasan" domains/embedded/runbooks/asan-debug-guide.md` | 1 | 未命中 PCR02-only 命令、程序名和部署路径。 | `domains/embedded/runbooks/asan-debug-guide.md` | Runbook | `embedded-asan-team-owner-ready-package-20260629` |
| `rtk bash tools/knowledge-regression.sh --json --suite full --as-of 2026-06-29` | 0 | full regression 覆盖团队 ASAN 去项目化门禁。 | `tools/knowledge-regression.sh` | Regression | `embedded-asan-team-owner-ready-package-20260629` |
| `rtk bash tools/knowledge-final-gate.sh --json --final-profile max-body --full-regression --as-of 2026-06-29` | 0 | final gate 通过；本包本身不生成 owner decision、不执行 active promotion，后续提升由 `embedded-asan-active-promotion-20260629` 完成。 | `tools/knowledge-final-gate.sh` | Final gate | `embedded-asan-team-owner-ready-package-20260629` |

## 闭环状态

- active promotion 已由 2026-06-29 用户明确授权和 `embedded-asan-active-promotion-20260629` 证据闭环。
- 非 PCR02 项目的 ASAN 实战记录已登记为后续增强项：`artifacts/manifests/embedded-asan-non-pcr02-evidence-followup-20260629.md`；当前未发现真实非 PCR02 实操验证记录，不再阻塞当前 active 状态。
