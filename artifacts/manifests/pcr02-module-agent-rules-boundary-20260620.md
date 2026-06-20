# PCR02 module agent rules boundary 2026-06-20

## 结论

`pcr02-module-agent-rules` 已完成当前只读复扫。所有发现的 `AGENTS.md` 只能作为 PCR02 project/module/local rule reference；未取得人工 owner decision 前，不复制正文、不提升为 Knowledge Hub 根规则或团队标准、不关闭 owner gate。

## 范围

- Source ID: `pcr02-module-agent-rules`
- Source root: `/home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo`
- 当前复扫发现：8 个 `AGENTS.md`。
- 历史 closeout 记录：target module AGENTS=6，additional observed in `modules/api`、`modules/app`、`modules/hdi`。
- 当前复扫未发现 `modules/**/AGENTS.md`，需作为历史证据差异记录，不能登记不存在路径为 active。

## 分类清单

| 路径或模式 | 分类 | 决策 | 风险 |
|---|---|---|---|
| `AGENTS.md` | `root-agent-not-observed` | `not-observed-current-scan` | 当前根目录未发现；不得从子目录规则反推根规则。 |
| `cli/AGENTS.md` | `module-local-owner-gated-control-entry-rule` | `reference-only-pending-owner` | 仅限 `cli` 模块；需 CLI owner、适用版本、review cycle。 |
| `cmd_server/AGENTS.md` | `module-local-owner-gated-routing-rule` | `reference-only-pending-owner` | 仅限 `cmd_server`；需协议/路由边界 owner 确认。 |
| `daemon/AGENTS.md` | `module-local-owner-gated-daemon-rule` | `reference-only-pending-owner` | 仅限 `daemon`；不得扩展为全项目规则。 |
| `docs/AGENTS.md` | `project-local-owner-gated-docs-rule` | `reference-first-pending-owner` | 项目文档规则需 docs owner 和生命周期确认。 |
| `tools/AGENTS.md` | `project-local-owner-gated-tool-wrapper-rule` | `tool-ref-owner-gated` | 不执行脚本，不复制通用工具实现，不写 memory。 |
| `knowledge/AGENTS.md` | `legacy-team-knowledge-owner-gated-rule-reference` | `reference-first-pending-owner` | legacy/team knowledge SSOT 需与当前 Knowledge Hub 规则隔离。 |
| `knowledge/docs/AGENTS.md` | `knowledge-docs-local-owner-gated-rule` | `reference-only-pending-owner` | 嵌套 local rule，不能提升为 Knowledge Hub 规则。 |
| `knowledge/tools/AGENTS.md` | `knowledge-tools-local-owner-gated-rule` | `tool-ref-or-reference-only` | 不执行工具，不复制脚本正文，不启用写操作。 |
| `modules/**/AGENTS.md` | `prior-evidence-not-observed-current-scan` | `owner-verify-path-list` | 历史 closeout 与当前复扫不一致；不得登记为 active。 |

## 控制规则

| 规则 | 状态 |
|---|---|
| AGENTS/local rules 默认 owner-gated | enforced-by-boundary |
| 只作为 project/module-local rule reference | enforced-by-boundary |
| 不复制规则正文 | enforced-by-boundary |
| 不提升到 Knowledge Hub 根规则或 `domains/embedded/standards/` | enforced-by-boundary |
| 历史 AGENTS 路径差异需 owner/maintainer 复核 | owner-gated |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| subagent `PCR02-MODULE-AGENTS-BOUNDARY` | 0 | 当前复扫发现 8 个 AGENTS；未发现 `modules/**/AGENTS.md`；确认只能 owner-gated reference | `pcr02-module-agent-rules` | Subagent evidence | `pcr02-module-agent-rules-boundary-20260620` |
| `rtk bash -lc 'base=...; find "$base" ... -name AGENTS.md ...'` | 0 | 主线程复核 8 个 AGENTS 路径 | `pcr02-module-agent-rules` | Source scan | `pcr02-module-agent-rules-boundary-20260620` |

## 未决项

- owner 需要确认各 AGENTS 当前有效性、适用模块、review cycle、维护 owner。
- 需要复核历史 closeout 提到的 `modules/api/app/hdi` AGENTS 是旧工作树、旧扫描口径、已删除路径，还是记录误差。
- `knowledge/docs/AGENTS.md` 与 `knowledge/tools/AGENTS.md` 可后续考虑归入 `pcr02-project-knowledge` source，但本轮只登记边界。
