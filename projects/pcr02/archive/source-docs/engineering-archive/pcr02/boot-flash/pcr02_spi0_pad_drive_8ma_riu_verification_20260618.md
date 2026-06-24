# PCR02 SPI0 pad drive RIU verification

Date: 2026-06-18

Status: current evidence note.

Source: PCR02 SSC305 flash-read troubleshooting session, `SSC30XXE_QFN128_HW_Checklist_V1.9_202502522.xlsx`, and board-side `riu_r` verification provided on 2026-06-18.

Scope: This note records SoC SPI0 boot-flash pad drive register mapping, software write behavior, board-side readback, and remaining risks. It does not claim that pad drive is the root cause of `/customer` SquashFS read instability.

Update 2026-06-18: after the 8mA readback was verified, the active software trial was changed to SoC SPI0 six-line 4mA while keeping MX35LF4GE4AD max_clk at 54MHz.

Update 2026-06-18 later: six-line 4mA improved the flash-read issue but did not eliminate it. The current software baseline is therefore fixed to CK 2mA and IO 4mA for the next validation round.

## Background

During PCR02 `/customer` SquashFS read-path investigation, an early electrical trial baseline was:

```text
SoC SPI0 six-line drive strength = 8mA
MX35LF4GE4AD max_clk             = 54MHz
```

Earlier boot logs still showed:

```text
SPI0 pad drive setup failed
```

Later instrumentation split the return mask and showed data pins failing first while CK passed:

```text
SPI0 pad drive setup failed
SPI0 pad drive fail: DO
SPI0 pad drive fail: DI
SPI0 pad drive fail: HLD
SPI0 pad drive fail: WPZ
SPI0 pad drive fail: CZ
SPI 54M
```

The immediate software issue was not that RIU was unwritable. Board-side `riu_r`/`riu_w` showed RIU registers could be written and read back correctly, for example:

```sh
/customer/riu_r 103e 28
/customer/riu_w 103e 28 654
/customer/riu_r 103e 28
```

## Register Addressing Conclusion

The checklist lists some drive bits with adjacent register labels, for example:

```text
PAD_SPI0_DO: bit0 reg[103E46]#7, bit1 reg[103E47]#8
PAD_SPI0_CK: bit0 reg[103E50]#7, bit1 reg[103E51]#8, bit2 reg[103E51]#10
```

In the SigmaStar driver, `HAL_GPIO_RIU_REG(addr)` accesses a 16-bit RIU word:

```c
#define HAL_GPIO_RIU_REG(addr) (*(volatile u16 *)(gRIUBaseAddr + (addr << 1)))
```

Therefore, the paired odd register label in the checklist should not be treated as a separate `HAL_GPIO_RIU_REG(odd)` word for this use case. The effective access pattern is:

```text
riu_r 103e 23 -> HAL_GPIO_RIU_REG(0x103E46)
riu_r 103e 24 -> HAL_GPIO_RIU_REG(0x103E48)
riu_r 103e 25 -> HAL_GPIO_RIU_REG(0x103E4A)
riu_r 103e 26 -> HAL_GPIO_RIU_REG(0x103E4C)
riu_r 103e 27 -> HAL_GPIO_RIU_REG(0x103E4E)
riu_r 103e 28 -> HAL_GPIO_RIU_REG(0x103E50)
```

The corrected 8mA software implementation set:

```text
DO/DI/HLD/WPZ/CZ 8mA: bit8:7 = 01
CK 8mA:              bit10:8:7 = 0:1:1
```

## Board-Side Verification

After the corrected implementation, board-side readback was:

```text
/customer/riu_r 103e 23
BANK:0x103E 16bit-offset 0x23
0x0AD4

/customer/riu_r 103e 24
BANK:0x103E 16bit-offset 0x24
0x0AE4

/customer/riu_r 103e 25
BANK:0x103E 16bit-offset 0x25
0x0AD5

/customer/riu_r 103e 26
BANK:0x103E 16bit-offset 0x26
0x0AD5

/customer/riu_r 103e 27
BANK:0x103E 16bit-offset 0x27
0x0AD5

/customer/riu_r 103e 28
BANK:0x103E 16bit-offset 0x28
0x03D4
```

Interpretation:

```text
DO  0x0AD4: bit8:7 = 01 -> 8mA
DI  0x0AE4: bit8:7 = 01 -> 8mA
HLD 0x0AD5: bit8:7 = 01 -> 8mA
WPZ 0x0AD5: bit8:7 = 01 -> 8mA
CZ  0x0AD5: bit8:7 = 01 -> 8mA
CK  0x03D4: bit10:8:7 = 0:1:1 -> 8mA
```

This verifies that the software-visible RIU drive fields were set to 8mA for the first trial. The next software trial changed both CLK and IO to 4mA:

```text
DO/DI/HLD/WPZ/CZ 4mA: bit8:7 = 00
CK 4mA:              bit10:8:7 = 0:0:1
```

That six-line 4mA trial improved the observed flash-read behavior but still reproduced flash-read failures. The current software baseline changes only CK one step lower while keeping IO at 4mA:

```text
DO/DI/HLD/WPZ/CZ 4mA: bit8:7 = 00
CK 2mA:              bit10:8:7 = 0:0:0
```

Expected board-side readback for the current CK 2mA / IO 4mA baseline:

```text
/customer/riu_r 103e 23 -> 0x0A54
/customer/riu_r 103e 24 -> 0x0A64
/customer/riu_r 103e 25 -> 0x0A55
/customer/riu_r 103e 26 -> 0x0A55
/customer/riu_r 103e 27 -> 0x0A55
/customer/riu_r 103e 28 -> 0x0254
```

## Current Conclusion

Current conclusion:

1. The earlier `SPI0 pad drive setup failed` was caused by incorrect software access/check logic, not by a locked RIU register.
2. The corrected RIU addressing logic was verified with an 8mA readback trial.
3. The six-line 4mA trial improved but did not eliminate flash-read failures.
4. The current software baseline sets SPI0 CK to 2mA and DO/DI/HLD/WPZ/CZ to 4mA.
5. This proves register-level write/read behavior, but does not prove the physical pad output waveform changed.
6. If measured waveform still looks like the previous 12mA state, the next investigation should focus on whether the active FSP/QSPI boot-flash function path uses a different controller or PAD-to-C drive control path.

## Recommended Follow-Up

Use runtime `riu_w` for an extreme A/B waveform check instead of comparing only 12mA and 8mA:

```sh
# CK 8mA, preserving observed non-drive bits from 0x03D4.
/customer/riu_w 103e 28 3d4
/customer/riu_r 103e 28

# CK 2mA: clear bit10, bit8, bit7 while preserving other observed bits.
/customer/riu_w 103e 28 254
/customer/riu_r 103e 28

# CK 16mA: set bit10, bit8, bit7 while preserving other observed bits.
/customer/riu_w 103e 28 7d4
/customer/riu_r 103e 28
```

If 2mA, 8mA, and 16mA produce no meaningful waveform difference, stop iterating on `103E46/48/4A/4C/4E/50` as the primary pad-drive control and ask BSP/vendor to confirm whether SSC305/iford boot SPI0 in FSP/QSPI mode uses another drive-control path.

## Relation To Flash Read Issue

This note does not close the low-probability `/customer` SquashFS read issue. Current flash-read evidence still points to read-path inconsistency below SquashFS/ubiblock, including possible BDMA/cache/FSP/QSPI/ECC factors. The CK 2mA / IO 4mA pad-drive setting is the current electrical baseline after the six-line 4mA trial showed improvement but not full resolution.

Related notes:

- `pcr02_spinand_read_path_bdma_riu_20260529.md`
- `../ubifs-squashfs/pcr02_customer_squashfs_overlay_flash_read_20260606.md`
- `../ubifs-squashfs/pcr02_customer_squashfs_libmsc_errno5_20260617.md`
