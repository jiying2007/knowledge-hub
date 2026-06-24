# app_product_test

SigmaStar SSC305 产测应用独立仓库，目标程序为 `prog_product_test`。本仓负责 PCBA、半成品、整机老化、标定和声学专项流程的设备侧测试编排、状态上报、工位配置读取和板端辅助诊断。

## 文档索引

| 文档 | 用途 |
| --- | --- |
| `README.md` | 仓库入口、模块总览、验证边界和维护规则 |
| `docs/TECHNICAL_DESIGN.md` | 运行时架构、阶段状态机、老化/标定/MIC/diag 设计 |
| `docs/PRODUCT_TEST_INI_PRODUCTION_GUIDE.md` | 产线人员维护 `product_test.ini` 的字段规则和模板 |
| `docs/DEVELOPMENT_PLAN.md` | 当前开发状态、待验证项和后续计划 |
| `AGENTS.md` | Codex 在本独立仓内工作的约定 |
| `.codex/skills/app-product-test/SKILL.md` | 面向 Codex 的项目专用 skill |

详细设计、产线配置说明和开发计划统一放在 `docs/` 下；根目录只保留入口文档、Codex 规则和构建/源码文件。

## 仓库边界

- 这是 `app_product_test/` 下的独立 Git 仓库，外层 SDK 仓库只把它作为子目录使用。
- 构建依赖外层 SDK 的 `BUILD_TOP`、`build/app_common.mk`、`build/app_3rdparty.mk`、`build/app_sigmastar.mk` 和模块库。
- 本仓存在历史编译产物 `*.o`、`*.d` 及备份/补丁文件。除非用户明确要求，不要批量删除、格式化或覆盖这些文件。
- 当前文档按主线代码事实维护。`pt_bt.patch` 和 `pt_hw_bt.backup` 记录蓝牙扫描接入草案，但蓝牙 feature 尚未在当前 `pt_common.c` 主线中生效。

## 运行阶段

`product_test.ini:[INFO] Stage` 决定运行阶段：

| Stage | 场景 | 主要行为 |
| --- | --- | --- |
| `PCBA` | PCBA 工位 | 启动 profile 中启用的基础硬件测试，接受上位机绑定与控制 |
| `SEMI_FINISHED` | 半成品工位 | 与 PCBA 类似，允许 `WHEELS` 标定类型 |
| `AGING` | 整机老化 | 启动连续老化、录像、LCD 状态、IR-cut/电机自动节拍和复位键门禁 |
| `CALIBRATION` | 标定工位 | 执行 TOF、IMU、摄像头外参标定，完成后按配置执行收尾 |
| `ACOUSTIC` | 声学专项 | 聚焦 LCD、MIC、Speaker 和 Factory 相关测试 |

程序按 `PROFILE_<Stage>_<Station>` 读取功能开关。新增工位时必须同步新增对应 profile 段，否则会导致 feature mask 缺失或行为与工位预期不一致。

## 核心模块

| 文件 | 职责 |
| --- | --- |
| `pt_main.c` | 进程入口，初始化 HDI/API/diag/uart/wifi/audio/video 后启动 `VSPT_CommonStart` |
| `pt_common.c` / `pt_common.h` | 配置加载、阶段解析、profile feature mask、消息订阅发布、生命周期编排、复位门禁 |
| `pt_hw_aging.c` | 2 小时老化计时、状态持久化、失败锁存、LCD 三态文案、存储健康联动 |
| `pt_hw_record.c` | 手动录像启停，不承担老化计时 |
| `pt_hw_ircut.c` / `pt_hw_motor.c` | AGING 自动节拍和上位机手动控制切换 |
| `pt_hw_mic.c` | MIC 能量、近似同声道、完全同声道和快速失败判定 |
| `pt_calibration_*.c/cpp` | TOF、IMU、摄像头外参标定 |
| `pt_diag_bridge.c` | `bridge/diag/perf/run` 到本地 CPU/MEM/SD/FLASH perf provider 的桥接 |

## 配置文件

设备侧读取路径：

```text
/var/run/media/mmcblk0p1/vstrong/product_test.ini
```

本仓的 `product_test.ini` 是开发模板。产线配置规则见 `docs/PRODUCT_TEST_INI_PRODUCTION_GUIDE.md`。

老化状态文件：

```text
/var/run/media/mmcblk0p1/vstrong/aging_state.ini
```

该文件由 `pt_hw_aging.c` 维护，包含 `stage/session_id/continuous_elapsed_ms/fail_bitmap/qualified_latch` 等字段。未达标重启不拼接时长；达标后通过态可跨重启保留；通过后出现失败会清除锁存。

## 构建与验证

本仓不能脱离外层 SDK 独立完整构建。直接在本目录运行：

```bash
rtk make -f app_product_test.mk
```

通常会因缺少外层 `BUILD_TOP` 或 `/build/app_sigmastar.mk` 失败。应优先复用外层项目既有 app 构建入口，或在明确 `BUILD_TOP` 后再执行定向构建。

文档或 Codex 资产改动的最低验证：

```bash
rtk git status --short --branch
rtk git diff --check
rtk python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/app-product-test
```

代码行为改动还需要补充：

- 目标文件编译或外层 app 构建。
- 板端日志检查：`Loaded config`、AGING 状态落盘、diag perf 返回、calibration 状态。
- 对 AGING 改动，至少覆盖 2 小时连续老化、异常锁存、复位门禁和重启恢复。

## 团队协作开发

协作开发默认以模块 ownership 切分，不新增独立协作文档。协作信息沉淀在本 README、`AGENTS.md`、`docs/DEVELOPMENT_PLAN.md` 和项目 skill 中。

| 协作域 | 主文档 | 主要源码 | 验证责任 |
| --- | --- | --- | --- |
| PCBA/半成品 | `docs/PRODUCT_TEST_INI_PRODUCTION_GUIDE.md`、`docs/TECHNICAL_DESIGN.md` | `pt_common.c`、`product_test.ini` | 绑定、profile、组件控制和状态上报 |
| AGING | `docs/TECHNICAL_DESIGN.md`、`docs/DEVELOPMENT_PLAN.md` | `pt_hw_aging.c`、`pt_hw_record.c`、`pt_common.c` | 2 小时老化、状态落盘、复位门禁 |
| CALIBRATION | `docs/TECHNICAL_DESIGN.md`、`docs/PRODUCT_TEST_INI_PRODUCTION_GUIDE.md` | `pt_calibration_*`、`pt_common.c` | TOF/IMU/Camera 标定状态和收尾 |
| MIC/声学 | `docs/TECHNICAL_DESIGN.md`、`docs/PRODUCT_TEST_INI_PRODUCTION_GUIDE.md` | `pt_hw_mic.c`、`pt_hw_spk.c` | MIC 阈值、状态码、喇叭播放 |
| Codex 资产 | `AGENTS.md`、`.codex/skills/app-product-test/SKILL.md` | `.codex/skills/app-product-test/*` | skill 校验和文档一致性 |

协作规则：

- 同一轮协作中，同一源码模块和同一 Markdown 文档只保留一个主改 owner。
- `pt_common.c`、`product_test.ini`、`app_product_test.mk`、`.codex/skills/app-product-test/SKILL.md` 属于共享契约，默认串行修改。
- 并行开发前必须明确 `scope_write`、`scope_read`、`must_not_touch` 和验证命令。
- 子任务完成后还需要统一整合验证，不能只依赖子任务局部结果。

## 当前已知边界

- 蓝牙扫描能力当前只是补丁草案：`pt_bt.patch`、`pt_hw_bt.backup`。在未合入 `PT_FEATURE_BT`、`VSPT_CommonPubBt`、`VSPT_BtTest` 和 `EnableBt` profile 之前，文档不得声明主线已支持蓝牙测试项。
- LCD 完成/异常提示使用 ASCII 文案，避免依赖额外中文字体。
- `CALIBRATION` 完成后默认格式化 TF 卡并重启；调试时需确认 `PT_CALIBRATION_COMPLETE_AUTO_FORMAT_REBOOT` 的编译取值。
- 老化阶段默认隔离上位机控制类命令，状态/心跳和必要查询可以保留。
- 团队协作进入提交前，必须补齐相关模块的构建或板端验证证据；无法执行时要说明环境边界和剩余风险。
