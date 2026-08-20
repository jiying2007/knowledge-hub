---
id: pcr02-asan-protobuf-container-annotation-callback-segv-20260812
title: PCR02 ASan protobuf 容器注解失配与独立回调崩溃排障记录
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-08-12-asan-protobuf-container-annotation-and-callback-segv.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: debug-session
  from: sanitized ASan evidence and repository static analysis
  source_sha256: 06fe03bf39f164521f37f562d01728993546268ae295dccf81290d5a77c0487e
  temporary_source_retained: false
review_after: '2026-09-12'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- asan
- protobuf
- armv7
- debug
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-12-asan-protobuf-container-annotation-and-callback-segv.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-12-asan-protobuf-container-annotation-and-callback-segv.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-12'
updated_at: '2026-08-12'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: codex-gpt-5
ai_generated_at: '2026-08-12'
manual_validation_pending: true
summary_zh: 确认 DeviceIdentityQuery container-overflow 高概率为 protobuf 混合 ASan 插桩造成的容器 shadow 假阳性；另一路 std::function 清理零地址崩溃需独立完整插桩复验。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 ASan protobuf 容器注解失配与独立回调崩溃排障记录

## 适用边界

- ARMv7 PCR02 ASan 构建出现两类不同 PID 的报告：主线程序列化 `DeviceIdentityQuery` 时的 `container-overflow`，以及 `task_poller` 线程清理电机回调副本时的零地址 `SEGV`。
- 本记录只保存脱敏后的调用链、指令语义、构建边界和复验门禁，不保存 raw log、设备端点、客户资料或二进制附件。
- 设备实际 ELF 的 BuildID/MD5 未随日志提供；当前主机 ELF 的地址与第二份报告精确对应，但仍需设备制品身份最终确认。

## 结论

### `DeviceIdentityQuery` container-overflow

1. 当前证据以高置信度指向 protobuf 连续容器 ASan 注解在混合插桩翻译单元之间失配，属于诊断器假阳性，不是 `DeviceIdentityQuery.field` 的真实越界读取。
2. `IotManager::publishDeviceIdentityQuery()` 位于未插桩的预编译 `libiot.a`，函数在当前栈上构造局部消息，只添加一个枚举值 `2`，随即调用 `SerializeAsString()`。该消息在序列化前不存在跨线程共享窗口，因此“并发修改 repeated field”被下调。
3. 第一次 `add_field()` 走扩容路径。最终 ELF 选择的 `RepeatedField<int>::Grow()` 是 ASan 版本：扩容后调用 `RepeatedField<int>::AnnotateSize()`，后者跳转到 `__sanitizer_annotate_contiguous_container`，把新缓冲区的 `[size, capacity)` 标为不可访问。
4. 返回未插桩的 `IotManager` 后，内联 Add 直接更新逻辑 size 并写入值 `2`，没有正常 ASan 版本 Add 在写入前执行的 `AnnotateSize(old_size, new_size)`。因此第一个逻辑有效元素的 shadow 仍保持 container poison。
5. ASan 版生成代码随后在 `DeviceIdentityQuery::_InternalSerialize()` 读取第一个元素。当前主机 ELF 中检查指令位于 `0x5ed39c`，实际读在 `0x5ed3a0`；报告 PC `0x5ed3a1` 是同一 Thumb 指令。检查命中残留 container poison，形成完整的假阳性链。
6. 生成代码标记为 protobuf C++ 5.29.3，设备栈显示 `libprotobuf-lite.so.29.3.0`，版本主线一致；当前没有生成代码/运行库版本错配证据。

### `std::function` 清理阶段零地址 SEGV

1. 另一 PID 的首个故障指令位于电机回调对应 `_M_manager` 的 operation=3（销毁）分支，不是回调复制或调用分支。调用点是 `Subscribe::onSensorMotorData()` 从 `ParseDataToCallback()` 返回后销毁栈上回调副本。
2. 与该日志地址匹配的反汇编中，调用者应把栈上副本地址保存在 callee-saved `r5`，再执行 `mov r0,r5` 进入 `_M_manager`；实际零地址读说明保存寄存器/栈状态被破坏，或者分析 ELF 与设备 ELF 不同。合法空 `std::function` 不会以这种方式访问地址 0。
3. `libtask.a` 的相关对象同样未被 ASan 插桩，首次非法写可能发生在未插桩调用链内，只在稍后的清理点表现为 CPU fault。
4. 两份报告来自不同 PID。protobuf container poison 只改变 ASan shadow，不修改业务字节，不能作为回调寄存器损坏的直接原因；两者必须分别复验。混合插桩本身则共同降低了当前 ASan 构建定位首次故障的能力。

## 假设矩阵

| 现象/假设 | 排序 | 支持证据 | 缺口 |
|---|---:|---|---|
| protobuf 报告由 mixed ASan container annotation 造成 | 高 | 插桩 Grow/AnnotateSize、未插桩内联 Add、插桩 serializer 的指令链完整；消息为局部对象 | 缺设备 ELF 身份及完整 shadow/allocation 段 |
| repeated field 被并发修改或真实越界 | 低 | 报告类型表面上是 container-overflow | 构造、add、serialize 均在同一局部函数和线程内；读的是逻辑第一个元素 |
| protobuf 生成代码与运行库 ABI 失配 | 低 | 动态/静态混合通常需检查 | 生成代码和运行库均为 5.29.3 系列 |
| 回调 SEGV 源于未插桩链中的越界写/ABI 破坏 | 高 | 销毁入口收到不可能的零存储地址；`libtask` 未插桩 | 尚无 core 寄存器和首次非法写证据 |
| 回调对象正常为空或正常单次退出竞态 | 低 | handler 有生命周期约束 | 空函数有安全分支；正常 deinit 会等待 Poller future 后再清理 |

## 最小确认实验

1. 冻结设备实际 ELF，记录 size、MD5、BuildID；不要用后续重建的同名主机文件替代。当前用于静态核验的主机 ELF BuildID 为 `3934e201048bc40ad664c25554b9ea93732667f1`。
2. 只重编 `libiot.a` 及其 protobuf 头文件使用者，确保与生成代码相同的 `-fsanitize=address -fno-omit-frame-pointer` 和容器注解设置，然后单次触发 `publishDeviceIdentityQuery()`。若该报告消失，注解失配即完成动态确认。
3. 快速诊断对照可临时设置 `ASAN_OPTIONS=detect_container_overflow=0`；它只用于证明报告依赖 container shadow，不能作为修复，也会降低此类错误的检测覆盖。
4. 获取完整报告并确认 shadow 字节为 container poison，分配栈落在 `RepeatedField<int>::Grow`。复验时建议停止 recover，保留首次错误，避免后续症状干扰。
5. protobuf 假阳性清除后，若电机回调 SEGV 仍出现，需对 `libtask` 与直接依赖做完整插桩，并在 `ParseDataToCallback()` 前后记录 `sp/r5/r0/r2`；若 `r5` 从栈地址变为 0，可直接证明被调链破坏 callee-saved 状态。

## 修复边界

- 最小修复是用同一 ASan/容器注解配置重编 `libiot.a`；稳妥边界是重编进程内所有包含 protobuf 头并操作 `RepeatedField` 的 C++ 模块，避免弱符号和内联模板继续跨越插桩边界。
- 当前仓内未发现 `IotManager::publishDeviceIdentityQuery()` 源码，只存在预编译归档，因此本会话不能从源码生成可信的 ASan 版 `libiot.a`。
- 不应修改 generated `iot_info.pb.cpp` 的序列化循环，也不应把禁用 `detect_container_overflow` 当成产品修复。
- 回调 SEGV 仍为 `needs-fix`；在首次非法写或 ABI 破坏被定位前，不把给 `std::function` 加锁、判空或改析构顺序视为已证实修复。

## 已排除或下调

- OpenSSL `_armv7_tick` 的 Valgrind 未支持指令与这两份 ASan 路径无关。
- MI SYS 设备号门禁属于此前启动阶段问题；当前两条路径均已进入应用业务逻辑。
- protobuf 容器假阳性不会修改业务内存，不能解释另一 PID 的零地址 CPU fault。

## Provenance

- Captured: 2026-08-12
- Source: 当前会话提供的脱敏 ASan 摘要；仓内 protobuf 生成代码；预编译 `libiot.a`、`libtask.a` 与当前主机 ARM ELF 的只读符号和反汇编；既有 Valgrind/MI 门禁 reviewing 记录。
- Verification: 静态指令链已闭合；设备 BuildID、完整 shadow/allocation 栈、统一插桩动态复验待执行。
