# Embedded ASAN Active Promotion 2026-06-29

## 结论

团队级 ASAN 调试方法论 `domains/embedded/runbooks/asan-debug-guide.md` 已按 2026-06-29 用户明确授权提升为 `active`。

本次 active promotion 只作用于团队级 runbook 条目 `embedded-asan-debug-guide-20260629`：

- 不提升到 `domains/embedded/standards/`。
- 不修改 PCR02 或其他源项目。
- 不写 `~/.codex/memories`。
- 不启用自动化写操作。
- 不做远端 push、merge、tag 或 release。
- 不把 PCR02 构建变量、程序名、部署路径或 `libasan` 布局写成团队默认。

## 授权

| 字段 | 值 |
| --- | --- |
| authorization_id | `auth-20260629-embedded-asan-active-promotion` |
| authorized_by | `leiwenjun` |
| authorized_at | `2026-06-29` |
| 用户指令 | `按建议处理落地，可升 active，自动闭环` |
| allowed_actions | `active-promotion` |
| rollback_path | 回退 `domains/embedded/runbooks/asan-debug-guide.md`、`registry/items.jsonl`、相关索引、`registry/authorizations.jsonl`、`registry/promotions.jsonl` 和本 manifest。 |

## Scope

- 目标文档：`domains/embedded/runbooks/asan-debug-guide.md`
- 目标 registry item：`embedded-asan-debug-guide-20260629`
- 原 review-ready 包：`artifacts/manifests/embedded-asan-team-owner-ready-package-20260629.md`
- active promotion 证据：本文和 `artifacts/manifests/embedded-asan-active-promotion-20260629.jsonl`

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk rg -n "DEBUG=256|prog_pcr02|/customer|release/bin/prog_pcr02|libs/3rdparty/libasan" domains/embedded/runbooks/asan-debug-guide.md` | 1 | 未命中 PCR02-only 构建变量、程序名、部署路径和 libasan 项目路径。 | `domains/embedded/runbooks/asan-debug-guide.md` | Runbook | `embedded-asan-active-promotion-20260629` |
| `rtk bash tools/knowledge-regression.sh --json --suite quick --as-of 2026-06-29` | 0 | quick regression 通过，22 个 selected tests 通过，ASAN active 边界回归通过。 | `tools/knowledge-regression.sh` | Regression | `embedded-asan-active-promotion-20260629` |
| `rtk bash tools/knowledge-final-gate.sh --json --final-profile max-body --full-regression --as-of 2026-06-29` | 0 | full final gate 通过，`final_status=ok`，full regression `result_count=134`，blockers/gap_map 为空。 | `tools/knowledge-final-gate.sh` | Final gate | `embedded-asan-active-promotion-20260629` |

## 风险与后续

- 当前方法论的 active 范围是团队级调试 runbook，不是标准强制项。
- 非 PCR02 项目的 ASAN 实操记录已登记为后续证据增强项：`artifacts/manifests/embedded-asan-non-pcr02-evidence-followup-20260629.md`。当前 Hub 检索未发现真实非 PCR02 ASAN 实操验证记录，因此该 follow-up 不被写成 validation evidence，也不阻塞本次 active promotion。
- 若后续发现某个项目需要差异化参数、部署路径或运行时库布局，应新增项目本地 runbook，而不是改写团队级正文。
