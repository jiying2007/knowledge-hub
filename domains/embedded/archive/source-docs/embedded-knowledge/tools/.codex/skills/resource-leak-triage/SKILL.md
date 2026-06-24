---
name: resource-leak-triage
description: 排查嵌入式设备 FD、线程、内存、SDK buffer、日志和媒体资源泄漏导致的长跑卡死、OOM、无输出和性能下降。
version: 1.0.0
last_updated: 2026-05-18
---

# Resource Leak Triage

## 1. 触发条件

- 用户描述长跑后卡死、内存上涨、FD 耗尽、线程数上涨、媒体 get/put 阻塞。
- 用户需要分析资源趋势而不是单次 crash。

## 2. 处理范围

- 处理 `/proc`、dmesg、线程、fd、内存、buffer 和日志增长证据。
- 不在无趋势数据时声明泄漏已定位。

## 3. 工作流

1. 读取 `docs/runbooks/device-resource-leak-triage-guide.md`。
2. 采集 `rtk bash tools/debug/collect-runtime-baseline.sh --proc <name> --duration <sec> --out-dir <dir>`。
3. 采集 `rtk bash tools/debug/collect-media-pipeline-snapshot.sh --proc <name> --out-dir <dir>`。
4. 按 FD、线程、内存、buffer、日志五类归因。
5. 输出趋势证据和建议的长跑验证窗口。

## 4. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk python3 docs/governance/check_docs_links.py --changed-only`
- 规范检查：`rtk python3 docs/governance/check_agent_skill_consistency.py`

## 5. 输出要求

- 输出泄漏类型、趋势证据、疑似代码路径、验证窗口和止损建议。
