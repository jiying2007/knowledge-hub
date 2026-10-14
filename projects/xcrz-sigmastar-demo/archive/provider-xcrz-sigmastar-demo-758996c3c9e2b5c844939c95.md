---
id: provider-xcrz-sigmastar-demo-758996c3c9e2b5c844939c95
title: PCR02 pstore 现场核验与暂缓启用
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-758996c3c9e2b5c844939c95.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:758996c3c9e2b5c844939c9578d903d7a83829891a0ec8863e4a17939408c098
  source_sha256: fcad17727c5bf6d4023cc77117b6335d9e07178fef8dbf2c04da47b71faac00a
  temporary_source_retained: false
review_after: '2027-01-11'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- debug-record
validation_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-758996c3c9e2b5c844939c95.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-758996c3c9e2b5c844939c95.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-13'
updated_at: '2026-10-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-13'
manual_validation_pending: true
summary_zh: '- captured_at: 2026-10-13 - last_verified: 2026-10-13 - status: reviewing - topic: debug-notes - source: 本侧会话用户提供的量产设备只读输出、本地
  SigmaStar sigdoc、SDK Git 历史及当前 BSP 源码。 - scope: pstore 存储链路及升级风险，不包含主线程系统卡死根因判定。 - sanitization: 仅保存必要结论和证据定位，不包含原始日志、完整进程列表、设备端点或客户信息。'
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 758996c3c9e2b5c844939c9578d903d7a83829891a0ec8863e4a17939408c098
---

# PCR02 pstore 现场核验与暂缓启用

- captured_at: 2026-10-13
- last_verified: 2026-10-13
- status: reviewing
- topic: debug-notes
- source: 本侧会话用户提供的量产设备只读输出、本地 SigmaStar sigdoc、SDK Git 历史及当前 BSP 源码。
- scope: pstore 存储链路及升级风险，不包含主线程系统卡死根因判定。
- sanitization: 仅保存必要结论和证据定位，不包含原始日志、完整进程列表、设备端点或客户信息。

## 结论与决定

用户决定暂不启用原始 MTD pstore，并要求撤回本次候选改动。保留现有 FWFS 格式及启动方式；未进行设备写入、格式迁移、部署或提交。当前证据不支持声明内核 pstore 已有效保存异常，也不支持声明 pstore 缺失就是系统卡死根因。

## 现场证据

用户提供的设备输出确认：mtd7 标签 PSTORE，大小 2 MiB，擦除块 256 KiB；FWFS 进程将 /dev/mtd7 挂载到 /pstore，挂载类型 fuse.fwfs。仅 pstore、pstore_zone 模块已加载；backend 参数为 (null)，pstore_blk 参数目录不存在。/pstore 与 /sys/fs/pstore 无可见记录，/proc/mounts 无 pstore 类型挂载。启动脚本只显示加载上述两个框架模块，未见后端注册日志。

这足以确认现场快照中内核 pstore 后端未注册。FWFS 是普通文件存储的一种可能载体，但本次证据没有证明存在日志采集或重启归档程序。空目录不代表 Flash 已擦除；框架模块存在、目录存在不等于存储后端启用。watchdogd 线程存在不证明硬件看门狗开启或会触发 Panic。

## 厂商资料与源码边界

资料位置：SDK 根目录下 SGSDocs/sigdoc；相关主题为 customer/Common/Development/debug_sop_zh.html、partitionfile_zh.html 和 platform/BSP/watchdog_zh.html。

检索 HTML 正文及解码后的全文索引，pstore、mtdpstore、mtdoops、ramoops 未命中。Debug SOP 的系统挂死章节描述 RTOS exception log 与 ELF 定位；Linux Watchdog 文档描述标准接口和超时复位，未承诺复位前保存 pstore；分区文档描述 FWFS 跨 U-Boot/Linux/RTK 文件访问。这些内容不能作为 Linux pstore 已接通的证据。

当前 BSP 的 drivers/mtd/mtdpstore.c 按 MTD 名称或数字编号匹配，注册 DMESG 前端及 panic_write。fs/pstore/blk.c 通用后端要求块设备，不接受普通文件；通用写入在中断上下文或 IRQ 关闭时返回忙。SigmaStar SPI NAND 驱动已有 oops_panic_write 对应的轮询路径。若未来启用，候选方向为原生 pstore/pstore_zone/pstore_blk/mtdpstore 独占 PSTORE；不能与 FWFS 共用该 MTD。

纯硬卡死后直接断电仍可能无新记录：原生 MTD 方案需要 CPU、异常处理和 Flash 写入仍能执行。写入完成的记录留存与完全硬卡死时产生记录是不同验收项。

## 历史来源

历史归属：SDK 父仓，目标配置为 SourceCode/project/image/configs/general/spinand_MX35_512M.squashfs.partition.config。

- c38cb429d，2025-12-26：新增用于 pstore 的 VSKERNELMTD 分区，指定 FWFS 并加入普通挂载列表；提交说明提及修复 pstore，但未找到选择 FWFS 的设计理由或板端验收证据。
- 7425c8e18，2026-04-30：将已有分区改名 PSTORE 并保留 FWFS，主要调整布局及坏块预留。该提交不是首次引入 FWFS。

沿用普通文件系统模板属于推断，不是已确认的开发者动机。

## 升级风险

核对的 OTA_IMAGE_LIST 不含 pstore。仅更新启动代码而保留旧 FWFS 介质，无法保证新 MTD 后端生效；直接接管可能触发后端擦写并损坏旧格式。空目录不能替代初始化。一次性格式切换会清除旧数据，必须先确认全部适用量产版本用途，并验证断电、回退及实际升级包。当前未形成量产升级安全证据，因此暂缓。

## 撤回与验证

已使用定向补丁撤回六个跟踪文件中的候选改动：分区配置、image.mk、rootfs.mk、script.mk、debug/release 模块列表。删除五个本次新增文件：pstore_mtd_probe.c、pstore_start.sh、README-pstore.md、test_pstore_mtd_probe.c、test_pstore_start.py。

新鲜检查：project/image 与指定模块列表目录 Git 状态无改动；新增 raw pstore 开关、脚本与探测器引用检索无残留；SDK 父仓 git diff --check 通过。未回退其他已有修改。未构建新固件，未部署或擦除设备，无 commit/push。

## 后续条件

如重新启用，先在与量产固件和介质一致的可恢复测试板验证：旧版升级、初始化断电恢复、旧版回退、受控 Panic 留存、重启读取、写入完成后断电读取、普通升级保留记录。不得将这些尚未执行的验证记为通过。
