---
id: provider-bd58125c34fc929ea8d289ed80a45f7782cf0de46a4a1c87fec3acffc4df03e0
title: WiFi持久化实现全面复审：初始化中断和多网策略恢复三项缺口
kind: validation
domain: projects/gros
path: projects/gros/validation/provider-bd58125c34fc929ea8d289ed80a45f7782cf0de46a4a1c87fec3acffc4df03e0.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:bd58125c34fc929ea8d289ed80a45f7782cf0de46a4a1c87fec3acffc4df03e0
  source_sha256: 279d33b8dfce22d4343661d998dc1b605de3b3ac8df5e31c224fcf71673e92a3
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
- projects/gros/validation/provider-bd58125c34fc929ea8d289ed80a45f7782cf0de46a4a1c87fec3acffc4df03e0.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gros/validation/provider-bd58125c34fc929ea8d289ed80a45f7782cf0de46a4a1c87fec3acffc4df03e0.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-19'
updated_at: '2026-10-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-19'
manual_validation_pending: true
summary_zh: 日期：2026-10-19。Review Target：working-tree；latest_worktree_reviewed=true。范围仅 sensor/api/wifi 本轮持久化与缓存修改；无源码修改、提交、推送、设备写入。既有音频脏改排除。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: gros
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: bd58125c34fc929ea8d289ed80a45f7782cf0de46a4a1c87fec3acffc4df03e0
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
aliases:
- WiFi持久化实现全面复审：初始化中断和多网策略恢复三项缺口
related:
- projects/gros/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# WiFi 持久化实现全面复审

日期：2026-10-19。Review Target：working-tree；latest_worktree_reviewed=true。范围仅 sensor/api/wifi 本轮持久化与缓存修改；无源码修改、提交、推送、设备写入。既有音频脏改排除。

## 快照与验收

- Sensor HEAD 6fb68755c68be8ca0410952d9ebd7b94a16fdb92；任务 tracked diff SHA256 2a34695d42911a9319eb6b85144a2088753651c3ea94613a8a43f493911d564c。
- API HEAD 53b557b0ae39368653041d299abb18732e5132ee；任务 tracked diff SHA256 a7b46f801a17cfcc5a5d6b044f01bb82c05fe87cb4d0d1dd57a7a7b814b76a05。
- WiFi HEAD 5c3f8bc06a6c73ed8cbbc78319600fefe3cfc8d3；任务 tracked diff SHA256 ba86f1c10186902655eefa74a8460c5d49f79660ab665db2d263df60182a7e5c。
- 新初始化头 SHA256 a1affddca60e8023744925d188c73543365a2cdf9ba6b62b1f969bb4d49ae992。
- Baseline：保护已有非空配置及软链；修复空配置；连接成功与落盘失败分离；重试不能固化临时策略；缓存查询不覆盖新代次。
- 主审结合 fresh independent whole-diff/lifecycle review；独立复审同样确认下列3项major。Spec/Quality verdict均 NEEDS_FIX；blocker=0, major=3。前轮局部PASS不足以证明整体通过，本报告更新该结论。

## 已核实问题

1. Major：wpa_config_file.h:30-47 原地写默认内容，同时把任意非空文件当作已完成。部分write后进程终止，rollback不会执行，后续启动永久保留残片，可能缺update_config或语法不完整。主审Host注入write仅落8字节后_exit，父进程重新调用真实helper，返回0且仍8字节，已复现。未做真实断电实验。建议为初始化引入可恢复事务，保留用户既有非空配置及软链；补中断恢复测试。
2. Major：linux_common.c:1035-1061 配置准备函数与上层均void，失败仅返回；1109-1110 无条件标记已更新，1113继续启动或接入后台。目录/锁/写入/fsync等暂态失败无法反馈，同进程下一次初始化会跳过准备，直到deinit清标记。源码调用链已核实，未注入整套init_wpad。建议传播必要配置准备结果，失败不设置完成标记，区分冷启动失败与已有链路的持久化降级。
3. Major：linux_sta.c:1651 临时禁用所有网络；2753连接成功后恢复其他网络失败仅warn；924-941新增Confirm只SAVE_CONFIG+sync，未补齐944-952的恢复步骤。后续SAVE成功可固化遗留disabled=1，Sensor2441/2463清pending，历史多网自动恢复问题可能重新暴露。主审Host使用真实wpa_conf_enable_all_networks及Confirm，mock第2网络disabled=0操作失败，再允许操作成功，Confirm返回成功而恢复调用数未增加；SAVE后端mock，未证明真实磁盘写入内容。建议区分策略恢复与单纯SAVE失败，重试补齐未完成步骤，保持连接不受扰动。

## 新鲜验证与限制

- 三仓持久化Host suites本轮重跑通过，使用各仓tests/persistence或tests/wifi_persistence入口；ASAN/UBSAN。
- 三仓git diff --check本轮通过。
- 两个独立/tmp故障注入程序成功复现上述1、3的控制流缺口；没有修改生产源码。
- Sensor代次拒绝、退避上限、停止/低功耗门禁和API在途计数未发现新的确定性问题。
- 本轮没有重跑ARM对象编译、完整链接、制品打包或HIL；先前对象构建证据仅是先前证据。源码/Host验证不能替代设备制品身份、冷启动、重启或OTA保持验证。
- 现场/etc和/data/etc同文件软链来自用户确认；本轮问题不以路径不一致为前提。没有把潜在失败路径归因为现场已发生事实。

以上均为项目 reviewing candidate，非产品放行或owner批准。本次只交付审查，三项缺陷待修复。
