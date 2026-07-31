---
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
target_version: null
test_environment: null
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
id: pcr02-dvr-replay-sd-hot-unplug-closure-20260715
title: PCR02 DVR回放SD热拔插闭环验证
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-15-dvr-replay-sd-hot-unplug-closure.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: registered
  from: manual-entry:knowledge-new.sh
  source_sha256: 21383d3c228cbf679e64e8ec1ed7ec35de74b1486fd8cf8889b7599425569f30
  source_id: codex-raw-sessions
  source_path: codex-raw-sessions:019f63de-5667-7951-8b3e-0ce1e55c3142
review_after: '2026-10-15'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- dvr
- sd-card
- hot-unplug
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-15-dvr-replay-sd-hot-unplug-closure.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-15-dvr-replay-sd-hot-unplug-closure.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-29'
updated_at: '2026-07-29'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-29'
manual_validation_pending: true
summary_zh: 记录DVR回放对物理拔卡、轮询检测、卸载格式化、暂停唤醒、句柄关闭和END_ERROR上报的代码闭环与构建证据，并保留真机状态矩阵待验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 DVR回放SD热拔插闭环验证
---

# PCR02 DVR 回放 SD 热拔插闭环验证

## 验证目标

确认 2026-07-15 历史实现是否覆盖 DVR 回放期间 SD 卡消失的代码路径；不声明真机 PLAY、PAUSE、SEEK 热拔插已经通过。

## 验证对象

- `api_dvr_record`、`api_dvr_replay` 和内部 replay 状态。
- SD 物理事件、轮询检测、主动卸载/格式化前停止。
- 异常结束事件和资源释放顺序。

## 历史命令证据

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk git diff --check`（历史会话） | 0 | 无空白错误。 | `codex-raw-sessions:019f63de-5667-7951-8b3e-0ce1e55c3142` | Project | DVR source |
| `rtk git -C modules/api clang-format --diff`（历史会话） | 0 | 目标文件格式检查无变化。 | 同一 provenance | Project | API module |
| 强制 API/应用构建（历史会话） | 0 | 代码与链接门禁通过。 | 同一 provenance | Project | local ELF |
| 真机热拔插矩阵 | not-run | 本轮和历史会话均未形成完整设备证据。 | none | Device | blocker |

历史命令没有在本轮源项目复跑，不能替代当前 commit 的构建证明。

## 结果矩阵

| case | 期望 | 当前证据 | 状态 |
| --- | --- | --- | --- |
| PLAY 时物理拔卡 | 停止回放并上报 `END_ERROR` | 代码路径已覆盖 | device pending |
| PAUSE 时物理拔卡 | 唤醒 pause semaphore 后停止 | 代码路径已覆盖 | device pending |
| SEEK 时物理拔卡 | 不继续访问失效介质 | 代码路径已覆盖 | device pending |
| 未收到热插拔事件 | 轮询检测后停止 | 代码路径已覆盖 | device pending |
| 主动卸载/格式化 | 操作前停止回放 | 代码路径已覆盖 | device pending |
| 正常 `ReplayStop` | 保持正常结束语义 | 代码审查支持 | regression pending |
| 新回放启动 | 清除上次 SD 异常 | 代码审查支持 | regression pending |

## 代码结论

- MP4 handle 在异常结束回调前关闭。
- 暂停状态能够被唤醒，避免卡在 semaphore。
- 未初始化 replay 模块时不访问无效 mutex。
- 异常与正常结束语义分离，没有修改公共 ABI。

## 结论

代码与历史构建证据为 `partial-pass`；设备行为为 `not-verified`。本条目保持 `reviewing`，不能作为量产或发布验收。

```yaml
manual_validation_pending: true
manual_validation_reason: 缺少PLAY、PAUSE、SEEK真机热拔插矩阵
required_followup: 使用匹配BuildID设备执行物理拔卡、卸载和格式化回归
owner: leiwenjun
review_after: 2026-10-15
```

## 剩余风险

- 热插拔事件与轮询同时到达可能重复结束。
- 文件系统阻塞、损坏 MP4 和高 I/O 并发尚未覆盖。
- 本文不保存 SD 内容、raw 日志或二进制。
