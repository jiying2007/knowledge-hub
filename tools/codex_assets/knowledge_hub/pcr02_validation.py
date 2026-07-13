"""Deterministic evidence-readiness hardening for three PCR02 decision candidates."""

from __future__ import annotations

import datetime as dt
import copy
import pathlib
from typing import Any, Dict, List, Mapping

from .common import (
    KnowledgeHubError,
    encode_jsonl,
    file_sha256,
    registry_items,
    render_markdown,
    split_frontmatter,
)
from .store import RepositoryTransaction


MANAGED_START = "<!-- pcr02-owner-device-release-validation:start -->"
MANAGED_END = "<!-- pcr02-owner-device-release-validation:end -->"
MANIFEST_PATH = "artifacts/manifests/pcr02-owner-ready-validation-paths-20260713.md"

TARGETS = {
    "pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711": {
        "owner_roles": ["PCR02 product decision owner", "display/BSP owner", "hardware/EMC owner", "release owner"],
        "section": """### 1. Owner 决策路径

- `decision_owner=unassigned`。Hub 维护人和既有 `accept-as-review-record` 记录均不等于产品 owner 签收。
- 产品 decision owner 必须对 36MHz 稳态档、40/43MHz 候选档、54MHz 观感档逐项给出 `accept/modify/reject`，并固定适用硬件版本、环境上限、刷新面积约束和降档阈值。
- display/BSP owner 负责 DTS、fbtft、MSPI 实际时钟和应用刷新策略；hardware/EMC owner 负责信号完整性及 EMI 风险；release owner 负责制品和回滚。角色可由同一真人承担，但每个责任必须显式记录。

### 2. Source 与制品身份

- 记录 remote key `robot/xcrz_sigmastar_demo`、source commit、分支、dirty 状态，以及实际使用的 kernel/DTS/config commit。
- 记录可复现构建入口、返回码、构建环境版本和 `uImage`/DTB/rootfs 或目标升级包 SHA256；不得只引用工作区目录或会话结论。
- 将 36MHz、40/43MHz、54MHz 三档配置 diff 与制品一一对应；无法从当前 commit 重建的制品不得进入设备矩阵。

### 3. 高温老化矩阵

owner 在执行前填写产品规范中的温度、供电、样机数和时长，不由 Hub 猜测规格。每个时钟档至少记录：

| 维度 | 必填证据 |
|---|---|
| 样机与版本 | 脱敏设备编号、PCB/屏模组批次、固件版本、制品 hash |
| 环境 | 箱体设定温度、板上实测温度、供电标称/下限、起止时间、累计 display-hours |
| 负载 | 双屏动画刷新面积、Wi-Fi/录像/AI/CPU 负载组合、亮度与休眠/唤醒循环 |
| 结果 | 白屏、花屏、残影、SPI timeout、初始化失败、重启次数及每 display-hour 失败率 |
| 证据 | 关键日志摘要、异常截图/视频引用、`dmesg` 时间窗口、复现步骤和处置 |

任何异常都必须关联时钟档、设备、温度和制品；只写“老化通过”不构成证据。

### 4. SCLK、信号完整性与 EMI

- 在两路 LCD 的 SCLK、CS、DC、MOSI 及电源/地参考上记录测点、探头、带宽、采样率和负载条件。
- 对 36MHz、40/43MHz、54MHz 分别保存实际频率、占空比、上升/下降时间、过冲/下冲、振铃、毛刺、CS/DC setup/hold 和帧间隙判断。
- 常温、高温和供电下限均需复核；驱动配置值不能替代示波器实测值。
- EMI 由 hardware/EMC owner 按产品适用标准确定预扫或正式测试条件，记录频段、天线/探头、最差档和裕量；“无明显干扰”不能替代测量。
- 若 54MHz 缺少信号或 EMI 裕量，release 必须锁定低一档并验证降档制品。

### 5. 端到端双屏显示验证

- 固定链路：应用测试图/动画 -> `/dev/fb0`、`/dev/fb1` 用户态 buffer -> fbtft deferred I/O -> MSPI -> 两块 ST77912 面板。
- 使用带帧号、颜色块、边界线和交替眼图案的确定性序列，记录应用提交时间、驱动刷新时间、实际帧率、丢帧、撕裂、花屏、残影和卡顿。
- 分别覆盖单屏、双屏交错、双屏同时、局部刷新、短时满帧、冷启动、热启动、休眠唤醒和长跑；视频或仪器证据必须能关联设备、制品和时钟档。
- 应用 buffer CRC 只能证明提交内容；必须同时有面板端观察或仪器证据，才能证明端到端显示正确。

### 6. Release 与回滚

- release owner 记录候选制品、设备矩阵结果、已知限制、发布说明和目标版本；缺少任一高温/SCLK/EMI/端到端证据时状态保持 `reviewing`。
- 在目标板实际验证 54 -> 43/40 -> 36MHz 以及 fps 降档的回滚制品可启动、双屏可显示、配置与版本可识别。
- promotion 只能在真实 owner 签收、所有必需证据引用可恢复且 product gate 无技术 blocker 后另行授权执行；本节不提供 promotion 授权。""",
    },
    "pcr02-st77912-fb-mi-fb-boundary-decision-20260711": {
        "owner_roles": ["PCR02 product decision owner", "display/BSP owner", "application owner", "release owner"],
        "section": """### 1. Owner 决策路径

- `decision_owner=unassigned`；既有内容复核记录只证明候选可读，不证明 framebuffer 边界已被产品 owner 接受。
- owner 必须确认适用硬件/固件版本，并对 `/dev/fb0`、`/dev/fb1`、`/dev/fb2` 的角色、应用依赖和未来失效条件作出明确决定。

### 2. Source 与运行态证据

- 记录 remote key `robot/xcrz_sigmastar_demo`、source commit、kernel/DTS/config commit、应用 commit 和构建制品 SHA256。
- 在同一目标制品上保存 `/proc/fb`、`/sys/class/graphics/fb*/name`、geometry/stride/smem_len，以及应用进程实际打开节点的 `/proc/<pid>/fd` 或等价证据。
- 将 `DisplayProvider` 节点配置、两个 ST77912 DTS 节点、fbtft 驱动注册和 `mi_fb` 配置引用到确切 commit/line；目录存在或旧会话输出不能替代当前 source identity。

### 3. 端到端边界验证

- 分别向 `/dev/fb0`、`/dev/fb1` 和 `/dev/fb2` 写入可区分的确定性测试图，确认物理输出目标和日志链路。
- 覆盖冷启动、重启、模块/驱动初始化顺序变化和发布配置，确认 framebuffer 编号未漂移；若编号可能变化，应用必须改用稳定身份发现或显式失败。
- 验证 `mi_fb` 参数变化只影响 SStar FB 路径，不被误报为 ST77912 双屏优化；验证 fbtft/SPI 参数变化能在双小屏观察到预期效果。

### 4. Release 与回滚

- 发布说明必须列出 display provider、DTS/fbtft、SStar FB/MI_FB 的边界，并标明适用 commit 与设备版本。
- 回滚到上一制品后重复 `/proc/fb`、sysfs、应用打开节点和三路测试图检查；不能只证明系统启动。
- owner、source、目标设备和 release 证据未闭环时保持 `reviewing`，不得因当前一次 `/proc/fb` 观察自动提升 active。""",
    },
    "pcr02-camera-raw-preview-virtual-stream-architecture-20260711": {
        "owner_roles": ["PCR02 product decision owner", "camera/media owner", "protocol/API owner", "application/AI owner", "release owner"],
        "section": """### 1. Owner 决策路径

- `decision_owner=unassigned`。既有 proto/build 通过和 review record 不等于架构 owner、协议 owner 或 release owner 签收。
- owner 必须确认单物理 RAW_PREVIEW + 三虚拟流 fan-out、旧 DS1/DS2 alias 生命周期、SHM padded payload 契约、消费者兼容边界和回滚方案。

### 2. Source、构建与制品身份

- 记录 remote key `robot/xcrz_sigmastar_demo`、source commit、proto 生成器版本、依赖版本、dirty 状态及明确 source file list。
- 复跑 proto 生成、目标构建和定向测试，保存命令、返回码、关键日志摘要及目标镜像/应用/协议制品 SHA256。
- 单独关闭 `pcr02/dep.mk` 发布打包风险，证明目标镜像实际包含预期应用和库；源码 build pass 不能替代镜像内容验证。

### 3. 实机功能与并发矩阵

| 场景 | 必填检查 |
|---|---|
| 单消费者 | `LCD_PREVIEW`、`QR_SCAN`、`VISION_RGB` 分别启停，验证格式、尺寸、stride、frame size、颜色和释放 |
| 双/三消费者 | 逐组合并发，验证一个消费者阻塞/退出不会卡住其他流或泄漏 physical reader refcount |
| 兼容客户端 | 旧 `DS1_RAW`/`DS2_RAW` alias 与新枚举互操作，未知/重复订阅返回码稳定 |
| SHM 契约 | `VISION_RGB` valid 640x360 区域正确，640x640 readable tail 为确定性黑色，无越界和旧帧泄漏 |
| 消费链路 | LCD、QR、AI、diag/product test 使用实际发布二进制端到端读取，不只调用 producer 单测 |

每个场景记录设备/固件、帧计数、首帧延迟、持续帧率、drop/timeout、CPU、RSS/SHM、图像正确性和关键日志。长跑时长与通过阈值由 owner 在执行前按产品要求填写。

### 4. 故障、恢复与 soak

- 覆盖消费者异常退出、重复 acquire/release、producer 重启、SHM reader 超时、camera source 短暂失败和系统休眠/唤醒。
- 检查 physical source refcount 回到零、SHM 无陈旧敏感帧、恢复后 metadata/stream id/stride 正确，并执行 ASAN 或适用内存诊断。
- soak 结果必须关联 source commit、设备、负载、时长和失败计数；“运行一段时间正常”不构成发布证据。

### 5. Release 与回滚

- release owner 核对协议兼容、镜像内容、应用消费者 smoke、升级/降级路径和发布说明；记录制品 hash 与目标设备验收。
- 回滚制品必须能恢复旧 DS1/DS2 行为或明确拒绝新客户端，并验证升级后产生的 SHM/配置不会破坏旧版本。
- 缺少 owner、实机并发/soak、镜像内容或回滚证据时保持 `reviewing`，不得按 implementation archive 自动提升 active。""",
    },
}


def _managed_section(body: str, section: str) -> str:
    block = """{start}
## Owner、实机与发布验证门禁

> 本节定义真实验证路径，不表示任何命令已经执行，也不是 owner decision、active promotion 或 release 授权。

{section}

### 证据落地契约

- 证据记录必须包含 `owner_identity`、`source_commit`、`artifact_sha256`、`device_identity`、`environment`、`commands`、`exit_codes`、`result_summary`、`rollback_result` 和可恢复引用。
- raw log、视频、截图和二进制只保存在受控外部制品位置；Hub 正文只保存脱敏摘要、hash 和引用。
- 最终复核命令：`rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --full-regression --as-of 2026-07-13`。
{end}""".format(start=MANAGED_START, section=section, end=MANAGED_END)
    has_start = MANAGED_START in body
    has_end = MANAGED_END in body
    if has_start != has_end:
        raise KnowledgeHubError("PCR02 managed validation markers are incomplete")
    if has_start:
        managed = body.split(MANAGED_START, 1)[1].split(MANAGED_END, 1)[0]
        if "### 证据落地契约" not in managed:
            raise KnowledgeHubError("PCR02 managed validation contract is incomplete")
        return body
    return body.rstrip() + "\n\n" + block + "\n"


def _initialize_candidate_contract(
    item: Mapping[str, Any],
    contract: Mapping[str, Any],
    path: str,
    today: dt.date,
) -> Dict[str, Any]:
    result = copy.deepcopy(dict(item))
    before = copy.deepcopy(result)
    result.setdefault("status", "reviewing")
    result.setdefault("promotion", "none")
    result.setdefault("decision_owner", "unassigned")
    result.setdefault("decision_status", "candidate")
    result.setdefault("manual_validation_pending", True)
    result.setdefault("review_scope", "content-review-record-only-not-owner-approval")
    result.setdefault("owner_roles_required", list(contract["owner_roles"]))
    result.setdefault(
        "evidence_readiness",
        {
            "owner": "pending-real-owner-assignment-and-decision",
            "source": "pending-current-commit-and-artifact-identity",
            "device": "pending-real-device-or-lab-evidence",
            "release": "pending-release-and-rollback-evidence",
            "validation_path": MANIFEST_PATH,
        },
    )
    validation_refs = list(result.get("validation_refs", []))
    for required in (path, MANIFEST_PATH):
        if required not in validation_refs:
            validation_refs.append(required)
    if not validation_refs:
        validation_refs.extend(
            [
                "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of {}".format(
                    today
                ),
                "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --as-of {}".format(
                    today
                ),
            ]
        )
    result["validation_refs"] = validation_refs
    if result != before:
        result["updated_at"] = today.isoformat()
    return result


def _manifest() -> str:
    rows = [
        "# PCR02 owner-ready validation paths 2026-07-13",
        "",
        "## 边界",
        "",
        "本记录把三条 PCR02 candidate 固定为 `reviewing + decision_owner=unassigned + manual_validation_pending=true`，并给出真实 source、实机和 release 证据路径。它不是 owner decision，不关闭 owner gate，不提升 active，不修改源项目，不写 memory。",
        "",
        "## 候选入口",
        "",
    ]
    for item_id in TARGETS:
        rows.append("- `{}`".format(item_id))
    rows.extend(
        [
            "",
            "## 统一成熟条件",
            "",
            "- Owner：真实产品/技术/release 责任人明确接受、修改或拒绝，不使用 Hub maintainer 或 delegated review 代签。",
            "- Source：remote key、commit、dirty 状态、构建环境、命令、返回码和制品 SHA256 可复现。",
            "- Device：设备/板卡/屏模组身份、固件、环境、负载、时长、阈值和结果可关联。",
            "- Release：发布镜像内容、版本、升级/降级、回滚和发布说明经过目标设备验证。",
            "- Promotion：以上证据齐备后仍需独立 authorization；本记录的存在不提供 promotion 权限。",
            "",
            "## ST77912 强制证据",
            "",
            "- 高温老化：三档时钟与产品规范温度/供电/负载矩阵，按 display-hours 记录异常率。",
            "- SCLK/EMI：SCLK、CS、DC、MOSI 波形和 EMI 风险/裕量由 hardware/EMC owner 复核。",
            "- 端到端显示：应用 buffer、fbdev/fbtft、MSPI 和两块面板的帧号/图案链路共同证明，不以单层 CRC 替代。",
            "",
            "## 当前状态",
            "",
            "截至 2026-07-13，上述路径已定义，但真实 owner、当前 source commit、目标设备矩阵和 release/rollback 证据未在 Hub 登记。三条 candidate 均保持 `reviewing`，不得声明 release-ready 或 active。",
            "",
            "## 验证",
            "",
            "```bash",
            "rtk bash ~/knowledge-hub/tools/knowledge-pcr02-owner-readiness.sh --check --json --as-of 2026-07-13",
            "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-13",
            "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --as-of 2026-07-13",
            "```",
        ]
    )
    return "\n".join(rows) + "\n"


def _add_text(transaction: RepositoryTransaction, root: pathlib.Path, path: str, content: str) -> None:
    target = root / path
    transaction.add_text(path, content, expected_sha256=file_sha256(target) if target.exists() else "")


def harden_pcr02_validation(root: pathlib.Path, today: dt.date, apply: bool = False) -> Dict[str, Any]:
    items = registry_items(root)
    by_id = {str(item.get("id", "")): item for item in items}
    missing_ids = sorted(set(TARGETS) - set(by_id))
    if missing_ids:
        raise KnowledgeHubError("missing PCR02 candidates: {}".format(", ".join(missing_ids)))
    transaction = RepositoryTransaction(root)
    rows: List[Dict[str, Any]] = []
    for item_id, contract in TARGETS.items():
        original_item = by_id[item_id]
        original_snapshot = copy.deepcopy(original_item)
        item = _initialize_candidate_contract(
            original_item,
            contract,
            str(original_item["path"]),
            today,
        )
        by_id[item_id].clear()
        by_id[item_id].update(item)
        path = str(item["path"])
        target = root / path
        if not target.exists():
            raise KnowledgeHubError("candidate body missing: {}".format(path))
        metadata, body = split_frontmatter(target.read_text(encoding="utf-8"))
        for field in (
            "status",
            "promotion",
            "decision_owner",
            "decision_status",
            "manual_validation_pending",
            "review_scope",
            "owner_roles_required",
            "evidence_readiness",
            "validation_refs",
            "updated_at",
        ):
            metadata[field] = item[field]
        related = metadata.get("related", [])
        related = related if isinstance(related, list) else [related]
        if MANIFEST_PATH not in related:
            related.append(MANIFEST_PATH)
        metadata["related"] = related
        rendered = render_markdown(metadata, _managed_section(body, str(contract["section"])))
        _add_text(transaction, root, path, rendered)
        rows.append(
            {
                "id": item_id,
                "path": path,
                "status": item["status"],
                "decision_owner": item["decision_owner"],
                "manual_validation_pending": item["manual_validation_pending"],
                "owner_role_count": len(contract["owner_roles"]),
                "lifecycle_preserved": all(
                    item.get(field) == original_snapshot.get(field)
                    for field in (
                        "status",
                        "promotion",
                        "decision_owner",
                        "manual_validation_pending",
                    )
                ),
            }
        )
    _add_text(transaction, root, "registry/items.jsonl", encode_jsonl(items))
    manifest_target = root / MANIFEST_PATH
    _add_text(
        transaction,
        root,
        MANIFEST_PATH,
        manifest_target.read_text(encoding="utf-8") if manifest_target.exists() else _manifest(),
    )
    plan = transaction.plan()
    result: Dict[str, Any] = {
        "schema_version": 1,
        "action": "harden-pcr02-owner-device-release-validation",
        "status": "planned",
        "candidate_count": len(rows),
        "candidates": rows,
        "reviewing_only": all(row["status"] == "reviewing" for row in rows),
        "decision_owner_default": "initial-only:unassigned",
        "manual_validation_pending": all(row["manual_validation_pending"] for row in rows),
        "lifecycle_preserved": all(row["lifecycle_preserved"] for row in rows),
        "active_promotion": False,
        "source_project_write": False,
        "manifest": MANIFEST_PATH,
        "transaction": {
            "transaction_id": plan["transaction_id"],
            "write_count": plan["write_count"],
            "changed_count": plan["changed_count"],
        },
    }
    if apply:
        applied = transaction.apply()
        result["status"] = applied.status
        result["transaction"].update(
            {
                "journal": applied.journal,
                "changed_count": len(applied.changed_paths),
                "unchanged_count": len(applied.unchanged_paths),
            }
        )
    return result
