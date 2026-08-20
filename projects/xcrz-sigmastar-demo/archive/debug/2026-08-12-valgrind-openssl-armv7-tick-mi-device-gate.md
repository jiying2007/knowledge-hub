---
id: pcr02-valgrind-openssl-armv7-tick-mi-device-gate-20260812
title: PCR02 Valgrind OpenSSL ARMv7 计数器与 MI 设备门禁排障记录
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-08-12-valgrind-openssl-armv7-tick-mi-device-gate.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: debug-session
  from: sanitized Memcheck evidence and repository static analysis
  source_sha256: c6bfed96fbb864f5f0fa25e3a17156e0aa7b81b4cd08264107da6334e33df766
review_after: '2026-09-12'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- valgrind
- openssl
- armv7
- memcheck
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-12-valgrind-openssl-armv7-tick-mi-device-gate.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-12-valgrind-openssl-armv7-tick-mi-device-gate.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-12'
updated_at: '2026-08-12'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: codex-gpt-5
ai_generated_at: '2026-08-12'
manual_validation_pending: true
summary_zh: 确认 OpenSSL ARMv7 计数器探测触发 Valgrind 未支持指令，实际退出点为 MI SYS 设备号门禁；泄漏需正常退出后复验。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 Valgrind OpenSSL ARMv7 计数器与 MI 设备门禁排障记录

## 适用边界

- ARMv7/Thumb-2 的 PCR02 应用使用 OpenSSL 1.1.1 与 Valgrind 3.26.0 Memcheck。
- 现象包含 `disInstr(thumb): unhandled instruction: 0xEC51 0x0F1E`、随后应用继续启动，以及 `_MI_WRAPPER_DEVICE_Open` 在 `sys_api.c:26` 断言退出。
- 本记录不包含原始现场日志、设备端点、客户信息或二进制附件。

## 结论

1. `0xEC51 0x0F1E` 可反汇编为 `mrrc p15, 1, r0, r1, c14`，位于 OpenSSL `_armv7_tick()`，用于读取 ARM 虚拟计数器 `CNTVCT`。这是合法的 CPU 能力探测，不是应用野跳。
2. OpenSSL `OPENSSL_cpuid_setup()` 为该探测安装临时 SIGILL handler；Valgrind 无法翻译该 Thumb 指令时抛出的 SIGILL 被 OpenSSL 捕获。应用随后继续输出启动日志，证明这次 SIGILL 不是最终退出原因。
3. 本仓 Valgrind 3.26.0 VEX ARM Thumb 解码器包含部分 CP15 `MRC` 处理，但没有匹配该 `MRRC` 计数器读指令的路径。因此该报错属于 Valgrind 指令覆盖边界。
4. 最终退出来自 `VSHDI_Init()` 下游的 MI SYS 门禁。`_MI_WRAPPER_DEVICE_Open()` 先调用 `MI_COMMON_CheckDevNum("/dev/mi_sys")`；返回负值后打印通用的 device-number-check-fail 消息并触发断言。该检查会读取设备节点 `st_rdev`，再与 `/sys/class/mi/mi_sys/dev` 或 `/sys/class/dualos-adaptor/mi_sys/dev` 中的 major/minor 比较。路径不可访问、`stat`/`fopen`/`fscanf` 失败或 major/minor 不一致都会收敛成同一条通用消息。
5. 此次 Memcheck 汇总为 `definitely lost: 0`、`indirectly lost: 0`、`possibly lost: 3660 bytes`、`still reachable: 59392858 bytes`。由于进程在启动阶段 SIGABRT，线程与全局对象未正常回收，不能据此认定业务内存泄漏；需要应用成功初始化并走可控正常退出后重测。

## 最小复验

1. 单独确认 OpenSSL 探测：临时设置 `OPENSSL_armcap=0` 后运行 Memcheck。该变量使 OpenSSL 跳过 CPU 探测；只用于诊断，会禁用 ARM 加速路径并降低密码学性能。
2. 在普通进程与 Valgrind 进程中分别只读核对 `/dev/mi_sys`、两个 sysfs 候选路径、设备节点 `stat` 的 major/minor，以及 sysfs 文件内容；必须记录具体失败的 syscall/errno，不能只依赖通用断言消息。
3. 设备门禁通过后，让应用走可控正常退出，再使用 `--track-origins=yes --show-leak-kinds=all --errors-for-leak-kinds=definite,indirect --num-callers=30 -s` 重测。
4. 必须为设备实际安装 ELF 保留同 BuildID 的未剥离 ELF或 split debug 文件。禁止用 BuildID 不匹配的本地 debug ELF 符号化地址；`--allow-mismatched-debuginfo=yes` 不可作为结论证据。

## 已证伪假设

- “应用跳到非代码地址导致 Valgrind 未识别指令”：已证伪。指令字节、OpenSSL 符号和上游汇编实现一致，且 SIGILL 后应用继续运行。
- “泄漏报告就是本次崩溃根因”：已证伪。时间线先出现 MI 设备门禁断言，泄漏摘要是在 SIGABRT 终止阶段生成，并且没有 definite/indirect leak。

## 风险与后续

- `OPENSSL_armcap=0` 是诊断绕行，不是生产修复。
- MI 设备门禁的具体失败分支尚需设备侧 syscall/errno 证据；在此之前根因只收敛到门禁阶段，不能进一步断言是路径缺失、Valgrind `stat` 兼容问题或 major/minor 漂移。
- 若长期需要 Memcheck 覆盖 OpenSSL 初始化，可评估给 VEX 增加该 Thumb `MRRC CNTVCT` 的受控模拟，或仅对诊断进程设置经验证的 `OPENSSL_armcap` 掩码。

## Provenance

- Captured: 2026-08-12
- Source: 当前会话提供的脱敏 Memcheck 输出；仓内 OpenSSL 1.1.1w 源码快照、Valgrind 3.26.0 VEX 源码、本地 ELF 反汇编和 MI wrapper 反汇编。
- Verification: 只读静态核验；设备侧最小复验待执行。
