# Knowledge Hub manual entry owner、personal 与 source 推荐加固 2026-06-23

## 结论

本轮把人工新增入口继续压实为更低错误率的中文维护路径。

- `knowledge-new.sh` 普通 item mode 现在会输出 `owner_registry_status`；未知 item owner 只给 warning，不伪造 owner，也不替代 owner registry。
- `knowledge-new.sh` 会对 `--domain personal` 或 `domains/personal/` 路径使用 personal-local 安全默认值：`visibility=personal-local`、`status=personal`、`scope=team-general`。显式 domain/path 冲突时会提示不可直接落盘。
- `knowledge-new.sh --source` 现在按 `role`、`write_policy` 和 check/no-check 状态输出 `recommended_final_disposition`、`recommended_source_strategy` 与中文理由。
- source 可复制 JSON 仍保守保持 `final_disposition=owner-gated-pending-decision`，推荐提示不替代 owner decision，不关闭 owner gate。
- README、tools README、templates README、knowledge-check manual-entry 锚点和 regression helper manifest 已同步新契约。

## 证据

| 命令 | 结果 | 摘要 |
|---|---|---|
| `rtk bash -n tools/knowledge-new.sh` | pass | 人工新增向导脚本语法通过。 |
| `rtk bash -n tools/knowledge-check.sh` | pass | 新增 manual-entry 锚点后检查脚本语法通过。 |
| `rtk bash -n tools/knowledge-regression.sh` | pass | 新增 regression 场景后回归脚本语法通过。 |
| `rtk bash tools/knowledge-new.sh --kind personal-note --domain personal --id personal-defaults --path domains/personal/defaults.md` | pass | personal 草稿输出 `personal-local`、`status=personal` 和 `- personal:` 索引草稿。 |
| `rtk bash tools/knowledge-new.sh --kind decision --domain governance --owner unknown-item-owner --id governance-owner-warning --path governance/owner-warning.md` | pass | 未登记 item owner 输出 warning，但 JSON 草稿保留原 owner，不伪造责任人。 |
| `rtk bash tools/knowledge-new.sh --source --source-id example-agent-config-source --source-path /tmp/example-agent-config --role project-agent-config-source --authority legacy-project-agent-config --write-policy do-not-write-through-knowledge-hub --check "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run"` | pass | source 向导推荐 `artifact-ref-registered`，但 copyable JSON 保持 `owner-gated-pending-decision`。 |
| `rtk bash tools/knowledge-new.sh --source --source-id example-current-no-check-source --source-path /tmp/example-current-no-check --role project-current-docs-source --authority legacy-project-current-docs --write-policy read-only-unless-explicitly-approved --no-check-reason "classify-first pending source coverage"` | pass | 无稳定 check 的 current source 推荐保持 owner-gated，并说明需先补 coverage/source identity/no-check evidence。 |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-23` | pass | 新增 manual-entry 锚点后全仓一致性通过，errors=0，warnings=0。 |

## 边界

- 不生成 owner decision。
- 不填写 `reviewed_by`、`reviewed_at` 或 owner 签收字段。
- 不关闭 owner gate。
- 不修改 PCR02 源项目 docs、tools、knowledge、app_product_test、scratch 或 source tree。
- 不复制 owner-gated source 正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用非 report-only 自动化。
- 不写 `~/.codex/memories`。

## 剩余状态

本轮只降低人工新增和新增 source 的误填风险。终态 gate 的预期剩余 blocker 仍是 7 个 `pcr02-project-docs` owner gate；这些 gate 需要真实 owner decision，不能由 Codex 自动关闭。
