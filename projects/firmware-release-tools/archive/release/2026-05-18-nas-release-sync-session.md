# firmware-release-tools NAS 发布同步历史会话 2026-05-18

## 归档边界

- 状态：archive-only historical session。
- 来源：旧 Codex archive `session-wrap/20260518-223626-mcu-session-wrap-firmware-release-nas.md`。
- 适用范围：`firmware-release-tools` 在 2026-05-18 的 NAS 发布同步能力和发布治理历史证据。
- 不声明当前 MCU 发布基线，不替代当前源仓、当前发布记录或真实发布前验证。
- 不包含 NAS 密码、凭据内容、raw logs、cache、binary、cookie、token 或 private key。
- 旧 Codex archive 正文删除仍需独立 delete-or-prune 授权、tombstone、rollback 和删除前复扫。

## 来源

| Field | Value |
| --- | --- |
| source_path | `domains/codex/archive/codex-archive/session-wrap/20260518-223626-mcu-session-wrap-firmware-release-nas.md` |
| source_sha256 | `f4b56957d2d216c1167215048add05d94c493aaaf9cdae110da1054c907fe33c` |
| source_size | `4284 bytes` |
| source_lines | `88` |
| source_captured_at | 2026-05-18 |
| migrated_at | 2026-07-10 |
| preflight_row | `artifacts/manifests/codex-archive-extract-first-preflight-20260710.jsonl#CAEF-20260710-009` |

## 历史结论

2026-05-18 的会话记录显示，`firmware-release-tools` 当时已经形成统一 NAS 发布同步能力：

- 新增 `publish-nas` 发布逻辑，支持 staging、checksum 校验、同版本防覆盖和批次 manifest。
- 新增 `release-to-nas.sh`，串联多个固件的 build/package/check/dry-run 和 NAS 发布计划。
- 新增 `setup-nas-mount.sh`，用于团队本机 CIFS 挂载初始化、凭据文件权限、挂载检查和发布根目录检查。
- 新增 NAS release guide，并把 NAS 发布目录、防覆盖、tag、批次记录和回退规则固化到项目文档。

当时保留的关键治理规则：

- 发布根目录使用 `<mcu-release-nas>/robot/mcu`，不要额外追加 `release` 子目录。
- NAS 密码不得写入仓库、命令示例、日志、manifest 或归档材料。
- 本机凭据文件只作为运行环境配置存在，内容不得归档；权限要求为 `600`。
- `release-to-nas.sh --publish` 必须要求 release root 预先存在且可写，避免 NAS 未挂载时误写本地目录。
- 同版本不存在时先发布到 staging，校验后 rename 到最终目录。
- 同版本同内容时幂等复用，状态为 `existing`。
- 同版本不同内容时立即失败，禁止自动覆盖。
- tag 顺序为先预检 tag，发布门禁通过并写入发布目录后，再创建或推送 app 版本 tag。

## 历史版本与提交

本节只保留 2026-05-18 历史 evidence，不代表当前固件版本或当前发布状态。

| Repository | Historical version or commit |
| --- | --- |
| `gd32l235` | `1.1.18`, commit `b852651` |
| `hc32f072` | `1.1.2`, commit `dabcb82` |
| `mm32spin023c` | `0.0.8`, commit `2ad4bdd` |
| `firmware-release-tools` | commit `992186c` |

## 历史验证摘要

旧会话记录中的验证只作为当时链路证据：

- NAS mount、release root 可写、CIFS 工具和凭据文件检查通过。
- `release-to-nas.sh --dry-run` 对 `gd32l235`、`hc32f072`、`mm32spin023c` 的发布计划和包检查完成。
- `firmware-release-tools` 单测记录为 `12 tests OK`。
- `firmware_release_tools` 与测试包的 Python compileall 通过。
- 四个相关仓库的 `git diff --check` 通过。
- 敏感信息扫描未发现 NAS 明文密码。
- 默认本地 `release/` dry-run 被同版本不同内容阻断，证明防覆盖门禁在当时生效。

## 风险与未验证项

- 历史验证不等于当前 release 通过；真实发布前必须重新执行当前工具链、当前 NAS mount 和当前包校验。
- NAS mount、release root 权限、CIFS 配置和凭据文件状态会随机器漂移。
- 版本号、tag、提交状态和远端分支状态均为 2026-05-18 时间点证据。
- 本归档不写入 memory、不提升 active runbook，也不授权旧 archive 删除。

## 相关覆盖

- 项目入口：`projects/firmware-release-tools/README.md`
- MCU 项目组入口：`projects/mcu/README.md`
- 后续实际发布历史：`projects/mcu/archive/2026-07-10-mcu-release-ir-distance-session.md`
- 迁移预检：`artifacts/manifests/codex-archive-extract-first-preflight-20260710.jsonl#CAEF-20260710-009`
- 旧来源：`domains/codex/archive/codex-archive/session-wrap/20260518-223626-mcu-session-wrap-firmware-release-nas.md`

## 后续处理

- 若要把这些规则提升为当前 runbook，必须基于 `firmware-release-tools` 当前源仓和当前发布流程重新验证。
- 若要删除旧 Codex archive 正文，必须另建删除执行 manifest，并保留 source hash、covered_by、tombstone、rollback、authorization_id 和验证命令。
