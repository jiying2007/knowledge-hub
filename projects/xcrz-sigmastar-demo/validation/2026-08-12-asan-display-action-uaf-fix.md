---
id: pcr02-asan-display-action-uaf-fix-validation-20260812
title: PCR02 显示动作 UAF 源码修复验证
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-08-12-asan-display-action-uaf-fix.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: validation-session
  from: source diff and local ARM ASan build evidence
  source_sha256: 0a905135a99fa4dff250a287bb5d60b77f60a4794031369c6fffaf343a6ace5e
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
- validation
- display
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-08-12-asan-display-action-uaf-fix.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-08-12-asan-display-action-uaf-fix.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-12'
updated_at: '2026-08-12'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: codex-gpt-5
ai_generated_at: '2026-08-12'
manual_validation_pending: true
summary_zh: 已在 BaseExpression 中增加 update 调用期 shared_ptr 保活与 switchAction 参数快照；ASan sensor 对象、库和 pcr02 应用构建通过，设备 HIL 待执行。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 显示动作 UAF 源码修复验证
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 显示动作 UAF 源码修复验证

## 范围

- 修复对象：`modules/sensor` 独立子仓中的 `display/eye/eye_base_expression.cpp`。
- 目标缺陷：`RobotStartUpAction`/`RobotWakeUpAction` 在自身 `update()` 内传递 `nextAction_` 引用并同步切换，旧 action 被 reset 后继续读取该引用。
- 非目标：protobuf mixed-ASan container annotation、设备部署、image/OTA 生成。

## 实现

1. `BaseExpression::update()` 先复制 `currentAction_` 到局部 `shared_ptr`，再调用虚函数 `update()`，使旧 action 至少存活到本次调用返回。
2. `BaseExpression::switchAction()` 在任何比较或 reset 前复制 `actionName`，后续创建逻辑只使用稳定值，切断调用参数与旧 action 成员的别名。
3. 未改变 `exit -> reset -> create -> bind callback -> enter` 顺序，也未修改公共函数签名。

## 静态复审

- `RobotStartUpAction` 与 `RobotWakeUpAction` 是当前仅有的 `currentExpression_->switchAction(nextAction_)` 自切换点，均由 `BaseExpression::update()` 驱动。
- `BaseScene::update()` 存在相似直接解引用写法，但当前没有 BaseScene action 在自身 update 中同步切换场景的证据，因此未扩大补丁。
- Review 结果：blocker 0、major 0；设备运行回归仍是 open item。

## 验证证据

| 命令 | 结果 | 说明 |
|---|---|---|
| `rtk git diff --check -- display/eye/eye_base_expression.cpp`（sensor 子仓） | exit 0 | 补丁空白检查通过 |
| `rtk make -j8 NC=1 DEBUG=256 modules/sensor_obj_all` | exit 0 | 格式/ASan 对象编译通过 |
| `rtk make -j8 NC=1 DEBUG=256 modules/sensor_lib_all` | exit 0 | ASan `libsensor.a/.so` 链接通过 |
| `rtk make -j8 NC=1 DEBUG=256 pcr02_app_all` | exit 0 | PCR02 ASan 应用链接通过 |

- 最终本地主机 ELF：`out/arm/app/prog_pcr02`
- BuildID：`39cf7bcfd1b51c47e115e9b2ce92e3371403f743`
- MD5：`9e70e77771b585924fefaecb5361ab07`
- Size：`288624952`

## 待完成门禁

1. 未执行设备 deploy/restart；该类操作需要单独显式授权。
2. 设备上应分别验证开机默认切 `BlinkAction`、开机期间缓存下一动作、唤醒完成切换。
3. 临时运行参数可用 `ASAN_OPTIONS=detect_container_overflow=0:halt_on_error=1:abort_on_error=1` 屏蔽已知 protobuf 假阳性并停在首个真实错误；protobuf 插桩闭包修复后须恢复 container 检测。
4. 按单次、5～10 次短循环再逐级扩大；出现 UAF、core、致命 dmesg 或状态泄漏即停止。
5. 后编译 app 不会自动进入既有 image/OTA；若发布需要重新生成对应制品并逐级核对身份。

## Provenance

- Captured: 2026-08-12
- Source: 当前会话 ASan 根因分析、sensor 子仓源码 diff、本地 ARM ASan 构建产物。
- Related debug record: `projects/xcrz-sigmastar-demo/archive/debug/2026-08-12-asan-display-action-nextaction-uaf.md`。
- Status: 源码修复和本地构建已完成；设备动态闭环 pending。
