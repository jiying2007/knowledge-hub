# PCR02 Owner Source Identity Preflight - 2026-06-18

## 摘要

本 preflight package 只核验 PCR02 docs governance 剩余 7 个 owner-gated 源文件的当前身份是否仍匹配 owner worksheet 中记录的 expected SHA256 和 size。它不代表 owner 决策已完成，不解除任何 blocker，不创建 active/current 项目事实。

当前结论：

- 7 / 7 源文件存在。
- 7 / 7 当前 SHA256 与 worksheet expected SHA256 一致。
- 7 / 7 当前 size 与 worksheet expected size 一致。
- `identity_status` 全部为 `match`。
- 负向缺失路径检查可失败，说明缺失文件路径不会被误判为存在。

## 核验范围

- Source id：`pcr02-project-docs`
- Source root：`~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs`
- Expected source：`artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl`
- Machine-readable result：`artifacts/manifests/pcr02-owner-source-identity-preflight-20260618.jsonl`
- Review after：`2026-09-17`

## 核验结果

| Source path | Expected size | Actual size | Identity status |
| --- | ---: | ---: | --- |
| `AGENTS.md` | 2414 | 2414 | `match` |
| `standards/diag-command-metadata-standard.md` | 5316 | 5316 | `match` |
| `runbooks/asan-debug-guide.md` | 4736 | 4736 | `match` |
| `runbooks/memory-auto-curation-guide.md` | 2060 | 2060 | `match` |
| `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md` | 4786 | 4786 | `match` |
| `reports/2026-05-29-motor-mcu-debug-record.md` | 13646 | 13646 | `match` |
| `reports/2026-06-16-dvr-record-replay-session-archive.md` | 6697 | 6697 | `match` |

## 证据命令

```bash
rtk jq -c '{id,source_path,source_sha256_expected,source_size_expected,review_after}' artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl
rtk sha256sum ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/AGENTS.md ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/standards/diag-command-metadata-standard.md ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/runbooks/asan-debug-guide.md ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/runbooks/memory-auto-curation-guide.md ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/reports/2026-05-29-motor-mcu-debug-record.md ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/reports/2026-06-16-dvr-record-replay-session-archive.md
rtk wc -c ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/AGENTS.md ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/standards/diag-command-metadata-standard.md ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/runbooks/asan-debug-guide.md ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/runbooks/memory-auto-curation-guide.md ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/reports/2026-05-29-motor-mcu-debug-record.md ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/reports/2026-06-16-dvr-record-replay-session-archive.md
rtk bash -lc "test -f ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/reports/2026-05-29-motor-mcu-debug-record.md.missing"
```

负向检查说明：最后一条命令预期退出码为 `1`，用于证明缺失路径不会被误判为存在。

## 不代表什么

本 preflight 不证明：

- owner 已签收。
- owner gate 已 resolved。
- source 内容语义仍然有效。
- 计划命令已执行通过。
- session archive 可作为 active fact。
- memory candidates 可写入 `~/.codex/memories`。
- PCR02 project-specific 内容可提升到 `domains/embedded/standards/`。

## 后续动作

1. Owner 填写 `pcr02-owner-decision-worksheets-20260618` 时，可引用本 preflight 的 source identity 结果。
2. 如果源项目 docs 后续发生变化，必须重新计算 SHA256 和 size，并生成新的 preflight 或更新 owner worksheet。
3. 任何迁移、抽取或状态提升仍必须等待 owner decision、evidence refs、review cycle 和 knowledge-check 通过。

## Review

- owner：`leiwenjun`
- status：`reviewing`
- review_status：`source-identity-match`
- promotion：`none`
- review_after：`2026-09-17`
