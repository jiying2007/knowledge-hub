# PCR02 Power Hold And Shutdown Path Notes

Date: 2026-06-06
Updated: 2026-06-15
Status: design note, hardware verification pending

## Background

Recent archive review found reusable conclusions around the power hold/shutdown chain, especially PA11/SWITCH and PA15/KEEP_ON style signals. The available evidence is primarily software design and historical session context, not final board-level waveform proof.

## Current Conclusion

Treat the power hold path as a hardware-software contract:

- Switch/input debounce, power-off request, shutdown ACK wait, and keep-on release are software-visible states.
- The software path can expose counters and diagnostic state, but cannot prove that power is physically removed.
- PA15/KEEP_ON release is only effective if the board power topology allows software to drop the hold rail.
- If a mechanical switch or external latch still asserts power, releasing KEEP_ON may not power the device down.

Therefore, this topic remains hardware-verification pending.

## Software Evidence To Preserve

The reusable software-side design points are:

- Debounce handling for switch/power input.
- Shutdown handshake and ACK wait timeout accounting.
- Stage drop or completion counters for shutdown progress.
- Wake/sleep pulse request counters.
- Protocol-visible status for board/system gates.

These are useful diagnostics and should be kept in debug or production-test evidence when investigating reboot, shutdown, or low-power behavior.

## Hardware Verification Required

Before treating shutdown as accepted, verify on the target board:

- PA11/SWITCH polarity and debounce behavior.
- PA15/KEEP_ON polarity and timing.
- Power rail behavior before, during, and after shutdown request.
- Whether external button state can keep the rail alive.
- MCU/SOC reset timing relative to SPI-NAND and UBI mount.
- Brownout or forced-reset behavior during low battery and repeated reboot testing.

## Relation To Flash Read Issues

This note does not claim PA11/PA15 caused `/customer` SquashFS read instability. It only records that repeated reboot, low battery, reset timing, and power-hold behavior are plausible investigation axes when `/dev/ubi0_3` or `/dev/ubiblock0_3` hashes change intermittently.

## 2026-06-15 Runtime Observation Update

Later sessions added field observations that should be kept with the power-hold topic:

- SOC could suddenly enter a no-response sleep/shutdown-like state while battery voltage was low and health logs still showed `soc: not_ready`.
- Charging tests reported alternating green breathing light and blue light, with measurement suggesting the mainboard MCU charge-control IO periodically switched.
- The same report stated `GD32L235_CHARGE_CERT_PROFILE` was not enabled and temperature was not over limit, so charge certification and thermal cutoff should not be assumed as the direct cause without more evidence.
- Repeated MCU watchdog resets after App jump mean power/charge diagnostics must be correlated with main-loop blocking diagnostics, not treated as a pure hardware-only issue.

When this symptom appears, collect these together:

- PA7/PB10 charge-detect/control state.
- PA11 switch raw/filter state.
- PA15 keep-on state.
- MCU reboot reason and watchdog flag.
- SOC sleep/request/ACK state.
- Battery voltage, capacity, temperature, charge current and work current.
- Main-loop max dt and any `EVT_SLOW` tags.
- Whether charge-control IO toggles before or after the software state transition.

## Provenance

- Current session archive audit on 2026-06-06.
- Historical local session snippets and MCU design notes referencing PA11/SWITCH, PA15/KEEP_ON, shutdown ACK, and power diagnostics.
- Later sessions on 2026-06-10 to 2026-06-12 describing charge-control IO toggling, low-battery SOC no-response behavior, and GD32L235 watchdog loops.
- Evidence status: software design evidence only; board waveform verification is still required.

## Follow-up

- Add a board validation capture template for shutdown request, KEEP_ON release, reset, SPI-NAND power, and first UBI attach after reboot.
- Keep this note separate from confirmed flash read-path root cause until hardware evidence is available.
