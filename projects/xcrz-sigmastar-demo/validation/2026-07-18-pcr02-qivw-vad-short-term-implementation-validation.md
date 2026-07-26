---
aliases:
- PCR02 AISpeech VAD 与 QIVW 短期优化落地验证
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: xcrz-sigmastar-demo-pcr02-qivw-vad-short-term-implementation-validation-20260718
title: PCR02 AISpeech VAD 与 QIVW 短期优化落地验证
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-18-pcr02-qivw-vad-short-term-implementation-validation.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: ephemeral-file-capture
  from: ephemeral-content-sha256:3b0484b274dc051b023e40029ee422557b63105199e1a506fff3d095bedcbbca
  source_sha256: 3b0484b274dc051b023e40029ee422557b63105199e1a506fff3d095bedcbbca
  temporary_source_retained: false
review_after: '2026-10-16'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- aispeech
- qivw
- vad
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-18-pcr02-qivw-vad-short-term-implementation-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: reviewing-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-18-pcr02-qivw-vad-short-term-implementation-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-18'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: codex
ai_generated_at: '2026-07-18'
manual_validation_pending: true
summary_zh: AISpeech NR-derived VAD 与 QIVW 门控的实现、板端半帧伪边沿根因更正、noise-safe 修复及构建集成证据；修复后声学指标待复测。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 AISpeech VAD 与 QIVW 短期优化落地验证

## 验证范围

本次在 PCR02 的 2 MIC + 1 REF、35 mm、16 kHz 生产链路上落地两个短期改动：

1. 补全 AISpeech NR-derived VAD 的结构、API、运行时语义和可配置 profile；不增加 FFT、NN 或逐帧动态内存。
2. 将 QIVW 由 5 帧/约 200 ms 聚包改为最多 1280 bytes（40 ms）写入，并用 AISpeech VAD 实现 IDLE/ACTIVE/TAIL 门控、480 ms pre-roll、400 ms tail 和 200 ms stale fail-open。

本验证证明源码、ARM 交叉编译、模块库和最终 PCR02 ELF 的集成闭环；不证明板上 FRR、FAH、真实 CPU 降幅、端到端延迟或 24 小时稳定性达标。

## 2026-07-18 板端运行时更正

### Source 与脱敏

- Source：设备端 `prog_main` 的 QIVW/VAD 运行日志，以及同一工作区的 AISpeech、HDI、`app_main` 源码和 ARM 制品。
- Sanitization：仅保留 VAD/QIVW 计数、时序和唤醒分数；不保存原始长日志、网络配置、设备地址、客户音频或二进制正文。
- Evidence strength：半帧伪边沿根因为运行时节拍与源码调用链交叉确认；声学效果仍为修复后板测待确认。

### 被证伪的旧判断

初始候选把板端问题主要留作 profile 调参。设备日志进一步显示，30 秒内输入 `960000 bytes`，VAD `seq=3753`、`edges=751`，并稳定重复约 `79 ms speech + 1 ms silence`。16 kHz、256-sample SEVC 帧率应为 `62.5 events/s`，但实测约为 `125 events/s`，说明其中一半并非新的 SEVC 结果。

源码核对确认：HDI 每次向 `_AI_SevcProcess()` 添加 128 samples，而 SEVC 累积到 256 samples 才执行一次 `SEVC_API_FeedProcess()`；调用方却在每个 128-sample 半帧后都上报 VAD，并在每个上层音频包把局部 `u8Vad` 重置为 0。由此每包首半帧制造一次假 silence，下一半帧才恢复真实状态，完整解释了固定节拍的 `0 -> 1` 抖动。旧日志中的高 edge 数不能作为声学 VAD 边沿使用。

### 修复结论

1. HDI 增加 `bVadUpdated`：只有实际执行 256-sample SEVC 帧并获得新结果时才调用 `AI_EVENT_TYPE_VAD`，同时同步传递该帧 Q24 分数；预期 30 秒事件序列由约 3750 降至约 1875。
2. PCR02 构建默认 profile 从 `speech-safe(2)` 改为 `noise-safe(0)`；该档提高 onset 门槛、增加确认帧并缩短误触发保持，更符合当前“先降误触发”的目标。480 ms pre-roll 保留词首，降低额外 onset 延迟风险。
3. 修复 NR-only 稳定噪声自锁：没有 NN gain 辅助时，不再要求瞬时 VAD 已经很低才允许稳定频谱进入 noise adaptation。否则噪声一旦被判 speech，noise PSD 冻结，分数无法自行回落。
4. `SEVC_API_VadProbabilityGet()` 在 NR 路径返回二值门控前的 `fVadSmooth`；`app_main` 的 first/edge/30 秒 stats 输出 `prob=%(Q24)`，供板端以真实分数继续调参。

### 本次验证证据

| Command | Exit Code | Result Summary | Evidence Path | Layer |
|---|---:|---|---|---|
| `rtk rg` 负搜索旧的无条件 VAD callback | 1 | 旧 `_AI_SevcProcess(...,&u8Vad); callback(...,NULL)` 路径已不存在；exit 1 为预期无匹配。 | PCR02 workspace | Source negative path |
| `rtk make -j4 DEP=modules/aispeech modules/aispeech_lib_all NC=1` | 0 | `sevc_nr.c`、`sevc_api.c` 以 `NR_VAD_PROFILE=0` 重新生成 ARM static/dynamic AISpeech 库。 | PCR02 build outputs | Build |
| build/managed AISpeech `sha256sum` | 0 | static 两份均为 `03e84ad...dcc6`；dynamic 两份均为 `6bf342a...b7de`，应用链接目录已同步。 | local generated artifacts | Artifact audit |
| `rtk make -j4 modules/hdi_lib_all NC=1` | 0 | `hdi_ai.c` 在 `-Werror` 模块规则下生成新 ARM object/lib；object 引用 `SEVC_API_VadProbabilityGet`。 | PCR02 build outputs | Build |
| `rtk make -j4 app_main_app_all NC=1` | 0 | 生成 `prog_main`；BuildID `c321f9a69c9ba9be05edc9f01d030160037b7631`，最终 ELF 含 Q24 first/edge/stats 日志契约。 | `out/arm/app/prog_main` | Integration |
| `rtk make -j4 pcr02_app_all NC=1` | 0 | 主产品入口兼容链接通过；最终 ELF 含新 HDI error marker。 | `out/arm/app/prog_pcr02` | Compatibility |
| host `objdump` 直接反汇编 ARM `.so` | 1 | 主机 objdump 报 architecture unknown；改用 SigmaStar ARM objdump 后成功，作为工具选择负证据。 | local toolchain | Negative path |

### 修复后板测验收

- 安静 30 秒时 `seq` 应接近 1875，而不是约 3750；不得再出现固定的 `79 ms speech + 1 ms silence` 周期。
- 无人声、无播放时 edge 应稀疏，`state` 应能回到 silence；`prob` 长期高于 noise-safe 门槛则说明仍需按真实 Q24 分布调阈值或排查通道/AEC。
- `on` 模式稳定静音后 `feed` 应明显低于 100%，且 `idle bytes` 增长；若 VAD 已回 silence 但 feed 仍为 100%，再排查 gate/tail，而不是继续调 VAD。
- 必须对同一批“小窝小窝”正样本和电视、人声、提示音负样本记录 FRR、FAH、分数分布与 QIVW CPU；当前仍不允许给出量产效果结论。

## 实现事实

### AISpeech VAD

- `SEVC_NR_S` 增加 8-band 固定点 VAD 状态；交叉编译得到 `sizeof(SEVC_NR_S)=0x5c=92 bytes`，低于 1 KiB 目标。
- VAD 复用 NR 已有频谱、noise PSD 和 gain，不新增 FFT/NN；profile 支持 noise-safe、balanced、speech-safe。初始候选使用 `NR_VAD_PROFILE=2`，已由上述板端证据更正为默认 `NR_VAD_PROFILE=0`（noise-safe）。
- `sevcNnCbFunc()` 在运行时 NN 关闭时从 NR 获取 VAD，并且该路径不再依赖编译启用 NN。
- `SEVC_API_FeedProcess()` 现在独立于 AGC 返回二值 VAD；`SEVC_API_VadProbabilityGet()` 暴露最新 Q24 probability。
- 最终 `prog_pcr02` 反汇编显示 `SEVC_API_FeedProcess()` 在 `SEVC_Feed()` 后读取 `fVadStatus`，按 `>0` 返回 0/1。

### QIVW 流程

- 初始音频状态从 `FIRST` 修正为 `INIT`，实际状态序列为 `INIT -> FIRST -> CONTINUE -> LAST -> INIT`。
- 删除 5 帧、6400 bytes、约 200 ms 的聚包与 5 点 VAD 投票；实际 PCM 以不超过 1280 bytes 的 chunk 写入 QIVW。
- `WAKEUP_VAD_GATE_MODE` 支持 `off`、`shadow`、`on`，默认 `on`；运行期间禁止切换，避免流状态破坏。
- `on` 模式下：IDLE 只写入 480 ms ring；VAD onset 时从 ring 以 FIRST/CONTINUE 排空；活动期 CONTINUE；VAD off 后保留 400 ms tail 并在最后一帧发送 LAST。
- 从未收到 VAD 或 VAD 超过 200 ms 未更新时 fail-open 连续喂流，VAD 恢复后回到配置门控，避免事件链异常导致永久漏唤醒。
- 原 `deque<vector<uint8_t>>` 每帧分配替换为 16 槽固定队列。ARM 符号大小：pre-roll/gate context `0x3c14=15380 bytes`，固定队列 `0x10040=65600 bytes`；队列容量与原上限一致，新增主要是 15 KiB pre-roll。
- 30 秒统计增加 input/QIVW bytes、feed ratio、idle skip、pre-roll/tail bytes、VAD active ratio、fail-open、FIRST/LAST、queue/drop 和 gate state。

## Completion Claim Audit

- Claimant：当前实现已完成源码和构建闭环。
- Verifier：同一会话按完成前验证门禁重新执行独立语法编译、模块构建、最终链接、符号/反汇编、hash 和 diff 检查。
- 可放行声明：源码实现、ARM 编译、模块库生成、受管 AISpeech 库同步、最终 ELF 链接均通过。
- 不可放行声明：板端效果、资源降幅和量产稳定性尚无设备证据，保持 `manual_validation_pending=true`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| AISpeech 三个目标源的 ARM `gcc -fsyntax-only` | 0 | 新 NR VAD、SEVC 回调和 API 通过；仅有原有 unused warning。 | 本地 PCR02 workspace；命令可复跑 | Project / Verification | AISpeech source |
| 首次用非 PATH 的交叉 `g++` 名称编译 QIVW | 127 | 工具定位失败，证伪“短名称可直接使用”；改为受信绝对 toolchain path。 | 当前会话负结果；不归档 raw log | Project / Verification | negative path |
| QIVW 源用绝对 ARM `g++ -fsyntax-only -std=gnu++17 -Wall -Wextra -Wformat=2` | 0 | 新固定队列、门控和公开 API 通过；仅有既存 unused parameter warning。 | 本地 PCR02 workspace；命令可复跑 | Project / Verification | `wakeup_test.cpp` |
| `rtk make -j4 DEP=modules/aispeech modules/aispeech_lib_all NC=1` | 0 | 生成 static/dynamic libaispeech；新 `sevc_nr.c`、`sevc_func.c`、`sevc_api.c` 均真实编译。 | PCR02 build outputs | Project / Build | `libaispeech.a/.so` |
| `rtk make -j4 modules/ai_lib_all NC=1` | 0 | 新 QIVW 源真实编译并生成 static/dynamic libai。 | PCR02 build outputs | Project / Build | `libai.a/.so` |
| `rtk make -j4 modules/hdi_lib_all NC=1` | 0 | `hdi_ai.c` 在 `-Werror` 下重新编译通过。 | PCR02 build outputs | Project / Build | `libhdi.a/.so` |
| `rtk make -j4 pcr02_app_all NC=1` | 0 | 最终 PCR02 ELF 重新链接通过；未 install、未生成 image/OTA。 | `out/arm/app/prog_pcr02` | Project / Integration | final local ELF |
| built/deployed AISpeech `sha256sum` | 0 | static 两份均为 `79035471065c8e5798a3ce4127fecb981b86c6644cef6711523d42291809ee45`；dynamic 两份均为 `15539fe3c4825a18a57e79f83caf59bb32c2c4e78da3dd4bdb20f41abb6601f9`。 | PCR02 build + managed third-party paths | Project / Artifact | deployed AISpeech libs |
| `arm-linux-gnueabihf-objdump -d --disassemble=SEVC_API_FeedProcess out/arm/app/prog_pcr02` | 0 | 最终 ELF 中调用 `SEVC_Feed` 后读取 VAD 字段并按大于零返回 0/1。 | final local ELF | Project / Binary Audit | `prog_pcr02` |
| `rtk rg` 搜索旧 `FRAME_LEN * 10`、`5 <= audio_count`、`g_abVad`、`deque<vector>` | 1 | 旧 200 ms 聚包、投票和逐帧动态队列模式均不存在；作为预期负搜索记录。 | `modules/ai/wakeup_test/chenyf/wakeup_test.cpp` | Project / Source Audit | negative old path |
| 三个受影响仓的 `rtk git diff --check` | 0 | 目标源码和公共头文件无 whitespace error。 | local dirty worktrees | Project / Verification | source diffs |

## Breaking Change 与回退

- 行为变化：QIVW 默认从连续/200 ms 聚包变为 VAD 门控/40 ms chunk；音频转发回调的粒度随 QIVW chunk 变化。当前仓没有该转发回调的注册调用方。
- 安全开关：启动前设置 `WAKEUP_VAD_GATE_MODE=shadow` 可保留连续喂流并观察 VAD；设为 `off` 可回到连续喂流。
- 二进制回退：恢复 Git 中原 `libs/3rdparty/aispeech/lib/libaispeech.a/.so` 并重新链接 app；不需要修改设备数据格式。
- 本轮没有 commit、push、install、image 或 OTA 操作；后编译 app 不会自动进入已有 image/OTA。

## Gate Result

- 源码与构建门禁：`pass`。
- 板端功能/性能门禁：`needs-device-validation`。
- Review blocker：未发现源码或链接 blocker；板测缺口不阻止形成开发候选，但阻止发布/量产结论。
- Retry budget：单类最多 2 次；工具路径和 artifact copy 首次失败均在第 2 次修复，没有连续 2 次无新证据的卡死。
- `manual_validation_pending: true`。
- 后续必须使用同一批“小窝小窝”正/负样本，在 `off/shadow/on` 三档记录 FRR、FAH、p95、QIVW CPU、总 CPU、RSS、30 秒统计和 24 小时 drop；达标后再更新本 validation。

## 2026-07-18 NR VAD v2 源码候选

### 新增实现事实

- `sevc_nr.c` 将原 8 带等权 SNR 平均改为中频优先的固定点加权评分，并增加 active-band、persistent-band、mid-band ratio 和 frame transient 特征；复用现有 FFT、noisy power 与 noise PSD，不新增 FFT、heap 或逐帧动态内存。
- NR-only 噪声更新由“二值 VAD 确认后才冻结”改为候选语音阶段即保护：fast VAD、至少 2 个 active bands 或低阈值概率任一满足时冻结 noise PSD，避免弱语音前 1--2 帧被快速学习成噪声。
- 稳定噪声受控适配确认由原 16 帧提升为 noise-safe 64 帧（16 kHz/256 samples 下约 1.024 秒）；balanced/speech-safe 分别为 96/128 帧。进入受控适配后以 profile 的 SPP 上限更新，不再立即硬清全部 VAD 状态。
- VAD 拆为 fast AGC/NR 状态和 slow wake-gate 状态。默认 noise-safe 的 fast 高/低阈值为 16%/12%，wake 高/低阈值为 18%/12%，wake 需要至少 2 个持续频带、1 个中频活动带和 6 帧连续证据；QIVW pre-roll 负责补回确认前词首。
- `SEVC_API_VadDiagnosticsGet()` 暴露 instant/smooth/transient/mid ratio、active/persistent/mid bands、AGC/wake 状态及 noise-update 状态，供后续 HDI/app 调试接线；现有 `SEVC_API_FeedProcess()` ABI 仍返回二值状态，但 NR 路径语义调整为 slow wake gate，AGC 内部改用独立 fast state。
- ARM 反汇编显示 `sizeof(SEVC_NR_S)=132 bytes`，相对上一版 92 bytes 增加 40 bytes，仍远低于 1 KiB 预算。

### 新增验证证据

| Command | Exit Code | Result Summary | Evidence Path | Layer |
| --- | ---: | --- | --- | --- |
| `rtk make -j4 DEP=modules/aispeech modules/aispeech_lib_all NC=1` | 0 | `sevc_nr.c`、`sevc_func.c`、`sevc_api.c` 真实 ARM 编译并生成 static/dynamic module 库；新增代码无编译 warning，输出中的 warning 为既有 AISpeech 代码。 | PCR02 workspace | Module build |
| changed-range `rtk clang-format --dry-run --Werror` | 0 | 6 个受影响 C/header 文件的修改区间通过格式门禁。 | PCR02 workspace | Source format |
| ARM `nm -D -S` | 0 | dynamic module 库含 `SEVC_API_VadDiagnosticsGet`、`SEVC_NR_AgcVadGet`、`SEVC_NR_VadProbabilityGet` 等新符号。 | `libs/arm/libs/glibc/11.1.0/dynamic/libaispeech.so` | Binary audit |
| ARM `objdump` on `SEVC_NR_LocMemSizeGet` | 0 | 立即数为 `132 (0x84)`，确认 NR state 固定内存大小。 | generated module library | Memory audit |
| `rtk cmp -s` generated vs thirdparty lib | 1 | 预期负结果：新 module 库尚未同步到 app 当前链接的 `libs/3rdparty/aispeech/lib/libaispeech.so`。 | local artifacts | Integration boundary |

### 当前边界

- 源码与 module library gate：`pass`。
- app/设备运行 gate：`needs-integration-and-device-validation`。本轮未覆盖 `libs/3rdparty` 公共头/库同步、HDI diagnostics 接线、最终 app 链接、image/OTA 或板端 A/B，因此不得声明人声 FRR、键盘/咳嗽误触发、CPU 降幅已经改善。
- 生成库哈希：dynamic `9cee377785126a4bdfed2d31378939631d7fab1047ea615a81c708b8501f9e52`；static `75bdb6a2de0a7a644622fefc2f7d83c4b6a385b3a5410ee5851cf62b6f38d270`。这些是本地验证制品，不作为发布基线。

## 关联

- `projects/xcrz-sigmastar-demo/archive/reports/2026-07-18-pcr02-audio-wakeup-afe-vad-kws-ipu-evaluation.md`
- 本条只更新短期实现与构建状态，不覆盖旧归档中关于 IPU 中长期方案和板测待办的结论。
