# PCR02 刷机后首次 UBIFS Fixup 验证规程

日期：2026-05-29

本文归档 PCR02 使用 UBIFS image 首次挂载时 `free space fixup` 的生产和测试规程。该内容是首启动风险窗口管理，不再作为当前 `/customer` 偶发读坏问题的最高优先级根因结论。

## 背景

当前 UBIFS 镜像生成曾使用 `mkfs.ubifs -F`。该选项会让 UBIFS 在首次挂载时执行 free space fixup。

设备首次启动时 dmesg 可能出现：

```text
UBIFS (ubi0:x): start fixing up free space
UBIFS (ubi0:x): free space fixup complete
```

这是正常机制，但首次挂载期间会写 UBIFS 空闲区域。若这个窗口内发生断电、异常复位、watchdog 或人为 reboot，下一次启动可能进入 recovery/replay，甚至暴露临时挂载异常。

## 当前定位

该机制可以解释部分现象：

1. 刷机后首次启动阶段更敏感。
2. 异常后再次 reboot 可能恢复。
3. 首次 fixup 完成前断电存在风险。

但截至 2026-05-29，它不应再作为最高优先级根因，因为后续证据更支持：

1. 同一文件可能一时读坏，后续 hash 又正确。
2. 所有板子都有概率复现。
3. 关闭业务应用反复 reboot + md5 可长期不复现。
4. AI 语音路径和 SPI-NAND 读路径更可疑。

因此本文定位为生产规程和风险控制，而不是最终根因说明。

## 首次启动规程

### 1. 刷机后禁止立即断电

刷机完成后首次上电，必须等待所有 UBIFS volume 完成 fixup。

需要看到每个 volume 对应的：

```text
free space fixup complete
```

当前常见 volume：

```text
factory
miservice
ota
customer
data
```

### 2. 首次启动完成后执行 sync

设备侧执行：

```sh
sync
```

再允许 reboot、断电或进入压测。

### 3. 第二次干净启动复验

第二次启动时理论上不应再次出现：

```text
start fixing up free space
```

如果每次启动都出现 fixup，说明：

1. fixup 状态没有持久化。
2. 升级路径反复写入 fresh UBIFS image。
3. 设备在 fixup 完成前被复位。
4. UBI/UBIFS 写入存在更底层问题。

## 验证命令

启动后采集：

```sh
dmesg | grep -Ei 'UBIFS .*fixing up free space|free space fixup complete|recovery needed|recovery completed'
cat /proc/mounts | grep -E ' /customer | /data | /ota | /factory '
sync
```

查看 UBI 状态：

```sh
cat /sys/class/ubi/ubi0/bad_peb_count 2>/dev/null
cat /sys/class/ubi/ubi0/ro_mode 2>/dev/null
for f in /sys/class/ubi/ubi0_*/corrupted /sys/class/ubi/ubi0_*/upd_marker; do
    echo "### $f"
    cat "$f" 2>/dev/null
done
```

## 产线/测试要求

1. 首烧后首次启动必须保留完整串口或 dmesg 日志。
2. 未看到所有 UBIFS volume fixup complete，不允许断电。
3. 首次启动后执行 `sync`。
4. 第二次启动确认不再 fixup。
5. 若出现 mount failed、`Structure needs cleaning`、`bad node`，不得继续拿该设备做稳定性结论，应先恢复干净镜像。

## 与 OTA 的关系

OTA 如果更新 UBIFS volume，也可能让对应 volume 在下一次挂载时经历类似首次挂载写入窗口。需要区分：

1. 全量刷机后的首次 fixup。
2. OTA 更新单个 volume 后的首次挂载。
3. 正常运行多次 reboot 后重复出现 fixup。

只有第 3 类属于异常信号。

## 当前结论

free space fixup 是必须管理的首启动风险窗口，但它不是当前最强根因解释。后续应继续保留该规程，同时把主要根因验证放在：

1. SPI-NAND BDMA/RIU A/B。
2. 读时钟和 quad read 参数。
3. AI 语音路径分阶段触发。
4. ECC uncorrected 返回值。

