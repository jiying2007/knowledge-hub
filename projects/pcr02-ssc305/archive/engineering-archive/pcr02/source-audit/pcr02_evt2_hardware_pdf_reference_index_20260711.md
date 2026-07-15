# PCR02 EVT2 hardware PDF reference index

Date: 2026-07-11
Status: reviewing; PDF-derived engineering index, not board-level validation proof
Project: PCR02 EVT2 / SSC305

## Purpose

This note extracts a reusable, searchable hardware reference index from the PCR02 EVT2 system block, power tree, and main-board schematic PDFs so later PCR02 work can query Knowledge Hub first instead of reparsing the PDFs every time.

It is an engineering index and cross-reference. It does not replace the source PDFs, does not prove board-level behavior, and does not supersede hardware measurements, boot logs, oscilloscope captures, or owner-approved decisions.

## Source set

| Source PDF | Local source path | Pages | SHA256 |
| --- | --- | ---: | --- |
| PCR02 EVT2 system block | workspace root: `PCR02 EVT2 系统框图-20251201.pdf` | 1 | `7d424bd76cde800b50f1d1044fc709da91ef730f95bc93159d2fcf139844344f` |
| PCR02 EVT2 power tree | workspace root: `PCR02 EVT2电源树-20251201.pdf` | 1 | `70f92dd846b0028b6380f03ebf75bb6ad4b1cdcbc053e188bd28d3719b53c6b1` |
| PCR02 main-board schematic | workspace root: `PCR02_MAIN_V2.0_20251211.pdf` | 20 | `dfaf9d47470314bb1ea65dd7a5805f714bd084bfc09e950a3f6c74f99e4f7f34` |

Duplicate copies under workspace-relative `work/mcu/` have the same SHA256 for these three PDFs and are not treated as separate sources.

Extraction evidence:

- `rtk pdfinfo` confirmed page counts and no PDF encryption.
- `rtk pdftotext -layout` extracted text from all three PDFs.
- `rtk pdftoppm` plus page image inspection was used to cross-check schematic page readability.

## High-level architecture

PCR02 EVT2 is organized around three practical power/control domains:

| Domain | Main role | Key members |
| --- | --- | --- |
| Always-on / low-power domain | Battery, RTC, wake detection, MCU-managed wake and power hold | battery, fuel gauge, MCU, RTC rails, IMU, TOF low-power interrupt, Wi-Fi wake, switch/power key |
| AOV mode supply domain | Keep selected wake/sensing and low-power communication paths alive while SoC is off or reduced | Wi-Fi keepalive/wake, IMU interrupt, TOF interrupt, MCU wake logic, selected RTC/3V3/1V8 rails |
| Main SoC active domain | Full Linux/SSC305 runtime with camera, LCD, audio, storage and Wi-Fi data | SSC305 CA32/DDR/M4-side resources, NAND Flash, Camera MIPI, dual LCD/backlight, audio amp, TF/MicroSD, AP6303BH Wi-Fi/BT |

The system block shows MCU as the low-power coordinator and SoC wake owner bridge:

- Wi-Fi can wake from keepalive mode through a wake pin after receiving an app-side command.
- IMU remains powered in keepalive mode; motion interrupt reaches MCU, then MCU wakes SoC.
- TOF can remain in low-power mode; target-distance interrupt reaches MCU, then MCU wakes SoC.
- MCU wakes SSC305 by driving SoC `RTC_IO1`.
- MCU can wake itself by timer and then wake SoC for scheduled work.

Power-off behavior is a hardware/software contract:

- User switch controls the main MOSFET path and is also visible to MCU IO.
- Switch ON pulls the main MOSFET gate low through diode logic, powering `Vsys` and starting MCU.
- MCU holds the main MOSFET gate low while switch status is ON, so moving switch OFF does not instantly drop power.
- On switch OFF, MCU detects the state, asks SoC to shut down, waits for response or timeout, then releases MOSFET hold.
- This sequence still needs board-level waveform validation when used to prove shutdown correctness.

Low-power SDIO leakage mitigation from the system block:

- Wi-Fi module provides an SDIO disable signal named `SDIO_ENB`.
- When Wi-Fi enters keepalive, MCU disables SDIO through `SDIO_ENB`; Wi-Fi SDIO becomes high impedance to avoid leakage into SoC.
- When Wi-Fi exits keepalive, MCU must release SDIO disable before powering/enabling SoC, otherwise SoC may not control Wi-Fi through SDIO.
- Production-test behavior for `SDIO_ENB` was marked pending in the source diagram.

## Power tree summary

Input and battery:

- Adapter input: 5V / 2A.
- Battery: 7.4V / 2500mAh.
- Fuel gauge: `CW2217BAAD`.
- Charge management: `SC8922QDLR`.
- Main switched system rail range: 6V to 8.4V through main switch MOSFET path.

Power-control sequencing from the power tree:

- After `IO0` is pulled high for 2ms, `IO4` and `IO5` output high together.
- In AOV mode, `IO4` goes low while `IO5` stays high.
- `IO4` and `IO5` gate several rail enables, so firmware and MCU sequencing must be checked against this relationship before changing low-power behavior.

Rail and load index:

| Rail / supply | Type / source | Main loads noted in PDF | Current hints from PDF |
| --- | --- | --- | --- |
| 6V to 8.4V system path | battery/adapter through switch MOSFET | motor driver board, high-power DCDC rails, LED/IR paths, audio amp, 5V DCDC | system input range |
| `3V3_RTC` | DCDC | SoC RTC, MCU, light sensor, IR receiver/detector domain, selected low-power devices | 740mA hint in power tree; schematic sheet says 2A rail |
| `1V8_RTC` | LDO/DCDC area | Wi-Fi and selected low-power logic | 510mA Wi-Fi hint; schematic sheet says 0.5A rail |
| `0V9` / SoC core | DCDC | SoC core | 600mA hint in power tree; schematic sheet says `VDD_Core` 0.9V/2A |
| `1V5` | DCDC | DDR-related supply | 600mA hint in power tree; schematic sheet has DDR power 1.5V/2A |
| `1V8` | DCDC | standard SoC/peripheral IO | 120mA hint in power tree; schematic sheet has `1V8_STD` 2A |
| `0V8` | DCDC/LDO | `DVDD_NODIE` style SoC bottom/core rail | 8mA hint in power tree; schematic sheet has 0.8V/0.5A |
| `3V3_STD` | MOS-gated / DCDC area | TF, LCD, MIC support, standard peripherals | TF 80mA, LCD 60mA, MIC 1mA hints |
| `3V3_NOR` | DCDC | Flash domain | Flash 40mA hint |
| `5V` | DCDC | audio amp, laser/IR driver paths, LED constant-current drivers | audio amp 450mA, laser 30mA, IR LED path 800mA, LCD backlight 80mA hints |
| Camera local rails | LDOs | Camera + IR-CUT | 1V5 70mA, 1V8 2mA, 2V8 25mA hints |
| `3V3_IR` / `3V3_IRdet` | MCU-IO gated MOS | IR receiver x5, IR distance sensing | IR receiver 10mA, IR distance 60mA hints |

Peripheral current hints from the diagram:

- TOF: 65mA.
- IMU: 2mA.
- MCU: 60mA.
- Light sensor: 13uA.
- Speaker path: 4 ohm / 2W through audio amp.
- Brushless motor driver board uses the 6V to 8.4V path directly.

These current values are design-reference hints from the power-tree PDF, not measured board evidence.

## Main schematic page index

The main schematic PDF has 20 sheets. The text layer and title blocks expose the following reusable index:

| Sheet | Title / topic | Key searchable signals and devices |
| ---: | --- | --- |
| 1 | cover / blank coordinate sheet | no useful net-level text extracted |
| 2 | Power Diagram | high-level power diagram title only |
| 3 | `POWERR System` / power system | `VCC_SYS`, `VCC_5V`, `V_DCIN`, `BATT_DCIN`, `SC8922`, `CHARGING_DET`, `MCU_EN_CHARGE`, `I_CHARGE_SET`, `KEY_PWRON_KEEP`, `PWR_KEY`, `3V3_RTC`, `1V8_RTC`, `3V3_NOR`, `3V3_STD`, `1V8_STD`, `DDR_IO_POWER_1V5`, `DVDD_NODIE`, `VDD_Core`, `DVDD_DDR_RX/TX` |
| 4 | SSC305 core / RTC / clocks / reset | `SSC305`, `PAD_RTC_IO0/1/4/5`, `PAD_PM_RESET`, `PAD_RESET`, `XTAL_24M_IN/OUT`, `S_XTAL_IN_32K`, `S_XTAL_OUT_32K`, `AVDD33_RTC`, `AVDDIO_DRAM`, `DVDD_NODIE`, `DVDD_DDR` |
| 5 | SSC305 audio pad group | `PAD_AUD_LINEOUT_R0`, `PAD_AUD_MICIN0/1`, `MIC_IN0/1`, `CODED_AOR`, `AVDD18_AUD`, `1V8_STD` |
| 6 | SSC305 MIPI/I2C pad group | `MIPI_CSI_MCLK`, `MIPI_CSI_RST`, `MIPI_CSI_I2C1_SCL/SDA`, `MIPI_CSI_RX_D0..D3`, `MIPI_CSI_RX_CLK0`, `IMU_I2C_SCL/SDA`, `BT_WAKE_HOST` |
| 7 | USB/ETH/DEBUG pad group | `USB20_HOST1_DP/DM`, `DEBUG_UART_TX/RX`, `ETH_RP/RN/TP/TN`, `AVDD18_USB`, `AVDD33_USB`, `AVDD18_ETH`, `AVDD33_ETH` |
| 8 | SSC305 GPIO/PM/mux pad group | `MCU_UART_TX/RX`, `WIFI_WAKE_HOST`, `SOC_WIFI_REG_ON`, `SOC_BT_REG_ON`, `LCD_BL_PWM`, `IR_BL_PWM`, `LASER_PWREN_H`, `TOF_I2C0_SCL/SDA`, `TOF-SYNC`, `SDMMC0_*`, `S-SPI_*`, `S-MSPI0/1_*`, `BT_*_SOC`, `PDM_*`, `SPK_SHDN` |
| 9 | NAND Flash | `NAND FLASH`, `ZB35Q04BYIG`, `S-SPI_CK/CS/DI/DO/HLO/WP`, `BOOT STRAPPING`, `VDDP33_18` |
| 10 | AUDIO | `NS4150B`, `AUDIO_OUT`, `SPK1_P/N`, `SPK_SHDN`, `MIC_IN0/1`, `PDM_CLK1_M1`, `PDM_SDI1_M1`, `VCC_5V`, `VDD_DMIC` |
| 11 | Camera | `CAMERA`, `MIPI_CSI_*`, `CAM_CSI_I2C1_SCL/SDA`, `CSI_MCLK`, `CSI_RST`, `IRCUT_AIN/BIN`, `VCC1V5_DVP`, `VCC1V8_DVP`, `VCC2V8_DVP`, `ETA5050V15/18/28`, `MS3111S` |
| 12 | IMU | `QMI8658B`, `IMU_I2C_SCL/SDA`, `IMU_INT`, `IMU_1V8`, `VCC3V3_MCU`, `1V8_RTC`, `1V8_STD` |
| 13 | IR receiver / IR detect | `IR-RX_1/2/3`, `IR_DET_ADC`, `IR_DET_PWR_EN`, `IR_PWR_EN`, `PWM_IR_23K`, `VCC3V3_IR`, `3V3_IR_DET`, `LM358`, `PT26-51B`, `IR26-51C` |
| 14 | MCU | `GD32L235CBT6`, `MCU_WAKEUP`, `MCU_UART_TX/RX`, `PAD_RTC_IO1`, `KEY_PWRON_KEEP`, `KEY_STATUS_DET`, `MCU_EN_CHARGE`, `CHARGING_DET`, `GAUGE_I2C_SCL/SDA`, `GAUGE_INT`, `IMU_INT`, `TOF-INT`, `WIFI_INT_1`, `MCU_WIFI_REG_ON`, `M1/M2_MOTOR_TX/RX`, `M1/M2_NTC`, `IR-RX_1..5`, `IR_DET_ADC`, `I_CHARGE_SET`, `SWDIO`, `SWCLK` |
| 15 | MicroSD Card | `SDMMC0_D0..D3`, `SDMMC0_CMD`, `SDMMC0_CLK`, `SDMMC0_DET_L`, `VDD_SD`, `VCC3V3_MCU`, `PWR_KEY`, `KEY_PWR_ON`, `MCU_KEY_RST` |
| 16 | LCD / backlight | `LCD_BL_PWM`, `LCD_DC_1`, `LCD_DC_2`, `LCD_RST`, `M_RST`, `S-MSPI1_CK`, `S-MSPI1_DO`, `S-MSPI1_CS`, `S-MSPI0_CS`, `VLCD_3V3`, `VCC_LCD`, `VCC_LEDA`, `VCC_LEDK`, `ETA2863H`, `ZH128X15842A` |
| 17 | MOTO Drive | `M1_MOTOR_TX/RX`, `M2_MOTOR_TX/RX`, `M1_NTC`, `M2_NTC`, `VDD_M1`, `VDD_M2`, `VCC_SYS`, `VBAT`, `MOTORDRV` |
| 18 | TOF/LASER | `TOF_SCL/SDA`, `TOF_INT`, `TOF_SYNC`, `TOF_I2C0_SCL/SDA`, `IR-RX_4/5`, `IR_LED+/-`, `IR_BL_PWM`, `LASER_5V0`, `LASER_PWREN_H`, `LDR-A`, `VCC3V3_IR`, `3V3_TOF`, `1V8_TOF`, `VCC_5V`, `VCC_SYS` |
| 19 | Wi-Fi / BT | `AP6303BH`, `WIFI_SDIO_CMD/CLK/D0..D3`, `SOC_WIFI_REG_ON`, `MCU_WIFI_REG_ON`, `WIFI_WAKE_HOST`, `WIFI_WAKE_MCU`, `BT_WAKE_HOST`, `BT_RX/TX/CTS/RTS`, `BT_*_SOC`, `BT_REG_ON`, `SOC_BT_REG_ON`, `WL_GPIO4`, `WIFI_1V8`, `VCC3V3_WIFI`, `WIFI_LPO`, `XTAL_37M4_IN/OUT`, `ANT0/ANT1` |
| 20 | Fuel gauge | `CW2217BAAD`, `VDD_GAUGE`, `GAUGE_I2C_SCL/SDA`, `GAUGE_INT`, `BAT_NTC`, `VBAT+`, `VBAT-`, `ETA5041`, `VCELL`, `INT_N` |

## Software-facing hardware contracts

Use these as starting points for driver, device-tree, MCU firmware, and diagnostic work:

| Contract | Hardware evidence | Software implication |
| --- | --- | --- |
| SoC wake by MCU | system block and schematic show MCU waking SSC305 through `RTC_IO1` / `PAD_RTC_IO1` | MCU firmware and Linux suspend/resume paths must agree on wake polarity, pulse width, debounce, and ACK timing |
| Switch power-off is sequenced, not instant | switch connects to main MOSFET path and MCU IO; MCU releases MOSFET hold after SoC response or timeout | shutdown code should expose request, SoC ACK, timeout, and hold-release telemetry; board waveform proof is still required |
| Wi-Fi low-power leakage is controlled by SDIO disable | system block documents `SDIO_ENB`; Wi-Fi page exposes AP6303BH SDIO and wake/reg-on nets | keepalive/resume sequencing must release SDIO disable before SoC expects SDIO control |
| AP6303BH has both SoC and MCU control paths | Wi-Fi sheet includes `SOC_WIFI_REG_ON`, `MCU_WIFI_REG_ON`, `WIFI_WAKE_HOST`, `WIFI_WAKE_MCU` | avoid treating Wi-Fi as SoC-only; MCU low-power path can affect Wi-Fi attach/detach and wake behavior |
| IMU and TOF are wake sources through MCU | system block and MCU sheet expose `IMU_INT`, `TOF-INT`, `MCU_WAKEUP` | low-power validation must include interrupt propagation into MCU and then SoC wake |
| LCDs are SPI-style panels | LCD sheet exposes `S-MSPI1_CK`, `S-MSPI1_DO`, `S-MSPI1_CS`, `S-MSPI0_CS`, `LCD_DC_1/2`, `LCD_RST`, `LCD_BL_PWM`; no TE/VSYNC/HSYNC/DCLK/DE was found in extracted schematic text | display stack should be treated as SPI/fbtft-style small panels, not MI_DISP scan-output panels, unless later hardware evidence says otherwise |
| Camera is MIPI CSI with local rails and IR-CUT | camera sheet exposes `MIPI_CSI_*`, camera I2C, 1V5/1V8/2V8 rails, `IRCUT_AIN/BIN` | camera bring-up should validate rail enable timing, reset, MCLK, I2C, MIPI lane mapping, and IR-CUT control separately |
| Audio output uses 5V amp path | audio sheet includes `NS4150B`, `VCC_5V`, `SPK_SHDN`, `SPK1_P/N`; SoC audio pins expose MIC and lineout/PDM nets | speaker pop/noise and low-power leakage diagnosis should include amp shutdown and 5V rail behavior |
| NAND Flash is SPI-style boot/storage device | NAND sheet exposes `ZB35Q04BYIG` and `S-SPI_*` nets | flash read-path issues must consider SPI/NAND electrical and timing margins, not only filesystem symptoms |
| Fuel gauge is MCU-visible over I2C | fuel gauge sheet exposes `CW2217BAAD`, `GAUGE_I2C_SCL/SDA`, `GAUGE_INT`, `BAT_NTC` | battery initialization or gauge polling should remain nonblocking in MCU runtime, especially around watchdog and power sequencing |

## Cross-reference to existing PCR02 decisions

This note supports, but does not supersede, these existing Hub facts:

- `hardware-power/pcr02_power_hold_shutdown_path_20260606.md`: power hold and shutdown path remains hardware-verification pending.
- `runtime-io/pcr02_gd32l235_uart_watchdog_nonblocking_20260612.md`: MCU main-loop, UART ACK, gauge/battery work, and watchdog interactions must stay nonblocking.
- `boot-flash/pcr02_spi0_pad_drive_8ma_riu_verification_20260618.md` and `ubifs-squashfs/pcr02_customer_squashfs_overlay_flash_read_20260606.md`: flash/read instability must still be validated through board evidence; this schematic index only identifies relevant rails and SPI/NAND nets.
- `decisions/st77912-dual-screen-spi-clock-fps-decision-20260711.md`: LCD hardware evidence is SPI-style dual small-panel control from the main schematic.

## Search keywords

Recommended query terms for future retrieval:

`PCR02 EVT2`, `系统框图`, `电源树`, `PCR02_MAIN_V2.0`, `SSC305`, `GD32L235CBT6`, `CW2217BAAD`, `SC8922QDLR`, `AP6303BH`, `QMI8658B`, `ZB35Q04BYIG`, `SDIO_ENB`, `RTC_IO1`, `PAD_RTC_IO1`, `KEY_PWRON_KEEP`, `PWR_KEY`, `MCU_WAKEUP`, `MCU_WIFI_REG_ON`, `SOC_WIFI_REG_ON`, `WIFI_WAKE_MCU`, `WIFI_WAKE_HOST`, `TOF_INT`, `IMU_INT`, `LCD_BL_PWM`, `S-MSPI1_CK`, `LASER_PWREN_H`, `GAUGE_I2C_SCL`, `GAUGE_I2C_SDA`.

## Limits and remaining work

- This index is derived from PDF text extraction and selective visual checks. It is suitable for retrieval and engineering triage, but exact net-level decisions still require opening the source PDF page.
- The source PDFs are design documents dated 2025-12-01 and 2025-12-11. Confirm against actual PCB revision, BOM, and board rework before treating any rail, load, or signal as final hardware truth.
- The power tree current hints are not measured values.
- Shutdown, wake, SDIO leakage, camera rail timing, LCD SPI timing, flash read stability, and fuel-gauge runtime behavior still require board-level validation when they are used as acceptance criteria.
- No source project files, live memory, or active decisions were modified by this archive note.

## Archive evidence

- Source: three local PCR02 EVT2 hardware PDFs listed above.
- Topic: PCR02 hardware reference / source audit / power architecture.
- Archive path: `projects/pcr02-ssc305/archive/engineering-archive/pcr02/source-audit/pcr02_evt2_hardware_pdf_reference_index_20260711.md`.
- Sanitization: no secrets, credentials, raw binary bodies, or complete PDF reproduction; only extracted engineering facts and source hashes.
- Provenance: local PDF metadata and SHA256; text extracted with `pdftotext`; page imagery checked with `pdftoppm`.
- Verification: `rtk pdfinfo`, `rtk sha256sum`, `rtk pdftotext -layout`, targeted PDF text cross-checks for wake/power/SDIO/rail/schematic-page signals, `rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 EVT2 MCU SoC 协同" --json`, `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics`, and `rtk git -C ~/knowledge-hub diff --check`.
- Memory candidate: no direct memory write; this note should be retrieved from Knowledge Hub.
- Gate result: pass for archive registration and Hub consistency as of 2026-07-11; board-level validation remains out of scope.
