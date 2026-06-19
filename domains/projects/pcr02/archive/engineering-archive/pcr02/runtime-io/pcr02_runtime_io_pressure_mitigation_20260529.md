# PCR02 运行期 I/O 压力收敛优化归档

日期：2026-05-29

本文归档 PCR02 应用运行期 I/O 压力收敛相关改动和验证结果。本文用于说明哪些改动是降低 UBIFS/UBI 写放大和异常重启风险的工程优化，但不把它们声明为 UBIFS 根因修复。

## 背景

早期排查中曾怀疑应用重构后启动阶段写压力放大，包括：

1. ZMQ IPC socket 创建。
2. 日志 fallback 写 `/data/log`。
3. WiFi 配置写入。
4. Bridge 配置写入。
5. 多进程和多模块启动期间读 `/customer`、写 `/data` 叠加。

后续根因方向已进一步收敛到底层 SPI-NAND 读路径，但这些 I/O 收敛改动仍然有工程价值：

1. 降低无 SD 卡场景对 `/data` 的持续写入。
2. 避免异常重启留下半截配置。
3. 减少 UBIFS journal 和 metadata 压力。
4. 降低排查变量。

## 已做优化

### ZMQ IPC 移到 tmpfs

进程间 IPC 从相对 `ipc://<channel>` 改为绝对 tmpfs 路径：

```text
/tmp/xcrz_zmq/*.sock
```

收益：

1. 避免相对路径落到进程当前工作目录。
2. 避免启动/重启时在 UBIFS 上创建、删除 socket 文件。
3. 统一 IPC 文件位置，便于设备侧检查。

验证命令：

```sh
ls -l /tmp/xcrz_zmq
readlink /proc/$(pidof prog_pcr02)/cwd
```

### 日志 fallback 移到 tmpfs

无 SD 卡时默认日志 fallback 从：

```text
/data/log
```

改为：

```text
/tmp/log
```

只有显式设置：

```text
PCR02_LOG_FALLBACK_DATA=1
```

才回落到 `/data/log`。

收益：

1. 无 SD 卡反复 reboot 时不持续写 `/data` UBIFS。
2. 减少日志写入与 `/customer` 读取共享同一 UBI device 的干扰。
3. 需要持久日志时仍保留显式开关。

### WiFi 配置原子写入

WiFi 配置 `/data/etc/wpa_supplicant.conf` 写入流程改为：

```text
write tmp
fflush
fsync(tmp fd)
rename
fsync(parent dir)
```

收益：

1. 避免重启/掉电时留下半截配置。
2. 降低启动后网络配置异常造成的连锁排查噪音。

### Bridge 配置补 fsync

Bridge 日志配置 TOML 保留 tmp + rename，同时补：

1. tmp 文件 `fsync`。
2. parent dir `fsync`。

收益与 WiFi 配置类似，目标是配置写入抗异常重启。

## 验证结果

已执行过的构建验证包括：

```text
rtk git diff --check
rtk make modules/common_lib_all
rtk make modules/bridge_lib_all modules/wifi_manager_app_all pcr02_app_all
rtk make modules/wifi_manager_script_start
rtk ./build.sh compile --profile ap6303bh_512m_v20 --no-sync-sources --allow-dirty --no-source-check
rtk ./build.sh package --profile ap6303bh_512m_v20 --pack sd --skip-defconfig --no-sync-sources --allow-dirty --no-source-check --no-copy-nfs
```

对应结论：

1. 源码格式检查通过。
2. 相关模块重编通过。
3. 应用和镜像打包通过。
4. 生成过 SD 升级包。

## 设备侧验证点

升级后建议确认：

```sh
ls -ld /tmp/xcrz_zmq /tmp/log /data/log 2>/dev/null
ls -l /tmp/xcrz_zmq 2>/dev/null
readlink /proc/$(pidof prog_pcr02)/cwd
cat /proc/mounts | grep -E ' /customer | /data | /ota '
dmesg | grep -Ei 'ubi|ubifs|mtd|nand|ecc|uncorrect|decompress|bad data node' | tail -100
```

若需要确认是否仍写 `/data/log`：

```sh
find /data/log -type f -mmin -5 -ls 2>/dev/null
find /tmp/log -type f -mmin -5 -ls 2>/dev/null
```

## 与当前根因判断的关系

这些改动是有效工程优化，但不能单独证明或修复当前 UBIFS 问题。

当前更准确的关系是：

```text
运行期 I/O 优化
  -> 降低 UBI 写压力和异常重启损伤窗口
  -> 减少排查变量
  -> 但不直接解释同一文件有时 hash 失败、有时恢复

SPI-NAND 读路径排查
  -> 更符合当前所有板子概率复现、drop cache 暴露、AI voice 触发的证据
```

## 当前结论

运行期 I/O 压力收敛应保留，但不应再作为唯一主线。后续排查主线应是：

1. AI 语音触发链分阶段验证。
2. SPI-NAND RIU/BDMA A/B。
3. 降频或禁用 quad read。
4. ECC uncorrected 返回值修正。
5. 继续保持 `/customer` 只读且不带 `bulk_read`。

