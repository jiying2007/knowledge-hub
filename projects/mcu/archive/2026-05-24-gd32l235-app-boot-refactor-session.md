# GD32L235 app_boot_v1 重构历史会话 2026-05-24

## 摘要

本文从两个旧 Codex archive `session-wrap` 合并迁移而来，保留 `gd32l235_app_boot_v1` 在 2026-05-24 的边界收敛、协议/OTA 重构、契约验证和静态 parity 检查历史。本文是 archive-only 记录，不代表当前仓库 HEAD、板级 HIL 或 OTA 验证状态。

## 阶段一：边界收敛和热点拆分

旧源 `20260524-141359-gd32l235-app-boot-v1-session-wrap-20260524.md` 记录：

- 仓库：`gd32l235_app_boot_v1`
- 分支：`master`
- 当时工作区干净。
- 当时提交：
  - `fd6f790 refactor(app): 拆分电机反馈解析流程`
  - `25f9564 refactor(app): 收敛边界并拆分复杂流程`
  - `ce12cf4 chore(init): 初始化当前重构基线`
- 删除旧聚合头 `App/include/app/My_include.h`，并在 `Tools/tests` 契约中禁止旧聚合头回归。
- 补齐 `Tools/Vendor/toolchains` 子模块 gitlink，提交点 `caeb712d508274c6539f693ea4efe7e15a607ce3`。
- 文档对齐 `Docs/verification/command-entrypoints.md`、`Docs/planning/drift-remediation.md`、`Docs/verification/acceptance-matrix.md`。
- 已拆复杂度热点：`motor_app_read_register_dual`、`motor_app_enter_bootloader_dual`、`protocol_system_try_handle_basic_command`、`protocol_handle_motor_hall_calibration_status`、`protocol_handle_motor_enter_boot`、`motor_parse_from_buffer`。

阶段一旧源记录当时通过：

- `rtk bash scripts/codex-check.sh --quick`
- `rtk git diff --check`
- `rtk git diff --cached --check`
- 跟踪文件 CRLF 扫描，`tracked_crlf_found=0`
- 旧残留引用扫描无命中

## 阶段二：协议、OTA 和 parity 收口

旧源 `20260524-231336-gd32l235-app-boot-v1-session-wrap.md` 记录：

- resumed baseline: `fd6f790 refactor(app): 拆分电机反馈解析流程`
- wrap 时 HEAD: `766485c refactor(app): 继续压缩协议与OTA函数`
- tracked working tree clean，`scratch/` 仍未跟踪。
- 当日新增提交：
  - `4f28f58 refactor(app): 继续收敛协议与驱动热点`
  - `cbafd8d refactor(app): 继续拆分驱动与协议热点`
  - `1a4934d refactor(app): 拆分电机OTA响应交换收尾`
  - `090e3be refactor(app): 清理剩余复杂度热点`
  - `766485c refactor(app): 继续压缩协议与OTA函数`
- 触及模块包括 ADC、fuel gauge、motor protocol、protocol exchange/router、factory bridge、OTA handler、system handler 和 IAP flash。

## 历史验证摘要

阶段二旧源记录最终通过：

- `rtk python3 Tools/tests/check_app_stage_style_contract.py`
- `rtk bash scripts/codex-check.sh --quick`

会话期间还曾通过一组 motor、OTA、protocol、factory bridge、IAP flash、system control、shutdown notify 和 power service 契约测试。旧源没有记录板级 HIL 通过。

## 静态 parity 结论

旧源记录：

- 未发现相对 `gd32l235` baseline 的明确生产功能丢失。
- 既有生产命令的协议命令值匹配。
- 旧仓 30 个 handled inbound commands 在重构仓中均有处理。
- motor protocol command/register 常量匹配。
- firmware version 保持 `1.1.19`。
- charge enable/current/temp range controls 存在。
- Hall calibration status command/register 支持存在。
- OTA/IAP status 和 retry behavior 由契约覆盖。
- outbound reports 存在：heartbeat、battery gauge、motor data、IR、IR distance、charge station、shutdown/runtime/aux reports。

已知差异：

- `CMD_BATTARY_GAUGE` 更名为 `CMD_BATTERY_GAUGE`，数值仍为 `0x30`。
- legacy `vofa.c/h` debug helper 未迁移，旧源判断为 debug residual，除非仍需要 VOFA float streaming。
- App image 从约 `40116` 增至 `43988` bytes，仍在预算内，但 flash headroom 降低。

## 风险和后续

- `scratch/` 当时仍未跟踪并被排除出提交。
- 功能 parity 主要来自静态对比和 quick contracts；高置信 timing/IO 行为仍需板级 HIL。
- 后续应做板级命令 sweep、完整 OTA HIL、充电控制硬件验证、factory bridge 并发验证，并确认 VOFA float debug streaming 是否废弃。

## 迁移边界

- Source:
  - `domains/codex/archive/codex-archive/session-wrap/20260524-141359-gd32l235-app-boot-v1-session-wrap-20260524.md`
  - `domains/codex/archive/codex-archive/session-wrap/20260524-231336-gd32l235-app-boot-v1-session-wrap.md`
- Source SHA256:
  - `8c78fc6ddd9ed56dc5995565bdc7497e835661c8d116fc64a908feb2417cb5d5`
  - `6b1202c675572b6f5c2da4a0ecb785b7ad34bb11cc6aed5d0e1d1ed2873b2117`
- Source size:
  - `2554` bytes
  - `5624` bytes
- Preflight rows: `CAEF-20260710-028..029`
- Tombstones: `CARE-20260710-036..037`
- 决策：两篇旧正文可在本记录、registry、index、tombstone 和授权账本落地后删除；不提升 active、不写 memory、不改 MCU 源项目。
