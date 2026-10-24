# Tools 总入口

本页是 Knowledge Hub 对团队工具的候选/历史导航，**不是可直接执行的当前团队工具仓工作区**。真实脚本和验证应从 `workspace://embedded-knowledge` 对应团队仓的受信 checkout 根目录运行，并验证源提交、授权和版本；本页存在脚本名称不代表实际设备验证、发布或工具执行许可。

SPI NAND 压测、设备日志采集、OTA 或固件操作属于高风险现场行为；必须有设备与数据范围授权、隔离测试介质、回滚/备份和证据预算，不能从此处复制历史示例在生产设备运行。

## 目录说明

1. `tools/debug/`
- 崩溃排查、离线调试、媒体链路、AI Vision、资源泄漏和二进制依赖审计脚本。

2. `.agents/skills/`
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

## BusyBox/NAND 最小闭环

1. 默认监控：`busybox-kernel-io-watch.sh` 使用 `--dmesg-mode snapshot`。
2. 复现场景：在监控基础上开启 `--snapshot 1` 抓取命中证据。
3. 压测复现：使用 `busybox-nand-stress-suite.sh` 并行压测与监控。
4. 详细参数与边界：`tools/debug/README.md` 与 `docs/runbooks/spi-nand-busybox-io-stress-guide.md`。

## Runbook 入口

- `docs/runbooks/core-dump-capture-guide.md`
- `docs/runbooks/offline-gdb-core-fastpass-guide.md`
- `docs/runbooks/asan-offline-symbolize-guide.md`
- `docs/runbooks/core-binary-match-verification-guide.md`
- `docs/runbooks/crash-bundle-collection-guide.md`
- `docs/runbooks/sigbus-alignment-check-guide.md`
- `docs/runbooks/thread-crash-correlation-guide.md`
- `docs/runbooks/embedded-linux-performance-triage-guide.md`
- `docs/runbooks/spi-nand-busybox-io-stress-guide.md`
- `docs/runbooks/device-resource-leak-triage-guide.md`
- `docs/runbooks/sigmastar-media-pipeline-triage-guide.md`
- `docs/runbooks/yolo-ai-vision-deployment-guide.md`
- `docs/runbooks/embedded-build-reproducibility-guide.md`
- `docs/runbooks/sigmastar-sdk-upgrade-playbook.md`
