---
aliases:
- PCR02 遗留 QIVW 回调与 APP diag provider 优化验证
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: xcrz-sigmastar-demo-pcr02-legacy-qivw-callback-optimization-validation-20260718
title: PCR02 遗留 QIVW 回调与 APP diag provider 优化验证
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-18-pcr02-legacy-qivw-callback-optimization-validation.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: local-source
  from: PCR02 local source and ARM build evidence, 2026-07-18
  source_sha256: 2226d166b85d66f79ac6a5241475f274f4db23eb564233a72e580fc8a7ce9966
review_after: '2026-10-16'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- qivw
- vad
- app-diag
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-18-pcr02-legacy-qivw-callback-optimization-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: reviewing-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-18-pcr02-legacy-qivw-callback-optimization-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-18'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: codex
ai_generated_at: '2026-07-18'
manual_validation_pending: true
summary_zh: 验证 app_main 遗留唤醒回调与 APP diag AI provider 的 40 ms QIVW/VAD 门控、资源生命周期、构建集成边界及剩余板测风险。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 遗留 QIVW 回调与 APP diag provider 优化验证

## 来源与范围

- captured_at: 2026-07-18
- source: PCR02 本地源码、ARM 交叉构建和最终 ELF 静态证据
- topic: PCR02 `app_main::_WakeupDataCallback` 与 APP diag AI provider 的 QIVW/VAD 流程收敛
- sanitization: 不包含客户音频、密钥、原始运行日志、二进制正文或其他 dirty 文件内容
- memory_candidate: no

本条补充 `xcrz-sigmastar-demo-pcr02-qivw-vad-short-term-implementation-validation-20260718`：主 `modules/ai/wakeup_test` 路径完成 40 ms/VAD 门控后，两个遗留测试入口仍保留 5 帧聚包和 VAD 投票。本轮将两处语义对齐，但不改变 APP diag 的命令注册、发现或分发路径。

## 实现结论

### 共同行为

- PCM reader 每帧使用 `AUDIO_FRAME_SIZE` 有界缓冲；删除 `app_main` 中把约 8 MiB 当作 12.8 KiB 目标缓冲剩余空间的越界风险。
- 删除 5 帧聚包、5 点 VAD 投票和 `u32NoVadCount`；输入按最多 1280 bytes 写入 QIVW。
- 轮询周期从 10 ms 调整为 `1000 / AUDIO_FRAME_PCM_FPS = 40 ms`，与 25 fps PCM 帧率一致，理论定时唤醒次数降为原来的 1/4。
- 默认 `WAKEUP_VAD_GATE_MODE=on`：`IDLE/ACTIVE/TAIL`、480 ms pre-roll、400 ms tail；`off` 与 `shadow` 保留连续喂流回退。
- VAD 状态与事件序列压入单个 32-bit `VSHDIOS_Atomic_t`，消除事件线程与 monitor 线程直接读写普通全局布尔值的数据竞争。
- 从未收到 VAD 或按 PCM 字节折算超过 200 ms 未更新时 fail-open；VAD 恢复后回到配置模式。
- QIVW 初始化由 monitor callback 移到 start 路径，任一步失败立即清理，不再在空 session/reader 上继续执行；stop 对 callback、reader、session 和 MSP login 做对称释放。
- 30 秒统计包括 input/QIVW bytes、feed ratio、idle bytes、fail-open、read miss、write error 和 FIRST/LAST。
- 新 wakeup context 的 ARM BSS 符号大小为 `0x5078 = 20600 bytes`；相对旧约 12.8 KiB 聚包结构，单入口增加约 7.7 KiB，主要用于 15 KiB pre-roll 与 5 KiB 有界 read buffer。

### 构建边界

- `modules/app/src/app_diag/provider/app_diag_ai_provider.c` 属于独立 `modules/app` Git 子仓，真实进入 `libapp`，并通过最终 `prog_pcr02` 链接；最终 ELF 保留 `_AI_WakeupDataCallback` 与 cleanup 符号。
- `app_main/app_main.c` 在父仓当前为未跟踪目录，且没有 `app_main.mk/dep.mk` 注册到顶层 `MODULES`。它完成 ARM `-Werror` 代码生成验证，但其符号不在当前 `prog_pcr02`；修改该文件本身不会改变当前 PCR02 固件。
- APP diag 命令表与 metadata 从 `_AI_ProviderCollect` 到文件末尾与 `HEAD` 完全一致；`modules/app/include/app_diag_ai_provider.h` 和 `include/app/app_diag_ai_provider.h` 一致，无公开头变更。

## Completion Claim Audit

- Claimant: 两个遗留回调的源码优化和可构建性已完成。
- Verifier: 独立执行项目 ARM 构建、直接 ARM 对象生成、APP 静态/动态库生成、最终应用链接、符号检查、旧路径负搜索、命令表对比和头文件同步检查。
- 可声明：源码和当前构建链内的 APP provider 集成通过。
- 不可声明：板上 CPU 降幅、FRR/FAH、24 小时稳定性与两个诊断入口的运行 smoke 尚未验证。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk make modules/app_obj_all -j20` 首次构建 | 2 | provider 默认日志宏被编译掉，暴露仅供日志使用的函数/临时量触发 `-Werror`；无产物放行。 | 当前 PCR02 workspace | Workflow / negative path | APP provider source |
| 修正后 `rtk make modules/app_obj_all -j20` | 0 | `app_diag_ai_provider.c` 在真实 ARM 工程 include/宏和 `-Werror` 下通过。 | `modules/app/**/*.user.arm.o` | Workflow / Build | APP objects |
| 直接调用 `build.mk` 构建未注册 `app_main` | 2 | 缺少父 Make 注入的 ARCH/include，证伪该入口可独立作为 app module 构建。 | 当前会话负结果 | Workflow / negative path | app_main build boundary |
| SigmaStar GCC 对 `app_main.c` 执行 `-fsyntax-only -Werror` | 0 | 使用真实 public include、第三方 QIVW 头和平台宏通过。 | local source | Workflow / Verification | `app_main.c` |
| SigmaStar GCC 生成 `/tmp/pcr02_app_main_wakeup_check.o` | 0 | ARM 代码生成通过；`stWakeupParam` 为 `0x5078`。 | `/tmp` 临时对象，不归档 | Workflow / Verification | app_main object |
| `rtk make -j4 modules/app_lib_all NC=1` | 0 | 更新 static/dynamic `libapp`。 | PCR02 build outputs | Workflow / Build | `libapp.a/.so` |
| `rtk make -j4 pcr02_app_all NC=1` | 0 | 最终 `prog_pcr02` 链接成功；未 install/image/OTA。 | `out/arm/app/prog_pcr02` | Workflow / Integration | final local ELF |
| `nm` 检查 provider object 与最终 ELF | 0 | provider callback 进入最终 ELF；context `0x5078`。 | local object/final ELF | Workflow / Binary Audit | `prog_pcr02` |
| `nm` 负搜索 app_main wakeup 符号 | 0 | 明确报告最终 ELF 不含 app_main 符号，符合未注册构建边界。 | final local ELF | Workflow / negative path | `prog_pcr02` |
| 旧 `abVad/u32NoVadCount/5-frame` 模式负搜索 | 1 | 两个目标文件均不再包含旧流程，exit 1 为预期无匹配。 | target source files | Workflow / Source Audit | callback sources |
| provider `git diff --check`、头文件 `cmp`、命令表 tail `diff` | 0 | whitespace、公开头同步及命令注册/metadata 均通过。 | nested APP worktree | Workflow / Contract Audit | APP provider |

## Review 与风险

- blocker: 无源码或当前 provider 构建 blocker。
- major: `VSHDIAI_RegisterEventCallback` 在 HDI 中仍为单回调槽，MSP/QIVW 登录也为进程级资源；生产 `modules/ai/wakeup_test`、`api_wakeup_test` 与 diag wakeup 不应并发启动。该限制为既有架构问题，本轮未扩大 HDI/API 契约。
- minor: 当前仓引用的 diag layer/naming/coverage 脚本与两份 standards 文档缺失；同级 `_dev/_lvgl` 有同 hash 脚本，但脚本按自身路径绑定 sibling root，未冒充当前仓原生门禁。本轮以目标 include/naming 负扫描、命令表对比和头同步补充。
- board pending: 需要分别运行 `api_wakeup_test` 和 `diag.app.ai.wakeup.start.run` 的 `off/shadow/on` smoke，并记录 FIRST/LAST、fail-open、feed ratio、CPU 和唤醒效果。

## Breaking Change 与回退

- 行为变化：两个遗留入口从约 200 ms/5 帧聚包改为 40 ms chunk 和默认 VAD gate on；start 命令现在在资源初始化失败时直接失败，不再启动空 monitor。
- 配置回退：启动前设置 `WAKEUP_VAD_GATE_MODE=shadow` 保持连续 QIVW 喂流并观察 VAD；设置 `off` 不注册本入口的 VAD callback并连续喂流。
- 源码回退：只需回退两个目标文件；没有 schema、持久数据或公开头迁移。
- 本轮未 commit、push、install、image 或 OTA；后编译 app 不会自动进入已有镜像。

## Gate Result

- source/build/integration: `pass`
- runtime/acoustic/resource: `needs-device-validation`
- archive candidate: `reviewing`
