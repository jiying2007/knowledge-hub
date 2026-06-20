# PCR02 agent config boundary 2026-06-20

## 结论

`pcr02-project-agent-config` 已完成当前只读复扫。该 source 只能保持 `config-ref + artifact-ref + report-only automation boundary + no-write + secret-scan-before-copy`。不得复制正文，不得纳入 active 团队规则，不得执行 `.vscode` task、`codex-tasks-sync.sh`、`.kilo/setup-script`、`npm`、`node` 或 `node_modules` 内容。

## 范围

- Source ID: `pcr02-project-agent-config`
- Source root: `/home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo`
- 重点路径：`.vscode/`、`.kilo/`
- 当前复扫：非 `node_modules` 顶层文件 10 个；`.kilo/node_modules` 约 58M、3426 个文件、4 个 native `.node` 二进制模块。
- 扫描边界：未打印潜在 secret 值，未执行脚本，未安装依赖，未启用自动化。

## 分类清单

| 路径或模式 | 分类 | 决策 | 风险 |
|---|---|---|---|
| `.vscode/settings.json` | `workspace-config-ref` | `config-ref` | 本地 IDE 配置，不能提升团队规则。 |
| `.vscode/tasks.json` | `vscode-task-automation-boundary` | `config-ref-report-only` | 含可触发命令；不执行，不复制命令正文。 |
| `.vscode/tasks.json.bak-20260415-190009` | `vscode-task-backup-artifact` | `artifact-ref-archive-only` | 与当前 tasks 一致；备份不应成为权威配置。 |
| `.vscode/codex-tasks-sync.sh` | `codex-task-sync-tool-ref` | `tool-ref-report-only` | 可执行脚本，可能改变源项目或本地环境。 |
| `.kilo/.gitignore` | `kilo-ignore-config-ref` | `config-ref` | agent 工具局部配置。 |
| `.kilo/agent-manager.json` | `kilo-agent-state-config` | `config-ref-owner-gated` | 可能反映本地 agent 状态，不作为团队规范。 |
| `.kilo/kilo.jsonc` | `kilo-config-ref` | `config-ref` | agent 工具配置，语义需 owner 确认。 |
| `.kilo/package.json` | `kilo-package-manifest-artifact` | `artifact-ref-supply-chain-boundary` | 声明第三方依赖，不触发安装。 |
| `.kilo/package-lock.json` | `kilo-lockfile-artifact` | `artifact-ref-supply-chain-boundary` | 可用于审计，不是知识正文。 |
| `.kilo/setup-script` | `kilo-setup-tool-ref` | `prohibited-by-default-automation` | setup 类脚本默认禁用，隔离审计前不得执行。 |
| `.kilo/node_modules/` | `third-party-dependency-artifact` | `artifact-ref-only` | 大型第三方依赖和 native binary，不进入文本知识层。 |

## 控制规则

| 规则 | 状态 |
|---|---|
| `.vscode` task 和 `.kilo` setup 不执行 | enforced-by-boundary |
| 自动化默认 report-only / no-write | enforced-by-boundary |
| `node_modules` 不复制正文、不执行 | enforced-by-boundary |
| 复制摘要或登记更多元数据前需 secret scan | owner-gated |
| 吸收依赖或工具链前需供应链审查 | owner-gated |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| subagent `PCR02-AGENT-CONFIG-BOUNDARY` | 0 | 只读复扫确认 `.vscode`/`.kilo` 顶层配置、`.kilo/node_modules` 大型依赖和 4 个 native `.node` 边界 | `pcr02-project-agent-config` | Subagent evidence | `pcr02-agent-config-boundary-20260620` |
| `rtk bash -lc 'base=...; for d in .vscode .kilo; find ...'` | 0 | 主线程复核 `.vscode`、`.kilo` 路径；发现 node_modules 需排除逐文件展开 | `pcr02-project-agent-config` | Source scan | `pcr02-agent-config-boundary-20260620` |

## 未决项

- owner 需要明确哪些配置可作为引用，哪些必须排除。
- 若后续要启用任何 agent automation，必须先补命令审查、secret scan、供应链审查、deny-path、日志脱敏、rollback 和 report-only gate。
