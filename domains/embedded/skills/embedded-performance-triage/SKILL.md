---
name: embedded-performance-triage
description: 嵌入式 Linux CPU、load、内存、I/O、线程与 fd 异常的低噪音分诊流程。
version: 1.0.0
last_updated: 2026-05-17
---

# Embedded Performance Triage Skill

## 1. 触发条件

- 用户反馈设备卡顿、CPU 高、load 高、内存上涨、I/O wait、线程阻塞或 fd 泄漏。
- 需要把线上运行期现象整理为可复现、可验证的问题单。
- 需要从 `top/ps/dmesg/proc` 输出中快速判断下一步排查方向。

## 2. 处理范围

- 处理运行期性能分诊与证据收集，不替代专项性能优化。
- 优先使用 `tools/debug/collect-runtime-baseline.sh` 采集第一现场。
- 需要内核 I/O 异常关联时联动 `tools/debug/busybox-kernel-io-watch.sh`。

## 3. 强制检查

1. 必须先确认设备版本、进程名/PID、触发场景和采样时间。
2. 必须区分 CPU 高、load 高、I/O wait、内存上涨、fd/线程泄漏。
3. 必须保留原始采集包路径，不只输出口头结论。
4. 发现崩溃或 core 时切换到 `offline-gdb-core-debug` 或 `crash-report-normalizer`。
5. 结构与验证流程遵循 `docs/standards/agent-skill-engineering-baseline.md`。

## 4. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk python3 docs/governance/check_docs_links.py --changed-only`
- 规范检查：`rtk python3 docs/governance/check_agent_skill_consistency.py`

## 5. 输出要求

- 输出顺序：
  1. 现象分类。
  2. 已有证据。
  3. 推荐采集命令。
  4. 下一步最小验证动作。
  5. 风险与置信度。
