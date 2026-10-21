# GD32L235 Firmware

- 项目 ID：`gd32l235`
- 所属组：`mcu`
- 事实边界：以 `registry/repositories.json` 中 `repo_id=gd32l235` 的 Git remote key 为准。
- 当前知识：`projects/gd32l235/current/`
- 当前低功耗协同契约候选：[GD32L235 与 PCR02 SoC 低功耗协同当前契约候选](current/soc-low-power-contract.md)（`reviewing`，不替代源码）
- 决策：`projects/gd32l235/decisions/`
- 验证：`projects/gd32l235/validation/`
- 归档：`projects/gd32l235/archive/`

## 文件命名约定

- `current/` 使用稳定语义名称，不添加日期，例如 `soc-low-power-contract.md`。
- `archive/` 下的长期 Markdown 使用 `archive/<分类>/YYYY-MM-DD-<ascii-kebab-topic>.md`，日期表示事件、决策、会话或捕获日期。
- registry `id` 可继续使用紧凑的 `YYYYMMDD` 后缀；文件路径与 `id` 无需采用相同日期分隔形式。
- `.txt` 派生全文、二进制和外部资料引用按 artifact/source 规则命名，不因本约定改写原始身份。
- 重命名归档时必须同步正文 `path`、registry、validation/evidence refs、核心索引和既有 capture 事件的 evidence path；不得只移动文件。

## 历史软件发布索引（不等于当前量产固件）

以下仅聚合**独立版本**的归档正文。版本号表示当时记录的发布身份；
不表示当前设备运行版本、已通过实机 HIL 或已被 Owner 签收。
每条文档仍处于 `reviewing`，需要回读对应源码 commit/tag、NAS manifest
和真实测试证据，才能确认其中的外部发布事实。

- [v1.1.40（2026-07-30）](archive/release/2026-07-30-gd32l235-v1.1.40-nas-release.md)：软件发布、校验和与 OpenOCD 命令 dry-run 的历史记录。
- [v1.1.41（2026-08-05）](archive/release/2026-08-05-gd32l235-v1.1.41-nas-release.md)：后续独立 NAS 包；明确未进行真实板级烧录和 HIL。
- [v1.2.0（2026-08-20）](archive/release/2026-08-20-gd32l235-v1.2.0-nas-release.md)：历史记录声明相对 **v1.1.42** 的增量，不可误写为从 v1.1.41 直接升级；49°C/300 秒 PB10 保护尚无新的实机验证。
- [PA12 快慢充兼容性（2026-07-13）](archive/design/2026-07-13-pa12-fast-slow-charge-compatibility.md)：45°C/38°C 的 PA12 档位控制和 PB10 充电许可分别处理；试产 PA12 悬空不构成量产实际充电电流切换验收。

这些版本记录彼此不是“兼容 shim”或重复正文，**不得为减少条目数而覆盖或删除**。
此入口未登记 v1.1.42 的完整发布报告，不能据此断言源码仓不存在该版本；
若要构建连续版本链，必须补充其可核验来源，而不能由 AI 推断。
`hardwareVerificationRequired=false` 只描述当次发布配置，不能替代真实设备资格。

## 充电唤醒历史契约差异（只作导航，不判定当前固件）

下列条目都属于有日期的 `reviewing` 记录，不是同一固件版本的
`active` 规则。它们对 **SLEEP 能否由充电接入唤醒** 的描述不一致，
不能仅选择日期较晚的一篇就推断当前量产行为，更不能据此修改 MCU
电源状态机或生成新的 owner 批准。

- [2026-07-22 MCU/SoC 低功耗协同候选](current/soc-low-power-contract.md)：该文档的四状态表将 SLEEP 唤醒限定为 WiFi、SoC RTC，将 DEEP_SLEEP 唤醒限定为 WiFi；其 `as_of=2026-07-22`，虽位于 `current/`，仍为待复核候选。
- [2026-07-30 智能留电与 PA7 充电唤醒](archive/design/2026-07-30-smart-reserve-charge-wakeup.md)：历史记录写明删除 MCU 2%/3% 自主低电休眠，业务 5% 策略归 SoC，PA7 CHARGE 可在 **SLEEP 与 DEEP_SLEEP** 触发不同的 PA8/PA15 唤醒动作；明确软件验证通过、板端 HIL 未执行。
- [2026-08-04 电源开关与 UART 同代交接](archive/session/2026-08-04-power-switch-uart-handoff-implementation.md)：后续记录**只允许 DEEP_SLEEP** 充电恢复，并将 SLEEP 定义为不被充电唤醒的用户休眠；同时描述 daemon 接管 UART 的 `TARGET_STATE/APP_EXITED` 和失败时硬回退。记录的是当时分支/工作区范围，不是已验证的当前量产配置。

**判定门槛：** 须用同一份现行 GD32L235 + PCR02 SoC 精确源码 commit、
协议定义和构建制品核对 PA7、`0x04`、`0x07`、PA8、PA15 的
状态转换，再通过真实硬件复现 SLEEP/DEEP_SLEEP 插桩、物理开关 OFF、
WiFi/CHARGE 同时到达的负例及示波器波形，最后取得真实 owner 的产品策略确认。
在此之前保持三篇独立的历史来源，不覆盖、删除、自动 supersede 或提升。

<!-- knowledge-hub-project-readiness:start -->
## 成熟度工作台

以下入口是单一 `reviewing` evidence contract 与统一 dashboard；不代表 owner 签收或发布就绪。

- [项目 evidence contract](validation/project-readiness.md)
- [统一 readiness dashboard](../../indexes/project-readiness.md)
<!-- knowledge-hub-project-readiness:end -->
