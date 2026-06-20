# PCR02 Motor MCU Owner Ready Package - 2026-06-20

## 结论

本包把 `pcr02-owner-decision-worksheet-006` 单独收口成 owner 可签收材料。它只服务 PCR02 docs `reports/2026-05-29-motor-mcu-debug-record.md` 这一条 owner gate：

- 不复制源 debug record 正文。
- 不修改源项目 docs。
- 不生成 owner decision。
- 不关闭 owner gate。
- 不创建 validation report。
- 不创建 decision fact。
- 不把现场反馈或推断写成 verified root cause。
- 不把 `0.2.0-20260527.hex` 阶段固件行为写成生产策略。
- 不隐藏 `1.3A for 3s` vs `10s` 等未决冲突。
- 不把 motor MCU 项目局部策略提升到团队标准。
- 不启用自动化，不写 `~/.codex/memories`。

当前状态仍为 `owner-fill-required`，最终门禁仍预期是 `needs-owner-review`，直到 owner 明确填写并验证通过。

## Source Identity

| 字段 | 值 |
| --- | --- |
| source_id | `pcr02-project-docs` |
| source_path | `reports/2026-05-29-motor-mcu-debug-record.md` |
| worksheet_id | `pcr02-owner-decision-worksheet-006` |
| owner | `motor-mcu-or-soc-owner` |
| observed_sha256 | `2ebdb26b56f3bd7a3561fd4f6a0aaf05389044e34530a10743d4032434fde734` |
| observed_size | `13646` |
| identity_status | `match` |

`observed_sha256` 和 `observed_size` 只是只读提示，不能自动替代 owner 在签收 JSONL 中显式填写的 `source_sha256` 和 `source_size`。

## Owner 只需回答的问题

请 owner 对以下问题给出唯一结论：

> 是否只按 archive-only 保留，还是补齐固件版本、保护参数、波形/协议日志、复测、校准前后、整机验证后再考虑 validation-report-candidate？

允许的 `owner_decision` 只有：

| owner_decision | 含义 | 允许 target_decision |
| --- | --- | --- |
| `archive-only` | 只作为历史调试记录保留，不进入 validation/current/decision。 | `archive-only` |
| `validation-report-candidate` | owner 确认可作为 validation report 候选，但必须先补齐证据并保留 open items。 | `validation-report-candidate-pending-verification` |

## 必填字段

owner decision JSONL 必须填写：

- `owner_decision`
- `target_decision`
- `reviewed_by`
- `reviewed_at`
- `review_after`
- `source_status`
- `source_sha256`
- `source_size`
- `firmware_version_refs`
- `protection_parameter_table`
- `serial_waveform_or_protocol_logs`
- `hardware_start_evidence`
- `field_retest_records`
- `calibration_before_after_data`
- `fault_code_or_protocol_field_definitions`
- `whole_device_validation_records`
- `unresolved_items_acknowledgement`
- `evidence_refs`
- `status_reason`

## Fact Boundary

本包只固定分类边界，不确认源记录中的结论为真。

| 类型 | 允许进入签收表的含义 | 不能做的事 |
| --- | --- | --- |
| Verified facts | 记录日期、问题来源、测试固件标签、报告列出的保护逻辑和已列出的 open items。 | 不能把这些事实扩展为生产策略。 |
| Field feedback | 低速/回位停机、同电流扭矩不一致、版本读取串口无数据、校准成功判断不足。 | 不能写成 root cause。 |
| Inference | 低速停机倾向误保护、转动异常倾向校准问题、SoC 综合决策方向。 | 不能写成已验证结论。 |
| Recommendations | 异常上报字段、停机决策策略、V1-V9 验证计划、P0/P1 后续行动。 | 不能写成已批准实现或生产默认策略。 |
| Open items | 参数冲突、缺相滤波、Hall 替代条件、异常电机复测、版本读取根因、校准合理性、SoC 策略实现。 | 不能删除、隐藏或默认关闭。 |

## Owner Evidence Gate

若 owner 选择 `validation-report-candidate`，必须先补齐：

- Motor MCU 或 SoC owner review。
- 固件版本引用。
- 保护参数表，特别是 `1.3A 持续 3s` 与 `持续偏大 10s` 的最终规格。
- 串口波形、协议日志或启动日志，能区分物理层无输出、协议无响应、程序未启动。
- 异常电机复测记录。
- 校准前后数据。
- 同电流/同转速对比。
- 故障码或协议字段定义，包含单位、刷新周期、持续时间和来源。
- 整机 V1-V9 或等价验证记录。
- 未决项确认，不得删除或静默关闭。

## Hard Gate

以下任一条件出现时，不能越过 owner gate：

- 推断被写成 verified root cause。
- 现场反馈被写成已验证根因。
- `0.2.0-20260527.hex` 阶段行为被写成生产策略。
- `1.3A for 3s` vs `10s` 参数冲突被隐藏。
- 缺少固件版本或保护参数表却进入 validation report。
- 缺少串口/协议日志却确认版本读取根因。
- 缺少异常电机复测或校准前后数据却确认校准根因。
- 缺少故障码/协议字段定义却固化 SoC 异常综合决策。
- open items 被删除、关闭或省略。
- motor MCU 项目局部策略被提升到团队标准。
- Hall 标定、电机运动、OTA 类设备动作命令被当成只读验证。

## Copyable Owner Decision Skeleton

以下 JSON 只能由 owner 填写空字段后作为单行 JSONL 使用。不要把它当作已签收结果。

```json
{"worksheet_id":"pcr02-owner-decision-worksheet-006","source_id":"pcr02-project-docs","source_path":"reports/2026-05-29-motor-mcu-debug-record.md","worksheet":"artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl","owner":"motor-mcu-or-soc-owner","status":"open","worksheet_status":"owner-fill-required","owner_question_zh":"是否只按 archive-only 保留，还是补齐固件版本、保护参数、波形/协议日志、复测、校准前后、整机验证后再考虑 validation-report-candidate？","default_state":"archive-only","allowed_owner_decisions":["archive-only","validation-report-candidate"],"must_not":["do not promote inference or suggested strategy as verified fact","do not treat 0.2.0-20260527.hex behavior as production policy","do not delete or hide open issues","do not promote motor MCU local strategy to team standard"],"owner_decision":"","target_decision":"","reviewed_by":"","reviewed_at":"","review_after":"2026-09-17","source_status":"","source_sha256":"","source_size":"","firmware_version_refs":[],"protection_parameter_table":"","serial_waveform_or_protocol_logs":"","hardware_start_evidence":"","field_retest_records":"","calibration_before_after_data":"","fault_code_or_protocol_field_definitions":"","whole_device_validation_records":"","unresolved_items_acknowledgement":"","evidence_refs":[],"status_reason":""}
```

## 验证和落地顺序

1. Owner 填写 JSONL 后，先只读校验：

```bash
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --json
```

2. 校验通过后，生成只读落地计划：

```bash
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-plan --json
```

3. 只按 landing plan 手工更新 Knowledge Hub，不修改源项目 docs，不把 inference 写成 fact，不关闭 open items。

4. 手工落地后至少运行：

```bash
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash tools/knowledge-regression.sh --json
rtk bash tools/knowledge-final-gate.sh --json
```

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-006 --checklist --forms` | 0 | 单条 checklist 和 form 可生成；`open_count=1`，`resolved_count=0`，`active_exposure_count=0`；source identity 为 match；owner fields 保持空白。 | `tools/knowledge-owner-gates.sh` | Owner gate | `pcr02-motor-mcu-owner-ready-package-20260620` |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-006 --forms --json` | 0 | JSON form 聚焦 worksheet-006；`owner_decision` 为空，allowed decisions 与 worksheet 一致；`open_count=1`，`resolved_count=0`，`active_exposure_count=0`。 | `tools/knowledge-owner-gates.sh` | Owner gate | `pcr02-motor-mcu-owner-ready-package-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | `status=pass`，`errors=[]`，`warnings=[]`。 | `tools/knowledge-check.sh` | Knowledge Hub | `pcr02-motor-mcu-owner-ready-package-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --explain pcr02-motor-mcu-owner-ready-package-20260620` | 0 | registry item 存在，artifact path 存在，owner/review-date/status core indexes 均命中。 | `tools/knowledge-check.sh` | Knowledge Hub | `pcr02-motor-mcu-owner-ready-package-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 20 个回归场景通过，`kept_temp=false`。 | `tools/knowledge-regression.sh` | Regression | `pcr02-motor-mcu-owner-ready-package-20260620` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 预期返回 `needs-owner-review`；knowledge-check 与 regression 均 pass；全仓 final gate 阻塞项为 7 个 open owner gates，其中 worksheet-006 仍 open；这是 owner-review 语义门禁，不是工具失败。 | `tools/knowledge-final-gate.sh` | Final gate | `pcr02-motor-mcu-owner-ready-package-20260620` |

## 非目标

- 不把源 record 迁移到 `domains/projects/pcr02/validation/reports/`。
- 不创建 motor MCU decision。
- 不确认 root cause。
- 不变更 worksheet 状态。
- 不修改 `registry/items.jsonl` 中既有 DVR/motor closeout 目标条目的状态。
