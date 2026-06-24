# PCR02 tools boundary 2026-06-20

## 结论

`pcr02-project-tools` 已完成只读边界复核。该目录是 PCR02 项目本地工具入口，不是长期知识正文来源。后续只允许按 `reference-first`、`tool-ref`、`validation-tool-ref`、`artifact-ref` 或 `excluded` 登记；不得复制脚本正文，不得自动执行脚本，不得把 memory automation 当成已放行自动化。

## 范围

- Source ID: `pcr02-project-tools`
- Source root: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/tools`
- 扫描方式：只读路径与小范围 Markdown 摘要复核；未运行任何源项目脚本。
- 覆盖文件数：19 个文件。
- 主要类型：Markdown 3、shell 3、Python 10、CSV 2、生成型 pyc 1。

## 分类清单

| 路径或模式 | 分类 | 决策 | 风险与后续 |
|---|---|---|---|
| `README.md` | `project-tool-index-ref` | `reference-first` | 只作为工具入口引用；owner 确认后可补中文摘要，不复制全文。 |
| `AGENTS.md` | `project-tool-rules-ref` | `owner-gated reference-first` | 仅是项目本地工具规则，不提升到团队标准。 |
| `debug/README.md` | `debug-tool-doc-ref` | `reference-first` | 记录工具说明边界；检查外部公共工具链接是否仍有效。 |
| `debug/project-knowledge-debug.sh` | `project-debug-wrapper-ref` | `tool-ref` | 运行会调用外部工具链；只能人工触发，不自动运行。 |
| `diag/diag-auto-run.sh` | `diag-runner-ref` | `validation-tool-ref` | 运行会产生日志和 summary artifact；默认不执行、不写源项目。 |
| `diag/checks/*.py` | `diag-static-check-ref` | `validation-check-ref` | 可登记检查集合、输入范围和失败语义；不复制源码正文。 |
| `diag/diag-case-matrix.csv` | `diag-case-matrix-artifact-ref` | `validation-matrix-ref` | 保留 source identity；active/candidate 状态需要 owner 复核。 |
| `diag/diag-interface-coverage.csv` | `diag-interface-coverage-artifact-ref` | `validation-coverage-ref` | 保留 source identity；coverage 有效性需要 owner 复核。 |
| `listen_bridge_heartbeat.py` | `bridge-heartbeat-listener-ref` | `runtime-diagnostic-tool-ref` | 运行态诊断辅助脚本；可能发送 ack，只能人工批准运行。 |
| `memory/memory-curator-auto.sh` | `memory-candidate-automation-ref` | `owner-gated report-only` | 最高风险项；必须标记 `no-active-memory-write`、`human-review-required`，不得默认启用。 |
| `__pycache__/*.pyc` | `binary-cache-generated` | `generated-artifact-exclude` | 生成型缓存，不进入文本知识层。 |

## 控制规则

| 规则 | 状态 |
|---|---|
| 不复制工具脚本正文 | enforced-by-boundary |
| 不自动运行 PCR02 tools 脚本 | enforced-by-boundary |
| memory automation 默认 report-only | owner-gated |
| 不写 `~/.codex/memories` | enforced-by-boundary |
| 不提升 PCR02 tool rules 到 `domains/embedded/standards/` | enforced-by-boundary |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -lc 'base=.../tools; find "$base" ...'` | 0 | 列出 19 个工具侧文件；确认无大型制品，发现 `README.md`、`AGENTS.md`、diag、debug、memory、pyc 边界 | `pcr02-project-tools` | Source scan | `pcr02-tools-boundary-20260620` |
| subagent `PCR02-TOOLS-BOUNDARY` | 0 | 只读扫描完成；确认 memory automation 是最高风险 owner-gated 边界 | `pcr02-project-tools` | Subagent evidence | `pcr02-tools-boundary-20260620` |

## 未决项

- owner 需要确认 `tools/AGENTS.md` 是否只保持 reference-first，或是否提取项目本地摘要。
- owner 需要确认 diag CSV 中 `active` / `candidate` 状态是否仍有效。
- memory automation 后续若进入工具链，必须先有 report-only manifest、deny-path、日志脱敏和 no-active-memory-write gate。
