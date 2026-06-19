# Knowledge Hub regression manifest coverage 2026-06-19

## 结论

`tools/knowledge-regression.sh` 已增加 `regression-manifest-coverage` 自检场景，用于防止回归脚本扩展后 `knowledge-hub-governance-regression-helper-20260619.md` 滞后。

当前 regression helper manifest 已同步到 20 个回归场景，并列出所有当前测试 ID。

## 问题地图

| ID | 问题 | 风险 | 处理 |
|---|---|---|---|
| RMC-001 | `knowledge-regression.sh` 已扩展到 20 个场景，但 regression helper manifest 曾滞后。 | 长期审计会误判回归覆盖范围，后续维护者不知道实际检查了什么。 | 同步 regression helper manifest 到 20 个场景。 |
| RMC-002 | 文档同步依赖人工记忆。 | 下次新增回归后可能再次漏改 manifest。 | 新增 `regression-manifest-coverage` 自检场景，要求 manifest 覆盖当前测试 ID 和场景数量。 |

## 决策

- `regression-manifest-coverage` 不复制仓库、不改临时 fixture，只读检查 manifest 文本。
- 当前用显式测试 ID 列表固定覆盖边界；新增回归场景时必须同步该列表和 manifest。
- 不引入测试框架，不生成自动文档。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；20 个回归场景全部 pass，包含 `owner-checklist-context`、`owner-form-context`、`owner-source-identity-context`、`owner-form-source-identity-mismatch`、`owner-summary-all-open`、`owner-next-open-focus`、`final-gate-owner-review-blocker`、`manual-entry-docs-owner-option` 和 `regression-manifest-coverage` 场景 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-regression-manifest-coverage-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认 manifest、registry 和 index 登记无漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-regression-manifest-coverage-20260619` |

## 边界

- 不修改 PCR02 源项目 docs。
- 不关闭 owner gate，不生成 owner decision。
- 不启用自动化，不写 memory。
- 不替代 `knowledge-check` 或 owner review。
