---
id: aispeech-mainline-integration-review-20260921
title: AISpeech迁入新媒体主线与产品链接验证
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-mainline-integration-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: f2d07965ed3760481d99e0ee9f44ca333f00f024993f108d08833c892de7c99c
  temporary_source_retained: false
review_after: '2026-10-21'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- aispeech
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-mainline-integration-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-mainline-integration-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 保留新媒体主线迁入音频，ARM产品链接和Host回归通过，诊断入口与新制品HIL待验证
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AISpeech 音频迁入新媒体主线验证记录

日期：2026-09-21。范围：按用户决定，以本地 API/HDI/APP master 的新媒体实现为基线迁入音频；状态为源码迁移及产品链接已验证，设备验收待进行。

## 基线与隔离
- 父仓 3ea30b44bf26345767ef04eb9711e082174637a2。
- API 50831f6f2867dd3b47cc575284db3e54e5dbde1b；HDI 5d14ea271fd3a0780486ca9d05bc06bb7ad056d6；APP 4b2a317a2d99a680d2b78cb89d8775cbcdd21349。
- AISpeech 9ce7a7f87b4835816e68df7fade6d43ebb3d47a1 加当前音频修复。47 个已修改或新增文件逐一比较，忽略行尾格式后无遗漏或差异。
- 隔离目录 `.worktrees/aispeech-product-20260921`；父仓和四个独立模块使用同名本地分支 `codex/aispeech-product-20260921`，未提交。
- sensor aeafef238de3c7679d42f3ba93a3eebe1a665d67、wifi 086ababf7e769768e8eda8bcc2bfa9b03e19327a 使用 detached worktree 完成依赖重建，源码仍干净。
- 原工作区和原 HDI ToF 的三个脏文件保留。父仓增加 worktree 忽略及 Makefile 扫描排除，防止嵌套构建目录被发现为模块。

## 迁移结果
- 保留主线 FrameView/FrameLease、Acquire/Release/Resync、消费者和读者生命周期实现及 3 秒音频帧缓冲。
- 迁入 VOICE/CALL 配置、就绪等待、参考延迟、AO 回声路径变化通知、WAV 写出修复、类型化 VAD 回调与诊断入口。
- API 配置接口适配主线状态锁，通道转换、消费者操作、读者转换期间返回 BUSY；已运行的同配置且就绪时只做幂等确认。管线 Init/DeInit/Suspend/Resume 仍要求 owner 串行。
- APP 唤醒启动在就绪等待后调用主线 AiReaderResync，失败走资源关闭路径。
- AISpeech 包含权重显式有符号、AEC/NR/BF/AGC/NN 数值及 Reset 修复；实验性低输入 AGC、静音保持、输出 headroom 开关仍为 0。
- 增加 API 音频公共头同步和产品直接构建对 API 库的依赖；产品使用源码 AISpeech 静态库。

## 新鲜验证
- 三模块 `rtk bash tools/ai.sh check` 均 pass（文档、层次依赖和 Git 空白范围）。
- 公共头 hdi/api/app/aispeech 全量 check 通过；各修改仓 diff --check 通过。
- API tests 全套通过：9 个原有 C 测试、新增 speech_profile_test、4 个 Python 契约检查。视频测试原 Makefile 的 libyuv include 路径不匹配当前根目录布局，运行时通过 C_INCLUDE_PATH 指向 libs/3rdparty/libyuv/include，未修改主线测试逻辑。
- 新配置测试覆盖初始化前透传、锁保护、非法配置、每通道转换/消费者忙、全局读者转换、活动配置幂等、参考延迟忙状态、就绪成功/25ms超时/配置漂移/底层错误。
- AISpeech run-nn-weight-sign、run-public-abi、run-vad-status、run-reset-equivalence、run-long 通过；echo_model_probe 的 4 个测试通过。使用独立 Host 输出和库目录。
- ARM `depend_internal -j4` 与 `pcr02_app_all -j4` 均 exit 0，显式 ALKAID_PATH 指向项目 SourceCode。构建存在第三方/遗留警告，未宣称无警告。
- task/iot/bridge/ai/navigation 等当前没有源码检出的依赖仍使用父仓已有预编译库，不能宣称整套产品所有依赖均由源码重建。

## 产品制品
- 路径：隔离目录下 `out/arm/app/prog_pcr02`，ARM 32-bit EABI5、未 strip，含 debug_info。
- 大小：287435652 字节。
- BuildID：cf44665d20059281ca2312065461042ba438c3d7。
- SHA256：72424153e1f06bfa4cd3f0405f4bc89390af7cc752c95f85c561f32e441ab018。
- 源码构建 libaispeech.a SHA256：8a9f4ae36e9b581cca01657290605c930a7e7b4313f5ee95834527cf0357524f。
- 产品定义全部 13 个 HDI 使用的 SEVC_API 接口，包括 FeedPlanar/New/Reset/EchoPathChange/TailModeRequest/TailStatusGet/VadStatusGet；无未解析 SEVC 引用，无 libaispeech.so 动态依赖。
- API 库定义全部 4 个新 SpeechProfile/RefDelay 接口。

## 验证边界与下一步
- 主线产品没有初始化 VSAPPDIAG_CenterInit，新增 profile 诊断和 API 配置函数未被产品引用，链接时被裁剪。算法实际音频路径已链接，不代表远程诊断入口已启用。后续使用独立诊断宿主或明确接入产品诊断中心，再验证 VOICE/CALL、参考延迟和时延遥测。
- 本轮未部署/替换设备程序，未生成 image/OTA。新候选的设备启动、并发媒体、中文唤醒与声学验收尚未进行；旧设备结果不能冒充新制品验证。
- VAD 是 CALL NN 增益代理，不是已校准语音检测器；不能把静音代理结果当语音验收。
- 工作树保留用于审查；源码改动和生成库/程序分开管理，不自动 commit/push/merge/rebase。

## 复跑
在隔离根目录运行：
```sh
rtk bash build/sync_public_headers.sh --check hdi api app aispeech
rtk make NC=1 ALKAID_PATH="${SIGMASTAR_SDK_ROOT:?set to current SDK checkout}" depend_internal -j4
rtk make NC=1 ALKAID_PATH="${SIGMASTAR_SDK_ROOT:?set to current SDK checkout}" pcr02_app_all -j4
```

此记录为 project-specific reviewing candidate，不是产品发布批准。
