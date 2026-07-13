---
title: PCR02 app NFS 共享挂载手册
doc_type: runbook
status: archived
owner: leiwenjun
source_id: local-runtime-config
source_path: ~/nfs/README-nfs-app.md
captured_at: 2026-07-02
last_verified: 2026-07-02
review_after: 2026-10-02
---

# PCR02 app NFS 共享挂载手册

## Hub 边界

本文是 PCR02 项目本机调试环境 runbook，只记录主机侧 NFS 共享、设备侧 mount 命令、验证证据和回滚方式。

不归档 app 目录内容、SDK 产物、raw log、凭证或完整会话记录；不代表团队级 NFS 标准，也不写入 memory。

## 目标

将 SigmaStar demo app 输出目录通过主机 NFS 导出，供嵌入式设备挂载使用。

主机导出路径：

```text
~/nfs/app
```

真实源目录：

```text
~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/out/arm/app
```

设备侧优先使用的主机 IP：

```text
192.168.1.41
```

## 主机配置

`~/nfs/app` 是一个持久化 bind mount。Hub 归档中主机 home 路径统一写成 `~`；写入 `/etc/fstab` 或设备端 mount 命令时必须展开为主机真实 home 目录。

```fstab
~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/out/arm/app ~/nfs/app none bind,nofail,x-systemd.requires-mounts-for=/vsdata 0 0
```

NFS 导出配置在 `/etc/exports`：

```exports
~/nfs/app *(rw,sync,no_subtree_check,no_root_squash,insecure)
```

`nfs-kernel-server` 已设置为开机自启。

## 设备端挂载

NFSv3 常用命令：

```sh
mkdir -p /mnt/app
mount -t nfs -o nolock,vers=3 192.168.1.41:~/nfs/app /mnt/app
```

若设备支持 NFSv4，可测试：

```sh
mkdir -p /mnt/app
mount -t nfs -o vers=4 192.168.1.41:~/nfs/app /mnt/app
```

设备侧验证：

```sh
mount | grep /mnt/app
ls -la /mnt/app
```

## 主机验证

确认 bind mount：

```sh
rtk findmnt ~/nfs/app
```

确认导出：

```sh
rtk showmount -e 127.0.0.1
```

确认服务自启和运行态：

```sh
rtk systemctl is-enabled nfs-kernel-server
rtk systemctl is-active nfs-kernel-server
```

修改 `/etc/exports` 后重载：

```sh
rtk sudo exportfs -ra
```

## 已验证证据

2026-07-02 已执行并通过：

- `rtk findmnt --verify --verbose`：`0 parse errors, 0 errors`；存在一个既有 swap warning，与本次 NFS 配置无关。
- `rtk mount -a`：按 `/etc/fstab` 验证挂载。
- 模拟重启关键路径：先卸载 `~/nfs/app`，再执行 `mount ~/nfs/app`，结果成功。
- `showmount -e 127.0.0.1` 可见 `~/nfs/app` 对应的展开路径已导出。
- `nfs-kernel-server` 状态：`enabled` 且 `active`。

## 回滚

临时取消主机 bind mount：

```sh
rtk sudo umount ~/nfs/app
```

完全停用该共享：

1. 从 `/etc/exports` 移除 `~/nfs/app` 对应的展开路径导出行。
2. 从 `/etc/fstab` 移除 `~/nfs/app` 对应的展开路径 bind mount 行。
3. 执行：

```sh
rtk sudo exportfs -ra
rtk sudo systemctl daemon-reload
```

## Provenance

- 当前本机文档：`~/nfs/README-nfs-app.md`
- `/etc/fstab` 修改前备份：`/etc/fstab.bak-nfs-app-20260702131334`
- 旧断链备份：`~/nfs/app.symlink-backup-20260702130737`
- captured_at: 2026-07-02
- last_verified: 2026-07-02
