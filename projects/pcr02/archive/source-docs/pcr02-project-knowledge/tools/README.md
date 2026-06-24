# Tools 总入口

## 目录说明

1. `tools/debug/`
- 崩溃排查、离线调试、媒体链路、AI Vision、资源泄漏和二进制依赖审计脚本。

2. `tools/.codex/skills/`
- 跨模块复用的调试、发布、制品审计与问题归一化技能定义。
- Crash：`offline-gdb-core-debug`、`asan-crash-triage`、`sigbus-memory-triage`、`crash-report-normalizer`。
- Runtime：`embedded-performance-triage`、`resource-leak-triage`、`sigmastar-media-pipeline-triage`。
- AI/Media：`yolo-ai-vision-triage`、`sigmastar-media-pipeline-triage`。
- Release：`embedded-build-release-check`、`sdk-upgrade-risk-review`、`artifact-provenance-audit`。
- Intake：`field-issue-intake-normalizer`。
- Audio asset：`voice-audio-normalizer`。

## 推荐使用顺序

1. 先看 `tools/debug/README.md`。
2. 现场问题先用 `field-issue-intake-normalizer` 归一化。
3. Crash 问题按 core/ASAN/SIGBUS 分流。
4. 媒体与 AI 问题先采集运行快照，再按链路分层归因。
5. 发布与制品问题先生成 manifest，再审计依赖和来源。

## Runbook 入口

- `docs/runbooks/core-dump-capture-guide.md`
- `docs/runbooks/offline-gdb-core-fastpass-guide.md`
- `docs/runbooks/asan-offline-symbolize-guide.md`
- `docs/runbooks/core-binary-match-verification-guide.md`
- `docs/runbooks/crash-bundle-collection-guide.md`
- `docs/runbooks/sigbus-alignment-check-guide.md`
- `docs/runbooks/thread-crash-correlation-guide.md`
- `docs/runbooks/embedded-linux-performance-triage-guide.md`
- `docs/runbooks/device-resource-leak-triage-guide.md`
- `docs/runbooks/sigmastar-media-pipeline-triage-guide.md`
- `docs/runbooks/yolo-ai-vision-deployment-guide.md`
- `docs/runbooks/embedded-build-reproducibility-guide.md`
- `docs/runbooks/sigmastar-sdk-upgrade-playbook.md`
