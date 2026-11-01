---
id: provider-f007bf9fd41ada9a453180263b3dbc21f08fd9d6154ca8a4ddfaf0fd12894f5b
title: A123X 调试包SHA校验与循环依赖修复验证
kind: validation
domain: projects/a123x
path: projects/a123x/validation/provider-f007bf9fd41ada9a453180263b3dbc21f08fd9d6154ca8a4ddfaf0fd12894f5b.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:f007bf9fd41ada9a453180263b3dbc21f08fd9d6154ca8a4ddfaf0fd12894f5b
  source_sha256: b75dcc04a02e09bbda35c83e2f981ddec96e4de25f438805ab27fc5a12ce72ed
  temporary_source_retained: false
review_after: '2027-01-20'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/a123x/validation/provider-f007bf9fd41ada9a453180263b3dbc21f08fd9d6154ca8a4ddfaf0fd12894f5b.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/validation/provider-f007bf9fd41ada9a453180263b3dbc21f08fd9d6154ca8a4ddfaf0fd12894f5b.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-22'
updated_at: '2026-10-22'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-22'
manual_validation_pending: true
summary_zh: 日期：2026-10-22。结论范围：源码修复、包规则与工具阶段验证；不代表新三板固件或实板通过。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: f007bf9fd41ada9a453180263b3dbc21f08fd9d6154ca8a4ddfaf0fd12894f5b
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
aliases:
- A123X 调试包SHA校验与循环依赖修复验证
related:
- projects/a123x/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# A123X SDK 调试包构建失败修复

日期：2026-10-22。结论范围：源码修复、包规则与工具阶段验证；不代表新三板固件或实板通过。

## 根因

用户运行三板串行构建，清理和CB400配置成功，工具阶段在libpcap校验退出。Makefile中的预期SHA256误写为67位，实际下载归档的SHA256为64位，导致sha256sum解析输入失败；不是当前归档损坏。

同时日志出现工具循环依赖：SDK在包被选中时已建立“包总目标依赖rootfs安装”，新增挂钩反向依赖包总目标形成循环。先前隔离验证使用缓存，且未覆盖所有工具选中的原生分支，因此不能代替本次验证。

## 修复

- 修正Makefile.debug-tools与tool-sources中的libpcap哈希，使其与实际已核验归档一致。
- 将七个包的rootfs安装依赖改为SDK原生的安装子目标，消除反向循环；iw构建显式等待libnl安装stamp。
- 未修改SDK通用包生成器、板型定义、下载归档或其他任务dirty。

## 回归

新增四项测试先复现失败，修复后全部通过：全部固定hash长度与缓存一致性、全新缓存libpcap准备、损坏包不生成准备stamp、所有工具选中时依赖图无环。合并构建切换、ADB/SSH和板端诊断回归共50项通过。

实际工具阶段：当前CB400配置使用SDK原生tools入口重放通过，exit_code=0，耗时127.175秒；日志无循环依赖警告。strace、gdbserver、ethtool、tcpdump、ip、ss、iw、iperf均安装为AArch64程序。其余板型完整构建仍由用户执行。

工具阶段回执SHA256：d447f81aaf292fb35f6d053e1a85a75bc537387b4211fb9c79ce0d22ed2a2292；日志SHA256：d4db6432ec0e98fe76324b3c20f2a4767eeddb57af9816d2ed43b79f5cbb593f。

## 保留与交接

保留原clean/configure通过证据、旧镜像和失败回执；不将旧产物计为修复后固件。修复期间持有SDK协作锁，结束释放。未提交推送、未启动完整固件构建、未访问设备。

复用模式：包规则测试必须覆盖Kconfig选中和未选中分支、全新缓存和损坏缓存，不能只依赖已准备stamp。owner review与Board/HIL仍待完成；不作为通用运行资产推广。回退仅限本轮两个SDK文件及新增回归，不覆盖其他dirty。
