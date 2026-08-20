# By Project

## PCR02 产品组关系索引

- group ID：`pcr02`；唯一声明位置是 `registry/project-groups.json`，不作为独立 project、正文 domain、目录或兼容 route。
- 平台规范入口：`projects/pcr02-ssc305/README.md`，承载 SDK、kernel、boot、镜像、OTA、存储、板级硬件和平台集成事实。
- 应用规范入口：`projects/xcrz-sigmastar-demo/README.md`，承载应用、诊断、媒体、显示应用层、模块联调和会话证据。
- 独立模块继续进入各自 `projects/pcr02-*` 项目；跨仓正文按结论主责只维护一份。
- 组级 source control：`sources/pcr02-project-docs` 与 `sources/engineering-archive`；它们只描述来源和历史 provenance，不替代两个规范项目入口。
- 项目组规范入口边界：`projects/pcr02-ssc305/decisions/pcr02-canonical-hardcut-20260715.md`。
- owner gate 与历史治理通过 `indexes/by-decision.md`、`indexes/by-source.md` 和 `artifacts/manifests/` 恢复。
- review-required 历史处理计划：`artifacts/manifests/pcr02-review-required-resolution-20260617.md`
- reference/artifact-ref applied 报告：`artifacts/manifests/pcr02-reference-artifact-ref-applied-20260618.md`
- owner-review 历史 package：`artifacts/manifests/pcr02-owner-review-package-20260618.md`
- ASAN 拆分历史目标：`artifacts/manifests/pcr02-asan-split-targets-20260618.md`
- memory auto-curation report-only 历史治理：`artifacts/manifests/memory-auto-curation-report-only-governance-20260618.md`
- DVR 与 motor MCU 历史收口目标：`artifacts/manifests/pcr02-dvr-motor-closeout-targets-20260618.md`
- owner gates 历史证据：`artifacts/manifests/pcr02-remaining-owner-gates-20260618.md`
- docs 治理历史收口：`artifacts/manifests/pcr02-docs-governance-closeout-20260618.md`
- owner 历史行动看板：`artifacts/manifests/pcr02-owner-action-board-20260618.md`
- 治理历史交接：`artifacts/manifests/pcr02-governance-handoff-20260618.md`
- owner 历史 intake package：`artifacts/manifests/pcr02-owner-intake-package-20260618.md`
- owner source identity 历史 preflight：`artifacts/manifests/pcr02-owner-source-identity-preflight-20260618.md`
- owner source identity validation：`artifacts/manifests/knowledge-hub-owner-source-identity-validation-20260620.md`
- Level 2 source coverage 收口：`artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.md`
- tools 边界：`artifacts/manifests/pcr02-tools-boundary-20260620.md`
- knowledge secret/config 边界：`artifacts/manifests/pcr02-knowledge-secret-config-boundary-20260620.md`
- product-test artifact/config/interface 边界：`artifacts/manifests/pcr02-product-test-artifact-config-interface-boundary-20260620.md`
- product-test artifact/config/interface 身份清单：`artifacts/manifests/pcr02-product-test-artifact-config-interface-identity-20260621.md`
- P1 source identity，覆盖 agent-config/tools/root-artifacts：`artifacts/manifests/pcr02-p1-source-identity-20260621.md`
- P2 archive/rule identity，覆盖 module-agent-rules/scratch：`artifacts/manifests/pcr02-p2-archive-rule-identity-20260621.md`
- Level 2 source check 执行快照：`artifacts/manifests/pcr02-level2-source-check-execution-snapshot-20260621.md`
- scratch archive 边界：`artifacts/manifests/pcr02-scratch-archive-boundary-20260620.md`
- root artifacts 边界：`artifacts/manifests/pcr02-root-artifacts-boundary-20260620.md`
- module agent rules 边界：`artifacts/manifests/pcr02-module-agent-rules-boundary-20260620.md`
- agent config 边界：`artifacts/manifests/pcr02-agent-config-boundary-20260620.md`
- Owner resolution playbook: `artifacts/manifests/pcr02-owner-resolution-playbook-20260618.md`
- Owner resolution schema: `artifacts/manifests/pcr02-owner-resolution-schema-20260618.md`
- Owner decision intake execution: `artifacts/manifests/pcr02-owner-decision-intake-execution-20260620.md`
- AGENTS historical owner signoff package: `artifacts/manifests/pcr02-agents-owner-ready-package-20260620.md`
- Diag metadata historical owner signoff package: `artifacts/manifests/pcr02-diag-owner-ready-package-20260620.md`
- ASAN historical owner signoff package: `artifacts/manifests/pcr02-asan-owner-ready-package-20260620.md`
- Memory auto-curation historical owner signoff package: `artifacts/manifests/pcr02-memory-auto-curation-owner-ready-package-20260620.md`
- DVR plan historical owner signoff package: `artifacts/manifests/pcr02-dvr-plan-owner-ready-package-20260620.md`
- Motor MCU historical owner signoff package: `artifacts/manifests/pcr02-motor-mcu-owner-ready-package-20260620.md`
- DVR session archive historical owner signoff package: `artifacts/manifests/pcr02-dvr-session-archive-owner-ready-package-20260620.md`
- Owner decision landing: `artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.md`
- Source 主控目录：`sources/pcr02-project-docs/README.md`、`sources/pcr02-project-docs/inventory.jsonl`、`sources/pcr02-project-docs/coverage.md`、`sources/pcr02-project-docs/source-policy.md`
- ASAN project-local target：`projects/xcrz-sigmastar-demo/current/runbooks/asan-debug-guide.md`
- DVR plan archive target：`projects/xcrz-sigmastar-demo/archive/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md`
- Motor MCU debug record archive target：`projects/xcrz-sigmastar-demo/archive/reports/2026-05-29-motor-mcu-debug-record.md`
- DVR record/replay session archive target：`projects/xcrz-sigmastar-demo/archive/reports/2026-06-16-dvr-record-replay-session-archive.md`
- Source control unification：`artifacts/manifests/knowledge-hub-source-control-unification-20260624.md`
- Owner target and landing validation: `artifacts/manifests/knowledge-hub-owner-target-landing-validation-20260621.md`
- Owner-ready command stability: `artifacts/manifests/knowledge-hub-owner-ready-command-stability-20260621.md`
- Source check docs, guardrails and search limit: `artifacts/manifests/knowledge-hub-source-check-docs-search-limit-20260621.md`
- Final gap readability and index recovery: `artifacts/manifests/knowledge-hub-final-gap-readability-index-20260621.md`
- Owner dispatch and readability sync: `artifacts/manifests/knowledge-hub-owner-dispatch-readability-sync-20260621.md`
- Status dispatch, owner recovery and AI provenance sync: `artifacts/manifests/knowledge-hub-status-dispatch-notes-zh-20260621.md`
- Owner routing recovery: `artifacts/manifests/knowledge-hub-owner-routing-recovery-20260621.md`
- Docs index reference: `projects/xcrz-sigmastar-demo/current/docs-index.ref.md`
- CI smoke session artifact reference: `projects/xcrz-sigmastar-demo/validation/prog-tool-ci-smoke.session.ref.md`
- Engineering archive corpus: `projects/pcr02-ssc305/archive/engineering-archive`
- PCR02 prog_pcr02 high-load monitoring: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-02-prog-pcr02-high-load-monitoring.md`; `pcr02-prog-pcr02-high-load-monitoring-20260702`
- PCR02 prog_pcr02 runtime hot-thread follow-up: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-10-prog-pcr02-runtime-hot-thread-followup.md`; `pcr02-prog-pcr02-runtime-hot-thread-followup-20260710`
- PCR02 camera RAW_PREVIEW virtual stream architecture decision candidate: `projects/xcrz-sigmastar-demo/decisions/camera-raw-preview-virtual-stream-architecture-20260711.md`; `pcr02-camera-raw-preview-virtual-stream-architecture-20260711`; reviewing candidate only, no owner-signed active rule or release claim
- PCR02 ST77912 dual-screen SPI clock/FPS decision candidate: `projects/pcr02-ssc305/decisions/st77912-dual-screen-spi-clock-fps-decision-20260711.md`; `pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711`; reviewing candidate only, requires aging, oscilloscope and animation validation
- PCR02 ST77912 fbtft 54MHz/25fps implementation evidence: `projects/pcr02-ssc305/decisions/st77912-fbtft-54m25fps-implementation-20260711.md`; `pcr02-st77912-fbtft-54m25fps-implementation-20260711`; archived evidence only, no owner-signed active decision, aging validation or release claim
- PCR02 ST77912 framebuffer and SigmaStar mi_fb boundary decision candidate: `projects/pcr02-ssc305/decisions/st77912-fb-mi-fb-boundary-decision-20260711.md`; `pcr02-st77912-fb-mi-fb-boundary-decision-20260711`; reviewing candidate only, records that `/dev/fb0` and `/dev/fb1` are `fb_st77912` while `/dev/fb2` is `SStar FB0`.
- PCR02 owner-ready validation paths: `artifacts/manifests/pcr02-owner-ready-validation-paths-20260713.md`; `pcr02-owner-ready-validation-paths-20260713`; validation path only, requires real owner signoff and target-device/lab evidence before active or release claim
- PCR02 SSC305 第三方库编译优化基线：`projects/pcr02-ssc305/current/runbooks/thirdparty-build-optimization-baseline.md`; `pcr02-thirdparty-build-optimization-baseline-20260710`; reviewing source-derived runbook，仍需 owner 和目标构建验证
- PCR02 EVT2 MCU/SoC contract source-derived index: `projects/pcr02-ssc305/archive/engineering-archive/pcr02/source-audit/pcr02_evt2_mcu_soc_contract_index_20260711.md`; `pcr02-evt2-mcu-soc-contract-index-20260711`; reviewing source-audit only, no owner-signed active contract or release claim
- PCR02 Codex history backfill engineering findings: `projects/xcrz-sigmastar-demo/archive/reports/2026-07-09-codex-history-backfill-engineering-findings.md`; `pcr02-codex-history-backfill-engineering-findings-20260709`
- PCR02 /customer ro SD upgrade historical session: `projects/pcr02-ssc305/archive/engineering-archive/pcr02/session/pcr02_customer_ro_sd_upgrade_20260526.md`; `pcr02-customer-ro-sd-upgrade-session-20260526`
- PCR02 SIGBUS core/debug tools historical session: `projects/xcrz-sigmastar-demo/archive/debug/2026-05-15-pcr02-sigbus-core-debug-tools-history.md`; `pcr02-sigbus-core-debug-tools-history-20260515`
- PCR02 GROS/SSC305/HDI historical session: `projects/pcr02-ssc305/archive/engineering-archive/pcr02/session/pcr02_build_gros_hdi_history_20260517_20260521.md`; `pcr02-build-gros-hdi-history-20260517-20260521`
- PCR02 SSC305 2026-05-19 release validation historical record: `projects/pcr02-ssc305/archive/engineering-archive/pcr02/ota-release/pcr02_release_validation_20260519.md`; `pcr02-release-validation-20260519`
- PCR02 media monotonic PTS DVR/MP4 historical analysis: `projects/pcr02-ssc305/archive/engineering-archive/pcr02/media-timing/pcr02_media_monotonic_pts_dvr_mp4_20260630.md`; `pcr02-media-monotonic-pts-dvr-mp4-20260630`
- PCR02 core/GDB triage historical debug record: `projects/xcrz-sigmastar-demo/archive/debug/2026-06-23-pcr02-core-gdb-triage.md`; `pcr02-core-gdb-triage-20260623`
- PCR02 DVR protocol sync build fix historical record: `projects/xcrz-sigmastar-demo/archive/reports/2026-06-30-dvr-protocol-sync-build-fix.md`; `pcr02-dvr-protocol-sync-build-fix-20260630`
- PCR02 regular OTA customer partition guard historical delta: `projects/pcr02-ssc305/archive/engineering-archive/pcr02/ota-release/pcr02_regular_ota_customer_partition_guard_20260625.md`; `pcr02-regular-ota-customer-partition-guard-20260625`
- PCR02 IR light/player/WiFi debug summary from 2026-07-08 daily split: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-08-pcr02-irlight-player-wifi-debug-summary.md`; `pcr02-irlight-player-wifi-debug-summary-20260708`
- PCR02 Video/Audio 共享内存使用说明: `projects/xcrz-sigmastar-demo/current/runbooks/video-audio-shm-usage.md`; `pcr02-video-audio-shm-usage-20260713`
- PCR02 ST77912 黑屏与 LCD ESD 根因记录: `projects/pcr02-ssc305/archive/debug/2026-07-14-st77912-black-screen-esd-root-cause.md`; `pcr02-st77912-black-screen-esd-root-cause-20260714`

## Firmware Release Tools

- Project entry: `projects/firmware-release-tools/README.md`
- NAS release sync historical session: `projects/firmware-release-tools/archive/release/2026-05-18-nas-release-sync-session.md`; `firmware-release-tools-nas-release-sync-session-20260518`
- MCU memory-curation coverage includes firmware-release-tools NAS governance history: `projects/mcu/archive/2026-05-18-mcu-memory-curation-coverage.md`; `mcu-memory-curation-coverage-20260518`
- Firmware Release Tools readiness validation: `projects/firmware-release-tools/validation/project-readiness.md`; `firmware-release-tools-readiness-validation-20260713`

## MCU

- GD32/HC32 Codex maintenance historical session: `projects/mcu/archive/2026-05-17-gd32-hc32-codex-maintenance-session.md`; `mcu-gd32-hc32-codex-maintenance-session-20260517`
- MCU memory-curation coverage historical record: `projects/mcu/archive/2026-05-18-mcu-memory-curation-coverage.md`; `mcu-memory-curation-coverage-20260518`
- GD32L235 app_boot_v1 refactor historical session: `projects/mcu/archive/2026-05-24-gd32l235-app-boot-refactor-session.md`; `mcu-gd32l235-app-boot-refactor-session-20260524`
- MCU release NAS guard governance historical record: `projects/mcu/archive/2026-06-29-mcu-release-nas-guard-governance.md`; `mcu-release-nas-guard-governance-20260629`

## LLM Tools

- Windows builder runbook 候选归档: `projects/llm-tools/archive/release/2026-07-09-windows-builder-runbook.md`; `llm-tools-windows-builder-runbook-20260709`
- Release governance archive: `projects/llm-tools/archive/release/2026-05-16-llm-tools-release-governance.md`; `llm-tools-release-governance-archive-20260516`
- Three-repo governance historical session: `projects/llm-tools/archive/release/2026-05-17-llm-tools-three-repo-governance-session.md`; `llm-tools-three-repo-governance-session-20260517`
- Normal iteration historical policy: `projects/llm-tools/archive/release/2026-05-17-llm-tools-normal-iteration-policy.md`; `llm-tools-normal-iteration-policy-20260517`
- v1.0.0 release memory review historical record: `projects/llm-tools/archive/release/2026-05-19-llm-tools-v1-release-memory-review.md`; `llm-tools-v1-release-memory-review-20260519`
- Migrated old source deletion tombstone: `artifacts/manifests/codex-archive-removal-execution-20260710-migrated-extract-first.md`; `codex-archive-removal-execution-20260710-migrated-extract-first`
- LLM Tools readiness validation: `projects/llm-tools/validation/project-readiness.md`; `llm-tools-readiness-validation-20260713`

## XCRZ SigmaStar Demo

- Dual-screen animation historical analysis: `projects/xcrz-sigmastar-demo/archive/reports/2026-05-14-dual-screen-animation-analysis.md`; `xcrz-sigmastar-demo-dual-screen-animation-analysis-20260514`
- Migrated old source deletion tombstone: `artifacts/manifests/codex-archive-removal-execution-20260710-migrated-extract-first.md`; `codex-archive-removal-execution-20260710-migrated-extract-first`
- XCRZ SigmaStar Demo readiness validation: `projects/xcrz-sigmastar-demo/validation/project-readiness.md`; `xcrz-sigmastar-demo-readiness-validation-20260713`
- PCR02 ST77912 双屏显示 CPU 热点 ADB 实机排障记录: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-13-st77912-dual-display-cpu-adb-triage.md`; `xcrz-sigmastar-demo-st77912-dual-display-cpu-adb-triage-20260713`
- PCR02 ST77912 局部刷新图像割裂与残留 ADB 排障记录: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-14-st77912-partial-refresh-visual-regression.md`; `xcrz-sigmastar-demo-st77912-partial-refresh-visual-regression-20260714`
- PCR02 Sensor 静态数据上报 Task/App 联调指南: `projects/xcrz-sigmastar-demo/archive/reports/2026-07-14-sensor-static-info-integration-guide.md`; `xcrz-sigmastar-demo-sensor-static-info-integration-guide-20260714`
- PCR02 ST77912 局部刷新 pwrite 提交与 SPI 时钟驱动配置: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-15-st77912-partial-refresh-pwrite-commit-pad-drive.md`; `xcrz-sigmastar-demo-st77912-partial-refresh-pwrite-commit-pad-drive-20260715`
- PCR02 API/App/HDI/MP4 精确源码构建审计: `projects/xcrz-sigmastar-demo/validation/2026-07-15-module-clean-source-build-audit.md`; `pcr02-module-clean-source-build-audit-20260715`
- PCR02 Robot 子模块精确源码契约审计: `projects/xcrz-sigmastar-demo/validation/2026-07-15-robot-module-contract-audit.md`; `pcr02-robot-module-contract-audit-20260715`
- PCR02 双麦声学前处理、VAD、KWS 与 SigmaStar IPU 方案评估: `projects/xcrz-sigmastar-demo/archive/reports/2026-07-18-pcr02-audio-wakeup-afe-vad-kws-ipu-evaluation.md`; `xcrz-sigmastar-demo-audio-wakeup-afe-vad-kws-ipu-evaluation-20260718`
- PCR02 AISpeech VAD 与 QIVW 短期优化落地验证: `projects/xcrz-sigmastar-demo/validation/2026-07-18-pcr02-qivw-vad-short-term-implementation-validation.md`; `xcrz-sigmastar-demo-pcr02-qivw-vad-short-term-implementation-validation-20260718`
- PCR02 遗留 QIVW 回调与 APP diag provider 优化验证: `projects/xcrz-sigmastar-demo/validation/2026-07-18-pcr02-legacy-qivw-callback-optimization-validation.md`; `xcrz-sigmastar-demo-pcr02-legacy-qivw-callback-optimization-validation-20260718`
- PCR02 QIVW VAD gate 显式参数化更正与验证: `projects/xcrz-sigmastar-demo/validation/2026-07-18-pcr02-qivw-vad-gate-explicit-parameter-validation.md`; `xcrz-sigmastar-demo-pcr02-qivw-vad-gate-explicit-parameter-validation-20260718`
- xcrz_sigmastar_demo_dev 三目录完全吸收与删除验证: `projects/xcrz-sigmastar-demo/validation/2026-07-18-dev-copy-three-dir-absorption-validation.md`; `xcrz-sigmastar-demo-dev-copy-three-dir-absorption-validation-20260718`
- PCR02 IMU/TOF 驱动规格与运行时设计参考: `projects/xcrz-sigmastar-demo/archive/reports/2026-07-21-pcr02-imu-tof-driver-runtime-reference.md`; `pcr02-imu-tof-driver-runtime-reference-20260721`
- PCR02 双核 A32 整机 CPU 优化规划: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-21-pcr02-dual-a32-system-cpu-optimization-plan.md`; `pcr02-dual-a32-system-cpu-optimization-plan-20260721`
- PCR02 SoC TCPKA 协议 v1 与低功耗生命周期实现归档: `projects/xcrz-sigmastar-demo/archive/reports/2026-07-22-pcr02-tcpka-low-power-protocol-v1.md`; `pcr02-tcpka-low-power-protocol-v1-20260722`
- PCR02 视频虚拟流降频与 LCD libyuv NEON 优化记录: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-22-pcr02-video-virtual-stream-cpu-optimization.md`; `pcr02-video-virtual-stream-cpu-optimization-20260722`
- PCR02 VENC main/sub 发布序号独立化记录: `projects/xcrz-sigmastar-demo/archive/reports/2026-07-23-pcr02-venc-main-sub-sequence-isolation.md`; `pcr02-venc-main-sub-sequence-isolation-20260723`
- PCR02 prog_pcr02 高负载 2026-07-24 最新状态跟踪: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-24-prog-pcr02-high-load-followup.md`; `pcr02-prog-pcr02-high-load-followup-20260724`
- PCR02 SSC305 SDK裁剪与启动、资源、功耗优化规划: `projects/xcrz-sigmastar-demo/archive/reports/2026-07-24-pcr02-ssc305-sdk-trimming-optimization-plan.md`; `pcr02-ssc305-sdk-trimming-optimization-plan-20260724`
- PCR02 SSC305 SDK裁剪规划运行态基线验证: `projects/xcrz-sigmastar-demo/validation/2026-07-24-pcr02-ssc305-runtime-resource-baseline.md`; `pcr02-ssc305-runtime-resource-baseline-20260724`
- PCR02 MCU/SoC 电机 UART 时间戳同步与实时链路最终方案: `projects/xcrz-sigmastar-demo/archive/reports/2026-07-26-pcr02-motor-uart-timestamp-sync-plan.md`; `pcr02-motor-uart-timestamp-sync-plan-20260726`
- PCR02 HDI VI 30/1 fps 路由与 H26x teardown 排障记录: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-27-hdi-vi-30-1fps-scl-pool-teardown.md`; `xcrz-sigmastar-demo-hdi-vi-30-1fps-scl-pool-teardown-20260727`
- PCR02 电机 UART 时间戳同步实施与离线验证: `projects/xcrz-sigmastar-demo/validation/2026-07-27-pcr02-motor-uart-timestamp-sync-implementation.md`; `pcr02-motor-uart-timestamp-sync-implementation-validation-20260727`
- PCR02 app_uart 时间同步与低功耗 ACK 槽竞争: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-28-app-uart-time-sync-low-power-busy.md`; `pcr02-app-uart-time-sync-low-power-busy-20260728`
- PCR02 ACTIVE_LOW_1 COLD 切换耗时优化决策: `projects/xcrz-sigmastar-demo/current/decisions/active-low-1-cold-switch-latency-optimization.md`; `pcr02-active-low-1-cold-switch-latency-optimization-20260728`
- PCR02 ACTIVE_LOW_1 WARM切换实验决策: `projects/xcrz-sigmastar-demo/current/decisions/active-low-1-warm-switch-experiment.md`; `pcr02-active-low-1-warm-switch-experiment-20260728`
- PCR02 ACTIVE_LOW_1 HOT切换实验决策: `projects/xcrz-sigmastar-demo/current/decisions/active-low-1-hot-switch-experiment.md`; `pcr02-active-low-1-hot-switch-experiment-20260728`
- PCR02 1/30fps 代码规范收敛与板级复验: `projects/xcrz-sigmastar-demo/validation/2026-07-28-vi-fps-code-quality-closeout.md`; `pcr02-vi-fps-code-quality-closeout-20260728`
- PCR02 VI 1/30fps 同步抽象规范收敛验证: `projects/xcrz-sigmastar-demo/validation/2026-07-28-vi-fps-sync-abstraction-closeout.md`; `pcr02-vi-fps-sync-abstraction-closeout-20260728`
- PCR02 2026-07-28 电机时间戳与低功耗联调收口: `projects/xcrz-sigmastar-demo/archive/reports/2026-07-28-pcr02-motor-uart-low-power-session-closeout.md`; `pcr02-motor-uart-low-power-session-closeout-20260728`
- PCR02 1/30fps Pipeline全量整改与板级验证: `projects/xcrz-sigmastar-demo/validation/2026-07-28-vi-fps-full-optimization-closeout.md`; `pcr02-vi-fps-full-optimization-closeout-20260728`
- PCR02 libmsc Lua RPC释放后使用core分析: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-24-libmsc-lua-rpc-use-after-free.md`; `pcr02-libmsc-lua-rpc-use-after-free-20260724`
- PCR02 Agora下行音频STARVE与丢尾音分析: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-13-agora-downlink-audio-starve-tail-loss.md`; `pcr02-agora-downlink-audio-starve-tail-loss-20260713`
- PCR02扫码配网显示状态机缺口分析: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-02-wifi-provision-display-state-gap.md`; `pcr02-wifi-provision-display-state-gap-20260702`
- PCR02 ZMQ context与mailbox生命周期崩溃分析: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-02-zmq-context-mailbox-lifecycle-crash.md`; `pcr02-zmq-context-mailbox-lifecycle-crash-20260702`
- PCR02 DVR回放SD热拔插闭环验证: `projects/xcrz-sigmastar-demo/validation/2026-07-15-dvr-replay-sd-hot-unplug-closure.md`; `pcr02-dvr-replay-sd-hot-unplug-closure-20260715`
- PCR02电机标定静态信息缓存语义验证: `projects/xcrz-sigmastar-demo/validation/2026-07-15-motor-calibration-static-info-cache.md`; `pcr02-motor-calibration-static-info-cache-20260715`
- PCR02电机Hall校准前置事务验证: `projects/xcrz-sigmastar-demo/validation/2026-07-24-motor-hall-calibration-prestart-transaction.md`; `pcr02-motor-hall-calibration-prestart-transaction-20260724`
- PCR02 QR_CODE_SN字符校验失败分析: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-28-qr-code-sn-character-validation.md`; `pcr02-qr-code-sn-character-validation-20260728`
- PCR02老化健康上报与超时契约归档: `projects/xcrz-sigmastar-demo/archive/design/2026-07-17-aging-health-report-timeout-contract.md`; `pcr02-aging-health-report-timeout-contract-20260717`
- PCR02 AI音频流顺序与EOF语义契约归档: `projects/xcrz-sigmastar-demo/archive/design/2026-07-13-ai-audio-stream-order-eof-contract.md`; `pcr02-ai-audio-stream-order-eof-contract-20260713`
- PCR02 ACTIVE_LOW_1 Profile Switch Mode当前决策: `projects/xcrz-sigmastar-demo/current/decisions/active-low-1-profile-switch-mode.md`; `pcr02-active-low-1-profile-switch-mode-20260729`
- PCR02 player 单调时钟与请求确认优化验证: `projects/xcrz-sigmastar-demo/validation/reports/2026-07-29-player-monotonic-sync-validation.md`; `pcr02-player-monotonic-sync-validation-20260729`
- PCR02 API消息队列并发创建导致Player/UART串消息验证: `projects/xcrz-sigmastar-demo/validation/reports/2026-07-30-api-msg-player-uart-crosstalk-validation.md`; `pcr02-api-msg-player-uart-crosstalk-validation-20260730`
- PCR02 DEEP_SLEEP ARMED ACK 物理发送完成与 PA15 切电诊断: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-30-deep-sleep-ack-completion.md`; `pcr02-deep-sleep-ack-completion-20260730`
- PCR02 Sensor 全面测试资产基线: `projects/xcrz-sigmastar-demo/validation/2026-07-30-app-sensor-test-foundation.md`; `pcr02-app-sensor-test-foundation-20260730`
- PCR02 Sensor 分层全面测试框架基线: `projects/xcrz-sigmastar-demo/validation/2026-07-30-app-sensor-test-framework.md`; `pcr02-app-sensor-test-framework-20260730`
- PCR02 Sensor 测试框架 v3 硬切换验证记录: `projects/xcrz-sigmastar-demo/validation/2026-07-31-app-sensor-test-v3-hard-cut.md`; `pcr02-app-sensor-test-v3-hard-cut-20260731`
- PCR02 SSC305 物理1fps/30fps VIF Sleep切换优化归档: `projects/xcrz-sigmastar-demo/archive/reports/2026-07-31-pcr02-vi-fps-vif-sleep-optimization.md`; `pcr02-vi-fps-vif-sleep-optimization-20260731`
- PCR02 Sensor 全面测试框架落地验证记录: `projects/xcrz-sigmastar-demo/validation/2026-07-31-app-sensor-test-comprehensive-closure.md`; `pcr02-app-sensor-test-comprehensive-closure-20260731`
- app_sensor_test JSONL v4 与 HIL 证据闭环验证: `projects/xcrz-sigmastar-demo/validation/2026-07-31-app-sensor-test-v4-evidence-closure.md`; `app-sensor-test-v4-evidence-closure-20260731`
- PCR02 1/30fps 优化提交推送与最终验收: `projects/xcrz-sigmastar-demo/validation/2026-07-31-vi-fps-publish-validation.md`; `pcr02-vi-fps-publish-validation-20260731`
- app_sensor_test 选择完整性、构建身份与性能门禁验证: `projects/xcrz-sigmastar-demo/validation/2026-07-31-app-sensor-test-selection-performance-closure.md`; `app-sensor-test-selection-performance-closure-20260731`
- app_sensor_test 证据裁决、并发真实性与 CI 硬门禁验证: `projects/xcrz-sigmastar-demo/validation/2026-07-31-app-sensor-test-evidence-ci-hardcut.md`; `app-sensor-test-evidence-ci-hardcut-20260731`
- app_sensor_test staged safe 板测 transport 阻塞: `projects/xcrz-sigmastar-demo/validation/2026-07-31-app-sensor-test-board-safe-smoke-blocked.md`; `app-sensor-test-board-safe-smoke-blocked-20260731`
- PCR02 prog_pcr02 匿名堆持续增长监控记录: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-31-prog-pcr02-memory-growth-monitoring.md`; `pcr02-prog-pcr02-memory-growth-monitoring-20260731`
- PCR02 Sensor audio queue 满与 MI AO 非对齐重试闭环: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-31-pcr02-sensor-audio-queue-ao-retry.md`; `pcr02-sensor-audio-queue-ao-retry-20260731`
- PCR02 Sensor/WiFi 多 WiFi 存储与切换方案评审: `projects/xcrz-sigmastar-demo/current/designs/2026-08-03-pcr02-sensor-wifi-multi-network-design.md`; `pcr02-sensor-wifi-multi-network-design-20260803`
- daemon 与 prog_ota UART 独占租约验证: `projects/xcrz-sigmastar-demo/validation/2026-08-04-daemon-ota-uart-lease-validation.md`; `daemon-ota-uart-lease-validation-2026-08-04`
- PCR02 AI视频输出帧率联调归档: `projects/xcrz-sigmastar-demo/archive/reports/2026-08-04-ai-video-output-fps-integration.md`; `pcr02-ai-video-output-fps-integration-20260804`
- prog_pcr02 Common/Proto预编译库不一致排障: `projects/xcrz-sigmastar-demo/archive/debug/2026-08-05-prog-pcr02-common-proto-link-failure.md`; `xcrz-prog-pcr02-common-proto-link-debug-20260805`
- PCR02 TCPKA payload 与服务端路由校验优化: `projects/xcrz-sigmastar-demo/archive/debug/2026-08-05-pcr02-tcpka-payload-server-alignment.md`; `pcr02-tcpka-payload-server-alignment-20260805`
- PCR02新增QIVW诊断调用后的libmsc链接契约排障: `projects/xcrz-sigmastar-demo/archive/debug/2026-08-06-pcr02-libmsc-link-contract.md`; `xcrz-pcr02-libmsc-link-contract-debug-20260806`
- PCR02 Valgrind OpenSSL ARMv7 计数器与 MI 设备门禁排障记录: `projects/xcrz-sigmastar-demo/archive/debug/2026-08-12-valgrind-openssl-armv7-tick-mi-device-gate.md`; `pcr02-valgrind-openssl-armv7-tick-mi-device-gate-20260812`
- PCR02 ASan protobuf 容器注解失配与独立回调崩溃排障记录: `projects/xcrz-sigmastar-demo/archive/debug/2026-08-12-asan-protobuf-container-annotation-and-callback-segv.md`; `pcr02-asan-protobuf-container-annotation-callback-segv-20260812`
- PCR02 显示动作自切换导致 nextAction_ 悬空引用: `projects/xcrz-sigmastar-demo/archive/debug/2026-08-12-asan-display-action-nextaction-uaf.md`; `pcr02-asan-display-action-nextaction-uaf-20260812`
- PCR02 显示动作 UAF 源码修复验证: `projects/xcrz-sigmastar-demo/validation/2026-08-12-asan-display-action-uaf-fix.md`; `pcr02-asan-display-action-uaf-fix-validation-20260812`
- PCR02 持续视频预览离线与内存池耗尽排障记录: `projects/xcrz-sigmastar-demo/archive/debug/2026-08-13-pcr02-video-soak-memory-deadlock.md`; `pcr02-video-soak-memory-deadlock-20260813`
- HDI/HAL 跨平台与 Host 开发测试架构决策候选: `projects/xcrz-sigmastar-demo/decisions/hdi-hal-cross-platform-host-development-architecture-20260813.md`; `pcr02-hdi-hal-cross-platform-host-development-architecture-20260813`
- HDI/HAL 跨平台与 Host 开发测试方案审查记录: `projects/xcrz-sigmastar-demo/validation/hdi-hal-cross-platform-host-development-review-20260813.md`; `pcr02-hdi-hal-cross-platform-host-development-review-20260813`
- HDI/HAL 跨平台与 Host 开发测试架构决策候选 v2: `projects/xcrz-sigmastar-demo/decisions/hdi-hal-cross-platform-host-development-architecture-20260813-v2.md`; `pcr02-hdi-hal-cross-platform-host-development-architecture-20260813-v2`
- HDI/HAL 跨平台与 Host 开发测试方案审查记录 v2: `projects/xcrz-sigmastar-demo/validation/hdi-hal-cross-platform-host-development-review-20260813-v2.md`; `pcr02-hdi-hal-cross-platform-host-development-review-20260813-v2`
- Diag、Observability 与 Maintenance 跨平台平面决策候选: `projects/xcrz-sigmastar-demo/decisions/diag-observability-maintenance-cross-platform-plane-20260813.md`; `pcr02-diag-observability-maintenance-cross-platform-plane-20260813`
- Diag、Observability 与 Maintenance 平面架构审查记录: `projects/xcrz-sigmastar-demo/validation/diag-observability-maintenance-plane-review-20260813.md`; `pcr02-diag-observability-maintenance-plane-review-20260813`
- HDI/HAL/Diag 跨平台硬切换与 Host 自动化架构决策候选 v3: `projects/xcrz-sigmastar-demo/decisions/hdi-hal-cross-platform-host-development-architecture-20260813-v3.md`; `pcr02-hdi-hal-cross-platform-host-development-architecture-20260813-v3`
- Diag、Observability 与 Maintenance 硬切换平面决策候选 v2: `projects/xcrz-sigmastar-demo/decisions/diag-observability-maintenance-cross-platform-plane-20260813-v2.md`; `pcr02-diag-observability-maintenance-cross-platform-plane-20260813-v2`
- HDI/HAL/Diag 硬切换与零残留架构审查记录: `projects/xcrz-sigmastar-demo/validation/hdi-hal-diag-hard-cut-review-20260813.md`; `pcr02-hdi-hal-diag-hard-cut-review-20260813`
- HDI/HAL/Diag 跨平台硬切换与 Host 自动化最终架构基线 v4: `projects/xcrz-sigmastar-demo/decisions/hdi-hal-cross-platform-host-development-architecture-20260813-v4.md`; `pcr02-hdi-hal-cross-platform-host-development-architecture-20260813-v4`
- Diag Observability Maintenance 跨平台最终平面规范 v3: `projects/xcrz-sigmastar-demo/decisions/diag-observability-maintenance-cross-platform-plane-20260813-v3.md`; `pcr02-diag-observability-maintenance-cross-platform-plane-20260813-v3`
- HDI/HAL/Diag 跨平台重构最终方案审查与定案: `projects/xcrz-sigmastar-demo/validation/hdi-hal-diag-final-architecture-determination-20260813.md`; `pcr02-hdi-hal-diag-final-architecture-determination-20260813`
- HDI HAL Diag AI MP4 跨平台硬切最终复审: `projects/xcrz-sigmastar-demo/archive/reports/2026-08-14-hdi-hal-diag-ai-mp4-hard-cut-final-review.md`; `xcrz-hdi-hal-diag-ai-mp4-hard-cut-final-review-20260814`
- PCR02 WARM低帧率VIF sleep引发CMDQ异常: `projects/xcrz-sigmastar-demo/archive/debug/2026-08-14-warm-vif-sleep-cmdq-regression.md`; `xcrz-pcr02-warm-vif-sleep-cmdq-debug-20260814`
- PCR02 WARM当前业务负载CMDQ异常V2: `projects/xcrz-sigmastar-demo/archive/debug/2026-08-15-warm-current-workload-cmdq-regression-v2.md`; `xcrz-pcr02-warm-current-workload-cmdq-debug-v2-20260815`
- OSAL Platform HDI 终版边界与硬切验证: `projects/xcrz-sigmastar-demo/decisions/osal-platform-hdi-final-boundary-20260817.md`; `xcrz-osal-platform-hdi-final-boundary-20260817`

## PCR02 SSC305 SDK

- PCR02 SSC305 SDK readiness validation: `projects/pcr02-ssc305/validation/project-readiness.md`; `pcr02-ssc305-readiness-validation-20260713`
- PCR02 IMSSV06C11 三方 SDK 审计：摄像头 AE、SPI NAND 与时钟电气路径: `projects/pcr02-ssc305/archive/source-audit/pcr02_imssv06c11_three_way_sdk_audit_20260715.md`; `pcr02-imssv06c11-three-way-sdk-audit-20260715`
- PCR02 项目组规范入口边界决策候选: `projects/pcr02-ssc305/decisions/pcr02-canonical-hardcut-20260715.md`; `pcr02-ssc305-canonical-hardcut-20260715`
- PCR02 新摄像头栈混装 ABI 故障与回退记录: `projects/pcr02-ssc305/archive/debug/2026-07-15-camera-mi-abi-rollback.md`; `pcr02-camera-mi-abi-mix-rollback-20260715`
- PCR02 SOC v1.1.33 NAS 发布证据审计: `projects/pcr02-ssc305/validation/2026-07-15-soc-v1.1.33-nas-release-audit.md`; `pcr02-soc-v1-1-33-nas-release-audit-20260715`
- embedded/knowledge SSC305 方法与工具引用吸收验证: `projects/pcr02-ssc305/validation/2026-07-18-embedded-knowledge-absorption-validation.md`; `pcr02-ssc305-embedded-knowledge-absorption-validation-20260718`
- PCR02 /data UBIFS 单页节点整体偏移 4 字节导致只读排障记录: `projects/pcr02-ssc305/archive/engineering-archive/pcr02/ubifs-squashfs/pcr02_data_ubifs_single_page_shift_readonly_20260720.md`; `pcr02-data-ubifs-single-page-shift-readonly-20260720`
- PCR02 SSC305 SDK系统优化实施计划: `projects/pcr02-ssc305/archive/reports/2026-07-24-sdk-system-optimization-plan.md`; `pcr02-ssc305-sdk-system-optimization-plan-20260724`
- PCR02 SSC305 ACTIVE_LOW_1组件化Pipeline与日夜策略: `projects/pcr02-ssc305/archive/design/2026-07-27-active-low-1-pipeline-architecture.md`; `pcr02-active-low-1-pipeline-architecture-20260727`
- PCR02 ACTIVE_LOW_1无H26x流关闭light-meter决策: `projects/pcr02-ssc305/decisions/active-low-1-no-h26x-light-meter-power-gate-20260727.md`; `pcr02-active-low-1-no-h26x-light-meter-power-gate-20260727`
- PCR02 BCMDHD suspend 竞态与可启动 SD 边界: `projects/pcr02-ssc305/archive/debug/2026-07-28-bcmdhd-suspend-and-sd-boot-boundary.md`; `pcr02-bcmdhd-suspend-sd-boot-boundary-20260728`
- PCR02 active 媒体 CPU 与 VENC 等待优化验证: `projects/pcr02-ssc305/validation/2026-07-31-active-media-cpu-venc-timeout.md`; `pcr02-ssc305-active-media-cpu-venc-timeout-20260731`
- PCR02 原理图第二批静态优化决策: `projects/pcr02-ssc305/decisions/pcr02-schematic-second-batch-static-optimization-20260802.md`; `pcr02-schematic-second-batch-static-optimization-20260802`
- PCR02 debug/release rootfs 与 OTA 边界决策: `projects/pcr02-ssc305/decisions/pcr02-debug-release-rootfs-policy-20260803.md`; `pcr02-debug-release-rootfs-policy-20260803`
- PCR02 release 网络恢复与启动时序分析: `projects/pcr02-ssc305/archive/debug/2026-08-03-release-network-and-boot-analysis.md`; `pcr02-release-network-boot-analysis-20260803`
- PCR02 Release 生产化、安全与性能优化范围: `projects/pcr02-ssc305/decisions/pcr02-release-production-hardening-scope-20260803.md`; `pcr02-release-production-hardening-scope-20260803`
- PCR02 customer 静态 UBI 卷启动扫描优化候选: `projects/pcr02-ssc305/decisions/pcr02-customer-ubi-startup-optimization-20260803.md`; `pcr02-customer-ubi-startup-optimization-20260803`
- PCR02 customer UBI 启动优化复核决策候选: `projects/pcr02-ssc305/decisions/pcr02-customer-ubi-startup-optimization-review-20260804.md`; `pcr02-customer-ubi-startup-optimization-review-20260804`
- PCR02 release 暂时保留 NFS 客户端: `projects/pcr02-ssc305/decisions/2026-08-04-release-nfs-client-retention.md`; `pcr02-release-nfs-client-retention-20260804`
- PCR02 no-clean 编译与 debug 镜像体积排障: `projects/pcr02-ssc305/archive/debug/2026-08-04-no-clean-and-debug-image-build.md`; `pcr02-no-clean-debug-image-build-20260804`
- PCR02 diag 大文件直链下载实现与构建边界验证: `projects/pcr02-ssc305/validation/2026-08-06-diag-curl-large-download.md`; `pcr02-diag-curl-large-download-validation-20260806`

## PCR02 API Module

- PCR02 API Module readiness validation: `projects/pcr02-api/validation/project-readiness.md`; `pcr02-api-readiness-validation-20260713`

## PCR02 App Module

- PCR02 App Module readiness validation: `projects/pcr02-app/validation/project-readiness.md`; `pcr02-app-readiness-validation-20260713`

## PCR02 HDI Module

- PCR02 HDI Module readiness validation: `projects/pcr02-hdi/validation/project-readiness.md`; `pcr02-hdi-readiness-validation-20260713`

## PCR02 Sensor Module

- PCR02 Sensor Module readiness validation: `projects/pcr02-sensor/validation/project-readiness.md`; `pcr02-sensor-readiness-validation-20260713`

## PCR02 Daemon App

- PCR02 Daemon App readiness validation: `projects/pcr02-daemon/validation/project-readiness.md`; `pcr02-daemon-readiness-validation-20260713`

## PCR02 CLI App

- PCR02 CLI App readiness validation: `projects/pcr02-cli/validation/project-readiness.md`; `pcr02-cli-readiness-validation-20260713`

## PCR02 Command Server App

- PCR02 Command Server App readiness validation: `projects/pcr02-cmd-server/validation/project-readiness.md`; `pcr02-cmd-server-readiness-validation-20260713`

## PCR02 Proto C App

- PCR02 Proto C App readiness validation: `projects/pcr02-proto-c/validation/project-readiness.md`; `pcr02-proto-c-readiness-validation-20260713`

## PCR02 Wi-Fi Module

- PCR02 Wi-Fi Module readiness validation: `projects/pcr02-wifi/validation/project-readiness.md`; `pcr02-wifi-readiness-validation-20260713`

## PCR02 MP4 Module

- PCR02 MP4 Module readiness validation: `projects/pcr02-mp4/validation/project-readiness.md`; `pcr02-mp4-readiness-validation-20260713`

## PCR02 OTA App

- PCR02 OTA App readiness validation: `projects/app-ota/validation/project-readiness.md`; `app-ota-readiness-validation-20260713`

## PCR02 Product Test App

- PCR02 Product Test App readiness validation: `projects/app-product-test/validation/project-readiness.md`; `app-product-test-readiness-validation-20260713`

## PCR02 Tool App

- PCR02 Tool App readiness validation: `projects/app-tool/validation/project-readiness.md`; `app-tool-readiness-validation-20260713`

## PCR02 Main App

- PCR02 Main App readiness validation: `projects/app-main/validation/project-readiness.md`; `app-main-readiness-validation-20260713`

## MCU Firmware Group

- MCU Firmware Group readiness validation: `projects/mcu/validation/project-readiness.md`; `mcu-readiness-validation-20260713`
- MCU NAS 发布制品与契约验证 2026-07-15: `projects/mcu/validation/2026-07-15-nas-release-evidence-audit.md`; `mcu-release-evidence-audit-20260715`

## GD32L235 Firmware

- GD32L235 Firmware readiness validation: `projects/gd32l235/validation/project-readiness.md`; `gd32l235-readiness-validation-20260713`
- GD32L235 PA12 快慢充控制与硬件兼容性归档: `projects/gd32l235/archive/design/2026-07-13-pa12-fast-slow-charge-compatibility.md`; `gd32l235-pa12-fast-slow-charge-compatibility-20260713`
- GD32L235 电池供电跳变与 MCU 循环重启排障记录: `projects/gd32l235/archive/debug/2026-07-17-battery-rail-drop-mcu-reboot.md`; `gd32l235-battery-rail-drop-mcu-reboot-20260717`
- GD32L235 与 PCR02 SoC 电源状态、TCPKA 和关机事务协同归档: `projects/gd32l235/archive/design/2026-07-22-soc-mcu-power-transition-owner-tcpka.md`; `gd32l235-pcr02-power-transition-owner-tcpka-20260722`
- GD32L235 与 PCR02 SOC SLEEP EBUSY 和提前 WiFi 唤醒初步排查: `projects/gd32l235/archive/debug/2026-07-22-soc-sleep-ebusy-early-wifi-wake.md`; `gd32l235-soc-sleep-ebusy-early-wifi-wake-20260722`
- GD32L235 低电量 SOC 休眠保护设计归档: `projects/gd32l235/archive/design/2026-07-22-low-battery-soc-sleep-protection-design.md`; `gd32l235-low-battery-soc-sleep-protection-design-20260722`
- GD32L235 PA11 关机、充电与 SOC 上电门控设计归档: `projects/gd32l235/archive/design/2026-07-22-pa11-charge-soc-power-gate-design.md`; `gd32l235-pa11-charge-soc-power-gate-design-20260722`
- GD32L235 与 SOC Shutdown 确认闭环设计归档: `projects/gd32l235/archive/design/2026-07-22-soc-shutdown-confirmation-closure-design.md`; `gd32l235-soc-shutdown-confirmation-closure-design-20260722`
- GD32L235 与 SOC 心跳状态同步终态方案归档: `projects/gd32l235/archive/design/2026-06-16-soc-heartbeat-terminal-state-plan.md`; `gd32l235-soc-heartbeat-terminal-state-plan-20260616`
- GD32L235 与 SOC 心跳、重启和 OTA 闭环会话归档: `projects/gd32l235/archive/session/2026-06-17-soc-heartbeat-reboot-ota-closure-session.md`; `gd32l235-soc-heartbeat-reboot-ota-closure-session-20260617`
- GD32L235 与 SOC 退出、休眠和掉电管理会话归档: `projects/gd32l235/archive/session/2026-06-04-soc-exit-poweroff-management-session.md`; `gd32l235-soc-exit-poweroff-management-session-20260604`
- GD32L235 与 PCR02 SoC 低功耗协同当前契约候选: `projects/gd32l235/current/soc-low-power-contract.md`; `gd32l235-soc-low-power-contract`
- PCR02 SoC 与 GD32L235 传感器频率契约及 50 Hz 融合方案: `projects/gd32l235/archive/design/2026-07-23-sensor-rate-contract-and-50hz-fusion.md`; `gd32l235-pcr02-sensor-rate-contract-50hz-fusion-20260723`
- PCR02 SoC SLEEP 网络冻结与 wakeup_count 两阶段门禁决策候选: `projects/gd32l235/decisions/soc-sleep-network-freezer-wakeup-count.md`; `gd32l235-pcr02-soc-sleep-network-freezer-wakeup-count-20260724`
- GD32L235 与 PCR02 SoC DISARM 和传感器恢复事务归档: `projects/gd32l235/archive/design/2026-07-27-disarm-sensor-restore-transaction.md`; `gd32l235-pcr02-disarm-sensor-restore-validation-20260727`
- GD32L235 WiFi wake shadow 诊断与验证: `projects/gd32l235/archive/debug/2026-07-28-wifi-wake-shadow-validation.md`; `gd32l235-wifi-wake-shadow-validation-20260728`
- GD32L235 v1.1.40 NAS 发布记录: `projects/gd32l235/archive/release/2026-07-30-gd32l235-v1.1.40-nas-release.md`; `gd32l235-v1.1.40-nas-release-20260730`
- GD32L235 智能留电充电唤醒与低电策略归档: `projects/gd32l235/archive/design/2026-07-30-smart-reserve-charge-wakeup.md`; `gd32l235-smart-reserve-charge-wakeup-20260730`
- GD32L235 在桩检测有效但未发生净充电的当前结论: `projects/gd32l235/archive/debug/2026-07-31-dock-detected-without-net-charging-analysis.md`; `gd32l235-dock-detected-without-net-charging-analysis-20260731`
- GD32L235 POWER_KEY 退出中拨回 ON 的重启收敛: `projects/gd32l235/archive/debug/2026-08-03-power-key-exit-restart-convergence.md`; `gd32l235-power-key-exit-restart-convergence-20260803`
- GD32L235 与 PCR02 拨动开关 UART 快速交接实现归档: `projects/gd32l235/archive/session/2026-08-04-power-switch-uart-handoff-implementation.md`; `gd32l235-power-switch-uart-handoff-implementation-20260804`
- GD32L235 调试唤醒诊断 Flash 溢出与 OTA 回归记录: `projects/gd32l235/archive/debug/2026-08-04-debug-wakeup-flash-overflow-and-ota-regression.md`; `gd32l235-debug-wakeup-flash-overflow-ota-regression-20260804`
- GD32L235 Power Diag 独立构建开关决策: `projects/gd32l235/decisions/power-diag-independent-build-switch.md`; `gd32l235-power-diag-independent-build-switch-20260804`
- GD32L235 APP_EXITED(OFF) 后拨回 ON 的硬恢复缺口: `projects/gd32l235/archive/debug/2026-08-04-power-off-hold-late-on-restart-gap.md`; `gd32l235-power-off-hold-late-on-restart-gap-20260804`
- GD32L235 v1.1.41 NAS 发布记录: `projects/gd32l235/archive/release/2026-08-05-gd32l235-v1.1.41-nas-release.md`; `gd32l235-v1.1.41-nas-release-20260805`
- GD32L235 PB12 WL_GPIO4 WoWLAN 引脚契约候选: `projects/gd32l235/current/pb12-wl-gpio4-contract.md`; `gd32l235-pb12-wl-gpio4-contract-20260812`
- GD32L235 充电温度软硬保护策略决策候选: `projects/gd32l235/decisions/charge-temperature-soft-hard-protection.md`; `gd32l235-charge-temperature-soft-hard-protection-20260812`
- GD32L235 可配置充电温度软硬保护策略决策候选: `projects/gd32l235/decisions/charge-temperature-configurable-soft-hard-protection.md`; `gd32l235-charge-temperature-configurable-soft-hard-protection-20260812`
- GD32L235 高温回桩热态充电治理策略决策候选: `projects/gd32l235/decisions/charge-temperature-thermal-governor-20260818.md`; `gd32l235-charge-temperature-thermal-governor-20260818`
- GD32L235 充电温度保护会话化与 PB10 计时归档: `projects/gd32l235/archive/design/2026-08-20-charge-temperature-session-protection.md`; `gd32l235-charge-temperature-session-protection-20260820`

## HC32F072 Firmware

- HC32F072 Firmware readiness validation: `projects/hc32f072/validation/project-readiness.md`; `hc32f072-readiness-validation-20260713`

## MM32SPIN023C Firmware

- MM32SPIN023C Firmware readiness validation: `projects/mm32spin023c/validation/project-readiness.md`; `mm32spin023c-readiness-validation-20260713`

## Firmware Toolchains

- Firmware Toolchains readiness validation: `projects/firmware-toolchains/validation/project-readiness.md`; `firmware-toolchains-readiness-validation-20260713`
- X5 AI Toolchain V1.2.8 下载与完整性验证: `projects/firmware-toolchains/validation/2026-08-05-x5-ai-toolchain-download.md`; `firmware-toolchains-x5-ai-toolchain-download-validation-20260805`
- X5 SDK V1.1.2 GitLab 层级镜像验证: `projects/firmware-toolchains/validation/2026-08-05-x5-v1.1.2-gitlab-mirror.md`; `firmware-toolchains-x5-v1-1-2-gitlab-mirror-validation-20260805`
- X5 SDK V1.1.2 固件构建验证: `projects/firmware-toolchains/validation/2026-08-05-x5-v1.1.2-firmware-build.md`; `firmware-toolchains-x5-v1-1-2-firmware-build-20260805`
- X5 SDK V1.1.2 DDR、eMMC、Camera 与 Wi-Fi 适配清单: `projects/firmware-toolchains/validation/2026-08-06-x5-v1.1.2-approved-vendor-list.md`; `firmware-toolchains-x5-v1-1-2-approved-vendor-list-20260806`
- X5 Integration P1 长期维护优化验证: `projects/firmware-toolchains/validation/2026-08-06-x5-integration-p1-maintainability.md`; `firmware-toolchains-x5-integration-p1-maintainability-20260806`
- X5 SDK版本化工作区迁移验证: `projects/firmware-toolchains/validation/2026-08-06-x5-versioned-workspace-migration.md`; `firmware-toolchains-x5-versioned-workspace-migration-20260806`
- X5 V1.1.2实机前交付闭环: `projects/firmware-toolchains/validation/2026-08-06-x5-pre-board-readiness.md`; `firmware-toolchains-x5-pre-board-readiness-20260806`

## LLM Agent

- LLM Agent readiness validation: `projects/llm-agent/validation/project-readiness.md`; `llm-agent-readiness-validation-20260713`
- LLM Agent 与 ADK 3.1 RC2 发布候选闭环验证: `projects/llm-agent/validation/adk-v3-1-rc2-release-closure-20260714.md`; `llm-agent-adk-v3-1-rc2-release-closure-20260714`
- LLM Agent 精确源码 Quick 门禁审计 2026-07-15: `projects/llm-agent/validation/2026-07-15-exact-source-quick-gate-audit.md`; `llm-agent-exact-source-quick-gate-audit-20260715`
- 微信公众号批量研究工作流与二十篇文章优化评估: `projects/llm-agent/archive/research/2026-07-16-wechat-account-research-optimization-assessment.md`; `llm-agent-wechat-account-research-assessment-20260716`
- LLM Agent 精确源码 Full 门禁审计 2026-07-17: `projects/llm-agent/validation/2026-07-17-exact-source-full-gate-audit.md`; `llm-agent-exact-source-full-gate-audit-20260717`
- LLM Agent 与 ADK 3.1 RC3 本地发布候选闭环验证: `projects/llm-agent/validation/adk-v3-1-rc3-release-closure-20260718.md`; `llm-agent-adk-v3-1-rc3-release-closure-20260718`
- llm_agent 与 agent-dev-kit 外部实践搜索及吸收候选: `projects/llm-agent/archive/research/2026-07-23-external-practice-absorption-candidates.md`; `llm-agent-external-practice-absorption-candidates-20260723`
- llm_agent 外部实践吸收落地: `projects/llm-agent/archive/research/2026-07-23-external-practice-absorption-implementation.md`; `llm-agent-external-practice-absorption-20260723`
- github/spec-kit 长期跟踪决策: `projects/llm-agent/decisions/2026-07-23-spec-kit-reference-tracking-decision.md`; `llm-agent-spec-kit-reference-tracking-20260723`
- github/spec-kit正式登记验证: `projects/llm-agent/validation/2026-07-23-spec-kit-reference-onboarding-validation.md`; `llm-agent-spec-kit-reference-onboarding-validation-20260723`

## Agent Dev Kit

- Agent Dev Kit readiness validation: `projects/agent-dev-kit/validation/project-readiness.md`; `agent-dev-kit-readiness-validation-20260713`
- Agent Dev Kit 团队 Harness Readiness v1 吸收决策候选: `projects/agent-dev-kit/decisions/harness-readiness-v1-candidate.md`; `agent-dev-kit-harness-readiness-decision-20260717`
- ADK Token 与上下文工作流优化验证: `projects/agent-dev-kit/validation/2026-08-01-token-context-workflow-optimization.md`; `agent-dev-kit-token-context-workflow-optimization-20260801`
- ADK/Codex/Hub Token 与门禁优化 v2: `projects/agent-dev-kit/validation/2026-08-01-token-context-governance-v2.md`; `agent-dev-kit-token-context-governance-v2-20260801`

## SigmaStar Flasher

- SigmaStar Flasher readiness validation: `projects/sigmastar-flasher/validation/project-readiness.md`; `sigmastar-flasher-readiness-validation-20260713`

## MM32SPIN Validator

- MM32SPIN Validator readiness validation: `projects/mm32spin-validator/validation/project-readiness.md`; `mm32spin-validator-readiness-validation-20260713`

## OTA Packager

- OTA Packager readiness validation: `projects/ota-packager/validation/project-readiness.md`; `ota-packager-readiness-validation-20260713`
- PCR02 IMU/TOF 高负载调度尾延迟现场分析: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-21-pcr02-imu-tof-high-load-scheduling-triage.md`; `pcr02-imu-tof-high-load-scheduling-triage-20260721`

## RDK X5 SDK

- X5 GitLab CE 多仓分支保护降级方案: `projects/x5-rdk/current/candidates/2026-08-15-gitlab-ce-branch-protection-fallback.md`; `x5-rdk-gitlab-ce-branch-protection-fallback-20260815`
- X5 Android repo 引用治理与安全清理: `projects/x5-rdk/current/candidates/2026-08-15-android-repo-manifest-ref-governance.md`; `x5-rdk-android-repo-ref-governance-20260815`
- X5 供应商资料不可变清单与修订协议: `projects/x5-rdk/current/candidates/2026-08-15-immutable-vendor-manifest-amendment.md`; `x5-rdk-immutable-vendor-manifest-amendment-20260815`
