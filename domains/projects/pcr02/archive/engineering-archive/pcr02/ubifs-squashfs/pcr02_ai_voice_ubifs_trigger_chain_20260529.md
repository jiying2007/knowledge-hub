# PCR02 AI 语音助手与 UBIFS 触发链归档

日期：2026-05-29

状态：历史触发链分析，保留为压力触发和应用路径证据。

当前口径：AI 语音路径仍可作为 `/customer` 读路径压力触发器；但当前有效规避方案不是继续调 UBIFS，而是 `/customer` SquashFS on static UBI volume。当前有效方案见 `../decision-index.md` 与 `../ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/README.md`。

本文归档 PCR02 主应用中 AI 语音助手相关代码对 `/customer` UBIFS 异常的触发链分析。本文是应用侧归档，不与 SDK-only 分区、OTA、rootfs/customer/data 文档混合。

## 背景现象

后续调试中观察到：

1. 刚烧录后全量 md5 校验可以通过。
2. 关闭业务应用，只做反复重启和 md5 校验，一直未复现。
3. 第一坏点经常是 `/customer/lib/libmsc.so` 或语音资源。
4. 屏蔽语音助手 `start_ai_voice_thread` 后，反复重启暂未测试到问题。

该现象说明：普通静态镜像损坏或单纯 reboot 本身不是最强解释，AI 语音路径是高价值触发器。

## 代码链路

主入口在应用启动阶段调用：

```text
pcr02/main.cpp
  -> start_ai_voice_thread()
```

语音线程路径：

```text
modules/ai/AI_voice_thread.cpp
  -> start_ai_voice_thread()
  -> sleep 5s
  -> ai_websocket_init("", "")
```

`ai_websocket_init()` 进一步执行：

```text
初始化 audio buffer manager
初始化全局状态机
启动 pub/sub 线程
初始化 websocket
wakeup_module_init()
set_wakeup_callback(...)
setEnableWakeupSound(0)
set_wakeup_post_sound_callback(...)
start_wakeup_test()
初始化 AiAudioCapture
```

唤醒模块路径：

```text
modules/ai/wakeup_test/chenyf/wakeup_test.cpp
  -> wakeup_module_init()
  -> MSPLogin(NULL, NULL, "appid = ..., work_dir = /data/msc")
  -> start_wakeup_test()
  -> QIVWSessionBegin(NULL, session_params, &err_code)
  -> QIVWRegisterNotify(...)
  -> 周期 audio task
  -> QIVWAudioWrite(...)
```

关键资源：

```text
/customer/lib/libmsc.so
/customer/bin/resource/msc/res/ivw/wakeupresource.jet
/customer/bin/resource/msc/res/audio/wake_up_sound_1.mp3
/customer/bin/resource/msc/res/audio/wake_up_sound_2.mp3
/customer/bin/resource/msc/res/audio/wake_up_sound_3.mp3
```

其中 `ai_websocket_init()` 正常路径会调用 `setEnableWakeupSound(0)`，因此 mp3 唤醒提示音理论上不应在默认路径播放；但 `libmsc.so` 和 `wakeupresource.jet` 会被真实加载/使用。

## 关键判断

### AI 语音路径没有看到直接擦写 NAND/UBI

源码搜索未发现 AI 语音路径直接调用：

```text
ubiupdatevol
ubiformat
flash_erase
nandwrite
/dev/mtd
/dev/ubi
remount /customer
```

因此当前不应把 AI 语音路径理解为“直接写坏 `/customer`”。

### AI 语音路径会触发实际读路径压力

AI 语音路径会：

1. 动态链接并执行 `libmsc.so`。
2. 调用 `MSPLogin()`。
3. 调用 `QIVWSessionBegin()` 读取唤醒资源。
4. 启动音频 reader 和周期任务。
5. 持续向讯飞唤醒引擎 `QIVWAudioWrite()` 输入音频。

这些动作会叠加：

```text
/customer 冷读
动态库 mmap/page fault
语音资源读取
AI/音频线程负载
DDR/cache/DMA 压力
```

这与“底层 SPI-NAND 读路径边界问题被应用负载触发”的主假设吻合。

## 分阶段验证方案

建议不要只做 `start_ai_voice_thread` 全开/全关，而是增加临时阶段开关，例如：

```text
PCR02_WAKEUP_STAGE=off
PCR02_WAKEUP_STAGE=thread
PCR02_WAKEUP_STAGE=login
PCR02_WAKEUP_STAGE=session
PCR02_WAKEUP_STAGE=reader
PCR02_WAKEUP_STAGE=write
```

### 阶段 0：完全关闭

不调用 `start_ai_voice_thread()`。

目的：确认基线稳定性。

### 阶段 1：只启动线程

启动线程，但不调用 `ai_websocket_init()`。

目的：排除线程本身、sleep、调度带来的影响。

### 阶段 2：只执行 `MSPLogin`

调用 `wakeup_module_init()`，但不开始 session。

目的：验证 `libmsc.so` 初始化和 `/data/msc` 工作目录写入是否触发。

### 阶段 3：执行 `QIVWSessionBegin`

加载：

```text
/customer/bin/resource/msc/res/ivw/wakeupresource.jet
```

但不启动音频 reader/task。

目的：验证唤醒资源加载是否为关键触发点。

### 阶段 4：启动 audio reader

打开音频 reader 和 task，但跳过 `QIVWAudioWrite()`。

目的：区分音频采集/DMA/线程负载与讯飞库处理的影响。

### 阶段 5：完整 `QIVWAudioWrite`

完整打开唤醒音频写入。

目的：验证完整语音助手路径是否触发底层读错或应用崩溃。

## 推荐校验命令

每个阶段启动前后建议执行：

```sh
sync
echo 3 > /proc/sys/vm/drop_caches
md5sum /customer/lib/libmsc.so >/dev/null 2>/dev/null || echo FAIL:/customer/lib/libmsc.so
md5sum /customer/bin/resource/msc/res/ivw/wakeupresource.jet >/dev/null 2>/dev/null || echo FAIL:wakeupresource.jet
dmesg | grep -Ei 'ubi|ubifs|spinand|fsp|bdma|riu|ecc|uncorrect|decompress|bad data node|readpage' | tail -80
```

若出现 inode 错误，需要立即反查：

```sh
find /customer -type f -exec ls -li {} \; 2>/dev/null | grep '^[[:space:]]*<inode>[[:space:]]'
```

## 代码风险点

当前可见风险包括：

1. `g_wakeup_thread_running` 是 `volatile bool`，不是 atomic，存在生命周期数据竞争风险。
2. wakeup session id 与 callback/audio task 生命周期需要仔细关停，避免 use-after-stop。
3. `libmsc.so` 是第三方闭源库，内部 I/O、线程、mmap、SIMD/DMA 行为不可见。
4. 关闭唤醒提示音不等于关闭讯飞 wakeup 引擎。

这些风险更偏应用稳定性和触发条件，不等同于直接写坏 Flash。

## 当前结论

AI 语音助手路径是当前最有价值的应用侧触发器：

1. 它解释了为什么关闭业务应用反复 reboot 不复现。
2. 它解释了为什么首坏文件经常集中在 `libmsc.so` 或语音资源。
3. 它没有显示直接写 `/customer` 的证据。
4. 它更可能通过动态库/资源冷读、音频线程、第三方库执行和系统负载触发底层 SPI-NAND 读路径问题。

后续应通过分阶段开关把触发点从“整条 AI voice”缩小到 `MSPLogin`、`QIVWSessionBegin`、audio reader 或 `QIVWAudioWrite` 中的一个阶段。
