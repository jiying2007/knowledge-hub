# PCR02 /customer ro SD 升级阶段归档 2026-05-26

## 归档边界

- 状态：历史会话证据，archive-only。
- 当前事实边界：本文只记录 2026-05-26 UBIFS `/customer` 阶段的一次构建与静态校验，不是当前 PCR02 release truth。
- 后续覆盖口径：PCR02 `/customer` 后续已演进为 `ubi0_3` static volume + `/dev/ubiblock0_3` SquashFS 只读挂载；当前分区与 OTA 口径以 `projects/pcr02/archive/engineering-archive/pcr02/decision-index.md` 和 `projects/pcr02/archive/engineering-archive/pcr02/ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/` 为准。
- 删除边界：旧 Codex archive 正文仍未删除；删除必须另走授权、tombstone、rollback 和验证批次。

## 来源

- source_path: `domains/codex/archive/codex-archive/session-wrap/20260526-162109-pcr02-session-wrap-20260526-customer-ro-sd-upgrade.md`
- source_sha256: `f5044d662e42b4e11b259ee2137b42be6774c3259fe7e3fb3fc7bbdb1ef01c62`
- source_captured_at: `2026-05-26`
- migrated_at: `2026-07-10`
- source_project: `pcr02_ssc305_compile`

## 历史结论

2026-05-26 这次 dirty build 的目标是降低 `/customer` UBIFS 运行态写入风险，并产出 SD 升级包用于后续上板验证。该阶段判断是：

- `/customer` 正常运行态应没有必需写路径，主要承载 app、lib 和静态资源。
- 当时将 `spinand_MX35_512M.squashfs.partition.config` 中 `customer$(MOUNTPARAM)` 改为 `-o ro,noatime`。
- 生成的 `rcS` 静态检查包含：`mount -t ubifs ubi0:customer /customer -o ro,noatime`。
- OTA、归档或产测校准如果确需写 `/customer`，应进入维护态，显式 remount rw，完成 `sync` / `fsync` 后再 remount ro。

上述结论已被后续 SquashFS static volume 方案替代为当前实现口径；本文只保留其历史阶段价值。

## 构建证据

当时执行过两条主命令，退出码均为 0：

```bash
rtk bash -lc './build.sh compile --profile ap6303bh_512m_v20 --jobs 16 --allow-dirty --no-sync-sources'
rtk bash -lc './build.sh package --profile ap6303bh_512m_v20 --pack sd --skip-defconfig --allow-dirty --no-sync-sources'
```

当时还完成了针对配置文件的 diff 检查：

```bash
rtk git diff --check -- SourceCode/project/image/configs/general/spinand_MX35_512M.squashfs.partition.config
```

`--allow-dirty --no-sync-sources` 是刻意选择：避免构建过程同步源码时覆盖本地挂载参数修改。因此这条记录不能被解读为干净发布构建。

## SD 制品证据

当时 SD 输出目录为 `SourceCode/project/image/output/images/Sd_Upgrade/`，记录到的主要制品为：

| 制品 | 大小 |
| --- | --- |
| `IPL` | 35.1K |
| `IPL_CUST` | 21.0K |
| `UBOOT` | 226.4K |
| `SigmastarUpgradeSD.bin` | 112.4M |

`SigmastarUpgradeSD.bin` SHA256：

```text
815b6cc3d558190530bdfc21c73425767c546b354a44a178b701738d9cce121e
```

该 hash 只证明当时 host 侧构建产物身份，不证明该 SD 包已通过上板烧录、启动或 OTA 实机验证。

## 风险与未验证项

- 未做上板烧录、启动和 OTA 实机验证；不能声明现场升级通过。
- 当时 dirty worktree 至少包含有效配置修改、构建生成的 `.dep` 变化，以及构建生成二进制 `.so` 变化；提交前需要另行确认纳入或还原。
- `/config`、`/factory`、`/ota`、`/data` 的 UBIFS 风险建议只代表 2026-05-26 阶段分析，不自动成为当前分区决策。

## 当时后续分区建议

- `/config`：启动关键内容，运行态写入风险仅次于 `/customer`；应审计真实写路径，确认无必须写入后再考虑 `ro,noatime`。
- `/factory`：设备个体数据，倾向正常态 `ro,noatime`，产测或校准窗口短时 remount rw。
- `/ota`：维护态写入分区，已有 `noatime,bulk_read`；重点转向升级状态机和断电恢复。
- `/data`：运行态写分区，不适合只读；更适合先加 `noatime`，并治理原子写和日志轮转。

## 相关覆盖

- `projects/pcr02/archive/engineering-archive/pcr02/decision-index.md`
- `projects/pcr02/archive/engineering-archive/pcr02/README.md`
- `projects/pcr02/archive/engineering-archive/pcr02/ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/verified-layout.md`
- `projects/pcr02/archive/engineering-archive/pcr02/partition-storage/pcr02_rootfs_customer_data_symlink_policy_20260606.md`
- `projects/pcr02/archive/engineering-archive/pcr02/validation/pcr02_sd_usb_batch_flash_runbook_20260606.md`
- `artifacts/manifests/codex-archive-extract-first-preflight-20260710.jsonl#CAEF-20260710-003`

## 脱敏与保留策略

- 未复制 raw session、完整构建日志、运行态日志、token、cookie、private key、cache、core 或 binary。
- 只保留命令、退出码摘要、静态校验结果、产物尺寸、hash、风险边界和旧 archive provenance。
- 旧 source 中的会话式包装、memory candidate 语气和一次性过程描述不迁移。
