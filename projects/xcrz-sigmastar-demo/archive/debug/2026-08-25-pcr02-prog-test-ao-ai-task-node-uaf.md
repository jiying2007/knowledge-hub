---
related: []
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: high
affected_version: null
id: pcr02-prog-test-ao-ai-task-node-uaf-20260825
title: PCR02 prog_test AO与AI并发启动触发任务节点UAF
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-08-25-pcr02-prog-test-ao-ai-task-node-uaf.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: controlled-debug
  from: 2026-08-25 受控设备复现、交叉 GDB、源码与构建验证；原始日志、设备标识和临时制品未归档。
review_after: '2026-11-25'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; project-specific defect does not authorize rule promotion
tags:
- pcr02
- audio
- use-after-free
- gdb
- ownership
validation_refs:
- make modules/hdi_obj_all -j8
- make modules/hdi_lib_all -j8
- make app_test_app_all -j8
- controlled AO-volume-80 plus AI smoke and five-cycle HIL
evidence_strength: source-and-device-reproduction
evidence_refs:
- app_test/app_test.c
- modules/hdi/src/hdi_audio/hdi_ai.c
created_at: '2026-08-25'
updated_at: '2026-08-25'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-25'
manual_validation_pending: true
summary_zh: 记录prog_test在AO播放后启动AI时，由Trim改写字符串所有权而释放陈旧别名、误释放AO任务节点并触发pthread mutex解锁崩溃的完整证据链、修复和板级短循环结果。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 prog_test AO 与 AI 并发启动触发任务节点 UAF

## 现象与边界

在 `prog_test` 中先启动 16 kHz 单声道 WAV 播放、设置音量 80，再启动 AI 采集，会稳定触发 SIGSEGV；AI 单独启动并持续运行正常。故障仅在测试命令路径复现，不足以证明 AISpeech、REF 延迟或音量参数本身存在缺陷。

本记录不包含设备端点、Wi-Fi 凭证、原始日志、core、二进制或客户音频。

## 根因证据链

受控 GDB 复现确认：

1. 崩溃发生在 pthread mutex unlock 内部，非法 mutex 基址接近空指针，fault address 为 `0x1c`。
2. 直接调用者为 `VSHDIOS_MutexUnlock`，上层为 OS 任务 `_TaskMain`。
3. 崩溃线程对应先前创建的 AO 任务；其任务节点内存随后被复用为 AI frame 对象。
4. 对内存释放函数设置条件断点后，确认 stdin 命令线程在 AO 启动返回后释放了该任务节点地址。
5. 源码中 `pcFileNameBuffer` 与 `pcFileName` 初始指向同一块内存；`VSAPISTRING_Trim(&pcFileName)` 会替换字符串并释放原内存，但旧别名 `pcFileNameBuffer` 未同步。
6. `_AoTestStart` 从相同定长内存池复用了旧地址创建 AO 任务节点；随后释放旧别名等价于释放仍在运行的任务节点。
7. AI 启动再次复用该块内存，令 UAF 从潜伏状态变成确定性 mutex 解锁崩溃。

结论：根因是测试命令字符串所有权错误造成的 AO 任务节点 use-after-free。AI 创建 frame 只是改变内存复用时序并暴露故障。

## 修复

- AO 文件名解析只保留一个权威指针；Trim 后只释放经 API 更新的当前指针，彻底移除陈旧别名。
- AI 测试启动路径检查初始化和 reader 创建返回值；reader 创建失败时执行反初始化。
- HDI AI reader 创建入口增加已初始化状态门禁，避免在初始化失败后继续分配 mutex、frame 和任务资源。

这些修改不引入旧接口兼容层，也不改变产品安装制品；修复版仅作为临时候选在设备 `/tmp` 运行。

## 验证

- HDI 对象构建、HDI 库构建和 `app_test` 应用构建通过。
- 父仓与 HDI 子仓空白检查通过。
- 单次 AO 播放、音量 80、AI 采集并发约 20 秒通过，AI/AO 停止及程序退出正常。
- 同一进程内连续 5 次执行 AO start、volume 80、AI start、AI stop、AO stop，全部通过。
- 验证结束后无遗留 `prog_test`/`gdbserver` 进程，无新增 page fault、SIGSEGV、core 或 fatal kernel 标记。
- 临时修复版和临时 gdbserver 均已删除，设备安装版未覆盖。

## 剩余风险与后续验证

- 当前证据覆盖确定性复现和 5 次短循环，尚未覆盖 1000 次循环、长时间 soak、内存压力及全量产品业务并发。
- `app_test` 当前在父仓中属于未跟踪目录，交付前必须确认其实际纳管仓和制品来源，避免只生成本地 app 而未进入 image/OTA。
- 本次只修复已证实的所有权缺陷；HDI 与 AISpeech 的其他既有改动应按各自范围独立评审。

```yaml
manual_validation_pending: true
manual_validation_reason: 已通过板级短循环，仍缺长循环、soak和正式安装制品验证
required_followup: 在冻结候选上执行至少1000次启停循环和长时间AO/AI并发soak
owner: leiwenjun
review_after: 2026-11-25
```

## 归档门禁

- Source：2026-08-25 受控设备复现、交叉 GDB、源码与构建结果。
- Topic：`pcr02-prog-test-ao-ai-task-node-uaf`。
- Sanitization：通过；不含端点、凭证、raw log、core、binary 或客户音频。
- Provenance：匹配 BuildID 的安装版复现与临时修复候选对照。
- Verification：源码构建通过，单次 smoke 与 5 次设备短循环通过。
- Memory Candidate：no。
- Gate Result：`reviewing / long-run-validation-pending`。
