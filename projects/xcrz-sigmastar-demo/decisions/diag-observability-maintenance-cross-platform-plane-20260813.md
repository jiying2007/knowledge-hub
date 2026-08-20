---
doc_type: architecture-decision-candidate
decision_id: pcr02-diag-observability-maintenance-cross-platform-plane-20260813
created: 2026-08-13
updated: 2026-08-13
related_decision: pcr02-hdi-hal-cross-platform-host-development-architecture-20260813-v2
platforms:
- SSC305
- SSU9383CM
- RDK X5
- Linux x86_64 Host
- future RTOS
build_policy: current product build rules remain unchanged
id: pcr02-diag-observability-maintenance-cross-platform-plane-20260813
title: Diag、Observability 与 Maintenance 跨平台平面决策候选
kind: decision
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/decisions/diag-observability-maintenance-cross-platform-plane-20260813.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: design-review
  from: reviewed cross-platform diagnostic architecture and repository static evidence
  source_sha256: 378cd9206a1700ee75b2a75b04fde309146009acdcbfdc963d405af03d6a25d0
review_after: '2026-09-13'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- diag
- observability
- maintenance
- security
- cross-platform
- host-test
- rtos
- hdi-hal
- architecture-decision
validation_refs:
- projects/xcrz-sigmastar-demo/decisions/diag-observability-maintenance-cross-platform-plane-20260813.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/decisions/diag-observability-maintenance-cross-platform-plane-20260813.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-13'
updated_at: '2026-08-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-13'
manual_validation_pending: true
summary_zh: 将 Diag 定义为独立正交平面：Common 仅保留稳定无 JSON ABI，runtime、codec、transport、adapter、中央策略、调用租约、持久审计、维护恢复、Host Fake 与 RTOS 静态有界实现均有强制迁移和验收门禁。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- Diag、Observability 与 Maintenance 跨平台平面决策候选
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# Diag、Observability 与 Maintenance 跨平台平面规范

## 1. 决策

Diag 不属于 Common、HDI、API 或 APP 中的单一层，而是一条与业务调用链正交的控制与观测平面：

1. Common 只保留固定宽度、版本化、无 OS、无 JSON、无 transport、无 APP runtime 的诊断 ABI 内核。
2. registry、dispatcher、policy、provider lifecycle、audit、codec 和 transport 属于独立 diag_runtime，由 APP composition root 选择和组装。
3. HDI、API、APP、OSAL 和 backend 各自只暴露本层稳定的 health、metrics、trace、self-test 或维护用例；它们不依赖 diag_runtime，也不主动向 APP 全局符号注册。
4. 位于 diag_runtime 上方的 adapter 把各层公开能力翻译成诊断命令。依赖方向始终是 adapter → 被观测层。
5. 只读 observe 可以通过受限 health port 查询 HDI；任何 self-test 或改变运行状态、配置、介质、固件、硬件行为的操作必须经过 API/APP domain self-test/maintenance use case，禁止从 Diag adapter 直接写 HDI。
6. Observability、Diagnostics、Self-test 和 Maintenance 分开建模。名称前缀不决定安全性，effect metadata 和中央 policy 才是授权依据。
7. Linux 入口可继续兼容 JSON；JSON 不进入 Common contract。RTOS 使用 bounded TLV/CBOR 或静态 typed payload，Linux proxy 可转换为 JSON。
8. 当前 Make 构建规则不变。源码重构使用兼容 shim 和 sidecar 测试分阶段落地，未来 GROS 直接映射本规范定义的 source set、profile 和 limits。

该规范是长期架构 SSOT。具体命令清单由 versioned command manifest 管理，不在不同 provider 源文件中重复定义安全属性。

## 2. 目标与非目标

### 2.1 目标

- 让 SSC305、SSU9383CM、RDK X5、x86_64 Host 和 future RTOS 共用相同诊断语义。
- 防止诊断入口绕过业务 API、权限、状态机、资源所有权和审计。
- 将当前 include/common/diag 中的 APP runtime/JSON 耦合拆出。
- 给生产、售后、产测、Host 和 RTOS 提供显式 profile 与资源预算。
- 支持 provider 热注销、超时、取消、分块结果和进程/核间代理。
- 为所有非只读命令提供 effect、permission、guard、confirmation、idempotency、recovery 和 audit 契约。
- 保留现有命令名的有界兼容期，同时建立可版本化的 canonical command identity。

### 2.2 非目标

- Diag 不替代产品业务 API、日志系统、监控平台、产测流程或 OTA 状态机。
- 不允许把 shell、任意文件路径、任意设备节点或厂商 SDK 指针包装成“通用诊断”。
- 不要求 RTOS 支持 Linux 全量命令、JSON、动态注册、文件系统或 32 KiB heap buffer。
- 不要求 runtime plugin/dlopen；静态组合是默认路径。
- 本规范不定义凭据签发、PKI 或云端账号系统，只定义 runtime 必须消费的已验证 principal 与 role contract。

## 3. 术语与边界

### 3.1 Observability

被动或只读地表达系统状态：

- logs：离散文本/结构化事件；
- metrics：有界计数器、gauge、histogram；
- traces：跨组件 correlation 和 span；
- health snapshot：状态、原因、最近错误和资源计数。

Observability 不改变业务状态，不通过命令轮询替代持续指标。

### 3.2 Diagnostics

受控的状态查询和问题定位：

- observe：读取 health、capability、版本、资源账本；
- self-test：短时执行可恢复测试，结束后必须恢复原状态；
- probe：验证依赖是否存在，不擅自创建长期资源。

### 3.3 Maintenance

改变设备状态、配置、数据或固件的受控操作：

- transient mutation：音量、预览、短时测试流；
- persistent mutation：SN、配置、校准数据；
- destructive：format、delete、repair；
- update/reboot：OTA、bootloader、重启；
- safety critical：马达、充电、功率或可能造成人身/设备风险的控制。

Maintenance 必须走领域 use case、中央 policy 和审计。

### 3.4 Control plane 与 data plane

- control plane 只携带命令、状态、进度、错误和小型结果；
- 大型媒体、dump、固件和归档文件不放入命令回复，通过受控 artifact/stream handle 传递；
- handle 有 generation、owner、expiry 和 release contract；
- RTOS 大数据使用共享内存/lease，控制 RPC 只传 descriptor。

## 4. 当前代码事实与问题

已核实：

- include/common/diag/diag_types.h 固定 DIAG_REPLY_JSON_MAX_LEN=4096，并把 JSON handler 放在 Common。
- diag_provider.h 暴露 DIAGPROV_Register/Unregister，但实现位于 modules/app 的 registry。
- diag_contract.h 暴露 DIAG_Invoke，但实现位于 modules/app 的 center/dispatcher。
- DIAG_Layer_e 仅包含 HDI/API/APP，无法稳定表达 Common、OSAL、backend、remote peer 和复合领域。
- DIAG_ERR_UNAUTHORIZED/RATE_LIMITED 已定义，但 dispatcher 当前找到 handler 后直接调用，没有中央授权、effect、rate、deadline 和 audit gate。
- 当前 provider 含 volume.set、gain.set、VI start/stop、SD format、SN set、motor control、OTA 等非只读操作。
- registry 返回裸 handler 指针，调用与 provider draining/cleanup 之间没有 invocation lease。
- registry 使用全局 atomic_flag busy spin；RTOS 优先级反转、单核抢占和长临界区行为未形成契约。
- Linux cmd node 为结果动态申请 32 KiB，不能作为 RTOS 公共预算。
- DIAG_ErrorCode 与运行时 VS_ERROR 返回语义并未统一。
- command metadata 的 owner、安全等级、敏感度、超时和幂等信息不足，安全属性散落或缺失。

这些不是局部命名问题，而是跨平台和量产安全边界，必须进入目标设计。

## 5. 目标架构

    Product / Service / Factory APP
      ├─ CLI / cmd_server / IPC / local console
      ├─ authenticated principal adapter
      └─ composition root
                         │
                         ▼
    diag_runtime
      ├─ registry + immutable catalog snapshot
      ├─ policy engine + device-state guards
      ├─ dispatcher + deadline/cancel
      ├─ invocation lease + audit
      ├─ codecs: JSON / TLV / CBOR
      └─ transports: inproc / IPC / AMP proxy
             │              │              │
             ▼              ▼              ▼
      hdi observe       api adapter       app adapter
             │              │              │
             ▼              ▼              ▼
      typed HDI health  API health/usecase APP workflow status
             │
             ▼
      internal HAL backend + OSAL native health

依赖规则：

- common_diag_contract 不依赖 diag_runtime；
- HDI/API/APP 不依赖 diag_runtime；
- diag_runtime 只依赖 common_diag_contract、OSAL core 和选中的 codec/transport port；
- adapters 依赖 diag_runtime provider port 和目标层公开接口；
- transport 不直接调用业务 handler，必须经过 policy/dispatcher；
- backend 不知道命令名称、role、JSON 或 transport。

## 6. 目标源码与头文件布局

目标布局：

    include/common/diag/
      diag_abi.h
      diag_status.h
      diag_descriptor.h
      diag_payload.h

    modules/diag/
      include/
        diag_runtime.h
        diag_registry.h
        diag_policy.h
        diag_provider_runtime.h
        diag_writer.h
      runtime/
        diag_runtime.c
        diag_registry.c
        diag_policy.c
        diag_dispatcher.c
        diag_audit.c
      codecs/
        diag_json_codec.c
        diag_tlv_codec.c
      transports/
        diag_inproc_transport.c
        diag_ipc_transport.c
        diag_amp_proxy.c
      adapters/
        hdi/
        api/
        app/
      compat/v4/
        diag_v4_contract_compat.c
        diag_v4_command_aliases.c

    products/<product>/
      diag/
        command_manifest.json
        policy_manifest.json
        limits_manifest.json
        aliases_manifest.json
        generated/
          diag_command_catalog.c
          diag_policy_catalog.c

    tests/host/diag/
      contract/
      policy/
      lifecycle/
      codecs/
      fuzz/

在当前 Make 阶段，新增 source set 必须显式列入独立实现任务，不允许通过全仓递归导致 Host/RTOS/生产源互相混入。

## 7. Common contract

### 7.1 允许进入 Common 的内容

- uint8_t/uint16_t/uint32_t/uint64_t 等固定宽度字段；
- 显式 abi_version 和 struct_size；
- stable status、effect、sensitivity、payload codec 枚举和 permission_id；
- command_id、schema_id、capability_id；
- request/result 的无所有权 view；
- deadline、correlation、generation 等标量；
- 不包含实现的纯常量和编译期断言。

### 7.2 禁止进入 Common 的内容

- JSON 字符串语义和固定 JSON buffer；
- pthread、fd、socket、ZMQ、FILE、RTOS task handle；
- registry/dispatcher 的全局函数；
- APP profile、cmd_server endpoint 和产品路径；
- 厂商 SDK 类型、GPIO、设备节点、板级路径；
- malloc/free、thread create、sleep 等执行机制；
- handler 函数指针和 provider lifecycle。

### 7.3 ABI 模型

所有跨模块结构遵循：

    struct DiagAbiHeader {
        uint16_t abi_version;
        uint16_t struct_size;
    };

- 接收方只读取 min(struct_size, known_size)；
- 新增字段只追加，不复用保留位；
- enum 在线协议中使用显式 uint16_t/uint32_t；
- 指针只允许进程内 view，不进入 wire/persist；
- wire envelope 显式规定 byte order、长度、schema 和 CRC/完整性策略；
- Common C ABI 为 stable，runtime C API 为 supported，adapter/provider private API 为 internal。

## 8. 命令与结果 contract

### 8.1 Command descriptor

每条命令由 versioned command manifest 定义，并机械生成 C descriptor、catalog 文档和 contract vectors：

    command_id
    canonical_name
    schema_id
    abi_version
    domain
    component
    effect
    required_permissions
    allowed_profiles
    required_capability
    required_device_state
    sensitivity
    audit_policy
    concurrency_policy
    default_timeout_ms
    max_timeout_ms
    idempotency_policy
    confirmation_policy
    recovery_policy
    target_resource
    max_request_bytes
    max_inline_result_bytes

command_id 显式分配、全项目唯一且永久不复用；canonical_name 改名不改变 command_id。缺少 descriptor、effect、permission、recovery 或 limits 的命令注册必须 fail closed。

### 8.2 Request context

runtime 从可信 transport adapter 构造 request context：

    correlation_id
    principal_id_hash
    roles
    granted_permissions
    source
    profile
    deadline_monotonic
    idempotency_key
    confirmation_token_view
    request_generation

context 不保存 credential、token 明文或网络会话对象。provider 不自行解释 transport identity，也不自行把 role 扩张为 permission。

### 8.3 Result

稳定结果包含：

- diag_status：OK、INVALID_ARGUMENT、NOT_FOUND、NOT_READY、UNSUPPORTED、UNAUTHORIZED、RATE_LIMITED、CONFLICT、TIMEOUT、CANCELED、NO_RESOURCE、BUFFER_TOO_SMALL、IO、CORRUPT、INTERNAL；
- domain；
- native_code，仅供诊断和审计；
- retryable；
- correlation_id；
- result flags：TRUNCATED、MORE、REDACTED、ASYNC；
- required_size 或 artifact/stream handle。

运行时 VS_ERROR、errno、vendor SDK 和 RTOS 错误都由 adapter/provider 映射到 stable diag_status。

### 8.4 Payload 与 writer

- runtime handler 接收 bounded payload view，不接收无界 C string；
- codec 在 dispatcher 前完成长度、编码和 schema 验证；
- provider 通过 writer/sink 输出，不假设固定 4096/32768 字节；
- inline result 超限时返回 BUFFER_TOO_SMALL/required_size，或切换 bounded chunk/artifact；
- RTOS 允许完全静态 writer；
- 大型 raw media、firmware 和 dump 永不内嵌 JSON。

## 9. 命令分类和命名

canonical namespace：

- observe.<domain>.<component>.<verb>
- selftest.<domain>.<component>.<verb>
- maint.<domain>.<component>.<verb>
- admin.diag.<component>.<verb>

规则：

- observe 必须是只读且无业务状态变化；
- selftest 允许短时资源占用，但必须有 precheck、timeout、restore 和 residue check；
- maint 必须经过领域 use case；
- admin 只管理 diag_runtime 自身，不控制业务硬件；
- start/stop/set/format/delete/repair/update/reboot 不得放在 observe/diag 伪装为只读；
- 产品正常功能，如音量调整和录像启停，继续属于产品 API；只有受控服务场景才提供 maint alias。

现有 v4 名称先登记为 alias：

| 旧名称示例 | 目标处理 |
|---|---|
| diag.hdi.os.stats.run | observe.system.os.stats |
| diag.hdi.ao.volume.get.run | observe.audio.output.volume |
| diag.hdi.ao.volume.set.run | 移至产品 API；必要时 maint.audio.output.volume.set |
| diag.hdi.vi.h26x.start.run | selftest.video.capture.h26x.start 或移除 |
| diag.api.dvr.sd.format.run | maint.storage.record_card.format |
| diag.api.factory.identity.sn.set.run | maint.identity.serial_number.set |
| maint.app.uart.ota.* | maint.firmware.mcu.* |

alias 只改变入口映射，不绕过新 descriptor、policy、audit 和 handler。

## 10. Effect 与安全策略

### 10.1 Effect

- OBSERVE：只读；
- SELF_TEST：短时、自动恢复；
- TRANSIENT_MUTATION：改变运行态，可恢复；
- PERSISTENT_MUTATION：写配置/身份/校准；
- DESTRUCTIVE：格式化、删除、修复；
- UPDATE：固件或启动链更新；
- REBOOT：重启/进入 bootloader；
- SAFETY_CRITICAL：马达、充电、功率或硬件安全动作。

effect 允许组合时取最高风险等级，禁止 provider 自行降级。

### 10.2 Role 与 permission

- SYSTEM_INTERNAL：进程内受信 composition；
- LOCAL_OBSERVER：本地只读诊断；
- SERVICE_OPERATOR：售后和受控维护；
- FACTORY_OPERATOR：产测和制造写入；
- UPDATE_AGENT：受控升级主体；
- SAFETY_CONTROLLER：安全控制主体。

role 由认证层映射，runtime 只消费不可伪造的 principal context。role 不定义隐式大小关系，而是由 versioned policy manifest 显式映射为 permission 集合，例如 diag.observe、diag.selftest.video、maint.storage.format、maint.identity.write、maint.firmware.update、safety.motor.control。command descriptor 声明 required_permissions，中央 policy 执行集合包含关系。profile 不是 role，位于本地 socket 也不是天然可信。

### 10.3 Policy pipeline

每次调用固定经过：

1. envelope/version/length validation；
2. transport/principal admission limit；
3. immutable catalog snapshot lookup；
4. profile allowlist；
5. permission/effect authorization；
6. versioned capability snapshot check；
7. rate/concurrency budget reservation；
8. provider READY generation 与 invocation lease 原子获取；
9. device-state guard；
10. confirmation/idempotency check；
11. deadline budget；
12. 高风险 pre-execution audit intent 预留/持久化；
13. handler；
14. result redaction；
15. completion audit；
16. lease/budget release。

catalog snapshot 只含不可变 descriptor 和 provider identity，不解引用 provider context；provider 在 snapshot reader epoch 和 invocation lease 都清零前不得释放 control block/context。任一 metadata 缺失或状态 UNKNOWN 都 fail closed。lease/budget 获取后的任何拒绝路径都必须释放；drain 在所有 invocation lease 释放前不得 cleanup。

### 10.4 Destructive confirmation

DESTRUCTIVE、UPDATE、REBOOT 和部分 PERSISTENT_MUTATION 需要二阶段确认：

- prepare 返回 operation_digest、expiry 和一次性 nonce；
- commit token 绑定 command_id、canonical args hash、device boot/session id、principal、expiry 和 nonce；
- token 只能使用一次；
- device state 在 prepare/commit 之间变化则失效；
- Host Fake 可确定性生成测试 token；
- token 验证实现由平台 security service 提供，不在 provider 自造。

SAFETY_CRITICAL 还必须经过独立安全控制器/物理状态 guard，不因拥有 factory role 自动放行。

### 10.5 路径和外部输入

- 禁止构造 shell command；
- 文件路径 canonicalize 后必须位于 command descriptor 的 allowlisted root；
- 设备节点来自受校验 board manifest，不接受调用者任意输入；
- URL、证书、firmware、SN 和配置分别使用领域 validator；
- 日志和 audit 默认脱敏 principal、SN、网络信息、路径和 payload。

### 10.6 维护事务与恢复

SELF_TEST、TRANSIENT_MUTATION、PERSISTENT_MUTATION、DESTRUCTIVE、UPDATE、REBOOT 和 SAFETY_CRITICAL 都必须声明非 NONE 的 recovery_policy；OBSERVE 使用 NONE：

- NONE：仅允许 OBSERVE；
- COMPENSATE：失败后执行确定性补偿；
- RESUME：使用 operation_id 和 durable checkpoint 恢复；
- ROLLBACK：验证前后版本并回退；
- REBOOT_RECOVERY：重启后由独立状态机继续或收敛；
- MANUAL_RECOVERY：不可逆操作失败后进入明确人工恢复态。

维护 operation 有 PREPARED、RUNNING、VERIFYING、COMMITTED、COMPENSATING、ROLLED_BACK、FAILED_MANUAL_RECOVERY 等状态，并绑定 command_id、canonical args hash、target resource/version、principal hash、boot/session、idempotency key 和 audit sequence。

- persistent/destructive/update 操作必须在执行前持久化 intent/checkpoint；
- 相同 idempotency key 返回同一 operation，不重复产生副作用；
- precondition version/state 不匹配返回 CONFLICT；
- format 等不可逆动作不得声称 rollback，必须在 prepare 阶段验证备份/可恢复条件并声明 MANUAL_RECOVERY；
- runtime 重启后可查询 operation 状态，不能只依赖原 IPC reply；
- cancellation 只停止尚可停止的步骤，已提交副作用由 recovery policy 收敛。

## 11. Profile 与命令暴露

| profile | 可注册命令 | 禁止项 |
|---|---|---|
| production | observe + 明确批准的领域 selftest | persistent/destructive/update/safety 默认不注册 |
| service | observe/selftest + allowlisted maint | 未认证远程写、任意文件/设备路径 |
| factory | observe/selftest/制造 allowlist | 非制造需求命令、无审计写入 |
| host_sim | fake observe/selftest/maint | 真实硬件副作用 |
| product_test | 产测 allowlist | 生产身份未确认时写永久数据 |
| rtos_control | 静态 observe + 最小控制 allowlist | 动态注册、JSON、任意维护命令 |

命令未注册优于注册后依赖隐藏参数拒绝。production 二进制应能通过 catalog/symbol audit 证明高风险 handler 不可达。

## 12. Registry、provider 与 composition

### 12.1 不允许 lower layer 向 APP 全局注册

HDI/API 不调用由 APP 实现的 DIAGPROV_Register。composition root 负责：

1. 构造 diag_runtime；
2. 构造 policy/limits/audit/codec/transport；
3. 构造 hdi/api/app adapters；
4. 把静态 provider descriptor 注册到 runtime；
5. 启动 transport；
6. 关闭 transport 后 drain providers。

compat/v4 可暂时提供旧全局符号，但实现只转发到 composition root 注入的 runtime，且只能被 legacy APP adapter 使用；公共新代码禁止引用。

### 12.2 Provider descriptor

provider descriptor 包含：

- abi_version、struct_size；
- provider_id、generation；
- static command descriptor table；
- prepare/handle/cancel/cleanup；
- context 和 context ownership；
- supported profile/capability；
- max concurrent calls；
- thread-safety declaration；
- required runtime feature/limits。

descriptor 和 ops 生命周期至少覆盖 registration 到 drain 完成。

### 12.3 Catalog snapshot

- 注册/注销生成新的 immutable catalog generation；
- dispatch 获取 command entry + provider invocation lease；
- catalog lock 内不执行 codec、policy、audit 或 handler；
- readers 使用 OSAL rwlock、RCU-like snapshot 或短 mutex，不使用无界 busy spin；
- RTOS 可在 init 后冻结 catalog，完全禁止动态注册；
- catalog list 输出是有界分页，不拼接无界 JSON。

## 13. Invocation 生命周期与并发

状态机：

    DOWN → PREPARING → READY → DRAINING → DOWN
                 │        │
                 └→ ERROR ←┘

调用 lease：

1. 在 immutable catalog snapshot 中 lookup descriptor/provider identity，不解引用 provider context；
2. 通过 profile/permission/capability 与 admission policy 后，原子检查 READY generation 并获取 invocation lease/active_calls++；
3. 运行 device guard、confirmation、intent audit 和 handler；
4. active_calls--；
5. DRAINING 等待 active_calls=0 或 deadline；
6. cancel outstanding；
7. cleanup；
8. generation++，旧 callback/result 丢弃。

约束：

- 不持 registry lock 调用 provider；
- handler 必须声明 serial、per-resource serial 或 parallel；
- mutating command 默认 per-resource serial；
- unregister 不得让裸 handler/context 悬空；
- timeout 后区分 handler 已停止、正在取消和不可取消；
- 不可取消的硬件动作必须返回 operation handle，不能谎称 canceled；
- callback 和 async progress 都携带 request/provider generation；
- release 后迟到结果只进入 audit，不交给原调用方。

## 14. 各层职责

### 14.1 Common

- ABI、stable status、descriptor scalar 和 payload view；
- 不含 runtime、handler、JSON 和 profile 实现。

### 14.2 OSAL

- monotonic time、mutex/event/atomic、bounded queue、memory/accounting；
- 输出 OS native health DTO；
- 不注册命令，不依赖 diag_runtime。

### 14.3 Internal HAL backend

- 提供 vendor native health、resource counters、driver status；
- 实现 HDI self-test/maintenance 所需的私有 ops；
- 不暴露 vendor pointer/native struct 给 adapter；
- 不决定 role/profile。

### 14.4 HDI

- 公共 typed health/capability/resource snapshot；
- 向领域 API 暴露可恢复、受限的 self-test/maintenance port，但不向 Diag adapter 直接开放写路径；
- 写操作仍遵守 HDI lifecycle 和 ownership；
- 普通产品控制与维护使用不同 use case/guard；
- 不知道 command name、JSON、audit sink。

### 14.5 API

- 聚合 HDI 状态为领域 health；
- 暴露维护用例，实施业务状态、互斥、补偿和幂等；
- format、identity write、OTA、recording control 等只能经 API/APP domain use case；
- 返回 stable domain error，adapter 再映射 diag status。

### 14.6 APP

- composition root、产品 profile、transport/auth adapter；
- 提供 APP workflow health；
- 不把大型 HardwareApi 作为诊断后门；
- 普通业务与 maintenance use case 共用领域规则。

### 14.7 diag_runtime adapter

- 读取对应层公开 DTO；
- 验证/解码 command-specific input；
- hdi adapter 只调用 typed health/capability/resource snapshot；self-test/maintenance 由 api/app adapter 调用领域 use case；
- 映射 result、progress 和 native evidence；
- 不复制业务状态机、不直接访问 backend。

## 15. Observability 数据模型

Health snapshot 至少包含：

- component_id、generation；
- state：UNKNOWN/STARTING/READY/DEGRADED/DRAINING/FAILED；
- reason_code；
- last_stable_error；
- last_transition_monotonic；
- capability identity hash；
- bounded resource counters；
- evidence freshness。

Metrics：

- metric_id、type、unit、value、monotonic timestamp；
- counter 不倒退，reset 带 generation；
- label 使用固定 allowlist，禁止高基数用户输入；
- RTOS 允许静态 metric table。

Trace/Audit：

- correlation_id 贯穿 transport/runtime/adapter/API/HDI；
- native pointer、credential、完整 payload 不进入 trace；
- audit 记录 allow/deny、command_id、effect、principal hash、operation_id、结果、时间和 evidence；
- SAFETY_CRITICAL/DESTRUCTIVE/UPDATE 在 handler 前必须成功写入或预留 durable intent audit，否则 fail closed；
- handler 后写 completion audit；若副作用已发生但 completion audit 失败，不伪造 rollback，runtime 阻断新的高风险操作并暴露待补偿/人工恢复状态；
- audit 使用 monotonic sequence、boot/session identity、dropped counter 和可验证的完整性策略；
- OBSERVE audit 可按 profile 采样，但 denied attempt 必须记录。

## 16. Codec 与 transport

### 16.1 Codec

- Linux 兼容 JSON，schema validation 在 handler 前完成；
- JSON escaping、UTF-8、数字范围、重复 key、未知字段策略固定；
- RTOS 优先 versioned TLV/CBOR；
- in-process typed request 可绕过编码，但不能绕过 policy；
- codec fuzz 运行在 x86_64；
- canonical args hash 基于 schema 规范化结果，不基于原始 JSON 文本。

### 16.2 Transport

- inproc、IPC、AMP proxy 都实现相同 request context contract；
- transport 负责认证和 framing，不负责业务授权；
- IPC 不因“本机”自动可信，必须校验 peer identity/权限；
- router 超时不等价 handler 取消；
- request/reply 有最大长度、序号、版本和完整性检查；
- RTOS peer reset 使所有 outstanding generation 失效；
- transport shutdown 先停止新请求，再 drain runtime；
- artifact/stream handle 绑定 principal、permission、boot/session、generation 和 expiry；后续读取重新授权，不能把裸 handle 当 bearer credential。

## 17. 资源预算

公共 contract 不硬编码 4096/32768。每个 target 通过 limits manifest 给出预算，runtime init 时验证：

| budget | linux_full 初始上限 | host_sim | rtos_control 初始上限 |
|---|---:|---:|---:|
| registered commands | 512 | 512 | 64 |
| concurrent observe | 8 | 16 | 2 |
| concurrent mutating per resource | 1 | 1 | 1 |
| request bytes | 4096 | 16384 | 1024 |
| inline result bytes | 32768 | 65536 | 1024 |
| stream chunk bytes | 16384 | 16384 | 512 |
| audit ring entries | 1024 | 4096 | 128 |
| maintenance journal entries | 64 | 256 | 16 |
| dynamic registration after init | allowed by profile | allowed | forbidden |
| heap after init | allowed/accounted | allowed/accounted | forbidden by default |

这些是设计起始门禁，不是芯片能力声明：

- target 可收紧；
- 放宽必须附 heap/stack/latency evidence；
- runtime 暴露当前 limits 与 high-water mark；
- 资源耗尽返回 NO_RESOURCE，不降级为无界分配；
- Host 测试覆盖所有边界值。

### 17.1 故障隔离和调度

- limits manifest 声明 diag runtime 是否为 required 或 optional；普通 production observe runtime 启动失败不得隐式阻断产品主功能，高风险 maintenance 依赖的 policy/audit 缺失则对应命令 fail closed。
- observe、self-test/maintenance 和 audit 使用有界队列/worker budget；mutating command 不与高频 observe 共用无界队列。
- Diag worker 优先级不得高于被观测的硬实时/关键业务线程，CPU、heap、stack、I/O 和日志均有 high-water mark。
- overload 返回 RATE_LIMITED/NO_RESOURCE，不自增线程、buffer 或重试风暴。
- codec/transport 失败只关闭对应入口，不破坏 catalog、provider 状态和业务服务。
- audit sink backlog 达上限时，observe 按 profile 降采样并记录 dropped counter；需要 durable audit 的高风险命令停止接收。
- runtime restart 必须使旧 invocation/artifact/confirmation generation 失效，并从 maintenance journal 恢复未终结 operation。
- RTOS 若没有已验证的 durable journal/audit sink，不注册 persistent/destructive/update/reboot/safety 命令；Linux proxy 的 intent 必须在下发 RTOS 动作前落盘。

## 18. ABI、版本和兼容策略

版本面：

- common_diag_abi；
- runtime_api；
- provider_ops；
- command_catalog；
- payload_schema；
- transport_envelope；
- audit_schema。

兼容等级：

| 层 | 等级 | 策略 |
|---|---|---|
| Common C ABI | stable | append-only + size/version |
| transport envelope | stable | negotiation + reject unsupported |
| command canonical name/id | supported | alias/deprecation manifest |
| payload schema | supported | versioned schema + migration |
| runtime/provider API | internal-supported | 同发布兼容或显式 adapter |
| backend native health | private | backend 内自由演进 |

v4 兼容：

- 旧 include/common/diag 头保留一个兼容周期；
- 旧 DIAGPROV_Register/DIAG_Invoke 标为 legacy-app-only；
- v4 alias 进入同一 policy pipeline；
- catalog 能显示 canonical_name、aliases、deprecated_since 和 remove_after；
- 移除前必须证明仓库/现场脚本无命中；
- 不为旧命令保留无权限直通行为。

## 19. 平台组合

### SSC305

- Linux diag_runtime + JSON/IPC；
- ssc305 backend 只提供 native health/ops；
- 现有命令通过 v4 alias 迁移；
- HIL 覆盖真实资源、format/OTA guard 和 cleanup。

### SSU9383CM

- Linux 与 RISC-V/RTOS 命令 catalog 分离；
- Linux proxy 聚合 RTOS static health；
- peer capability UNKNOWN 时不注册对应维护命令；
- AMP reset/generation 是必测项。

### RDK X5

- aarch64 Linux runtime；
- X5 backend 映射统一 health/capability；
- 不复用 SigmaStar device path 或 ARMv7 库；
- camera/codec self-test 受 BSP/board/sensor identity 约束。

### Host x86_64

- fake auth、virtual clock、fake providers、deterministic audit；
- 无 ARM SDK/库；
- 支持 codec fuzz、policy matrix、race 和 compatibility test；
- 高风险命令只操作 fake resource ledger。

### RTOS

- static catalog、bounded writer、无动态注册、默认 init 后无 heap；
- 只实现 observe 和批准的控制 allowlist；
- Linux JSON 在 proxy 端终止；
- 本地 TLV/CBOR 与 shared-memory handle 有独立 version/generation。

## 20. 实施工作流

Diag 重构作为 P0–P5/P8 的强制横切工作流，不作为“后续优化”：

### D0：命令与证据冻结

- 生成当前 command inventory；
- 为每条命令标记 owner、真实调用层、effect、profile、capability、敏感度；
- 识别 alias、重复、死命令和直接 HDI 写操作；
- 保存当前 catalog/response golden。

完成条件：所有现有命令均有 disposition，不允许 unknown effect。

### D1：中央 policy membrane

- 在旧 dispatcher 与 handler 之间加入 descriptor/policy/audit 和 maintenance journal seam；
- 默认缺失 metadata 拒绝；
- production 首先禁用 destructive/update/safety；
- 保留现有 wire 名称。

完成条件：所有入口都经过同一 policy，负面矩阵通过。

### D2：v5 Common ABI 与 codec seam

- 新增无 JSON common contract；
- JSON 移到 codec；
- stable diag_status 与 VS/native error 映射；
- 添加 C11/C++17/32/64 位布局测试。

完成条件：Common 头无 APP/OS/JSON/runtime。

### D3：独立 runtime 与生命周期

- registry/dispatcher/provider/audit 移入 modules/diag；
- composition root 注入；
- catalog generation、原子 invocation lease、drain/cancel、故障隔离；
- OSAL lock 替换 busy spin。

完成条件：并发注销、迟到 callback、timeout 和 cleanup contract 通过。

### D4：Adapter 与 use case 收敛

- hdi/api/app provider 迁入 adapters；
- observe 只读映射 health port；
- 产品控制移出 diag；
- maintenance 调用 API/APP domain use case；
- 禁止 direct backend 和非只读 direct HDI。

完成条件：静态 dependency gate 通过，高风险命令无绕行路径。

### D5：兼容与 profile 收敛

- v4 alias manifest；
- production/service/factory/product_test/host catalog 固化；
- 弃用信息和现场脚本迁移；
- production symbol/catalog audit。

完成条件：兼容测试通过，production 高风险 handler 不可达。

### D6：Host 完整门禁

- policy、codec、registry、lifecycle、resource limits、fuzz；
- Fake capability/health/maintenance；
- ASan/UBSan，TSan 独立运行；
- golden catalog 与 wire vectors。

完成条件：Host clean/build/test 不链接 ARM 库，资源账本归零。

### D7：真机与 RTOS

- SSC305 首先 HIL；
- SSU9383CM/RDK X5 分平台接入；
- RTOS static catalog/TLV/AMP proxy；
- 资源、权限、重启和 peer reset 实测。

完成条件：平台 contract + HIL 通过后才能声明该命令受支持。

### D8：移除 v4

- repo、产测、售后脚本和现场工具无旧名称命中；
- owner 批准 remove_after；
- 删除 compat，不删除审计和迁移证据。

完成条件：无未迁移消费者，rollback 包保留一个批准周期。

## 21. 测试矩阵

### Contract

- ABI size/version、unknown field、endianness；
- command descriptor 完整性；
- stable/native error 映射；
- JSON/TLV golden vector；
- alias 与 canonical 等价；
- limits manifest validation。

### Policy

- permission × profile × effect 全矩阵；
- UNKNOWN capability/state fail closed；
- token expiry/replay/args mismatch；
- rate/concurrency；
- production catalog 不含高风险命令；
- denied attempt audit。

### Lifecycle

- register/unregister；
- unregister 与 invoke race；
- drain timeout/cancel；
- provider generation 与迟到结果；
- async operation handle；
- audit failure；
- runtime restart 与 maintenance journal 恢复；
- peer reset。

### Input security

- malformed JSON/TLV；
- size/number overflow；
- duplicate/unknown fields；
- path traversal/symlink；
- shell metacharacter；
- invalid UTF-8；
- artifact handle forgery；
- fuzz corpus。

### Functional/HIL

- observe health 与真实状态一致；
- self-test 恢复原状态且无 residue；
- format/identity/OTA 的 guard、confirm、audit 和 rollback；
- 不可逆操作的 MANUAL_RECOVERY 与重启后 operation 查询；
- motor/safety command 独立安全 gate；
- backend native error 可诊断但不泄露敏感数据。

## 22. 验收门禁

- DG-01：Common diag 头无 JSON、OS、APP profile、handler 和 runtime global。
- DG-02：HDI/API/APP/OSAL/backend 不依赖 diag_runtime。
- DG-03：所有 command descriptor 有 effect、permission、profile、deadline、limits、audit 和 recovery policy。
- DG-04：所有入口在 handler 前经过中央 policy。
- DG-05：production 不注册 destructive/update/reboot/safety command，除非逐项 owner 批准。
- DG-06：非只读操作不直接从 APP adapter 写 HDI/backend。
- DG-07：format、identity、OTA、motor 等通过领域 maintenance use case。
- DG-08：unregister/drain 不产生悬空 handler/context。
- DG-09：没有 handler 在 registry lock 内运行。
- DG-10：stable diag_status 与 native error 映射完整。
- DG-11：结果支持 required_size/chunk/artifact，不依赖固定大 buffer。
- DG-12：Host policy/lifecycle/codec/fuzz 与 sanitizer 通过。
- DG-13：RTOS static catalog、bounded memory 和 peer reset 通过目标验证。
- DG-14：v4 alias 不绕过新 policy，移除有使用证据和 rollback。
- DG-15：catalog、audit 和 capability identity 可关联到同一版本。
- DG-16：文档、command manifest 和测试为同一 SSOT 或可机械生成。
- DG-17：高风险命令在副作用前有 durable intent audit，completion audit 失败时不会伪造回滚且会阻断后续高风险操作。
- DG-18：runtime 故障、过载或重启满足队列/线程/内存隔离，并能恢复或明确标记未终结 maintenance operation。

## 23. 风险与控制

| 风险 | 级别 | 控制 |
|---|---|---|
| 诊断入口变成产品后门 | blocker | central policy、profile catalog、effect/permission、audit |
| 未可信 IPC 可执行维护命令 | blocker | authenticated principal、peer check、fail closed |
| format/OTA/motor 绕过领域状态机 | blocker | maintenance use case、guard、confirmation |
| provider 注销与调用竞态 | high | invocation lease、generation、drain barrier |
| JSON/大 buffer 阻断 RTOS | high | codec seam、bounded writer、static limits |
| v4 兼容保留旧直通 | high | alias 进入同一 policy pipeline |
| layer enum 持续膨胀 | medium | domain/component/source 独立 metadata |
| audit 泄露 SN/路径/payload | high | sensitivity、redaction、hash principal |
| resource limit 任意放宽 | medium | target limits manifest + evidence gate |
| Fake 自证正确 | high | 真机 contract/HIL 与 capability identity |
| 高风险动作完成但 audit/回复丢失 | blocker | pre-intent audit、operation journal、idempotency、recovery state |
| Diag 过载拖垮业务线程 | high | 独立有界预算、优先级、队列和 high-water mark |

## 24. 所有权与长期维护

- team-core：Common ABI、runtime contract、policy model；
- product owner：profile 与 command allowlist；
- platform owner：health/capability/backend evidence；
- security owner：principal mapping、confirmation、audit policy；
- factory/service owner：维护命令和现场兼容；
- build owner：Make/GROS source set 和 target isolation；
- test owner：Host contract、fuzz 和 HIL coverage。

### 24.1 受治理资产集

长期 SSOT 不是单份设计文档，而是一组有明确 source/derived 边界的资产：

| 资产 | 权威性 | 维护规则 |
|---|---|---|
| 本架构规范 | architecture SSOT | 变更边界、contract、安全模型和门禁 |
| common diag ABI headers + schema | ABI SSOT | append-only、version/size、布局测试 |
| command_manifest.json | command SSOT | 显式 command_id，禁止复用 |
| policy_manifest.json | permission/profile SSOT | security/product owner review |
| limits_manifest.json | target resource SSOT | 放宽必须附资源证据 |
| aliases_manifest.json | compatibility SSOT | deprecated_since/remove_after/consumer evidence |
| generated C catalog/docs/vectors | derived | 禁止手改，生成后做 clean diff |
| Host contract/fuzz corpus | executable evidence | 版本绑定 manifest/schema |
| HIL matrix/receipts | platform evidence | 绑定 BSP/board/sensor/backend identity |

机械一致性：

- manifest schema 校验 command_id/name/alias 唯一性、permission/effect/recovery 完整性和 limits 上界；
- generator 输出 catalog C、可读命令文档、policy matrix 和 golden vectors；
- generated 内容携带 source manifest hash，runtime 可报告 command/policy/limits hash；
- CI 在 source 未变时要求生成结果 clean，在 source 变化时审查 production catalog diff；
- production policy/limits/catalog 采用编译内置或经过平台 trust service 完整性验证的只读加载，Diag 不能修改自身 policy；
- 外部 override 默认禁止；service/factory 如需 override，必须有签名/授权、版本、expiry、audit 和 rollback；
- 设计文档只描述规则，不复制完整命令表，避免双重 SSOT。

变更规则：

- 新命令必须先改 manifest/schema/test，再实现 adapter；
- effect/permission 降级视为安全 breaking change；
- 删除/改名必须更新 alias/deprecation evidence；
- limits 放宽必须有资源证据；
- profile 暴露变化必须审查 production catalog diff；
- platform 支持声明必须绑定 BSP/board/sensor/backend identity；
- owner 未批准时状态保持 reviewing。

## 25. 证据索引

仓库证据：

- include/common/diag/diag_types.h：JSON reply limit、layer enum、JSON handler。
- include/common/diag/diag_provider.h：全局 provider register。
- include/common/diag/diag_contract.h：全局 invoke。
- modules/app/src/app_diag/framework/app_diag_center.c：Common contract 的 APP 实现。
- modules/app/src/app_diag/framework/app_diag_registry.c：provider runtime、busy spin、裸 handler lookup。
- modules/app/src/app_diag/framework/app_diag_dispatcher.c：直接 handler 调用。
- modules/app/src/app_diag/provider/hdi：直接 HDI 读写命令。
- modules/app/src/app_diag/provider/api：format、identity、download、业务启停等命令。
- modules/app/src/app_diag/provider：motor/OTA 等维护命令。
- modules/app/src/app_diag/ipc/app_diag_cmd_node.c：JSON/IPC 和 32 KiB 动态结果 buffer。

关联决策：

- HDI/HAL 跨平台与 Host 开发测试架构决策候选。

验证边界：

- 本规范基于静态源码和现有架构证据；
- 未声明现有权限入口可被外部利用；
- 未声明未实现的 v5 runtime、Host 或 RTOS 测试通过；
- 实现支持必须按 DG-01 至 DG-18 提供新证据。

## 26. 可恢复执行与停止条件

- goal_statement：把 Diag 从混合公共头/APP runtime 重构为可跨 Linux、Host、RTOS 的受控诊断与维护平面。
- completion_claim：目标架构、contract、policy、资源预算、迁移、测试和治理均形成长期 SSOT；不包含代码实现。
- claimant：Codex。
- verifier：独立 review loop；team-core/security/product owner 待批准。
- retry_budget：同一路径 2 次。
- evidence_stale_after：24 小时。
- heartbeat：draft、integration、review、verification、archive、final。
- stop conditions：
  - 任何 blocker/major 设计发现未闭环时禁止归档；
  - 未经 owner 不提升 active；
  - 发现需要改变当前编译规则时另立构建任务；
  - 归档事务或精确检索失败时 completion=needs-fix。

## 27. 决策状态

本规范已通过本轮分离式架构与安全 review。归档状态保持 reviewing，等待 team-core、security、product、platform owner 批准；它作为总体 HDI/HAL 跨平台方案的强制组成部分，不为未实现功能背书。
