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

## Validation

- Command:
  `rtk ./build.sh kernel --profile ap6303bh_512m_v20_debug_customer --allow-dirty --no-clean --no-copy-nfs`
- Result: exit code 0.
- Evidence:
  - `drivers/staging/fbtft/fbtft-core.o` compiled.
  - `arch/arm/boot/dts/iford-ssc029a-s01b.dtb` generated.
  - `arch/arm/boot/uImage` generated.
  - DTB decompile confirmed both ST77912 nodes have `spi-max-frequency = <0x337f980>` and `fps = <0x19>`.

## Boundary

- This is still fbtft single-framebuffer deferred I/O, not SigmaStar `mi_fb` and not true FB pan/display double buffering.
- The app-side display provider code with staging/back buffer, dirty area merge, and dual-screen interleaving was not present under `SourceCode/sdk/verify/xcrz_sigmastar_demo/modules/sensor/display`; `pcr02/dep.mk` only conditionally includes that module if the directory exists.
- Therefore, app-side optimization must be applied in the actual application source tree that participates in the target image build before claiming full end-to-end display optimization.

## Rollback

- Safe fallback clock/fps pair: revert DTS ST77912 nodes to `spi-max-frequency = <36000000>; fps =<25>;` or `fps =<20>;` if 54MHz fails aging or EMI validation.
- Driver dirty/deferred fixes are independent of the 54MHz risk and can remain unless they introduce a regression.
