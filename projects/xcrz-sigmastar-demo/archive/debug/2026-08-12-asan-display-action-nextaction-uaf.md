---
id: pcr02-asan-display-action-nextaction-uaf-20260812
title: PCR02 显示动作自切换导致 nextAction_ 悬空引用
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-08-12-asan-display-action-nextaction-uaf.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: debug-session
  from: sanitized ASan evidence, ARM DWARF layout, and repository static analysis
  source_sha256: a71b7af64d38d9bba0430d4e963cfb209bf095a59c85d2e0c482a200535c9757
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
- use-after-free
- display
- lifecycle
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-12-asan-display-action-nextaction-uaf.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-12-asan-display-action-nextaction-uaf.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-12'
updated_at: '2026-08-12'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: codex-gpt-5
ai_generated_at: '2026-08-12'
manual_validation_pending: true
summary_zh: 确认 RobotStartUpAction 在 update 内以引用传递自身 nextAction_，BaseExpression reset 旧 action 后继续读取该引用，形成同线程确定性 UAF；建议用局部
  shared_ptr 生命周期保护并复制切换参数。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 显示动作自切换导致 `nextAction_` 悬空引用

## 适用边界

- PCR02 ARMv7 ASan 构建在 `sensor_disp0` 线程完成 `RobotStartUpAction` 后报告 `heap-use-after-free`。
- 本记录只保留脱敏的地址语义、源码所有权链、修复边界与复验门禁，不保存 raw log、设备端点或二进制附件。
- 当前主机未剥离 ELF 与报告地址精确对应；设备安装 ELF 的 BuildID/MD5 仍需现场确认。

## 根因结论

这是同线程重入式动作切换造成的确定性悬空引用，不是并发竞态：

1. `BaseExpression::update()` 通过 `currentAction_->update()` 调用当前动作，但没有复制 `shared_ptr` 形成调用期间的强生命周期保护。
2. `RobotStartUpAction::update()` 完成后调用 `currentExpression_->switchAction(nextAction_)`；参数 `const std::string&` 直接引用当前动作自己的 `nextAction_` 成员。
3. `BaseExpression::switchAction()` 先调用旧动作 `exit()`，再执行 `currentAction_.reset()`。因为没有其他强引用，`RobotStartUpAction` 的 `make_shared` 控制块和对象在这里被释放。
4. 函数随后把仍指向旧对象成员的 `actionName` 传给 `RobotExpression::createAction()`。字符串比较、复制和 `find` 分别触发 `memcmp`、`memcpy`、`memchr` 对已释放存储的读取。
5. 分配、释放和读取均发生在 `sensor_disp0` 同一线程；加锁不能修复该生命周期问题。

## 地址与对象布局证据

- 被释放分配是 `std::make_shared<sensor::RobotStartUpAction>` 创建的 224 字节区域；业务对象大小为 208 字节。
- 释放栈落到 `BaseExpression::switchAction()` 的 `currentAction_.reset()`，源码位置为 `eye_base_expression.cpp:24`。
- 读取地址位于分配区域内偏移 152。DWARF 布局显示 `EyeAction::nextAction_` 位于业务对象偏移 128，`std::string` 的 SSO 字符缓冲区位于其内部；计入 `make_shared` 控制块后，报告地址正对应 `nextAction_` 的 SSO 内容。
- 读取业务栈落到 `RobotExpression::createAction()` 和 `RobotFallenAction::isRobotFallenAction()`；这与对悬空 `actionName` 逐个执行字符串比较、复制和查找一致。
- ASan shadow 为 `fd`，且报告同时给出同一对象的分配与释放栈，因此这不是容器注解假阳性。

## 去重与相关现象

- 同一地址上的 `memcmp`、`memcpy`、`memchr` 是同一次 UAF 沿字符串处理链继续执行产生的重复报告，不是三个独立缺陷。
- 同一进程里的两个 protobuf `container-overflow` 均为 16 字节 `RepeatedField<int>` 扩容后第一个元素仍带 `fc` container poison；分配栈落到 ASan 版 `Grow()`，调用点分别来自未插桩 `libiot.a` 和 `libtask.a`。它们确认混合插桩注解失配，但不会释放 `RobotStartUpAction`，与本 UAF 根因独立。
- 该进程启用了 ASan recover，因而在前一个 protobuf 假阳性后继续运行，并把同一 UAF 报告多次。

## Repair Note

- failed_scope: `RobotStartUpAction` 完成后从自身 `nextAction_` 切换动作；`RobotWakeUpAction` 存在相同调用模式。
- passing_scope_to_preserve: 现有动作 `exit -> create -> bind callback -> enter` 的语义顺序；外部场景切换接口和 protobuf 处理不在本修复范围。
- minimal_rerun: 开机动作默认切到 `BlinkAction`、开机期间缓存其他下一动作、唤醒动作完成切换，各跑单次和 5～10 次短循环。
- rollback_anchor: 当前源码基线；用于符号化的主机 ELF BuildID `3934e201048bc40ad664c25554b9ea93732667f1`。
- root_cause_status: known。
- repair_action: 在 `BaseExpression::update()` 中先复制 `currentAction_` 到局部 `shared_ptr` 再调用 `update()`，保证旧动作直到本次更新返回后才析构；同时在 `switchAction()` 入口复制 `actionName`，避免任何调用方把旧动作成员引用跨越 reset。
- semantic_verification: 用 `ASAN_OPTIONS=detect_container_overflow=0:halt_on_error=1:abort_on_error=1` 暂时消除已知 protobuf 噪声并停在首个真实错误；修复 mixed protobuf 插桩后恢复 container-overflow 检测。
- do_not_repeat: 不通过加锁、判空或只关闭 ASan 来掩盖；不要把三条字符串拦截报告当成三个补丁点。

## 建议代码形态

```cpp
void BaseExpression::update() {
    auto action = currentAction_;
    if (action) {
        action->update();
    }
}

void BaseExpression::switchAction(const std::string &actionName) {
    const std::string stableActionName = actionName;
    // 后续比较和 createAction 均使用 stableActionName。
}
```

`BaseScene::update()` 也采用直接解引用 `shared_ptr` 的形态，但当前没有动作从自身 update 中同步切换 BaseScene 的证据；本次只作为同类审查候选，不扩大修复范围。

## 最小验证门禁

1. 冻结设备安装 ELF 的 size、MD5、BuildID，并确认与符号化 ELF 一致。
2. 先用非 recover ASan 单次复现三个动作切换场景；不得再出现 `RobotStartUpAction` 区域的 `fd` 读取。
3. 执行 5～10 次短循环，再按设备 HIL 门禁逐级扩大；任一级出现 UAF、core、致命 dmesg 或状态泄漏即停止。
4. 检查动作完成回调仍只触发一次，新动作正确执行 `enter()`，旧动作 `exit()` 后不再更新。
5. 单独处理 protobuf 插桩闭包；关闭 `detect_container_overflow` 只能作为本 UAF 的临时去噪条件。

## Provenance

- Captured: 2026-08-12
- Source: 当前会话提供的脱敏 ASan 报告；仓内显示动作源码；匹配地址的 ARM ELF、DWARF 类型布局和预编译静态库符号。
- Related: `projects/xcrz-sigmastar-demo/archive/debug/2026-08-12-asan-protobuf-container-annotation-and-callback-segv.md`。
- Verification: 分配/释放/读取栈、对象成员偏移和源码调用链已静态闭合；代码修复与设备动态回归尚未执行。
