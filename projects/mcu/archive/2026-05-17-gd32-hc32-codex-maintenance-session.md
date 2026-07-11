# GD32/HC32 固件 Codex 维护历史会话 2026-05-17

## 摘要

本文从旧 Codex archive `session-wrap` 选择性迁移而来，保留 `firmware-toolchains`、`gd32l235`、`charge_hc32f072` 三仓在 2026-05-17 的 Codex 维护配置治理历史。本文是 archive-only 记录，不代表当前固件构建、远端或硬件验证状态。

## 历史完成事项

- `gd32l235` 重新检查远端同步、fresh build、package、`fwtool check --scope all`、旧 `Examples/`、旧 `GD32L235_APP_BOOT`、旧构建产物和本机路径残留。
- `gd32l235` 移除个人 Codex VSCode 任务、旧根目录 `.agents/`、根目录 `skills/` 和 `.vscode/codex-tasks-sync.ps1`。
- 三仓新增仓库级 `AGENTS.md`。
- 三仓将项目 skill 放入 `.codex/skills/...`，避免污染固件根目录。
- 三仓新增 `scripts/codex-check.sh` 作为统一提交前检查入口。
- 工具链仓库新增 `docs/codex-workflow.md`，两个固件仓库新增 `Docs/codex-workflow.md`。

## 历史提交

- `firmware-toolchains/main`: `caeb712 chore: 添加 Codex 工具链维护规范`
- `gd32l235/master`: `1ea219b chore: 规范 Codex 固件维护配置`
- `charge_hc32f072/master`: `e2cdd29 chore: 添加 HC32 Codex 维护规范`

## 历史决策

- `gd32l235` 不再要求保持单一提交，因此使用普通提交推送，未改写远端历史。
- Codex 支持文件统一放在 `.codex/`、`AGENTS.md`、`Docs/codex-workflow.md` 或 `docs/codex-workflow.md`、`scripts/codex-check.sh`。
- VSCode 配置保持纯固件用途，不混入个人 Codex 配置切换任务。
- `charge_hc32f072` 继续按 `HC32F072FAUA`、TQFN-32-EP/QFN32(5x5)、单 App 镜像维护，不套用 GD32L235 的 Stage0/Stage1 分区。
- `firmware-toolchains` 以 `manifest.json` 作为消费仓库工具路径机器契约，新版本工具链应并排新增，不原地覆盖。

## 历史验证摘要

旧源记录当时通过：

- `firmware-toolchains/scripts/codex-check.sh --versions`
- `gd32l235/scripts/codex-check.sh --full`
- `charge_hc32f072/scripts/codex-check.sh --full`
- 三仓 `git diff --check`

旧源记录的资源占用：

- `gd32l235`: App FLASH 约 `77.13%`，Stage1 FLASH 约 `81.76%`，Stage0 FLASH 约 `28.32%`
- `charge_hc32f072`: App FLASH 约 `11.94%`，RAM 约 `14.36%`

这些验证只证明旧会话当时状态。本次迁移未重新执行当前源仓构建、Windows 主机验证、OpenOCD 或硬件验证。

## 风险

- Windows 本机未在旧会话中重新实际构建。
- `gd32l235` 仍有 GD32 官方库 allowlist 内 `-Wtautological-compare` 警告。
- `charge_hc32f072` 仍有既有 C warning；旧源记录当时 `fwtool check` 通过。
- Windows OpenOCD GD32L23x flash/debug 仍需硬件验证。

## 迁移边界

- Source: `domains/codex/archive/codex-archive/session-wrap/20260517-154134-gd32-firmware-session-wrap.md`
- Source SHA256: `c8c3e8361a0cc3bdf0fbfa72eb6a11b73e441cb773e58872ed20cb683095566b`
- Source size: `4170` bytes
- Preflight row: `CAEF-20260710-025`
- Tombstone: `CARE-20260710-033`
- 决策：旧正文可在本记录、registry、index、tombstone 和授权账本落地后删除；不提升 active、不写 memory、不改 MCU 源项目。
