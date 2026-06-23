# Knowledge Hub governance regression helper 2026-06-19

## 结论

新增 `tools/knowledge-regression.sh` 作为轻量回归入口。它只复制当前仓库到 `/tmp`，只修改临时副本，并验证关键治理门禁不会退化。2026-06-20 起，每个临时 fixture 默认逐场景清理；低空间或内部异常会记录为结构化 failure result，并在 `--json` / final gate 路径输出 JSON，避免 final gate 只能看到空输出或残留临时目录。

## 覆盖范围

| ID | 场景 | 预期 |
|---|---|---|
| baseline-knowledge-check | 当前仓库全量 `knowledge-check` | 通过 |
| governance-goal-path-allowed | 当前终态目标规格作为 governance item 可解释 | `docs/goals/knowledge-hub-final-state.md` 可由 `knowledge-check --explain` 解释，避免目标 SSOT 路径漂移 |
| pcr02-level2-source-coverage | PCR02 Level 2 source 同时完成 registry、by-source 和 latest coverage JSONL 覆盖 | 7 个 Level 2 source 均出现在 `registry/sources.json`、`indexes/by-source.md` 和 `knowledge-hub-source-coverage-closeout-20260620.jsonl` |
| pcr02-level2-boundary-manifests | PCR02 Level 2 source 具备具体边界 manifest | 7 个 PCR02 Level 2 source 均有 Markdown/JSONL 边界清单、registry item、by-source 和 by-project 索引 |
| boundary-health-internal-evidence | 当前 `knowledge-check` 输出 PCR02 Level 2 boundary 内部证据健康面 | `boundary_health.status=pass`，7 组 boundary manifest、registry item、source coverage、by-source 和 by-project 引用齐全；负向 fixture 篡改 source_id 时必须失败 |
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
| owner-prefill-candidates-manual-fields | 当前 owner decision form 输出只读预填候选 | `read_only_prefill_candidates` 给出 source hash/size、review_after 和 evidence ref 候选，但正式 owner 字段仍为空，不能替代签收 |
| owner-evidence-readiness | 当前 owner gate helper 输出证据准备度视图 | `--evidence-readiness --json` 汇总字段 readiness、owner-ready evidence ref、safe/project command candidates，不写文件、不关闭 gate |
| owner-inbox-contract | 当前 owner gate helper 输出单屏 owner inbox | `--owner-inbox --json` 按 owner/worksheet 汇总路由、中文问题、字段分组、只读候选、owner-ready package 和 validate/landing 命令模板，不生成 owner decision、不关闭 gate |
| owner-summary-all-open | 当前 owner gate helper 输出全部 open gate 摘要 | `--summary` 输出 7 条 open gate、owner 分布、owner_dispatch 分派包、source identity 计数和聚焦命令，但不输出 forms/checklists |
| owner-summary-by-owner | 当前 owner gate helper 按 owner 输出 open gate 摘要 | `--owner project-owner --summary` 只输出 project-owner 名下 2 条 open gate，并保留该 owner 的只读 forms-jsonl、validate、landing-plan 和 next focus 分派命令 |
| owner-next-open-focus | 当前 owner gate helper 自动聚焦下一条 open worksheet | `--next-open --checklist --forms` 只输出下一条 open gate 的 checklist 和 form，不需要人工复制 worksheet id |
| status-next-owner-gate | 当前状态看板输出下一条 owner gate 聚焦命令 | JSON 中存在 `owner_gates.owner_dispatch[]`、`owner_gates.next_open.next_open_command`、`focus_command` 和 evidence-readiness 命令；`next_actions_zh` 使用 `owner_gates.owner_dispatch[]`、`--next-open --checklist --forms` 与 `--evidence-readiness --json`，兼容字段仍指向 `pcr02-owner-decision-worksheet-001` |
| status-text-owner-summary-commands | 当前状态看板文本输出暴露 owner 分派摘要命令 | 文本模式同时输出 all-open/by-owner summary commands、forms-jsonl commands 和 review_after 复核命令，人工分派不必切到 JSON 才能发现 owner summary 入口 |
| status-owner-gates-exit-code-blocker | 临时副本让 owner-gates 输出可解析 JSON 但返回非零 | `knowledge-status --strict --json` 必须返回 `needs-fix`，并输出 `owner-gates-command-failed` blocker |
| final-gate-owner-review-blocker | 当前终态 gate 聚合 check、regression、`rtk git diff --check`、strict status、命令级 evidence index、结构化 gap map、owner recovery、Level 1/2/3 审计摘要和 proof 主制品可发现性摘要 | `knowledge-check`、`knowledge-regression` 与 `git_diff_check` 必须通过；当前只因 `owner-gates-open` 返回 `needs-owner-review`，并输出 `automatic_governance.status=complete-except-owner-review`、`automatic_governance.owner_blocker_source`、`evidence_index`、`owner_recovery`、稳定字段 `proof_artifacts`、兼容字段 `proof_artifacts_20260622`、`final_state_audit` 与 owner gap map |
| final-gate-skip-regression-blocker | 显式设置 `KNOWLEDGE_FINAL_GATE_SKIP_REGRESSION=1` 让 regression 自测短路 | final gate 必须返回 `needs-fix`，并输出 `knowledge-regression-skipped` blocker，避免终态验收被环境变量绕过 |
| final-gate-empty-child-json-blocker | 临时副本让 child gate exit 0 但 stdout 为空 | final gate 必须返回 `needs-fix`，并把空 JSON 输出归为 unparseable blocker，不能把静默成功当作通过 |
| final-gate-default-regression-path | 当前终态 gate 默认路径真实执行 regression | 非自测路径下 final gate 返回 `needs-owner-review` 时，`checks.knowledge_regression.status=pass`、`skipped_for_self_test=false`，避免只覆盖 recursion skip 分支 |
| final-gate-source-final-state-field-gap | 临时副本移除某个 registered source 的 `final_disposition` 字段后运行 final gate | final gate 必须输出 `registry` typed gap，带 source_id、field、可自动修复标记和无需 owner decision 标记，避免非 owner/source 缺口被压成泛化 `final-gate` |
| final-gate-strict-status-nonowner-blocker | 临时副本让 `knowledge-status --strict --json` 输出可解析的非 owner blocker | final gate 必须返回 `needs-fix`，`automatic_governance.status=needs-fix`，不能把非 owner blocker 包装成 `needs-owner-review` |
| final-gap-readability-positive-contracts | 当前仓库不改 fixture，直接验证终态 gap/readability 正向路径 | `knowledge-check` 必须 pass，final gate 必须只停在 owner review；2026-06-21 后 governance audit、migration `notes_zh` 和 source final-state 字段均完整 |
| final-gate-maintenance-entry-wording-no-section-drift | 当前 final gate 维护入口摘要不得依赖易漂移的章节编号 | `tools/knowledge-final-gate.sh` 必须使用“docs/goals 中列出的 8 类长期维护入口”描述运行时摘要，不得继续输出“第七节”章节口径 |
| owner-landing-plan-project-index | 当前 landing plan 和 landing audit 输出 owner 决策人工落地文件清单、worksheet 验证目录、验证命令和落地审计 | `required_manual_files` 包含 `pcr02-owner-decision-worksheets-20260618.jsonl`、`indexes/by-project.md` 和 `indexes/by-status.md`；landing audit 标记只读，要求人工更新 worksheet 行，并列出 registry/migration/index 手工 delta |
| owner-validate-forms-partial-coverage-warning | 当前 owner 表单校验允许合法分批签收，但必须暴露过滤范围覆盖情况 | 单条合法 owner form 在全 `pcr02-project-docs` 范围校验时仍可 pass；`form_validation.coverage_status=partial`，`missing_open_worksheet_ids` 和 landing plan/audit 的 `remaining_open_after_this_batch` 必须提示剩余 open worksheet |
| owner-archive-only-target-path-compatibility | 当前 archive-only owner 表单允许指向明确 archive 路径 | worksheet 007 选择 `owner_decision=archive-only` 且 `target_decision` 为 `domains/projects/pcr02/archive/...` 时必须通过表单兼容性校验，不要求 owner 使用 worksheet 未列出的字面 `archive-only` 目标 |
| owner-archive-only-rejects-non-archive-target | 当前 archive-only owner 表单拒绝 validation / decisions 等非 archive 目标 | worksheet 007 选择 `owner_decision=archive-only` 但 target 指向 `domains/projects/pcr02/validation/` 时必须失败，并给出 `owner-decision-target-mismatch` 诊断 |
| status-owner-ready-source-no-registry-fallback | 当前 status dashboard 的 owner queue 不得用 registry item presence 推断 owner-ready covered | `owner_gates.next_open_queue[]` 的 `owner_ready_package_status` 必须来自 `knowledge-owner-gates` 逐行强校验字段；若 open row 缺字段，应暴露 schema blocker，且 `tools/knowledge-status.sh` 不得保留 registry fallback 片段 |
| owner-landing-plan-requires-owner-ready-missing | 临时副本移除某条 owner-ready registry item 后生成 landing plan | owner 表单校验仍可通过，但 `landing_plan.status=blocked`，`owner_ready_gate.status=blocked`，不能输出人工落地 steps |
| owner-landing-plan-requires-owner-ready-invalid | 临时副本破坏某条 owner-ready package JSONL 后生成 landing plan | owner 表单校验仍可通过，但 `owner_ready_package_status=invalid` 会阻断 landing plan，不能输出人工落地 steps |
| owner-landing-plan-requires-owner-ready-repo-relative-command | 临时副本把某条 owner-ready package Markdown 的稳定工具命令改回 repo-relative 命令 | owner 表单校验仍可通过，但 `owner_ready_package_status=invalid` 会阻断 landing plan，避免生成只能在仓库 cwd 下执行的签收命令 |
| owner-landing-plan-requires-owner-ready-duplicate | 临时副本复制某条 owner-ready registry item 后生成 landing plan | owner 表单校验仍可通过，但 `owner_ready_package_status=duplicate` 会阻断 landing plan，不能输出人工落地 steps |
| owner-form-target-decision-candidate-gate | 当前 owner 表单校验拒绝 target_decision 越过 worksheet 候选目标 | valid form 若把 `target_decision` 改成 `domains/embedded/standards/...` 等非 `target_candidates` 值，`--validate-forms` 必须失败 |
| owner-form-decision-target-pair-reference-only-project-path | 当前 owner 表单校验拒绝 `reference-only` 搭配项目落地路径 | valid form 若把 `owner_decision` 填为 `reference-only` 且 `target_decision` 仍指向 `domains/projects/...`，`--validate-forms` 必须失败 |
| owner-form-decision-target-pair-no-migration-project-path | 当前 owner 表单校验拒绝 `no-migration` 搭配项目落地路径 | valid form 若把 `owner_decision` 填为 `no-migration` 且 `target_decision` 仍指向 `domains/projects/...`，`--validate-forms` 必须失败 |
| owner-form-decision-target-pair-project-rule-reference-only | 当前 owner 表单校验拒绝落地类 decision 搭配 `reference-only` target | valid form 若把 `owner_decision` 填为 `project-local-rule` 且 `target_decision` 填为 `reference-only`，`--validate-forms` 必须失败 |
| owner-form-decision-target-pair-positive-reference-only | 当前 owner 表单校验接受 `reference-only` 与 `reference-only` 的合法终止组合 | valid form 若把 `owner_decision` 和 `target_decision` 都填为 `reference-only`，`--validate-forms` 必须通过，避免负向门禁误伤不迁移引用决策 |
| owner-form-decision-target-pair-positive-no-migration | 当前 owner 表单校验接受 `no-migration` 与 `no-migration` 的合法终止组合 | valid form 若把 `owner_decision` 和 `target_decision` 都填为 `no-migration`，`--validate-forms` 必须通过，避免负向门禁误伤明确不迁移决策 |
| owner-form-routing-owner-reviewed-by-gate | 当前 owner 表单校验拒绝把 routing_owner 当作 reviewed_by | `routing_status=needs-human-assignment` 的 valid form 若把 `reviewed_by` 填成 `pcr02-registry-owner` 等 routing_owner，`--validate-forms` 必须失败 |
| owner-form-must-not-tamper-gate | 当前 owner 表单校验拒绝 must_not guardrail 被改写 | valid form 若改写 `must_not`，`--validate-forms` 必须失败，避免漂移 guardrail 进入 landing plan |
| owner-form-allowed-decisions-tamper-gate | 当前 owner 表单校验拒绝 allowed_owner_decisions 被改写 | valid form 若改写 `allowed_owner_decisions`，`--validate-forms` 必须失败，避免漂移枚举进入 landing plan |
| owner-form-target-candidates-tamper-gate | 当前 owner 表单校验拒绝 target_candidates 被改写 | valid form 若改写 `target_candidates`，`--validate-forms` 必须失败，避免 owner form 越过 worksheet 原始候选目标 |
| owner-form-source-identity-mismatch | 当前 owner 表单校验拒绝过期源文件身份 | owner 回填的 `source_sha256` 不等于当前只读观测 hash 时，`--validate-forms` 返回失败 |
| manual-entry-project-index-hint | 当前人工新增条目向导输出条件索引提示 | 项目域包含 `indexes/by-project.md`，非项目域不包含项目索引噪音；已登记 source 才提示同步 `indexes/by-source.md`，`kind=decision` 才输出 `indexes/by-decision.md` 骨架 |
| manual-entry-registered-source-binding | 当前人工新增条目向导支持已登记 source 绑定 | 普通 item 模式传入 `--item-source-id` 后，registry 草稿写入 `source.source_id`，输出真实 `by-source` 草稿和带 `--source-id` 的检索命令；未知 source id 必须失败，不能伪造 source |
| manual-entry-project-derived-from-domain | 当前人工新增项目条目向导从 domain 推导项目名 | 未传 `--project` 时由 `projects/<project>` 推导；不一致时输出 warning |
| manual-entry-default-dates | 当前人工新增向导输出默认日期 | registry / migration 草稿填入 ISO 日期，不保留日期占位符 |
| manual-entry-owner-override | 当前人工新增向导支持 owner 覆盖 | 默认 owner 为 `leiwenjun`，传入 `--owner team-core` 时草稿使用 `team-core` |
| manual-entry-owner-registry-and-personal-defaults | 当前人工新增向导暴露 item owner registry 状态，并对 personal-local 给出安全默认值 | 未登记 item owner 只输出 warning、不伪造 owner；`domain=personal` 或 `domains/personal/` 路径默认 `visibility=personal-local`、`status=personal`，显式 domain/path 冲突会提示不可直接落盘 |
| manual-entry-docs-owner-option | 当前 README、tools README 和 `knowledge-new.sh --help` 暴露人工新增 owner 参数 | README、tools README 与工具 help 均包含 `knowledge-new.sh` 和 `--owner`；项目示例展示从 domain 推导 project |
| manual-entry-offline-docs | 当前 README 和模板说明离线人工默认字段与迁移条件 | README 明确 `manual_validation_pending: true`、`source.type=manual`、`status=reviewing`、`review_status=manual-entry-pending-review`；模板说明 `registry/migrations.jsonl` 只在迁移、引用或归档时补齐 |
| readme-offline-shortest-paths | 当前 README 保留 5 条人工维护最短路径和终态检查离线 fallback | README 必须包含“人工维护 5 条最短路径”、5 个子标题、`manual_validation_pending: true`、`required_followup`、`rtk git diff --check` 和 final-gate 命令，避免离线维护入口被删改 |
| manual-entry-validation-diagnostics-default | 当前人工新增向导默认使用 diagnostics 验证命令 | registry 草稿 `validation_refs` 和 Evidence Index 默认使用 `knowledge-check --dry-run --json --diagnostics`，离线 follow-up 不退化为普通 check |
| manual-entry-readability-fields | 当前人工新增向导输出中文长期资产字段 | registry 草稿包含 `summary_zh`、`primary_language`、`review_status`、`evidence_strength`、AI provenance 和人工待验证原因 |
| manual-entry-archive-default-status | 当前人工新增归档类条目默认使用 archived 状态 | `knowledge-new.sh --kind project-archive` 输出 registry 草稿时使用 `status=archived`，避免历史归档被误写成 active/reviewing 当前事实 |
| offline-validation-template-placeholders | 当前离线待验证模板保留人工复核占位 | README / indexes / templates 的离线片段包含 `manual_validation_pending`、原因、required follow-up 和 `review_after`，避免离线补录缺少后续验证路径 |
| governance-audit-readability-gate | 临时副本移除 2026-06-21 governance audit registry item 的 `summary_zh` | `knowledge-check` 必须失败，避免新增治理 audit 缺少中文摘要和语言字段 |
| ai-generated-item-provenance-gate | 临时副本移除 2026-06-21 AI-generated registry item 的 `ai_model_or_tool` 和 `ai_generated_at` | `knowledge-check` 必须失败，避免 AI 生成条目缺少可追溯模型/工具和生成时间 |
| migration-notes-zh-gate | 临时副本移除 2026-06-21 migration row 的 `notes_zh` | `knowledge-check` 必须失败，避免新增 migration 只保留英文 notes 而无法被中文维护者快速理解 |
| manual-entry-migration-conditional-guide | 当前人工新增向导把 migration 作为条件步骤 | 普通新知识不强制新增 migration；只有迁移、引用或归档时使用 `registry/migrations.jsonl` 草稿，且草稿包含 `notes_zh` |
| manual-entry-template-selection | 当前人工新增向导保持 kind 到模板映射稳定 | `runbook`、`decision`、`validation`、`project-archive`、`artifact-ref` 使用专用模板，其他 kind 回落 `templates/item.md` |
| templates-required-sections | 当前核心模板包含长期资产字段和关键章节 | `item.md`、`runbook.md`、`decision.md` 均包含 canonical 可读性字段、AI provenance、Evidence Index、风险与 Review 章节 |
| index-readme-maintenance-coverage | 当前索引 README 覆盖人工维护入口与 AI 安全边界 | README 必须说明 registry/source/migration 权威来源、核心与扩展索引、`knowledge-index-plan`/`knowledge-check` 命令、offline 默认字段，以及不得覆盖人工结论、自动 active、关闭 owner gate 或写 memory |
| index-plan-extended-sections | 当前索引规划器覆盖核心索引维护面 | `knowledge-index-plan.sh --section project/source/topic/decision/manifest --json` 均输出 read-only planned 结果，并包含 `by_project`、`by_source`、`by_topic`、`by_decision`、`by_manifest` 派生视图；source 视图带 owner/review_after/final_disposition/check/no_check_reason 和 coverage decision/risk，owner worksheet 视图带 owner/status/review_after，manifest 视图带 Markdown/JSONL 配对、行数、证据计数、filename-date-only latest 策略和 unpaired `expected` / `needs_review` 只读分类 |
| manifest-latest-filename-date-only | 临时副本新增两个 row 日期与文件名日期相反的 manifest | `knowledge-index-plan.sh --section manifest --json` 必须只按文件名 `YYYYMMDD` 排 latest，row 内日期只作为 `row_date`，避免旧文件凭 checked_at 抢占最新恢复依据 |
| manifest-jsonl-profile-gate | 临时副本移除 2026-06-21 及之后 governance manifest JSONL 的中文摘要和证据字段 | `knowledge-check` 必须失败，避免新增治理 manifest 只留下难读或无证据的 JSONL 行 |
| template-readability-field-gate | 临时副本移除 `templates/runbook.md` 的 `summary_zh` 字段 | `knowledge-check` 必须失败，避免长期模板退化为缺少中文摘要、证据、review 或 AI provenance 字段 |
| status-source-governance-summary | 当前状态看板 JSON 暴露 source coverage、source check、boundary health、review_after 和终态恢复命令 | `knowledge-status.sh --json` 必须输出 source 注册数、最新 source coverage manifest、latest coverage 选择依据、source_check_health、boundary_health、stale review_after 计数、review_after 复核命令、owner-ready package 覆盖率和 final gate 命令 |
| source-check-health-contract | 当前 `knowledge-check` 输出 source check/no-check 静态契约健康面 | 13 个 registered source 中 9 个有 rtk check、4 个有 no_check_reason，不执行 check 命令；负向 fixture 将 check 改成非 rtk 时必须失败 |
| source-check-report-only-helper | 当前 source check 辅助工具只执行 PCR02 Level 2 allowlist 的 report-only availability check | `knowledge-source-check.sh --scope pcr02-level2 --json` 必须 7/7 pass，且不改变 `knowledge-check` 的 `source_check_health.executed=false` 静态契约 |
| source-check-rejects-unsafe-runtime-command | 临时副本把 allowlist source 的 check 改成带 shell 控制符的 runtime payload | `knowledge-source-check.sh` 必须拒绝执行并返回非零，避免 registry 字符串变成任意 shell 执行入口 |
| final-gate-source-check-runtime-failed-blocker | 临时副本把 allowlist source 的 check 改成合法但必失败的路径存在性检查 | `knowledge-final-gate.sh` 必须输出 `source-check-runtime-failed` blocker、`final_status=needs-fix` 和 `gap_type=source-coverage`，避免 source-check 失败被 owner gate 掩盖 |
| review-after-near-due-json-contract | 当前 review_after 辅助工具输出 30 天 near-due report | `knowledge-review-after.sh --as-of 2026-06-22 --window-days 30 --json` 必须输出 32 个 near-due item、0 个 stale item/source、7 个 owner gate open，且 near-due 不作为 blocking gate |
| automation-report-only-safety-gate | 当前 `knowledge-check` 对 maintenance automation 记录执行 report-only/no-memory 硬门禁 | 负向 fixture 将 memory auto-curation automation 改成 enabled、apply、写 memory、写 team active index 且移除 no_memory_write_gate 时必须失败 |
| source-coverage-date-filename-selection | 临时副本新增非日期 latest closeout 候选 | `knowledge-check`、`knowledge-status`、`knowledge-index-plan` 和 `knowledge-final-gate` 必须继续选择最新 `YYYYMMDD` closeout，并把非日期候选列入 ignored metadata |
| source-coverage-duplicate-source-id-warning | 临时副本在 latest source coverage closeout 中追加重复 `source_id` 行 | `knowledge-index-plan.sh --section source --json` 必须输出 `duplicate_source_ids` 和 warning，并保留第一行作为恢复视图，避免后写重复行静默覆盖 |
| review-after-as-of-deterministic | 临时副本把一条 reviewing item 的 `review_after` 固定在 2026-06-30，并分别用 `--as-of 2026-06-01/2026-07-01` 运行 check/status/final-gate | `knowledge-check`、`knowledge-status` 和 `knowledge-final-gate` 必须暴露固定 `today/as_of_source`，并按固定日期稳定判断 stale review_after，避免真实当天日期导致回归不可复现 |
| stale-review-after-warning-surface | 临时副本把一条 reviewing item 的 `review_after` 改到过去 | `knowledge-check` 仍通过但输出 stale warning，`knowledge-status` 暴露 stale count、sample 和 review_after 复核命令，证明过期复核是人工治理提醒而不是阻断错误 |
| source-review-after-stale-surface | 临时副本把一条 registered source 的 `review_after` 改到过去 | `knowledge-check` 仍通过但输出 source stale warning，`knowledge-status.sources` 暴露 stale count、sample 和 source 复核命令，证明 source 过期复核是人工治理提醒而不是阻断错误 |
| source-manual-entry-guide | 当前人工 source 新增向导输出完整草案 | `knowledge-new.sh --source` 输出 `registry/sources.json` object、`indexes/by-source.md` 主表行和 source coverage JSONL row 草案，并保留 no-check reason；registry source `review_after` 默认使用 owner 复核周期，不与 coverage `checked_at` 同日 |
| source-manual-entry-enum-guide | 当前人工 source 新增向导输出枚举速查并拒绝非法枚举 | `knowledge-new.sh --source` 输出 role/authority/status/write_policy/final_disposition 常用值；传入非法枚举必须非零退出，避免生成 schema 不接受的 source 草稿 |
| source-manual-entry-guide-check-command | 当前人工 source 新增向导支持稳定只读 check | 传 `--check "rtk ..."` 时 registry source 草稿和 source coverage JSONL row 草稿均包含 `check` 字段，且不输出 JSON 形式的 `no_check_reason` |
| source-manual-entry-status-coverage-sync | 当前人工 source 新增向导让 coverage row 跟随 `--source-status` | `--source-status retired/deprecated` 时，registry source object 保留对应状态，coverage row 输出 `retired-pending-classification` / `deprecated-pending-classification`，不得固定写 registered |
| source-manual-entry-unknown-owner-warning | 当前人工 source 新增向导对未知 owner 给出预警 | `knowledge-new.sh --source --owner <unknown>` 保持 exit 0 输出草稿，但显示 `owner_registry_status=unknown-owner` 和中文 warning，提醒落盘前补 owner registry |
| source-manual-entry-requires-check-or-reason | 当前人工 source 新增向导要求检查命令或 no-check 原因二选一 | 不传 `--check` / `--no-check-reason` 会失败；二者同时传也会失败，避免生成占位 source coverage 草稿 |
| source-manual-entry-docs-check-preferred | 当前 README、tools README 和 `knowledge-new.sh --help` 展示 source `--check` 优先路径 | 文档和 help 同时展示 `--check` 与 `--no-check-reason`，说明二选一约束，并说明有稳定检查命令时 registry source object 与 source coverage JSONL row 草稿都记录 `check` |
| source-manual-entry-role-aware-recommendations | 当前 source 新增向导按 role/write_policy/check 输出只读推荐终态和理由 | 推荐值不替代 owner decision，不关闭 owner gate，copyable registry JSON 仍保守使用 `owner-gated-pending-decision` |
| knowledge-search-structured-filters | 当前搜索入口支持 registry-backed 结构化过滤 | `knowledge-search.sh` 保持全文搜索兼容，同时按 `--owner`、`--status` 和 `--source-id` 返回带 `item_id/status/owner/source_id` 的 registry item 命中 |
| knowledge-search-structured-filters-exclude-unregistered-raw | 临时副本新增同关键词但未登记 raw file 后运行结构化 source 搜索 | 使用 `--source-id` 等结构化过滤时，结果必须全部关联 registry item，并排除未登记 raw file，避免恢复时把历史材料误当 current fact |
| knowledge-search-kind-alias-filters | 当前搜索入口支持模板 kind 别名归一到 registry kind | `--kind validation-report` 会归一为 `validation` 过滤，并在 JSON 中暴露 `kind_normalized`，避免模板别名和 registry 枚举割裂 |
| knowledge-search-registry-metadata-fallback | 临时副本新增正文不含关键词、registry metadata 含关键词的 item 后运行结构化搜索 | `knowledge-search.sh` 必须通过 registry metadata fallback 返回 `match=registry-metadata` 的 item，避免只登记在 registry 的长期入口无法被关键词发现 |
| knowledge-search-invalid-filters | 当前搜索入口拒绝非法枚举过滤值和非正 limit | `--status not-a-status`、`--kind not-a-kind` 和 `--limit 0` 非零退出，并提示允许值或正整数要求，避免无效过滤静默退化为全文搜索 |
| stable-governance-command-examples | 治理文档和模板保持稳定命令示例 | README、tools README、templates、governance 和 indexes 不得退回 repo-relative `rtk bash tools/...`、短 `knowledge-check --dry-run` 或弱 validation_refs 示例 |
| final-proof-artifact-discoverability | 当前终态 proof/gate/recovery 主制品可从 registry、migration 和核心索引发现 | 10 个 2026-06-22 终态 proof 主项必须有 `.md/.jsonl` 配对，出现在 registry/items、registry/migrations、by-owner、by-status、by-review-date 和 by-topic，且索引引用不得指向不存在文件 |
| final-proof-artifact-as-of-date-selector | 临时副本新增 2026-06-23 governance proof manifest 后运行 final gate | `knowledge-final-gate.sh --as-of 2026-06-23` 必须按 as-of 日期发现新 proof，同时保留 2026-06-22 seed 基线，避免动态 proof selector 继续绑定固定日期 |
| final-proof-artifacts-stable-alias | 当前终态 proof 主制品摘要提供稳定 JSON 字段并兼容旧日期字段 | final gate 必须输出稳定 `proof_artifacts`，保留 `proof_artifacts_20260622`，且两者内容完全一致，避免长期恢复依赖日期化 key |
| index-plan-topic-schema-health | 当前 topic 索引规划视图和 `registry/topics.json` 对齐 | `knowledge-index-plan.sh --section topic --json` 输出的 topic id 与 topic registry 完全一致 |
| index-plan-decision-registry-health | 当前 decision 索引规划视图覆盖 registry decisions | `knowledge-index-plan.sh --section decision --json` 的 registry decision id 与 `registry/decisions.jsonl` 完全一致且不重复 |
| index-decision-registry-subsection-gate | 当前 `by-decision` 强门禁只锁 registry decision 覆盖 | 移除 registry decision 的索引引用会触发 `knowledge-check`，但不把 owner worksheet / migration decision 当作 registry decision 强约束 |
| index-topic-zero-bucket-allowed | 当前 topic 规划允许空 topic | 空 topic 作为健康数据保留，不作为硬失败 |
| regression-manifest-coverage | 当前回归 helper manifest 覆盖所有回归 ID | manifest 覆盖范围表必须为每个实际回归 ID 提供唯一行，且“场景”和“预期”列非空；自检会用实际已执行 result id 反查 required 清单，避免漏登 ID 或只在正文里随意出现 ID |

## 决策

- 不引入测试框架。
- 不写真实仓库。
- 不保存临时 fixture；默认逐场景清理，需要排查时使用 `--keep-temp`。
- 低空间预检使用 `KNOWLEDGE_REGRESSION_MIN_TMP_FREE_BYTES`，默认 4 MiB；空间不足或复制异常时先记录 failure details，`--json` 模式输出 JSON，默认模式保留人工可读文本摘要；`knowledge-final-gate.sh` 将临时空间耗尽归类为 environment gap，避免误判为知识内容回归。
- 作为提交前可选回归入口，覆盖最容易造成终态漂移的 owner/status 门禁。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json` | 0 | 通过；105 个回归场景全部 pass，覆盖 governance goal path explainability、PCR02 Level 2 source coverage、7 个 PCR02 Level 2 source boundary manifests、boundary_health 内部证据健康面和负向 source_id 篡改、status 负向 fixture、owner gate 负向 fixture、owner handoff packet、owner form 聚焦、owner forms 文本 JSONL 输出、owner forms 纯 JSONL 输出、owner forms target candidates、owner forms 纯 JSONL 互斥保护、owner checklist、owner form 上下文、owner source identity 上下文、owner prefill candidates、owner evidence readiness、owner inbox 字段分组与安全命令、owner source identity 过期拒绝、owner target_decision 候选目标门禁、owner decision/target 成对兼容门禁、owner decision/target 合法终止组合正向门禁、owner routing_owner 代签 reviewed_by 拒绝、owner guardrail/decision enum/target_candidates 篡改拒绝、owner summary、owner by-owner summary、owner next-open 聚焦、status next owner gate、status text owner summary/review_after commands、owner-gates 子命令非零阻断、final gate owner blocker、final gate evidence index、final gate strict 非 owner blocker、final gate skip regression blocker、final gate empty child JSON blocker、final gate default regression path、final gate typed registry gap、final gate source coverage selection、final gate 当前 source-check 证据和高优先级规则审计、final gate source-check runtime 失败 blocker、final gap/readability 正向契约、final gate git diff check、final gate automatic governance/gap map、final state Level 1/2/3 audit summary、final gate owner_recovery、final proof as-of 日期选择、owner landing plan / landing audit 执行目录、动态 worksheet 文件、worksheet 验证命令和人工 delta、owner-ready missing/invalid/duplicate/repo-relative-command landing gate、manual entry by-project/by-source/by-decision 条件索引提示、manual entry 已登记 source 绑定、unknown source 拒绝、owner 文档可发现性、owner registry 状态与 personal-local 默认值、offline manual defaults、README 5 条最短路径和终态检查离线 fallback、人工新增 diagnostics 默认验证、人工新增可读性字段、归档类人工入口默认 archived、离线待验证模板占位、governance audit 可读性 gate、AI provenance gate、migration notes_zh gate、migration 条件提示、模板选择和 registry kind 映射、模板必备章节、indexes README 维护规则、index planner 核心 section 派生视图、coverage decision/risk、manifest filename-date-only latest 与 unpaired 分类、manifest JSONL 轻量 profile gate（2026-06-21 及之后）、模板可读性字段 gate、终态 proof 主制品可发现性、topic/decision 索引规划健康、decision registry 强门禁、空 topic 允许、status source governance summary、source_check_health 静态契约和非 rtk 负向门禁、source-check report-only helper、source-check unsafe runtime 拒绝、review_after near-due report、review_after 分组 JSON 契约、automation report-only/no-memory 硬门禁、source coverage 日期文件名选择、source coverage duplicate source_id warning、review_after as-of 固定日期复现、stale item/source review_after warning/status surface、source 新增向导、source 新增向导 review_after 默认复核周期、source 枚举速查和非法枚举预校验、source check 命令分支、source status coverage 同步、source unknown owner warning、source check/no-check 二选一、source check 文档优先路径、source role-aware 推荐提示、knowledge-search 结构化过滤、structured filters 排除未登记 raw file、kind alias 归一过滤、registry metadata-only fallback、无效 filter/limit 拒绝、治理文档稳定命令示例和 regression manifest 自检 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-governance-regression-helper-20260619` |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json --as-of 2026-06-23` | 0 | 通过；111 个回归场景全部 pass，新增 `final-proof-artifacts-stable-alias`、`owner-validate-forms-partial-coverage-warning`、`status-owner-ready-source-no-registry-fallback`、`final-gate-maintenance-entry-wording-no-section-drift`、`owner-archive-only-target-path-compatibility` 和 `owner-archive-only-rejects-non-archive-target`，证明 final gate 的 canonical `proof_artifacts` 与 legacy `proof_artifacts_20260622` 内容一致，owner validate/landing 对分批签收给出 partial coverage 提示，status owner queue 不再从 registry item presence 推断 owner-ready covered，final gate 维护入口摘要不依赖易漂移的章节编号，且 archive-only owner 表单可使用明确 archive 路径并拒绝非 archive 目标。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-governance-regression-helper-20260619` |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认新增 helper 和文档登记后全仓门禁通过 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-governance-regression-helper-20260619` |
| `rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind audit --domain governance --id sample-regression --path artifacts/manifests/sample-regression.md` | 0 | 通过；人工新增向导输出短 canonical status 行示例 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-governance-regression-helper-20260619` |

## Current Regression IDs Added 2026-06-21/2026-06-22

- `manual-entry-archive-default-status`
- `readme-offline-shortest-paths`
- `offline-validation-template-placeholders`
- `manual-entry-validation-diagnostics-default`
- `manifest-latest-filename-date-only`
- `source-coverage-duplicate-source-id-warning`
- `source-manual-entry-status-coverage-sync`
- `knowledge-search-structured-filters-exclude-unregistered-raw`
- `knowledge-search-kind-alias-filters`
- `knowledge-search-registry-metadata-fallback`
- `final-proof-artifact-as-of-date-selector`
- `manual-entry-registered-source-binding`
- `source-manual-entry-enum-guide`
- `owner-form-routing-owner-reviewed-by-gate`
- `owner-inbox-contract`
- `automation-report-only-safety-gate`
- `source-review-after-stale-surface`
- `final-gate-strict-status-nonowner-blocker`
- `source-check-report-only-helper`
- `source-check-rejects-unsafe-runtime-command`
- `review-after-near-due-json-contract`
- `owner-form-decision-target-pair-reference-only-project-path`
- `owner-form-decision-target-pair-no-migration-project-path`
- `owner-form-decision-target-pair-project-rule-reference-only`
- `owner-form-decision-target-pair-positive-reference-only`
- `owner-form-decision-target-pair-positive-no-migration`
- `owner-form-target-candidates-tamper-gate`

## 边界

- 不修改 PCR02 源项目 docs。
- 不关闭任何 PCR02 owner gate。
- 不生成 owner decision。
- 不启用自动化，不写 memory。
- 不替代 `knowledge-check`、`knowledge-status --strict` 或 owner review。
