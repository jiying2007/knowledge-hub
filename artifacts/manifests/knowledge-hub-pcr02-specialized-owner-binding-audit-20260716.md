# PCR02 3 项专项 Owner 绑定落地审计（2026-07-16）

## 结论

真实 owner attestation 已按 Packet 三行机械落地：三项均绑定 `decision_owner=leiwenjun`、同一 `owner_attestation_ref`、精确 `owner_decision` 与 `decision_status=accepted-boundary-evidence-pending`。三项继续保持 `status=reviewing`、`promotion=none`、`manual_validation_pending=true`；本次没有 active promotion、release approval、evidence-ready 或任何工程/设备/采用通过声明。

- Audit ID：`knowledge-hub-pcr02-specialized-owner-binding-audit-20260716`
- Attestation ID：`knowledge-hub-pcr02-specialized-owner-attestation-20260716`
- Attestation JSONL SHA256：`7a057f5c45b68c75b40067d6d2f51441bfed505e1f74b5741e68137c6ae6a47b`
- Packet JSONL SHA256：`ed72da24c54207f6a52189cc2b11f88a7ac15a10dfce0166460023c9d0ca5e88`
- Owner：`leiwenjun`
- 机器可读审计：`artifacts/manifests/knowledge-hub-pcr02-specialized-owner-binding-audit-20260716.jsonl`

## 落地结果

| 检查项 | 结果 | 边界 |
| --- | ---: | --- |
| `decision_owner=leiwenjun` | 3/3 | 只绑定 Packet 中三项 |
| `owner_attestation_ref` | 3/3 | 指向同一 hash-bound attestation |
| 精确 `owner_decision` | 3/3 | 分别等于 Packet 对应行 `proposed_decision` |
| `decision_status=accepted-boundary-evidence-pending` | 3/3 | 边界已接受，证据仍待补 |
| `status=reviewing` | 3/3 | 未提升 active |
| `promotion=none` | 3/3 | 无 lifecycle promotion |
| `manual_validation_pending=true` | 3/3 | 实机与发布验证继续待补 |
| release/evidence-ready | 0/3 | 没有批准或推导 |

## 逐项正文绑定

| Item | Before SHA256 | After SHA256 | Owner Decision | Result |
| --- | --- | --- | --- | --- |
| `pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711` | `062bbbf0043746dce564e53e4355e634dbcf7777b92c14fa7ef4221ebc381801` | `87c2dd44ac8e93f64b6bcb29b39e6244ce43eac6a62ac261c257a862d4dd5623` | `accept-36mhz-stable-baseline-higher-clocks-validation-only-remain-reviewing` | pass |
| `pcr02-st77912-fb-mi-fb-boundary-decision-20260711` | `ff3d406e09035869822ff2b176fcc40b81dda32c2c9024adab26e261650bf2ed` | `a1e0c6c0aac4ee28f3d488f070594128af4cea0ad9d3b0fe4c6a1550bdea7170` | `accept-fbtft-st77912-vs-mi-fb-boundary-remain-reviewing` | pass |
| `pcr02-camera-raw-preview-virtual-stream-architecture-20260711` | `f2858a2ce1d5e9eba150b8af4dd1194d3059dda6b85b48967c34bc27a0d12df6` | `22c93d37799f2b86f69441c6bfcd6e5a660a489935892dd5590962204ac1c2d9` | `accept-single-raw-preview-three-virtual-stream-contract-remain-reviewing` | pass |

正文 after hash 变化只来自 owner attestation 字段、owner 决定、日期、禁止边界说明与一致的 evidence-readiness owner 状态；Packet 绑定的 before hash 保留在 attestation 和本审计中。

## 验证证据

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk sha256sum ...specialized-owner-boundary-packet-20260716.jsonl` | 0 | SHA256 与 owner 回复一致。 | Packet JSONL | Owner Review | Packet |
| 三份 decision `sha256sum`（绑定前） | 0 | 3/3 与 Packet `body_sha256` 一致。 | Packet 与 decision 正文 | Owner Review | Attestation |
| `knowledge-pcr02-owner-readiness --check`（schema 更新前） | 1 | stale schema 仍要求 `initial-only:unassigned`，阻断 apply；随后同步 schema。 | 命令输出 | Workflow | 负结果/被证伪路径 |
| `knowledge-pcr02-owner-readiness --apply --as-of 2026-07-16` | 0 | 3 项 owner 字段通过事务工具写入，无 active promotion。 | transaction journal | Workflow | 本审计 |
| `pytest -q tests/test_pcr02_validation.py tests/test_schemas.py tests/test_project_readiness.py` | 0 | 18 个定向测试通过。 | pytest 输出 | Workflow | 本审计 |

## 剩余边界

- ST77912 的高温、SCLK/EMI、端到端双屏、设备、发布和降档回滚证据仍未闭环。
- framebuffer 边界仍需当前固件和目标设备重采 `/proc/fb`、sysfs、应用实际节点，并补发布/回滚证据。
- RAW_PREVIEW fan-out 仍需设备并发/soak、镜像打包、协议兼容、消费者端到端和回滚验证。
- 本审计不提供 active promotion、release approval、evidence-ready、源项目/memory/远端写入授权。
