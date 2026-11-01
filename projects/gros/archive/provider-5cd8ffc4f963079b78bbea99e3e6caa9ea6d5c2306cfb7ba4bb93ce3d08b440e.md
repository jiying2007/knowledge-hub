---
id: provider-5cd8ffc4f963079b78bbea99e3e6caa9ea6d5c2306cfb7ba4bb93ce3d08b440e
title: PCR02 手动 WiFi 切换与重复扫描分析补录
kind: debug-record
domain: projects/gros
path: projects/gros/archive/provider-5cd8ffc4f963079b78bbea99e3e6caa9ea6d5c2306cfb7ba4bb93ce3d08b440e.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:5cd8ffc4f963079b78bbea99e3e6caa9ea6d5c2306cfb7ba4bb93ce3d08b440e
  source_sha256: a699ed2a4928587d57dc2651402143257f2b3fe19538b7989ab5ec259709cdd1
  temporary_source_retained: false
review_after: '2027-01-19'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- debug-record
validation_refs:
- projects/gros/archive/provider-5cd8ffc4f963079b78bbea99e3e6caa9ea6d5c2306cfb7ba4bb93ce3d08b440e.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gros/archive/provider-5cd8ffc4f963079b78bbea99e3e6caa9ea6d5c2306cfb7ba4bb93ce3d08b440e.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-21'
updated_at: '2026-10-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-21'
manual_validation_pending: true
summary_zh: 历史证据日期：2026-10-19；补录核对日期：2026-10-21。历史会话 01a14268-6400-7222-b17e-427b4b38a619。原输入为部分乱序日志和本地源码；此处去除网络名称、BSSID尾部和网段值。没有设备安装制品身份，本次未重跑。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: gros
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 5cd8ffc4f963079b78bbea99e3e6caa9ea6d5c2306cfb7ba4bb93ce3d08b440e
provenance:
  source_kind: document
  source_ref: session:01a14268-6400-7222-b17e-427b4b38a619;document:wifi-manual-switch-analysis-20261019.md;sha256:2a030d2f062df90019ffa096581902b98596e515f5d8e2bf7061b263b5181ae2
  verification_state: declared
---

# PCR02 手动 WiFi 切换与重复扫描分析补录

历史证据日期：2026-10-19；补录核对日期：2026-10-21。历史会话 01a14268-6400-7222-b17e-427b4b38a619。原输入为部分乱序日志和本地源码；此处去除网络名称、BSSID尾部和网段值。没有设备安装制品身份，本次未重跑。

原记录显示手动切换控制处理约4.14秒，WPA关联及DHCP成功，并非DHCP卡死。API ScanStart与GetScanResults都调用无条件触发SCAN的路径，日志中两次约2.18/2.15秒扫描与源码一致；同步扫描返回后补发STARTED形成误导。

Sensor同一worker同步connect，回调只排队，返回后集中消费旧通知。转换通知虽已核快照，DISCONNECTED仍可能直接置断开；同一generation不能排除同次切换的旧链路事件。重复connected日志也不等于多次真实关联。另有两个匿名BSSID跨不同子网往返，必须保留真实地址重建语义，不能以同SSID掩盖offline。

原建议是明确start/fetch缓存和终态owner、对迟到断连通知按新鲜快照判定、对重复成功去重副作用，继续取驱动/AP证据。IoT源码不可见，提前success ACK只确认日志行为。该条为修复前分析；后续扫描与通知修复已有独立候选，不把当时发现表述为当前版本仍未修复。
