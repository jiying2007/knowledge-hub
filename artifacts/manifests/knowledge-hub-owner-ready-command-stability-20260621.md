# Knowledge Hub owner-ready command stability 2026-06-21

## 结论

本轮把 PCR02 owner-ready 签收包和 Knowledge Hub 运行时状态面板中的人工可复制命令统一为 cwd-stable 入口：`rtk bash ~/knowledge-hub/tools/...`。

这次变更只修正命令可复制性和回归门禁，不生成 owner decision，不关闭 PCR02 owner gate，不修改 PCR02 源项目 docs，不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`，不启用自动化，不写 `~/.codex/memories`。

## 变更范围

- 7 个 PCR02 owner-ready package Markdown 的 `knowledge-owner-gates` 命令改为 `~/knowledge-hub/tools` 入口。
- 7 个 PCR02 owner-ready package JSONL 的 `evidence_refs` 命令改为 `~/knowledge-hub/tools` 入口。
- `tools/knowledge-owner-gates.sh` 增加 owner-ready package 强校验：
  - `package_markdown_commands_cwd_stable`
  - `package_evidence_refs_cwd_stable`
- `tools/knowledge-status.sh` 的 owner summary、forms-jsonl、validate-forms、landing-plan、next-open、review_after 和 final gate 命令改为 cwd-stable 展示入口。
- `tools/knowledge-final-gate.sh` 的人工复核命令改为 cwd-stable 展示入口。
- `tools/knowledge-regression.sh` 新增 repo-relative owner-ready command 负向 fixture，总回归场景从 55 个提升到 56 个。

## Owner Gate 状态

- `pcr02-project-docs` owner-ready coverage：7/7。
- `owner_ready_missing_count`：0。
- `owner_ready_invalid_count`：0。
- `owner_ready_duplicate_count`：0。
- `open_owner_gate_count`：7。
- 当前仍只允许 owner 人工签收后再生成 landing plan；本轮不代替 owner review。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json` | 0 | 通过；状态面板输出 `needs-owner-review`，owner-ready coverage 为 7/7，所有 owner 分派、forms-jsonl、validate-forms、landing-plan、next-open、review_after 和 final gate 命令均使用 `~/knowledge-hub/tools` 展示入口。 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-owner-ready-command-stability-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary --json` | 0 | 通过；7 个 owner-ready package 均为 valid，新增 `package_markdown_commands_cwd_stable` 与 `package_evidence_refs_cwd_stable` 覆盖检查均为 true。 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-ready-command-stability-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json` | 0 | 通过；56 个回归场景全部 pass，其中新增 `owner-landing-plan-requires-owner-ready-repo-relative-command` 阻断 repo-relative owner-ready 命令。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-ready-command-stability-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings。 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-owner-ready-command-stability-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json` | 1 | 通过预期阻断；`final_status=needs-owner-review`，`automatic_governance.status=complete-except-owner-review`，`knowledge_check=pass`，`knowledge_regression=pass`，`git_diff_check=pass`，唯一终态 blocker 为 7 个 owner gates。 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-owner-ready-command-stability-20260621` |

## 边界

- 不改 PCR02 源项目。
- 不复制 owner-gated source 正文。
- 不写 owner decision 表单。
- 不把 project-specific 内容提升为团队标准。
- 不启用自动化或 memory 写入。
- 其它工具 README / helper 中的历史 repo-relative 示例不在本轮全部重写；本轮只固定 owner-ready package、owner gate/status/final gate 的终态人工路径。
