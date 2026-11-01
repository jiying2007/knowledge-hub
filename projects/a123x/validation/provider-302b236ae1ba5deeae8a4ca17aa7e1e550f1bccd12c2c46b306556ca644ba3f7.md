---
id: provider-302b236ae1ba5deeae8a4ca17aa7e1e550f1bccd12c2c46b306556ca644ba3f7
title: DEVWIRE WiFi REG_ON读回诊断与候选模块验证
kind: validation
domain: projects/a123x
path: projects/a123x/validation/provider-302b236ae1ba5deeae8a4ca17aa7e1e550f1bccd12c2c46b306556ca644ba3f7.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:302b236ae1ba5deeae8a4ca17aa7e1e550f1bccd12c2c46b306556ca644ba3f7
  source_sha256: 8a51b9fae01b6f437d5289c23539da6a90510acdd12360aef89c264018c54b93
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
- projects/a123x/validation/provider-302b236ae1ba5deeae8a4ca17aa7e1e550f1bccd12c2c46b306556ca644ba3f7.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/validation/provider-302b236ae1ba5deeae8a4ca17aa7e1e550f1bccd12c2c46b306556ca644ba3f7.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-22'
updated_at: '2026-10-22'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-22'
manual_validation_pending: true
summary_zh: 用户授权按建议增加 WiFi 使能信号诊断。目标为 A123X F20 DEVWIRE、Linux 6.12.69+、AArch64；现场现象为 SDIO CMD5 超时，用户示波器观察开发板端 WIFI_EN 始终低。该现象尚不能确定硬件或软件根因。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 302b236ae1ba5deeae8a4ca17aa7e1e550f1bccd12c2c46b306556ca644ba3f7
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
aliases:
- DEVWIRE WiFi REG_ON读回诊断与候选模块验证
related:
- projects/a123x/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# DEVWIRE WiFi REG_ON 读回诊断实现与软件验证

用户授权按建议增加 WiFi 使能信号诊断。目标为 A123X F20 DEVWIRE、Linux 6.12.69+、AArch64；现场现象为 SDIO CMD5 超时，用户示波器观察开发板端 WIFI_EN 始终低。该现象尚不能确定硬件或软件根因。

本次新增受管 0007-a123x-reg-on-readback-diagnostics.patch。只在 BCMDHD_A123X 下，在 GPIO 设置前后及原有上电等待后的 SDIO 重扫入口记录 GPIO 全局编号、期望电平、设置返回值、方向与原始输入读回。使用 GPIO consumer API，不直接读写物理寄存器，不添加等待，不改变 GPIO 输出、重试或回收语义。方向 0=输出、1=输入、负值=读取失败；raw 为输入采样，不是输出锁存值或物理焊盘电压证明。before-set 的 set_rc=-EINPROGRESS 表示尚未执行设置；before-sdio-rescan 的 set_rc=0 标记前序上电成功，不是再次执行设置。

补丁清单、来源锁和项目验证入口同步，补录已有 0006 补丁在来源锁中遗漏的哈希。供应商 266 个原文件和固件四件套保持原件校验通过。没有改设备树、GPIO 控制器或共享 MMC 驱动。

软件证据：

- 当前 SDK 的 bcmdhd 包 make build 在隔离 OUT 中依次零 fuzz 应用七份补丁，使用 SDK GCC 13.2、当前内核 Module.symvers；完整 modules 构建及 modpost 返回 0，没有跳过未解析符号检查。
- ELF 检查为 AArch64；vermagic 为 6.12.69+ SMP preempt mod_unload aarch64；模块包含 REG_ON_DIAG、before-set、after-set 和 before-sdio-rescan，引用 gpio_to_desc、gpiod_get_direction、gpiod_get_raw_value_cansleep 和 sdio_reinit。
- 从非仓库 cwd 执行 Python CLI help 和 5 项定向 unittest 均返回 0。故障注入编译真实补丁函数，覆盖 GPIO/IRQ 申请和方向设置失败、OF 禁用节点、重扫、输出失败、读回失败不改变控制返回值、释放后无 GPIO 读取，以及补丁来源锁与清单一致性。
- project 和 common_drivers 的 git diff --check 返回 0；相关实现和资源路径完成源码自审，没有独立 reviewer 或设备证据。

候选模块 SHA256：f4905c6ddcbd0aa8869cf543265fa99b02c364aba879999c5e47d5df89236ca0。
补丁 SHA256：0a9a34dd29c38e37bc483eaf0c10dbef210b74c7d1bd0294eb224a8243220593。
来源锁 SHA256：9f10d2e3aaaad994c2e24b1d4f893e7b1bb30c6cb2e81bab88066e924ad31b1b。
构建使用的内核配置 SHA256：450399ae9fe9167df307826d1a571cf82469267e472ac4ee231768a564276dc3。
构建使用的 Module.symvers SHA256：31cbb3641f9a594bda5830751d2710bbc618edeb1fb1cf705bd14d3605f06dcc。

验收边界：诊断源码与候选模块的软件验证完成；未部署开发板、未重打整机镜像、未证实 WIFI_EN 拉高或 WiFi 枚举/联网成功。现有 rootfs 驱动未替换。下一步在确认候选部署身份后，对齐示波器启动窗口，比较 after-set 与 before-sdio-rescan 的 dir/raw；必要时对比空载和带载。GPIO 输入读回不能单独证明 mux、输出锁存或焊盘连接正常。

回退只涉及新增 0007、其清单/来源锁/验证引用和相关文档测试增量，不回退其他既有修改。没有 commit、push、设备写入或运行资产变更。
