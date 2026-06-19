# Knowledge Hub Source Coverage Closeout 2026-06-19

## 目标

把 `registry/sources.json` 中 6 个已登记 source 的治理状态收口到控制面，明确哪些已经完成迁移覆盖、哪些只能引用、哪些保持 owner-gated 或 auxiliary-only，避免后续把外部来源误当成已迁移正文或 active fact。

## 覆盖矩阵

| Source | 当前状态 | 终态分类 | 控制面结论 |
| --- | --- | --- | --- |
| `pcr02-project-docs` | 32/32 文件已有 copy-first、reference-first、artifact-ref 或 owner-gated coverage。 | mixed governance coverage | 控制面闭合；7 个 owner-gated 文件仍不能 active promotion。 |
| `engineering-archive` | 38 个历史工程归档文本已 copy-first 到 PCR02 archive。 | copy-first archive-only | 迁移闭合；单文件提升需新增 owner review。 |
| `patent-disclosure` | 10 个 Markdown 已 copy-first，181 个非文本附件已 artifact-ref。 | copy-first + artifact-ref | 覆盖闭合；专利语义仍需 owner/legal review。 |
| `embedded-knowledge` | 作为 legacy team SSOT 登记，inventory 时源仓 dirty=7。 | owner-review-gated reference-first candidate | 不做批量迁移；跨项目标准提升必须先稳定 source、owner review、拆分 project-specific 内容。 |
| `codex-archive` | 作为 Codex workflow history 登记，要求通过 archive tools 使用。 | reference-first | 不 duplicate wholesale；通过 `domains/codex/archive/codex-archive.ref.md` 登记引用边界。 |
| `codex-memories` | 作为 auxiliary recall-only 登记。 | auxiliary-only no-memory-write | 不迁移、不作为事实唯一来源、不自动写 memory；提升只能走 memory curator 候选和 owner review。 |

## 决策

- Knowledge Hub 不再追求把所有 registered source 正文复制一遍；终态可以是 copy-first、reference-first、artifact-ref、owner-gated 或 auxiliary-only。
- `embedded-knowledge` 暂不迁移正文。原因是 source inventory 记录源仓存在 dirty 状态，且它是 legacy team SSOT；任何标准提升必须走 owner review 和边界拆分。
- `codex-archive` 采用 reference-first，长期访问通过 Codex archive tools 与 `archive-check.sh`，不复制历史归档正文。
- `codex-memories` 只作为辅助召回；不能成为规则、事实或 active index 的唯一依据。
- 本 closeout 只关闭 source coverage 控制面，不关闭 PCR02 7 个 owner-gated 语义决策。

## 非目标

- 不修改任何 source 目录。
- 不写入 `~/.codex/memories`。
- 不复制 `codex-archive` 或 `embedded-knowledge` 正文。
- 不把 `embedded-knowledge` 或 PCR02 project-specific 内容直接提升到 `domains/embedded/standards/`。
- 不启用自动化。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk sed -n '1,260p' registry/sources.json` | 0 | 复核 6 个 registered source 的 role、authority、write_policy 和 check。 | `registry/sources.json` | Knowledge Hub | source coverage |
| `rtk sed -n '1,240p' artifacts/manifests/source-inventory-20260616.md` | 0 | 复核 source inventory baseline、risk notes 和 priority plan。 | `artifacts/manifests/source-inventory-20260616.md` | Knowledge Hub | source inventory |
| `rtk rg -n "embedded-knowledge|codex-archive|codex-memories|source-index|memory auto" artifacts/manifests indexes registry README.md governance -g '*.md' -g '*.jsonl' -g '*.json'` | 0 | 复核 existing control-plane references 与 no-memory-write 边界。 | `artifacts/manifests`、`indexes`、`registry` | Knowledge Hub | source coverage |
| `subagent: source-coverage-review` | 0 | 只读复核 6 个 source 覆盖状态；确认 PCR02、engineering、patent 覆盖闭合，embedded/codex/memories 保持外部或辅助边界。 | 本会话子代理回执 | Subagent | source coverage |
| `subagent: codex-memory-boundary-review` | 0 | 只读复核 codex-archive reference-first 与 codex-memories auxiliary/no-memory-write 边界。 | 本会话子代理回执 | Subagent | codex/memory boundary |

## 后续边界

- `embedded-knowledge`：owner 决策前只保持外部 SSOT 引用；任何 team standard 提升必须新增拆分证据、review_status、promotion_decision 和 rollback。
- `codex-archive`：如果某条历史归档要提升为 active governance，必须新建独立 manifest，不得直接把历史记录当规则。
- `codex-memories`：只允许进入候选治理报告，不直接写 memory、不自动推广 active fact。
- `pcr02-project-docs`：7 个 owner-gated 文件仍按 owner action board 单独解决。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- validation_refs：`tools/knowledge-check.sh --dry-run --json --diagnostics`
