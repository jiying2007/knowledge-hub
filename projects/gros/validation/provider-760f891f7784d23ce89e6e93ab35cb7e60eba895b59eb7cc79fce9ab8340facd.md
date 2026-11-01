---
id: provider-760f891f7784d23ce89e6e93ab35cb7e60eba895b59eb7cc79fce9ab8340facd
title: WiFi三仓设计复杂度复审：必要保护、局部重复与慢保存超时耦合
kind: validation
domain: projects/gros
path: projects/gros/validation/provider-760f891f7784d23ce89e6e93ab35cb7e60eba895b59eb7cc79fce9ab8340facd.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:760f891f7784d23ce89e6e93ab35cb7e60eba895b59eb7cc79fce9ab8340facd
  source_sha256: e7bd6afc36d993cdf7f28f724ff4ae900c36cfab73f75d32b03cdba71c9507fb
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
- projects/gros/validation/provider-760f891f7784d23ce89e6e93ab35cb7e60eba895b59eb7cc79fce9ab8340facd.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gros/validation/provider-760f891f7784d23ce89e6e93ab35cb7e60eba895b59eb7cc79fce9ab8340facd.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-19'
updated_at: '2026-10-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-19'
manual_validation_pending: true
summary_zh: 2026-10-19。用户要求“审查三个仓库修复，是否过渡设计”，本轮按过度设计审查。只读working-tree全WiFi diff及相邻调用链，排除音频。主审及fresh independent whole-diff/lifecycle复审。未修改源码、暂存、提交、推送或操作设备。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: gros
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 760f891f7784d23ce89e6e93ab35cb7e60eba895b59eb7cc79fce9ab8340facd
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
aliases:
- WiFi三仓设计复杂度复审：必要保护、局部重复与慢保存超时耦合
related:
- projects/gros/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# WiFi三仓修复的设计复杂度复审

2026-10-19。用户要求“审查三个仓库修复，是否过渡设计”，本轮按过度设计审查。只读working-tree全WiFi diff及相邻调用链，排除音频。主审及fresh independent whole-diff/lifecycle复审。未修改源码、暂存、提交、推送或操作设备。

## 快照与结论

已逐仓重新计算HEAD、任务diff和新增文件hash，与/tmp/wifi-review-fixes-manifest.json完全一致。Sensor HEAD 6fb68755c68be8ca0410952d9ebd7b94a16fdb92；API HEAD 53b557b0ae39368653041d299abb18732e5132ee；WiFi HEAD 5c3f8bc06a6c73ed8cbbc78319600fefe3cfc8d3。manifest SHA256 eb14c71a196b02cc69be2b63e56aea2cc7385add002f99784629d08015af230e。

整体没有明显过度设计：没有新增线程、通用框架或重复业务状态机；backend唯一负责配置路径和文件事务，API负责准入/串行/生命周期，Sensor负责编排/代次/有限重试。原三项major修复有效，但本轮发现额外一项连接确认与持久化的时间耦合，需修正上轮整体PASS结论。当前blocker=0、major=1；Spec/Quality=NEEDS_FIX。设计简化方向是减小职责耦合和正常路径重复，不能撤掉已修复历史故障的保护。

## Major：已验证连接仍可能因慢保存被判失败

Sensor wifi/sensor_wifi_service.cpp:3994在SSID/IP已验证后同步saveConnectedCredential，3995再expireSubmittedConnect，4022之后才返回联网成功ACK。新的Confirm包含两次STATUS、LIST、每网络两次SET、SAVE、fsync。保存跨连接deadline时，expireSubmittedConnect(:3379)把linked清false、状态设ERROR并完成失败ACK。即使保存本身成功，也会发生。持久化结果与链路分离的语义尚未落实到调用顺序。

主审已用真实SensorWifiService+现有平台mocks进行Host ASAN/UBSAN故障注入：有效audit-ap SSID/IP、提交态连接、未来deadline，Confirm成功回调中将deadline推进至过期，handleConnectedState返回false，linked=false，state=ERROR。进程退出0，输出REPRODUCED。该实验确定性模拟跨deadline，不是实测设备保存耗时，也没有证明现场已发生。程序/tmp/wifi-save-deadline-review.cpp SHA256 443e99fe96b617bf414bad820d0b50092cc8f87c1c497569d5c3c3cf240fbd05；二进制SHA256 e2816d60f7e96ab83c4dab6d3551f9425c68ebb7c0105b93533f09324ed1015c。

最小修复方向：先提交已验证且generation仍匹配的连接成功/ACK；保留待保存generation，由现有worker保存入口执行首次保存及重试，不新增线程。保留停止/低功耗门禁；保存不能反向改变已确认链路。属于调用顺序/终态边界调整，落地前应更新契约及成功临界deadline回归。

## Minor：可以简化的局部设计

1. WiFi linux_sta.c:2776连接成功已恢复策略并SAVE，Sensor首次Confirm(:2441)又通过linux_sta.c:932完整恢复+SAVE+同步。正常成功路径约4N次SET和两次SAVE，属重复工作。先统一WiFi内部restore/save/sync实现以防两份逻辑漂移；消除第二次写盘需提供可核验的后端持久化结果，不能直接删除Confirm或backend保存，以免失去失败重试或改变其他调用方语义。
2. Sensor :4014先保存pending marker，finishConnectAttemptLocked(:3353)清除，再恢复，职责绕行。连接完成清理与持久化取消可明确分开；取消、新请求、退出才取消对应持久化任务。保留generation，不引入新状态机。
3. Sensor/API lib.mk将整个modules/api/include置于父工程镜像前，范围大于WiFi新接口需求，会影响所有同名api头的来源。本轮未核出ABI错误，不升major。建议后续统一canonical公共头来源或收窄构建依赖，配套库仍须一起构建；不建议在代码中散布跨仓相对include。
4. Sensor save_attempts>=3、5000U退避、30000U缓存TTL可改成局部命名常量。不需要配置文件、策略对象或通用retry框架。

## 必要机制与保留理由

- 原子暂存/发布及真实软链目标处理：初始化中断已被前轮复现，不能退回原地写空文件。
- 暂存内容识别与锁/owner校验：固定暂存名需要防未知内容被接管；对其直接截断不构成安全简化。
- generation与cache revision不同：generation隔离新连接请求，revision阻止同连接代次内更新被迟到查询覆盖；TTL控制缓存年龄。三者不能简单合并。
- 待保存标记、次数和下次时间：连接结束后仍需驱动有限重试；不能以链接成功清除失败保存。
- API saved-network锁、background active与暂停/关闭检查各司其职；沿用既有生命周期设施，没有必要删除。
- 每10秒后台完整复核与UI缓存30秒TTL可在设备耗时证据后合并刷新节律，当前没有测量依据认定性能故障；避免再增加一层缓存。

## 验证与边界

本轮三仓git diff --check退出0，快照匹配核验退出0，新增deadline故障注入构建及执行退出0。前轮三仓Host suites、WiFi生命周期回归、五个ARM对象属于此前证据，本轮没有冒称重新全量执行。独立reviewer未执行构建，其源码审查与主审实测分开记录。无完整链接、设备身份、真实supplicant时延或HIL。

本轮只交付审查；major未修复，不能声明当前实现整体通过。建议优先修正连接成功关键路径，再做局部去重和命名整理，保持范围可回滚。仅project-specific reviewing candidate，未获得owner产品放行。
