# Sigmastar 双屏动画实现分析 2026-05-14

## 摘要

本文从旧 Codex archive 迁移而来，保留 2026-05-14 对 `xcrz_sigmastar_demo/modules/sensor/display` 的只读源码分析。它是 historical code analysis，不代表当前实现事实，不进入 `current/`。

## 历史结论

当时分析认为，双屏动画实现采用“单显示线程驱动 + 双 framebuffer + 场景包装层”的结构：

1. `DisplayMain` 线程周期处理请求并驱动 `update/tick`。
2. `DisplayManager` 维护左右两个 `lv_disp`，分别 flush 到两块屏幕。
3. Eye、Network、OTA 等场景在左右屏分别创建对象，并用相同参数同步执行动画。

## 历史调用链

- 控制消息入口：`display_control.cpp`
- 请求汇总与线程驱动：`display_main_cpp.cpp`
- 场景注册与切换：`display_manager.cpp`、`display_manager_cpp.cpp`
- 动画主体：`scene_eye.cpp`、`scene_network.cpp`、`scene_ota.cpp`

## 历史风险

- `DisplayControl` 线程退出风险：`threadEntry()` 使用长期阻塞轮询，`stop()` 后可能无法自然退出。
- 显示设备初始化健壮性风险：`open` 判定和部分分配失败路径需要复核。
- OTA 状态边界语义风险：旧分析指出状态上限命名可能不一致。
- 场景切换开销风险：频繁销毁重建可能增加抖动和资源压力。
- 能力开关风险：旧分析指出部分 blink/expression 相关判断可能未完全生效。

## 证据边界

旧原文记录了当时的源码文件和行号，但本次迁移未重新打开源仓验证当前行号是否仍有效。以下内容只能作为 2026-05-14 快照：

- 双 framebuffer、LVGL display、场景同步的实现形态。
- 约 16ms 一帧、场景 `exit()->deinit()`、资源加载方式等行为观察。
- 所有源码行号和风险判断。

## 后续建议

- 如果要提升为 current runbook 或当前架构说明，必须基于当前 `xcrz-sigmastar-demo` 源仓重新核验源码和运行行为。
- 如果只做历史归档，本条可作为旧 Codex archive 的 `migrated_as` 替代路径，旧正文后续可进入删除前候选。

## 迁移边界

- Source：`domains/codex/archive/codex-archive/research-notes/20260514-102409-dual-screen-animation-analysis.md`
- Source SHA256：`26631926204833ea84e3e8705521cc0020d169c4d6a40aba6d3488d859a2c6a3`
- 迁移方式：archive-only 历史源码分析摘要，不声明当前源码事实，不保存 raw logs、binary 或源码全文。
