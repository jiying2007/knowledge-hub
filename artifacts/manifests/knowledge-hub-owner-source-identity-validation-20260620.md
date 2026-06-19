# Knowledge Hub Owner Source Identity Validation 2026-06-20

## 结论

`tools/knowledge-owner-gates.sh --validate-forms` 现在会把 owner 回填的 `source_sha256/source_size` 与当前只读观测到的源文件身份进行硬校验。owner 表单如果带着旧 hash 或旧 size，将不能进入 landing plan。

这只是在人工签收前减少漂移风险，不代表 owner 已经签收，不关闭任何 PCR02 owner gate。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| OSV-001 | owner 表单可手工填写 `source_sha256/source_size`。 | 人工可能复制旧值，导致 landing plan 基于过期源文件继续推进。 | 校验时读取 worksheet 的当前 `observed_source_identity`，要求状态为 `match`。 |
| OSV-002 | 旧 form validation 文档已经提到 source identity，但实现未硬比较 hash/size。 | 文档和工具语义不一致，长期维护时容易误判。 | 补齐 `source_sha256/source_size` 与 `observed_sha256/observed_size` 的一致性校验，并更新文档。 |
| OSV-003 | 正向 fixture 不能再使用伪 hash。 | 回归可能绕过真实源文件身份。 | landing plan 正例 fixture 改为使用当前只读观测 hash/size。 |

## 决策

- `--validate-forms` 对每个 owner form 执行 source identity 校验：
  - 当前只读观测 `identity_status` 必须为 `match`。
  - owner 回填的 `source_sha256` 必须等于 `observed_source_identity.observed_sha256`。
  - owner 回填的 `source_size` 必须等于 `observed_source_identity.observed_size`。
- `--landing-plan` 仍然只读，只在表单校验通过后输出人工落地步骤。
- 新增回归场景 `owner-form-source-identity-mismatch`，确认旧 hash 会被拒绝。

## 非目标

- 不生成 owner decision。
- 不关闭 owner gate。
- 不写 worksheet、registry、index、migration 或 memory。
- 不修改 PCR02 源项目 docs。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；20 个回归场景全部 pass，新增 `owner-form-source-identity-mismatch` 负例。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-source-identity-validation-20260620` |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --validate-forms <mismatch-fixture> --json` | 1 expected | 预期失败；`source_sha256 does not match observed source identity`。 | `/tmp/kh-regression-owner-source-identity-*` | Negative fixture | `owner-form-source-identity-mismatch` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings。 | `tools/knowledge-check.sh` | Knowledge Hub | `knowledge-hub-owner-source-identity-validation-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --explain knowledge-hub-owner-source-identity-validation-20260620` | 0 | 通过；registry item 和核心索引可解释。 | `tools/knowledge-check.sh` | Knowledge Hub | `knowledge-hub-owner-source-identity-validation-20260620` |

## Review

- owner: `leiwenjun`
- status: `reviewing`
- review_after: `2026-09-20`
- review_status: `owner-source-identity-validation-applied`
- 下一次复核内容：若 owner landing schema 引入新的 source identity 字段、source root 规则或离线源快照规则，同步 `validate-forms` 和回归 fixture。
