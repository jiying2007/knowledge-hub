# Knowledge Hub 维护入口与关联恢复审计加固 2026-06-22

## 结论

本轮继续压实终态自动治理证据面，新增两个可机器判定的审计面：

- `maintenance_entry_audit`：在 `knowledge-final-gate.sh --json` 中显式证明终态目标第七节的 8 类长期维护入口均可恢复，覆盖人工新增知识、source coverage、人工复核、人工检索、owner 签收、自动化边界、质量门禁和中文可读性。
- `linking_audit`：在 `knowledge-index-plan.sh --section linking --json` 中复用 `by-project`、`by-source`、`by-topic`、`by-decision` 和 Markdown index 锚点，证明跨会话、项目、source、topic、decision 的恢复链路存在；`knowledge-final-gate.sh --json` 会把该审计提升为顶层证据。

这两个审计只证明入口和恢复链路存在，不证明人工动作已完成，不替 owner 做签收。

## 边界

- 不生成 owner decision。
- 不代填 `reviewed_by`，不关闭 PCR02 7 个 owner gate。
- 不修改 PCR02 源项目 docs、tools、knowledge、app_product_test、scratch 或 source tree。
- 不读取 PCR02 源项目正文，不复制 owner-gated source 正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化写操作，不写 `~/.codex/memories`。
- `maintenance_entry_audit` 的 `pass` 只代表入口存在、边界清楚且可恢复；不代表某条知识、source 或 owner decision 已由人工处理完成。
- `linking_audit` 的 `pass` 只代表 registry/index/search 恢复链路存在；不代表 owner decision 已签收。

## 变更明细

| 区域 | 文件 | 变更 |
|---|---|---|
| index plan | `tools/knowledge-index-plan.sh` | 新增 `--section linking` 和 `linking_audit`，检查 registry 派生视图与 Markdown index 锚点 |
| final gate | `tools/knowledge-final-gate.sh` | 新增顶层 `maintenance_entry_audit` 与 `linking_audit`，失败时进入非 owner `needs-fix` |
| regression | `tools/knowledge-regression.sh` | 扩展 final gate owner-review blocker 与 index plan extended sections 的契约断言 |
| docs | `README.md`、`tools/README.md` | 同步新增审计字段、恢复链路和只读边界说明 |
| governance | 本 manifest、registry、migration、核心索引 | 登记本次工具契约变更和验证证据 |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-index-plan.sh` | 0 | shell 语法通过 | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-maintenance-linking-audit-hardening-20260622` |
| `rtk bash -n tools/knowledge-final-gate.sh` | 0 | shell 语法通过 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-maintenance-linking-audit-hardening-20260622` |
| `rtk bash tools/knowledge-index-plan.sh --section linking --json` | 0 | `linking_audit.status=pass`，跨会话、项目、source、topic、decision 和 Markdown index 恢复链路均通过 | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-maintenance-linking-audit-hardening-20260622` |
| `KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22` | 1 | 自测模式预期返回 `needs-owner-review`；`maintenance_entry_audit.status=pass`、`linking_audit.status=pass`，唯一 gap 为 `owner-gates-open` | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-maintenance-linking-audit-hardening-20260622` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-22` | 0 | 回归通过，包含新增审计字段与 linking section 契约 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-maintenance-linking-audit-hardening-20260622` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-22` | 0 | 全仓知识门禁通过，0 errors | `tools/knowledge-check.sh` | Tool | `knowledge-hub-maintenance-linking-audit-hardening-20260622` |
| `rtk git diff --check` | 0 | 当前 diff 无空白错误 | `git diff --check` | Tool | `knowledge-hub-maintenance-linking-audit-hardening-20260622` |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22` | 1 | 预期停在 `needs-owner-review`；自动治理为 `complete-except-owner-review`，唯一 blocker 为 7 个 owner gate | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-maintenance-linking-audit-hardening-20260622` |

## 后续人工动作

- 真实 owner 仍需按 `knowledge-owner-gates.sh` 的 owner inbox / forms-jsonl / validate / landing-plan / landing-audit 路径处理 7 个 open gate。
- 后续若修改第七节长期维护入口或核心索引恢复结构，需要同步更新 `maintenance_entry_audit` / `linking_audit` 的锚点和回归断言。
- `linking_audit` 不应直接调用无约束 `knowledge-search.sh` 扫描外部 source；搜索恢复证据继续通过 regression contract 或限定 `--source knowledge-hub` 的人工命令验证。
