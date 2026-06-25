---
name: sigmastar-media-pipeline-triage
description: 排查 SigmaStar Sensor/VIF/ISP/SCL/VENC/IPU/AI 媒体链路黑屏、花屏、掉帧、延迟、buffer 阻塞和模块状态异常。
version: 1.0.0
last_updated: 2026-05-18
---

# Sigmastar Media Pipeline Triage

## 1. 触发条件

- 用户描述 SigmaStar 媒体链路黑屏、花屏、掉帧、延迟升高、VENC/AI 无输出。
- 用户需要分析 Sensor/VIF/ISP/SCL/VENC/IPU/IVE/AI 模块之间的数据流或 buffer 生命周期。

## 2. 处理范围

- 处理媒体链路结构、运行状态、日志、线程和 buffer 证据。
- 不替代 SDK 原厂文档，不直接声明硬件损坏；必须先收集证据。

## 3. 工作流

1. 读取 `docs/architecture/sigmastar-media-ai-dataflow.md` 确认链路层级。
2. 读取 `docs/runbooks/sigmastar-media-pipeline-triage-guide.md` 确认排查顺序。
3. 指导或执行 `rtk bash tools/debug/collect-media-pipeline-snapshot.sh --proc <name> --out-dir <dir>`。
4. 按 Sensor/VIF/ISP/SCL/VENC/IPU/Application/Output 分层归因。
5. 对每个结论标注证据文件、风险和下一步验证动作。

## 4. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk python3 docs/governance/check_docs_links.py --changed-only`
- 规范检查：`rtk python3 docs/governance/check_agent_skill_consistency.py`

## 5. 输出要求

- 输出链路拓扑、异常层级、关键证据、排除项和下一步验证命令。
