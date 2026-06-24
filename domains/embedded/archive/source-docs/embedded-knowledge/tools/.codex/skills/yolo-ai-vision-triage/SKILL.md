---
name: yolo-ai-vision-triage
description: YOLO / AI Vision 模型加载、预处理、后处理、帧率与误检漏检问题的分诊流程。
version: 1.0.0
last_updated: 2026-05-17
---

# YOLO AI Vision Triage Skill

## 1. 触发条件

- 用户反馈 YOLO 模型加载失败、检测不到目标、误检多、框偏移或 FPS 低。
- 需要核对模型、输入帧、预处理、后处理、媒体链路和运行期资源。
- 需要把 AI Vision 问题整理为可执行排查清单。

## 2. 处理范围

- 处理 YOLO/AI Vision 部署与运行期分诊，不替代模型训练评估。
- 优先参考 `docs/runbooks/yolo-ai-vision-deployment-guide.md`。
- 媒体输入异常时联动 `docs/runbooks/sigmastar-media-pipeline-triage-guide.md`。

## 3. 强制检查

1. 必须确认模型文件、输入尺寸、类别映射、阈值与 NMS 配置。
2. 必须确认输入帧颜色空间、stride、缩放和 letterbox 处理。
3. FPS 问题必须分段区分采集、预处理、推理、后处理和渲染耗时。
4. 误检漏检必须绑定固定样本或场景，不只凭主观描述。
5. 结构与验证流程遵循 `docs/standards/agent-skill-engineering-baseline.md`。

## 4. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk python3 docs/governance/check_docs_links.py --changed-only`
- 规范检查：`rtk python3 docs/governance/check_agent_skill_consistency.py`

## 5. 输出要求

- 输出模型与输入信息。
- 输出媒体链路状态。
- 输出分段耗时或需要补采的耗时点。
- 输出阈值/类别/NMS 风险。
- 输出下一步最小验证动作。
