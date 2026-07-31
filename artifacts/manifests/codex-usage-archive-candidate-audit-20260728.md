---
id: codex-usage-archive-candidate-audit-20260728
title: 近一个月 Codex 使用记录与可归档候选审计
kind: audit
domain: codex
path: artifacts/manifests/codex-usage-archive-candidate-audit-20260728.md
scope: team-general
visibility: team-internal
status: draft
owner: leiwenjun
source:
  type: runtime-inventory
  from: local Codex runtime metadata, rollout summaries and Knowledge Hub coverage search
review_after: '2026-08-28'
created_at: '2026-07-28'
updated_at: '2026-07-29'
promotion: none
promotion_decision: none; report-only audit, no archive candidate promotion, owner decision, memory write, source project write or remote publish
tags:
  - codex
  - usage-audit
  - archive-candidate
  - memory-curation
  - report-only
related:
  - domains/codex/README.md
  - projects/xcrz-sigmastar-demo/archive/reports/2026-07-09-codex-history-backfill-engineering-findings.md
validation_refs:
  - rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
  - rtk rg -n "近一个月 Codex 使用记录与可归档候选审计" artifacts/manifests/codex-usage-archive-candidate-audit-20260728.md
summary_zh: 审计 2026-06-28 至 2026-07-28 的本机 Codex 会话、历史输入、摘要、附件入口与 Knowledge Hub 覆盖情况；识别的 10 组项目候选已于 2026-07-29 脱敏落盘并登记为 reviewing，本文同时区分已覆盖、仅溯源和应丢弃内容。不复制 raw session，不写 memory，不提升 active。
review_status: pending
maturity: candidate
security_classification: team-internal-sanitized
primary_language: zh-CN
source_language: mixed
translation_status: summarized-in-zh-CN
terminology_status: pending-review
evidence_strength: full-runtime-metadata-inventory-plus-targeted-session-review-plus-hub-coverage-search
evidence_refs:
  - ~/.codex/session_index.jsonl
  - ~/.codex/history.jsonl
  - ~/.codex/sessions/2026/06/28
  - ~/.codex/sessions/2026/06/29
  - ~/.codex/sessions/2026/06/30
  - ~/.codex/sessions/2026/07
  - ~/.codex/memories/rollout_summaries
  - registry/items.jsonl
generated_by_ai: true
ai_role: classified
ai_model_or_tool: Codex
ai_generated_at: '2026-07-28'
human_reviewed_by:
human_reviewed_at:
review_basis:
---

# 近一个月 Codex 使用记录与可归档候选审计

## 摘要

本审计覆盖 `2026-06-28 00:00:00` 至 `2026-07-28 23:59:59`（Asia/Hong_Kong）的本机 Codex 使用记录。审计采用“全量元数据盘点、顶层会话标题与 summary 复核、高信号 raw session 定向读取、Knowledge Hub 检索去重”四层方法。

本轮识别出 10 组值得独立归档的候选，其中 4 组优先级为 P0、6 组为 P1。它们已于 `2026-07-29` 分别落入项目 debug、design 和 validation 路由，并登记为 `reviewing`。这些内容属于项目事实、调试记录、验证记录或设计契约，不适合直接写入全局 memory。已被 Hub 覆盖的结论不重复归档；附件、完整日志、core、shell snapshot、SQLite 运行库、认证文件和缓存不进入文本知识层。

本文仍是 `report-only` 审计。候选已登记但尚未获得 owner promotion，不代表 active fact、发布完成或实机验收。

## 适用范围

- 时间范围：`2026-06-28` 至 `2026-07-28`，含首尾日期。
- 运行态来源：`~/.codex/session_index.jsonl`、`history.jsonl`、`sessions/**`、`memories/rollout_summaries/**`、附件入口和 shell snapshot 清单。
- 长期覆盖来源：`registry/items.jsonl`、`domains/codex/` 和项目 current/archive/decision/validation 条目。
- 本文不复核源项目最新工作树、设备当前固件、远端分支或发布制品；候选落盘时仍须回到源项目验证。

## 来源盘点

| 来源 | 数量或规模 | 审计用途 | 长期保留策略 |
| --- | ---: | --- | --- |
| rollout session | 359 个，约 866 MiB | 全量会话边界、cwd、来源和 session id | 只作 provenance，不复制正文 |
| 直接交互 session | 188 个 | 127 个 VS Code、61 个 CLI | 从中提取可复用结论 |
| subagent session | 171 个 | 发现、测试、审查和整合过程 | 并入父任务结论，不独立归档 |
| `history.jsonl` | 1534 条输入，186 个 session | 全量用户意图和 steer 入口 | 不保存完整输入 |
| 标题索引 | 41 个近月更新顶层线程 | 主题分类与候选初筛 | 只保留候选标题和 session id |
| rollout summary | 10 个 | 2026-06-28 至 2026-06-30 的高层结论 | 与 Hub 去重后引用 |
| 附件入口 | 44 个文件 | 日志、粘贴文本和临时输入线索 | 不复制；只保留脱敏摘要 |
| shell snapshot | 8 个 | 环境恢复和运行态诊断 | 不归档 |
| 同期 Hub registry item | 187 条 | 判断是否已有 canonical 覆盖 | 65 archived、118 reviewing、3 draft、1 active |

### 主要工作域

按 rollout 的 `cwd` 聚合，使用最集中的工作域为：

1. Knowledge Hub：122 个 session。
2. PCR02/SSC305 主工程及相关工作树：合计超过 110 个 session。
3. `llm_agent` / Agent Dev Kit：68 个 session。
4. MCU 工作区：21 个 session。
5. 其他：ESP32、音频、图像和个人工具等零散会话。

这说明近月长期价值主要集中在 Knowledge Hub 治理、PCR02 设备调试、低功耗与传感器链路、MCU/SoC 协同和 Codex 工作流治理。

## 高信号发现

### P0：建议优先形成独立归档

| 候选 | 可复用结论 | 证据 | 风险 | Confidence | Write route | 下次为何有用 |
| --- | --- | --- | --- | --- | --- | --- |
| 讯飞 `libmsc.so` Lua RPC Use-After-Free core 分析 | 同步 Lua RPC 等待方提前释放 proto/同步上下文，队列消费者随后访问已释放对象；第三方库符号可信，主程序 BuildID 不匹配 | session `019f9397-6a5d-7dd0-b796-a5f9a1487b9c`；core/GDB/BuildID 定向分析 | high；不得保存 core 或完整栈，业务调用方仍待匹配构建 | high for library root cause / medium for caller | `projects/xcrz-sigmastar-demo/archive/debug/` | 后续 AI voice 随机崩溃可先核对 RPC 生命周期与 BuildID，避免误归因 glibc |
| Agora 下行音频拥塞、SHM `STARVE` 与丢尾音 | 128 深度任务队列拥塞和 4 帧 SHM ring 强制回收分别造成断续；`STREAM_END` 后过早收尾造成尾音丢失 | session `019f5b80-6445-7440-90d2-5037ca2c2ff9`；两组运行日志与源码链路 | medium；需脱敏日志并补板级复测 | high | `projects/xcrz-sigmastar-demo/archive/debug/` | 后续音频断续、丢尾音、RTC 正常但播放异常时可快速区分队列、SHM 和结束时序 |
| 扫码成功但界面未切换的跨模块状态机缺口 | WiFi 配网实际已开始，但二维码显示缺少确定的 `NETWORK_CONNECTING` 切换；sensor 只适合有限兜底，task/IOT 应负责业务编排 | session `019f2106-845d-72a2-94f9-3de0e6fbcd7a`；日志、源码、sensor 定向构建 | medium；task 无源码，最终 owner 边界尚未闭环 | high for observed gap / medium for final ownership | `projects/xcrz-sigmastar-demo/archive/debug/`，必要时关联 decision candidate | 下次“网络已连但 UI 未动”的概率性问题可按三条异步链路定位 |
| 老化健康位图与 MCU/SoC 上报超时契约 | MCU 变化触发/低频保底上报与 SoC 5 秒 stale 超时冲突；普通健康项调整到 20 秒，WiFi/IR 特殊语义不能机械统一 | session `019f6ff1-9fa8-71a1-8b2a-e8019fbf1a54`；MCU 与 `app_product_test` 跨仓核对和构建 | medium；需确认源仓提交、设备回归和特殊项边界 | high | `projects/xcrz-sigmastar-demo/decisions/` 或 `archive/design/`，关联 MCU 项目 | 后续老化假失败、健康帧节流或跨 MCU/SoC 超时变更可复用同一契约 |

### P1：建议逐条复核后归档

| 候选 | 可复用结论 | 证据 | 风险 | Confidence | Write route | 下次为何有用 |
| --- | --- | --- | --- | --- | --- | --- |
| ZMQ context 生命周期崩溃 | `ctx_t::send_command()` 在 `ctx->slots[tid]` 取 mailbox 时崩溃，优先检查 context 失效、socket 跨生命周期或 registry 复用，不应只归因 `libzmq` | session `019f217a-de44-7d63-9a26-10e51cffbcb0`；反汇编与源码只读分析 | high；缺 core、寄存器和设备 BuildID，结论是高质量推断而非最终根因 | medium | `projects/xcrz-sigmastar-demo/archive/debug/` | 后续 ZMQ 内部崩溃可复用符号可信度和 context/mailbox 排查顺序 |
| DVR 回放 SD 热拔插异常闭环 | 物理拔卡、轮询检测、卸载/格式化、暂停唤醒、handle 关闭和 `END_ERROR` 上报已形成完整代码闭环 | session `019f63de-5667-7951-8b3e-0ce1e55c3142`；代码复审、格式和构建门禁 | medium；缺真机 PLAY/PAUSE/SEEK 热拔插矩阵 | high for code / low for hardware acceptance | `projects/xcrz-sigmastar-demo/validation/` | 后续 DVR/SD 异常回归可直接复用状态矩阵和验收缺口 |
| AI 音频 stream 顺序与 EOF 语义 | 同一 SHM channel 正常保持 `START/DATA/END` 顺序；主要风险是丢帧、seq 跳号、新旧流交叉和缺少 `stream_id`；`Parser read failed: 1` 实为正常 EOF | sessions `019f50b9-16f3-7523-8220-0079d25fe813`、`019f5a5d-4503-7403-b644-4538bdcab3cb` | medium；需板端验证 EOF 日志消失且 drain 事件保持 | high for code semantics | `projects/xcrz-sigmastar-demo/archive/design/` 或 `validation/` | 后续音频乱序、丢帧和 EOF 告警可区分协议缺口与正常结束 |
| 电机标定静态信息缓存语义 | `read_ok=true` 与 `status_value` 分离；成功读取“未标定”也应缓存，只重试失败侧，避免左右电机重复查询 | session `019f64ba-488c-7000-816b-c9daf687344d`；编译期断言与模块/应用构建 | medium；需设备启动和主动重标定复测 | high for code / medium overall | `projects/xcrz-sigmastar-demo/archive/design/` 或 `validation/` | 可复用到其他“读取成功但值为 false/0”的静态信息缓存设计 |
| 产测电机 Hall 校准前置事务 | 所有 HallCalibration 调用统一执行 `ClearFault → Estop → HallCalibration`，前置失败记录诊断但不阻断校准 | session `019f93d1-d685-78d1-b6c3-c0f9ebb24564`；三处调用点扫描和联合构建 | medium；需板级确认左右/both 目标与故障态行为 | high for code / medium overall | `projects/xcrz-sigmastar-demo/validation/` | 后续产测、维修工具和交互命令可使用同一校准前置契约 |
| QR_CODE_SN 非法字符诊断 | 长度 17 已通过但 `reason=char` 表示白名单失败；诊断应只记录非法位置和字节，不打印完整 SN | session `019fa81a-c46a-7750-917f-516e5153adb0`；日志与校验源码 | low；需核对设备 BuildID 和上位机实际 protobuf 字节 | high for validator semantics | `projects/xcrz-sigmastar-demo/archive/debug/` 或产测 runbook | 后续扫码枪结束符、大小写和混淆字符问题可快速定位且避免泄露完整 SN |

## 已覆盖，不建议重复归档

| 主题 | 现有覆盖 | 处理建议 |
| --- | --- | --- |
| QMI8658 校准、老化门禁、AI/HDI 性能 | `projects/xcrz-sigmastar-demo/archive/reports/2026-07-09-codex-history-backfill-engineering-findings.md` | 只补关联，不重写同类总览 |
| `prog_pcr02` 高负载、`cmd_server`、IMU/TOF 调度 | 2026-07-02、07-10、07-21、07-24 的 high-load/debug/validation 条目 | 新证据追加到对应时间线 |
| 光敏、IR、1/30fps 和 ACTIVE_LOW_1 | 既有 AOV/光敏分析及 2026-07-27 至 07-28 pipeline/decision/validation 候选 | 不再从旧会话回填重复原理 |
| MCU/SoC 低功耗、TCPKA、shutdown、WiFi wake | 2026-07-22 至 07-28 的 current/decision/archive/debug 条目 | 继续走现有 owner/HIL 门禁 |
| 2026-07-28 电机 UART、BCMDHD suspend 与启动 SD 边界 | 当日 session closeout 与三个项目 debug/archive 候选 | 当前工作树候选完成 review 后再决定登记 |
| 2026-06-29 至 06-30 monotonic PTS、DVR/MP4 | `projects/pcr02-ssc305/archive/engineering-archive/pcr02/media-timing/` | 保留 rollout summary 为 provenance |
| Codex archive、ADK hardcut、token 与治理迁移 | `artifacts/manifests/codex-archive-*` 和 `domains/codex/archive/` tombstone | 不恢复已删除旧正文 |
| GD32L235 v1.1.38 NAS 发布 | `projects/gd32l235/archive/release/2026-07-18-gd32l235-v1.1.38-nas-release.md` | 只补实机烧录/HIL，不重复写发布摘要 |

## 仅保留 provenance

- 171 个 subagent session：发现、测试、审查和整合过程应并入父任务结论。
- 10 个 rollout summary：用来恢复会话和引用证据，不直接成为 current fact。
- `session_index.jsonl`、`history.jsonl` 和 session id：只用来定位来源。
- 同期 Hub 审计、迁移、tombstone 和 coverage manifest：只用于说明治理过程。
- 工作区 dirty 状态、临时分支名、一次性构建路径和本机端点：不得提升为长期事实。

## 应丢弃或禁止进入文本知识层

- `auth.json`、token、cookie、private key、password 和其他凭证。
- 完整聊天、完整日志、完整 GDB 输出、raw core、SDK 压缩包、release binary。
- 44 个附件原文、8 个 shell snapshot、cache、tmp、SQLite/WAL/SHM 运行库。
- “Greet user”、简单问候、一次性命令、更名、机械格式修复、临时 stash/pull 恢复。
- 已被 canonical 条目覆盖且没有新增证据的重复分析。

## Memory candidate 结论

本轮没有建议写入 `~/.codex/memories` 的 stable memory candidate。

原因：

- 技术结论全部是 PCR02、SSC305、GD32L235、产测或 Codex 治理的 project-specific 内容，应走项目 archive/decision/validation 路由。
- 稳定工作流规则已经由 AGENTS、governance、skill 和 manifest 管理；再次写入 memory 会制造重复权威。
- 用户偏好、长期职责和跨项目规则未发现比现有规则更新且有充分证据的新内容。

## 风险与限制

- 359 个 rollout 已完成元数据级全量盘点，但没有逐行人工阅读约 866 MiB raw session；语义复核覆盖 41 个顶层标题、10 个 summary、1534 条 history 索引和高信号候选会话。
- `session_index.jsonl` 只有 41 个近月更新线程标题，不能代表全部直接交互 session；无标题记录通过 cwd、source、history 和 Hub 时间线补充统计。
- Hub 当前工作树存在用户原有的未提交变更；本次归档只新增 10 个候选正文，并通过治理工具增量更新 registry/index，未回退、覆盖或清理无关内容。
- `libzmq`、`libmsc`、音频、DVR 和 MCU/SoC 候选必须在落盘时重新核对源仓 commit、BuildID、设备证据和敏感信息。

## 验证与证据

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash ~/knowledge-hub/tools/knowledge-context.sh --cwd ~/knowledge-hub --query "近一个月 Codex 使用记录、会话总结、决策、排障、研究与可归档候选审计" --task-type archive --context-budget small --limit 3 --summary-json` | 0 | 路由到 `domains/codex/`，确认 raw session 只作 provenance，owner/memory/source write 有门禁。 | `domains/codex/README.md` | Knowledge Hub | 本审计 |
| `rtk find ... ~/.codex/sessions ...` 与 `rtk jq ...` 聚合 | 0 | 统计 359 个 rollout、188 个直接交互、171 个 subagent、1534 条 history 输入和 186 个 history session。 | 本机 Codex runtime metadata | Tool | 本审计 |
| `rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<候选主题>" --limit 10` | 0 | 对 8 组主题和 6 个高信号候选执行 canonical 去重检索。 | Knowledge Hub search index | Knowledge Hub | 候选/已覆盖表 |
| `rtk git status --short` | 0 | 发现既有 registry/index 与项目文档 dirty 变更；本轮避开这些文件。 | 当前工作树 | Knowledge Hub | 风险与限制 |

补充说明：

- date：`2026-07-28`
- cwd：`~/knowledge-hub`
- scope：本机 Codex 近月运行记录与 Knowledge Hub 已登记覆盖
- artifact_refs：本文

## 执行结果（2026-07-29）

10 组候选均已按项目边界脱敏落盘，并通过 Knowledge Hub 治理工具登记。所有条目的 `status` 均为 `reviewing`，`promotion` 均为 `none`，人工复核或实机验证仍为待办；本次未写 memory、未创建 owner decision、未提升 active、未修改源项目，也未执行 commit、push、merge 或发布。

| Registry ID | 类型 | 落盘路径 |
| --- | --- | --- |
| `pcr02-libmsc-lua-rpc-use-after-free-20260724` | debug | `projects/xcrz-sigmastar-demo/archive/debug/2026-07-24-libmsc-lua-rpc-use-after-free.md` |
| `pcr02-agora-downlink-audio-starve-tail-loss-20260713` | debug | `projects/xcrz-sigmastar-demo/archive/debug/2026-07-13-agora-downlink-audio-starve-tail-loss.md` |
| `pcr02-wifi-provision-display-state-gap-20260702` | debug | `projects/xcrz-sigmastar-demo/archive/debug/2026-07-02-wifi-provision-display-state-gap.md` |
| `pcr02-aging-health-report-timeout-contract-20260717` | architecture | `projects/xcrz-sigmastar-demo/archive/design/2026-07-17-aging-health-report-timeout-contract.md` |
| `pcr02-zmq-context-mailbox-lifecycle-crash-20260702` | debug | `projects/xcrz-sigmastar-demo/archive/debug/2026-07-02-zmq-context-mailbox-lifecycle-crash.md` |
| `pcr02-dvr-replay-sd-hot-unplug-closure-20260715` | validation | `projects/xcrz-sigmastar-demo/validation/2026-07-15-dvr-replay-sd-hot-unplug-closure.md` |
| `pcr02-ai-audio-stream-order-eof-contract-20260713` | architecture | `projects/xcrz-sigmastar-demo/archive/design/2026-07-13-ai-audio-stream-order-eof-contract.md` |
| `pcr02-motor-calibration-static-info-cache-20260715` | validation | `projects/xcrz-sigmastar-demo/validation/2026-07-15-motor-calibration-static-info-cache.md` |
| `pcr02-motor-hall-calibration-prestart-transaction-20260724` | validation | `projects/xcrz-sigmastar-demo/validation/2026-07-24-motor-hall-calibration-prestart-transaction.md` |
| `pcr02-qr-code-sn-character-validation-20260728` | debug | `projects/xcrz-sigmastar-demo/archive/debug/2026-07-28-qr-code-sn-character-validation.md` |

治理工具拒绝以 `project-archive` 类型直接创建条目，因为该类型需要经过授权的 lifecycle transition。两项设计契约因此按实际内容类型登记为 `architecture`，仍保持 `reviewing`；未绕过归档生命周期门禁。

定向校验已确认 10 个 registry id 与路径唯一、正文无 diff whitespace 错误，且未发现凭证模式、本机绝对用户路径或完整设备标识。全库 `knowledge-check --dry-run` 仍被一个本次任务开始前已存在、且不属于上述 10 个条目的用户路径边界问题阻塞：`projects/xcrz-sigmastar-demo/current/decisions/active-low-1-warm-switch-experiment.md`。因此本次新增条目可判定为定向验证通过，但不能声称全库门禁全绿。

## 后续执行顺序

1. 由 owner 逐条复核 10 个 `reviewing` 候选的来源、结论和项目边界。
2. DVR、音频 EOF/stream、motor calibration 和 Hall calibration 优先补板级验证；ZMQ 保持“推断”标签。
3. `libmsc` 补主程序匹配 BuildID 和业务调用方证据；二维码 SN 补上位机 protobuf 原始字节核对，但正文仍不得记录完整 SN。
4. 完成证据闭环后，再通过授权 lifecycle transition 决定是否进入正式 archive 或其他状态。

## Review

- owner：`leiwenjun`
- review_after：`2026-08-28`
- 下一次复核：逐条确认 10 个 `reviewing` 候选的证据强度、实机验证缺口和 lifecycle 去向。
