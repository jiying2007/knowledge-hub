# Knowledge Hub final gap readability index 2026-06-21

## 结论

本轮把 Knowledge Hub 终态 gate、中文长期资产可读性门禁和核心索引恢复锚点继续压实。

关键收口点：

- `knowledge-final-gate.sh` 不再把非 owner / 非环境 blocker 全部压成泛化 `final-gate`，而是按 diagnostics、source coverage 和 registry final-state 字段输出可执行 typed gap。
- source registry 缺项、source coverage 缺项和 source final-state 字段缺项全部进入结构化 `gap_map`，并标明是否可由 Codex 自动补齐、是否需要 owner decision、修复范围和验证命令。
- 新增 2026-06-21 起的治理 audit 中文可读性门禁：governance audit item 必须带 `summary_zh` 和语言/术语状态字段。
- 新增 2026-06-21 起的 migration 中文可读性门禁：migration row 必须带 `notes_zh`。
- `by-project` 与 `by-source` 增加最新维护锚点，避免 PCR02 / source governance 恢复时只能从长 registry 搜索。

本轮不生成 owner decision，不关闭 PCR02 owner gate，不修改 PCR02 源项目 docs / tools / knowledge / app_product_test / scratch / source tree，不复制 owner-gated source 正文，不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`，不启用自动化写操作，不写 `~/.codex/memories`。

## 变更范围

- `tools/knowledge-final-gate.sh`
  - 增加 diagnostics category 到 gap type 的稳定映射。
  - 把 `knowledge-check` 失败 blocker 暴露为 `diagnostic_categories` 与 `gap_type`。
  - 把 blocker 到 gap 的转换改为 typed path，owner、environment、regression、registry、source coverage 和 tooling 分开表达。
  - 增加 source audit gap map：Level 2 source registry 缺失、Level 2 source coverage 缺失、registered source coverage 缺失、source final-state 字段缺失。
  - source final-state 字段缺失归入既有 `registry` gap type，细分原因保留在 `gap_id/source_id/field`。
- `tools/knowledge-check.sh`
  - 对 2026-06-21 及之后新增的 governance audit item 执行中文摘要、语言状态和术语状态门禁。
  - 对 2026-06-21 及之后新增的 migration row 执行 `notes_zh` 门禁。
- `tools/knowledge-regression.sh`
  - 新增 final gate source final-state 字段缺失 typed gap 负向 fixture。
  - 新增 governance audit readability 负向 fixture。
  - 新增 migration `notes_zh` 负向 fixture。
  - 回归场景从 56 个提升到 60 个。
- `registry/schema.md`
  - 说明 2026-06-21 后 migration row 的 `notes_zh` 要求。
- `registry/migrations.jsonl`
  - 为 2026-06-21 已有 migration row 补中文说明。
- `indexes/by-project.md`
  - 为 PCR02 增加 owner target / landing validation 和 source check docs/search limit 的最新维护锚点。
- `indexes/by-source.md`
  - 为 Source Governance Recovery 和 `pcr02-project-docs` 增加最新恢复锚点。
- `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md`
  - 同步 59 个回归场景和新增门禁说明。

## Gap Type 边界

本轮把 final gate 已有的环境阻断显式补入终态目标的 gap type 词表，避免临时空间等运行环境问题被误判为知识内容缺口。新增 source/readability 细分缺口仍落入既有类型：

| 场景 | gap_type | 细分字段 |
|---|---|---|
| PCR02 Level 2 source 未登记 | `registry` | `gap_id=level2-source-missing:<source_id>` |
| PCR02 Level 2 source 未覆盖 | `source-coverage` | `gap_id=level2-source-coverage-missing:<source_id>` |
| registered source 未覆盖 | `source-coverage` | `gap_id=registered-source-coverage-missing:<source_id>` |
| source final-state 字段缺失 | `registry` | `gap_id=source-final-state-field-missing:<source_id>:<field>` |
| owner gate 未关闭 | `owner-review` | `gap_id=owner-gates-open` |
| regression 失败 | `regression` | blocker evidence |
| 环境临时空间不足 | `environment` | blocker evidence |

## 中文可读性门禁

本轮把“尽量使用中文以及可阅读性”从规则文档推进到可验证门禁：

- 新增或更新日期在 2026-06-21 及之后的 governance audit registry item 必须包含：
  - `summary_zh`
  - `primary_language`
  - `source_language`
  - `translation_status`
  - `terminology_status`
- 新增或更新日期在 2026-06-21 及之后的 migration row 必须包含：
  - `notes_zh`

该门禁只约束治理 audit 和 migration 记录，不强行改写历史行，也不要求命令、路径、协议字段、API 名称和必要英文原文翻译成中文。

## Owner Gate 状态

- PCR02 owner-ready package 仍为 7/7。
- 当前未提供有效 owner decision JSONL。
- 7 个 PCR02 owner gate 仍然 open。
- 终态 gate 允许停在 `needs-owner-review`，但只能因为 owner gates open。
- 本轮所有新增 gap/readability/index 工作都属于 Codex 可完成的自动治理面，不代替 owner review。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-final-gate.sh` | 0 | 通过；final gate shell wrapper 语法有效。 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-final-gap-readability-index-20260621` |
| `rtk bash -n tools/knowledge-check.sh` | 0 | 通过；knowledge-check shell wrapper 语法有效。 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-final-gap-readability-index-20260621` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；regression shell wrapper 语法有效。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-final-gap-readability-index-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；新增中文可读性门禁、registry、migration 和 index 登记后全仓无 errors / warnings。 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-final-gap-readability-index-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json` | 0 | 通过；60 个回归场景全部 pass，包含 typed registry gap、final gap/readability 正向契约、governance audit readability gate 和 migration notes_zh gate。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-final-gap-readability-index-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json` | 1 | 通过预期阻断；`final_status=needs-owner-review`，自动治理面完成，剩余 blocker 为 7 个 PCR02 owner gates。 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-final-gap-readability-index-20260621` |
| `rtk git diff --check` | 0 | 通过；无 whitespace error。 | git diff | Git | `knowledge-hub-final-gap-readability-index-20260621` |

## 边界

- 不修改 PCR02 源项目。
- 不复制 owner-gated source 正文。
- 不生成或伪造 owner decision。
- 不关闭任何 owner gate。
- 不把 PCR02 project-specific 内容提升为团队标准。
- 不启用自动化写操作。
- 不写 `~/.codex/memories`。
