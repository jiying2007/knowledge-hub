# PCR02 scratch archive boundary 2026-06-20

## 结论

`pcr02-project-scratch` 已完成当前只读复扫。该 source 只能作为历史证据、session wrap、context preflight 或 handoff 参考；不得进入 active facts，不得写 memory，不得把历史排障过程提升为团队规则或当前 runbook。

## 范围

- Source ID: `pcr02-project-scratch`
- Source root: `/home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/scratch`
- 当前复扫：8 个 Markdown，均为 session/context 类材料。
- 扫描边界：只读路径与关键词路径级扫描；未复制正文，未写 memory，未修改源项目。

## 分类清单

| 路径 | 分类 | 决策 | 风险 |
|---|---|---|---|
| `2026-05-10-diag-v4-hybrid-refcount-session-wrap.md` | `historical-session-evidence` | `archive-only` | 可作历史排障线索，不能直接成为 active fact。 |
| `2026-05-10-v4-session-resume.md` | `handoff-reference` | `archive-only` | resume/handoff 容易被误当当前状态。 |
| `20260510-142633-context-preflight.md` | `context-state-reference` | `archive-only` | 上下文快照不能作为当前事实或规则。 |
| `20260510-204521-context-preflight.md` | `context-state-reference` | `archive-only` | 上下文快照不能作为当前事实或规则。 |
| `20260515-142032-context-preflight.md` | `context-state-reference` | `archive-only` | 上下文快照不能作为当前事实或规则。 |
| `20260515-154613-context-preflight.md` | `context-state-reference` | `archive-only` | 上下文快照不能作为当前事实或规则。 |
| `20260515-session-wrap-core-debug-and-busybox-tools.md` | `historical-session-evidence` | `archive-only` | 历史命令和排障过程只能引用，不复制为规范。 |
| `20260515-session-wrap-crash-debug-tools.md` | `historical-session-evidence` | `archive-only` | 可作历史证据，不能提升为当前 runbook。 |

## 控制规则

| 规则 | 状态 |
|---|---|
| scratch Markdown 不复制为 active knowledge | enforced-by-boundary |
| session/context/resume 不进入 active facts | enforced-by-boundary |
| memory candidates 不写 `~/.codex/memories` | enforced-by-boundary |
| 抽取当前事实、runbook、规则或决策前必须 owner review | owner-gated |
| PCR02 project-specific 内容不提升团队标准 | enforced-by-boundary |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| subagent `PCR02-SCRATCH-BOUNDARY` | 0 | 只读扫描确认 8 个 Markdown、session-name 4、context-name 4、handoff-content paths 5、memory-candidate paths 0 | `pcr02-project-scratch` | Subagent evidence | `pcr02-scratch-archive-boundary-20260620` |
| `rtk bash -lc 'base=.../scratch; find "$base" ...'` | 0 | 主线程复核 scratch 文件列表；8 个 Markdown，无非 Markdown | `pcr02-project-scratch` | Source scan | `pcr02-scratch-archive-boundary-20260620` |

## 未决项

- 若未来要从某个 scratch 文件抽取长期知识，需单独建立 owner-review 条目，明确 source path、source identity、抽取字段、landing 位置和不复制正文边界。
