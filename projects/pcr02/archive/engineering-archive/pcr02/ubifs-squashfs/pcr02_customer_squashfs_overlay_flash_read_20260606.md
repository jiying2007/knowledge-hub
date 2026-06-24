# PCR02 customer SquashFS、调试 overlay 与 Flash 读异常归档

日期：2026-06-06
更新：2026-06-15

状态：当前排障与发布决策记录。本文补充 2026-05-29 `/customer` SquashFS 迁移结论；不替代迁移发布指南，但修正“SquashFS 静态卷即可完全规避 customer 读异常”的风险判断。2026-06-15 更新后，Flash 侧 `E0h=80h` / 85ohm 输出驱动仅保留为历史试验记录，不再作为当前默认基线。

## Source

- 当前会话排障和实现记录，时间范围约 2026-06-03 至 2026-06-06。
- 后续会话修正记录，时间范围约 2026-06-10 至 2026-06-13：SPI0 pad drive、SNI clock、Flash 侧输出驱动变量和 regular OTA 分区保护边界。
- 设备侧复测摘要：`/customer` SquashFS 升级后多次重启大多正常，约 20 次 reboot 中偶发一次异常；异常时 `/dev/ubi0_3` 与 `/dev/ubiblock0_3` 的 hash 与正常值不一致，且异常 hash 每次不同。
- 仓库记录：`README.md` 已补充 24M 降频无效结论；boot/kernel FSP QSPI 强制 24M 限频补丁已移除。

## Sanitization

- 未归档完整串口日志、core dump、二进制文件或设备私有网络地址。
- 仅保留故障模式、命令形态、hash 现象、决策和后续排查方向。

## 当前有效发布与文件系统决策

### 生产版

- `/customer` 使用 SquashFS，挂载源为 `/dev/ubiblock0_3`。
- customer UBI volume 保持 `static`，用于只读资源和业务内容。
- 生产版不引入 overlay 写入层。

### 调试版

- 调试版不再使用 “customer 为 UBIFS” 的兼容路径。
- 调试版 `/customer` 使用 SquashFS lower + `/data/customer_overlay` 持久 overlay upper。
- `/customer_ro` 挂载只读 SquashFS lower，`/customer` 暴露 overlay 视图。
- `/customer/etc/version.ini` 作为 lower 版本哨兵；版本变化时归档旧 upper 并重建写入层，避免旧调试残留污染新版本。
- 调试版默认 NAS 发布路径为 `/mnt/mcu-release-nas/robot/soc/DVT/debug`。

### 发布流

- `migration`：用于旧生产布局到新布局的首次迁移，目标是支持 SD 卡升级与 OTA 都能完成 `/customer` SquashFS + `ubia` resize 迁移。
- `regular`：用于已经完成迁移后的常规升级，不应重建整个 `ubia`，特别是不升级 `/factory` 和 `/data`。
- `release-dual` 应同时产出生产版和调试版；二者需要在 manifest 中明确 `releaseFlow`、`releaseKind`、`productionAllowed` 和 customer 文件系统属性。
- 手动发布也需要遵守 migration/regular 的边界，不应绕过发布流语义。

## 故障现象

迁移到 `/customer` SquashFS 后，随机重启压力下仍出现低概率异常：

```text
SQUASHFS error: lzo decompression failed
SQUASHFS error: Failed to read block ...
SQUASHFS error: Unable to read page ...
```

异常时观察到：

- 正常启动时，`sha256sum /dev/ubi0_3` 与 `sha256sum /dev/ubiblock0_3` 稳定一致。
- 异常启动时，`/dev/ubi0_3` 与 `/dev/ubiblock0_3` 的 hash 均偏离正常值。
- 异常 hash 每次不同，不像固定镜像打包错误或固定坏块映射错误。
- 某些 `/customer` 资源文件可以 `ls -lh` 看到大小，但读取或计算 hash 会卡住或失败。

## 已验证结论

1. `customer` 使用 UBIFS 时曾出现异常，因此迁移到 SquashFS 是合理的可靠性收敛方向，但 SquashFS 不是当前问题的最终根因证明。
2. SquashFS 把问题从 “可写文件系统/UBIFS 元数据风险” 收敛为 “只读镜像读路径数据一致性风险”。
3. 异常时 `/dev/ubi0_3` 本身 hash 已变化，因此问题不局限于 `ubiblock` 缓存层或 SquashFS 解压层。
4. `/dev/ubi0_3` 与 `/dev/ubiblock0_3` 异常 hash 每次不同，更符合偶发读路径、供电/复位时序、ECC 上报、cache/DMA 或底层 NAND 时序类问题。
5. SPI NAND/FSP QSPI 降频到 24M 后仍可复现，不能通过单纯降低 Flash 时钟解决。
6. 不保留强制 24M 的 FSP QSPI 限频补丁；boot/kernel 侧 SPI NAND 时钟选择保持平台默认逻辑。

## 2026-06-06 SPI0 pad drive 验证补充

### 背景

硬件侧测得 SSC305 SPI0 六根线 SCLK、CS#、SI、SO、WP#、HOLD# 未串接匹配电阻，存在轻微过冲，Vpp 约 4V，接近 MX35LF4GE4AD NAND Flash 输入绝对最大值 4.6V。硬件判断默认 pad drive strength 偏大可能导致边沿过快和振铃过冲。

### 当前试验策略

- 将 SPI0 pad drive 降档作为优先试验项，boot 与 kernel 两侧都保持同一 drive strength 配置，避免进入 kernel 后重新初始化导致验证条件变化。SCLK 不再从 12mA 一次降到 6mA，当前按硬件建议调整为与 IO 相同的 8mA。
- 当前试验值：
  - SCLK / PAD_SPI0_CK / GPIO40：8mA，编码 `3'b011`。
  - DO / DI / HLD / WPZ / CZ，即 GPIO35/36/37/38/39：8mA，编码 `2'b01`。
- 硬件测量发现将 SNI `max_clk` 改为 48 后，SCLK 实测降为 24M。平台文档 `SGSDocs/sigdoc/platform/BSP/flash_zh.html` 列出的 Flash SNI CLK speed 支持档位为 54/86/104/108MHz，未列出 48M；因此 48M 不是当前 iford Flash SNI 已确认支持档位。早期尝试在 iford FSP/QSPI HAL 中增加 `HAL_CLKGEN_REG_CKG_SPI = 0x10` 的 48M 分支已证实会落到 24M，不能继续标记为 `SPI 48M`。
- 当前策略恢复为：`MX35LF4GE4AD.max_clk=54`，不保留 iford FSP/QSPI 的 48M 分支；若要验证低频，只能明确作为 24M 变量试验，且历史已经验证强制 24M 不能单独解决 `/customer` hash/SquashFS 偶发异常。
- MX35LF4GE4AD 规格书显示 Flash 侧输出驱动能力由 `E0h Configuration Register` 的 `DS_IO[1:0]` 控制：`00` 约 25ohm、`01` 约 35ohm、`1X` 约 85ohm。2026-06-10 后续会话明确修正：PCR02 当前默认基线不包含 Flash 侧 85ohm 输出驱动；`E0h=80h` 只保留为历史变量试验，不得写成 release 默认或长期规则。若后续重新验证 Flash 侧输出驱动，必须单独记录 `E0h` 读回、示波器波形、hash 循环和回退方式。
- 验证建议仍按变量分组执行：先记录 pad drive 降档 + 54M；若另行测试 24M，必须把结果标记为 24M 低频试验，不写成 48M。
- 板端读回发现 `devmem 0x1F207CA2 16 = 0x0000`，说明 `PAD_SPI0_CK` 的 DRV1/DRV2 不能按 `HAL_GPIO_RIU_REG(0x103E50)` 同一 16-bit word 的 `BIT8/BIT10` 处理；必须严格按 checklist 将 CK DRV0 写 `reg[103E50]#7`、DRV1/DRV2 写 `reg[103E51]#8/#10`，并清掉早期试验误写的 `reg[103E50]#10`。同理，GPIO35-39 的 IO drive 也按 `103E46/47`、`103E48/49`、`103E4A/4B`、`103E4C/4D`、`103E4E/4F` 分寄存器写入。
- 当前 active `flash_list.sni` 的 `MX35LF4GE4AD` 条目通过 `scripts/flash-sni.sh` 保持为 `max_clk=54`。后续解析或修改 SNI 时使用该工具，不再手工推导二进制偏移；除非另开试验并记录证据，不应把 `init_set=e0=80` 作为 active baseline。

### 2026-06-15 当前基线修正

- 当前 PCR02 SPI NAND 读稳定性试验基线：SoC SPI0 六线 drive strength 8mA + `MX35LF4GE4AD.max_clk=54`。
- 当前基线不包含 Flash 侧 85ohm 输出驱动；`E0h=80h` 只能作为历史试验或后续单独 A/B 变量。
- 54M 是当前平台资料确认的 SNI clock 档位；24M 低频试验已验证不能单独解决 `/customer` hash/SquashFS 偶发异常。
- 若后续再次调整 SNI 或 pad drive，归档必须同时记录工具读回、板端寄存器读回、示波器结果和重启/hash 循环结果。

### 平台文档依据

- `/vsdata/leiwenjun/SSC30XXE_QFN128_HW_Checklist_V1.9_202502522.xlsx`：
  - `IO Mapping`：SPI0 boot flash 六线对应 PIN57/58/59/60/61/64、GPIO35/36/37/38/39/40。其中 `IO Mapping` 行内 WPZ pad 名称写作 `PAD_SPIO_WPZ`，`GPIO_Ctrl_Reg_Table` 使用 `PAD_SPI0_WPZ`，两者按同一 SPI0 WP# 信号处理。
  - `GPIO_Ctrl_Reg_Table` R37-R41：`PAD_SPI0_DO/DI/HLD/WPZ/CZ` 为 2-bit driving，编码 `(00)=4mA`、`(01)=8mA`、`(10)=12mA`、`(11)=16mA`，默认 `2'b10`。
  - `GPIO_Ctrl_Reg_Table` R42：`PAD_SPI0_CK` 为 3-bit driving，编码 `(000)=2mA`、`(001)=4mA`、`(010)=6mA`、`(011)=8mA`、`(100)=10mA`、`(101)=12mA`、`(110)=14mA`、`(111)=16mA`，默认 `3'b101`。
  - `PAD_SPI0_CK` DRV 位为 `reg[103E50]#7`、`reg[103E51]#8`、`reg[103E51]#10`；代码必须分别访问 `HAL_GPIO_RIU_REG(0x103E50)` 和 `HAL_GPIO_RIU_REG(0x103E51)`，不能把 `103E51` 的位合并到 `103E50` 的 16-bit 访问中。
- `SGSDocs/sigdoc/platform/BSP/flash_zh.html`：Flash SNI CLK speed 支持档位为 54MHz、86MHz、104MHz、108MHz；Flash SNI CLK speed 说明调试时建议 54M，实际应用需根据 Flash 规格书确认。
- `SGSDocs/sigdoc/platform/RTOS/spi_zh.html`：SPI debug 章节说明 clock 速率过高时，例如超过 45M，可能出现异常，此时可以调 GPIO 驱动能力。
- `SourceCode/boot/drivers/sstar/fsp_qspi/hal/souffle/hal_fsp_qspi.c` 与 `SourceCode/boot/drivers/sstar/fsp_qspi/hal/infinity6f/hal_fsp_qspi.c`：同平台族 `rate >= 54` 分支使用 `HAL_CLKGEN_REG_CKG_SPI = 0x10`，但不能据此推断 iford 支持 48M；本板实测该档位会落到 24M。

### 代码状态

- U-Boot iford GPIO HAL 增加 SPI0 专用 drive strength 设置入口。
- Kernel iford GPIO HAL 同步增加 SPI0 专用 drive strength 设置入口，并导出 `sstar_gpio_spi0_drv_set()`。
- Boot 与 kernel 的 FSP/QSPI boot storage 初始化早期调用该入口，预期日志出现 `SPI0 pad drive: CK 8mA, IO 8mA`；该成功日志包含 SPI0 六线 drive 写后读回校验，读回不是 `PAD_SPI0_CK=3'b011` 或 IO=`2'b01` 时会打印 `SPI0 pad drive setup failed`。
- Boot 与 kernel 的 iford FSP/QSPI STR rate 路径不保留 48M 档位；请求低于 54M 的 SNI clock 时按平台原逻辑回退到 `SPI 54M`，避免误把实测 24M 标记为 48M。
- 新增 `scripts/flash-sni.sh` / `tools/flash_sni_tool.py`，用于列出 SNI 条目、按 partnumber 修改 `max_clk`、修改 SPI NAND init Feature Register，并刷新被修改条目的 `SNIF` CRC。
- 历史试验曾把 MX35LF4GE4AD SNI init 设置为 `SET FEATURE E0h=80h`。该变量已从当前基线剥离；若需切换变量，可用同一工具改为 `E0h=40h` 验证 35ohm，或改为 `E0h=00h` 恢复默认 25ohm，但必须作为单独试验闭环。
- 该补丁只用于验证 SoC pad drive 降档和 Flash 输出驱动降档是否改善过冲与读稳定性；不能单独作为硬件根因闭环证据。

### 验证要求

每组验证需同时记录：

- 示波器：SCLK、CS#、SI、SO、WP#、HOLD# 的 Vpp、过冲峰值、振铃持续时间和上升/下降沿。
- U-Boot / kernel 日志：确认 SPI0 pad drive 打印和实际 SPI clock 打印。
- SNI 工具读回：当前基线确认 `MX35LF4GE4AD` 为 `max_clk=54`、`crc=ok`；只有在重新执行 Flash 侧输出驱动 A/B 时，才额外记录 `init_set` 和板端 `GET FEATURE E0h` 读回。
- Linux 侧 RIU 读回：CK 需确认同寄存器 `devmem 0x1F207CA0 16` 的 bit7 为 1、bit8 为 1、bit10 为 0；IO 需确认同寄存器 `0x1F207C8C/90/94/98/9C` bit7 为 1 且 bit8 为 0。CK 若读到 `0x02D4`，说明 bit8 未置 1，仍不是目标 `3'b011`；IO 若读到 `0x0Bxx`，说明 bit7/bit8 同时为 1，IO 仍不是目标 `2'b01`。
- Linux 侧 hash：`sha256sum /dev/ubi0_3`、`sha256sum /dev/ubiblock0_3`、关键 `/customer` 资源文件 hash。
- `dmesg`：记录 `squashfs`、`ubi`、`ubiblock`、`ecc`、`nand`、`qspi` 相关错误。
- 重启或掉电循环：记录总次数、首次失败轮次和每次异常 hash。

## 代码与文档状态

- 已移除 boot 与 kernel 两侧 FSP QSPI 强制 24M 修改：
  - `SourceCode/boot/drivers/sstar/fsp_qspi/hal/iford/hal_fsp_qspi.c`
  - `SourceCode/kernel/drivers/sstar/fsp_qspi/hal/iford/hal_fsp_qspi.c`
- 已移除旧 `debug_customer_ubifs` 兼容语义，调试版改为 SquashFS + overlay。
- SPI0 pad drive 降档试验记录归档在本文，不写入 `README.md`。

## 后续排查方向

优先从以下方向继续收敛：

1. 读路径一致性：对比 UBI char device、ubiblock、SquashFS 文件读取的 hash 与错误位置。
2. ECC 状态：补充 NAND ECC corrected/failed 统计或驱动日志，确认异常启动期间是否有未上报纠错失败。
3. 供电与复位时序：重点验证低电量、reboot、快速开关机、Flash 上电稳定时间和 SoC 复位释放顺序。
4. cache/DMA/BDMA/RIU：在可控版本中对比不同读路径，确认是否存在 DMA cache coherency 或 QSPI/FSP 状态恢复问题。
5. UBI/ubiblock 映射：记录异常时 UBI attach 日志、volume 信息、PEB/LEB 映射和 `ubiblock` 创建时机。
6. 压力测试：使用 reboot 循环、全卷 hash、关键资源 hash、dmesg 错误抓取和电源扰动组合提高复现概率。

## 建议验证命令形态

设备侧可保留以下验证形态，具体路径按版本调整：

```sh
sha256sum /dev/ubi0_3
sha256sum /dev/ubiblock0_3
sha256sum /customer/bin/resource/msc/res/ivw/wakeupresource.jet
dmesg | grep -Ei 'squashfs|ubi|ubiblock|ecc|uncorrect|crc|mtd|nand|qspi'
mount
```

压力复现建议记录每轮：

- boot 次数和触发方式：`reboot`、断电、低电量恢复、SD 卡残留场景等。
- `/dev/ubi0_3` hash。
- `/dev/ubiblock0_3` hash。
- 第一个出现 `SQUASHFS error` 的 block offset。
- 关键资源文件 hash 是否可读。
- UBI attach 与 ubiblock 创建日志。

## Memory / AGENTS 候选

- 不建议把 “Flash 降频可解决问题” 写入长期规则；当前证据已否定。
- 不建议把 “Flash 侧 85ohm 输出驱动是当前默认基线” 写入长期规则；该变量已降级为历史试验。
- 可以作为项目级经验候选：PCR02 `/customer` 的 SquashFS 迁移降低了 UBIFS 写入面风险，但仍需对 SPI NAND 读路径一致性做独立验证；随机 hash 变化时优先看底层读路径和复位/供电，而不是只看文件系统格式。

## Quality Gate

- Source：当前会话与仓库 README 记录。
- Topic：ubifs-squashfs / boot-flash / ota-release。
- Archive Candidate Path：`archive/pcr02/ubifs-squashfs/pcr02_customer_squashfs_overlay_flash_read_20260606.md`。
- Sanitization：pass，未包含完整日志、设备私有地址、core dump 或密钥。
- Provenance：设备侧复测摘要 + 仓库改动状态。
- Verification：host 侧已做关键词检查和脚本语法检查；板端后续仍需继续复现和底层读路径验证。
- Memory Candidate：yes，需人工审查后再提升。
- Gate Result：pass。
