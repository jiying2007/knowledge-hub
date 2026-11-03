---
id: provider-654b50cc73ac96d9a3ede2c01dfbef1dc7bfd2ea109db61942a297d674c919b2
title: 全库知识 AI 语义复核：第 101—125 条
kind: audit
domain: governance
path: governance/product/archive/provider-654b50cc73ac96d9a3ede2c01dfbef1dc7bfd2ea109db61942a297d674c919b2.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:654b50cc73ac96d9a3ede2c01dfbef1dc7bfd2ea109db61942a297d674c919b2
  source_sha256: cbafe9ac05bc6eee56d91c141fd3e9a03777710b9edf932459706a9b72bc17fb
  temporary_source_retained: false
review_after: '2027-01-29'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- audit
validation_refs:
- governance/product/archive/provider-654b50cc73ac96d9a3ede2c01dfbef1dc7bfd2ea109db61942a297d674c919b2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- governance/product/archive/provider-654b50cc73ac96d9a3ede2c01dfbef1dc7bfd2ea109db61942a297d674c919b2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-31'
updated_at: '2026-10-31'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-31'
manual_validation_pending: true
summary_zh: 复核日期：2026-10-31。执行者：Codex 独立 AI reviewer。 授权来源：本线程用户明确授权自动复核，并授权当前目标重规划及追加预算。 本批属于 reviewing 复核证据候选；不构成真人签收、active
  提升、owner 决定或产品放行。 完整正文按条目 SHA256 绑定；历史验证命令和工程结论未因此重跑。原正文、owner、状态、review_after 均保留。 条目路径仅是本轮审读定位，不作为跨仓写入契约。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: knowledge-hub
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 654b50cc73ac96d9a3ede2c01dfbef1dc7bfd2ea109db61942a297d674c919b2
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# 全库知识 AI 语义复核：第 101—125 条

复核日期：2026-10-31。执行者：Codex 独立 AI reviewer。
授权来源：本线程用户明确授权自动复核，并授权当前目标重规划及追加预算。
本批属于 reviewing 复核证据候选；不构成真人签收、active 提升、owner 决定或产品放行。
完整正文按条目 SHA256 绑定；历史验证命令和工程结论未因此重跑。原正文、owner、状态、review_after 均保留。
条目路径仅是本轮审读定位，不作为跨仓写入契约。

## 101. gd32l235-pa11-charge-soc-power-gate-design-20260722

- 正文定位：`projects/gd32l235/archive/design/2026-07-22-pa11-charge-soc-power-gate-design.md`
- 完整正文 SHA256：`cdf7d9a344aa68515cb4bec66f8f6970f6d3294efa09bf2932d75efd6f743e79`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-08-22`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`needs-edits`。
- 适用范围与内容判断：PA11关机禁充、硬件DNP和SoC上电门控设计演进。
- 证据及验证边界：DNP/BOM与charger默认态仍待artifact/板测确认，不能自动成为量产硬件事实。
- 发现：第4.1节允许浅睡一次9ms唤醒和0x09，但第4.2/5.3/6.2节与后续验收又绝对禁止PA11 OFF的PA8或shutdown。；第4.1要求PA15必须OFF同时要求等0x09确认，与第5.2允许退出期间临时ON之间的顺序未收敛。；166给出PA11 ON时PA15不能保证独立切电的硬件OR路径修正，本文“可独立切断”仍未关联该后续反证。
- 处理结果或后续动作：统一为先best-effort退出再最终断SoC及禁充，明确浅睡9ms例外；将绝对禁止的旧草案隔离为历史。
- 下一复核建议：完成所列修订或补证后复核；本轮不构成人类签收、设备验证或状态晋升。

## 102. gd32l235-soc-shutdown-confirmation-closure-design-20260722

- 正文定位：`projects/gd32l235/archive/design/2026-07-22-soc-shutdown-confirmation-closure-design.md`
- 完整正文 SHA256：`1019b284ecc60b754cec73c91bef3ddce4a6f17c5be2340165e5f808fa197d67`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-08-22`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`needs-edits`。
- 适用范围与内容判断：SoC退出尾部确认、串口保留、单飞取消和PA15动作协同方案。
- 证据及验证边界：本条是计划演进且已有首部固定3B声明；未复跑任一源码命令或HIL。
- 发现：第3/5/10/11/12节仍以1B/2B兼容parser、payload_len和旧协议测试作当前建议，与首部固定3B相反。；首部补充及6.4称OFF+charging不发shutdown，与首部终态更新和第11用例要求best-effort 0x09冲突。
- 处理结果或后续动作：移除当前建议中的旧payload兼容代码，将取消边界、SoC确认和浅睡一次唤醒收敛到首部最终合同，保留历史由来。
- 下一复核建议：完成所列修订或补证后复核；本轮不构成人类签收、设备验证或状态晋升。

## 103. gd32l235-soc-heartbeat-terminal-state-plan-20260616

- 正文定位：`projects/gd32l235/archive/design/2026-06-16-soc-heartbeat-terminal-state-plan.md`
- 完整正文 SHA256：`11713c0dea71a6ed69e41f7032e1d03f7b6501c8c66d4f5cfa5e2912e0d3e9bf`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-08-22`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`accept-historical-record`。
- 适用范围与内容判断：4B heartbeat角色/状态/位图/原因与版本查询分离计划。
- 证据及验证边界：6月计划和建议周期不能作为当前部署成功证据；本轮不核验源项目。
- 发现：本次审读未发现确定的正文矛盾；不据此推导外部事实已验证。
- 处理结果或后续动作：保留不兼容4B、boot guard与offline规则的历史设计；任何临时旧格式分支不得进入主线。
- 下一复核建议：按历史记录保留；引用为当前事实前重验相应源码、制品或外部证据。

## 104. gd32l235-soc-heartbeat-reboot-ota-closure-session-20260617

- 正文定位：`projects/gd32l235/archive/session/2026-06-17-soc-heartbeat-reboot-ota-closure-session.md`
- 完整正文 SHA256：`36545006c23a2c578ee9f012cd89d573a2099211e445fc995a060a056f91f620`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-08-22`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`accept-historical-record`。
- 适用范围与内容判断：4B心跳、reboot失败恢复、OTA handoff及PA8抑制的会话摘要。
- 证据及验证边界：软件构建不证明PA8波形或真实reboot；脚本0返回成功限于用户当次外部接管契约。
- 发现：本次审读未发现确定的正文矛盾；不据此推导外部事实已验证。
- 处理结果或后续动作：保留具体责任边界及脏仓状态为历史，不将memory候选表自动写memory或泛化成OTA通用成功策略。
- 下一复核建议：按历史记录保留；引用为当前事实前重验相应源码、制品或外部证据。

## 105. gd32l235-soc-exit-poweroff-management-session-20260604

- 正文定位：`projects/gd32l235/archive/session/2026-06-04-soc-exit-poweroff-management-session.md`
- 完整正文 SHA256：`0a5dc9154b3aa97a249da6de67ef04a010b023da064d9bec63cf41f9009376a9`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-08-22`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`accept-historical-record`。
- 适用范围与内容判断：6月SoC退出单飞、低电保护与PA11/PA15管理的历史会话。
- 证据及验证边界：明确未编译、未HIL；旧PA15/1B兼容已在首部声明失效。
- 发现：本次审读未发现确定的正文矛盾；不据此推导外部事实已验证。
- 处理结果或后续动作：保留当时决策和负边界，旧格式段落仅历史provenance；当前确认不可撤销逻辑以新契约为准。
- 下一复核建议：按历史记录保留；引用为当前事实前重验相应源码、制品或外部证据。

## 106. gd32l235-soc-low-power-contract

- 正文定位：`projects/gd32l235/current/soc-low-power-contract.md`
- 完整正文 SHA256：`8ca2a15fd9d3575baff46417116de9effbcc389aca7cb19e32d0db4ec158dc91`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-08-22`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`needs-edits`。
- 适用范围与内容判断：MCU/SoC四状态、完整快照revision及固定3B关机当前契约候选。
- 证据及验证边界：as_of为7月；最小构建通过，四态HIL和提交身份仍缺失，且保持reviewing。
- 发现：当前契约候选仍把DEEP_SLEEP定义为PA15切电、仅WiFi冷启动；150已改为PA15保持与PA8长脉冲，149增加CHARGE，167又将充电恢复收窄为仅DEEP_SLEEP的有效正电流确认，当前索引未同步这些演进。
- 处理结果或后续动作：补后续150/167候选关联并按最终已记录的策略更新四状态表；仍保持HIL pending，不把历史设计更新当硬件事实批准。
- 下一复核建议：完成候选契约的版本化修订后复核；保留源码与组合制品HIL独立门禁。

## 107. llm-agent-external-practice-absorption-candidates-20260723

- 正文定位：`projects/llm-agent/archive/research/2026-07-23-external-practice-absorption-candidates.md`
- 完整正文 SHA256：`4be42852dd1861902c8a4c656f89307ad00d2d77b6aa599e63d7d7e1edaa12a7`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-10-23`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`accept-historical-record`。
- 适用范围与内容判断：11类外部吸收候选，侧重真实仓库campaign、过程质量、安全和MCP观察。
- 证据及验证边界：118候选及引用官方资料仅原7月研究快照；外部版本、许可证与真实性未在本轮联网复核。
- 发现：本次审读未发现确定的正文矛盾；不据此推导外部事实已验证。
- 处理结果或后续动作：保留review-required和Gitee降级负证据；MCP未来版本只observe，实际采纳前重新取证。
- 下一复核建议：按历史记录保留；引用为当前事实前重验相应源码、制品或外部证据。

## 108. gd32l235-pcr02-sensor-rate-contract-50hz-fusion-20260723

- 正文定位：`projects/gd32l235/archive/design/2026-07-23-sensor-rate-contract-and-50hz-fusion.md`
- 完整正文 SHA256：`57362287045e3499393df8cc961e73cabcb219df9a6261bfe5e5db56c145d6da`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-08-23`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`needs-edits`。
- 适用范围与内容判断：跨MCU/SoC物理频率、50Hz电机聚合和导航公共时间轴的方案。
- 证据及验证边界：50Hz为当次需求确认；未编译或板测，原始采样与保持值区分正确。
- 发现：SoC来源和modules/sensor关键实现仍使用workspace://pcr02-ssc305，应归属GROS应用，避免SDK与应用知识混杂。
- 处理结果或后续动作：改正SoC应用逻辑来源；保留UART带宽估算为方案而非实测，不依据本条直接提升固定50Hz契约。
- 下一复核建议：完成所列修订或补证后复核；本轮不构成人类签收、设备验证或状态晋升。

## 109. llm-agent-external-practice-absorption-20260723

- 正文定位：`projects/llm-agent/archive/research/2026-07-23-external-practice-absorption-implementation.md`
- 完整正文 SHA256：`498e644495349301bc2603e53ae916ae035efd5b05c59be4e1699d3a02e9e89f`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-10-23`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`accept-historical-record`。
- 适用范围与内容判断：repository runtime、MCP staging、field evidence和Skill维护控制面实施。
- 证据及验证边界：56/56等属当次测试；根quick50/53及M5真实证据blocker明确未清零。
- 发现：本次审读未发现确定的正文矛盾；不据此推导外部事实已验证。
- 处理结果或后续动作：保留控制面落地与真实M5阻塞并列结论；旧nested源码索引只作历史来源。
- 下一复核建议：按历史记录保留；引用为当前事实前重验相应源码、制品或外部证据。

## 110. llm-agent-spec-kit-reference-tracking-20260723

- 正文定位：`projects/llm-agent/decisions/2026-07-23-spec-kit-reference-tracking-decision.md`
- 完整正文 SHA256：`3d015eecfa7b5a2e0e2a255405131f9999f08664cc3e5e48c93d1ff0e32ed181`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-10-23`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`needs-edits`。
- 适用范围与内容判断：spec-kit长期跟踪批准及dirty主工作区apply负结果。
- 证据及验证边界：精确commit/tree及13项dry-run只证明阶段记录，不证明登记完成。
- 发现：同日110已经记录隔离分支applied，但本条仅称当前apply-blocked，缺successor关联，检索可能返回过期阻塞为现状。
- 处理结果或后续动作：保留首次负结果，在首部增加被同日onboarding validation更新的明确引用；不改写原失败证据。
- 下一复核建议：完成所列修订或补证后复核；本轮不构成人类签收、设备验证或状态晋升。

## 111. llm-agent-spec-kit-reference-onboarding-validation-20260723

- 正文定位：`projects/llm-agent/validation/2026-07-23-spec-kit-reference-onboarding-validation.md`
- 完整正文 SHA256：`4c3763e937d3d5f1c3eaaffb6ef3a9895e7e462d6a53369210168c977d42b61c`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-10-23`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`accept-historical-record`。
- 适用范围与内容判断：spec-kit在隔离分支登记与范围门禁通过。
- 证据及验证边界：未合并main且quick52/53；不执行上游代码，候选仅原有效期内。
- 发现：本次审读未发现确定的正文矛盾；不据此推导外部事实已验证。
- 处理结果或后续动作：保留scoped-pass与全仓needs-fix；不得把本地分支登记解释为main或当前已部署。
- 下一复核建议：按历史记录保留；引用为当前事实前重验相应源码、制品或外部证据。

## 112. pcr02-venc-main-sub-sequence-isolation-20260723

- 正文定位：`projects/gros/archive/reports/2026-07-23-pcr02-venc-main-sub-sequence-isolation.md`
- 完整正文 SHA256：`e35886dfd28340d77ea2c27a99b59fbf245efa1fad6d13051e6f8699c348caeb`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-10-23`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`accept-historical-record`。
- 适用范围与内容判断：VENC main/low各自独立sequence及channel身份语义。
- 证据及验证边界：定向编译与负搜只证明源码；IoT跨流唯一性依赖和长期设备连续性未验证。
- 发现：本次审读未发现确定的正文矛盾；不据此推导外部事实已验证。
- 处理结果或后续动作：保留原子relaxed适用范围和(channel,seq)消费契约；不把伪跳号修复当Agora带宽问题已解。
- 下一复核建议：按历史记录保留；引用为当前事实前重验相应源码、制品或外部证据。

## 113. gd32l235-pcr02-soc-sleep-network-freezer-wakeup-count-20260724

- 正文定位：`projects/gd32l235/decisions/soc-sleep-network-freezer-wakeup-count.md`
- 完整正文 SHA256：`52fef3443fac6ead29978d5cf1ec0f1989ccd5166850802b938177f2b3ace64e`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-08-24`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`needs-edits`。
- 适用范围与内容判断：SoC wakeup_count两阶段与bcmdhd SDIO wake hold修复决策候选。
- 证据及验证边界：两轮板测是失败/回滚负证据；新bcmdhd成功suspend与唤醒HIL仍缺。
- 发现：变更位置将sensor/HDI应用源码和kernel均统一写workspace://pcr02-ssc305；前者应GROS、后者SDK，且本条主要实现并无MCU改动。；结论第2项称TCPKA必须配置，而后文时序按configured arm，RTC-only条件未明确，易与97的SLEEP可RTC-only冲突。
- 处理结果或后续动作：分清GROS应用与SDK kernel URI；说明TCPKA硬要求限当次启用场景或同步可选唤醒源契约，不据构建批准驱动量产。
- 下一复核建议：完成所列修订或补证后复核；本轮不构成人类签收、设备验证或状态晋升。

## 114. pcr02-prog-pcr02-high-load-followup-20260724

- 正文定位：`projects/gros/archive/debug/2026-07-24-prog-pcr02-high-load-followup.md`
- 完整正文 SHA256：`848316b0d1b595f21b309214ff487b789d232e4007982f8ee7784eb99356f3f4`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-10-24`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`accept-historical-record`。
- 适用范围与内容判断：匹配dirty release二进制的三窗口整机高负载与IMU降频跟踪。
- 证据及验证边界：release MD5相同但debug BuildID不同；50Hz降低CPU只有相关性，非受控A/B。
- 发现：本次审读未发现确定的正文矛盾；不据此推导外部事实已验证。
- 处理结果或后续动作：保留91.79% busy和50Hz偏离目标的负结果；新产品是否接受降级须另有需求决定。
- 下一复核建议：按历史记录保留；引用为当前事实前重验相应源码、制品或外部证据。

## 115. pcr02-ssc305-sdk-trimming-optimization-plan-20260724

- 正文定位：`projects/pcr02-ssc305/archive/reports/2026-07-24-sdk-trimming-historical-plan.md`
- 完整正文 SHA256：`78ad8becaf8dc3f95efee7da3d170daef786f25fcc384b64b87442cc21f0ab42`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-10-24`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`accept-historical-record`。
- 适用范围与内容判断：SDK裁剪、启动、资源和功耗原始静态规划。
- 证据及验证边界：searchable=false及successor明确，未取得当次运行/功耗，后续115/116已补基线。
- 发现：本次审读未发现确定的正文矛盾；不据此推导外部事实已验证。
- 处理结果或后续动作：保留不可搜索历史与替代关系，不恢复旧默认检索或将建议门槛计为实现收益。
- 下一复核建议：按历史记录保留；引用为当前事实前重验相应源码、制品或外部证据。

## 116. pcr02-ssc305-runtime-resource-baseline-20260724

- 正文定位：`projects/pcr02-ssc305/validation/2026-07-24-pcr02-ssc305-runtime-resource-baseline.md`
- 完整正文 SHA256：`3b270f20db4af9fc614ce495d73b6666bc11ed198bf6aee167ccc43c580514b8`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-08-24`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`accept-historical-record`。
- 适用范围与内容判断：SDK目标板启动、CPU、共享库、MMA和模块只读基线。
- 证据及验证边界：单次约10分钟且5秒tick窗口；MD5仅关联制品，非发布签名，未证明最大负载。
- 发现：本次审读未发现确定的正文矛盾；不据此推导外部事实已验证。
- 处理结果或后续动作：保留MMA96MiB不能骤减和单OPP限制；不用累计线程ticks当瞬时热点或load当纯CPU队列。
- 下一复核建议：按历史记录保留；引用为当前事实前重验相应源码、制品或外部证据。

## 117. pcr02-ssc305-sdk-system-optimization-plan-20260724

- 正文定位：`projects/pcr02-ssc305/archive/reports/2026-07-24-sdk-system-optimization-plan.md`
- 完整正文 SHA256：`4f379644f0f7b08ff823f8fd4fdb7d9e22d855513ed31ac6bad97226ab896ec8`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-10-24`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`accept-historical-record`。
- 适用范围与内容判断：SDK系统优化S0至S7计划和A32 release/打包/启动治理。
- 证据及验证边界：规划依赖匹配运行基线，所有CPU/功耗和首帧数字仍是目标；HIL未执行。
- 发现：本次审读未发现确定的正文矛盾；不据此推导外部事实已验证。
- 处理结果或后续动作：保留SDK主责及嵌套GROS应用协作边界；不据计划批删模块、启用IDAC或缩MMA。
- 下一复核建议：按历史记录保留；引用为当前事实前重验相应源码、制品或外部证据。

## 118. pcr02-remote-adb-hil-deployment-recovery-runbook-20260726

- 正文定位：`projects/gros/current/runbooks/pcr02-remote-adb-hil-deployment-recovery.md`
- 完整正文 SHA256：`5751d009eb0eac25635acee258e312ae77c6fef81fc34f1b1d5a604f5f767f82`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-10-26`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`retain-current-with-caveats`。
- 适用范围与内容判断：远程ADB分层preflight、制品门禁、授权部署、分级HIL和健康恢复。
- 证据及验证边界：候选runbook不授设备写权限；团队工具真实存在与当前CLI未在本轮执行验证。
- 发现：本次审读未发现确定的正文矛盾；不据此推导外部事实已验证。
- 处理结果或后续动作：保留只读默认、失联熔断与备份锚点；跨仓使用先由Provider解析团队工具，不能根据旧物理路径盲执行。
- 下一复核建议：完成所列修订或补证后复核；本轮不构成人类签收、设备验证或状态晋升。

## 119. pcr02-motor-uart-timestamp-sync-plan-20260726

- 正文定位：`projects/gros/archive/reports/2026-07-26-pcr02-motor-uart-timestamp-sync-plan.md`
- 完整正文 SHA256：`619f91bfea362f4685cfcc6c10318f0d51d2c77896ff7f62b7b3c6b467c0cb03`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-10-26`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`needs-edits`。
- 适用范围与内容判断：电机UART时钟同步、60B 0x16和实时链路的冻结设计草案。
- 证据及验证边界：明确未实现；121随后记录owner收敛40B单采集时间戳及事件驱动速度状态。
- 发现：本条以“最终方案”给出60B、Proto18..23及超龄旧非零速度丢弃，与121明确40B、仅timing_flags18且最新速度不按年龄stop不同，缺替代关系。
- 处理结果或后续动作：增加121的显式successor并将本条限定前期设计；防止按旧60B协议或旧速度语义实现。
- 下一复核建议：完成所列修订或补证后复核；本轮不构成人类签收、设备验证或状态晋升。

## 120. gros-hdi-vi-30-1fps-scl-pool-teardown-20260727

- 正文定位：`projects/gros/archive/debug/2026-07-27-hdi-vi-30-1fps-scl-pool-teardown.md`
- 完整正文 SHA256：`e443df928ca329d27102d6bbfb2ce03c3807184bf8defa99e8e72331e9f09f0c`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-08-31`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`accept-historical-record`。
- 适用范围与内容判断：物理FPS早期HOT反例、SCL pool teardown顺序修复和5轮COLD。
- 证据及验证边界：历史HOT失败限当时路由，后续受控HOT不同；未完成decoder/1000次/8h。
- 发现：本次审读未发现确定的正文矛盾；不据此推导外部事实已验证。
- 处理结果或后续动作：保留BuildID及bundle摘要和高置信failure mechanism；不得据5轮扩大为长稳或据早期失败否定所有后续HOT实验。
- 下一复核建议：按历史记录保留；引用为当前事实前重验相应源码、制品或外部证据。

## 121. gd32l235-pcr02-disarm-sensor-restore-validation-20260727

- 正文定位：`projects/gd32l235/archive/design/2026-07-27-disarm-sensor-restore-transaction.md`
- 完整正文 SHA256：`fd1d555a54d8ac3d1b119283e3d399fefc5244d42e68ed114cc278936cd36c9d`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-08-27`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`needs-edits`。
- 适用范围与内容判断：DISARM ACK屏障和Sensor worker假恢复的跨端修复。
- 证据及验证边界：MCU构建及SoC对象通过但DHD综合门禁失败、格式/HIL待补。
- 发现：source.from仍把SoC应用工作树标为workspace://pcr02-ssc305，与实际app/sensor应用归属GROS混杂。
- 处理结果或后续动作：将SoC应用来源改为GROS；保留DHD负证据和双端同批回退约束，不声明整体suspend通过。
- 下一复核建议：完成所列修订或补证后复核；本轮不构成人类签收、设备验证或状态晋升。

## 122. pcr02-motor-uart-timestamp-sync-implementation-validation-20260727

- 正文定位：`projects/gros/validation/2026-07-27-pcr02-motor-uart-timestamp-sync-implementation.md`
- 完整正文 SHA256：`517f095c237dff5cc9c4da4ac3b4ba327b963b2354a239df5a5b1ea404e59852`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-10-27`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`accept-historical-record`。
- 适用范围与内容判断：0x1A、40B电机反馈、源时间门禁、持久速度状态及OTA排他实施。
- 证据及验证边界：离线契约和全量构建不证明TEMT ioctl、P99同步或混合版本门禁；Flash裕量仅44B。
- 发现：本次审读未发现确定的正文矛盾；不据此推导外部事实已验证。
- 处理结果或后续动作：保留40B对60B草案更正与未HIL边界；保留缺diag脚本为负证据，不以编译代替其通过。
- 下一复核建议：按历史记录保留；引用为当前事实前重验相应源码、制品或外部证据。

## 123. pcr02-active-low-1-pipeline-architecture-20260727

- 正文定位：`projects/pcr02-ssc305/archive/design/2026-07-27-active-low-1-pipeline-architecture.md`
- 完整正文 SHA256：`38a12ccc03e2753bee62c372c0538ddfa7d71acf6a4d9a34f3bbfdf0fb1b6bd1`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-10-25`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`needs-edits`。
- 适用范围与内容判断：HDI组件graph与1/30fps日夜策略的初始方案。
- 证据及验证边界：源码设计候选，无新板测；123同日已收紧无H26x的soft-light条件。
- 发现：本文source是gros/DESIGN.md且主体为HDI/IrLight应用编排，却落在SDK pcr02-ssc305；需按仓库边界重新分类。；soft_light未含h26x_gate_effective并允许无媒体仅light维持backbone，123已更正但本条缺明确superseded标记。
- 处理结果或后续动作：路由到GROS应用知识或仅保留SDK硬件能力引用；标记被123更新，正文去重。
- 下一复核建议：完成所列修订或补证后复核；本轮不构成人类签收、设备验证或状态晋升。

## 124. pcr02-active-low-1-no-h26x-light-meter-power-gate-20260727

- 正文定位：`projects/pcr02-ssc305/decisions/active-low-1-no-h26x-light-meter-power-gate-20260727.md`
- 完整正文 SHA256：`1527075c41a5efcc834ba264c20cd9928268a890c70211398226d5ccb5bae289`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-10-25`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`needs-edits`。
- 适用范围与内容判断：无H26x时关闭soft-light/light-meter避免ISP无效保活。
- 证据及验证边界：独立产品策略候选，不是已验证板端功耗。
- 发现：第2节soft_light表达式包含h26x_gate_effective，第8节最后又说H26x gate不参与ADC/软光敏选择，内部直接矛盾。；全文大量重复122，且第5.3仍称无媒体可打开soft-light最小backbone，未限定仅HDI能力而非本策略允许。；业务IrLight/HDI编排源于GROS却放SDK项目，主责边界不清。
- 处理结果或后续动作：按唯一候选正文收敛表达式、资源能力和业务策略；明确gate参与源选择并迁正主责。
- 下一复核建议：完成所列修订或补证后复核；本轮不构成人类签收、设备验证或状态晋升。

## 125. pcr02-app-uart-time-sync-low-power-busy-20260728

- 正文定位：`projects/gros/archive/debug/2026-07-28-app-uart-time-sync-low-power-busy.md`
- 完整正文 SHA256：`c968bdf0bd4266377b652754c93a28030d611d2e2692148bbaa32a4967e16ded`
- 原状态：`reviewing`；登记 owner：`leiwenjun`；原复核日期：`2026-10-28`。
- `body_read_complete=true`；`semantic_review_performed=true`；真人复核未执行。
- AI 结论：`accept-historical-record`。
- 适用范围与内容判断：0x1A与0x04争单ACK槽引发本地BUSY及transaction mutex修复。
- 证据及验证边界：构建与静态测试通过，20次SLEEP设备复测未执行；DHD整体门禁仍失败。
- 发现：本次审读未发现确定的正文矛盾；不据此推导外部事实已验证。
- 处理结果或后续动作：保留本地BUSY而非MCU NACK归因；不从mutex存在推导设备竞争已验证或整体低功耗PASS。
- 下一复核建议：按历史记录保留；引用为当前事实前重验相应源码、制品或外部证据。

