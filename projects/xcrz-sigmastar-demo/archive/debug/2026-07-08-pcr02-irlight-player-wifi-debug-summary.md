---
title: PCR02 IR light、播放器 start/wait 与 WiFi 行为归档 2026-07-08
doc_type: debug-record
knowledge_type: incident-learning
maturity: archived
status: archived
owner: leiwenjun
created: 2026-07-11
last_updated: 2026-07-11
tags: [pcr02, irlight, colortogray, player, wifi, wpa-supplicant, codex-archive-migration]
related:
  - 2026-07-03-pcr02-camera-whiteout-ae-exposure-analysis.md
---

# PCR02 IR light、播放器 start/wait 与 WiFi 行为归档 2026-07-08

## 归档边界

本文从旧 Codex archive `daily-summary/20260708-211900-engineering-archive-summary.md` 中拆出 PCR02 设备侧结论。它只保留脱敏摘要、验证命令和未上板边界，不复制 `.codex/sessions`、完整设备日志、WiFi 凭据、AP 扫描列表、NAS 制品或运行态缓存。

## IR light ColorToGray 刷屏修复

- `IrLight: set color mode failed, ret=0x-5fdeddfe` 的核心风险不是 IR-cut 或灯失败，而是 `ColorToGray` 辅助步骤失败后阻断 `setRelight(false)`。
- 阻断会导致 `m_isNight` 不更新，worker 持续重试并约每 500ms 刷屏。
- 修复方向是 `VSHDIVI_IspSetColorToGray()` 增加 VI 主链路 guard，`irlight.cpp` 将 `ColorToGray` 失败降级为 warning，并继续完成 IR-cut、灯亮度、IQ path 和 `m_isNight` 更新。
- `0x-5fdeddfe` 按 32 位无符号为 `0xa0212202`，未能在平台通用 ISP 错误码表中直接映射为某个 `MI_ERR_ISP_*`，更可能是 `MI_ISP_IQ_*` 子模块或厂商内部编码。
- 平台文档推荐的更稳流程是 `Alloc/Get/Set/Free` IQ data buffer。
- 验证摘要：`rtk make modules/hdi_lib_all modules/sensor_lib_all NC=1` 通过。
- 边界：板端复测前，不把 `0xa0212202` 解释为确定厂商根因。

## 播放器 start.wait_start_state 风险

- `VSAPIPLAYER_Start()` 偶发 `start.wait_start_state` 超时的高概率风险点是播放器线程在释放 start 状态 semaphore 前先执行上层回调。
- 若回调中的 `GetVolume()`、`publishState()`、ZMQ 或线程调度变慢，`Start()` 可能误判 2 秒超时。
- 修复方向是先更新状态并释放 semaphore，再执行回调，降低启动期回调阻塞导致的误超时。
- 长期语义应拆成 `state_started` 和 `stream_ready/open_ready` 两阶段，因为当前 `Start()` 等待的是状态进入 `PLAYING`，不是 parser/render 已打开成功。
- `Drained stale player semaphore` 本身不是播放失败，但说明 semaphore 仍存在历史残留信号窗口。若高频出现，应引入 generation/sequence 化 ack。

## 1T1R WiFi 扫描配置判断

- `wpa_supplicant.conf` 中的 `scan_ssid=1` 不等于持续后台扫描开关。它表示连接或重连时对该 SSID 做主动探测扫描，主要用于隐藏 SSID。
- 没有配置 `bgscan` 时，稳定连接通常不会周期性后台扫描。
- 1T1R 设备如果被上层或配置频繁触发扫描，可能带来短时延迟、丢包、音视频卡顿和弱信号重连风险。
- 配置建议是非隐藏 SSID 删除 `scan_ssid=1` 或设为 `0`，不配置 `bgscan`，避免上层周期性执行 `wpa_cli scan`。
- 现场确认应查看 `wpa_cli status`、`wpa_cli scan_results`，以及 wpa 日志是否持续出现 `CTRL-EVENT-SCAN-STARTED` / `CTRL-EVENT-SCAN-RESULTS`。

## VSAPIWIFI_DeInit 不断网但释放 wpa_ctrl 残留

- `VSAPIWIFI_DeInit()` 的 `bKeepWifiRunning` 分支应保留不断网语义，但释放本进程创建的 `wpa_ctrl_<pid>-*` socket 文件。
- 实现方向是新增 `wifi_detach()` 控制路径，Linux STA 层只关闭本进程 control/monitor socket 和事件 socket。
- 底层 `detach_wpad()` 只执行 `wifi_close_sockets()` 和清本进程状态，不执行 `stop_wpad()`，因此不停止 `wpa_supplicant`，不 `ifconfig wlan0 down`。
- `VSAPIWIFI_PowerOff()` 和正常关 WiFi 路径保持原行为，仍走 `wifi_off()` 断网。
- 验证摘要：WiFi 动态库、静态库、API 对象和 `pcr02_app_all` 链接目标均构建通过；`libwifi.a` 与 `libwifi.so` 均确认导出 `wifi_detach`；关键对象确认是 ARM。
- 残留风险：当时只完成代码与链接验证，尚未在真实设备上跑退出场景。需要上板确认 `VSAPIWIFI_DeInit()` 后业务连接不断，并确认本进程 `wpa_ctrl_<pid>-*` 文件消失。

## 迁移记录

- Old source: `domains/codex/archive/codex-archive/daily-summary/20260708-211900-engineering-archive-summary.md`
- Old source SHA256: `07d43e00e0dbfc5b1aeb676251c1919527dab7f2bb9e412243c6be5a2ddf3936`
- Old source size: `8678` bytes
- Old source lines: `82`
- Final coverage row: `artifacts/manifests/codex-archive-final-body-coverage-20260711.jsonl#CAFC-20260711-005`
- Tombstone: `artifacts/manifests/codex-archive-removal-execution-20260711-final-bodies.jsonl#CARE-20260711-045`
