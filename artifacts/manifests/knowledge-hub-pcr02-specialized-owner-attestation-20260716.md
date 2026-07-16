# PCR02 3 项专项 Owner Attestation（2026-07-16）

## 结论

真实 owner `leiwenjun` 已对 Packet `knowledge-hub-pcr02-specialized-owner-boundary-20260716` 作出 hash-bound 确认，接受全部 3 行各自的 `proposed_decision`。本 attestation 只确认三项专项技术边界和 decision owner；候选继续保持 `reviewing`，所有工程、实机、制品、发布、回滚和采用证据继续保持 pending。

- Attestation ID：`knowledge-hub-pcr02-specialized-owner-attestation-20260716`
- Packet Manifest：`artifacts/manifests/knowledge-hub-pcr02-specialized-owner-boundary-packet-20260716.jsonl`
- Packet Manifest SHA256：`ed72da24c54207f6a52189cc2b11f88a7ac15a10dfce0166460023c9d0ca5e88`
- Packet 行数：3
- Owner：`leiwenjun`
- 确认码：`KH-PCR02-ED72DA24C542`
- 确认日期：2026-07-16
- 机器可读记录：`artifacts/manifests/knowledge-hub-pcr02-specialized-owner-attestation-20260716.jsonl`

## 用户原始显示文本

以下代码块按本轮用户消息保留 quote 标记、空白和视觉换行：

```text
> 我是 leiwenjun。我已复核 Packet knowledge-hub-pcr02-specialized-owner-boundary-20260716，Manifest
  > SHA256 为 ed72da24c54207f6a52189cc2b11f88a7ac15a10dfce0166460023c9d0ca5e88，共 3 项；我接受全部行
  > 各自的 proposed_decision，确认码 KH-PCR02-ED72DA24C542。我授权 Codex 将本回复记录为 hash-bound
  > owner attestation，并按各行机械绑定 decision_owner=leiwenjun、owner_attestation_ref 与
  > decision_status=accepted-boundary-evidence-pending。本确认不授权 active promotion、release
  > approval 或 evidence-ready，不声明任何高温/SCLK/EMI、设备 soak、镜像打包、协议兼容、回滚或采用反馈
  > 已经通过。
```

## 规范化绑定文本

> 我是 leiwenjun。我已复核 Packet `knowledge-hub-pcr02-specialized-owner-boundary-20260716`，Manifest SHA256 为 `ed72da24c54207f6a52189cc2b11f88a7ac15a10dfce0166460023c9d0ca5e88`，共 3 项；我接受全部行各自的 `proposed_decision`，确认码 `KH-PCR02-ED72DA24C542`。我授权 Codex 将本回复记录为 hash-bound owner attestation，并按各行机械绑定 `decision_owner=leiwenjun`、`owner_attestation_ref` 与 `decision_status=accepted-boundary-evidence-pending`。本确认不授权 active promotion、release approval 或 evidence-ready，不声明任何高温/SCLK/EMI、设备 soak、镜像打包、协议兼容、回滚或采用反馈已经通过。

规范化只移除 Markdown quote 前缀与视觉换行；Packet ID、完整 SHA256、行数、决定、确认码、owner、授权效果和禁止边界均未改变。

## 逐项决定

| Item | Owner Decision | Owner 已接受的边界 | 继续 pending 的证据 |
| --- | --- | --- | --- |
| `pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711` | `accept-36mhz-stable-baseline-higher-clocks-validation-only-remain-reviewing` | 36MHz 为稳态默认；40/43MHz、54MHz 仅作验证档 | 高温、SCLK/EMI、设备、发布和回滚 |
| `pcr02-st77912-fb-mi-fb-boundary-decision-20260711` | `accept-fbtft-st77912-vs-mi-fb-boundary-remain-reviewing` | 当前范围内 fb0/fb1 属于 fbtft/ST77912，fb2 属于 SStar/MI_FB | 当前固件、设备、发布和回滚 |
| `pcr02-camera-raw-preview-virtual-stream-architecture-20260711` | `accept-single-raw-preview-three-virtual-stream-contract-remain-reviewing` | 接受单 RAW_PREVIEW 与三虚拟流 fan-out；DS1/DS2 仅为临时兼容 alias | 设备 soak、镜像打包、协议兼容、发布和回滚 |

## 机械绑定效果

- 三项统一绑定 `decision_owner=leiwenjun`。
- 三项统一绑定 `owner_attestation_ref=artifacts/manifests/knowledge-hub-pcr02-specialized-owner-attestation-20260716.md`。
- 三项统一记录 `decision_status=accepted-boundary-evidence-pending`，并分别保存 Packet 中的 `proposed_decision`。
- `status=reviewing`、`promotion=none`、`manual_validation_pending=true` 保持不变。
- `evidence_readiness.owner` 只表示专项边界 owner 已接受；source/device/release/rollback 等证据状态不改变。

## 前置验证

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk sha256sum artifacts/manifests/knowledge-hub-pcr02-specialized-owner-boundary-packet-20260716.jsonl` | 0 | Packet SHA256 与 owner 回复完全一致。 | Packet JSONL | Owner Review | `knowledge-hub-pcr02-specialized-owner-boundary-20260716` |
| 三份 decision 正文 `sha256sum` | 0 | 三个正文 SHA256 与 Packet 对应行完全一致，mismatch=0。 | Packet JSONL 与三份 decision 正文 | Owner Review | 本 attestation |
| registry 前置状态审计 | 0 | 三项均为 `decision_owner=unassigned`、`decision_status=candidate`、`status=reviewing`。 | `registry/items.jsonl` | Knowledge Hub | 本 attestation |

## 独立执行授权与禁止边界

本 attestation 保存 owner 内容确认，不以自身替代一般执行授权。本次 Hub 写入同时受 `auth-20260715-knowledge-hub-terminal-maturity-full-closeout` 的仓内 `automation-apply-with-review` 边界约束。

本确认不提供 active promotion、release approval、evidence-ready、源项目写入、memory 写入或远端 Git 写入授权，也不证明高温/SCLK/EMI、设备 soak、镜像打包、协议兼容、回滚或采用反馈已经通过。

## 回滚与失效

- owner 绑定只对 Packet 中 3 个精确 item 和绑定前正文 SHA 生效。
- 如需撤销，只能定向恢复本 attestation 引入的 owner 字段、审计记录和报告字段，不得 reset 或覆盖其他用户变更。
- 未来 active、release approval 或 evidence-ready 必须有新的精确证据和授权，不能从本确认推导。
