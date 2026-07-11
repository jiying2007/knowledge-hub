# Codex WeChat absorption final handoff coverage 2026-07-10

## Scope

本记录从旧 Codex archive `session-wrap/20260523-135801-wechat-all-cleared-handoff.md` 迁移 WeChat article absorption final handoff 的 coverage 数字、验证状态、风险和方法边界。本文是 coverage audit，不是 current rule、owner decision、memory、source-to-live apply 或 active promotion。

## 方法边界

旧源记录的 method-only absorption 边界：

- 不导入文章原文、外部 repo、安装命令、MCP server、plugin manifest、hook、cloud/bot setup、SDK snippet、provider config、marketplace claim、model ranking、benchmark claim 或平台 API 语义。
- 优先 `MERGE` 到既有 ADK runbook、skill 和 template。
- Generic Skill/MCP/market/news 默认 `REFERENCE_ONLY` 或 `REJECT`，除非增加 durable gate。

## Coverage 数字

- P0：9 份 evidence report，`p0-001` 到 `p0-009`；旧源未给 P0 item 总数，本文不补造。
- P1：处理 `21` 项，`MERGE 11`、`REFERENCE_ONLY 8`、`REJECT 2`。
- P2 external-code：处理 `48` 个高风险 external-code candidates，`MERGE 3`、`REFERENCE_ONLY 19`、`REJECT 26`。
- P2 reference-only：处理剩余 `119` 个 P2 reference-only items，使用 4 个只读 subagent shards，`MERGE 2`、`REFERENCE_ONLY 69`、`REJECT 48`。
- Ledger：`reports/wechat-article-intake.jsonl` 为 `313 rows`；`reports/wechat-article-decisions.tsv` 为 `314 lines including header`。
- Pending：`pending-triage`、`pending-security-review`、`reference-only-pending` 均为 `0`。
- `reports/wechat-absorb-next-batch.md` 无 next batch candidates。

## 吸收的 durable gates

旧源记录的长期方法结论包括：

- 写工具不得接受无界 selector。
- bulk writes 需要 dry-run、`affected_count`、scope summary、max limit、rollback/audit fields 和显式批准。
- 高风险工具/API 需要结构化返回 `approval_required`。
- 文件写入或 patch 成功需要 postcondition evidence，如 diff、hash、summary 和 deny-path tests。

这些只作为历史吸收闭环与候选规则记录，不自动提升为 active ADK 规则。

## 验证状态

旧源记录的通过项：

- `scripts/check-wechat-intake-ledger.sh .`：PASS，`articles=313`
- `agent-dev-kit/scripts/check-token-budget.sh`：PASS
- `scripts/check-skill-routing-conflicts.sh .`：PASS
- `agent-dev-kit/scripts/validate-assets.sh --strict`：PASS
- `agent-dev-kit/scripts/check-memory-governance.sh`：PASS
- `agent-dev-kit/tests/run_all.sh`：PASS，`37/37`
- `scripts/check-doc-sync.sh .`：PASS
- root 与 `agent-dev-kit` 的 `git diff --check`：PASS

旧源记录的未通过项：

- `scripts/evidence-bundle.sh . --format markdown --max-summary-chars 2000`：NEEDS-FIX
- `scripts/check-all.sh --quick`：NEEDS-FIX，`26/28` passed
- `final-ready.sh` command record PASS，但 Session Coach CRITICAL

## 未决风险

- 未 commit/push。
- 未写 formal memory。
- 未执行 source-to-live apply 到 `~/.codex`。
- ADK changes targeted validation 已过，但 root workspace 和 `agent-dev-kit` subrepo 当时仍未提交。
- `check-evidence-bundle.sh` 与 `check-subrepo-state.sh` 因 dirty subrepo 失败：`dirty=21`、`known_dirty=20`、`unexpected_dirty=1`。
- 外部 repo、安装流、plugin、MCP server implementation、hook、cloud/bot setup、SDK snippets、model claims、benchmarks、marketplace content 均未验证且有意未导入。

## Source identity

- Source: `domains/codex/archive/codex-archive/session-wrap/20260523-135801-wechat-all-cleared-handoff.md`
- Source SHA256: `01e93739e354812d4d3a9938b6eb1340ed367a94679b97c146e991bb78985888`
- Source size: `11414` bytes
- Preflight row: `CAEF-20260710-027`
- Tombstone: `CARE-20260710-035`

## Decision

旧正文可在本 coverage audit、registry、index、tombstone 和授权账本落地后删除。删除前必须将早前 4 个 WeChat 中间 handoff tombstone 的最终覆盖入口改指向本 coverage audit，避免 final anchor 丢失。
