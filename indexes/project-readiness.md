# 项目成熟度工作台

本页由 `knowledge-project-readiness.sh` 确定性生成。每项目只保留一份 evidence contract；结构存在不代表 owner、源码、实机或发布证据完备。

| 项目 | evidence contract | 源码定位 |
|---|---|---|
| [PCR02 SSC305 SDK](../projects/pcr02-ssc305/README.md) | [evidence contract](../projects/pcr02-ssc305/validation/project-readiness.md) | `local-only` |
| [XCRZ SigmaStar Demo](../projects/xcrz-sigmastar-demo/README.md) | [evidence contract](../projects/xcrz-sigmastar-demo/validation/project-readiness.md) | `local-only` |
| [PCR02 API Module](../projects/pcr02-api/README.md) | [evidence contract](../projects/pcr02-api/validation/project-readiness.md) | `local-only` |
| [PCR02 App Module](../projects/pcr02-app/README.md) | [evidence contract](../projects/pcr02-app/validation/project-readiness.md) | `local-only` |
| [PCR02 HDI Module](../projects/pcr02-hdi/README.md) | [evidence contract](../projects/pcr02-hdi/validation/project-readiness.md) | `local-only` |
| [PCR02 Sensor Module](../projects/pcr02-sensor/README.md) | [evidence contract](../projects/pcr02-sensor/validation/project-readiness.md) | `local-only` |
| [PCR02 Daemon App](../projects/pcr02-daemon/README.md) | [evidence contract](../projects/pcr02-daemon/validation/project-readiness.md) | `local-only` |
| [PCR02 CLI App](../projects/pcr02-cli/README.md) | [evidence contract](../projects/pcr02-cli/validation/project-readiness.md) | `local-only` |
| [PCR02 Command Server App](../projects/pcr02-cmd-server/README.md) | [evidence contract](../projects/pcr02-cmd-server/validation/project-readiness.md) | `local-only` |
| [PCR02 Proto C App](../projects/pcr02-proto-c/README.md) | [evidence contract](../projects/pcr02-proto-c/validation/project-readiness.md) | `local-only` |
| [PCR02 Wi-Fi Module](../projects/pcr02-wifi/README.md) | [evidence contract](../projects/pcr02-wifi/validation/project-readiness.md) | `local-only` |
| [PCR02 MP4 Module](../projects/pcr02-mp4/README.md) | [evidence contract](../projects/pcr02-mp4/validation/project-readiness.md) | `local-only` |
| [PCR02 OTA App](../projects/app-ota/README.md) | [evidence contract](../projects/app-ota/validation/project-readiness.md) | `local-only` |
| [PCR02 Product Test App](../projects/app-product-test/README.md) | [evidence contract](../projects/app-product-test/validation/project-readiness.md) | `local-only` |
| [PCR02 Tool App](../projects/app-tool/README.md) | [evidence contract](../projects/app-tool/validation/project-readiness.md) | `local-only` |
| [PCR02 Main App](../projects/app-main/README.md) | [evidence contract](../projects/app-main/validation/project-readiness.md) | `local-only` |
| [MCU Firmware Group](../projects/mcu/README.md) | [evidence contract](../projects/mcu/validation/project-readiness.md) | `local-only` |
| [GD32L235 Firmware](../projects/gd32l235/README.md) | [evidence contract](../projects/gd32l235/validation/project-readiness.md) | `local-only` |
| [HC32F072 Firmware](../projects/hc32f072/README.md) | [evidence contract](../projects/hc32f072/validation/project-readiness.md) | `local-only` |
| [MM32SPIN023C Firmware](../projects/mm32spin023c/README.md) | [evidence contract](../projects/mm32spin023c/validation/project-readiness.md) | `local-only` |
| [Firmware Release Tools](../projects/firmware-release-tools/README.md) | [evidence contract](../projects/firmware-release-tools/validation/project-readiness.md) | `local-only` |
| [Firmware Toolchains](../projects/firmware-toolchains/README.md) | [evidence contract](../projects/firmware-toolchains/validation/project-readiness.md) | `local-only` |
| [Codex Local Runtime Assets](../domains/codex/README.md) | [evidence contract](../domains/codex/validation/project-readiness.md) | `local-only` |
| [LLM Agent](../projects/llm-agent/README.md) | [evidence contract](../projects/llm-agent/validation/project-readiness.md) | `local-only` |
| [Agent Dev Kit](../projects/agent-dev-kit/README.md) | [evidence contract](../projects/agent-dev-kit/validation/project-readiness.md) | `local-only` |
| [LLM Tools](../projects/llm-tools/README.md) | [evidence contract](../projects/llm-tools/validation/project-readiness.md) | `local-only` |
| [SigmaStar Flasher](../projects/sigmastar-flasher/README.md) | [evidence contract](../projects/sigmastar-flasher/validation/project-readiness.md) | `local-only` |
| [MM32SPIN Validator](../projects/mm32spin-validator/README.md) | [evidence contract](../projects/mm32spin-validator/validation/project-readiness.md) | `local-only` |
| [OTA Packager](../projects/ota-packager/README.md) | [evidence contract](../projects/ota-packager/validation/project-readiness.md) | `local-only` |
| [Knowledge Hub](../README.md) | [evidence contract](../governance/product/validation/project-readiness.md) | `local-only` |

## 判定边界

- structural coverage：30 项目均有一份 reviewing evidence contract；group 元数据不重复计入项目数。
- source discovery：运行时从未跟踪的 `local/workspaces.json` 读取；本页不固化绝对路径、HEAD 或本机映射状态。
- evidence readiness：由 product gate 按 owner、source、manual/device/platform/release evidence 独立判定。
- lifecycle：不得从目录、表格、Obsidian Base 或 Graph 自动推断 active。
