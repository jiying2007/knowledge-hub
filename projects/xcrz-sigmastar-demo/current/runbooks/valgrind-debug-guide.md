---
doc_type: runbook-draft
created: 2026-09-29
last_verified: 2026-09-29
validation_status: local-static-only
knowledge_target: projects/xcrz-sigmastar-demo/current/runbooks/valgrind-debug-guide.md
id: pcr02-valgrind-debug-guide-20260929
title: PCR02 Valgrind 调试指导
kind: runbook
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/current/runbooks/valgrind-debug-guide.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: project-source
  from: 3rdparty/valgrind/VALGRIND_DEBUG_GUIDE.md
  source_sha256: af98069edf548bd47d3f57f51ca40161e10bc6dc8261e42e8d5f1fc0c098594f
review_after: '2026-12-28'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- runbook
- capture
- manual-validation-pending
validation_refs:
- projects/xcrz-sigmastar-demo/current/runbooks/valgrind-debug-guide.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/current/runbooks/valgrind-debug-guide.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-29'
updated_at: '2026-10-05'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-29'
manual_validation_pending: true
summary_zh: PCR02 ARMv7 Valgrind Memcheck 与 Massif 项目级诊断流程；设备端完整安装和复现待验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 Valgrind 调试指导
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 Valgrind 调试指导

## 1. 目的与边界

本文参照 Knowledge Hub 的 PCR02 ASAN 项目指南组织章节，用于在受控环境中用 Valgrind 排查 `prog_pcr02` 或缩小后的模块复现程序。重点是 Memcheck 的非法访问、未初始化值和泄漏报告，以及 Massif 的堆增长剖析。

Valgrind 必须在启动目标程序时接管它；不能对已经运行的普通 `prog_pcr02` 补采先前的分配历史。Memcheck 的分配栈能指向调用路径，但一个线程分配、另一个线程持有或释放的情形仍需结合业务生命周期判断。`/proc/<pid>/task` 的线程 CPU 和状态不能直接给出每线程持有内存。

**当前证据等级：**源项目的静态检查记录显示存在 ARMv7 Valgrind 3.26.0 的构建产物和配置；尚未核实目标设备上的完整安装树、运行库、内存余量、正常启动与可控退出。下述设备命令是满足前置检查后的诊断示例，不表示已在设备通过。

## 2. 使用前检查

1. 固定设备固件、`/customer/bin/prog_pcr02`、相关动态库、未剥离 ELF 和符号的 BuildID 或 hash。若设备程序与本地符号不匹配，只能给出模块及偏移级线索。
2. 确认程序在普通运行方式下可复现，并记录相同的配置、工作目录、环境变量、设备节点和输入。Valgrind 下的启动条件必须可比。
3. 先用轻量 `/proc` 采样确定增长发生在 `Private_Dirty`、匿名映射、FD、线程还是其他资源，并固定重复业务动作及结束后的空闲观察点。
4. 确认设备 RAM、持久化日志空间和 watchdog/实时性窗口。此前 PCR02 样本的 `MemAvailable` 曾约为 8 MiB，不适合直接在该内存余量下运行完整应用的 Memcheck。
5. 只在受控诊断环境启动目标实例。不能在原应用仍占用 MI/媒体设备时直接再起一个实例；不要把启动阶段设备门禁失败当成业务泄漏。

## 3. 源项目 Valgrind 状态与安装验证

`3rdparty/valgrind/README_valgrind.md` 记录了 3.26.0 ARM 交叉编译方法。当前 `valgrind-3.26.0_modify/Makefile` 的配置前缀为 `/mnt/valgrind`，因此正常安装树预计包含 `/mnt/valgrind/bin/valgrind` 和 `/mnt/valgrind/lib/valgrind/`。实际路径必须以目标设备为准。

本地已见以下 ARM ELF：

- `valgrind-3.26.0_modify/coregrind/valgrind`：内部 core，**不能当作安装后的启动命令**。
- `valgrind-3.26.0_modify/memcheck/memcheck-arm-linux`。
- `valgrind-3.26.0_modify/memcheck/vgpreload_memcheck-arm-linux.so`。
- `valgrind-3.26.0_modify/massif/massif-arm-linux`。

设备端只读预检示例：

```sh
ls -l /mnt/valgrind/bin/valgrind /mnt/valgrind/lib/valgrind/memcheck-arm-linux
ls -l /mnt/valgrind/lib/valgrind/vgpreload_memcheck-arm-linux.so
ls -l /lib/ld-linux-armhf.so.3
/mnt/valgrind/bin/valgrind --version
```

如果安装树不在配置前缀，可将 `VALGRIND_LIB` 指向实际的 `lib/valgrind` 目录；仍须确认启动器、core、工具及预加载库来自同一次构建。仅有仓内的几个 ELF，不等于设备已安装可用。安装或部署前须另行核对设备文件系统空间和制品身份。

## 4. Memcheck 最小运行方式

以下命令只能在完成第 2、3 节检查、确定日志目录可写且目标程序可以独占设备后使用。保留原程序所需的工作目录、参数和环境变量；`/mnt/diag` 是示例日志目录。

```sh
VALGRIND_LIB=/mnt/valgrind/lib/valgrind \
  /mnt/valgrind/bin/valgrind \
  --tool=memcheck \
  --leak-check=full \
  --show-leak-kinds=all \
  --num-callers=30 \
  --log-file=/mnt/diag/memcheck.%p.log \
  /customer/bin/prog_pcr02
```

首轮先让缩小后的复现程序或应用走一轮动作，并**正常、可控地退出**。`--leak-check=full` 在退出时列出分配栈。`--log-file` 的 `%p` 用于区分进程；不要把日志写到内存紧张设备的 tmpfs 中。

如果问题是“内存持续增长但进程仍能访问那些块”，退出时的 `definitely lost` 可能为 0。先用 `/proc` 比较动作后低水位，再考虑 Massif 或在 Valgrind 已接管的进程中做受控的运行中泄漏检查。不要仅凭退出时的总量判定增长来源。

### 报告判读

| 类别 | 含义 | 排查动作 |
|---|---|---|
| `definitely lost` | 没有可达指针指向分配块 | 优先核查分配栈和对应释放路径 |
| `indirectly lost` | 只能从已丢失块到达 | 先找上层拥有者的直接丢失记录 |
| `possibly lost` | 只找到内部指针等不确定引用 | 核查自定义内存池、指针偏移与真实生命周期 |
| `still reachable` | 退出时仍有可达引用 | 对比正常退出与异常退出，判断缓存、全局持有或未完成清理；单凭这一项不能认定泄漏 |

`--track-origins=yes` 用于追查未初始化值的来源，会进一步增加开销；纯泄漏首轮不必开启。Valgrind 也不能自动识别驱动/媒体 SDK 的所有专有 buffer；这类资源应配合 SDK 获取/释放计数和设备侧状态检查。

## 5. Massif：分析仍可达的堆增长

当 `Private_Dirty` 或匿名内存逐轮增加，而 Memcheck 没有相应的明确丢失块时，可在缩小后的复现程序中尝试 Massif：

```sh
VALGRIND_LIB=/mnt/valgrind/lib/valgrind \
  /mnt/valgrind/bin/valgrind \
  --tool=massif \
  --time-unit=ms \
  --massif-out-file=/mnt/diag/massif.%p.out \
  /path/to/reproducer
```

Massif 用分配调用栈展示堆随时间的变化，适合区分某类持有对象逐轮增长和首轮预热后的平台期；它不能直接证明该内存永远不会释放，也不能覆盖所有 DMA、内核和设备侧分配。报告应与相同动作的 `/proc` 采样时间线对齐。只有确认资源余量足够后，才考虑扩大到完整应用。

## 6. PCR02 已知干扰与最小复验

Knowledge Hub 的 2026-08-12 PCR02 记录描述过：Valgrind 未识别 OpenSSL ARMv7 计数器探测指令，随后应用继续运行，最终在 MI SYS 设备号检查阶段断言退出。该次 Memcheck 的 `definitely lost` 和 `indirectly lost` 均为 0，但退出属于启动阶段异常，不能据此判断业务运行期是否泄漏。

遇到类似现象时按顺序分层：

1. 判断 Valgrind 的指令提示之后应用是否继续；不要把第一条提示自动当成最终退出点。
2. 对比普通启动和 Valgrind 启动的设备节点、sysfs major/minor、工作目录与运行环境，记录真正失败的 syscall/errno。
3. 只有初始化成功、复现业务动作、正常退出后，才把 Memcheck 泄漏摘要用于业务结论。
4. `OPENSSL_armcap=0` 只能作为验证 OpenSSL 探测路径的临时诊断变量；它会改变加速路径，不是生产修复。

## 7. 符号、线程与结论证据

主机侧应分别核对设备安装 ELF、同次构建未剥离 ELF 和关键共享库的 BuildID/hash，再解释 Valgrind 栈；旧源码、旧库或不匹配符号不得直接解释当前地址。Valgrind 报告中的分配栈指向“在哪里分配”，不必然指向“哪个线程最终持有”；需要结合业务事件、线程入口和释放栈继续追踪。

一次可复核结论至少记录：设备/构建身份、复现步骤、普通运行基线、Valgrind 启动条件、首个真实错误或增长栈、退出方式、动作后低水位变化、正常退出泄漏摘要以及未覆盖的 SDK/内核资源。原始日志和二进制只保留在受控证据位置，不写入知识正文。

## 8. 与 ASAN 的分工及参考

- ASAN 更适合定位可重编代码的越界、释放后访问等首发内存错误；它需要匹配的插桩构建与运行库。PCR02 项目指南：`projects/xcrz-sigmastar-demo/current/runbooks/asan-debug-guide.md`。
- Memcheck 可在不重编目标程序的前提下检查可观察到的用户态内存操作，但有明显速度和内存开销，且必须从 Valgrind 下启动目标。
- Massif 用于观察仍可达的堆增长；`/proc` 采样用于低开销长跑与业务时间线。三者的结果不能互相替代。

参考资料：

- [Valgrind Memcheck 手册](https://valgrind.org/docs/manual/mc-manual.html)
- [Valgrind Massif 手册](https://valgrind.org/docs/manual/ms-manual.html)
- [Valgrind Core 手册](https://valgrind.org/docs/manual/manual-core.html)
- Knowledge Hub：`projects/xcrz-sigmastar-demo/archive/debug/2026-08-12-valgrind-openssl-armv7-tick-mi-device-gate.md`（`reviewing`，设备侧复验未完成）。

**治理状态：**本文件已作为项目专用 reviewing 候选登记到 Knowledge Hub，正文路径与 registry 一致；设备侧复验、内容复核和 owner review 尚未闭环。登记状态不代表 active runbook、团队通用规范或设备验证通过。
