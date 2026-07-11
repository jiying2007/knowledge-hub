# MCU 发布、flash guard 与 NAS 发布链路治理归档 2026-06-29

## 边界

本文从旧 Codex archive `release-governance/20260629-040442-mcu-release-nas-guard-governance.md` 抽取，记录 2026-06 下旬 GD32L235 / HC32F072 / MM32SPIN023C 发布治理经验。本文是 archive-only，不声明当前 MCU 发布基线、当前 tag 状态或硬件验证完成。

## 关键结论

- GD32L235 的构建门禁不是形式检查；`scripts/codex-check.sh --full` 会真实检查 App flash headroom。
- 如果用户明确指定“保留 4KB 余量”，发布 guard 应收敛到 4096B，而不是反复试探中间值。
- 调整 `Tools/Firmware/build_guard_baseline.json` 的 `app.minFlashHeadroom` 不等于改变 IAP 分区、CRC、metadata 或升级流程。
- GD32L235 的版本真源仍是 `App/bsp.h` 中的版本宏，tag 已存在时必须 bump patch，不能复用旧 tag。
- HC32F072 在本机缺少 OpenOCD backend 时，只能声明构建/打包/脚本 dry-run 通过，不能声明板级 flash/readback 已验证。
- 子仓发布和根仓 gitlink 是两个层级：子仓先验证、提交、push；根仓再更新 gitlink 或 lock；根仓无 remote 时不能承诺 push。
- 默认调试信息关闭应从宏默认值和 build type 默认值两层处理，不能只改运行时日志。

## 推荐发布检查矩阵

GD32L235:

- `rtk bash scripts/codex-check.sh --full`
- `rtk python3 Tools/Firmware/fwtool.py build ...`
- `rtk python3 Tools/Firmware/fwtool.py package ...`
- `rtk python3 Tools/Firmware/fwtool.py check --scope all ...`
- 检查 `build_budget_summary.json` 或 guard report 中实际 headroom。

HC32F072:

- `rtk bash scripts/codex-check.sh --full`
- 若缺少 OpenOCD，只保留 warning，不使用硬件验证措辞。

firmware-release-tools / MM32SPIN023C:

- 发布脚本 `--help`
- profile check
- package / check-package / dry-run burn/readback，按仓库能力执行。

NAS 发布:

- mount preflight
- release dry-run
- publish
- tag / push tag
- 目标目录 `sha256sum -c checksums.sha256.txt`

## 已沉淀的历史事实

- GD32L235 guard 从 8192B 调整到 4096B 后，实际 App 余量仍高于 4KB。
- GD32L235 / HC32F072 联合发布会先做 version/change/tag 预检，再执行各子仓 release 脚本，最后 publish 到 NAS 批次目录。
- `release-to-nas.sh` 成功后应检查批次 manifest 和最终目录 checksum。

## 迁移记录

- Old source: `domains/codex/archive/codex-archive/release-governance/20260629-040442-mcu-release-nas-guard-governance.md`
- Old source SHA256: `fa9828b56e3dbc54689551b4a59dd5eecc3cce8b510065f2ee6cd61a8cfffef7`
- Old source size: `3519` bytes
- Old source lines: `76`
- Final coverage row: `artifacts/manifests/codex-archive-final-body-coverage-20260711.jsonl#CAFC-20260711-007`
- Tombstone: `artifacts/manifests/codex-archive-removal-execution-20260711-final-bodies.jsonl#CARE-20260711-047`

## 风险

- 发布时仍应以当次 manifest 和 checksum 为准，不能复用旧 NAS 产物结论。
- 后续分区布局、IAP bootloader 或 release tools 变化后，4KB guard 结论需要重新评估。
- 没有硬件 flash/readback 证据时，不得把 dry-run 等同于量产验证。
