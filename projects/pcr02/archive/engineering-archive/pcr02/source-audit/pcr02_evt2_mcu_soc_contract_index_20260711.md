# PCR02 EVT2 MCU/SoC contract index

Date: 2026-07-11
Status: reviewing; source-derived MCU/SoC contract index, not board-level validation proof
Project: PCR02 EVT2 / SSC305 / GD32L235 / MM32SPIN023C

## Purpose

This note turns the PCR02 EVT2 MCU/SoC relationship into a reusable, searchable Knowledge Hub index. It connects the hardware PDF index with GD32L235 main-board MCU firmware documents, GD32L235 source contracts, MM32SPIN023C release-package boundaries, and the SSC305 side integration assumptions.

The goal is to avoid reparsing the same PDFs, DOCX files, firmware docs, and protocol headers for every follow-up task. This is an engineering index and source-audit record. It does not replace source files, does not prove board behavior, and does not certify a release.

## Source set

Primary source documents and code:

| Source | Workspace-relative path | Role |
| --- | --- | --- |
| PCR02 hardware PDF index | `projects/pcr02/archive/engineering-archive/pcr02/source-audit/pcr02_evt2_hardware_pdf_reference_index_20260711.md` | Hardware topology, power tree, schematic page index |
| MCU aggregate repo README | `workspace-root:work/mcu/README.md` | MCU subrepo and release-tool boundaries |
| MCU aggregate repo rules | `workspace-root:work/mcu/AGENTS.md` | Release, archive, and subrepo governance |
| GD32L235 rules | `workspace-root:work/mcu/gd32l235/AGENTS.md` | Flash layout, Stage0/Stage1/App/Download roles |
| GD32L235 README | `workspace-root:work/mcu/gd32l235/README.md` | Build/package artifacts and release evidence |
| GD32L235 release profile | `workspace-root:work/mcu/gd32l235/firmware-release.json` | `source-build` release entrypoint |
| GD32L235 IO DOCX | `workspace-root:work/mcu/PCR02 EVT2 GD32L235CBT6（LQFP48）单片机IO功能说明.docx` | Main-board MCU pin functions |
| Motor serial DOCX | `workspace-root:work/mcu/串口通信协议.docx` | Motor MCU app-level UART frame semantics |
| GD32L235 SoC heartbeat doc | `workspace-root:work/mcu/gd32l235/Docs/SOC心跳状态同步终态方案与落地计划.md` | Final heartbeat ABI and boot guard behavior |
| GD32L235 main protocol doc | `workspace-root:work/mcu/gd32l235/Docs/主板MCU串口通信与转发协议规范.md` | SoC-main MCU-motor routing contract |
| GD32L235 PA11 power policy doc | `workspace-root:work/mcu/gd32l235/Docs/PA11关机禁止充电与SOC上电禁止设计.md` | PA11/PA15/PA8/PB10 power gate semantics |
| GD32L235 shutdown doc | `workspace-root:work/mcu/gd32l235/Docs/SOC侧Shutdown确认闭环设计.md` | Shutdown-stage confirmation contract |
| GD32L235 low-battery sleep doc | `workspace-root:work/mcu/gd32l235/Docs/低电量SOC休眠保护设计.md` | Low-battery sleep state-machine boundary |
| GD32L235 protocol headers/source | `workspace-root:work/mcu/gd32l235/App/protocol.h`, `App/protocol_handlers/*.c`, `App/motor_protocol.h`, `App/motor_protocol.c`, `App/bsp.c`, `App/bsp.h` | Current source-level constants and implementation anchors |
| MM32SPIN023C rules and README | `workspace-root:work/mcu/mm32spin023c/AGENTS.md`, `workspace-root:work/mcu/mm32spin023c/README.md` | Third-party motor MCU artifact/package boundary |
| MM32SPIN023C release profile | `workspace-root:work/mcu/mm32spin023c/firmware-release.json`, `workspace-root:work/mcu/mm32spin023c/release.json` | `external-artifacts` release entrypoint and current version metadata |

## System topology

PCR02 EVT2 has three software-visible control actors:

| Actor | Practical role | Key links |
| --- | --- | --- |
| SSC305 SoC | Linux/application runtime, camera/LCD/audio/storage/Wi-Fi data path, high-level OTA orchestration | Talks to GD32L235 over the main UART protocol on the MCU UART path |
| GD32L235 main-board MCU | Low-power coordinator, power/charge/fuel-gauge owner, wake/sleep/shutdown bridge, IR/TOF/IMU/Wi-Fi wake arbiter, motor command/OTA proxy | Talks to SSC305 over PC10/PC11-side UART and to two motor MCUs over PA2/PA3 and PC6/PC7 |
| MM32SPIN023C motor MCU | Third-party motor-control firmware and OTA target; source is not owned in this repo | Reached indirectly by SSC305 through GD32L235 motor UART proxy |

The main hardware PDF index should be consulted first for rail names, schematic page numbers, and board-level signal names. This note adds the firmware/protocol view on top of that hardware index.

## GD32L235 main-board MCU IO map

The GD32L235 IO DOCX defines these PCR02-facing pins:

| Pin | Direction | PCR02 role |
| --- | --- | --- |
| PC13 | Output | IR receiver power control; set high during recharge start, otherwise low |
| PC14 | Output | Motor driver module power control; `1` on, `0` off; added for DVT pilot |
| PA0 | Input | Wi-Fi/IMU/TOF interrupt wake input to MCU |
| PA1 | ADC input | IR distance analog input |
| PA2/PA3 | UART | Motor driver module 1 UART |
| PA4 | Input | TOF interrupt |
| PA5/PA6 | Input | Motor NTC inputs |
| PA7 | Input | Charging-dock charge-success detect; `1` success, `0` failure |
| PB0/PB1 | UART | Debug serial |
| PB10 | Output | Battery charge enable; disabled on fuel-gauge TS abnormality and under PA11 OFF policy |
| PB11 | Output | IR distance module power; `1` on, `0` off; normally enabled during motor movement |
| PB5/PB14/PB15/PB6/PB8 | Input | IR receiver inputs |
| PA12 | Output | Charge-current setting; `1` = 1.15A, `0` = 1.0A, default `0` |
| PC6/PC7 | UART | Motor driver module 2 UART |
| PA8 | Output | SoC work-mode control; `1` SoC on/wake, `0` SoC sleep |
| PA9 | Input | Fuel-gauge interrupt |
| PA10 | Input | IMU interrupt |
| PA11 | Input | Power switch status; `1` on, `0` off |
| PB13 | Input | Host reset tactile switch; `1` active |
| PA13/PA14 | SWD | Firmware programming/debug |
| PA15 | Output | Power-on keep; defaults high after power-on, later released after switch-off flow |
| PC10/PC11 | UART | SoC communication UART |
| PC12 | Input | Wi-Fi communication interrupt |
| PB3/PB4 | I2C | Fuel-gauge I2C |
| PB12 | Output | SDIO enable control for low-power strategy |
| PB7 | Output | Wi-Fi internal power control; `0` on, `1` off; held low after power-on |
| PB9 | Output | 23kHz PWM |

Important naming caution: the main protocol document maps left motor to link A, board silkscreen `MOTOR2`, UART `PA2/PA3`, NTC `PA5`; right motor to link B, board silkscreen `MOTOR1`, UART `PC6/PC7`, NTC `PA6`. Future diagnostics should name both logical side and board silkscreen to avoid reversing the two motors.

## SoC-main MCU protocol contract

The SSC305 side and GD32L235 main-board MCU use a unified main protocol:

- Frame header: `AA 55`.
- Frame includes `TARGET`, `CTRL`, `SEQ`, `CMD`, payload, and `CRC16`.
- `LENGTH` and `CRC16` use Big-Endian.
- `TARGET=0x00` means GD32L235 main-board MCU itself.
- `TARGET=0x01` means left motor MCU.
- `TARGET=0x02` means right motor MCU.
- `TARGET=0x03` means dual motor MCU target.

Main command ranges from current GD32L235 source:

| Range / command | Meaning |
| --- | --- |
| `0x01` | `CMD_HEARTBEAT`; final ABI is 4B state payload |
| `0x02` | `CMD_GET_FW_VERSION`; returns main-board MCU App version |
| `0x03..0x0F` | SoC reset, sleep, wake, shutdown, runtime state, module IRQ/policy/resync/factory-reset commands |
| `0x10..0x19` | Motor app-control, motor data report, motor app version and hall-calibration commands |
| `0x20..0x2E` | OTA command domain |
| `0x30..0x37` | Battery gauge, charge station, IR power, charge enable/current/temp commands |
| `0x40..0x42` | IR data reporting |
| `0xE0..0xE2` | Factory bridge mode and raw motor-frame tunnel |

Factory bridge and motor OTA routing:

- `0xE0` configures or reads bridge state.
- `0xE1` sends a raw motor frame from SoC through GD32L235 to the selected motor target.
- `0xE2` reports motor-side raw or abnormal frames back to SoC.
- Motor OTA uses `TARGET=0x01/0x02/0x03` with `CMD=0x20..0x28`.
- `0x2E` explicitly enters motor Boot mode through the sequence "Boot-ready probe -> App `0x0E` -> Boot-ready recheck".
- `0x21` must not implicitly trigger App `0x0E`.
- `0x2B` is only for main-board MCU OTA status; motor targets return `UNSUPPORTED`.
- Dual-motor OTA standard sequence is `0x17`, `0x2E`, `0x21`, `0x27`, repeated `0x23`, then `0x24`, `0x26`, `0x22`.

Main-board MCU App OTA from current source uses the same `CMD_OTA_*` command IDs for `TARGET=0x00`: begin/write/verify/clear/commit/reboot, write-offset resume, memory-info, status, comms/profiler snapshots. `CMD_OTA_BEGIN` accepts 8B or 12B payload: firmware size, expected CRC32, and optional firmware type. `CMD_OTA_GET_MEM_INFO` reports `IAP_DOWNLOAD_ADDR` and `IAP_DOWNLOAD_MAX_SIZE`.

## Heartbeat and SoC boot guard

The GD32L235 heartbeat design is intentionally incompatible with the legacy version-carrying heartbeat:

- `CMD_HEARTBEAT / UART_MSG_TYPE_HEARTBEAT_NOTIFY = 0x01`.
- Payload length is fixed at 4 bytes.
- Byte 0: `seq`.
- Byte 1: endpoint state, with Bit7..6 as `source_role` and Bit5..0 as `runtime_state`.
- Byte 2: `status_bitmap`.
- Byte 3: `reset_or_reboot_reason`.
- Version read belongs to `GET_FW_VERSION(0x02)`, not heartbeat.
- `len != 4` is invalid heartbeat.

Current source anchors:

- `PROTOCOL_HEARTBEAT_PAYLOAD_LEN = 4`.
- roles: `PROTOCOL_HEARTBEAT_ROLE_MCU=0x00`, `PROTOCOL_HEARTBEAT_ROLE_SOC=0x01`.
- runtime states include `BOOTING`, `RUNNING`, `APP_READY`, `PREPARE_SLEEP`, `KEEPALIVE_SLEEP`, `WAKING_SOC`, `SHUTDOWN_HANDSHAKE`, `REBOOTING`, `FAULT`.
- status bits include `READY`, `UART_READY`, `SOC_POWER_ON`, `SHUTDOWN_PENDING`, `BOOT_GUARD_ACTIVE`, `LOW_POWER`, `FAULT`, `REQUEST_RESYNC`.
- `system_handler.c` accepts SoC heartbeat only when payload length is 4 and source role is SoC.
- On valid SoC heartbeat, GD32L235 updates `RunParam.Soc_Boot_Guard_Flag` from `BOOT_GUARD_ACTIVE`.

Operational implication:

- During SoC soft reboot, SoC should report `REBOOTING -> BOOTING -> APP_READY`.
- During `boot_guard_active`, GD32L235 suppresses Wi-Fi/IMU/TOF-triggered PA8 wake pulses.
- If SoC reboot command fails and the process continues running, SoC must recover to `APP_READY` and clear boot guard/shutdown-pending state.

## Shutdown, PA11, PA15, and PA8 contract

The current source/docs split power control into distinct roles:

| Signal / state | Contract |
| --- | --- |
| PA11 | Highest product-level gate for whether SoC is allowed to run and whether charging is allowed |
| PA15 | `KEY_PWRON_KEEP`; releases MCU/system power-hold path during true switch-off shutdown |
| PA8 | SoC wake/sleep pulse/control path; not a total power switch |
| PB10 | Charge enable; must remain disabled under PA11 OFF policy |
| PB7 | Wi-Fi internal power control |
| PB12 | SDIO enable/disable control for low-power leakage strategy |

Shutdown-stage protocol:

- Command: `CMD_SHUTDOWN_STAGE_NOTIFY / UART_MSG_TYPE_SHUTDOWN_STAGE_NOTIFY = 0x09`.
- Stage `0x01`: `SWITCH_OFF_DETECTED`.
- Stage `0x02`: `COMMAND_SENT`.
- Stage `0x03`: `SOC_CONFIRMED`.
- Stage `0x04`: `TIMEOUT_FORCE_OFF`.
- Stage `0x05`: `CANCELLED`.
- Reason `0x01`: power key.
- Reason `0x02`: low-battery sleep.
- Reason `0x03`: charge sleep.
- Payload is backward compatible: `stage`, optional `reason`, optional `detail`.

Source-level behavior:

- `system_handler.c` handles `SOC_CONFIRMED` by calling `Bsp_SocExit_OnSocConfirmed(...)`.
- `system_handler.c` handles `CANCELLED` by calling `Bsp_SocExit_OnSocCancelled(...)`.
- `bsp.c` defines distinct exit actions for `SOC_EXIT_ACTION_POWER_OFF_PA15` and `SOC_EXIT_ACTION_SLEEP_SOC_PA8`.
- `Bsp_ApplySwitchChargePolicy()` applies switch-gated charge policy to charge enable logic.
- Wake processing clears Wi-Fi/IMU/TOF wake flags when switch is off or SoC boot guard is active.

PA11 OFF policy:

- PA11 OFF means SoC is forbidden to power on, wake, or run.
- PA11 OFF after docking/charging must not support charging and must not trigger SoC or whole-device power-on.
- Runtime `PA11=0 && charging=true` is treated as `SWITCH_OFF_CHARGE_BLOCK`: PB10 disabled, no SoC wake, and no normal shutdown/sleep request.
- The hardware document states EVT2 later boards remove/DNP the `CHARGING_DET` diode path to the main MOSFET. That board-level BOM/path fact still needs owner or board validation before being used as acceptance proof on a specific unit.

Low-battery policy:

- Low-battery protection is "SoC sleep protection", not unconditional power-off.
- `battery_percent <= 2 && !charging` is the base trigger, but actual triggering must pass startup grace, consecutive sampling, and voltage cross-checks.
- Low-battery recovery is `battery_percent > 2 || charging == true`.
- If PA11 remains ON, releasing PA15 does not prove SoC power-off because the switch path can still hold system power.
- Therefore PA8 sleep is the correct low-battery SoC protection action, while PA15 release belongs to true PA11 OFF shutdown.

## Motor MCU app protocol and MM32 boundary

Motor app-level UART protocol:

- Motor MCU sends periodic data at 50Hz.
- Nominal baud rate is documented as 38400 bps, with 115200 bps also noted in the source document; validate actual configured baud before line-level debugging.
- Feedback frame header is `55 5A`.
- Upper-control command frame header is `55 A5`.
- Checksum is the 8-bit sum of bytes excluding frame header and checksum.
- Feedback frame length field is `0x15`.
- Speed control command uses command `0x05`, default motor ID `0x7F`, direction and target speed fields, reserved 2B, and checksum.
- GD32L235 source defines `MOTOR_PROTOCOL_BROADCAST_ID=0x7F`, `CMD_SPEED_CONTROL=0x05`, `CMD_POSITION_CONTROL=0x06`, `CMD_STATUS_FEEDBACK=0x06`, `MOTOR_STATUS_FRAME_LEN_FIELD=0x15`.

MM32SPIN023C release/flash boundary:

- The PCR02 MM32SPIN023C repo is a third-party artifact packaging repo, not a source firmware repo.
- It must not modify vendor firmware content and should not permanently commit `.hex`/`.bin` vendor blobs.
- Flash base is `0x08000000`, size 32KB.
- SRAM is 4KB at `0x20000000..0x20000FFF`.
- `BootJumpFlag` is at `0x08001400`, value `55 AA AA 55`.
- App starts at `0x08001800`.
- Data partition is `0x08007C00..0x08007FFF`, 1KB, for parameters/calibration.
- OTA payload is `mm32spin023c_app.bin`.
- Merged image is `mm32spin023c_boot_flag_app_merged.hex/.bin`.
- Flash-full image is `mm32spin023c_flash_full.hex/.bin`.
- Default programming uses merged image and preserves data partition.
- Factory/full recovery uses flash-full image and erases data, requiring explicit `--force-erase`.
- Current release metadata observed during this archive pass: `release.json` version `0.4.7`; treat as source metadata, not a certified deployed version unless release evidence is checked.

## GD32L235 boot and OTA layout

GD32L235 is a source-build firmware repo with three executable images and one download slot:

| Region | Address | Size | Role |
| --- | ---: | ---: | --- |
| Flash base | `0x08000000` | 128KB total | GD32L235 internal flash |
| Stage0 | `0x08000000` | 8KB | Minimal boot trust chain |
| Stage1 | `0x08002000` | 16KB | Upgrade-capable boot / emergency OTA path |
| App | `0x08006000` | 50KB | Business firmware and protocol bridge |
| Download | `0x08012800` | 50KB | OTA download slot |
| Flag/User | `0x0801F000` | 4KB | Boot/OTA flags and user data |
| RAM | `0x20000000` | 24KB | Runtime RAM |

Expected build/package outputs:

- `gd32l235_app.bin`.
- `gd32l235_stage0_stage1_app_merged.bin`.
- `gd32l235_flash_full.bin`.
- `package_v<version>.zip`.
- `package_manifest.json`.
- `checksums.sha256.txt`.

`firmware-release.json` declares profile `gd32l235`, type `source-build`, and uses the repo fwtool build/package/check commands. Formal version bumps are release actions and should not be conflated with source-audit archiving.

## Release orchestration implications

The PCR02 vehicle should be treated as a multi-firmware system:

- SSC305 SoC release and OTA packaging come from the PCR02 SigmaStar release flow.
- GD32L235 main-board MCU firmware is source-built and released through MCU release tooling.
- MM32SPIN023C motor MCU firmware is an external-artifact package with strict boot/app/data partition constraints.
- Release evidence should include package manifests, checksums, release manifests, and batch manifests from the MCU release tooling.
- SOC OTA flows that consume MCU artifacts should pin artifact versions/hashes rather than rely on a live working tree.

MCU aggregate repo stable evidence paths:

- NAS root: `/mnt/mcu-release-nas/robot/mcu`.
- Per-package evidence: `package_manifest.json`, `checksums.sha256.txt`, `release_manifest.json`.
- Batch evidence: `_batches/<batch-id>/release_batch_manifest.json`.

These release paths are listed for retrieval and audit. Large binary artifacts should not be copied into Knowledge Hub.

## Cross-reference

This note should be read together with:

- `pcr02-evt2-hardware-pdf-reference-index-20260711`: hardware PDF-derived topology, rails, schematic page index, and key signals.
- `mcu-memory-curation-coverage-20260518`: historical MCU memory-curation coverage; archive-only.
- `mcu-release-nas-guard-governance-20260629`: historical MCU release/NAS guard governance; archive-only unless current release evidence is rechecked.
- PCR02 `runtime-io` and `hardware-power` Hub records for watchdog, UART nonblocking behavior, power-hold, and shutdown path validations.

## Search keywords

Recommended query terms:

`PCR02 EVT2 MCU SoC`, `GD32L235`, `MM32SPIN023C`, `SSC305`, `PA11`, `PA15`, `PA8`, `PB10`, `PB12`, `PC10`, `PC11`, `BootJumpFlag`, `SOC_CONFIRMED`, `CMD_HEARTBEAT`, `BOOT_GUARD_ACTIVE`, `CMD_SHUTDOWN_STAGE_NOTIFY`, `CMD_OTA_ENTER_BOOTLOADER`, `TARGET=0x03`, `MOTOR2 PA2 PA3`, `MOTOR1 PC6 PC7`, `55 A5`, `55 5A`, `IAP_DOWNLOAD_ADDR`, `SWITCH_OFF_CHARGE_BLOCK`.

## Limits and remaining work

- This note is source-derived from local docs, firmware source, and release metadata. It is not a board validation report.
- No GD32L235 build, MM32 package check, SOC build, HIL run, serial trace, oscilloscope capture, or vehicle OTA validation was executed for this archive entry.
- MM32SPIN023C source is not available in the observed repo; only artifact packaging and memory-layout constraints are indexed here.
- DOCX extraction was used for IO/protocol content; if these DOCX files are later superseded, this note should be reviewed.
- PA11 OFF charging and `CHARGING_DET` DNP semantics require specific board/BOM/waveform confirmation before being used as pass/fail criteria.
- The SoC-side implementation must be checked in the SSC305 application repo before declaring heartbeat/shutdown protocol compatibility complete.
- No live memory, source project code, or active release baseline was modified by this note.

## Archive evidence

- Source: local PCR02 EVT2 hardware index, MCU aggregate docs, GD32L235 docs/source, MM32SPIN023C package docs, and motor protocol DOCX listed above.
- Topic: PCR02 MCU/SoC contract / source audit / power and UART protocol.
- Archive path: `projects/pcr02/archive/engineering-archive/pcr02/source-audit/pcr02_evt2_mcu_soc_contract_index_20260711.md`.
- Sanitization: no secrets, credentials, full logs, vendor binary bodies, or full source reproduction; only extracted engineering facts and code constants.
- Provenance: source docs and code read locally through `rtk`; DOCX text extracted from local document XML for targeted fields.
- Verification: Hub registry and consistency checks required after this file is registered.
- Memory candidate: no direct memory write; retrieve this note from Knowledge Hub.
- Gate result: needs registry entry, index updates, `knowledge-search`, and `knowledge-check` before final closeout.
