---
id: provider-f0897a775cb57d42cd7bd56ddbf58b099361b866d0ed7dcfc075d104c4b8bffb
title: WiFi扫描适配提交前检查
kind: validation
domain: projects/gros
path: projects/gros/validation/provider-f0897a775cb57d42cd7bd56ddbf58b099361b866d0ed7dcfc075d104c4b8bffb.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:f0897a775cb57d42cd7bd56ddbf58b099361b866d0ed7dcfc075d104c4b8bffb
  source_sha256: 2641cd05f903fe4614a9c3bfca0cfa2af66ded3848a087698bd563d79ab0135e
  temporary_source_retained: false
review_after: '2027-01-18'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/gros/validation/provider-f0897a775cb57d42cd7bd56ddbf58b099361b866d0ed7dcfc075d104c4b8bffb.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gros/validation/provider-f0897a775cb57d42cd7bd56ddbf58b099361b866d0ed7dcfc075d104c4b8bffb.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-20'
updated_at: '2026-10-20'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-20'
manual_validation_pending: true
summary_zh: 检查日期：2026-10-20。仅检查，未改变源码、暂存区、提交或远端。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: gros
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: f0897a775cb57d42cd7bd56ddbf58b099361b866d0ed7dcfc075d104c4b8bffb
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
aliases:
- WiFi扫描适配提交前检查
related:
- projects/gros/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# WiFi 扫描适配提交前检查

检查日期：2026-10-20。仅检查，未改变源码、暂存区、提交或远端。

结论：needs-fix（提交范围与测试纳管待整理）。定向源码复核未发现新的阻断缺陷，但当前没有 staged 候选，不能给最终提交快照放行。

## 发现

1. Major：app_product_test/pt_wifi_scan_session.h 未跟踪。pt_common.c 与 pt_hw_wifi.c 已包含此头；若仅提交已跟踪文件（例如 commit -a），其他检出环境缺头会编译失败。必须与两处使用者同批提交。
2. Major：四组本轮验证入口在外层父仓均未跟踪：tests/app_product_test_wifi_scan、tests/sensor_wifi_service、tests/wifi_recovery_lifecycle、tests/contracts/test_wifi_security_contracts.py。仅提交产测仓不会保留测试。需确定测试归属并纳管；若留父仓，应单独提交测试及其配套 public header 同步，明确 API/Sensor/WiFi 依赖基线。
3. Major：产测已有日志降噪与 WiFi 修复混合。pt_common.c 的 router heartbeat 两个 hunk、TECHNICAL_DESIGN 的日志策略 hunk，以及 README、battery/IR/motor/speaker 等其他修改均不属于本次扫描修复。WiFi 提交需按 hunk 选择，不能整体 commit -a。父仓另有音频、构建配置、库变更和库删除，不能整体提交。

这些是提交打包问题，未断言它们已进入暂存区：当前五个仓的暂存区均为空。

## 仓库状态与范围

- app_product_test HEAD d1aa346：本轮应含 pt_wifi_scan_session.h、pt_hw_wifi.c、pt_common.c 的扫描相关 hunk，以及 DEVELOPMENT_PLAN、PRODUCT_TEST_INI_PRODUCTION_GUIDE 和 TECHNICAL_DESIGN 的扫描说明 hunk。
- API HEAD 5b40c67、Sensor HEAD 840ac01、WiFi HEAD 0a40817：相应 WiFi 修复已在当前提交中，无需重复提交。API/Sensor 尚有无关音频 dirty；WiFi clean。
- 外层父仓 HEAD 90cfa77：include/api/api_wifi.h 与当前 API 子仓 public header 字节一致，但相对父仓 HEAD 包含更早的接口增删，不能描述为本轮仅注释变化；应作为跨仓同步单独审查与提交。测试依赖当前独立仓和 SDK 头文件布局。

## 复核和验证证据

- 手工复核显式启动、当前会话回调证明、失败/取消后旧缓存拒绝、35 秒轮询阈值、取消失败保留 owner 和老化锁存；未发现新的源码阻断项。该结论来自同一代理复核，未替代独立 owner review。
- make -C tests/app_product_test_wifi_scan test OUT=/tmp/pcr02-product-wifi-precommit-test：新路径重新编译并运行，退出 0；ASAN/UBSAN + Werror。
- make -C tests/sensor_wifi_service test：退出 0；生命周期、安全模式等用例通过。
- make -C tests/wifi_recovery_lifecycle test：退出 0；7 个 ASAN/UBSAN 程序及 release contract 通过。
- python3 tests/contracts/test_wifi_security_contracts.py：退出 0，22 项通过。
- 根 Makefile dry-run 提取实际 ARM 编译命令，pt_common.c、pt_hw_wifi.c 输出至 /tmp/wifi-precommit-*.arm.o：退出 0。
- 四个独立仓 working diff --check 通过，public header 相同；产测 skill quick_validate 通过。
- 其他 API/Sensor/daemon 对象构建与旧 DVR 契约负结果见前次 wifi-scan-consumer-validation-20261020.md；本轮未重跑全仓 DVR 套件，未把旧结果当作新鲜全仓通过证据。

## 门禁边界

本轮无配置、schema、运行控制面、CI 或发布脚本修改。产测私有 helper 不新增公开 ABI；依赖 GetScanResults 只读结果及当前 API 的取消回调清理契约。回退应按匹配的 API/WiFi/产测组合执行，不能仅回退某个行为依赖。
未执行最终链接、设备部署、HIL 或发布。提交前仍需形成精确暂存快照并复核 staged diff；受保护分支合入须由仓库 human owner 复审。
本次检查完成不等同于提交候选通过，不等同于产品 release-ready。
