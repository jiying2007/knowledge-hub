---
id: audio-test-phase1-implementation-20260921
title: 音频场景采集第一阶段实现与验证
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-test-phase1-implementation.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: ephemeral-file-capture
  from: ephemeral-content-sha256:1f874d8918c68c38266ea12496a6f5c3813650bead6d7d5500d0d99a6a6895f1
  source_sha256: 1f874d8918c68c38266ea12496a6f5c3813650bead6d7d5500d0d99a6a6895f1
  temporary_source_retained: false
review_after: '2026-12-20'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- debug-record
- capture
- manual-validation-pending
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-test-phase1-implementation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-test-phase1-implementation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: false
manual_validation_pending: true
summary_zh: 全C音频采集工具与模块规范同步，主机及ARM构建通过，板端待验证
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# 音频场景采集第一阶段实现记录

- 项目：workspace://xcrz-sigmastar-demo
- 状态：reviewing；源码和交叉构建证据，不是设备放行。
- 范围：新增全C app_audio_test；HDI新增中性只读采样回调及公共头镜像。
- 用户约束：SD卡固定挂载目录；零速结束驱动、允许滑行，不要求锁止；八类近端/远端/双讲/运动组合。

## 实现

采集双麦、双通道原始参考、延迟后单通道实际参考、最终输出；帧CSV记录输入PTS、处理epoch、阶段、采样偏移和输出有效标志。
采用预分配有界内存，停止驱动和播放后保存到SD卡独立目录；校验挂载设备，保持目录fd，拒绝同名覆盖。
WAV、CSV以partial保存并持久化，最后发布session元数据。元数据含执行程序MD5及播放PCM MD5、profile、参考延迟、时长和错误。
HDI回调仅reader关闭时设置，回调数据借用期明确；reader退出失败保留内存，不伪造完成采集。
AO使用有界写入，素材支持RIFF chunk遍历。双讲提供远端先、近端先和交替窗口，人工近端实际活动待确认。
电机通过APP UART直接发送RPM，无Sensor倍率补偿；右轮方向集中反转，初始选择速度模式；零速等待TX完成但不声明MCU执行确认或物理静止。
初始及运行中检查遥测新鲜度/故障，不以非零轮速判定停车失败；零速发送失败不进入后退；退出不自动倒车、急停、锁止或清故障。

## 验证

- make -C app_audio_test/tests test：退出0，ASan/UBSan；八类选项、时间线、WAV未知chunk/截断/通道拒绝、采样复制与epoch、容量和禁止覆盖保存。
- 生命周期fake clock：正常、零速TX失败、遥测失联、取消、reader超时、部分创建失败，均通过。
- 独立Python解析测试生成的JSON/WAV，转义、采样率、通道和长度正确。
- Host CLI help、dry-run及非仓库cwd运行通过；Host stub不提供硬件操作。
- modules/hdi_lib_all与app_audio_test_app_all顺序构建通过；新C文件按目录clang-format无差异。
- HDI模块check及hdi_ai.h公开头镜像check通过；Git空白检查通过。
- 负结果：首次并行链接复用了构建中的旧HDI库，缺新符号；顺序完成HDI库后重链通过。README明确顺序。

## 制品

- out/arm/app/prog_audio_test：ARM EABI5，动态系统依赖，包含调试信息。
- BuildID：53f17f595e6252ea6084890636d80b0899c9f85d。
- SHA256：ef18e826b6f6847adfa9e06c1b1244273e9ff31f0ece6e188ced8667efbfcdf9。
- 后编译app不会更新既有image/OTA；本轮未部署、未运动、未提交。

## 边界及待办

按后续用户要求同步模块资料：AGENTS、.agents专属skill及团队要求配套文件、docs开发/架构/验证/操作/C规范、docs/ai/module.json、tools/ai.sh。
应用是集成Git树内新目录，未自动初始化独立仓；本地适配器明确报告此事实，复用团队检查函数。
clang-format与HDI/API/APP/app_test逐字一致（SHA256 e15e72d6bbb5b33da006345c6bf29db8c2ad92f2701e878a5cf7a7062f8cdc53）。
接口及类型统一VSAPPAUDIOTEST与VS基础类型，补充头防卫/C++链接保护、指针检查，bootstrap封装初始化前内存和CLI输出。
规范修正后重新通过ASan/UBSan测试、CLI非仓库cwd预演、ARM链接、skill quick_validate及doctor/check/knowledge入口。
机械规范修改曾引入比较表达式及显式void转换错误，编译检出后已定点修正；最终同版本测试和构建通过。

AO现有停止接口不能严格证明排空，事件标为stop-returned-unverified，实际发声以参考录音复核。
内存录音在进程崩溃时可能没有音频落盘；最大场景新增内存预算需板端测量。
SD卡挂载、目录fsync和renameat2 NOREPLACE支持、拔卡/满盘需要实机验证，不降级成覆盖保存。
设备方向和单位、MCU失联行为、近端/双讲有效性、实时性能与音质均未验证。
复用模式仅为本项目候选，不晋升团队标准；owner review pending。回退时仅移除本轮新目录及捕获接口/观测点，保留其他既有脏改。
