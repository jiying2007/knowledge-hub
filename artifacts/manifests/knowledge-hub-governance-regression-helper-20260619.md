# Knowledge Hub governance regression helper 2026-06-19

## 结论

新增 `tools/knowledge-regression.sh` 作为轻量回归入口。它只复制当前仓库到 `/tmp`，只修改临时副本，并验证关键治理门禁不会退化。2026-06-20 起，每个临时 fixture 默认逐场景清理；低空间或内部异常会记录为结构化 failure result，并在 `--json` / final gate 路径输出 JSON，避免 final gate 只能看到空输出或残留临时目录。

## 覆盖范围

| ID | 场景 | 预期 |
|---|---|---|
| baseline-knowledge-check | 当前仓库全量 `knowledge-check` | 通过 |
| status-wrong-bucket | 临时副本把 active item 放入 `- reviewing:` | `knowledge-check` 失败并报告 wrong status bucket |
| status-noncanonical-only | 临时副本只把 item 写入非 canonical 说明行 | `knowledge-check` 失败并报告 by-status missing item |
| owner-partial-resolved | 临时副本只填 `owner_decision` 并把 worksheet 状态改为 `owner-approved` | owner gate 仍保持 open，不能 resolved |
| owner-single-form | 当前仓库按单个 `worksheet_id` 输出 owner form | 只输出 1 条 row 和 1 条 decision form |
| owner-forms-text-jsonl-output | 当前仓库按单个 `worksheet_id` 以文本模式输出 owner form | `--forms` 非 JSON 输出直接打印 1 条可复制 JSONL skeleton，包含 `worksheet_id`、`source_path`、`owner_decision` 和 `observed_source_identity` |
| owner-forms-jsonl-single-output | 当前仓库按单个 `worksheet_id` 输出纯 JSONL owner form | `--forms-jsonl` 只输出 1 行 JSONL，不包含 Markdown、包裹对象或验证提示，且不自动填 owner 决策字段 |
| owner-forms-jsonl-all-open-output | 当前仓库输出全部 open owner form 的纯 JSONL | `--forms-jsonl` 输出 7 行 JSONL，每条 open worksheet 一行，源文件身份为 match，owner 字段仍为空 |
| owner-forms-jsonl-conflict-json-mode | 当前仓库拒绝混用纯 JSONL 和包裹 JSON 输出 | `--forms-jsonl --json` 非零退出，stdout 为空，避免下游把包裹对象误当 JSONL |
| owner-checklist-context | 当前仓库按单个 `worksheet_id` 输出 owner closure checklist | checklist 合并 intake 中文问题、硬门禁和 worksheet 必填字段 |
| owner-form-context | 当前仓库按单个 `worksheet_id` 输出 owner decision form | form 自带 owner 中文问题、默认状态、允许状态和硬门禁只读上下文 |
| owner-source-identity-context | 当前 owner decision form 输出只读源文件身份提示 | form 自带当前源文件 observed sha256/size 和 match 状态，但不自动填充 owner 必填的 `source_sha256/source_size` |
| owner-summary-all-open | 当前 owner gate helper 输出全部 open gate 摘要 | `--summary` 输出 7 条 open gate、owner 分布、source identity 计数和聚焦命令，但不输出 forms/checklists |
| owner-next-open-focus | 当前 owner gate helper 自动聚焦下一条 open worksheet | `--next-open --checklist --forms` 只输出下一条 open gate 的 checklist 和 form，不需要人工复制 worksheet id |
| status-next-owner-gate | 当前状态看板输出下一条 owner gate 聚焦命令 | JSON 中存在 `owner_gates.next_open.next_open_command` 和 `focus_command`；`next_actions_zh` 使用 `--next-open --checklist --forms`，兼容字段仍指向 `pcr02-owner-decision-worksheet-001` |
| final-gate-owner-review-blocker | 当前终态 gate 聚合 check、regression 和 strict status | `knowledge-check` 与 `knowledge-regression` 必须通过；当前只因 `owner-gates-open` 返回 `needs-owner-review` |
| owner-landing-plan-project-index | 当前 landing plan 输出 owner 决策人工落地文件清单 | `required_manual_files` 包含 `indexes/by-project.md` 和 `indexes/by-status.md` |
| owner-landing-plan-requires-owner-ready-missing | 临时副本移除某条 owner-ready registry item 后生成 landing plan | owner 表单校验仍可通过，但 `landing_plan.status=blocked`，`owner_ready_gate.status=blocked`，不能输出人工落地 steps |
| owner-landing-plan-requires-owner-ready-invalid | 临时副本破坏某条 owner-ready package JSONL 后生成 landing plan | owner 表单校验仍可通过，但 `owner_ready_package_status=invalid` 会阻断 landing plan，不能输出人工落地 steps |
| owner-landing-plan-requires-owner-ready-duplicate | 临时副本复制某条 owner-ready registry item 后生成 landing plan | owner 表单校验仍可通过，但 `owner_ready_package_status=duplicate` 会阻断 landing plan，不能输出人工落地 steps |
| owner-form-source-identity-mismatch | 当前 owner 表单校验拒绝过期源文件身份 | owner 回填的 `source_sha256` 不等于当前只读观测 hash 时，`--validate-forms` 返回失败 |
| manual-entry-project-index-hint | 当前人工新增项目条目向导输出项目索引提示 | 项目域包含 `indexes/by-project.md`，非项目域不包含项目索引噪音 |
| manual-entry-project-derived-from-domain | 当前人工新增项目条目向导从 domain 推导项目名 | 未传 `--project` 时由 `projects/<project>` 推导；不一致时输出 warning |
| manual-entry-default-dates | 当前人工新增向导输出默认日期 | registry / migration 草稿填入 ISO 日期，不保留日期占位符 |
| manual-entry-owner-override | 当前人工新增向导支持 owner 覆盖 | 默认 owner 为 `leiwenjun`，传入 `--owner team-core` 时草稿使用 `team-core` |
| manual-entry-docs-owner-option | 当前 README、tools README 和 `knowledge-new.sh --help` 暴露人工新增 owner 参数 | README、tools README 与工具 help 均包含 `knowledge-new.sh` 和 `--owner`；项目示例展示从 domain 推导 project |
| regression-manifest-coverage | 当前回归 helper manifest 覆盖所有回归 ID | manifest 包含 27 个回归场景和所有当前测试 ID |

## 决策

- 不引入测试框架。
- 不写真实仓库。
- 不保存临时 fixture；默认逐场景清理，需要排查时使用 `--keep-temp`。
- 低空间预检使用 `KNOWLEDGE_REGRESSION_MIN_TMP_FREE_BYTES`，默认 4 MiB；空间不足或复制异常时先记录 failure details，`--json` 模式输出 JSON，默认模式保留人工可读文本摘要。
- 作为提交前可选回归入口，覆盖最容易造成终态漂移的 owner/status 门禁。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；27 个回归场景全部 pass，覆盖 status 负向 fixture、owner gate 负向 fixture、owner form 聚焦、owner forms 文本 JSONL 输出、owner forms 纯 JSONL 输出、owner forms 纯 JSONL 互斥保护、owner checklist、owner form 上下文、owner source identity 上下文、owner source identity 过期拒绝、owner summary、owner next-open 聚焦、status next owner gate、final gate owner blocker、owner landing plan、owner-ready missing/invalid/duplicate landing gate、manual entry 防漏、owner 文档可发现性和 regression manifest 自检 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-governance-regression-helper-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认新增 helper 和文档登记后全仓门禁通过 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-governance-regression-helper-20260619` |
| `rtk bash tools/knowledge-new.sh --kind audit --domain governance --id sample-regression --path artifacts/manifests/sample-regression.md` | 0 | 通过；人工新增向导输出短 canonical status 行示例 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-governance-regression-helper-20260619` |

## 边界

- 不修改 PCR02 源项目 docs。
- 不关闭任何 PCR02 owner gate。
- 不生成 owner decision。
- 不启用自动化，不写 memory。
- 不替代 `knowledge-check`、`knowledge-status --strict` 或 owner review。
