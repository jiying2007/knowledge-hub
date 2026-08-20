---
id: pcr02-customer-ubi-startup-optimization-20260803
title: PCR02 customer 静态 UBI 卷启动扫描优化候选
kind: decision
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/decisions/pcr02-customer-ubi-startup-optimization-20260803.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: current-session-debug-and-decision
  source_sha256: c55b5e6a40bd8dbca6d36dd0401025d74195ecee59e9db36f3bcca1141a41f90
review_after: '2026-11-03'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- ubi
- boot-optimization
- release-security
validation_refs:
- projects/pcr02-ssc305/decisions/pcr02-customer-ubi-startup-optimization-20260803.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/pcr02-ssc305/decisions/pcr02-customer-ubi-startup-optimization-20260803.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-03'
updated_at: '2026-08-03'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-03'
manual_validation_pending: true
summary_zh: customer 静态 UBI 卷首次打开会全量读取约 51.4 MiB 并校验 CRC，稳定阻塞约 4.37 秒；短期候选为 OTA 写后可信 readback 验证再设置 skip_check，长期优先评估 dm-verity，未获准直接进入量产。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 customer 静态 UBI 卷启动扫描优化候选
related:
- projects/pcr02-ssc305/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 customer 静态 UBI 卷启动扫描优化候选

## 背景

PCR02 release 镜像将 `/customer` 制作为静态 UBI 卷，其中承载只读
SquashFS。两份启动测量显示，卷首次打开时稳定消耗约 4.36～4.38 秒，直接推迟
应用和用户可感知的开机动画。

本记录只保存脱敏后的测量摘要、实现依据和方案边界，不保存原始串口日志、设备
标识、二进制、内部服务地址或凭证。

## 实测结论

- customer 卷类型：static UBI volume。
- 文件系统：SquashFS，当前压缩算法为 LZO。
- `used_ebs=213`，`used_bytes=53,886,976`，约 51.4 MiB。
- 两次 `ubi_check_volume()` 测量分别约 4.360 秒和 4.375 秒。
- 有效顺序读取和 CRC 校验速度约 11.8 MiB/s。
- `ubiblock_create()` 仅为几十毫秒，SquashFS mount 仅为十毫秒量级，均不是主要
  瓶颈。

内核实现表明，`ubi_check_volume()` 会遍历静态卷全部已使用 LEB，通过
`ubi_eba_read_leb(..., check=1)` 完整读取并校验数据 CRC；动态卷直接跳过。因此
该耗时与实际写入字节数近似线性相关，不是 UBI attach、ubiblock 创建或
SquashFS 解压造成的等待。

## 候选方案比较

### 方案一：OTA/生产写入验证完成后设置 skip_check

UBI 原生提供 `UBI_VOL_SKIP_CRC_CHECK_FLG`，内核文档明确将缩短启动时间列为主要
用途，但只允许在上层能够验证数据完整性时使用。U-Boot 同样支持为指定卷设置或
清除 `skip_check`，本机构建使用的 `ubinize` 也支持 `vol_flags=skip-check`。

建议的受控流程是：

1. OTA 包包含受签名 manifest 和 customer 镜像 hash。
2. 写入静态卷后执行全量 readback，并计算 SHA-256。
3. 只有读回结果与可信 manifest 一致时，才设置 `skip_check` 并允许版本切换。
4. OTA 中断、校验失败或状态不完整时禁止切换，并进入回滚或恢复流程。
5. 日常启动跳过全卷 CRC；可在空闲或充电阶段执行后台巡检。

预计正常启动可接近完整节省约 4.37 秒。该方案仍会降低每次启动主动发现后续
NAND 静默损坏的能力，NAND ECC 和按需读取错误不能完全等价替代全卷 CRC，因此
目前仅为 reviewing 候选，不能无条件进入量产镜像。

### 方案二：skip_check 配合 dm-verity

长期 release 安全架构建议为：静态 UBI → ubiblock → dm-verity → SquashFS。
dm-verity 按访问块校验，无需开机顺序扫描整卷；若 root hash 由 Secure Boot
信任链或签名 manifest 保护，可同时覆盖随机损坏和内容篡改。

该方案能兼顾启动速度、SquashFS 只读压缩和 release 防篡改，是长期优先方向。
当前内核尚未启用 Device Mapper/DM Verity，需要补充内核配置、hash tree 布局、
可信 root hash 传递、启动映射、OTA 和回滚验证。

### 方案三：customer 改为动态 UBI 上的只读 UBIFS

UBIFS 按需读取并校验节点，不在首次打开时扫描整个卷，预计可消除大部分 4 秒级
等待，改造量低于 dm-verity。但它会改变镜像格式和 OTA 契约，也不具备
SquashFS 同等级的物理不可变性；需要验证内存、压缩率、掉电、recovery、只读
挂载和回滚行为。综合 release 安全要求，不作为当前首选。

### 方案四：拆分或缩小 customer

将启动必需程序、动画和音频放入较小静态卷，大型模型和非启动资源延迟挂载，
可以在不降低 UBI CRC 保障的前提下减少阻塞时间。按当前吞吐，每减少 10 MiB
大约节省 0.85 秒。该方案会增加分区、镜像和 OTA 多卷管理复杂度，作为无法接受
`skip_check` 风险时的保守备选。

更高压缩率也能减少被扫描字节数，但需要同时测量应用启动阶段解压开销，只能
作为辅助优化。UBI fastmap、继续优化 ubiblock 创建或 SquashFS mount 均不能
解决本瓶颈。

## 当前建议

1. 短期优先验证“OTA/生产写入后全量 SHA-256 readback，通过后设置
   `skip_check`”的原型和断电状态机；量产启用必须经过安全评审和板端故障注入。
2. release 安全专项评估 dm-verity 和可信 root hash，将按需完整性校验作为长期
   目标。
3. 若完整性风险暂不接受，则选择缩小/拆分 customer，不直接注释
   `ubi_check_volume()`，也不无条件设置卷标志。

## 验证要求

- 对比开启前后的 UBI attach、卷打开、挂载、首帧动画和开机音频时间。
- 覆盖正常 OTA、写入中断、读回 hash 失败、卷损坏、坏块增长和版本回滚。
- 验证 UBI 标志在量产烧录、OTA 更新、卷重建和恢复流程中的持久化行为。
- 若采用 dm-verity，验证 hash tree 损坏、数据块损坏、root hash 篡改和启动失败
  策略。

## 决策状态与边界

本记录为 AI 整理的 reviewing 候选，等待 owner 和板端证据确认；不授权修改量产
镜像、不提升为 active 规则、不写 memory。此前“量产 release 保持最小化、
debug 仅用于开发测试”的边界继续有效。

## Archive evidence

- Source: 当前排障会话的脱敏测量摘要与本地内核/镜像构建源码审查。
- Topic: pcr02-customer-ubi-startup-optimization。
- Captured at: 2026-08-03 Asia/Hong_Kong。
- Sanitization: 未保存原始日志、设备唯一标识、凭证、二进制或内部端点。
- Provenance: Linux 5.10 UBI 实现、PCR02 customer 镜像配置和两次板端启动测量。
- Verification: 源码静态核对和两次启动时间交叉对比；方案尚未板端实施。
- Memory Candidate: no。
- Gate Result: reviewing，需 owner、安全评审和 HIL 验证。
