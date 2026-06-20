# PCR02 knowledge secret/config boundary 2026-06-20

## 结论

`pcr02-project-knowledge` 已完成只读边界复核。该目录包含 PCR02 本地知识库、治理脚本、项目本地规则、runbook、standards-like 文档、技能资产和环境配置。当前只能建立分类与风险边界；不得直接把 `docs/standards/*` 提升为团队标准，不得复制 `.env` 正文，不得导入 `.codex/skills` 为 live Codex 资产。

## 范围

- Source ID: `pcr02-project-knowledge`
- Source root: `/home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/knowledge`
- 扫描方式：只读路径分类；未读取 `.env` 正文，未执行源项目脚本。
- 排除 `.git` 后文件数：191。
- 主要类型：Markdown 93、shell 32、yaml 14、Python 13、pyc 13、env 2、CSV 2。

## 分类清单

| 路径或模式 | 分类 | 决策 | 风险与后续 |
|---|---|---|---|
| `profiles/pcr02.env`、`profiles/template.env` | `secret-boundary` | `excluded-or-artifact-boundary` | 不复制正文、不打印值；是否仅登记 size/hash 需 owner 决定。 |
| `scripts/check-secrets.sh` | `secret-scan-tool-ref` | `tool-ref` | 可作为源项目自带检查入口引用；本轮不执行。 |
| `.gitea/workflows/knowledge-check.yml`、`.gitlab-ci.yml`、`.githooks/pre-commit` | `source-governance-config-ref` | `config-ref` | 源项目治理配置，不等同于 Knowledge Hub 规则。 |
| `.github/PULL_REQUEST_TEMPLATE.md`、`.gitlab/merge_request_templates/knowledge.md` | `source-review-template-ref` | `reference-first` | 只记录模板存在和边界；不自动提升为团队模板。 |
| `AGENTS.md`、`docs/AGENTS.md`、`tools/AGENTS.md`、`CODEOWNERS`、`OWNERS.md` | `owner-gated-rule-reference` | `owner-gated reference-first` | 仅作为 project-local/module-local 规则引用。 |
| `docs/architecture/*.md` | `architecture-migration-candidate` | `classify-first` | 可迁移候选；默认进入 PCR02 project scope，需 owner 指定 disposition。 |
| `docs/runbooks/*.md` | `runbook-migration-candidate` | `classify-first` | 可迁移候选；需去重、确认 owner、scope、review_after。 |
| `docs/standards/*.md` | `project-local-standard-candidate` | `owner-gated no-embedded-promotion` | 名称像 standards，但当前是 PCR02/source-local 资料；不能直接进入 `domains/embedded/standards/`。 |
| `docs/governance/*.py`、`docs/governance/tests/*.py` | `validation-tool-ref` | `tool-ref` | 可登记用途、输入和失败语义；不复制源码正文。 |
| `docs/archive/sigmastar/manifest.*`、`docs/governance/knowledge-repo-migration-map.csv` | `archive-governance-ref` | `artifact-ref` | 作为归档治理证据；是否迁移正文需 owner/review。 |
| `docs/governance/**/__pycache__/*.pyc` | `generated-artifact-boundary` | `excluded` | 生成物不得进入文本知识层。 |
| `docs/.codex/skills/**`、`tools/.codex/skills/**` | `skill-asset-ref` | `supply-chain-review-required` | 只能作为技能资产引用；启用或导入前需安全和供应链审查。 |
| `tools/debug/*.sh`、`tools/sigmastar/archive_sigdoc_artifact.sh` | `diagnostic-tool-ref` | `tool-ref` | 只作为工具入口候选；运行需人工触发。 |

## 控制规则

| 规则 | 状态 |
|---|---|
| `.env` 只登记边界，不复制正文 | enforced-by-boundary |
| `docs/standards/*` 不直接提升团队标准 | enforced-by-boundary |
| `.codex/skills` 需要供应链审查 | owner-gated |
| 源项目治理脚本不自动执行 | enforced-by-boundary |
| 生成型 pyc 不进入文本知识层 | enforced-by-boundary |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -lc 'base=.../knowledge; find "$base" ... secret/config paths ...'` | 0 | 发现 `.env`、CI、skill agent yaml、secret-check 脚本等路径；未读取 secret-like 文件正文 | `pcr02-project-knowledge` | Source scan | `pcr02-knowledge-secret-config-boundary-20260620` |
| subagent `PCR02-KNOWLEDGE-BOUNDARY` | 0 | 只读扫描完成；确认 191 个文件、secret/config、project-local standards、skill assets 与 generated artifact 边界 | `pcr02-project-knowledge` | Subagent evidence | `pcr02-knowledge-secret-config-boundary-20260620` |

## 未决项

- owner 需要决定 `profiles/*.env` 是完全排除，还是仅保留 artifact-boundary 身份信息。
- owner 需要筛选哪些 `docs/runbooks`、`docs/architecture` 可进入 copy-first 或 reference-first。
- `docs/standards/*` 如需提升团队规范，必须另走 promotion manifest、owner review、secret scan 和 rollback gate。
- `.codex/skills` 若要纳入 Codex 资产链路，需要补 transport/deny-path/日志脱敏/供应链审查。
