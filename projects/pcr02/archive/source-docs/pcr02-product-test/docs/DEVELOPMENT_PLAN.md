# app_product_test 开发计划

## 1. 当前目标

- 维护 `app_product_test` 独立仓库的产测应用。
- 确保文档、`product_test.ini`、Codex agent/skill 与当前主线代码一致。
- 持续收口 AGING、CALIBRATION、MIC、diag perf 和工位配置的验证闭环。

## 2. 已完成

### 2.1 AGING 模块拆分

- [x] `pt_hw_record.c` 仅保留录像启停。
- [x] `pt_hw_aging.c` 承担 2 小时计时、SD 持久化、LCD 文案和失败锁存。
- [x] 对外接口覆盖：
  - `VSPT_AgingTimerTest`
  - `VSPT_AgingTimerCompleted`
  - `VSPT_AgingTimerReachedTarget`
  - `VSPT_AgingResetGateReady`
  - `VSPT_AgingFailSet`
  - `VSPT_AgingFailClear`
  - `VSPT_AgingFailBitmapGet`
  - `VSPT_AgingStateClear`

### 2.2 生命周期编排

- [x] `pt_common.c` 在 AGING 阶段启动 feature、录像和老化计时。
- [x] `pt_common.c` 在 stop 阶段统一关闭 feature、AGING auto API、录像和老化计时。
- [x] AGING 阶段喇叭使用循环播放。
- [x] CALIBRATION 阶段跳过通用 IMU/TOF 测试，避免与标定线程争用。

### 2.3 老化行为

- [x] IR-cut 自动模式按 `[AGING_CTRL] IrOnMs/IrOffMs` 切换。
- [x] 电机自动模式按正转、反转、休息参数运行。
- [x] AGING 下 IR 补光由 IR 仲裁保持常亮。
- [x] `PROFILE_AGING_1` 启用 LCD、录像、IR、TOF、Laser、MIC、IMU、Speaker、ADC、Battery、Factory 等测试项。
- [x] 复位键门禁：仅老化达标且无失败时允许切到 `CALIBRATION`。
- [x] 老化状态文件为 `aging_state.ini`。
- [x] `fail_bitmap` sticky，仅人工清除或流程切换清除。
- [x] 持久化失败具备计数、节流日志和恢复日志。
- [x] 存储健康联动：周期检查 TF 挂载/可写性，录像异常时尝试恢复。
- [x] LCD 三态：运行中、完成态、异常态。

### 2.4 标定与收尾

- [x] TOF、IMU、摄像头外参标定类型和状态结构已归入 `pt_calibration.h`。
- [x] `VSPT_CommonHandleCalibrationComplete` 实现 LCD 提示、TF 格式化、老化状态清理和重启。
- [x] 支持通过编译宏关闭自动格式化/重启，便于调试。

### 2.5 MIC 与 diag

- [x] MIC 判定支持能量不足、近似同声道、完全同声道、快速失败和近克隆相关阈值。
- [x] `header.sequence` 透传 MIC 细分状态码。
- [x] `pt_diag_bridge.c` 支持 CPU/MEM/SD/FLASH perf case 桥接。

### 2.6 文档与 Codex 资产

- [x] 新增 `README.md` 作为文档入口。
- [x] 更新 `docs/TECHNICAL_DESIGN.md`，按主线实现归集设计。
- [x] 更新 `docs/PRODUCT_TEST_INI_PRODUCTION_GUIDE.md`，明确产线配置规则。
- [x] 更新 `AGENTS.md`，定义本独立仓 Codex 工作方式。
- [x] 新增 `.codex/skills/app-product-test` 项目 skill。
- [x] 将团队协作规则并入 `README.md`、`AGENTS.md`、`docs/DEVELOPMENT_PLAN.md` 和项目 skill。

## 3. 当前配置状态

`PROFILE_AGING_1` 当前启用：

- [x] `EnableAdc=1`
- [x] `EnableAvRtsp=1`
- [x] `EnableBattery=1`
- [x] `EnableFactory=1`
- [x] `EnableImu=1`
- [x] `EnableIrLight=1`
- [x] `EnableIrCut=1`
- [x] `EnableIrDistance=1`
- [x] `EnableLaser=1`
- [x] `EnableLcd=1`
- [x] `EnableMic=1`
- [x] `EnableMotor=1`
- [x] `EnableShutdown=1`
- [x] `EnableSpeaker=1`
- [x] `EnableTof=1`
- [x] `EnableRecord=1`

`PROFILE_AGING_1` 当前关闭：

- [x] `EnableIrRecv=0`

## 4. 待验证

### 4.1 构建验证

- [ ] 使用外层 SDK 既有 app 构建入口完成 `prog_product_test` 编译。
- [ ] 若直接在本仓验证，需要先设置正确 `BUILD_TOP`，否则 `app_product_test.mk` 会找不到外层 build mk。
- [ ] 检查新增/修改文档和 Codex skill：
  - [x] `rtk git diff --check`
  - [x] `rtk python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/app-product-test`

### 4.2 AGING 板端验证

- [ ] 连续运行至少 2 小时。
- [ ] IR-cut 按配置节拍切换。
- [ ] 电机按配置节拍正转、反转、休息。
- [ ] 喇叭持续循环。
- [ ] MIC、IMU、TOF、IR 距离持续有数据。
- [ ] 录像文件持续落盘。
- [ ] 未达标重启：连续时长清零。
- [ ] 达标重启：保留门禁通过态。
- [ ] 通过后模拟存储失败：清除通过锁存并显示异常。
- [ ] LCD 完成态显示 `STATUS DONE` 和 `STATION <station>`。
- [ ] LCD 异常态左屏显示 `STATUS ERROR/ERR`，右屏保持电池/电机数据。
- [ ] 老化完成前按复位键不切换；完成后按复位键切换到 `CALIBRATION`。

### 4.3 CALIBRATION 板端验证

- [ ] TOF 标定参数读取正确。
- [ ] IMU 两阶段 `AT_180 -> AT_0` 状态推进正确。
- [ ] 摄像头外参标定可采集并返回状态。
- [ ] 标定完成后 LCD 提示、TF 格式化、老化状态清理、重启行为符合预期。

### 4.4 MIC 验证

- [ ] 正常双通道音频上报 `mic_valid=true`。
- [ ] 低能量触发 `LOW_ENERGY`。
- [ ] 完全相同通道达到 `MicFastFailFrames` 后触发 `CHANNEL_CLONE_FAST_FAIL`。
- [ ] 近克隆阈值组合不误杀正常左右声道差异。

### 4.5 PCBA/半成品协作验证

- [ ] PCBA：`Loaded config: Stage=PCBA` 与 `PROFILE_PCBA_<Station>` 一致。
- [ ] PCBA：上位机 bind 使用 `type=PCBA` 且 `id=Operator`。
- [ ] PCBA：WiFi、Version、ADC、Battery、IMU、IR、LCD、MIC、Motor、Speaker、TOF 等上报符合 profile。
- [ ] 半成品：`Loaded config: Stage=SEMI_FINISHED` 与 `PROFILE_SEMI_FINISHED_<Station>` 一致。
- [ ] 半成品：上位机 bind 使用 `type=SEMI_FINISHED` 且 `id=Operator`。
- [ ] 半成品：`WHEELS` 标定允许进入，其它标定类型仍需 `CALIBRATION`。
- [ ] 协作提交前补齐相关模块 owner、板端日志和构建证据。

## 5. 待开发

- [ ] 蓝牙扫描主线化：
  - 合入 `pt_bt.patch` 的 feature mask、publish topic 和 lifecycle 逻辑。
  - 将 `pt_hw_bt.backup` 正式转为 `pt_hw_bt.c`。
  - 在 `product_test.ini` 中按 profile 增加 `EnableBt`。
  - 编译并板端验证 `bridge/pcba/bt`。
- [ ] 老化蓝牙常开测试项：蓝牙主线化后再决定是否在 `PROFILE_AGING_<Station>` 启用。
- [ ] LCD 叠加“电量评估”文案：基于 Battery snapshot 做清晰的 pass/fail 或状态提示。
- [ ] 将 `docs/PRODUCT_TEST_INI_PRODUCTION_GUIDE.md` 的 PDF 生成方式纳入可重复脚本，避免 Markdown 和 PDF 漂移。
- [ ] 按模块补齐团队协作 owner 表，并写入 `docs/DEVELOPMENT_PLAN.md` 或对应专题文档，不新增独立协作文档。

## 6. 风险与边界

- 蓝牙扫描尚未合入主线，不能按已完成能力对外承诺。
- 本仓依赖外层 SDK，孤立执行 `make -f app_product_test.mk` 不能代表最终构建结果。
- AGING 的关键验收依赖真实硬件、TF 卡和 2 小时连续运行，本地静态检查只能覆盖文档/格式/skill 结构。
