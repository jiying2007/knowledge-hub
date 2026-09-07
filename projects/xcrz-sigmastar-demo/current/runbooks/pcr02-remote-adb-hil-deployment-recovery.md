---
aliases:
- PCR02 Remote ADB/HIL 部署恢复
- PCR02 远程板测失联熔断
related:
- projects/xcrz-sigmastar-demo/current/runbooks/prog-pcr02-high-load-debug.md
- indexes/obsidian-home.md
id: pcr02-remote-adb-hil-deployment-recovery-runbook-20260726
title: PCR02 Remote ADB/HIL 部署与失联恢复 Runbook
kind: runbook
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/current/runbooks/pcr02-remote-adb-hil-deployment-recovery.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: current-session-engineering-contract
  from: PCR02 pipeline HIL、ADB 失联与制品身份调试经验及已退役私人 AI 资产的脱敏提炼；端点、raw log、core 和二进制已排除
  source_sha256: 787802965365ac0fccda2c855a27560352367b89cce8f9f44d69b5506b4c7dee
  temporary_source_retained: false
review_after: '2026-10-26'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; project-local reviewing runbook candidate, no active promotion, release gate or owner decision
tags:
- pcr02
- ssc305
- adb
- remote-debug
- hil
- artifact-identity
- deployment-gate
- unreachable
- recovery
- reviewing
- no-active-promotion
validation_refs:
- projects/xcrz-sigmastar-demo/current/runbooks/pcr02-remote-adb-hil-deployment-recovery.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: current-debugging-contract-device-revalidation-pending
evidence_refs:
- team-knowledge:tools/codex_assets/pcr02_adb_runtime_debug.py
- team-knowledge:docs/governance/knowledge-repo-migration-map.csv
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-27-hdi-vi-30-1fps-scl-pool-teardown.md
- projects/xcrz-sigmastar-demo/validation/2026-07-31-vi-fps-publish-validation.md
created_at: '2026-07-26'
updated_at: '2026-09-07'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-26'
manual_validation_pending: true
summary_zh: 固化 PCR02 远程 ADB/HIL 的分层连通性、失联熔断、制品身份、授权部署、逐级板测和最终健康恢复；现场端点和原始制品不进入长期正文。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 Remote ADB/HIL 部署与失联恢复 Runbook

## 适用范围

本 runbook 适用于 PCR02/SigmaStar SSC305 目标板的远程 ADB 恢复、`prog_pcr02` 候选身份核对、受控部署、30fps/1fps pipeline HIL、MAIN/SUB/BOTH 板测和设备失联后的接力。

它不替代媒体 pipeline 的设计/验收文档，也不授权设备写入、回滚、重启、刷机或发布。高负载低扰动采集仍使用 `prog-pcr02-high-load-debug.md`。

## Transport、权限与敏感边界

- Transport：主机 route/network hint、ADB TCP transport、remote shell、应用/诊断面。
- Endpoint：由本次授权环境注入，例如 `PCR02_ADB_SERIAL`；正文不保存实际地址。
- 默认权限：设备只读；允许本地 evidence bundle 写入已忽略临时目录。
- 写操作：push、kill、restart、remount、覆盖、rollback、image/OTA 必须有当前用户明确授权。
- Deny path：不得把凭证、现场端点、raw log、core、二进制、SDK 包或客户资料写入 Hub/Git。
- 回退：ADB 熔断后转串口、受控电源恢复或现场协助；没有这些能力时状态为 `blocked`。

## 主状态机

```text
DISCOVER
  -> READONLY_PREFLIGHT
  -> ARTIFACT_GATE
  -> AUTHORIZED_DEPLOY
  -> SINGLE_SMOKE
  -> SHORT_CYCLE
  -> LONG_STRESS
  -> SOAK
  -> RESTORE_HEALTHY_STATE
  -> EVIDENCE_ARCHIVE

任一阶段失联
  -> UNREACHABLE
  -> stop writes and retries
  -> preserve last-known evidence
  -> serial/power/onsite handoff
  -> recovery 后重新从 READONLY_PREFLIGHT 开始
```

每次源码、SDK、sensor mode、候选 MD5/BuildID 或设备 boot identity 变化，旧 HIL 证据立即 stale。

## 1. Discover 与只读 preflight

以下命令从 PCR02 源码根运行；若从其他目录调用，必须通过 `PCR02_SOURCE_ROOT` 显式指定源码根。设置本次 endpoint 后运行团队工具：

```bash
rtk python3 ~/knowledge/tools/codex_assets/pcr02_adb_runtime_debug.py \
  preflight --serial "${PCR02_ADB_SERIAL}"
```

必须独立判断：

| Layer | Probe | 说明 |
|---|---|---|
| host route | `ip route get` | 只说明主机路由 |
| network hint | 单次 ping | 失败不跳过 ADB |
| ADB transport | `adb connect` 输出 + `adb devices -l` | 不能只看退出码 |
| remote shell | heartbeat、boot_id、uptime | 使用独立 timeout |
| app/diag | PID、health、诊断 reply | 使用业务 timeout |

禁止 `ping && adb connect`。`offline`、`unauthorized`、`missing`、`No route to host`、refused、timeout 均不是 transport ready。

设备恢复后先记录：

1. `boot_id` 和 uptime；
2. `prog_pcr02` PID/状态；
3. core hints 和 fatal dmesg；
4. installed MD5/BuildID；
5. backup anchors；
6. watchdog、auto standby、supervisor 和其他 FPS/profile mutator；
7. transport/shell/app 分层时延。

恢复可达不等于允许部署。

## 2. Retry budget 与失联熔断

- connect 默认 1 次，显式扩大不得超过 3 次。
- network、transport、shell、app/diag 分别记录 timeout 和 elapsed。
- 连续失败打开 circuit breaker：停止 push、kill、restart、remount、覆盖、rollback、flash/OTA 和 HIL。
- 保留最后成功层、最后 boot/artifact identity、最后日志窗口和失败输出 SHA256。
- 设备恢复后重新 preflight；不得从失败循环盲目续跑。
- auto standby、watchdog、媒体循环并发时只标记 `confounded`，不得把失联单因果归于 VENC/pipeline 或当前补丁。

## 3. Artifact identity gate

本地离线核对：

```bash
rtk python3 ~/knowledge/tools/codex_assets/pcr02_adb_runtime_debug.py \
  artifact-gate --bin <frozen-candidate>
```

设备部署前核对：

```bash
rtk python3 ~/knowledge/tools/codex_assets/pcr02_adb_runtime_debug.py \
  artifact-gate --bin <frozen-candidate> --include-device \
  --serial "${PCR02_ADB_SERIAL}"
```

必须把 source HEAD/dirty、app out、frozen candidate、release bin、NFS/staged、installed、image/OTA 分成不同阶段。每级至少记录 path/class、size、MD5、SHA256、BuildID（可用时）和时间。

`release/bin` 与候选不一致时不得误部署。后编译 app 不会自动更新既有 image/OTA。

## 4. 场景抓证与分析

运行态抓证统一使用 `capture`，随后对同一 evidence bundle 执行 `analyze`：

```bash
rtk python3 ~/knowledge/tools/codex_assets/pcr02_adb_runtime_debug.py \
  capture --profile <base|detection-overlay|video-route|rgn-osd> \
  --serial "${PCR02_ADB_SERIAL}"
rtk python3 ~/knowledge/tools/codex_assets/pcr02_adb_runtime_debug.py \
  analyze --capture tmp/pcr02-adb-runtime-debug/<timestamp>
```

| Profile | 主要证据 | 判断边界 |
|---|---|---|
| `base` | boot、进程、mutator、core hint、dmesg、staged/installed identity | 只提供通用运行态基线 |
| `detection-overlay` | sensor/AI tail、RGN、SCL0/SCL1 | 无检测消息先查发布/订阅；有 active box 但无画面再查坐标、格式、alpha、layer 和编码通道 |
| `video-route` | raw source callback、SCL0/SCL1、会话日志 | DS1/DS2 同时活跃时查生命周期、引用计数和 SCL2 仲裁；480x480 优先核对扫码路径是否释放 |
| `rgn-osd` | RGN handle、layer、`bShow`、`UpdateCanvasCnt` | `bShow=0` 表示不可见，计数不增长表示 canvas 更新停滞；不同 OSD 必须有独立 owner |

固定场景 CPU 使用：

```bash
rtk python3 ~/knowledge/tools/codex_assets/pcr02_adb_runtime_debug.py \
  cpu-baseline --scenario <idle|vision|lcd-vision|full> --confirm-scene \
  --serial "${PCR02_ADB_SERIAL}" --note "记录实际启用项与环境"
```

四个场景必须使用同一设备、同一 installed MD5、相同日志/网络/输入条件；切换后稳定至少 10 秒，采集 60 秒。进程重启、制品变化或场景未确认时该 run 不进入对比基线。

## 5. 授权部署

先只输出计划：

```bash
rtk python3 ~/knowledge/tools/codex_assets/pcr02_adb_runtime_debug.py \
  deploy --dry-run
```

只有本次明确授权后才能使用 `--confirm-deploy`。部署契约：

1. candidate 存在；
2. staged MD5 等于 candidate；
3. 覆盖前创建新 timestamp backup anchor，不覆盖既有原始备份；
4. 只停止 `prog_pcr02`，TERM -> 有界等待 -> KILL fallback；
5. supervisor/watchdog 立即拉起时在 install 前阻断；
6. 临时文件复制、chmod、原子 `mv`；
7. 异常路径尽力恢复 `/customer` 只读；
8. installed MD5 等于 candidate；
9. restart 后记录 PID/boot/core/dmesg/mount；
10. 重新执行只读 preflight。

默认不 `adb push`；只有 staged 缺失/确认过期且用户批准时才使用。工具不静默 rollback；失败时保留 backup anchor，恢复目标需单独确认。

## 6. HIL 逐级扩大

HIL 前隔离或记录 60 秒 auto standby、watchdog、supervisor 和其他 FPS/profile mutator。

| Stage | 范围 | 必须观察 | 扩大门槛 |
|---|---|---|---|
| SINGLE_SMOKE | SUB-only、MAIN-only、BOTH 各一次 | 状态 mask、bind/cascade、首 IDR、core/dmesg | 全部通过 |
| SHORT_CYCLE | 5～10 次 30↔1 | switch/首帧、callback、旧 P 帧/花屏、unexpected ISP deinit | 无 fatal/泄漏/身份漂移 |
| LONG_STRESS | 1000 次 | P50/P95/P99/max、thread/fd/RSS/MMA、decoder | 短循环通过 |
| SOAK | 8h/功耗/稳定性 | 资源趋势、consumer、网络健康 | 长循环通过 |
| COLD_DEINIT | 独立测量 | ISP deinit 分 API 时延和 fail-stop | 不污染 HOT 结论 |

30→1 的控制面时延与 1fps 自然首帧等待分开统计。HOT 30↔1 不应通过 ISP deinit 实现；COLD deinit 的长耗时单独归档。

出现失联、core、fatal dmesg、callback 停滞、unexpected ISP deinit、状态泄漏、身份漂移或健康恢复失败时立即停止。

## 7. 最终健康恢复

完成或中断前：

- 恢复健康 `NORMAL_30`；
- 关闭临时 diag H26x/reader/stream；
- 确认 ADB transport、shell、`prog_pcr02` 健康；
- 记录最终 installed MD5/BuildID、boot_id、uptime；
- 检查没有新增 core/fatal dmesg；
- 记录 evidence bundle 路径和 bundle SHA256。

恢复失败时 gate 固定为 `blocked`/`needs-recovery`，不能声明 HIL 或发布闭环。

## Evidence bundle

每个阶段保存脱敏 `manifest.json` 与 `evidence-index.json`：

- layer result、timeout、elapsed；
- boot/artifact identity；
- raw evidence 临时路径和 SHA256；
- mutation authority、backup anchor；
- HIL stage、stop reason；
- restore/postcondition；
- gate、next action、residual risk。

Knowledge Hub 只保存脱敏结论、哈希和证据引用，不保存 endpoint、raw log/core/binary。

## 当前成熟度

本文为 `reviewing` 项目 runbook candidate。工具和主机测试可验证流程结构，但真实目标板恢复、候选部署、1000 次、decoder、8h soak、COLD ISP deinit 分位数和 owner 签收仍必须由新的板级证据关闭。
