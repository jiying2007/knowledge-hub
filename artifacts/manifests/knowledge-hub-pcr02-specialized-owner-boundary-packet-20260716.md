# PCR02 3 项专项 Owner 决策 Packet（2026-07-16）

## 结论

30 项通用 authority-boundary owner 已完成绑定；product gate 仍暴露 3 个 Packet 外 PCR02 专项 decision candidate。本 Packet 把三个候选的当前正文 hash、保守提议、落地效果与禁止边界冻结，供真实 owner 精确决定。生成 Packet 不等于 owner 接受，不修改候选状态。

- Packet ID：`knowledge-hub-pcr02-specialized-owner-boundary-20260716`
- Manifest：`artifacts/manifests/knowledge-hub-pcr02-specialized-owner-boundary-packet-20260716.jsonl`
- Manifest SHA256：`ed72da24c54207f6a52189cc2b11f88a7ac15a10dfce0166460023c9d0ca5e88`
- 项目数：2
- 决策数：3
- 确认码：`KH-PCR02-ED72DA24C542`

## 逐项提议

| Item | 当前正文 SHA256 | Proposed Decision | 保留边界 |
| --- | --- | --- | --- |
| `pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711` | `062bbbf0043746dce564e53e4355e634dbcf7777b92c14fa7ef4221ebc381801` | `accept-36mhz-stable-baseline-higher-clocks-validation-only-remain-reviewing` | 36MHz 作为稳态默认；40/43MHz、54MHz 仅作验证档；高温/SCLK/EMI/设备/回滚均未通过 |
| `pcr02-st77912-fb-mi-fb-boundary-decision-20260711` | `ff3d406e09035869822ff2b176fcc40b81dda32c2c9024adab26e261650bf2ed` | `accept-fbtft-st77912-vs-mi-fb-boundary-remain-reviewing` | 当前范围内 fb0/fb1 属于 fbtft/ST77912，fb2 属于 SStar/MI_FB；仍需当前固件、设备、发布和回滚验证 |
| `pcr02-camera-raw-preview-virtual-stream-architecture-20260711` | `f2858a2ce1d5e9eba150b8af4dd1194d3059dda6b85b48967c34bc27a0d12df6` | `accept-single-raw-preview-three-virtual-stream-contract-remain-reviewing` | 接受单 RAW_PREVIEW + LCD_PREVIEW/QR_SCAN/VISION_RGB fan-out；DS1/DS2 仅临时兼容 alias；设备 soak、打包、兼容与回滚未通过 |

## 接受后的机械效果

若真实 owner 使用下方精确文本确认全部行，Codex 只可：

- 将 3 个 candidate 的 `decision_owner` 绑定为 `leiwenjun`。
- 绑定同一 hash-bound `owner_attestation_ref`。
- 记录 `decision_status=accepted-boundary-evidence-pending` 及各行 `proposed_decision`。
- 保持 `status=reviewing`、`promotion=none`、`manual_validation_pending=true`。
- 保持所有真实设备、制品、发布、回滚和采用结论为 pending。

不得由本 Packet 推导 active promotion、release approval、evidence-ready、高温/SCLK/EMI 通过、设备 soak 通过、镜像打包通过、协议兼容通过或回滚通过。

## 精确确认文本

如接受全部三行，真实 owner 可原样回复：

> 我是 leiwenjun。我已复核 Packet knowledge-hub-pcr02-specialized-owner-boundary-20260716，Manifest SHA256 为 ed72da24c54207f6a52189cc2b11f88a7ac15a10dfce0166460023c9d0ca5e88，共 3 项；我接受全部行各自的 proposed_decision，确认码 KH-PCR02-ED72DA24C542。我授权 Codex 将本回复记录为 hash-bound owner attestation，并按各行机械绑定 decision_owner=leiwenjun、owner_attestation_ref 与 decision_status=accepted-boundary-evidence-pending。本确认不授权 active promotion、release approval 或 evidence-ready，不声明任何高温/SCLK/EMI、设备 soak、镜像打包、协议兼容、回滚或采用反馈已经通过。

若只接受部分行，必须逐项列出 `item_id` 与接受/修改后的 decision；不能用模糊“同意”替代 Packet ID、完整 Manifest SHA256 和确认码。

## 失效条件

- 任一候选正文 hash 变化后，本 Packet 对该行立即失效。
- owner、硬件/固件范围或 proposed decision 变化后，必须重新生成 Packet。
- 执行授权与 owner attestation 必须继续分离；本 Packet 自身不授权写入。
