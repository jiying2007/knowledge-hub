---
id: provider-29e7b371698a5ad8e5638fca6f1febba37e55dde4e94e3ae83aef43e4f1c85c8
title: WiFi三仓known-persist命名整改与定向验证
kind: validation
domain: projects/gros
path: projects/gros/validation/provider-29e7b371698a5ad8e5638fca6f1febba37e55dde4e94e3ae83aef43e4f1c85c8.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:29e7b371698a5ad8e5638fca6f1febba37e55dde4e94e3ae83aef43e4f1c85c8
  source_sha256: 510eb7cc6afb2913ba3380098b7b4b7391d70b9967b175af2fdc4dec93f98f7d
  temporary_source_retained: false
review_after: '2027-01-17'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/gros/validation/provider-29e7b371698a5ad8e5638fca6f1febba37e55dde4e94e3ae83aef43e4f1c85c8.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gros/validation/provider-29e7b371698a5ad8e5638fca6f1febba37e55dde4e94e3ae83aef43e4f1c85c8.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-19'
updated_at: '2026-10-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-19'
manual_validation_pending: true
summary_zh: 日期：2026-10-19。用户授权 Sensor/API/WiFi 三仓修复优化，proto 不变；不修改父仓，不提交推送。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: gros
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 29e7b371698a5ad8e5638fca6f1febba37e55dde4e94e3ae83aef43e4f1c85c8
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
aliases:
- WiFi三仓known-persist命名整改与定向验证
related:
- projects/gros/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# WiFi 三仓 known/persist 命名整改与验证

日期：2026-10-19。用户授权 Sensor/API/WiFi 三仓修复优化，proto 不变；不修改父仓，不提交推送。

## 实现

- 删除无生产调用、只复制重连上下文的 VSAPIWIFI_SaveNetwork，不添加兼容包装。Connect 继续维护内存重连目标。
- 主动持久化统一为 VSAPIWIFI_PersistStationConfig、wifi_sta_persist_config、linux_sta_persist_config。expected SSID 保护目标身份，操作恢复网络策略、SAVE_CONFIG 并同步整个 station 配置。日志改为 connection_result_updated=false，避免声称实际链路已经复核在线。
- 运行时查询统一为 VSAPIWIFI_GetKnownNetworks；Sensor 缓存、查询、刷新、remove/clear 标志和相关参数统一 known。后端与本地来源均不证明磁盘持久化。proto 查询命令、消息结构及 saved_networks 字段保持原样。
- Sensor 使用 processPendingPersistence/persistNetworkConfig，pending_persist_generation_、persist_retry_generation_、persist_attempts_、next_persist_attempt_ms_ 明确任务含义，保留原有成功结果、代次、退避、停止及低功耗保护。
- API 持久化函数补全分支花括号、枚举变量前缀、常量在左比较和扩展头 guard。WiFi 写配置声明移出只读查询注释组。采用锁定 LLVM18.1.8 修复触达排版，保留 vendor 风格。

## 验证

- Sensor/API doctor 和 check 通过；三个仓库 diff --check 通过。
- 三仓 persistence 定向套件通过：配置初始化/中断暂存恢复/软链保护/失败重试，策略恢复后写入/目标复核/同步失败，API 准入/串行化/返回传播，Sensor 成功先于持久化/截止时间隔离/有限重试/取消/迟到结果/缓存刷新。Host ASAN/UBSAN 无执行失败。
- 集成 tests/wifi_recovery_lifecycle 通过：恢复/回调寿命/退出传播/IPv4 snapshot/并发解析/脱敏日志与 release contract。
- 按根 Makefile dry-run 的实际参数定向构建 api_wifi.c、sensor_wifi_service.cpp、linux_common.c、linux_sta.c、wifimg.c 五个 ARM 对象，通过。API/Sensor/wifimg 无 warning；linux_common 6 条、linux_sta 11 条既有 vendor warning，未宣称无警告构建。
- 锁定 clang-format 对新增文件和变更新行的待修 replacement 为零。全文仍有旧格式差异，未宣称全文格式通过。
- 开工/收口哈希比对覆盖 proto、父公共头、Sensor 音频及 API 已有音频修改共 296 个文件，未变化。
- 跨三仓生产源码及测试扫描无旧 SaveNetwork/GetSavedNetworks/ConfirmNetworkSaved 调用。WPA SAVE_CONFIG 和真实磁盘 restore/save 命名保留。

## 独立审查

工作树 whole-diff 和适用 lifecycle 复审未发现新的 blocker/major。Spec PASS，Quality PASS WITH MINOR。WiFi 扩展头作用范围注释发现已修复并复核。剩余 minor 为真实 worker 并发集成覆盖不足；helper 测试不能替代运行中通知、在途写入及低功耗排空验证。

## 边界

现有预编译 libsensor.a/.so 仍引用旧 VSAPIWIFI_SaveNetwork/GetSavedNetworks，已证实与新源码不匹配。最终集成须同批重建三仓库并完整应用链接；本轮不修改生成库。父公共镜像头、旧 sensor 测试和部分静态契约测试仍是旧名称，按范围保持不动，不能声称这些原测试未经适配即可通过。生产源码扫描未发现外部旧调用。

本轮无完整产品链接、设备运行、掉电/重启持久化或 OTA 验证，不能推导产品问题已闭环。未暂存、提交或推送；原有音频修改排除。

源码 HEAD：Sensor 6fb68755c68be8ca0410952d9ebd7b94a16fdb92；API 53b557b0ae39368653041d299abb18732e5132ee；WiFi 5c3f8bc06a6c73ed8cbbc78319600fefe3cfc8d3。均为 dev/wifi_fix 加当前工作树 overlay。

任务文件 SHA256 manifest 单独保存供本次复核，产物仅临时对象，不作为发布制品。归档为 reviewing candidate，不代表 owner 批准或产品放行。
