---
title: SigmaStar 平台主题索引目录
doc_type: standard
knowledge_type: guideline
maturity: verified
status: archived
searchable: false
owner: team-core
created: 2026-05-15
last_updated: 2026-05-15
tags: [sigmastar, topic-catalog, indexing]
related: [../architecture/sigmastar-platform-internal-overview.md, ../architecture/sigmastar-platform-capability-matrix.md, ../runbooks/sigmastar-platform-development-workflow.md]
validation_refs: [docs/archive/sigmastar/manifest.csv, examples/sigmastar]
---

# SigmaStar 平台主题索引目录

## 1. 目标

- 为后续 Codex 检索提供统一主题目录。
- 将平台资料映射为“技术域 + 主题 ID + 路径”三元组。
- 本文仅作为内部索引，不承载外部文档原文。

## 2. 使用方式

1. 先按“平台 + 技术域”定位候选主题。
2. 再根据 `内部主题 ID` 在代码与配置中做定向检索。
3. 涉及跨平台迁移时，优先查找同名/同域主题对照。

## 3. SSC305 主题清单（115）

| 技术域 | 内部主题 ID | 主题名称 | 路径 |
| --- | --- | --- | --- |
| customer/Common/Development | customer.Common.Development.Memory_layout_zh | Memory layout参考 | customer/Common/Development/Memory_layout_zh.html |
| customer/Common/Development | customer.Common.Development.SDK_Directory_Guide_zh | SDK目录说明 | customer/Common/Development/SDK_Directory_Guide_zh.html |
| customer/Common/Development | customer.Common.Development.SOC_power_scheme_zh | SOC外挂MCU电源控制 | customer/Common/Development/SOC_power_scheme_zh.html |
| customer/Common/Development | customer.Common.Development.STR_Time_consuming_Guide_zh | STR各阶段耗时DEBUG指南 | customer/Common/Development/STR_Time_consuming_Guide_zh.html |
| customer/Common/Development | customer.Common.Development.Security_Boot_manual_zh | SecurityBoot手动签章使用指南 | customer/Common/Development/Security_Boot_manual_zh.html |
| customer/Common/Development | customer.Common.Development.Security_Boot_zh | SecurityBoot使用参考 | customer/Common/Development/Security_Boot_zh.html |
| customer/Common/Development | customer.Common.Development.Sensor_Porting_Guide_zh | Sensor移植指南 | customer/Common/Development/Sensor_Porting_Guide_zh.html |
| customer/Common/Development | customer.Common.Development.UVC-Usage-Guide_zh | UVC使用指南 | customer/Common/Development/UVC-Usage-Guide_zh.html |
| customer/Common/Development | customer.Common.Development.alkaid_defconfig_zh | alkaid defconfig详解 | customer/Common/Development/alkaid_defconfig_zh.html |
| customer/Common/Development | customer.Common.Development.bootflow_zh | 启动流程 | customer/Common/Development/bootflow_zh.html |
| customer/Common/Development | customer.Common.Development.debug_sop_zh | Debug SOP | customer/Common/Development/debug_sop_zh.html |
| customer/Common/Development | customer.Common.Development.ota_zh | OTA打包和升级 | customer/Common/Development/ota_zh.html |
| customer/Common/Development | customer.Common.Development.partitionfile_zh | 系统分区 | customer/Common/Development/partitionfile_zh.html |
| customer/Common/Development | customer.Common.Development.power_zh | 功耗调整指引 | customer/Common/Development/power_zh.html |
| customer/Common/ReleaseNote | customer.Common.ReleaseNote.ReleaseNote_zh | Release Note | customer/Common/ReleaseNote/ReleaseNote_zh.html |
| customer/DualOS/Development | customer.DualOS.Development.Rtos_Earlyinit_Sensor_Porting_Guide_zh | RTOS Sensor快启移植指南 | customer/DualOS/Development/Rtos_Earlyinit_Sensor_Porting_Guide_zh.html |
| customer/DualOS/Development | customer.DualOS.Development.TTFF-TTUFF-TTCL_guide_zh | TTFF-TTUFF-TTCL说明 | customer/DualOS/Development/TTFF-TTUFF-TTCL_guide_zh.html |
| customer/DualOS/Development | customer.DualOS.Development.arch_zh | DualOS架构说明 | customer/DualOS/Development/arch_zh.html |
| customer/DualOS/Development | customer.DualOS.Development.dualos_alkaid_config_guide_zh | DualOS alkaid defconfig配置手册 | customer/DualOS/Development/dualos_alkaid_config_guide_zh.html |
| customer/DualOS/Development | customer.DualOS.Development.dualos_customer_development_guide_zh | Dualos客户开发指南 | customer/DualOS/Development/dualos_customer_development_guide_zh.html |
| customer/DualOS/Development | customer.DualOS.Development.dualos_scene_guide_zh | DualOS场景介绍 | customer/DualOS/Development/dualos_scene_guide_zh.html |
| customer/DualOS/Development | customer.DualOS.Development.independently_compile_rtos_guide_zh | RTOS独立编译步骤说明 | customer/DualOS/Development/independently_compile_rtos_guide_zh.html |
| customer/DualOS/Development | customer.DualOS.Development.ipl_earlyinit_guide_zh | IPL Earlyinit说明 | customer/DualOS/Development/ipl_earlyinit_guide_zh.html |
| customer/DualOS/Development | customer.DualOS.Development.multiprocess_guide_zh | DualOS多进程资源管理说明 | customer/DualOS/Development/multiprocess_guide_zh.html |
| customer/DualOS/Development | customer.DualOS.Development.rtos_earlyinit_guide_zh | RTOS Earlyinit说明 | customer/DualOS/Development/rtos_earlyinit_guide_zh.html |
| customer/DualOS/EnvironmentSetup | customer.DualOS.EnvironmentSetup.Environmentsetup_zh | 环境搭建 | customer/DualOS/EnvironmentSetup/Environmentsetup_zh.html |
| platform/Audio_algo | platform.Audio_algo.aec_zh | AEC算法使用参考 | platform/Audio_algo/aec_zh.html |
| platform/Audio_algo | platform.Audio_algo.apc_zh | AGC算法使用参考 | platform/Audio_algo/apc_zh.html |
| platform/Audio_algo | platform.Audio_algo.bf_zh | BF算法使用参考 | platform/Audio_algo/bf_zh.html |
| platform/Audio_algo | platform.Audio_algo.fe_zh | FE算法使用参考 | platform/Audio_algo/fe_zh.html |
| platform/Audio_algo | platform.Audio_algo.kws_zh | KWS算法使用参考 | platform/Audio_algo/kws_zh.html |
| platform/Audio_algo | platform.Audio_algo.mix_zh | MIX算法使用参考 | platform/Audio_algo/mix_zh.html |
| platform/Audio_algo | platform.Audio_algo.se_zh | SE算法使用参考 | platform/Audio_algo/se_zh.html |
| platform/Audio_algo | platform.Audio_algo.sed_zh | SED算法使用参考 | platform/Audio_algo/sed_zh.html |
| platform/Audio_algo | platform.Audio_algo.src_zh | SRC算法使用参考 | platform/Audio_algo/src_zh.html |
| platform/Audio_algo | platform.Audio_algo.ssl_zh | SSL算法使用参考 | platform/Audio_algo/ssl_zh.html |
| platform/Audio_algo | platform.Audio_algo.vad_zh | VAD算法使用参考 | platform/Audio_algo/vad_zh.html |
| platform/Audio_algo | platform.Audio_algo.vc_zh | VC算法使用参考 | platform/Audio_algo/vc_zh.html |
| platform/Audio_tuning | platform.Audio_tuning.tuning_zh | Sstar音频调试手册 | platform/Audio_tuning/tuning_zh.html |
| platform/BSP | platform.BSP.adclp_zh | ADCLP使用参考 | platform/BSP/adclp_zh.html |
| platform/BSP | platform.BSP.audio_zh | AUDIO使用参考 | platform/BSP/audio_zh.html |
| platform/BSP | platform.BSP.cipher_zh | Cipher使用参考 | platform/BSP/cipher_zh.html |
| platform/BSP | platform.BSP.emmc_zh | eMMC使用参考 | platform/BSP/emmc_zh.html |
| platform/BSP | platform.BSP.flash_support_list_zh | Flash支持列表 | platform/BSP/flash_support_list_zh.html |
| platform/BSP | platform.BSP.flash_zh | Flash List新增Flash SOP | platform/BSP/flash_zh.html |
| platform/BSP | platform.BSP.gpio_zh | GPIO使用参考 | platform/BSP/gpio_zh.html |
| platform/BSP | platform.BSP.hardware_parameters_zh | 涉硬参数调整指南 | platform/BSP/hardware_parameters_zh.html |
| platform/BSP | platform.BSP.i2c_zh | I2C使用参考 | platform/BSP/i2c_zh.html |
| platform/BSP | platform.BSP.idac_zh | IDAC使用参考 | platform/BSP/idac_zh.html |
| platform/BSP | platform.BSP.ir_zh | IR使用参考 | platform/BSP/ir_zh.html |
| platform/BSP | platform.BSP.mbx_zh | Mailbox使用参考 | platform/BSP/mbx_zh.html |
| platform/BSP | platform.BSP.pwm_zh | PWM使用参考 | platform/BSP/pwm_zh.html |
| platform/BSP | platform.BSP.register_zh | 寄存器使用参考 | platform/BSP/register_zh.html |
| platform/BSP | platform.BSP.rtc_zh | RTC使用参考 | platform/BSP/rtc_zh.html |
| platform/BSP | platform.BSP.sdcard_zh | SDMMC使用参考 | platform/BSP/sdcard_zh.html |
| platform/BSP | platform.BSP.sensor_support_list_zh | Camera Sensor支持列表 | platform/BSP/sensor_support_list_zh.html |
| platform/BSP | platform.BSP.spi_zh | SPI使用参考 | platform/BSP/spi_zh.html |
| platform/BSP | platform.BSP.timer_zh | Timer使用参考 | platform/BSP/timer_zh.html |
| platform/BSP | platform.BSP.uart_zh | UART使用参考 | platform/BSP/uart_zh.html |
| platform/BSP | platform.BSP.usb_zh | USB host/device使用说明 | platform/BSP/usb_zh.html |
| platform/BSP | platform.BSP.watchdog_zh | Watchdog使用参考 | platform/BSP/watchdog_zh.html |
| platform/BSP | platform.BSP.xzdec_zh | XZDEC使用参考 | platform/BSP/xzdec_zh.html |
| platform/CM4 | platform.CM4.Interaction_between_nonpm_and_pm_zh | NonPM与PM间的交互关系 | platform/CM4/Interaction_between_nonpm_and_pm_zh.html |
| platform/CM4 | platform.CM4.adclp_zh | CM4_ADCLP使用参考 | platform/CM4/adclp_zh.html |
| platform/CM4 | platform.CM4.cm4_api_zh | CM4 API | platform/CM4/cm4_api_zh.html |
| platform/CM4 | platform.CM4.gpio_zh | CM4_GPIO使用参考 | platform/CM4/gpio_zh.html |
| platform/CM4 | platform.CM4.i2c_zh | CM4_I2C使用参考 | platform/CM4/i2c_zh.html |
| platform/CM4 | platform.CM4.pir_zh | CM4_PIR使用参考 | platform/CM4/pir_zh.html |
| platform/CM4 | platform.CM4.pm_power_zh | PM power使用参考 | platform/CM4/pm_power_zh.html |
| platform/CM4 | platform.CM4.pspi_zh | CM4_PSPI使用参考 | platform/CM4/pspi_zh.html |
| platform/CM4 | platform.CM4.pwm_zh | CM4_PWM使用参考 | platform/CM4/pwm_zh.html |
| platform/CM4 | platform.CM4.rtc_zh | CM4_RTC使用参考 | platform/CM4/rtc_zh.html |
| platform/CM4 | platform.CM4.sdmmc_zh | CM4_SDMMC使用参考 | platform/CM4/sdmmc_zh.html |
| platform/CM4 | platform.CM4.timer_zh | CM4_TIMER使用参考 | platform/CM4/timer_zh.html |
| platform/CM4 | platform.CM4.uart_zh | CM4_UART使用参考 | platform/CM4/uart_zh.html |
| platform/CV_guide | platform.CV_guide.IS_user_guide_zh | IS用户手册 | platform/CV_guide/IS_user_guide_zh.html |
| platform/CV_guide | platform.CV_guide.ldc_user_guide_zh | LDC 用户手册 | platform/CV_guide/ldc_user_guide_zh.html |
| platform/IPU_Algo | platform.IPU_Algo.cls_zh | 分类算法 | platform/IPU_Algo/cls_zh.html |
| platform/IPU_Algo | platform.IPU_Algo.det_zh | 检测算法 | platform/IPU_Algo/det_zh.html |
| platform/IPU_Algo | platform.IPU_Algo.fr_zh | 人脸识别算法 | platform/IPU_Algo/fr_zh.html |
| platform/IPU_Algo | platform.IPU_Algo.hgr_zh | 手势识别算法 | platform/IPU_Algo/hgr_zh.html |
| platform/IPU_Algo | platform.IPU_Algo.hpose_zh | 人体姿态识别算法 | platform/IPU_Algo/hpose_zh.html |
| platform/IPU_Algo | platform.IPU_Algo.hseg_zh | 人像分割算法 | platform/IPU_Algo/hseg_zh.html |
| platform/IPU_Algo | platform.IPU_Algo.ovcls_zh | 跨模态分类算法 | platform/IPU_Algo/ovcls_zh.html |
| platform/IPU_Algo | platform.IPU_Algo.ovseg_zh | 跨模态分割算法 | platform/IPU_Algo/ovseg_zh.html |
| platform/ISP/iford | platform.ISP.iford.3a_zh | AE/AWB/AF Interface | platform/ISP/iford/3a_zh.html |
| platform/ISP/iford | platform.ISP.iford.api_zh | ISP软件开发参考 | platform/ISP/iford/api_zh.html |
| platform/ISP/iford | platform.ISP.iford.hdr_zh | ISP HDR Tuning Guide | platform/ISP/iford/hdr_zh.html |
| platform/ISP/iford | platform.ISP.iford.iqtuning_zh | ISP API Tuning SOP | platform/ISP/iford/iqtuning_zh.html |
| platform/MI | platform.MI.ai_zh | AI | platform/MI/ai_zh.html |
| platform/MI | platform.MI.ao_zh | AO | platform/MI/ao_zh.html |
| platform/MI | platform.MI.disp_zh | DISP | platform/MI/disp_zh.html |
| platform/MI | platform.MI.fb_zh | FB | platform/MI/fb_zh.html |
| platform/MI | platform.MI.ipu_zh | IPU | platform/MI/ipu_zh.html |
| platform/MI | platform.MI.isp_zh | ISP | platform/MI/isp_zh.html |
| platform/MI | platform.MI.ive_zh | IVE | platform/MI/ive_zh.html |
| platform/MI | platform.MI.ldc_zh | LDC | platform/MI/ldc_zh.html |
| platform/MI | platform.MI.rgn_zh | RGN | platform/MI/rgn_zh.html |
| platform/MI | platform.MI.scl_zh | SCL | platform/MI/scl_zh.html |
| platform/MI | platform.MI.sensor_zh | SENSOR | platform/MI/sensor_zh.html |
| platform/MI | platform.MI.sys_zh | SYS | platform/MI/sys_zh.html |
| platform/MI | platform.MI.vdf_zh | VDF | platform/MI/vdf_zh.html |
| platform/MI | platform.MI.vdisp_zh | VDISP | platform/MI/vdisp_zh.html |
| platform/MI | platform.MI.venc_zh | VENC | platform/MI/venc_zh.html |
| platform/MI | platform.MI.vif_zh | VIF | platform/MI/vif_zh.html |
| platform/RTOS | platform.RTOS.adclp_zh | ADCLP使用参考 | platform/RTOS/adclp_zh.html |
| platform/RTOS | platform.RTOS.gpio_zh | GPIO使用参考 | platform/RTOS/gpio_zh.html |
| platform/RTOS | platform.RTOS.i2c_zh | I2C使用参考 | platform/RTOS/i2c_zh.html |
| platform/RTOS | platform.RTOS.ir_zh | IR使用参考 | platform/RTOS/ir_zh.html |
| platform/RTOS | platform.RTOS.pwm_zh | PWM使用参考 | platform/RTOS/pwm_zh.html |
| platform/RTOS | platform.RTOS.rtc_zh | RTC使用参考 | platform/RTOS/rtc_zh.html |
| platform/RTOS | platform.RTOS.spi_zh | SPI使用参考 | platform/RTOS/spi_zh.html |
| platform/RTOS | platform.RTOS.timer_zh | Timer使用参考 | platform/RTOS/timer_zh.html |
| platform/RTOS | platform.RTOS.uart_zh | UART使用参考 | platform/RTOS/uart_zh.html |
| platform/RTOS | platform.RTOS.watchdog_zh | Watchdog使用参考 | platform/RTOS/watchdog_zh.html |

## 4. SSU9383CM 主题清单（119）

| 技术域 | 内部主题 ID | 主题名称 | 路径 |
| --- | --- | --- | --- |
| customer/Common/Development | customer.Common.Development.AddTouchScreenDriver_zh | 触控驱动集成参考 | customer/Common/Development/AddTouchScreenDriver_zh.html |
| customer/Common/Development | customer.Common.Development.Bootlogo_zh | BootLogo使用参考 | customer/Common/Development/Bootlogo_zh.html |
| customer/Common/Development | customer.Common.Development.Bootmusic_zh | BootMusic使用参考 | customer/Common/Development/Bootmusic_zh.html |
| customer/Common/Development | customer.Common.Development.DNS_DHCP_zh | DNS & DHCP配置参考 | customer/Common/Development/DNS_DHCP_zh.html |
| customer/Common/Development | customer.Common.Development.DisplayPanels_zh | 点屏参考 | customer/Common/Development/DisplayPanels_zh.html |
| customer/Common/Development | customer.Common.Development.LastLog_zh | Lastlog使用参考 | customer/Common/Development/LastLog_zh.html |
| customer/Common/Development | customer.Common.Development.SigmaStar_Linux_Developer_Guide_Audio_zh | Audio开发指南 | customer/Common/Development/SigmaStar_Linux_Developer_Guide_Audio_zh.html |
| customer/Common/Development | customer.Common.Development.adb_tool_zh | ADB使用参考 | customer/Common/Development/adb_tool_zh.html |
| customer/Common/Development | customer.Common.Development.bluez_zh | Bluez移植使用参考 | customer/Common/Development/bluez_zh.html |
| customer/Common/Development | customer.Common.Development.buildroot_zh | Buildroot编译使用参考 | customer/Common/Development/buildroot_zh.html |
| customer/Common/Development | customer.Common.Development.busybox_zh | Busybox裁剪参考 | customer/Common/Development/busybox_zh.html |
| customer/Common/Development | customer.Common.Development.device_mapper_zh | Device Mapper使用参考 | customer/Common/Development/device_mapper_zh.html |
| customer/Common/Development | customer.Common.Development.dvfs_zh | dvfs使用参考 | customer/Common/Development/dvfs_zh.html |
| customer/Common/Development | customer.Common.Development.iper2_zh | Iperf2移植使用参考 | customer/Common/Development/iper2_zh.html |
| customer/Common/Development | customer.Common.Development.ipu_userguid_zh | IPU使用参考 | customer/Common/Development/ipu_userguid_zh.html |
| customer/Common/Development | customer.Common.Development.makefile_rootfs_zh | 编译打包介绍 | customer/Common/Development/makefile_rootfs_zh.html |
| customer/Common/Development | customer.Common.Development.memory_debug_zh | 内存使用参考 | customer/Common/Development/memory_debug_zh.html |
| customer/Common/Development | customer.Common.Development.ota_zh | OTA升级使用参考 | customer/Common/Development/ota_zh.html |
| customer/Common/Development | customer.Common.Development.p2p_zh | Wifi P2P使用参考 | customer/Common/Development/p2p_zh.html |
| customer/Common/Development | customer.Common.Development.power_zh | 功耗调整指南 | customer/Common/Development/power_zh.html |
| customer/Common/Development | customer.Common.Development.reboot_and_bootreason_zh | 系统重启和原因获取使用参考 | customer/Common/Development/reboot_and_bootreason_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.heartbeat_zh | HeartBeat使用参考 | customer/Common/Development/riscv/heartbeat_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.riscv_adclp_zh | RISCV_ADCLP使用参考 | customer/Common/Development/riscv/riscv_adclp_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.riscv_adcmp_zh | RISCV_ADCMP使用参考 | customer/Common/Development/riscv/riscv_adcmp_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.riscv_capture_zh | RISCV_Capture使用参考 | customer/Common/Development/riscv/riscv_capture_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.riscv_gpio_zh | RISCV_GPIO使用参考 | customer/Common/Development/riscv/riscv_gpio_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.riscv_i2c_zh | RISCV_I2C使用参考 | customer/Common/Development/riscv/riscv_i2c_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.riscv_ir_zh | RISCV_IR使用参考 | customer/Common/Development/riscv/riscv_ir_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.riscv_log_zh | RISCV日志保存功能使用参考 | customer/Common/Development/riscv/riscv_log_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.riscv_mountriver_zh | RISCV_BSP_MOUNRIVER使用参考 | customer/Common/Development/riscv/riscv_mountriver_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.riscv_pwm_zh | RISCV_PWM使用参考 | customer/Common/Development/riscv/riscv_pwm_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.riscv_rpmsg_zh | RISCV_RPMsg使用参考 | customer/Common/Development/riscv/riscv_rpmsg_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.riscv_spi_zh | RISCV_SPI使用参考 | customer/Common/Development/riscv/riscv_spi_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.riscv_spwm_zh | RISCV_SPWM使用参考 | customer/Common/Development/riscv/riscv_spwm_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.riscv_timer_zh | RISCV_TIMER使用参考 | customer/Common/Development/riscv/riscv_timer_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.riscv_uart_zh | RISCV_UART使用参考 | customer/Common/Development/riscv/riscv_uart_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.riscv_use_zh | RISCV开发环境使用指南 | customer/Common/Development/riscv/riscv_use_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.riscv_virtual_filesystem_zh | RISCV虚拟文件系统使用参考 | customer/Common/Development/riscv/riscv_virtual_filesystem_zh.html |
| customer/Common/Development/riscv | customer.Common.Development.riscv.riscv_watchdog_zh | RISCV_WATCHDOG使用参考 | customer/Common/Development/riscv/riscv_watchdog_zh.html |
| customer/Common/Development/rtos | customer.Common.Development.rtos.ai_zh | RTOS_AI使用参考 | customer/Common/Development/rtos/ai_zh.html |
| customer/Common/Development/rtos | customer.Common.Development.rtos.ao_zh | RTOS_AO使用参考 | customer/Common/Development/rtos/ao_zh.html |
| customer/Common/Development/rtos | customer.Common.Development.rtos.rtos_adclp_zh | RTOS_ADCLP使用参考 | customer/Common/Development/rtos/rtos_adclp_zh.html |
| customer/Common/Development/rtos | customer.Common.Development.rtos.rtos_adcmp_zh | RTOS_ADCMP使用参考 | customer/Common/Development/rtos/rtos_adcmp_zh.html |
| customer/Common/Development/rtos | customer.Common.Development.rtos.rtos_gpio_zh | RTOS_GPIO使用参考 | customer/Common/Development/rtos/rtos_gpio_zh.html |
| customer/Common/Development/rtos | customer.Common.Development.rtos.rtos_i2c_zh | RTOS_I2C使用参考 | customer/Common/Development/rtos/rtos_i2c_zh.html |
| customer/Common/Development/rtos | customer.Common.Development.rtos.rtos_pwm_zh | RTOS_PWM使用参考 | customer/Common/Development/rtos/rtos_pwm_zh.html |
| customer/Common/Development/rtos | customer.Common.Development.rtos.rtos_spi_zh | RTOS_SPI使用参考 | customer/Common/Development/rtos/rtos_spi_zh.html |
| customer/Common/Development/rtos | customer.Common.Development.rtos.rtos_uart_zh | RTOS_UART使用参考 | customer/Common/Development/rtos/rtos_uart_zh.html |
| customer/Common/Development/rtos | customer.Common.Development.rtos.rtos_usb_zh | RTOS_USB使用参考 | customer/Common/Development/rtos/rtos_usb_zh.html |
| customer/Common/Development/rtos | customer.Common.Development.rtos.rtos_use_zh | RTOS开发环境使用指南 | customer/Common/Development/rtos/rtos_use_zh.html |
| customer/Common/Development | customer.Common.Development.rz_sz_zh | RZ & SZ 移植使用参考 | customer/Common/Development/rz_sz_zh.html |
| customer/Common/Development | customer.Common.Development.sensor_guide_zh | Sensor驱动移植参考 | customer/Common/Development/sensor_guide_zh.html |
| customer/Common/Development | customer.Common.Development.ssh_scp_tool_zh | SSH & SCP使用参考 | customer/Common/Development/ssh_scp_tool_zh.html |
| customer/Common/Development | customer.Common.Development.top_zh | Top移植使用参考 | customer/Common/Development/top_zh.html |
| customer/Common/Development | customer.Common.Development.usb_factorytool_update_zh | usb factory tool使用参考 | customer/Common/Development/usb_factorytool_update_zh.html |
| customer/Common/Development | customer.Common.Development.usbsdupdate_zh | USB & SD升级 | customer/Common/Development/usbsdupdate_zh.html |
| customer/Common/Development | customer.Common.Development.vendor_burn_zh | Vendor分区数据烧录介绍 | customer/Common/Development/vendor_burn_zh.html |
| customer/Common/Development | customer.Common.Development.wlan_zh | Wlan使用参考 | customer/Common/Development/wlan_zh.html |
| customer/Common/Development | customer.Common.Development.wpa_iwlist_zh | Wpa_supplicant & iwlist移植使用参考 | customer/Common/Development/wpa_iwlist_zh.html |
| customer/DispCam/Development | customer.DispCam.Development.Audio_Cap_Play_zh | ALSA声音采集播放程序说明 | customer/DispCam/Development/Audio_Cap_Play_zh.html |
| customer/DispCam/Development | customer.DispCam.Development.Gpio_ctrl_zh | GPIO控制程序说明 | customer/DispCam/Development/Gpio_ctrl_zh.html |
| customer/DispCam/Development | customer.DispCam.Development.Npu_Model_zh | IPU模型识别程序说明 | customer/DispCam/Development/Npu_Model_zh.html |
| customer/DispCam/Development | customer.DispCam.Development.arch_zh | ARM SDK架构 | customer/DispCam/Development/arch_zh.html |
| customer/DispCam/Development | customer.DispCam.Development.gui_to_panel_zh | 点屏程序说明 | customer/DispCam/Development/gui_to_panel_zh.html |
| customer/DispCam/Development | customer.DispCam.Development.sensor_to_panel_zh | 点sensor程序说明 | customer/DispCam/Development/sensor_to_panel_zh.html |
| customer/DispCam/EnvironmentSetup | customer.DispCam.EnvironmentSetup.Environmentsetup_zh | 编译环境搭建 | customer/DispCam/EnvironmentSetup/Environmentsetup_zh.html |
| customer/DispCam/EnvironmentSetup | customer.DispCam.EnvironmentSetup.burn_zh | 软件烧录说明 | customer/DispCam/EnvironmentSetup/burn_zh.html |
| platform/Audio_algo | platform.Audio_algo.aec_zh | AEC算法使用参考 | platform/Audio_algo/aec_zh.html |
| platform/Audio_algo | platform.Audio_algo.apc_zh | APC算法使用参考 | platform/Audio_algo/apc_zh.html |
| platform/Audio_algo | platform.Audio_algo.asr_zh | ASR算法使用参考 | platform/Audio_algo/asr_zh.html |
| platform/Audio_algo | platform.Audio_algo.bf_zh | BF算法使用参考 | platform/Audio_algo/bf_zh.html |
| platform/Audio_algo | platform.Audio_algo.kws_zh | KWS算法使用参考 | platform/Audio_algo/kws_zh.html |
| platform/Audio_algo | platform.Audio_algo.ssl_zh | SSL算法使用参考 | platform/Audio_algo/ssl_zh.html |
| platform/BSP | platform.BSP.PMIC_zh | PMIC驱动开发指导手册 | platform/BSP/PMIC_zh.html |
| platform/BSP | platform.BSP.adclp_zh | ADCLP使用参考 | platform/BSP/adclp_zh.html |
| platform/BSP | platform.BSP.adcmp_zh | ADCMP使用参考 | platform/BSP/adcmp_zh.html |
| platform/BSP | platform.BSP.capture_zh | Capture使用参考 | platform/BSP/capture_zh.html |
| platform/BSP | platform.BSP.cipher_zh | Cipher使用参考 | platform/BSP/cipher_zh.html |
| platform/BSP | platform.BSP.emmc_support_list_zh | eMMC支持列表 | platform/BSP/emmc_support_list_zh.html |
| platform/BSP | platform.BSP.emmc_zh | EMMC使用和母片制作 | platform/BSP/emmc_zh.html |
| platform/BSP | platform.BSP.ethernet_zh | Ethernet使用参考 | platform/BSP/ethernet_zh.html |
| platform/BSP | platform.BSP.flash_support_list_zh | Flash支持列表 | platform/BSP/flash_support_list_zh.html |
| platform/BSP | platform.BSP.flash_zh | Flash List新增Flash SOP | platform/BSP/flash_zh.html |
| platform/BSP | platform.BSP.gpio_zh | GPIO使用参考 | platform/BSP/gpio_zh.html |
| platform/BSP | platform.BSP.i2c_zh | I2C使用参考 | platform/BSP/i2c_zh.html |
| platform/BSP | platform.BSP.ir_zh | IR使用参考 | platform/BSP/ir_zh.html |
| platform/BSP | platform.BSP.keypad_zh | Keypad使用参考 | platform/BSP/keypad_zh.html |
| platform/BSP | platform.BSP.padmux_zh | Padmux使用参考 | platform/BSP/padmux_zh.html |
| platform/BSP | platform.BSP.partitionfile_zh | 分区介绍 | platform/BSP/partitionfile_zh.html |
| platform/BSP | platform.BSP.pwm_zh | PWM使用参考 | platform/BSP/pwm_zh.html |
| platform/BSP | platform.BSP.register_zh | 寄存器使用参考 | platform/BSP/register_zh.html |
| platform/BSP | platform.BSP.rtc_zh | RTC使用参考 | platform/BSP/rtc_zh.html |
| platform/BSP | platform.BSP.sd_emmc_stress_test_zh | SD_EMMC压力测试参考 | platform/BSP/sd_emmc_stress_test_zh.html |
| platform/BSP | platform.BSP.sdmmc_zh | SDMMC使用参考 | platform/BSP/sdmmc_zh.html |
| platform/BSP | platform.BSP.sensor_bsp_zh | Sensor使用参考 | platform/BSP/sensor_bsp_zh.html |
| platform/BSP | platform.BSP.sensor_support_list_zh | Camera Sensor支持列表 | platform/BSP/sensor_support_list_zh.html |
| platform/BSP | platform.BSP.spi_zh | SPI使用参考 | platform/BSP/spi_zh.html |
| platform/BSP | platform.BSP.spwm_zh | SPWM使用参考 | platform/BSP/spwm_zh.html |
| platform/BSP | platform.BSP.timer_zh | Timer使用参考 | platform/BSP/timer_zh.html |
| platform/BSP | platform.BSP.uart_zh | UART使用参考 | platform/BSP/uart_zh.html |
| platform/BSP | platform.BSP.usb_zh | USB使用参考 | platform/BSP/usb_zh.html |
| platform/BSP | platform.BSP.watchdog_zh | Watchdog使用参考 | platform/BSP/watchdog_zh.html |
| platform/ISP/Common | platform.ISP.Common.3a_zh | AE/AWB/AF Interface | platform/ISP/Common/3a_zh.html |
| platform/ISP/pcupid | platform.ISP.pcupid.api_zh | ISP软件开发参考 | platform/ISP/pcupid/api_zh.html |
| platform/ISP/pcupid | platform.ISP.pcupid.iqtuning_zh | ISP API Turning SOP | platform/ISP/pcupid/iqtuning_zh.html |
| platform/MI | platform.MI.disp_zh | DISP | platform/MI/disp_zh.html |
| platform/MI | platform.MI.fb_zh | FB | platform/MI/fb_zh.html |
| platform/MI | platform.MI.gfx_zh | GFX | platform/MI/gfx_zh.html |
| platform/MI | platform.MI.ipu_zh | IPU | platform/MI/ipu_zh.html |
| platform/MI | platform.MI.iqserver_zh | IQSERVER | platform/MI/iqserver_zh.html |
| platform/MI | platform.MI.isp_zh | ISP | platform/MI/isp_zh.html |
| platform/MI | platform.MI.ive_zh | IVE | platform/MI/ive_zh.html |
| platform/MI | platform.MI.pspi_zh | PSPI | platform/MI/pspi_zh.html |
| platform/MI | platform.MI.rgn_zh | RGN | platform/MI/rgn_zh.html |
| platform/MI | platform.MI.scl_zh | SCL | platform/MI/scl_zh.html |
| platform/MI | platform.MI.sensor_zh | SENSOR | platform/MI/sensor_zh.html |
| platform/MI | platform.MI.sys_zh | SYS | platform/MI/sys_zh.html |
| platform/MI | platform.MI.vdisp_zh | VDISP | platform/MI/vdisp_zh.html |
| platform/MI | platform.MI.vif_zh | VIF | platform/MI/vif_zh.html |

## 5. Codex 检索约定

1. 查询提示词优先包含：平台、技术域、问题类型（移植/调试/优化/交付）。
2. 对同域跨平台问题，先比较内部主题 ID 再定位差异配置。
3. 调试类问题优先关联 `docs/runbooks/` 下执行手册。
