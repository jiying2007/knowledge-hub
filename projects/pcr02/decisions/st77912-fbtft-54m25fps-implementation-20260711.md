# PCR02 ST77912 fbtft 54MHz/25fps implementation note

Date: 2026-07-11
Project: PCR02 SigmaStar SSC305
Repo: PCR02 SSC305 SDK compile root

## Scope

Implemented the kernel-side part of the dual ST77912 display optimization in the SDK compile root.

## Changes

- `SourceCode/kernel/arch/arm/boot/dts/iford.dtsi`
  - `st77912@0` and `st77912@1` now use `spi-max-frequency = <54000000>;`
  - `st77912@0` and `st77912@1` now use `fps =<25>;`
- `SourceCode/kernel/drivers/staging/fbtft/fbtft-core.c`
  - `fbdefio->delay` now uses `max_t(..., 1, DIV_ROUND_CLOSEST(HZ, fps))`, avoiding zero/under-rounded deferred delay.
  - Per-refresh timing in `fbtft_update_display()` is now debug-gated instead of always enabled.
  - `fbtft_mkdirty()` clamps dirty line ranges to valid screen bounds.
  - `fbtft_deferred_io()` skips update when the dirty range is empty instead of falling through to full-screen update.
  - Resume refresh now uses `par->info->var.yres - 1` instead of hardcoded `239`.
- `SourceCode/kernel/drivers/sstar/mspi/drv_mspi.c`
  - 2026-07-13 update: MSPI group 0 probe now explicitly sets `PAD_MSPI_CK` drive level to `0`, the lowest supported drive setting for the LCD SPI clock pad.
  - `PAD_MSPI_CK` is a 2-bit drive field: `(00)=4mA`, `(01)=8mA`, `(10)=12mA`, `(11)=16mA`.
  - Later 2026-07-13 waveform evidence showed the measured LCD SPI clock changes when the `PAD_SPI0_CK` 3-bit drive field at `0x103E/0x28` is adjusted. Therefore the earlier `PAD_MSPI_CK`-only assumption is not sufficient for PCR02 board validation.
  - MSPI/fbtft remains the logical LCD controller path; this does not mean the LCD and SPI-NAND boot flash share the same SPI controller. It means the board-level clock waveform validation must distinguish controller identity from the physical PAD drive field.
- `SourceCode/kernel/drivers/sstar/gpio/iford/hal_gpio.c`
  - 2026-07-13 update: `hal_gpio_spi0_drv_set()` now clears `PAD_SPI0_CK` drive bits `BIT7 | BIT8 | BIT10` in `HAL_GPIO_RIU_REG(0x103E50)`, matching runtime `/customer/riu_w 0x103E 0x28 0x0254` for `2mA`.
- `SourceCode/boot/drivers/sstar/gpio/iford/hal_gpio.c`
  - U-Boot side mirrors the kernel `PAD_SPI0_CK = 2mA` setup so early boot and kernel runtime do not use different CK drive settings.
- `SourceCode/kernel/drivers/sstar/fsp_qspi/hal/iford/hal_fsp_qspi.c`
- `SourceCode/boot/drivers/sstar/fsp_qspi/hal/iford/hal_fsp_qspi.c`
  - Success log now reports `SPI0 CK pad drive: 2mA` instead of `SPI0 pad drive: default`.

## Validation

- Command:
  `rtk ./build.sh kernel --profile ap6303bh_512m_v20_debug_customer --allow-dirty --no-clean --no-copy-nfs`
- Result: exit code 0.
- Evidence:
  - `drivers/staging/fbtft/fbtft-core.o` compiled.
  - `drivers/sstar/mspi/drv_mspi.o` compiled.
  - `drivers/sstar/gpio/iford/hal_gpio.o` compiled.
  - `drivers/sstar/fsp_qspi/hal/iford/hal_fsp_qspi.o` compiled.
  - `arch/arm/boot/dts/iford-ssc029a-s01b.dtb` generated.
  - `arch/arm/boot/uImage` generated.
  - DTB decompile confirmed both ST77912 nodes have `spi-max-frequency = <0x337f980>` and `fps = <0x19>`.
  - DTB decompile confirmed both ST77912 nodes are under `compatible = "sstar,mspi"` with `mspi-group = <0x00>`.
- Command:
  `rtk make -C SourceCode/project/board/uboot -f uboot.mk boot PROJ_ROOT=<PCR02_SOURCE_ROOT>/SourceCode/project`
- Result: exit code 0.
- Evidence:
  - U-Boot build regenerated `SourceCode/boot/u-boot`.
  - `strings SourceCode/boot/u-boot | rg 'SPI0.*pad drive|2mA'` includes `SPI0 CK pad drive: 2mA`.
  - `strings SourceCode/kernel/vmlinux | rg 'SPI0.*pad drive|PAD_SPI0_CK|PAD_MSPI_CK'` includes `SPI0 CK pad drive: 2mA`, `PAD_MSPI_CK`, and `PAD_SPI0_CK`.

## Boundary

- This is still fbtft single-framebuffer deferred I/O, not SigmaStar `mi_fb` and not true FB pan/display double buffering.
- The app-side display provider code with staging/back buffer, dirty area merge, and dual-screen interleaving was not present under `SourceCode/sdk/verify/xcrz_sigmastar_demo/modules/sensor/display`; `pcr02/dep.mk` only conditionally includes that module if the directory exists.
- Therefore, app-side optimization must be applied in the actual application source tree that participates in the target image build before claiming full end-to-end display optimization.
- LCD pad-drive validation must read both candidate physical PAD drive fields:
  - `/customer/riu_r 0x103E 0x22` for `PAD_MSPI_CK`; bit7/bit8 clear means the 2-bit field is at its lowest supported `4mA` level.
  - `/customer/riu_r 0x103E 0x28` for `PAD_SPI0_CK`; bit7/bit8/bit10 clear means the 3-bit field is `000 = 2mA`, expected whole-word readback around `0x0254` if non-drive bits match the observed board baseline.
- Waveform evidence directory: `<LOCAL_EVIDENCE_ROOT>/20260713-SPI屏clk波形`. The screenshots support using `2mA` as the current electrical trial baseline, but they should be followed by an A/B readback test that changes only `0x103E/0x22` or only `0x103E/0x28` while probing the same LCD CLK point.

## Rollback

- Safe fallback clock/fps pair: revert DTS ST77912 nodes to `spi-max-frequency = <36000000>; fps =<25>;` or `fps =<20>;` if 54MHz fails aging or EMI validation.
- Driver dirty/deferred fixes are independent of the 54MHz risk and can remain unless they introduce a regression.
