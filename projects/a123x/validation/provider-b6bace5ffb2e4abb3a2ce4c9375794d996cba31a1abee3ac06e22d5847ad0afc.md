---
id: provider-b6bace5ffb2e4abb3a2ce4c9375794d996cba31a1abee3ac06e22d5847ad0afc
title: A123X提交前门禁整改与本机复验20261026
kind: validation
domain: projects/a123x
path: projects/a123x/validation/provider-b6bace5ffb2e4abb3a2ce4c9375794d996cba31a1abee3ac06e22d5847ad0afc.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:b6bace5ffb2e4abb3a2ce4c9375794d996cba31a1abee3ac06e22d5847ad0afc
  source_sha256: 4a3525c5eb83ce81145383c0762ad8390243393b8c97a314104707dbb40c62c5
  temporary_source_retained: false
review_after: '2027-01-24'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/a123x/validation/provider-b6bace5ffb2e4abb3a2ce4c9375794d996cba31a1abee3ac06e22d5847ad0afc.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/validation/provider-b6bace5ffb2e4abb3a2ce4c9375794d996cba31a1abee3ac06e22d5847ad0afc.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-26'
updated_at: '2026-10-26'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-26'
manual_validation_pending: true
summary_zh: 本轮整改关闭已复现的本机检查失败；未暂存、提交、推送、部署或清理原始材料。各仓既有dirty保留。本结果不代表整批功能、完整固件或产品通过。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: b6bace5ffb2e4abb3a2ce4c9375794d996cba31a1abee3ac06e22d5847ad0afc
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
aliases:
- A123X提交前门禁整改与本机复验20261026
related:
- projects/a123x/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# A123X 提交前门禁整改与本机复验 2026-10-26

本轮整改关闭已复现的本机检查失败；未暂存、提交、推送、部署或清理原始材料。各仓既有dirty保留。本结果不代表整批功能、完整固件或产品通过。

## 最终实现

1. integration板型检查对Linux Wi-Fi/Camera/Display及U-Boot显示项目增量分别固定hash；rootfs项目元数据与索引精确一致。参考树只使用原厂基线加该层登记增量；缺hash、内容漂移、额外硬件节点仍拒绝。hardware_approved和flash_approved保持false。
2. rootfs hook按本次隔离Kconfig选择BOOT_LOGO，避免活动DEVWIRE配置影响EVT1。未修改活动.config。
3. 通用NV3006A组件不含产品路径，保留旧产品文件；F20产品Makefile在安装策略前拒绝旧显示程序/库及悬空链接，要求显式迁移，不自动覆盖、删除。负例检查文件保留和产品元数据未安装。
4. 修复telemetry转发脚本CDPATH空值写法。release-tool忽略Python缓存，MBP精确忽略已确认的编译输出和SDK安装Makefile链接；音频源码仍可见，文件均保留，已跟踪预编译输入不受影响。
5. 增补703个既有材料的discovery-unreviewed身份清单，细分559项未审查参考、135项随附编译产物、9项抓包/数据库附件。只登记路径/hash，不执行或上传原件，不作为可信源码、发布载荷或本次构建证据。逐项hash和精确覆盖规则不放宽。
6. 当前使用说明对齐20MHz/1-bit/OOB与显式SPI设备显示接口；历史25MHz/inband设备记录仍是历史证据。

## 验证证据

| 命令或检查 | 退出码 | 结果 |
| --- | --- | --- |
| integration/scripts/a123x-check.sh --scope unit --require-complete | 0 | 最终214项全部执行通过，无skip |
| 同入口 --scope sdk --sdk-root 当前RC1 SDK | 0 | 94项选中，88项执行通过、6项skip，覆盖不完整 |
| python3 -B -m unittest discover -s project/tools/codex_assets -p test_*.py | 0 | 最终145项通过，110.653秒 |
| 板型CLI --compile --dtc /usr/bin/dtc，从/tmp调用 | 0 | DEVWIRE/EVT1 Kconfig、Linux/U-Boot DTS、rootfs hook通过；7项供应商基线不变 |
| project/scripts/validate.sh --dry-run | 0 | 201条原件历史记录保持，1580补充项，1774唯一文件精确覆盖/hash通过；10条EV |
| 同入口 --metadata-only --dry-run | 0 | 元数据通过，不验证来源字节与外部依赖 |
| integration/scripts/a123x-docs-check.sh | 0 | 45份文档、169个本地链接；未检查远端 |
| 两仓scripts的bash -n、shellcheck及telemetry外部cwd help | 0 | 通过 |
| 10个有改动仓库的git diff --check与暂存检查 | 0 | 全部通过，staged_files均为0；外层容器仓干净 |

SDK跳过原因：BusyBox applet隔离1项、libgpiod stage1项、native Dropbear能力/协议4项，均缺显式测试输入。Host/隔离编译/规则测试不替代最终镜像或设备验收。

active_config_unchanged=true；活动配置SHA256：7a3000c3ce1b43068535f0dad27eb3b37c8e22bdc379a89fb214f966ba1bcdcb。
Linux显示增量SHA256：eb5ff7c63496ec45042218f25493038b126e9b975291009f1a68d0074f808158。
U-Boot项目增量SHA256：602a6ad30d1633753684b9439b537f0a0ee80b2710756c5f303c423dad86f77d。

## 复审与剩余边界

Review Target为本轮working-tree增量；Reviewer Independence为author-self-review，没有独立owner签收。最终机械门禁支持本轮整改关闭，不声明整批dirty可合并。

负结果保留：初始资料覆盖与显示hash失败；后续暴露rootfs元数据旧hash、U-Boot增量未登记、rootfs探测串用活动Logo，以及旧owner保护与组件中立契约冲突。按跨仓固定点和产品分层修复，未放宽拒绝断言。

旧显示owner须显式迁移；索引、rootfs项目元数据和检查器须配套。回退仅撤销本轮增量，不能整文件checkout覆盖已有dirty。提交按门禁/资料治理、显示启动、音频/传感器、蓝牙、telemetry及各自跨仓依赖拆分，不进行宽泛staging。W1U版本文件删除可追溯到供应商clean规则，本轮保留现场且不列为功能提交。

未执行新完整固件、最终镜像门禁、远端引用检查、部署或Board/HIL。材料获取路径、许可/安全、团队远端复现及owner审查仍需责任人落实。Codify Decision：复用固定增量和分层验收，promotion_candidate=false；缺独立owner及匹配制品/HIL，不推广为产品放行。Runtime final结果另报。
