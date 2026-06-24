# PCR02 DVR 与电机 MCU 收口目标 - 2026-06-18

## 摘要

本 manifest 固化 PCR02 剩余 review-required 项中的 DVR plan、DVR session archive 和电机 MCU debug record 的终态治理边界。它不是正文迁移结果，不创建 active 项目事实，不复制源文档正文，也不把 PCR02 项目设计提升到团队级 `domains/embedded/standards/`。

本轮使用 3 个只读子代理并行复核：

- DVR plan 状态复核：建议 plan 本体走 `completed`，但必须通过 owner gate。
- 电机 MCU 事实边界复核：建议默认 `archive-only`，只有补齐 owner evidence 且保留 open items 后才可作为 `validation-report-candidate`。
- DVR session archive 归档复核：必须维持 `archive-only`，其中 memory candidates 和 handoff/worktree notes 不得进入 active facts。

## Scope

- Source id: `pcr02-project-docs`
- Source root: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs`
- Baseline package: `artifacts/manifests/pcr02-owner-review-package-20260618.md`
- Follow-up package: `artifacts/manifests/pcr02-owner-review-follow-up-20260618.md`
- Owner worksheet: `artifacts/manifests/pcr02-owner-decision-worksheets-20260618.md`

| Row | Source path | Source sha256 | Size | 收口建议 |
| --- | --- | --- | --- | --- |
| `pcr02-owner-review-005` | `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md` | `9134247182e7578eec8c2bb4d702ffaed6c75359039d549b679f058bf8532cb3` | `4786` | owner gate 后 `completed` 优先；若 owner 面向当前 checkout 验收则仍可能 `active`。 |
| `pcr02-owner-review-006` | `reports/2026-05-29-motor-mcu-debug-record.md` | `2ebdb26b56f3bd7a3561fd4f6a0aaf05389044e34530a10743d4032434fde734` | `13646` | 默认 `archive-only`；补齐证据后可成为 `validation-report-candidate`。 |
| `pcr02-owner-review-007` | `reports/2026-06-16-dvr-record-replay-session-archive.md` | `266a1c2706da87b39d9e4b204ccece61b0ec9c7a95183c64324e95f606c1dadc` | `6697` | `archive-only`。 |

## 终态结论

| 条目 | 当前 row 状态 | registry 状态 | 终态目标 | 不做动作 |
| --- | --- | --- | --- | --- |
| DVR plan | `blocked-pending-owner-status-decision` | `reviewing` | 等 owner 确认三仓分支/提交和验证证据后，优先将 plan 状态收口为 `completed`。 | 不把计划中的命令文本当作已通过验证；不把当前 checkout 误写成已完成。 |
| 电机 MCU debug record | `blocked-pending-owner-review` | `reviewing` | 先保留 archive-only 边界；owner 补齐证据后再拆成 validation report candidate。 | 不把现场反馈和推断写成已验证根因；不关闭 open items。 |
| DVR session archive | `blocked-pending-archive-metadata` | `reviewing` | 整份材料只作为 archive-only；只允许 owner review 后抽取 validation/decision/risk 子片段。 | 不复制整篇到 current；不写 memory；不把 handoff/worktree notes 作为 active facts。 |

## DVR plan 收口边界

建议状态：`completed`，但必须加 owner gate。

### Verified facts

- 源 plan 存在，hash 和 size 已与 owner worksheet 对齐。
- 源 plan 声明范围是 DVR record/replay 控制链路从 api timing 轮询解耦到 proto + sensor 控制消息。
- owner follow-up 已要求优先考虑 `completed` 或 `superseded`，`active` 只能在 owner 确认该计划仍是当前执行基线时保留。
- 子代理只读复核确认 `dev/dvr_record_replay` 三仓分支存在目标提交和目标符号：
  - 根应用仓 `dev/dvr_record_replay`: `02b7383c feat(dvr): add DVR record and replay control messages`
  - `modules/api` `dev/dvr_record_replay`: `cad7d30 refactor(api_dvr): remove event timing infrastructure and simplify record event handling`
  - `modules/sensor` `dev/dvr_record_replay`: `56e0f51 feat(hardware): add DVR record and replay APIs`
- 当前 checkout 不是上述实现态：根仓为 `dev/pcr02`，`modules/api` 和 `modules/sensor` 为 `master`。

### Inference

- 该 plan 很可能已在专门的 `dev/dvr_record_replay` 三仓分支上实现过。
- 如果 owner 接受上述三仓分支/提交作为最终交付基线，并补充实际验证结果，plan 可收口为 `completed`。
- 如果 owner 面向当前 checkout 验收，DVR 解耦目标不能声明完成。

### Owner gate

owner 必须补齐：

- 唯一状态：`completed`、`active` 或 `superseded`。
- 最终基线：branch / commit / tag 是否为 `dev/dvr_record_replay` + `02b7383c` / `cad7d30` / `56e0f51`。
- 实际 proto generation、build、API DVR refcount 和 targeted grep 结果。
- `task/iot` 接入状态和责任 owner。
- replay data channel 是已接入、占位还是后续任务。
- `LIST_FETCH` 128 条限制是否可接受，或是否扩展分页/limit 契约。
- `RecordSetEvent` active event update 语义是否批准为 PCR02 project contract。

### Must not

- 不使用 `local-codex` 作为长期 owner。
- 不把源 plan 的 `status: active` 当作 Knowledge Hub active 状态。
- 不把 planned commands 或 session archive 的文字声明直接当作当前源码验证结果。
- 不把 DVR 项目设计提升到 `domains/embedded/standards/`。
- 不隐藏 `task/iot`、replay data channel、`LIST_FETCH` 和 `RecordSetEvent` 的开放项。

## 电机 MCU debug record 收口边界

建议状态：默认 `archive-only`。只有 owner 补齐 evidence，并保持 open items 可见时，才可拆成 `validation-report-candidate`。

### Fact split

| 类型 | 内容 |
| --- | --- |
| Verified facts | 源记录日期为 `2026-05-29`；问题来源为 `2026-05-27` 联调/现场反馈；测试固件标签为 `0.2.0-20260527.hex`；报告列出堵转保护、低转速、Hall 异常、三相幅值差异和三相整体幅值过小等保护逻辑。 |
| Field feedback | 低速/回位场景停机、同电流扭矩不一致、版本读取串口无数据、校准成功判断不足。 |
| Inference | 低速停机倾向误保护、转动异常倾向校准问题、SoC 综合决策方向。 |
| Recommendations | 异常上报字段、停机决策策略、V1-V9 验证计划、P0/P1 后续行动。 |
| Open items | `1.3A 持续 3s` 与 `持续偏大 10s` 参数冲突；缺相保护滤波和低电流噪声抑制；Hall 替代判定；异常电机复测；版本读取根因；校准成功判断；SoC 异常综合决策。 |

### Owner evidence

owner 必须补齐：

- Motor MCU 或 SoC owner review。
- 固件版本引用和保护参数表，特别是 `1.3A 持续 3s` 与 `持续偏大 10s` 的最终规格。
- 串口波形、协议日志、启动日志，区分物理层无输出、协议无响应、程序未启动。
- 异常电机复测、校准前后数据、同电流/同转速对比。
- 故障码或协议字段定义，包含单位、刷新周期、持续时间和来源。
- 整机 V1-V9 或等价验证记录。

### Must not

- 不把 `0.2.0-20260527.hex` 阶段性行为写成生产策略。
- 不把“倾向校准问题”写成 root cause。
- 不隐藏参数冲突和 open items。
- 不把 motor MCU 项目局部策略提升到 team standard。
- 不把 Hall 标定、电机运动、OTA 类命令当作只读验证；这些命令需要设备安全、版本基线和 owner 授权。

## DVR session archive 收口边界

建议状态：`archive-only`。

### Required metadata

```text
status=archive-only
source_status_at_capture=active handoff
contains_memory_candidates=true
not_active_source=true
excluded_sections=["Memory Candidates","handoff/worktree cleanup notes"]
extracts_require_owner_review=true
owner=<project owner required>
reviewer=<reviewer required>
review_date=<required>
source_path=~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/reports/2026-06-16-dvr-record-replay-session-archive.md
source_sha256=266a1c2706da87b39d9e4b204ccece61b0ec9c7a95183c64324e95f606c1dadc
source_size_bytes=6697
evidence_refs=<branch/commit/validation refs required>
```

### Allowed extracts

仅在 owner review 后允许抽取：

- Validation extract：只抽取命令结果、分支/commit refs 和可复现证据。
- Decision extract：只抽取 owner 已确认的 DVR 生命周期和接口语义。
- Risk extract：可以保留 `task/iot`、replay data channel、`LIST_FETCH` 和 `RecordSetEvent` 风险，但不能改写成已解决事实。

### Excluded sections

必须排除：

- `Memory Candidates` 整段。
- handoff / worktree cleanup notes。
- dirty / untracked worktree 说明。
- `下一步建议` 只能作为 backlog 候选，不能直接当作已批准计划或事实。

### Must not

- 不写入 `~/.codex/memories`。
- 不把 memory candidates 提升为 active project facts。
- 不复制整份 session archive 到 current。
- 不清理、revert 或 rewrite 源 worktree。
- 不在 owner review 前抽取 decision facts。
- 不把 session handoff 或 dirty worktree notes 当作当前事实。

## Verification plan

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 DVR RecordSetEvent task iot sensor"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 motor MCU 0.2.0-20260527"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 DVR session archive memory candidates"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "memory candidates archive-only not_active_source"
rtk sha256sum ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md
rtk sha256sum ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/reports/2026-05-29-motor-mcu-debug-record.md
rtk sha256sum ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/reports/2026-06-16-dvr-record-replay-session-archive.md
rtk wc -c ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md
rtk wc -c ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/reports/2026-05-29-motor-mcu-debug-record.md
rtk wc -c ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/reports/2026-06-16-dvr-record-replay-session-archive.md
```

## Non-actions

- No source project file was edited.
- No source document body was copied into `domains/`.
- No active project fact was created.
- No PCR02 project-specific material was promoted to `domains/embedded/standards/`.
- No automation was enabled.
- No memory was written.

## Review

- owner：`leiwenjun`
- review_after：`2026-09-17`
- validation_refs：`tools/knowledge-check.sh --dry-run`
