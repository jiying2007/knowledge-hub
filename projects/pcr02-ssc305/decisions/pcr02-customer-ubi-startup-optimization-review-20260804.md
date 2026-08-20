---
id: pcr02-customer-ubi-startup-optimization-review-20260804
title: PCR02 customer UBI 启动优化复核决策候选
kind: decision
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/decisions/pcr02-customer-ubi-startup-optimization-review-20260804.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: current-session-review-and-owner-archive-request
  source_sha256: 04f3ee2d76e448d5d229a04d2abd573ec61e4f55fca5d2a83cc951a84b56cec7
review_after: '2026-11-04'
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
- supersedes-candidate
validation_refs:
- projects/pcr02-ssc305/decisions/pcr02-customer-ubi-startup-optimization-review-20260804.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/pcr02-ssc305/decisions/pcr02-customer-ubi-startup-optimization-review-20260804.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-04'
updated_at: '2026-08-04'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-04'
manual_validation_pending: true
summary_zh: 复核后否决当前量产直接使用纯 skip_check；近期保留静态 UBI 全卷 CRC，优先将 /config 早期硬件与模块初始化和 customer 扫描并行，压缩算法独立 A/B，仍不达标再评审按需 LEB CRC，长期目标为可信
  dm-verity。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 customer UBI 启动优化复核决策候选
related:
- projects/pcr02-ssc305/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 customer UBI 启动优化复核决策候选

## 复核目的

复核 2026-08-03 的 customer 静态 UBI 卷启动优化候选，重点验证“OTA 写后校验
再设置 `skip_check`”能否由当前 Linux、OTA 和 release 安全链直接落地，并在不
降低量产完整性保障的条件下收敛近期方案。

本候选拟 supersede
`pcr02-customer-ubi-startup-optimization-20260803` 中的短期实施优先级；旧记录保留
为历史 provenance，不删除、不静默改写。两者均保持 reviewing，最终取代关系仍
需 owner 复核。

## 已确认基线

- `/customer` 是静态 UBI 卷上的只读 SquashFS，当前使用 LZO。
- `used_ebs=213`、`used_bytes=53,886,976`，约 51.4 MiB。
- 两次 `ubi_check_volume()` 测量约为 4.360 秒和 4.375 秒，有效吞吐约
  11.8 MiB/s。
- `ubiblock_create()` 为几十毫秒，SquashFS mount 为十毫秒量级，不是主要瓶颈。
- 启动脚本先完成 customer 全卷 CRC，再执行 GPIO、内核模块加载和应用启动，
  因而存在可重叠的串行阶段。

## 对旧建议的修正

### 当前不能把纯 skip_check 作为近期量产方案

复核内核路径确认：

1. ubiblock 正常读取使用 `ubi_read_sg()`，最终以 `check=0` 调用静态卷读取；如果
   首次打开同时被 `skip_check` 跳过，后续普通 SquashFS 读取不会执行等价的 UBI
   数据 CRC，仅保留 NAND ECC 错误检测。
2. 当前 Linux 的 `UBI_IOCSETVOLPROP` 只提供 dynamic volume direct-write 属性，
   没有持久设置或清除 `skip_check` 的标准接口。现有可用路径是镜像生成时写入
   `vol_flags=skip-check`、通过 U-Boot 修改卷表，或新增自定义内核接口。
3. 当前 OTA 收尾路径只重新计算并记录升级包 MD5；尚未形成发布者签名、customer
   写后全量 readback、可信 manifest、可信根和跨分区回滚闭环。

因此，旧候选中的“OTA 写后验证通过便设置 `skip_check`”是长期前提成立后的方案，
不是当前可直接实施的量产优化。不得仅依赖 MD5、NAND ECC 或 SquashFS 只读属性
取消 UBI 全卷 CRC。

## 近期推荐方案

### 第一优先级：保留 CRC，将早期硬件初始化与 customer 扫描并行

将当前 `/customer/demo.sh` 拆成：

- rootfs 中的 `early_hw_init.sh`：GPIO 设置，以及只依赖已挂载 `/config` 的内核
  模块初始化；
- customer 中的应用启动阶段：在 customer 挂载且早期初始化成功后启动
  `prog_application.sh`。

推荐启动时序：

```text
mount /config
├─ early_hw_init.sh &
└─ ubiblock -c /dev/ubi0_3 &
wait 两个任务并核验退出码
mount /customer
start prog_application.sh
```

实施约束：

- 保持现有模块依赖顺序，不把单个 `insmod` 无序并行。
- 两个后台任务独立记录 PID、耗时和退出码；任一失败都不启动主应用。
- 不改变静态卷类型、分区布局、OTA 格式和 UBI 完整性语义。
- 先作为单变量实施，避免与压缩算法、模块裁剪或应用初始化重排混在同一轮。

从现有时序看，CRC 完成后到 launcher 仍存在约秒级的 GPIO/模块初始化窗口；并行
可望隐藏其中约 1～2 秒，但真实收益必须以板端 P50/P95 为准。由于模块文件也从
同一 NAND 上的 `/config` 读取，不能直接把串行耗时相加作为收益承诺。

### 第二优先级：独立进行 SquashFS 压缩 A/B

在同一 customer 源目录上的主机侧对照结果：

| 压缩 | 镜像大小 | 相对当前 LZO | 按线性吞吐估算的 CRC 时间 |
| --- | ---: | ---: | ---: |
| LZO 当前值 | 51.4 MiB | 基线 | 约 4.37 秒 |
| XZ | 43.14 MiB | 约减少 16% | 约 3.67 秒 |
| ZSTD level 15 | 45.49 MiB | 约减少 11% | 约 3.87 秒 |

XZ 已被当前内核 SquashFS 配置支持；ZSTD 需要启用 `CONFIG_SQUASHFS_ZSTD`。镜像
更小只证明 CRC 扫描字节减少，不能证明 `prog_pcr02` 和资源的按需解压更快，因此
必须在并行初始化方案单独验证后，再以开机动画、开机音频和应用可交互 P50/P95
做独立 A/B。

## 若近期收益仍不足

### 中期候选：按需 LEB CRC，开机动画后后台补扫

相比纯 `skip_check`，更合适的中期内核方案是让 ubiblock 成为上层完整性校验者：

1. customer 卷使用 `skip_check` 避免首次打开全扫。
2. ubiblock 首次访问某个 LEB 时，先完整读取该 LEB并使用 VID 中的数据 CRC
   校验，再向 SquashFS 返回数据。
3. 用 bitmap 缓存已验证 LEB，避免重复全块读取。
4. RobotStartUpAction 或应用 ready 后，由后台 worker 校验剩余 LEB。
5. CRC 失败时返回 I/O 错误、标记卷损坏并进入回滚或恢复策略。

该方案不改变 customer 磁盘格式和 OTA 分区，但需要自定义约 248 KiB LEB 缓冲、
并发锁、verified bitmap、后台 worker 和故障处理，必须覆盖关键/非关键 LEB
损坏、并发读取、内存压力、掉电和回滚测试。它保持对已访问数据的 UBI CRC，
仍然不是防恶意篡改的密码学方案。

## 长期方向

release 安全链成熟后，目标架构仍是：静态 UBI → ubiblock → dm-verity →
SquashFS，并由 Secure Boot 或等价信任链保护可信 root hash。当前内核未启用
Device Mapper/DM Verity，U-Boot 也没有已确认的可信 root hash 传递闭环，故不
作为本轮启动优化的首发改动。

## 不选方案

- 纯 `skip_check`：当前没有等价运行期完整性校验。
- customer 直接改为 UBIFS：量产后更换文件系统和 OTA 契约风险较大，并削弱现有
  静态只读边界。
- 立即拆分多个 customer 卷：增加跨卷版本一致性和 OTA 原子性问题。
- UBI fastmap：只改善 attach，不能消除静态卷内容 CRC。
- 单独优化 ubiblock 创建或 SquashFS mount：两者当前耗时均远小于全卷扫描。

## 分阶段验收

1. 基线与每轮优化均至少执行 10 次冷启动，记录 monotonic P50/P95。
2. 节点包括 customer check begin/end、早期模块初始化 begin/end、customer mount、
   launcher、`RobotStartUpAction`、开机音频开始和应用可交互。
3. 第一轮只验证并行初始化，要求功能、模块顺序、失败门禁和启动完整性无回归。
4. 第二轮再做 LZO/XZ/ZSTD 独立 A/B，任何解压退化均按节点数据回退。
5. 按需 LEB CRC 若进入实施，必须注入访问中 LEB和未访问 LEB损坏，验证前台
   拒绝、后台发现、恢复和回滚。

## 当前决策候选

1. 当前量产 release 保留静态 UBI 首次打开全卷 CRC。
2. 近期先落地 `/config` 早期硬件/模块初始化与 customer CRC 扫描并行。
3. 压缩算法作为下一轮独立实验，不与并行改造同批交付。
4. 若目标仍不满足，再评审按需 LEB CRC；纯 `skip_check` 不进入当前量产方案。
5. dm-verity 归入 release 安全长期架构，不以未受信任 root hash 冒充防篡改闭环。

上述内容为 reviewing 候选，等待 owner 复核和板端证据；不授权自动修改量产镜像、
不提升 active、不写 memory。

## Archive evidence

- Source: 2026-08-03 至 2026-08-04 当前排障会话的脱敏时序、源码审查和压缩对照。
- Topic: pcr02-customer-ubi-startup-optimization-review。
- Captured at: 2026-08-04 Asia/Hong_Kong。
- Sanitization: 未保存原始串口日志、设备标识、凭证、二进制或内部端点。
- Provenance: Linux 5.10 UBI/ubiblock 路径、PCR02 rootfs/customer/OTA 构建脚本、
  两次启动测量和临时主机压缩实验。
- Verification: 源码静态核对、两份启动时序交叉对比、LZO/XZ/ZSTD 体积对照；
  并行方案和按需 LEB CRC 尚未板端实施。
- Memory Candidate: no。
- Gate Result: reviewing，需 owner 与 HIL 验证。
