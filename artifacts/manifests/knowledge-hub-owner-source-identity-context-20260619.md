# Knowledge Hub owner source identity context 2026-06-19

## 结论

`tools/knowledge-owner-gates.sh --forms` 和 `--checklist` 已增加 `observed_source_identity` 只读字段。owner 人工填写表单时，可以直接看到当前源文件是否存在、当前 SHA256/size、worksheet expected SHA256/size 和 match 状态。

这个字段只用于减少人工查源文件身份的复制成本，不自动填充 `source_sha256` / `source_size`，不替 owner 签收，不关闭 owner gate。

## 问题地图

| ID | 问题 | 风险 | 处理 |
|---|---|---|---|
| OSI-001 | owner worksheet 必填 `source_sha256` 和 `source_size`，但 form 过去只给空字段。 | owner 或 AI 需要另跑 hash/size 命令，容易复制错、漏证据或引用过期 preflight。 | owner gate helper 每次只读计算当前源文件身份，并输出到 `observed_source_identity`。 |
| OSI-002 | 自动填充必填字段会被误读为 owner 已完成证据。 | 未经 owner 复核的机器观测值可能被当作签收字段。 | 保持 `source_sha256` 和 `source_size` 为空，只把观测值放到只读上下文。 |
| OSI-003 | 源文件缺失或源路径越界时需要显式可见。 | 缺失文件可能被误判为可迁移或可签收。 | `identity_status` 输出 `match`、`mismatch`、`missing`、`path-outside-source-root`、`read-error` 或 `observed-no-expected`。 |

## 决策

- 只读读取 `registry/sources.json` 中登记的 source root。
- 只计算 worksheet 中 `source_id` + `source_path` 对应的当前源文件 SHA256 和 size。
- 不写源项目 docs，不写 registry，不写 memory，不关闭 owner gate。
- `observed_source_identity` 是辅助证据提示，owner 仍必须把确认后的 `source_sha256`、`source_size`、`reviewed_by`、`reviewed_at` 和 `status_reason` 写入 owner decision landing artifact。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --next-open --forms --json` | 0 | 通过；下一条 owner form 包含 `observed_source_identity.identity_status=match`，但 `source_sha256` / `source_size` 仍为空 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-source-identity-context-20260619` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；18 个回归场景全部 pass，包含 `owner-source-identity-context` | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-source-identity-context-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认新增 manifest、registry 和 index 登记无漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-owner-source-identity-context-20260619` |

## 边界

- 不修改 PCR02 源项目 docs。
- 不关闭任何 PCR02 owner gate。
- 不生成 owner decision。
- 不自动填充 owner 必填字段。
- 不启用自动化，不写 memory。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards`。
