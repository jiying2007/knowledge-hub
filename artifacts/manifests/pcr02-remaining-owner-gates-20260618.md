# PCR02 剩余 Owner Gate 收口 - 2026-06-18

## 摘要

本 manifest 固化 PCR02 剩余 2 个 review-required 项的终态治理边界：

- `AGENTS.md`
- `standards/diag-command-metadata-standard.md`

本轮使用 2 个只读子代理并行复核。结论是：两个源文件都可以继续作为 owner-review 证据或 reference-only 候选，但现阶段不得迁移为 active 规则或 current 标准，不得覆盖 Knowledge Hub 根 `AGENTS.md`，不得提升到 `domains/embedded/standards/`。

本 manifest 不是正文迁移结果，不复制源文档正文，不修改源项目 docs，不创建 active project facts。

## Scope

- Source id: `pcr02-project-docs`
- Source root: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs`
- Baseline package: `artifacts/manifests/pcr02-owner-review-package-20260618.md`
- Follow-up package: `artifacts/manifests/pcr02-owner-review-follow-up-20260618.md`
- Owner worksheet: `artifacts/manifests/pcr02-owner-decision-worksheets-20260618.md`

| Row | Source path | Source sha256 | Size | 当前收口建议 |
| --- | --- | --- | --- | --- |
| `pcr02-owner-review-001` | `AGENTS.md` | `95ed7fa20ee52972d79038fb7ec9c5e9b8594fb35b29df50eefdcbf102130566` | `2414` | `blocked-pending-owner`，默认 reference-only，不迁 active。 |
| `pcr02-owner-review-002` | `standards/diag-command-metadata-standard.md` | `89e897bee7e3f8372a0d4c4655748fbe3476780129b157718387c1cbbb80e95d` | `5316` | `blocked-pending-owner-gate`，默认 reference-only，不迁 current/decision。 |

## 总体结论

| 条目 | registry 状态 | 默认处置 | 可升级条件 | 禁止动作 |
| --- | --- | --- | --- | --- |
| PCR02 `AGENTS.md` | `reviewing` | reference-only / owner-gated | owner 确认当前有效性、project-only scope、适用版本和 review cycle 后，才可作为 PCR02 项目本地 docs 规则。 | 不覆盖 Knowledge Hub 根 `AGENTS.md`；不成为全局 Codex 规则；不进入 `domains/embedded/standards/`。 |
| Diag command metadata standard | `reviewing` | reference-only / owner-gated | diag owner 确认 project-only source-of-truth、适用版本，并提供 gate evidence 或 owner exception 后，才可作为 PCR02 decision/current 候选。 | 不把整篇原文提升为 team standard；不把 gate command 文本当作已通过证据。 |

## `AGENTS.md` 收口边界

### Verified facts

- 源文件身份已核对：sha256 和 size 与 worksheet 一致。
- 源文件标题为“项目 Docs Agent 规则”，定位是当前项目强绑定文档入口。
- 源文件明确包含项目本地边界：
  - 项目特有内容保留在当前 `docs/`。
  - 项目工具适配层保留在当前 `tools/`。
  - 禁止把团队通用知识重新复制回当前项目仓。
  - 禁止把项目阶段性结论写成团队通用规范。
  - `plans/` 与 `reports/` 默认按历史资料维护，只有明确仍作为当前执行入口时才允许 `status: active`。
- owner-review package、follow-up 和 worksheet 均保留该 row 的 blocker：owner、scope、status、review cycle 未确认。

### Inference

- 该文件适合作为 PCR02 项目本地 docs 治理依据或 reference-only 审计材料。
- 当前缺少 owner、当前有效性、适用 branch/SDK/project phase 和 review cycle，因此不能直接进入 active 规则。
- 源文件仍引用旧团队知识库路径 `~/embedded/knowledge`；若后续迁移为 PCR02 project-local rule，owner 必须明确这是历史路径、当前有效路径，还是需要转换为 Knowledge Hub registry 引用。

### Owner gate

owner 必须补齐：

- PCR02 docs owner 或 `team-core` sign-off。
- 当前有效性声明。
- project-only scope statement。
- 适用 branch、SDK version 或 project phase。
- review cycle：`reviewed_by`、`reviewed_at`、`review_after`。
- target decision：`project-local-rule`、`reference-only` 或 `no-migration`。
- `~/embedded/knowledge` 引用的处理结论：保留历史引用、转换为 `~/knowledge-hub` 引用，或只作为源文件原文事实保留。

### Allowed targets

- `reference-only`：当前默认，只登记源文件身份和 owner gate。
- `no-migration`：owner 确认 stale、superseded 或不适合迁移。
- `domains/projects/pcr02/current/project-docs-agent-rules.md`：仅在 owner 批准 project-local rule 后创建。

### Must not

- 不覆盖 Knowledge Hub 根 `AGENTS.md`。
- 不提升到 `domains/embedded/standards`。
- 不把 PCR02 项目本地规则当作全局 Codex 规则。
- 不在 owner 未确认当前有效性、scope、版本和 review cycle 前声明 active。

## `diag-command-metadata-standard.md` 收口边界

### Verified facts

- 源文件身份已核对：sha256 和 size 与 worksheet 一致。
- 源文件定义的是 PCR02 diag command metadata、provider 生命周期、catalog/help runtime metadata 和 gate 命令。
- 源文件包含项目实现相关边界：`cmd_node`、`modules/app/src/app_diag/provider/`、`modules/common`、`diag.api.*`、`diag.hdi.*`、provider lifecycle、catalog/help runtime metadata。
- owner-review package 将 blocker 定义为 project standard risk 和 unverified gate commands。
- follow-up 明确没有新增 evidence，该 row 仍阻塞于 project-only scope、source-of-truth、applicable version、gate command evidence。

### Inference

- 当前最稳妥状态是 `reference-only pending owner-gate`。
- 该文件可以作为 PCR02 项目局部 standard/decision 候选，但不能按原文提升为团队级 standard。
- 文档中的 gate commands 只能作为建议验证命令，不能当作已通过证据。
- 若缺少 owner evidence 和实际 gate output 就迁移为 current/active，会制造错误长期事实。

### Owner gate

owner 必须补齐：

- PCR02 diag owner 或 `team-core` sign-off。
- project-only source-of-truth statement。
- 适用 branch、firmware 或 SDK version。
- provider lifecycle、command metadata、catalog/help runtime 与文档一致的证据。
- 五个 diag gate 的实际运行结果，或 documented owner exception。
- target decision：`reference-only`、`no-migration`、`pcr02-project-decision-after-owner-gate` 或 `pcr02-project-current-after-owner-gate`。

### Allowed targets

- `reference-only`：当前默认，只登记源文件身份和 owner/gate 缺口。
- `no-migration`：owner 确认 stale、mismatched 或 replaced。
- `domains/projects/pcr02/decisions/diag-command-metadata-standard.md`：仅在 owner 批准为 PCR02 project decision 后创建。
- `domains/projects/pcr02/current/diag-command-metadata-standard.md`：仅在 owner 批准为 PCR02 current project standard，且 gate evidence 或 owner exception 完整后创建。

### Must not

- 不放入 `domains/embedded/standards`。
- 不把整篇文件提升为 team standard。
- 不把 PCR02 command names、项目路径、provider lifecycle 假设泛化为跨项目默认。
- 不把 worksheet 或源文档中的 gate command 文本当作已通过证据。
- 不声明 active/current standard，除非 owner evidence 和 gate evidence 齐全。

## Verification plan

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 AGENTS"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "project docs agent rules"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 diag command metadata"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "reference-only pending owner-gate"
rtk sha256sum ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/AGENTS.md
rtk sha256sum ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/standards/diag-command-metadata-standard.md
rtk wc -c ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/AGENTS.md
rtk wc -c ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/standards/diag-command-metadata-standard.md
```

真正放行 diag current/decision 前还必须由 owner 提供源仓运行结果：

```bash
rtk python3 tools/diag/checks/check_diag_metadata.py
rtk python3 tools/diag/checks/check_diag_command_quality.py
rtk python3 tools/diag/checks/check_diag_naming.py
rtk python3 tools/diag/checks/check_diag_interface_coverage.py
rtk python3 tools/diag/checks/check_diag_layer_deps.py
```

## Non-actions

- No source project file was edited.
- No source document body was copied into `domains/`.
- No active project rule or active project standard was created.
- No Knowledge Hub root `AGENTS.md` was modified.
- No PCR02 project-specific material was promoted to `domains/embedded/standards/`.
- No automation was enabled.
- No memory was written.

## Review

- owner：`leiwenjun`
- review_after：`2026-09-17`
- validation_refs：`tools/knowledge-check.sh --dry-run`
