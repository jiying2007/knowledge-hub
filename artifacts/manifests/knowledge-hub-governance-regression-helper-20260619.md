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
| owner-summary-all-open | 当前 owner gate helper 输出全部 open gate 摘要 | `--summary` 输出 7 条 open gate、owner 分布、owner_dispatch 分派包、source identity 计数和聚焦命令，但不输出 forms/checklists |
| owner-summary-by-owner | 当前 owner gate helper 按 owner 输出 open gate 摘要 | `--owner project-owner --summary` 只输出 project-owner 名下 2 条 open gate，并保留该 owner 的只读 forms-jsonl、validate、landing-plan 和 next focus 分派命令 |
| owner-next-open-focus | 当前 owner gate helper 自动聚焦下一条 open worksheet | `--next-open --checklist --forms` 只输出下一条 open gate 的 checklist 和 form，不需要人工复制 worksheet id |
| status-next-owner-gate | 当前状态看板输出下一条 owner gate 聚焦命令 | JSON 中存在 `owner_gates.owner_dispatch[]`、`owner_gates.next_open.next_open_command`、`focus_command` 和 evidence-readiness 命令；`next_actions_zh` 使用 `owner_gates.owner_dispatch[]`、`--next-open --checklist --forms` 与 `--evidence-readiness --json`，兼容字段仍指向 `pcr02-owner-decision-worksheet-001` |
| status-text-owner-summary-commands | 当前状态看板文本输出暴露 owner 分派摘要命令 | 文本模式同时输出 all-open/by-owner summary commands、forms-jsonl commands 和 review_after 复核命令，人工分派不必切到 JSON 才能发现 owner summary 入口 |
| status-owner-gates-exit-code-blocker | 临时副本让 owner-gates 输出可解析 JSON 但返回非零 | `knowledge-status --strict --json` 必须返回 `needs-fix`，并输出 `owner-gates-command-failed` blocker |
| final-gate-owner-review-blocker | 当前终态 gate 聚合 check、regression、`rtk git diff --check`、strict status、结构化 gap map、owner recovery 和 Level 1/2/3 审计摘要 | `knowledge-check`、`knowledge-regression` 与 `git_diff_check` 必须通过；当前只因 `owner-gates-open` 返回 `needs-owner-review`，并输出 `automatic_governance.status=complete-except-owner-review`、`owner_recovery`、`final_state_audit` 与 owner gap map |
| final-gate-skip-regression-blocker | 显式设置 `KNOWLEDGE_FINAL_GATE_SKIP_REGRESSION=1` 让 regression 自测短路 | final gate 必须返回 `needs-fix`，并输出 `knowledge-regression-skipped` blocker，避免终态验收被环境变量绕过 |
| final-gate-empty-child-json-blocker | 临时副本让 child gate exit 0 但 stdout 为空 | final gate 必须返回 `needs-fix`，并把空 JSON 输出归为 unparseable blocker，不能把静默成功当作通过 |
| final-gate-default-regression-path | 当前终态 gate 默认路径真实执行 regression | 非自测路径下 final gate 返回 `needs-owner-review` 时，`checks.knowledge_regression.status=pass`、`skipped_for_self_test=false`，避免只覆盖 recursion skip 分支 |
| final-gate-source-final-state-field-gap | 临时副本移除某个 registered source 的 `final_disposition` 字段后运行 final gate | final gate 必须输出 `registry` typed gap，带 source_id、field、可自动修复标记和无需 owner decision 标记，避免非 owner/source 缺口被压成泛化 `final-gate` |
| final-gap-readability-positive-contracts | 当前仓库不改 fixture，直接验证终态 gap/readability 正向路径 | `knowledge-check` 必须 pass，final gate 必须只停在 owner review；2026-06-21 后 governance audit、migration `notes_zh` 和 source final-state 字段均完整 |
| owner-landing-plan-project-index | 当前 landing plan 和 landing audit 输出 owner 决策人工落地文件清单、worksheet 验证目录、验证命令和落地审计 | `required_manual_files` 包含 `pcr02-owner-decision-worksheets-20260618.jsonl`、`indexes/by-project.md` 和 `indexes/by-status.md`；landing audit 标记只读，要求人工更新 worksheet 行，并列出 registry/migration/index 手工 delta |
| owner-landing-plan-requires-owner-ready-missing | 临时副本移除某条 owner-ready registry item 后生成 landing plan | owner 表单校验仍可通过，但 `landing_plan.status=blocked`，`owner_ready_gate.status=blocked`，不能输出人工落地 steps |
| owner-landing-plan-requires-owner-ready-invalid | 临时副本破坏某条 owner-ready package JSONL 后生成 landing plan | owner 表单校验仍可通过，但 `owner_ready_package_status=invalid` 会阻断 landing plan，不能输出人工落地 steps |
| owner-landing-plan-requires-owner-ready-repo-relative-command | 临时副本把某条 owner-ready package Markdown 的稳定工具命令改回 repo-relative 命令 | owner 表单校验仍可通过，但 `owner_ready_package_status=invalid` 会阻断 landing plan，避免生成只能在仓库 cwd 下执行的签收命令 |
| owner-landing-plan-requires-owner-ready-duplicate | 临时副本复制某条 owner-ready registry item 后生成 landing plan | owner 表单校验仍可通过，但 `owner_ready_package_status=duplicate` 会阻断 landing plan，不能输出人工落地 steps |
| owner-form-target-decision-candidate-gate | 当前 owner 表单校验拒绝 target_decision 越过 worksheet 候选目标 | valid form 若把 `target_decision` 改成 `domains/embedded/standards/...` 等非 `target_candidates` 值，`--validate-forms` 必须失败 |
| owner-form-must-not-tamper-gate | 当前 owner 表单校验拒绝 must_not guardrail 被改写 | valid form 若改写 `must_not`，`--validate-forms` 必须失败，避免漂移 guardrail 进入 landing plan |
| owner-form-allowed-decisions-tamper-gate | 当前 owner 表单校验拒绝 allowed_owner_decisions 被改写 | valid form 若改写 `allowed_owner_decisions`，`--validate-forms` 必须失败，避免漂移枚举进入 landing plan |
| owner-form-source-identity-mismatch | 当前 owner 表单校验拒绝过期源文件身份 | owner 回填的 `source_sha256` 不等于当前只读观测 hash 时，`--validate-forms` 返回失败 |
| manual-entry-project-index-hint | 当前人工新增条目向导输出条件索引提示 | 项目域包含 `indexes/by-project.md`，非项目域不包含项目索引噪音；已登记 source 才提示同步 `indexes/by-source.md`，`kind=decision` 才输出 `indexes/by-decision.md` 骨架 |
| manual-entry-project-derived-from-domain | 当前人工新增项目条目向导从 domain 推导项目名 | 未传 `--project` 时由 `projects/<project>` 推导；不一致时输出 warning |
| manual-entry-default-dates | 当前人工新增向导输出默认日期 | registry / migration 草稿填入 ISO 日期，不保留日期占位符 |
| manual-entry-owner-override | 当前人工新增向导支持 owner 覆盖 | 默认 owner 为 `leiwenjun`，传入 `--owner team-core` 时草稿使用 `team-core` |
| manual-entry-docs-owner-option | 当前 README、tools README 和 `knowledge-new.sh --help` 暴露人工新增 owner 参数 | README、tools README 与工具 help 均包含 `knowledge-new.sh` 和 `--owner`；项目示例展示从 domain 推导 project |
| manual-entry-offline-docs | 当前 README 和模板说明离线人工默认字段与迁移条件 | README 明确 `manual_validation_pending: true`、`source.type=manual`、`status=reviewing`、`review_status=manual-entry-pending-review`；模板说明 `registry/migrations.jsonl` 只在迁移、引用或归档时补齐 |
| manual-entry-readability-fields | 当前人工新增向导输出中文长期资产字段 | registry 草稿包含 `summary_zh`、`primary_language`、`review_status`、`evidence_strength`、AI provenance 和人工待验证原因 |
| governance-audit-readability-gate | 临时副本移除 2026-06-21 governance audit registry item 的 `summary_zh` | `knowledge-check` 必须失败，避免新增治理 audit 缺少中文摘要和语言字段 |
| ai-generated-item-provenance-gate | 临时副本移除 2026-06-21 AI-generated registry item 的 `ai_model_or_tool` 和 `ai_generated_at` | `knowledge-check` 必须失败，避免 AI 生成条目缺少可追溯模型/工具和生成时间 |
| migration-notes-zh-gate | 临时副本移除 2026-06-21 migration row 的 `notes_zh` | `knowledge-check` 必须失败，避免新增 migration 只保留英文 notes 而无法被中文维护者快速理解 |
| manual-entry-migration-conditional-guide | 当前人工新增向导把 migration 作为条件步骤 | 普通新知识不强制新增 migration；只有迁移、引用或归档时使用 `registry/migrations.jsonl` 草稿，且草稿包含 `notes_zh` |
| manual-entry-template-selection | 当前人工新增向导保持 kind 到模板映射稳定 | `runbook`、`decision`、`validation`、`project-archive`、`artifact-ref` 使用专用模板，其他 kind 回落 `templates/item.md` |
| templates-required-sections | 当前核心模板包含长期资产字段和关键章节 | `item.md`、`runbook.md`、`decision.md` 均包含 canonical 可读性字段、AI provenance、Evidence Index、风险与 Review 章节 |
| index-readme-maintenance-coverage | 当前索引 README 覆盖人工维护入口与 AI 安全边界 | README 必须说明 registry/source/migration 权威来源、核心与扩展索引、`knowledge-index-plan`/`knowledge-check` 命令、offline 默认字段，以及不得覆盖人工结论、自动 active、关闭 owner gate 或写 memory |
| index-plan-extended-sections | 当前索引规划器覆盖核心索引维护面 | `knowledge-index-plan.sh --section project/source/topic/decision/manifest --json` 均输出 read-only planned 结果，并包含 `by_project`、`by_source`、`by_topic`、`by_decision`、`by_manifest` 派生视图；source 视图带 owner/review_after/final_disposition/check/no_check_reason 和 coverage decision/risk，owner worksheet 视图带 owner/status/review_after，manifest 视图带 Markdown/JSONL 配对、行数、证据计数和 unpaired `expected` / `needs_review` 只读分类 |
| manifest-jsonl-profile-gate | 临时副本移除 2026-06-21 governance manifest JSONL 的中文摘要和证据字段 | `knowledge-check` 必须失败，避免新增治理 manifest 只留下难读或无证据的 JSONL 行 |
| template-readability-field-gate | 临时副本移除 `templates/runbook.md` 的 `summary_zh` 字段 | `knowledge-check` 必须失败，避免长期模板退化为缺少中文摘要、证据、review 或 AI provenance 字段 |
| status-source-governance-summary | 当前状态看板 JSON 暴露 source coverage、source check、boundary health、review_after 和终态恢复命令 | `knowledge-status.sh --json` 必须输出 source 注册数、最新 source coverage manifest、latest coverage 选择依据、source_check_health、boundary_health、stale review_after 计数、review_after 复核命令、owner-ready package 覆盖率和 final gate 命令 |
| source-check-health-contract | 当前 `knowledge-check` 输出 source check/no-check 静态契约健康面 | 13 个 registered source 中 9 个有 rtk check、4 个有 no_check_reason，不执行 check 命令；负向 fixture 将 check 改成非 rtk 时必须失败 |
| source-coverage-date-filename-selection | 临时副本新增非日期 latest closeout 候选 | `knowledge-check`、`knowledge-status` 和 `knowledge-index-plan` 必须继续选择最新 `YYYYMMDD` closeout，并把非日期候选列入 ignored metadata |
| review-after-as-of-deterministic | 临时副本把一条 reviewing item 的 `review_after` 固定在 2026-06-30，并分别用 `--as-of 2026-06-01/2026-07-01` 运行 check/status/final-gate | `knowledge-check`、`knowledge-status` 和 `knowledge-final-gate` 必须暴露固定 `today/as_of_source`，并按固定日期稳定判断 stale review_after，避免真实当天日期导致回归不可复现 |
| stale-review-after-warning-surface | 临时副本把一条 reviewing item 的 `review_after` 改到过去 | `knowledge-check` 仍通过但输出 stale warning，`knowledge-status` 暴露 stale count、sample 和 review_after 复核命令，证明过期复核是人工治理提醒而不是阻断错误 |
| source-manual-entry-guide | 当前人工 source 新增向导输出完整草案 | `knowledge-new.sh --source` 输出 `registry/sources.json` object、`indexes/by-source.md` 主表行和 source coverage JSONL row 草案，并保留 no-check reason |
| source-manual-entry-guide-check-command | 当前人工 source 新增向导支持稳定只读 check | 传 `--check "rtk ..."` 时 registry source 草稿和 source coverage JSONL row 草稿均包含 `check` 字段，且不输出 JSON 形式的 `no_check_reason` |
| source-manual-entry-unknown-owner-warning | 当前人工 source 新增向导对未知 owner 给出预警 | `knowledge-new.sh --source --owner <unknown>` 保持 exit 0 输出草稿，但显示 `owner_registry_status=unknown-owner` 和中文 warning，提醒落盘前补 owner registry |
| source-manual-entry-requires-check-or-reason | 当前人工 source 新增向导要求检查命令或 no-check 原因二选一 | 不传 `--check` / `--no-check-reason` 会失败；二者同时传也会失败，避免生成占位 source coverage 草稿 |
| source-manual-entry-docs-check-preferred | 当前 README、tools README 和 `knowledge-new.sh --help` 展示 source `--check` 优先路径 | 文档和 help 同时展示 `--check` 与 `--no-check-reason`，说明二选一约束，并说明有稳定检查命令时 registry source object 与 source coverage JSONL row 草稿都记录 `check` |
| knowledge-search-structured-filters | 当前搜索入口支持 registry-backed 结构化过滤 | `knowledge-search.sh` 保持全文搜索兼容，同时按 `--owner`、`--status` 和 `--source-id` 返回带 `item_id/status/owner/source_id` 的 registry item 命中 |
| knowledge-search-invalid-filters | 当前搜索入口拒绝非法枚举过滤值和非正 limit | `--status not-a-status`、`--kind not-a-kind` 和 `--limit 0` 非零退出，并提示允许值或正整数要求，避免无效过滤静默退化为全文搜索 |
| index-plan-topic-schema-health | 当前 topic 索引规划视图和 `registry/topics.json` 对齐 | `knowledge-index-plan.sh --section topic --json` 输出的 topic id 与 topic registry 完全一致 |
| index-plan-decision-registry-health | 当前 decision 索引规划视图覆盖 registry decisions | `knowledge-index-plan.sh --section decision --json` 的 registry decision id 与 `registry/decisions.jsonl` 完全一致且不重复 |
| index-decision-registry-subsection-gate | 当前 `by-decision` 强门禁只锁 registry decision 覆盖 | 移除 registry decision 的索引引用会触发 `knowledge-check`，但不把 owner worksheet / migration decision 当作 registry decision 强约束 |
| index-topic-zero-bucket-allowed | 当前 topic 规划允许空 topic | 空 topic 作为健康数据保留，不作为硬失败 |
| regression-manifest-coverage | 当前回归 helper manifest 覆盖所有回归 ID | manifest 包含当前全部回归场景和所有当前测试 ID；自检会用实际已执行 result id 反查 required 清单，避免漏登 ID 但仍因总数文本通过 |

## 决策

- 不引入测试框架。
- 不写真实仓库。
- 不保存临时 fixture；默认逐场景清理，需要排查时使用 `--keep-temp`。
- 低空间预检使用 `KNOWLEDGE_REGRESSION_MIN_TMP_FREE_BYTES`，默认 4 MiB；空间不足或复制异常时先记录 failure details，`--json` 模式输出 JSON，默认模式保留人工可读文本摘要；`knowledge-final-gate.sh` 将临时空间耗尽归类为 environment gap，避免误判为知识内容回归。
- 作为提交前可选回归入口，覆盖最容易造成终态漂移的 owner/status 门禁。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json` | 0 | 通过；73 个回归场景全部 pass，覆盖 governance goal path explainability、PCR02 Level 2 source coverage、7 个 PCR02 Level 2 source boundary manifests、boundary_health 内部证据健康面和负向 source_id 篡改、status 负向 fixture、owner gate 负向 fixture、owner form 聚焦、owner forms 文本 JSONL 输出、owner forms 纯 JSONL 输出、owner forms target candidates、owner forms 纯 JSONL 互斥保护、owner checklist、owner form 上下文、owner source identity 上下文、owner prefill candidates、owner evidence readiness、owner source identity 过期拒绝、owner target_decision 候选目标门禁、owner guardrail/decision enum 篡改拒绝、owner summary、owner by-owner summary、owner next-open 聚焦、status next owner gate、status text owner summary/review_after commands、owner-gates 子命令非零阻断、final gate owner blocker、final gate skip regression blocker、final gate empty child JSON blocker、final gate default regression path、final gate typed registry gap、final gap/readability 正向契约、final gate git diff check、final gate automatic governance/gap map、final state Level 1/2/3 audit summary、final gate owner_recovery、owner landing plan / landing audit 执行目录、worksheet 验证命令和人工 delta、owner-ready missing/invalid/duplicate/repo-relative-command landing gate、manual entry by-project/by-source/by-decision 条件索引提示、owner 文档可发现性、offline manual defaults、人工新增可读性字段、governance audit 可读性 gate、AI provenance gate、migration notes_zh gate、migration 条件提示、模板选择、模板必备章节、indexes README 维护规则、index planner 核心 section 派生视图、coverage decision/risk 和 manifest unpaired 分类、manifest JSONL 轻量 profile gate、模板可读性字段 gate、topic/decision 索引规划健康、decision registry 强门禁、空 topic 允许、status source governance summary、source_check_health 静态契约和非 rtk 负向门禁、source coverage 日期文件名选择、review_after as-of 固定日期复现、stale review_after warning/status surface、source 新增向导、source check 命令分支、source unknown owner warning、source check/no-check 二选一、source check 文档优先路径、knowledge-search 结构化过滤、无效 filter/limit 拒绝和 regression manifest 自检 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-governance-regression-helper-20260619` |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认新增 helper 和文档登记后全仓门禁通过 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-governance-regression-helper-20260619` |
| `rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind audit --domain governance --id sample-regression --path artifacts/manifests/sample-regression.md` | 0 | 通过；人工新增向导输出短 canonical status 行示例 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-governance-regression-helper-20260619` |

## 边界

- 不修改 PCR02 源项目 docs。
- 不关闭任何 PCR02 owner gate。
- 不生成 owner decision。
- 不启用自动化，不写 memory。
- 不替代 `knowledge-check`、`knowledge-status --strict` 或 owner review。
