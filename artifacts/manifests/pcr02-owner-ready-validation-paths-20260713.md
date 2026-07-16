# PCR02 owner-ready validation paths 2026-07-13

## 边界

本记录把三条 PCR02 candidate 固定为 `reviewing + decision_owner=leiwenjun + decision_status=accepted-boundary-evidence-pending + manual_validation_pending=true`，并给出真实 source、实机和 release 证据路径。Owner 边界由 `knowledge-hub-pcr02-specialized-owner-attestation-20260716` 确认；本记录不提升 active，不批准 release，不声明 evidence-ready，不修改源项目，不写 memory。

## 候选入口

- `pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711`
- `pcr02-st77912-fb-mi-fb-boundary-decision-20260711`
- `pcr02-camera-raw-preview-virtual-stream-architecture-20260711`

## 统一成熟条件

- Owner：2026-07-16 已由真实 owner 对三项精确正文和 proposed decision 作出 hash-bound 接受；未来 active、release approval 或边界变化仍需独立决定。
- Source：remote key、commit、dirty 状态、构建环境、命令、返回码和制品 SHA256 可复现。
- Device：设备/板卡/屏模组身份、固件、环境、负载、时长、阈值和结果可关联。
- Release：发布镜像内容、版本、升级/降级、回滚和发布说明经过目标设备验证。
- Promotion：以上证据齐备后仍需独立 authorization；本记录的存在不提供 promotion 权限。

## ST77912 强制证据

- 高温老化：三档时钟与产品规范温度/供电/负载矩阵，按 display-hours 记录异常率。
- SCLK/EMI：SCLK、CS、DC、MOSI 波形和 EMI 风险/裕量由 hardware/EMC owner 复核。
- 端到端显示：应用 buffer、fbdev/fbtft、MSPI 和两块面板的帧号/图案链路共同证明，不以单层 CRC 替代。

## 当前状态

截至 2026-07-16，三项专项边界已由真实 owner 作出 hash-bound 确认；当前 source commit、目标设备矩阵和 release/rollback 证据仍未闭环。三条 candidate 均保持 `reviewing`，不得声明 evidence-ready、release-ready 或 active。

## 验证

```bash
rtk bash ~/knowledge-hub/tools/knowledge-pcr02-owner-readiness.sh --check --json --as-of 2026-07-16
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-16
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --as-of 2026-07-16
```
