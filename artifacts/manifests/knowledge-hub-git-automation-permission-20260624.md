# Knowledge Hub Git 自动化权限优化 2026-06-24

## 摘要

本次将 Knowledge Hub 的默认 AI / Codex 权限从“多数写入需要人工确认”调整为“Git 可回滚边界内默认自动维护，高风险外部副作用仍需授权”。

新的权限边界：

- L1/L2 Hub 本仓维护默认允许：Markdown、registry、index、manifest、template、tools、Hub 内文件移动和整理。
- 门禁全绿后允许创建本地 commit。
- 本地 commit 只代表可审计快照，不代表发布、owner approval、active promotion、memory write、source project write 或 remote publish。
- push、merge、release、tag、owner decision、active promotion、memory write、源项目写入、删除外部资料和非 report-only 自动化仍必须有 `registry/authorizations.jsonl` 授权记录。

## 变更范围

- 更新 `AGENTS.md`、`README.md`、`docs/goals/knowledge-hub-simplified-final-version.md` 的权限模型。
- 更新 `registry/schema.md`，新增 `remote-git-write` 授权动作和 `local-commit` 自动化模式。
- 更新 `tools/knowledge-check.sh`、`tools/knowledge-final-gate.sh`、`tools/README.md`、`tools/knowledge-regression.sh` 的门禁、文案和回归契约。
- 补充 registry、migration 和核心索引记录。

## 边界

- 本次未 push、merge、release、tag 或改变远端 Git 状态。
- 本次未写 `~/.codex/memories`。
- 本次未修改源项目。
- 本次未新增 owner decision。
- 本次未把任何条目提升为 active。
- 本次未执行非 report-only 自动化。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | `status=pass`，errors=0，warnings=0；验证 registry、index、schema、manifest 和治理门禁通过。 | runtime:knowledge-check | Governance | `knowledge-hub-git-automation-permission-20260624` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-24` | 0 | `status=pass`，result_count=120；验证 `local-commit`、授权动作和文档锚点回归契约通过。 | runtime:knowledge-regression | Governance | `knowledge-hub-git-automation-permission-20260624` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 0 | `final_status=ok`；proof artifacts 覆盖 22/22，maintenance entry audit 9/9，linking audit pass。 | runtime:knowledge-final-gate | Governance | `knowledge-hub-git-automation-permission-20260624` |
