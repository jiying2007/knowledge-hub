# Codex OpenAI 本地运行边界历史归档 2026-05-24

## 摘要

本记录从旧 Codex archive 抽取 2026-05-24 的 OpenAI local runtime boundary 会话结论，作为 `archive-only` / `freshness-required` 治理证据。

它只证明当时曾围绕 OpenAI 官方资料、本地 Codex runtime、Docs MCP、permissions、rules、hooks、automations 和 source-to-live 健康链路做过一次治理吸收；不证明这些 OpenAI/Codex 官方资料在 2026-07-10 仍然有效，也不把旧会话判断提升为当前 active rule。

结构化台账：`artifacts/manifests/codex-openai-local-runtime-boundary-20260524.jsonl`。

## 来源

- source_path: `domains/codex/archive/codex-archive/session-wrap/20260524-231443-codex-session-wrap-20260524-openai-local-runtime-boundary.md`
- source_sha256: `b731c2ab6e95835b0c38c37241ebda5c5c8e903568a51f6ca49c274a91f82a79`
- source_date: `2026-05-24`
- migrated_at: `2026-07-10`
- source_type: sanitized session-wrap
- current_fact_policy: `historical-governance-boundary-only; official/current claims require freshness review`

## 归档边界

- 本记录不复制 raw session、完整日志、cache、runtime state、cookie、private key、binary 或未脱敏材料。
- 本记录不写 Codex memory，不生成 owner decision，不关闭 owner gate，不提升 active，不修改 Codex live source。
- OpenAI/Codex 官方资料、产品能力、配置字段、MCP 启用状态和运行态验证结果均标记为 `freshness-required` 或 `historical`。
- 旧 archive 正文仍未删除；删除必须另有授权、tombstone、rollback 和验证批次。

## 可迁移的长期治理事实

以下内容可作为本地 Codex 治理原则的历史来源支撑，但仍需结合当前 `codex-live` 资产和官方 freshness gate 后才能提升为当前规则：

- OpenAI 官方资料进入本地治理前，应有 source URL、`retrieved_at`、`review_status`、`expires_at`、rollback 和治理 eval 证据。
- 官方指导不应直接扩写 `AGENTS.md`；应先落到小型 manifest、contract、eval 或 workflow recipe，再经验证后提升。
- permissions、command rules 和 hook contract 需要负向测试，否则容易停留在不可执行的 policy prose。
- hook contract 不能被当作完整 enforcement boundary；未覆盖行为、runner 缺失和回退方式必须显式声明。
- 自动化候选默认 disabled 或 report-only；不能默认扩大写入、发布、发送或外部集成能力。
- OpenAI Docs / 文档查询类 MCP 的本地治理边界应保持只读，不上传私有代码、secret 或未脱敏日志。
- 本地 runtime boundary 变更不得放宽 sandbox、network 或 approval 默认值；如需变更，必须有 strict-config doctor、rollback 和验证证据。
- source-to-live 健康检查应覆盖 build、doctor、plan/dry-run、apply、diff/drift、check 和 final-ready 等链路。

## Historical / Freshness-Required

| 旧 source 内容 | 当前处理 |
| --- | --- |
| 当时 reviewed OpenAI official Developers sources | `freshness-required`；只能证明 2026-05-24 做过吸收。 |
| Codex permissions、rules、hooks、automations、app commands、tools、conversation state、Codex safety 等官方指导 | `freshness-required`；不能从旧 source 声明为当前官方事实。 |
| `sandbox_mode` 与 `default_permissions` 的关系 | `freshness-required`；配置字段和推荐实践必须按当前官方资料复核。 |
| `openaiDeveloperDocs` enabled、其他 MCP disabled | `historical`；只是 2026-05-24 本地运行态状态。 |
| 35 tests OK、doctor/check/final-ready pass | `historical evidence`；仅代表当次提交验证。 |
| commit `dd0ba05` 与 pushed to `origin/main` | `historical provenance`；不代表当前远端状态。 |
| branch、remote sync、worktree clean | `historical`；迁移价值低，不作为当前状态。 |

## 当前覆盖关系

本批未执行 OpenAI 官方资料 freshness review，也未修改 Codex live source。只读核查显示，当前 `codex-live` 已有相近治理资产，可作为后续复核入口：

- `codex-live:AGENTS.md`
- `codex-live:docs/codex-asset-management.md`
- `codex-live:docs/codex-cli-config-guide.md`
- `codex-live:docs/codex-operating-model.md`
- `codex-live:docs/design.md`
- `codex-live:manifests/official_docs_freshness_gates.json`
- `codex-live:manifests/permission_profiles.json`
- `codex-live:manifests/exec_rules.json`
- `codex-live:manifests/hook_contracts.json`
- `codex-live:manifests/mcp_servers.json`

这些覆盖说明旧 source 的部分治理意图已进入 Codex live 资产链路，但本记录不重新验证其官方 freshness、运行态启用状态或当前规则有效性。

## 删除前门禁

旧 source 进入删除批次前必须满足：

1. 本记录或后续 canonical 记录保留 `source_path`、`source_sha256`、source 日期、迁移边界和替代路径。
2. 存在覆盖本 source 的有效 `delete-or-prune` 授权。
3. 独立删除执行 manifest 列出 source hash、covered_by、tombstone_as、rollback 和验证命令。
4. 不存在 raw session、secret、cookie、cache、完整日志或 binary 正文风险。
5. `delete_ready=true` 由删除执行批次显式设置；本记录不设置删除就绪。
6. 如后续要把内容提升到 `domains/codex/workflows/` 或 Codex live source，必须完成官方资料 freshness gate、owner review、source-to-live 验证和 rollback 证据。

## 验证计划

```bash
rtk jq -c . artifacts/manifests/codex-openai-local-runtime-boundary-20260524.jsonl
rtk rg -n "(?i)(password|token|cookie|private[_ -]?key|secret)\\s*[:=]" artifacts/manifests/codex-openai-local-runtime-boundary-20260524.md artifacts/manifests/codex-openai-local-runtime-boundary-20260524.jsonl
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "OpenAI local runtime boundary"
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
```
