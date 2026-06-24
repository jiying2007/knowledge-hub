# PCR02 GD32L235 UART Watchdog And Nonblocking Runtime Notes

Date: 2026-06-12
Captured: 2026-06-15
Status: troubleshooting and implementation guidance

## Source

- Codex sessions:
  - `019eb024-28ff-75f3-bb8d-20ddd13874eb`
  - `019eb1e6-f65f-7952-8724-9849a3daad26`
  - `019ebb04-aeb5-7210-87c3-476fce324944`
  - `019ebbc3-373d-78d0-91c1-0b5f44edadfa`
- Scope: GD32L235 mainboard MCU, SoC UART protocol, watchdog resets, MCU OTA aftermath, battery/CW2217 initialization, and loop timing diagnostics.

## Sanitization

- Full serial logs and build artifacts are not copied.
- Preserved only command shapes, failure modes, diagnostic counters, timing thresholds, and version-context facts.

## Symptoms

Observed symptoms across sessions:

- SoC queries to mainboard MCU version timed out even though the command handlers existed.
- Motor version queries could sometimes work while mainboard MCU self queries timed out.
- Bootloader reported repeated watchdog resets and emergency-mode cycles after some firmware updates.
- `EVT_SLOW` logs showed long battery processing windows:
  - initial blocking examples around `dt=2984 ms`.
  - after partial improvement, remaining examples around `dt=852 ms`.
- Main loop timing could miss the 60Hz budget; a loop duration greater than 16ms was treated as evidence that the current cycle did not satisfy 60Hz.

## Current Analysis

The high-value conclusion is that the symptom is not simply "mainboard MCU command unsupported".

- `CMD_GET_FW_VERSION` / `0x02 target=0x00` exists in the mainboard MCU App system handler and should return a version ACK.
- `CMD_OTA_GET_BOOT_VERSION` / `0x20 target=0x00` should return either boot version ACK in Stage1 or an unsupported error ACK in App runtime. It should not normally become a pure timeout.
- A pure timeout therefore points to ACK not returning to SoC or the main loop not processing the protocol within the SoC timeout window.

The strongest software suspects were:

- `Uart_Soc_Send()` silently dropping ACK when `s_soc_uart_ready == 0`.
- TX wait timeout setting `s_soc_uart_ready = 0` without enough recovery/observability.
- `protocol_process()` placed after slower tasks in the main loop.
- Long blocking paths such as sleep/power management or battery initialization exceeding the 2s SoC wait window or the watchdog refresh budget.
- Battery/CW2217 initialization doing blocking work on the main runtime path.

## Implementation Guidance

For GD32L235 App runtime:

- Do not silently drop SoC ACKs when UART TX is not ready.
- Add or preserve counters for:
  - `soc_tx_not_ready_count`
  - `soc_tx_wait_timeout_count`
  - `soc_rx_overflow_count`
  - `crc_error_count`
  - protocol dispatch latency or loop max dt
- Move `protocol_process()` as early as practical in the main loop.
- Avoid long blocking delays in power/sleep/battery paths; if a delay is unavoidable, feed watchdog and continue protocol processing.
- Convert CW2217/battery initialization to a nonblocking state machine or bounded incremental work.
- Keep heavy diagnostics default-off; enable them by compile-time or runtime switch when chasing field issues.
- Record max loop dt; if one loop exceeds 16ms, classify that cycle as not meeting the 60Hz budget.

## Field Verification Commands

Use SoC-side diag to separate transport contention from MCU-side delays:

```sh
/customer/bin/prog_tool run-cmd diag.app.uart.versions.get.run '{}' --mode=remote
/customer/bin/prog_tool run-cmd diag.app.uart.versions.get.run '{}' --mode=local
```

Compare mainboard MCU and motor targets:

```sh
/customer/bin/prog_tool run-cmd diag.app.uart.motor.app_version.run '{"target":"left"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.motor.app_version.run '{"target":"right"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.versions.get.run '{}' --mode=local
```

Interpretation:

- `remote` stable and `local` unstable points toward local process/serial ownership or initialization contention.
- both modes timing out on target 0 points toward MCU ACK path, protocol loop blocking, UART TX readiness, or watchdog-loop interaction.
- motor targets stable while `mcu:"unknown"` points toward mainboard MCU local handler/ACK window, not a total UART physical outage.

## Watchdog And OTA Notes

After MCU OTA, repeated bootloader messages such as watchdog reset and emergency idle can coexist with a valid update result. That means:

- Do not stop at "download CRC and app CRC passed"; verify runtime stays alive after jump to App.
- Log reboot reason and watchdog reset state early in App.
- If reset repeats after App jump, inspect the first long-blocking initialization path and watchdog feed cadence.
- Clock fallback such as `clk=16000000` / IRC16M warning is a separate risk signal and should be recorded with reset loops.

## Battery And Charge Path Notes

Runtime observations also showed charge-state toggling and battery path timing issues:

- A field symptom described green breathing light and blue light alternating while charging.
- Measurement suggested the mainboard MCU charge-control IO was switching periodically.
- The report explicitly said `GD32L235_CHARGE_CERT_PROFILE` was not enabled and temperature was not over limit.
- This does not prove the charge IO caused watchdog reset, but it is a strong axis to log together with battery polling, PA7/PB10 charge detect, PA11 switch state, PA15 keep-on, and loop timing.

## Remaining Risks

- This note records a software-side diagnosis and mitigation direction; it is not a board-level electrical proof.
- UART physical quality, SoC serial ownership, MCU clock stability, and charge/power rail behavior still need targeted evidence when the symptom persists.
- Debug logs can perturb timing; default-off diagnostics are preferred for production-like testing.

## Provenance

- Related archive: `hardware-power/pcr02_power_hold_shutdown_path_20260606.md`.
- Related system topic: SoC `app_uart` and `sensor` paths in the PCR02 application stack.
- Related field behavior: repeated watchdog resets after MCU app update and slow battery processing logs.

## Quality Gate

- Source: local Codex session history and summarized serial evidence.
- Topic: runtime-io / hardware-power.
- Archive Candidate Path: `archive/pcr02/runtime-io/pcr02_gd32l235_uart_watchdog_nonblocking_20260612.md`.
- Sanitization: pass.
- Verification: based on code-path review and reported serial/runtime evidence; full board-level timing validation remains required.
- Memory Candidate: yes, after human review this can become a project diagnostic checklist.
- Gate Result: pass.
