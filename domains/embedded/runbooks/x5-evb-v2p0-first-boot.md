---
id: embedded-x5-evb-v2p0-first-boot-20260805
title: X5 EVB V2P0 首次启动与固件恢复 Runbook
kind: runbook
domain: embedded
path: domains/embedded/runbooks/x5-evb-v2p0-first-boot.md
scope: team-general
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-documentation
  from: RDK X5 仓库本地 SDK V1.1.2、EVB V2P0 用户指南与仓库 runbook
  source_sha256: 5957bbec261cfb89426b9cb657379279787f01f6f8db2c87974063c1b0b03de4
review_after: '2026-11-05'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- x5
- evb
- board-bring-up
- firmware-recovery
validation_refs:
- domains/embedded/runbooks/x5-evb-v2p0-first-boot.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- domains/embedded/runbooks/x5-evb-v2p0-first-boot.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-05'
updated_at: '2026-08-05'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-05'
manual_validation_pending: true
summary_zh: 基于 X5 SDK V1.1.2 本地交付资料整理的 EVB V2P0 首启、串口验收、网络与 ADB 连接、Fastboot/DFU 恢复流程；资料已核对，实机验证待完成。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- X5 EVB V2P0 首次启动与固件恢复 Runbook
related:
- indexes/obsidian-home.md
---

# X5 EVB V2P0 首次启动与固件恢复 Runbook

- 文档状态：资料已核对，实机验证待完成
- 适用板型：D-Robotics X5 EVB V2P0
- SDK 基线：`LNX6.1.83_PL5.1_V1.1.2`
- 最后核对日期：2026-08-05
- 维护原则：优先验证出厂 eMMC 系统；仅在系统不可启动时刷机

## 1. 目标与边界

本文用于将一块 X5 EVB V2P0 从未接线状态推进到以下最小可用状态：

1. 调试串口能看到完整启动日志；
2. 能进入 Linux 并使用 `root` 账号登录；
3. 能识别 eMMC、内存和根文件系统；
4. 能通过网口或 ADB 建立至少一种远程连接；
5. 系统损坏时，能使用 SDK 随附的 release 镜像恢复。

本文不覆盖 BSP 编译、摄像头调试、算法部署、量产烧录、安全启动开通和自定义硬件适配。默认 release 系统基于 Buildroot，HDMI 不提供桌面环境，黑屏不能单独作为启动失败依据。

## 2. 所需材料

- X5 EVB V2P0 开发板；
- 12V、至少 2A 的电源适配器；
- 至少一根支持数据通信的 Micro USB 2.0 线，用于调试串口；
- 如需 ADB 或 USB 烧录，再准备一根 Micro USB 2.0 数据线；
- 如需网络连接，准备一根网线；
- Windows 或 Ubuntu 主机。

首次基础启动不要求连接摄像头、显示器或其他扩展板。

## 3. 首次启动：先验证出厂 eMMC

### 3.1 断电设置启动拨码

接口 9 的拨码设置如下：

| 拨码 | 状态 | 含义 |
|---|---|---|
| D5 | ON | eMMC 启动选择位 |
| D2 | OFF | eMMC 启动选择位 |
| D1 | OFF | eMMC 启动选择位 |
| D0 | ON | eMMC 启动选择位 |
| D4 | OFF | 调试串口使用 115200 bps |
| D11 | OFF | eMMC 在时钟下降沿采样 |

即 `D5,D2,D1,D0 = 1001`。拨码方向必须以开关本体上的 `ON` 标识判断，不以照片左右方向猜测。改变拨码前先关闭电源。

### 3.2 接线

| 接口 | 用途 | 首启是否必需 |
|---|---|---|
| 接口 1 | 12V DC 电源 | 是 |
| 接口 19 | Micro USB 调试串口，板载 CH340N | 是 |
| 接口 4 | 千兆以太网 | 否 |
| 接口 5 | Micro USB 2.0 数据、ADB、DFU、Fastboot | 否 |
| 接口 23 | 电源开关 | 是 |

调试串口必须接接口 19。接口 5 是 USB 数据与烧录口，不能替代首次启动时的调试串口观察。

### 3.3 配置串口终端

串口参数：

```text
Baud rate: 115200
Data bits: 8
Parity: None
Stop bits: 1
Hardware flow control: No
Software flow control: No
```

Windows 可使用 MobaXterm、SecureCRT 或 PuTTY，并安装 SDK `software_tools/serial_to_usb_drivers` 中的 CH340 驱动。

Ubuntu 通常可直接识别为 `/dev/ttyUSB*`：

```bash
ls /dev/ttyUSB*
sudo minicom -D /dev/ttyUSB0
```

### 3.4 上电与登录

先打开串口终端，再接通 12V 电源并打开接口 23 的电源开关。正常启动应依次看到 BootROM、U-Boot、Linux 内核和登录提示。

默认凭据：

```text
username: root
password: root
```

默认账号仅适用于隔离的开发环境。接入共享或不可信网络前应修改密码，并按项目安全策略限制 SSH/ADB 暴露范围。

## 4. 最小验收

登录后执行：

```bash
uname -a
cat /proc/device-tree/model
cat /proc/cmdline
free -h
df -h
lsblk
ifconfig
dmesg | tail -n 100
```

最低通过条件：

- 电源工作指示灯正常；
- 串口启动日志连续、可读；
- 可以使用 `root` 登录 Linux；
- `lsblk`、`df -h` 能看到 eMMC 和根文件系统；
- 内存容量与板卡配置大致一致；
- `dmesg` 末尾没有持续刷屏的崩溃、I/O 或文件系统错误；
- 网口或 ADB 至少有一种连接方式可用。

建议保存以下实机证据后再把本文状态升级为“实机已验证”：

```text
板卡丝印/版本：
DDR/eMMC 规格：
SDK/镜像版本：
完整启动日志路径：
uname -a 输出：
板端 model 输出：
存储与内存检查：
网口/ADB 检查：
验证人和日期：
```

## 5. 网络和 ADB

### 5.1 网口

release 系统默认配置：

```text
Board IP: 192.168.1.10
Netmask: 255.255.255.0
Gateway: 192.168.1.1
```

PC 直连时可将 PC 网口设置为 `192.168.1.100/24`，然后测试：

```bash
ping 192.168.1.10
ssh root@192.168.1.10
```

默认未启用 DHCP。网络不通时先通过串口执行 `ifconfig`，确认实际接口名、地址和链路状态。

### 5.2 ADB

使用接口 5 连接 PC：

```bash
adb devices
adb shell
source /etc/profile
```

如果 PC 无法识别设备：

1. 确认 Micro USB 线支持数据通信；
2. 在板端执行 `ps | grep adbd`；
3. 必要时在板端执行 `/etc/init.d/usb-gadget.sh restart adb`；
4. Windows 检查 WinUSB 驱动，Ubuntu 检查 udev 规则和用户组。

## 6. 固件恢复

只有出厂系统无法进入 Linux，或明确需要更新 SDK 基线时才刷机。刷机前保存串口日志和现有版本信息；不要默认启用“全盘擦除 eMMC”。

### 6.1 固件与工具

- XBurn GUI：`X5_LNX_SDK/LNX6.1.83_PL5.1_V1.1.2/software_tools/download_tools/`
- 普通 EVB 固件：`board_support_package/firmwares/product_ddr_auto_detect_non-secure_release.zip`
- 安全启动固件：`product_ddr_auto_detect_secure_release.zip`

普通开发板默认使用 `non-secure` release。只有确认目标芯片已启用安全启动并核对密钥/签名链后，才可使用 secure release，禁止混刷。

完整解压固件 ZIP。XBurn 的镜像目录应选择包含 `x5-soc-release-gpt.json`、`uart_usb/` 和各分区 `.img` 文件的目录。SDK 实际交付工具版本为 XBurn GUI 1.1.9；以交付目录内安装包为准。

### 6.2 原系统仍可进入 ADB：Fastboot

板端或 ADB shell 执行：

```bash
reboot -m usb2 -f
```

XBurn 设置：

```text
产品类型：X5
连接类型：USB
下载模式：Fastboot
镜像目录：解压后的 release 镜像目录
```

使用接口 5 连接 USB，确认 XBurn 识别设备后开始升级。

### 6.3 空板或固件损坏：USB DFU+Fastboot

1. 断电；
2. 设置 `D5=0`，并设置 `D2,D1,D0=010`，即 D2 OFF、D1 ON、D0 OFF；
3. D4 保持 OFF，对应 115200 bps；
4. 将接口 5 连接 PC；
5. XBurn 选择 `X5`、`USB`、`DFU+Fastboot`；
6. 上电后 1 分钟内点击“开始升级”，否则 DFU 会超时；
7. 进度达到 100% 后断电；
8. 将启动拨码恢复为 eMMC：`D5,D2,D1,D0=1001`；
9. 重新以 115200 bps 观察完整启动日志。

若串口打印 `USB DFU function timeout` 后连续显示 `C`，说明 DFU 已超时并切换到 Xmodem 等待状态。断电后重新进入 DFU，并在一分钟内开始升级。

## 7. 故障分流

| 现象 | 优先检查 | 后续动作 |
|---|---|---|
| 电源灯不亮 | 12V 电源、电流能力、接口 23 | 断电检查，不继续烧录 |
| 电源灯亮但串口无输出 | 接口 19、数据线、CH340 驱动、拨码、波特率 | 确认 D4 与串口速率一致 |
| 串口乱码 | D4 状态和终端波特率 | D4 OFF 用 115200；D4 ON 用 921600 |
| 串口连续显示 `C` | 进入 Xmodem 等待 | 检查启动拨码或执行固件恢复 |
| 停在 U-Boot | eMMC 镜像、bootargs、分区 | 保存日志后使用 Fastboot/DFU 恢复 |
| Linux 已登录但网口不通 | 静态 IP、PC 网段、防火墙、链路 | 先用串口核对 `ifconfig` |
| ADB 无设备 | 接口 5、数据线、驱动、adbd | 重启 USB gadget 服务 |
| HDMI 黑屏 | 默认 Buildroot 无桌面 | 以串口 Linux 登录作为启动判据 |

## 8. 停止条件与升级原则

发生以下情况应停止反复上电或刷机，保留完整日志后重新评审：

- 同一烧录流程连续失败两次；
- 无法确认板型或拨码定义；
- secure/non-secure 状态不明确；
- 电源、PMIC、DDR 或 eMMC 出现疑似硬件错误；
- 刷机工具识别到了多个设备，无法确认目标 UID；
- 镜像目录版本与板卡或 SDK 基线不一致。

禁止在问题未定位时循环全盘擦除、混刷 secure/non-secure 镜像或更改 eFuse。

## 9. 来源与验证状态

主要本地来源（以下为源仓相对路径；PDF、SDK 和固件二进制未复制到 Knowledge Hub）：

- `X5_datasheet_and_design_guide/HardwareInterface/X5 EVB V2P0 User Guide V1.1.2.pdf`
- `X5_LNX_SDK/LNX6.1.83_PL5.1_V1.1.2/release_note_and_change_log/LNX6.1.83_PL5.1_V1.1.2 ReleaseNotes.pdf`
- `X5_LNX_SDK/LNX6.1.83_PL5.1_V1.1.2/user_manual/user_manual_v1.1.2.zip`
- `X5_LNX_SDK/LNX6.1.83_PL5.1_V1.1.2/board_support_package/firmwares/product_ddr_auto_detect_non-secure_release.zip`

已完成的验证：

- 核对 SDK V1.1.2 release notes 的内核、Buildroot 和适配板型说明；
- 核对用户手册中 eMMC/DFU 拨码真值表、串口参数、默认登录、网络配置和 XBurn 流程；
- 核对 release 固件 ZIP 包含 GPT 配置、分区镜像和 `uart_usb` 启动文件；
- 核对 SDK 实际包含 XBurn GUI 1.1.9 安装包。

尚未完成的验证：

- 未在当前会话中对真实开发板上电；
- 未采集实际 BootROM、U-Boot、Linux 和登录日志；
- 未实际执行 XBurn 烧录；
- 未验证具体板卡的 DDR/eMMC 容量、网络和 ADB。

因此，本文当前是可执行的资料核对版 runbook，不是实机通过报告。
