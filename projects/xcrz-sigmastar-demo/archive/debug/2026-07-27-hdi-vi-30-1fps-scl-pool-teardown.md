---
id: xcrz-sigmastar-demo-hdi-vi-30-1fps-scl-pool-teardown-20260727
title: PCR02 HDI VI 30/1 fps 路由与 H26x teardown 排障记录
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-27-hdi-vi-30-1fps-scl-pool-teardown.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-project
  from: xcrz-sigmastar-demo HDI VI redesign, implementation, review and HIL evidence through 2026-07-27
  source_sha256: 79e3f66955adc8069cc6eade4e36da219a354ae2d95f181b7e8348a41fdbd791
review_after: '2026-08-31'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- hdi-vi
- media-pipeline
- debug-record
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-27-hdi-vi-30-1fps-scl-pool-teardown.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-27-hdi-vi-30-1fps-scl-pool-teardown.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-27'
updated_at: '2026-07-27'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-27'
manual_validation_pending: true
summary_zh: 记录 SSC305 物理30/1fps HOT证伪、安全COLD路由、SCL pool teardown高置信根因、资源journal修复、验证边界与待完成HIL。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 HDI VI 30/1 fps 路由与 H26x teardown 排障记录

captured_at：2026-07-27

## 现象

- 物理 30 fps / 1 fps 动态切换曾出现延迟、花屏风险和异步 ISP/VIF/LDC CMDQ reset。
- 安全 COLD 候选在一次 BOTH 30→1 切换中出现 FPS handler 永久阻塞；后续诊断超时，应用优雅退出也卡住。
- 现场序列停在 H26x VENC teardown 后、SCL/LDC/ISP 主链释放前。

## 影响范围

- 项目：XCRZ SigmaStar Demo / PCR02 SSC305。
- 模块：`hdi_vi`、SigmaStar SNR/VIF/ISP/LDC/SCL/VENC pipeline、诊断控制面。
- 当前结论只适用于已测试的 SSC305 与当前 sensor mode；不提升为跨平台通用规范。

## 环境

- 平台 SDK 参考代码和本地 SigmaStar 文档已与产品源码交叉核对。
- 设备 HIL 使用运行时注入的 ADB 端点和 NFS mount；现场端点、raw log、core 与二进制不进入本记录。
- 源码权威记录：
  - `HDI_VI_MEDIA_PIPELINE_REDESIGN.md`
  - `docs/changes/hdi-vi-pipeline-r3/STATE.md`
  - `docs/changes/hdi-vi-pipeline-r3/VERIFICATION.md`

## 时间线

| 阶段 | 操作或观察 | 结果 |
| --- | --- | --- |
| HOT 探索 | 动态 edge rebind + sensor FPS | 出现 ISP/VIF reset，证伪 |
| HOT 探索 | 保留 LDC 主链，仅动态 sensor FPS | 出现 SCL/LDC CMDQ reset，证伪 |
| HOT 探索 | 保持 RAW reader 排空 | 仍有 reset，且增加 CMDQ reset 面，撤回 |
| 安全路径 | 关闭 HOT capability，物理 FPS 选择 COLD rebuild | 上一候选 exact demand 与短循环通过 |
| teardown 异常 | BOTH COLD teardown 永久阻塞 | 定位到 SCL private ring pool 释放窗口 |
| 源码修复 | pool release 后移；增加 pool/output-role journal | host 合约、构建和本地制品门禁通过 |
| 安全部署 | NFS staged candidate + 显式主机备份 | frozen/staged/installed 身份一致；空间不足时先阻止 mutation |
| 最终 HIL | exact demand、BOTH 单次、连续 5 次 COLD | 全部通过；两类 journal 停止后清零，无新增 fatal/core |
| 收尾 | 恢复产品配置、NORMAL30、H26x stop、只读 mount | 最终 preflight stable，artifact gate already-installed |
| handoff 恢复 | 历史目标 transport 中断后切换到用户提供的新运行时端点 | 从 readonly preflight 重建证据；相同 installed identity，NORMAL30/H26x stop/motor estop/只读 mount/健康进程全部恢复 |

## 证据

- HOT 负向板端证据证明：同步 API 返回成功不能作为切换提交点；异步 reset 会在后续出现。
- 最终候选 5 轮中，30→1 为 1.638～1.713 秒、平均 1.670 秒；1→30 为 3.217～3.809 秒、平均 3.463 秒。
- 10 次 COLD transition 的 ISP `DestroyDevice` 为 0.997～1.000 秒、平均 0.999 秒，是 COLD 切换固定慢项之一；5 次 LDC init 为 1.025～1.178 秒、平均 1.079 秒，是 1→30 慢项之一。
- 最终源码执行顺序：拆 cascade/VENC pool/SCL→VENC edge，停止 RecvPic，停止 reader/RGN，停止或重配 SCL H26x output role，deinit VENC，最后释放 SCL private ring pool。
- `bSclPoolCreated` 与 `bSclOutputRoleActive` 仅在各自 cleanup 成功后清零，失败时可重试。
- app diag 暴露 `h26x_scl_output_role_active` 和 `h26x_scl_pool_created`，用于 HIL 检查资源泄漏。
- Host 验证：27 项 Python 测试通过，其中 13 项为 HDI VI source contract、14 项为 ADB runtime tool test；planner `-Wall -Wextra -Werror`、公共头同步和 HIL 脚本语法通过；HDI/app 库、PCR02 app 和 cmd server 构建通过。
- 最终冻结候选 BuildID：`495754fe8bc40c163a51774de1b1f47276739193`；MD5：`ac0a580e3bc89c44aa7dfc680ee1d4ed`。该身份只用于追溯本次候选，不表示 release/image/OTA 已更新。
- 最终 HIL bundle SHA256：exact demand `b69d3e51741cca02b594749b40b03870ea734c3f91b7d2678ae6cfdcd605fca8`；BOTH 单次 `3fc8f8175b4d5d335aa94696dad9161f399476d4669b07dfaf40ee07c89033d0`；BOTH 5 轮 `1d69b92418deef80db95ab7a0608ce82a54c0b0cd39cdb0d3e64d860df9e8eee`。
- handoff recovery 最终 preflight bundle SHA256：`4842e4fea31872fc7e785cf5ab38054499e51c976a781c248e4018fd73bdec35`；artifact gate bundle SHA256：`8bbbbb0060adcc823e25b7af82369808ef6252aff688a7db5bb1c09830393391`。

## 假设与排除

| 假设 | 验证动作 | 结果 | 状态 |
| --- | --- | --- | --- |
| 物理 FPS 可通过解绑、SetFps、重绑安全 HOT 切换 | 多个 HOT route 板端实验 | 均出现异步 reset | 已排除 |
| RAW reader 不排空是 reset 唯一原因 | 保持 RAW reader 排空 | reset 未消失 | 已排除 |
| ISP deinit 可完全避免 | HOT route 板端实测 | 当前平台 HOT 不安全 | 当前生产方案不成立 |
| SCL pool 过早释放导致永久阻塞 | 源码调用序列、平台 multi-ring teardown、现场停滞位置与最终候选 HIL 交叉核对 | exact/single/5-cycle 未再阻塞，journal 收敛 | 已在当前覆盖范围验证 |
| transport 丢失由当前媒体补丁唯一触发 | 检查时间窗口内的 Wi-Fi reconnect 与 auto-standby mutator | 无法建立唯一因果 | 未确认 |
| 第 5 轮 FPS 错误代表媒体资源泄漏 | 对照 60 秒 auto-standby 日志，隔离该 mutator 后重跑 5 轮 | 隔离后全通过 | 已排除；属于控制面竞争 |

## 根因

- HOT reset 根因边界：当前 SSC305/sensor mode 不具备已验证的物理 sensor FPS HOT capability；具体 driver/CMDQ 异步失稳机制仍未细分。
- teardown 永久阻塞：SCL private ring pool 在 H26x output role 与 VENC consumer 仍存在时被释放，是本次 failure mechanism；最终候选 exact-demand、单次和 5 轮回归已在当前覆盖范围验证修复。
- ADB transport 中断：未确认，不归因于媒体 pipeline；新端点恢复只证明 handoff 已重新建立，不反向推断历史失联原因。
- HIL 第 5 轮控制错误：产品 auto-standby 与人工 FPS 命令竞争；安全隔离后未复现，不归因于资源泄漏。

## 修复或规避

- 生产 capability 固化为 `sensorFpsHotSwitch=0`、`vifSourceGateRebind=0`、`streamGraphPartialRebuild=1`。
- 真实物理 30↔1 fps 强制 `COLD_REBUILD`；因此会发生 ISP/SNR/VIF stop/deinit/init。
- 如果只要求输出 1 fps、不要求 sensor 省电，可在上层使用 FRC/丢帧，避免物理 FPS 切换。
- MAIN/SUB/BOTH 使用 exact demand，只创建所需 VENC；AOV 1 fps 图不创建 LDC。
- 修复 H26x teardown pool 顺序和失败重试 journal；控制面 FPS route timeout 独立为 10 秒，并回收过期临时 CLI rate entry。
- 设备空间不足时，部署工具要求调用者显式提供主机备份目录；停止进程前对 installed-before、host-backup、installed-after 执行三方 MD5 校验，避免为了腾空间丢失可回滚锚点。

## 验证

已通过：

- host source contracts、planner、public-header 镜像检查；
- HDI/app 库、PCR02 app、cmd server 构建；
- frozen/staged/installed artifact identity gate；
- 最终 pool-journal + diag 候选 MAIN/SUB/BOTH/stop exact demand；
- 最终候选 BOTH 单次和连续 5 次物理 COLD；
- 每次首 I/持续帧、output-role/pool journal、增量 dmesg/core 检查；
- 最终健康 preflight 与 `already-installed` artifact gate。
- 新端点 handoff recovery：30 fps、LDC=1、H26x mask/journal=0、motor estop、`/customer` 只读、应用/命令服务健康。

未通过或未执行：

- 独立 decoder 无花屏验证、1000 次循环、8 小时 soak；
- RSS/MMA/thread/fd 和 LIGHT_ONLY 功耗曲线；
- release/image/OTA 重生与升级/降级。

## 后续动作

1. 增加跨实例 ISP disable/stop/destroy/deinit/init/IQ/LDC 结构化聚合，扩充 P50/P95/P99/max 样本。
2. HIL 前隔离或记录 auto-standby、watchdog 和其他 FPS mutator，执行 1000 次 COLD 并记录资源曲线。
3. 使用独立 ES decoder/event trace 签收 STOP/START/CONFIG/IDR 与无花屏。
4. 完成 8 小时 soak、LIGHT_ONLY 功耗和 AE 稳定性。
5. 重生 release/image/OTA 并执行升级/降级后，再评估 validation 或 owner decision。

## 边界

- 本条目是 `reviewing` debug-record candidate，不是 active 事实、通用平台标准或发布声明。
- 不授权 HOT capability 重开、设备部署、owner decision、active promotion、memory write 或 release。
- 当前 `fix-verified` 只覆盖 exact-demand、单次和 5 轮 COLD；若 1000 次、decoder 或 fault injection 出现反例，应以新证据更新或 supersede，不静默扩大结论。
