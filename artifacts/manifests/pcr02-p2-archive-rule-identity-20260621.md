# PCR02 P2 archive/rule identity 2026-06-21

## 结论

本轮为 PCR02 Level 2 中仍缺逐文件身份的小型 P2 source 补充只读 identity 清单：`pcr02-module-agent-rules` 和 `pcr02-project-scratch`。

该清单只登记 `source_path`、`uri`、`size`、`sha256`、分类、引用模式和禁止事项；不复制正文、不执行脚本、不修改源项目、不生成 owner decision、不关闭 owner gate、不写 memory。

## 范围

| Source ID | Source root | 登记文件数 | 边界 |
|---|---|---:|---|
| `pcr02-module-agent-rules` | `/home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo` | 8 | 覆盖当前复扫存在的 module/project/local `AGENTS.md`；只作为 owner-gated rule reference。 |
| `pcr02-project-scratch` | `/home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/scratch` | 8 | 覆盖 scratch 下 8 个 Markdown session/context/resume 文件；全部 archive-only，不进入 active facts。 |

## 控制规则

| 规则 | 状态 |
|---|---|
| 不复制 source 正文 | enforced-by-identity |
| 不修改源项目 | enforced-by-identity |
| `AGENTS.md` / local rules 只做 owner-gated reference | enforced-by-boundary |
| scratch session/context/resume 只做 archive-only | enforced-by-boundary |
| memory candidates 不写 `~/.codex/memories` | enforced-by-boundary |
| 抽取 active fact、runbook、decision 或团队规则前必须 owner review | owner-review-required |
| PCR02 project-specific 内容不提升到 `domains/embedded/standards/` | enforced-by-boundary |

## 与既有边界的关系

- `pcr02-module-agent-rules-boundary-20260620` 和 `pcr02-scratch-archive-boundary-20260620` 继续作为分类边界。
- 本清单只补可恢复身份：文件路径、大小、hash、引用模式和 `must_not`。
- `pcr02-project-tools/tools/AGENTS.md` 已在 P1 tools identity 中登记；本清单再次在 `pcr02-module-agent-rules` source 视角登记同一文件的规则身份，不复制正文。
- 历史 closeout 提到但当前复扫不存在的 `modules/**/AGENTS.md` 不登记为 active identity。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk python3 -c '... hashlib ... module AGENTS and scratch markdown ...'` | 0 | 只读计算 8 个 AGENTS 与 8 个 scratch Markdown 的 `size` / `sha256`；未复制正文进入 Knowledge Hub | source filesystem metadata | Source identity | `pcr02-p2-archive-rule-identity-20260621` |
| `rtk sed -n '1,220p' artifacts/manifests/pcr02-module-agent-rules-boundary-20260620.md` | 0 | 复核 module/local AGENTS 只能 owner-gated reference，不提升 Knowledge Hub 根规则 | `artifacts/manifests/pcr02-module-agent-rules-boundary-20260620.md` | Boundary evidence | `pcr02-p2-archive-rule-identity-20260621` |
| `rtk sed -n '1,220p' artifacts/manifests/pcr02-scratch-archive-boundary-20260620.md` | 0 | 复核 scratch 只能 archive-only，不进入 active facts，不写 memory | `artifacts/manifests/pcr02-scratch-archive-boundary-20260620.md` | Boundary evidence | `pcr02-p2-archive-rule-identity-20260621` |

## 下一步

- 若 owner 后续要求处理 module AGENTS，必须先确认真实 owner、适用模块、当前有效性、review cycle 和 target decision。
- 若 owner 后续要求从 scratch 抽取长期知识，需单独建立 owner-review 条目，明确抽取字段和落点；不得复制整篇 session/handoff 为 current fact。
- owner decision 未提供前，final gate 仍应停在 `needs-owner-review`，且唯一 blocker 应为 `owner-gates-open`。
