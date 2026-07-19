---
id: xcrz-sigmastar-demo-pcr02-qivw-vad-gate-explicit-parameter-validation-20260718
title: PCR02 QIVW VAD gate 显式参数化更正与验证
kind: validation
domain: projects/xcrz-sigmastar-demo
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-10-16'
review_status: manual-entry-pending-review
promotion: none
tags:
- pcr02
- qivw
- vad
- explicit-config
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: codex
ai_generated_at: '2026-07-18'
manual_validation_pending: true
summary_zh: 更正不受支持的 WAKEUP_VAD_GATE_MODE 环境变量方案，验证生产 setter、app_main 命令参数和 APP diag JSON 参数的 ARM 构建及最终链接。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
promotion_decision: none; capture does not authorize active promotion or owner decision
path: projects/xcrz-sigmastar-demo/validation/2026-07-18-pcr02-qivw-vad-gate-explicit-parameter-validation.md
aliases:
- PCR02 QIVW VAD gate 显式参数化更正与验证
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 QIVW VAD gate 显式参数化更正与验证

## 来源与适用范围

- captured_at: 2026-07-18
- source: PCR02 本地源码、SigmaStar ARM 交叉编译、静态库与最终 ELF 证据
- topic: 用显式参数和 setter 取代 `WAKEUP_VAD_GATE_MODE` 环境变量
- sanitization: 不包含音频样本、密钥、完整构建日志或其他 dirty 文件正文
- memory_candidate: no

本条更正 `xcrz-sigmastar-demo-pcr02-legacy-qivw-callback-optimization-validation-20260718` 中关于通过环境变量选择 `off/shadow/on` 的说明。目标平台不支持依赖 `getenv()` 配置唤醒流程；旧记录的声学处理、资源生命周期和构建边界结论仍有效，只有配置入口被本条取代。

## 当前配置契约

### 生产 `modules/ai/wakeup_test`

- 默认模式仍为 `WAKEUP_VAD_GATE_ON`。
- 在 `start_wakeup_test()` 前调用 `set_wakeup_vad_gate_mode(WAKEUP_VAD_GATE_OFF|SHADOW|ON)`。
- setter 对非法枚举返回 `-EINVAL`；唤醒线程或 session 已运行时返回 `-EBUSY`，不支持运行中热切换。
- 删除 start 路径内的环境变量读取；模式只来自显式 setter 或编译期初始化默认值。

### 遗留 `app_main`

- 命令改为 `api_wakeup_test start [on|shadow|off]`，省略模式时默认 `on`。
- 参数不区分大小写；非法模式或多余参数打印 usage 并拒绝启动。
- `app_main/` 仍未注册到当前顶层构建，完成的是 SigmaStar ARM 对象生成验证，不影响当前 `prog_pcr02`。

### APP diag provider

- 命令路径保持 `diag.app.ai.wakeup.start.run`。
- 可选 JSON 参数：`{"vad_gate_mode":"on|shadow|off"}`；`{}` 保持兼容并默认 `on`。
- key 存在但类型错误或值非法时返回 `invalid_vad_gate_mode` 和 supported 列表。
- 已运行时相同模式保持幂等成功；请求不同模式返回 `VS_ERROR_INVALID_STATE`，不会误报热切换成功。
- metadata schema、description 和 example 已同步更新；命令注册与 dispatcher 路径不变，公开 provider 头未修改。

## Completion Claim Audit

- Claimant: 三个 QIVW/VAD gate 入口不再依赖 `WAKEUP_VAD_GATE_MODE`/`getenv()`，并提供确定性显式配置入口。
- Verifier: 对三个源码路径执行负搜索；分别完成 APP/AI ARM `-Werror` 对象构建、静态/动态库重建、未注册 app_main 的 ARM 对象生成、最终 PCR02 应用链接和 ELF/静态库符号检查。
- 可声明：源码、ARM 构建和当前固件链接集成通过。
- 不可声明：未在设备上实际执行三种模式命令，VAD/唤醒声学指标仍需板测。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| 精确搜索 `WAKEUP_VAD_GATE_MODE|getenv(...)|configure_wakeup_vad_gate_mode` | 1 | 三个目标路径无匹配；exit 1 为预期负结果。 | PCR02 source workspace | Workflow / Source Audit | three wakeup entries |
| `rtk make modules/app_obj_all -j20` | 0 | APP provider JSON 参数解析在真实 ARM 宏、include 和 `-Werror` 下通过。 | provider ARM object | Workflow / Build | modules/app |
| `rtk make modules/ai_obj_all -j20` | 0 | 生产 wakeup setter 路径在真实 C++ ARM 构建中通过。 | wakeup ARM object | Workflow / Build | modules/ai |
| SigmaStar GCC 生成 `/tmp/pcr02_app_main_wakeup_param_check.o` | 0 | `app_main.c` 的命令参数解析和回调完成 ARM 代码生成。 | `/tmp` 临时对象，不归档 | Workflow / Verification | app_main source |
| `rtk make -j4 modules/app_lib_all modules/ai_lib_all NC=1` | 0 | 两个更新模块的静态/动态库生成通过。 | local build outputs | Workflow / Build | libapp/libai |
| 首次 `rtk make -j4 pcr02_app_all NC=1` | 2 | 链接缺少既有 dirty sensor 新增的 `notify_soc_app_ready()`；与目标代码无关，但未放行。 | local linker output | Workflow / negative path | stale libsensor |
| 对 sensor source/object/library 做 `rg`、`nm -C` 和 timestamp 对比 | 0 | source/object 含符号，12:35 的旧 `libsensor.a` 不含符号，定位为新调用方配旧静态库。 | local workspace | Workflow / Root Cause | incremental build |
| `rtk make -j4 modules/sensor_lib_all NC=1` 后 `nm -C` | 0 | 不修改 sensor 源码，仅重打包已有对象；新 `libsensor.a` 含缺失符号。 | local static library | Workflow / Repair | libsensor.a |
| 第二次 `rtk make -j4 pcr02_app_all NC=1` | 0 | 单变量修复后最终 `prog_pcr02` 链接通过。 | `out/arm/app/prog_pcr02` | Workflow / Integration | final ELF |
| provider/AI `git diff --check` 与 provider public header `cmp` | 0 | whitespace 和公开头同步通过。 | nested worktrees | Workflow / Contract Audit | source/header |
| ELF `strings`/`nm` 与 `libai.a nm -C` | 0 | provider JSON 契约进入最终 ELF；生产 setter 存在于 `libai.a`。 | local binary artifacts | Workflow / Binary Audit | prog_pcr02/libai.a |

## 兼容性、风险和回退

- breaking change: 不再支持环境变量选择模式；目标平台本就不支持该配置机制，因此这是兼容性修正。
- backward compatible: APP diag `{}` 和 `api_wakeup_test start` 仍默认 `on`；生产调用方不调用 setter 时仍默认 `on`。
- runtime restriction: 三种入口仍受 HDI 单 VAD callback 槽和进程级 MSP/QIVW 资源限制，不应并发运行。
- rollback: APP diag 或 app_main 显式传 `shadow`/`off`；生产路径在启动前调用对应 setter。无需 schema 或持久数据迁移。
- board pending: 分别执行三种模式 smoke，检查日志、FIRST/LAST、feed ratio、CPU、FRR 和 FAH。
- 本轮未 commit、push、install、image 或 OTA；未修改 sensor dirty 源码。

## Gate Result

- source/build/integration: `pass`
- runtime/acoustic/resource: `needs-device-validation`
- archive candidate: `reviewing`
