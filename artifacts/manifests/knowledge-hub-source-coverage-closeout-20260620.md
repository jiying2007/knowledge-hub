# Knowledge Hub source coverage closeout 2026-06-20

## 结论

本轮把 PCR02 Level 2 关键资料源纳入 Knowledge Hub registered source 控制面。新增 source 只表示治理覆盖、只读引用和后续分类入口已经建立；不表示复制正文、执行源项目脚本、关闭 owner gate 或提升 active fact。

最新 source coverage 覆盖 13 个 registered source：原 6 个 Knowledge Hub source，加上 PCR02 `tools`、`knowledge`、`app_product_test`、`scratch`、根目录 loose artifacts、module `AGENTS.md` 和 agent config。

## 终态差距地图

| gap_id | gap_type | source_id | evidence | 当前影响 | 自动完成 | owner decision | 本轮动作 | 状态 |
|---|---|---|---|---|---|---|---|---|
| L2SC-001 | source-coverage | pcr02-project-tools | `tools` 存在，19 个非 `.git` 文件，含 diag scripts/csv、README/AGENTS、memory automation | 原先未登记，diag/tool/memory 自动化边界不可被 source coverage gate 追踪 | yes | maybe | 登记 source，分类为 reference/tool/validation-tool/owner-gated 混合边界 | applied |
| L2SC-002 | source-coverage | pcr02-project-knowledge | `knowledge` 存在，排除 `.git` 后 191 个文件，含 93 个 Markdown、`.env`、治理脚本 | 原先未登记，runbook/architecture 和 secret-like config 没有统一边界 | yes | maybe | 登记 source，分类为 classify-first + tool-ref/artifact-ref + secret-boundary | applied |
| L2SC-003 | source-coverage | pcr02-product-test | `app_product_test` 存在，排除 `.git` 后 127 个文件，含 Markdown/PDF/zip/tgz/ini/C/C++/object | 原先未登记，产品测试文档、制品和源码边界不清 | yes | maybe | 登记 source，分类为 artifact/config/interface/validation reference | applied |
| L2SC-004 | source-coverage | pcr02-project-scratch | `scratch` 存在，8 个 Markdown，均为 context/session 类材料 | session/handoff 可能被误当 active fact | yes | no | 登记 archive-only source，明确 no-memory-write 和 not-active-fact | applied |
| L2SC-005 | source-coverage | pcr02-project-root-artifacts | adjusted root loose view 为 21 个候选，含 `.md/.log/.txt/.patch/.sh/.py/.bin` | 根目录散落制品无法被统一 artifact-boundary 管理 | yes | maybe | 登记 root artifact source，明确 adjusted view 排除已单独治理子目录 | applied |
| L2SC-006 | source-coverage | pcr02-module-agent-rules | 6 个目标 module `AGENTS.md` 存在，实际只读扫描还发现额外 AGENTS | 模块本地规则可能被误提升为 Knowledge Hub 根规则 | yes | yes | 登记 module-local owner-gated rule source | applied |
| L2SC-007 | source-coverage | pcr02-project-agent-config | `.vscode/codex-tasks-sync.sh` 与 `.kilo/*` 存在 | agent 自动化配置缺少 report-only / artifact-ref 边界 | yes | maybe | 登记 config/artifact-ref source，自动化保持 report-only | applied |
| L2SC-008 | regression | all level2 sources | 新增 source 后需要防止 by-source 或 coverage JSONL 漏登记 | 后续可能出现 registry/source coverage 漂移 | yes | no | 新增 `pcr02-level2-source-coverage` 回归 | applied |

## Source Coverage Matrix

| Source | 终态分类 | 控制面结论 | 风险 |
|---|---|---|---|
| `pcr02-project-docs` | copy-first + reference-first + artifact-ref + owner-gated | 32/32 docs 已有治理覆盖；7 个 owner-gated 仍保持未语义关闭 | 控制面闭合不等于 owner 决策完成 |
| `engineering-archive` | copy-first archive-only | 38 个历史工程归档文本已 copy-first 到 PCR02 archive | 历史 archive corpus 不等于 active fact |
| `patent-disclosure` | patent markdown copy-first + attachments artifact-ref | 10 个 Markdown 已迁入，181 个非文本附件已 artifact-ref | 专利语义和法律状态仍需 owner/legal review |
| `embedded-knowledge` | legacy-team-ssot reference-first-candidate | 保持外部 legacy team SSOT，不批量迁移 | source dirty 或 project-specific 内容可能污染 team standards |
| `codex-archive` | codex workflow history reference-first | 通过 Codex archive tools 引用，不复制历史归档正文 | 历史记录不能直接作为 active governance rule |
| `codex-memories` | auxiliary recall only | 只作为辅助召回，不迁移、不自动写入、不作为事实唯一来源 | 自动化启用前必须补 owner approval、secret scan、rollback 和 writes_memory=false 运行证据 |
| `pcr02-project-tools` | reference-first + tool-ref + validation-tool-ref + owner-gated | README/AGENTS 只引用或 owner-gated；diag scripts/checks/csv 作为 validation-tool-ref；memory automation owner-gated/report-only/no-memory-write | memory 自动化脚本不能写 memory；模块 AGENTS 不能提升为根规则；脚本正文不默认复制 |
| `pcr02-project-knowledge` | classify-first + migration-candidate + tool-ref/artifact-ref + secret-boundary | runbooks/architecture 只是迁移候选；governance scripts 走 tool-ref；`.env`/config 需 secret scan 后 exclusion 或 artifact boundary | 含 `.env`、治理脚本、`.git` 和 docs/standards，不能直接提升团队标准 |
| `pcr02-product-test` | classify-first + artifact-ref + config-ref + interface/diagnostic/validation reference | Markdown 待 owner 决策；PDF/zip/tgz artifact-ref；ini/config config-ref；C/C++ 只建接口/诊断/验证引用 | 构建产物和源码不得进入文本知识层 |
| `pcr02-project-scratch` | archive-only registered | session wrap/context preflight 仅作历史证据或 handoff 参考 | handoff、memory candidates 不进入 active facts，不写 memory |
| `pcr02-project-root-artifacts` | mixed artifact/tool/reference boundary | adjusted root loose artifacts 作为 artifact-ref、archive-only、tool-ref 或 classify-first 候选 | `.bin/.log/.patch/.sh/.py` 不复制正文；抽取事实需 owner review |
| `pcr02-module-agent-rules` | module-local owner-gated rules | module `AGENTS.md` 只登记为项目/模块本地规则引用 | 未确认 owner、适用模块、review cycle 前不能提升为 active rule |
| `pcr02-project-agent-config` | config-ref + artifact-ref | `.vscode` 和 `.kilo` agent config 只作配置/自动化边界引用 | 不执行 setup/script，不验证依赖，不作为 active 团队规则 |

## 边界

- 不修改 PCR02 源项目任何文件。
- 不复制脚本、源码、日志、patch、bin、PDF、zip/tgz 或 `.env` 正文。
- 不执行源项目脚本、构建、setup 或产品测试。
- 不写 `~/.codex/memories`。
- 不生成 owner decision，不关闭 PCR02 owner gate。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- `pcr02-project-root-artifacts` 使用 adjusted root loose 视图，排除已由 docs/tools/knowledge/app_product_test/scratch/module AGENTS/agent config 单独治理的路径，避免重复 coverage。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -lc 'base=~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo; for d in tools knowledge app_product_test scratch; do printf "%s " "$d"; find "$base/$d" -path "*/.git/*" -prune -o -type f -print 2>/dev/null \| wc -l; done'` | 0 | `tools=19`，`knowledge=191`，`app_product_test=127`，`scratch=8`，均为只读元数据扫描并排除 `.git` 对象 | PCR02 source roots | Source metadata | `knowledge-hub-source-coverage-closeout-20260620` |
| `rtk bash -lc 'base=~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo; find "$base" -maxdepth 3 -name AGENTS.md -type f ...'` | 0 | module AGENTS、`.vscode/codex-tasks-sync.sh`、`.kilo/*` 和 root loose artifacts 均只读确认存在 | PCR02 project root | Source metadata | `knowledge-hub-source-coverage-closeout-20260620` |
| `subagent: PCR02-SCAN-A` | 0 | 只读扫描 tools/knowledge/app_product_test，输出 terminal classification、risk、owner/check 建议 | 本会话子代理回执 | Subagent | `knowledge-hub-source-coverage-closeout-20260620` |
| `subagent: PCR02-SCAN-B` | 0 | 只读扫描 scratch/root artifacts/module AGENTS/agent config，建议 root artifacts 采用 adjusted view | 本会话子代理回执 | Subagent | `knowledge-hub-source-coverage-closeout-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 30 个回归场景通过，包含 `pcr02-level2-source-coverage` | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-source-coverage-closeout-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 最新 source coverage JSONL 覆盖 13/13 registered sources，0 errors / 0 warnings | `tools/knowledge-check.sh` | Knowledge Hub | `knowledge-hub-source-coverage-closeout-20260620` |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-20`
- review_status：`source-coverage-closeout-level2-applied`
- 下一步：对 `pcr02-project-knowledge` 做 secret-boundary/owner review 包；或对 `pcr02-product-test` 的 PDF/zip/tgz/config/C/C++ 生成 artifact/config/interface reference 清单。
