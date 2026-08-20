---
doc_type: architecture-decision-candidate
decision_id: pcr02-hdi-hal-cross-platform-host-development-architecture-20260813-v2
supersedes_candidate: pcr02-hdi-hal-cross-platform-host-development-architecture-20260813
created: 2026-08-13
updated: 2026-08-13
platforms:
- SSC305
- SSU9383CM
- RDK X5
- Linux x86_64 Host
- future RTOS
build_policy: current product build rules remain unchanged
id: pcr02-hdi-hal-cross-platform-host-development-architecture-20260813-v2
title: HDI/HAL 跨平台与 Host 开发测试架构决策候选 v2
kind: decision
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/decisions/hdi-hal-cross-platform-host-development-architecture-20260813-v2.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: design-review
  from: reviewed repository architecture document and local static evidence
  source_sha256: 2cc12b6e3d8846026a05b2dfa2c1cbce29796233db867b63aac3080729f0912e
review_after: '2026-09-13'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- hdi
- hal
- cross-platform
- host-test
- x86_64
- ssc305
- ssu9383cm
- rdk-x5
- rtos
- gros
- diag
- decision-candidate
validation_refs:
- projects/xcrz-sigmastar-demo/decisions/hdi-hal-cross-platform-host-development-architecture-20260813-v2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/decisions/hdi-hal-cross-platform-host-development-architecture-20260813-v2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-13'
updated_at: '2026-08-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-13'
manual_validation_pending: true
summary_zh: v2 替代旧候选作为最新设计入口；冻结 HDI/HAL/API/APP/OSAL 与 Diag 正交平面的长期分层，覆盖三平台、Linux x86_64 Host、future RTOS 和未来 GROS；当前编译规则不变，D0-D8
  与 DG-01-DG-18 为强制门禁。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- HDI/HAL 跨平台与 Host 开发测试架构决策候选 v2
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# HDI/HAL 跨平台与 Host 开发测试完整方案

## 1. 结论

本项目采用“稳定语义接口 + 可替换平台后端 + 能力驱动组合”的演进路线：

1. HDI 是面向 API 的稳定硬件语义接口；HAL 是 HDI 内部的平台适配机制，不向 API、APP 泄露厂商 SDK 类型、板级引脚和操作系统对象。
2. 第一阶段保留当前产品编译规则，不修改根 Makefile、build/*.mk、各模块 lib.mk，也不尝试用现有 ARCH=x86 构建完整产品。
3. Linux x86_64 是第一优先级 Host 平台。Host 只承诺纯逻辑、协议、状态机、资源生命周期、API 编排和 APP 部分业务的开发测试；不模拟真实图像质量、硬编解码性能、驱动时序和板级电气行为。
4. SSC305 保持参考实现地位；SSU9383CM 与 RDK X5 分别落成独立后端，不通过大量条件编译把三套 SDK 混入公共层。
5. RTOS 先支持 rtos_control 或 amp_proxy 受限配置，不默认搬迁完整 Linux APP；所有公共接口不得假设文件系统、进程、动态加载、ZMQ 或 POSIX 线程存在。
6. 未来 GROS 只负责目标、源码、依赖与 feature 组合。其语法、包管理、锁文件和缓存规则尚无可信规格，本方案只定义 GROS 需要表达的目标模型，不臆造具体 DSL。
7. x86 现有变量可作为历史别名保留，但第一阶段实际支持的是 Linux x86_64；真正 i386 仅在有明确业务需求、32 位工具链和依赖后另立目标。
8. Diag、Observability 与 Maintenance 是一条正交平面：Common 只保留无 OS/JSON/runtime 的 ABI；独立 diag_runtime 承担 policy、registry、dispatcher、audit、codec 和 transport；非只读操作必须通过领域 maintenance use case。

该决策已通过包含 Diag 重构的本轮分离式 review，只代表架构候选，不代表平台实现、实板验证、负责人批准或发布完成。

## 2. 目标与非目标

### 2.1 目标

- 在 SSC305、SSU9383CM、RDK X5 和后续 RTOS 之间保持 API/APP 的主体代码稳定。
- 把 SigmaStar MI、RDK X5 SDK、Linux/POSIX、RTOS 和板级差异收敛到明确边界。
- 让 x86_64 PC 能覆盖高频逻辑开发、故障注入、资源泄漏和并发契约测试。
- 保留当前产品构建路径，降低架构迁移对在研版本的扰动。
- 为未来 GROS 提供可直接映射的 target/profile/backend/capability 模型。
- 给每个迁移包配置独立验收、停止条件和回滚点。
- 一次性冻结 Diag 的分层、安全策略、生命周期、资源预算、Host/RTOS contract 和长期治理，不留作非约束性后续优化。

### 2.2 非目标

- 不在本阶段实现三个 SoC 后端、RTOS 端或 GROS 构建描述。
- 不承诺 PC 能执行 ARM 专有动态库、真实 ISP 调优、硬编解码性能或硬件在环验证。
- 不把 HAL 设计成公开的“大而全”硬件类，也不要求运行时插件化。
- 不立即重排现有源码目录或改变安装包、量产和 OTA 流程。
- 不把 Host Fake 的通过等价为真机通过。
- 不把 Diag 作为绕过 API、权限、状态机和审计的硬件后门。

## 3. 已核实事实、架构决策与待确认项

### 3.1 已核实事实

- 当前 build/mi_dep.mk 存在 ARCH=x86 分支并选择本机 gcc/g++，但没有形成完整 Host 产品目标，也没有明确 i386 的 -m32 约束。
- 当前公共 hdi_os.h 暴露 pthread、semaphore、unistd、reboot、time 和 stat 等 Linux/POSIX 头文件。
- 当前 hdi_init.h 的公开语义包含 SigmaStar MI_SYS，部分 HDI 公开头还包含板级 GPIO 宏。
- 当前部分 API 公开头直接包含 HDI 头，api_zmq.h 还公开 pthread_mutex_t 和 pthread_cond_t。
- 当前部分 API 实现直接使用 VSHDIOS_*，说明 OS 抽象与 API 边界尚未完全收敛。
- 当前 hdi_sys.c 等实现直接依赖 SigmaStar MI 头文件，SSC305 后端事实存在但尚未形成统一 backend contract。
- VS_HANDLE 和 VS_ID 当前是 32 位整数；在 x86_64 上必须继续作为代次/索引类句柄，禁止装入指针。
- 仓库内抽查到的 spdlog、fmt、protobuf-lite、zmq 动态库为 32 位 ARM ELF，不能链接到 x86_64 Host 测试。
- 当前 tests 下已有独立测试 Makefile 和 fake priority controller，证明 sidecar Host 测试路径可行，但不是完整跨平台框架。
- 历史架构材料确认现有总体分层意图是 HDI 负责硬件和 OS、API 提供通用服务、APP 负责产品编排。
- 历史平台材料表明 SSC305 面向 Linux/DualOS/CM4，SSU9383CM 面向 Linux 与 RISC-V/RTOS 能力，RDK X5 当前可信基线为 ARM64 Linux/Buildroot；具体 BSP、板卡和传感器仍需项目 owner 冻结。
- 当前 include/common/diag 同时包含 JSON handler、固定 reply buffer、provider/register/invoke contract，而实现位于 modules/app，公共 ABI 与 APP runtime 职责混合。
- 当前 Diag provider 同时包含只读状态和 volume/gain/start/stop/format/SN/OTA/motor 等写操作；dispatcher 尚未实施已定义的 UNAUTHORIZED/RATE_LIMITED 语义、effect policy、deadline 和统一 audit。
- 当前 registry 返回裸 handler 后解锁调用，provider drain/cleanup 与 invocation 之间缺少 lease/generation barrier；32 KiB 动态 reply 也不能成为 RTOS 公共预算。

### 3.2 本方案决策

- 公共依赖方向固定为 APP → API → HDI → internal HAL backend → OS/SDK/driver。
- APP 只在 composition root 组装依赖；只读 Diag 由独立 adapter 通过 typed HDI health port 查询，普通 APP 和非只读维护均不得绕过 API。
- OSAL 只覆盖内存、线程、同步、时间、原子和基础日志等最小机制；文件、进程、网络、动态加载归入可选平台服务。
- 后端优先静态链接与启动时注入，不把 dlopen 作为跨 Linux/RTOS 的基础要求。
- 平台选择由构建组合决定，运行时能力由 capability query 决定；不得仅依据 SoC 名称猜能力。
- Host Fake 在 HDI 边界实现同一契约；APP 侧另通过窄业务端口隔离现有大型 HardwareApi 类。
- Diag 采用 common_diag_contract + diag_runtime + layer adapters：lower layer 不向 APP 全局符号注册，JSON 仅为 Linux codec，所有命令经中央 policy、invocation lease 和 audit。
- Observability、self-test、maintenance 分开建模；format、identity、OTA、reboot、motor 等高风险命令使用 effect/permission/profile/device-state/confirmation/idempotency/recovery contract。

### 3.3 待 owner 确认

- SSU9383CM 与 RDK X5 的正式 BSP/SDK、板型、传感器和量产 feature 集。
- RTOS 是单芯运行、异构核控制端，还是 Linux 主核的 AMP 从端。
- GROS 的正式名称、语法、toolchain 定义、依赖锁定与产物目录规范。
- 公共 C ABI 的版本兼容策略，以及哪些旧 API 可破坏性升级。
- Host 允许的本机三方依赖白名单。

这些事项不阻塞方案成为 reviewing candidate，但会阻塞对应实现包进入开发。

## 4. 目标架构

    Product APP
      ├─ product workflow / state machine / policy
      ├─ narrow product ports
      └─ composition root and read-only diagnostics
                    │
                    ▼
    Domain API
      ├─ media graph compiler / diff
      ├─ recording / streaming / storage services
      └─ desired state, policy-free service contracts
                    │
                    ▼
    Stable HDI Facade
      ├─ lifecycle / ownership / error / capability contract
      ├─ video / audio / storage / power / device domains
      └─ backend-independent handles and data descriptors
                    │
                    ▼
    Internal HAL Backend Ops
      ├─ ssc305_mi
      ├─ ssu9383cm_mi
      ├─ rdk_x5
      ├─ host_fake
      └─ rtos_native or amp_proxy
                    │
                    ▼
    OSAL + optional platform services + vendor SDK / drivers

    Orthogonal Diag / Observability / Maintenance Plane
      APP transport/auth/composition
                    │
                    ▼
      diag_runtime: catalog/policy/dispatcher/audit/codec
          ├─ hdi adapter → typed HDI health port
          ├─ api adapter → API health/maintenance use case
          └─ app adapter → APP workflow health/use case

Diag 平面只能从 adapter 指向被观测层，不允许 HDI/API/OSAL/backend 反向依赖 diag_runtime。

### 4.1 Common

Common 层只包含固定宽度类型、无厂商含义的数据结构、序列化、容器和可移植算法：

- 线协议和持久化格式显式定义字节序、版本、长度和校验，不直接写入 C/C++ 原始结构体。
- 不暴露 long、size_t、指针大小和编译器 padding。
- 句柄、对象 ID 和跨进程 ID 不复用指针。
- 公共结构新增字段采用 size/version 或显式 TLV 兼容策略。
- Common diag 只允许 stable status、effect/permission、versioned descriptor scalar 和 bounded payload view；禁止 JSON、handler、registry、APP profile 和 transport。

### 4.2 OSAL 与平台服务

OSAL 的最小公共面：

- memory：分配、释放、对齐和可选内存统计；
- thread：创建、join、命名、优先级能力查询；
- sync：mutex、semaphore、condition/event；
- time：单调时钟、墙钟、deadline、sleep；
- atomic：公共需要的整数原子操作；
- logging：不依赖特定格式库的最小日志 sink。

以下能力不进入 OSAL 核心，而是独立 profile：

- filesystem；
- process/signal/reboot；
- socket/network；
- dynamic_library；
- persistent_kv；
- shared_memory/cache maintenance。

这样 RTOS 可以只实现 osal_core，Linux full profile 再组合 POSIX 服务。API 的公开头不得出现 pthread_t、pthread_mutex_t、sem_t 或 Linux 文件描述符。

OSAL 可以输出 typed native health/metrics DTO，但不注册命令、不依赖 diag_runtime；Diag registry 也不得使用无界 busy spin 代替 OSAL 同步原语。

### 4.3 HDI

HDI 面向“业务需要的硬件语义”，不面向厂商函数的逐项包装：

- 视频域表达 camera stream、frame、encoder channel 和 graph，而不是 MI_SYS/MI_VIF/MI_VPE 的直接镜像。
- 音频域表达 input/output stream、format、buffer 和 clock，而不是厂商设备号的裸露组合。
- 存储、设备信息、电源和看门狗按相同方式形成窄域接口。
- 所有调用都定义前置状态、并发规则、超时、所有权、失败后的可恢复状态。
- 按域提供 typed capability、health、resource snapshot，并向领域 API 提供可恢复 self-test/maintenance port；不向 Diag adapter 直接开放写路径。

### 4.4 Internal HAL backend

HAL 后端是 HDI 的私有机制，可用 C ops table 或等价静态 vtable 表达：

    struct HdiBackendOps {
        uint32_t abi_version;
        uint32_t struct_size;
        void *context;
        lifecycle_ops;
        capability_ops;
        video_ops;
        audio_ops;
        storage_ops;
        power_ops;
    };

要求：

- ops table 有 abi_version 和 struct_size；
- context 由 backend 拥有，HDI facade 不解释其内部结构；
- 允许按域拆分，禁止所有平台实现一个巨型 switch；
- 默认在 link time 选择 backend，并在 composition root 注入；
- 后端厂商类型只能存在于 backend 私有头和实现；
- 同一个 HDI contract suite 必须能运行 host_fake 和真机 backend 的可测子集。
- backend 只提供 native health/ops，既不决定 Diag role/permission/profile，也不接触 transport、JSON 和 audit policy。

### 4.5 API

API 是跨平台领域服务层：

- 接收 desired state、业务参数和资源策略；
- 把目标状态编译为 HDI 操作计划；
- 管理并发请求、幂等、重试、补偿和状态收敛；
- 不包含 GPIO、sensor bus、MI/RDK SDK 类型或 RTOS task 类型；
- 不公开 OS 线程对象；
- 对不支持能力返回稳定领域错误，而不是静默降级。
- format、identity write、OTA、reboot、motor 等维护动作通过 API/APP domain maintenance use case 执行业务 guard、补偿、幂等和资源互斥。

### 4.6 APP

APP 只做产品编排、UI/命令映射、业务状态机和策略：

- 普通业务通过 API 使用设备能力；
- composition root 负责选择 profile/backend/diag profile、构造 runtime 和 adapters；
- APP 不直接查询 HDI；只读 hdi adapter 只调用 typed HDI capability/health port；
- transport/auth adapter 将已认证 principal 交给 diag_runtime，不能把“本机 IPC”视为天然可信；
- 现有 HardwareApi 不直接被命名为 HAL，后续拆为 CameraPort、AudioPort、StoragePort、PowerPort、DeviceInfoPort 等窄接口；
- DvrCommandHandler 等消费者逐个改为依赖窄端口或领域 API，而不是依赖整个 HardwareApi。

### 4.7 Diag、Observability 与 Maintenance 平面

完整 SSOT 见 docs/architecture/diag-observability-maintenance-plane.md，以下为不可删减的总体约束：

- Common contract 无 OS、JSON、runtime global 和 handler；
- diag_runtime 独立承载 immutable catalog、policy、dispatcher、provider lifecycle、audit、codec 和 transport ports；
- command descriptor 强制包含 effect、required_permissions、allowed_profiles、capability/state guard、deadline、limits、audit、concurrency、idempotency、confirmation 和 recovery；
- 命令分 observe/selftest/maint/admin；名称不能替代 effect policy；
- production 默认只注册 observe 和批准的轻量 selftest，高风险 handler 必须经 catalog/symbol audit 证明不可达；
- destructive/update/reboot/safety critical 使用二阶段确认和独立安全 guard；
- provider invoke 使用 lease/generation/drain barrier，registry lock 内禁止执行 handler；
- JSON 是 Linux codec，RTOS 使用 static catalog、bounded writer、TLV/CBOR 或 Linux proxy；
- 大型 media/dump/firmware 使用 artifact/stream handle，不进入 inline reply；
- 现有 v4 名称只作为 alias，经同一 policy/audit pipeline，在有使用证据后按 remove_after 移除。

## 5. 接口契约

### 5.1 生命周期

每个 HDI 域遵循明确状态机：

    UNINITIALIZED → INITIALIZED → CONFIGURED → RUNNING → STOPPED
          ▲              │             │           │
          └──────────────┴─────────────┴───────────┘ release

- init 和 release 必须幂等或明确返回重复操作错误；
- partial init 失败必须能安全 release；
- stop 返回后是否允许残留 callback 必须写入契约；本方案要求 stop barrier 后不再产生旧代次 callback；
- 异步对象携带 generation，旧 generation 事件必须丢弃；
- release 前检查 buffer/frame lease，泄漏要进入诊断而不是静默回收。

### 5.2 所有权与内存

跨平台 frame/buffer 描述至少包含：

- plane count、format、width、height、stride、offset、size；
- monotonic timestamp 和可选 wall timestamp；
- memory kind：host heap、dma contiguous、shared memory、vendor surface；
- cache policy 和必要的 sync hook；
- lease/release token；
- producer generation。

API/APP 不直接 free 厂商 buffer。Host Fake 与真机后端遵守相同 lease 规则。

### 5.3 句柄与 ABI

- VS_HANDLE/VS_ID 保持固定宽度整数语义，建议编码 index + generation。
- 禁止 uintptr_t 强转为 VS_HANDLE 后长期保存。
- 公开 C ABI 使用固定宽度整数、显式 enum width、size/version。
- C++ 仅作为内部 RAII 包装，跨模块契约保留 C ABI 或明确同工具链约束。
- wire/persist 数据不得依赖本机结构体布局。

### 5.4 错误模型

统一错误至少包含：

- stable_code：跨平台稳定分类，如 INVALID_STATE、UNSUPPORTED、TIMEOUT、NO_RESOURCE、IO、CORRUPT、INTERNAL；
- domain：video/audio/storage/os/backend；
- native_code：原始 SDK/errno/RTOS 错误，仅用于诊断；
- retryable；
- context_id，用于关联日志与异步结果。

API 只基于 stable_code 决策；native_code 不进入业务分支。

### 5.5 超时与取消

- 所有可能阻塞的 HDI 调用接受 deadline 或配置上限；
- 使用 monotonic clock 判断超时；
- 取消必须说明是 best effort 还是 barrier；
- Fake backend 用虚拟时钟推进，不依赖真实 sleep；
- RTOS 实现不得假设无限等待可接受。

### 5.6 Diag 调用、权限与结果契约

- request context 包含 correlation、principal hash、roles、granted permissions、profile、deadline、idempotency key 和 request generation，不保存 credential 明文。
- stable diag status 与 VS_ERROR/errno/vendor/RTOS native code 分离；provider 不把 native code 暴露给业务决策。
- 调用顺序固定为 validate/admission → immutable catalog lookup → profile/permission/effect/capability → rate budget → atomic READY invocation lease → device guard → confirmation/idempotency/deadline → high-risk intent audit → handler → redaction/completion audit → release lease/budget。
- metadata 缺失、能力 UNKNOWN、身份未验证或 audit 必需但不可用时 fail closed。
- provider drain 等待 active invocation 清零或到 deadline；不可取消动作返回 operation handle，不谎称 canceled。
- payload 由 codec 在 handler 前做长度、编码和 schema 验证；结果使用 bounded writer、required_size、chunk 或 artifact handle。
- 高风险操作使用 operation journal、precondition、idempotency 和 recovery policy；不可逆动作进入明确 MANUAL_RECOVERY，不伪造 rollback。
- runtime/transport/audit 采用有界队列、线程、内存和优先级隔离；audit intent 不可用时高风险命令 fail closed。

## 6. 能力模型

能力状态采用三态：

- UNKNOWN：未探测或证据与当前身份不匹配；
- UNSUPPORTED：当前组合明确不支持；
- SUPPORTED_VERIFIED：在匹配身份下通过探测或验证。

能力记录必须绑定：

- SoC；
- SDK/BSP 和驱动版本；
- board revision；
- sensor/codec/storage 等外设身份和模式；
- backend ABI；
- profile/feature set；
- 验证来源与时间。

原则：

- UNKNOWN 默认 fail closed；
- 不根据 SSC305、SSU9383CM 或 X5 名称直接推断具体 sensor mode；
- backend 初始化时生成 capability snapshot，API 可订阅变化但不修改硬件事实；
- APP 只依据领域能力决定 UI/业务分支；
- 未验证能力不得进入量产默认路径。

建议能力键按域命名，例如：

- video.capture.stream_count；
- video.encode.h264.max_resolution；
- video.display.available；
- audio.input.channel_count；
- storage.atomic_rename；
- system.reboot；
- system.amp.peer_available。

### 6.1 Board manifest 与 capability 的边界

从公开头移出的 GPIO、设备节点、sensor bus、IQ/校准路径和存储分区等板级事实，统一进入只读 board manifest：

- manifest 由产品/板型配置生成或静态编译，不由 APP 在运行时随意拼接；
- manifest schema 有 version、board_id、revision 和校验；
- backend 在初始化时读取并验证 manifest，转换为私有厂商配置；
- capability 描述“当前身份验证后能做什么”，manifest 描述“这块板如何连接”，两者不得混用；
- manifest 中的设备路径必须经过固定 schema 和 allowlist，禁止把外部不可信字符串直接传给 shell、driver 或动态加载器；
- Host 使用最小合成 manifest；真机 manifest 必须绑定 BSP/板型证据；
- board manifest 变更属于平台配置变更，要单独评审和 HIL，不通过公共 API 宏传播。

## 7. 媒体链路的首个垂直切片

视频链路是平台差异最大、收益最高的验证切片：

    API desired state
          │
          ▼
    pure graph compiler
          │ graph + capability snapshot
          ▼
    deterministic diff / operation plan
          │
          ▼
    HDI video facade
          │
          ▼
    backend executor

设计约束：

- API 只描述输入、输出、分辨率、帧率、编码和消费关系；
- graph compiler 是纯函数，可在 x86_64 测试；
- VIF/VPE/VENC、RDK pipeline 等物理节点只存在于 backend；
- operation plan 可序列化为诊断信息，但不持久化厂商指针；
- executor 提供 create/bind/start/stop/unbind/destroy 的补偿序列；
- 中途失败要验证反向清理和资源账本归零。

首个场景选择“单路模拟帧 → 编码服务抽象 → 录制/推流消费者假实现”。Host 不编码真实 H.264，可用确定性 packet fixture 验证上层生命周期、时间戳、背压和分段策略。

## 8. 平台与 profile 矩阵

| 平台 | OS/架构基线 | backend | 推荐 profile | 第一阶段职责 | 必须补证 |
|---|---|---|---|---|---|
| SSC305 | Linux ARMv7；历史含 DualOS/CM4 | ssc305_mi | linux_full | 参考真机实现与回归基线 | 当前产品板型、SDK、sensor |
| SSU9383CM | Linux + RISC-V/RTOS 能力 | ssu9383cm_mi | linux_full / rtos_control | 新 SigmaStar 平台后端 | 正式 BSP、核间拓扑、板型 |
| RDK X5 | ARM64 Linux/Buildroot | rdk_x5 | linux_full | 独立媒体/系统后端 | 项目 BSP、camera/DDR/eMMC/Wi-Fi |
| Host | Linux x86_64 | host_fake | host_sim | 纯逻辑、契约、故障注入、部分 APP | 本机依赖白名单 |
| future RTOS | CPU/RTOS 待定 | rtos_native / amp_proxy | rtos_control / amp_proxy | 控制面、硬实时小服务 | RTOS、CPU、内存和 IPC 方案 |

### 8.1 Host 支持等级

- L0 编译级：公共头可由 C11/C++17 本机编译，检查尺寸、对齐和 include 泄漏。
- L1 纯逻辑级：容器、序列化、状态机、graph compiler、策略和命令校验。
- L2 契约级：OSAL fake、HDI fake、资源生命周期、故障注入和 callback 顺序。
- L3 进程内集成级：API + fake HDI + APP 窄端口，验证典型工作流。
- L4 真机/HIL：真实 SDK、driver、DMA、cache、性能、图像质量和电气行为。

Host 初期交付 L0–L3；L4 永远由 ARM/RTOS 真机承担。

### 8.2 不适合 Host 结论化的内容

- ISP 图像质量、AE/AWB 收敛；
- 真实硬编解码吞吐、延迟和码率质量；
- DMA/cache coherency；
- sensor MIPI 时序、GPIO 和电源时序；
- eMMC 掉电安全；
- Wi-Fi、温升和看门狗；
- 多核 AMP 的真实共享内存与中断时序。

## 9. Host Fake 设计

Host Fake 不是随意的 mock 集合，而是可重复执行的 backend：

- capability fixture：声明本场景支持、未知和不支持的能力；
- virtual clock：测试可显式推进时间；
- deterministic event queue：事件按 timestamp + sequence 排序；
- resource ledger：记录 handle、generation、buffer lease、绑定关系；
- scripted faults：按第 N 次调用、资源类型或时间点注入错误；
- canned media：使用项目自有或可再分发的小型合成数据；
- trace sink：记录稳定操作和状态，不保存敏感/raw 媒体；
- health snapshot：暴露未释放资源、迟到 callback 和非法状态转换。
- diag fixture：提供 fake principal、permission/profile/effect matrix、virtual audit、confirmation token、operation journal 和静态/动态 catalog 场景。

Fake contract suite 至少覆盖：

- 正常 init/config/start/stop/release；
- capability UNKNOWN 与 UNSUPPORTED；
- partial init 和第 N 步失败；
- timeout/cancel；
- stop 后迟到 callback；
- stale generation；
- double release；
- buffer lease 泄漏；
- backpressure 与队列上限；
- graph diff 的幂等和补偿。
- Diag 未授权、profile 拒绝、token replay、drain/invoke race、result overflow 和 audit failure。

Fake 只能证明调用方遵守公共契约。每个真机 backend 仍必须运行可移植 contract suite 子集和 HIL 专项测试，避免“Fake 自证正确”。

## 10. x86/x64 兼容策略

### 10.1 目标命名

- 正式 Host 目标名使用 host_linux_x86_64。
- 现有 ARCH=x86 只视作历史条件名，不把它解释为已支持的 32 位 x86。
- 若必须兼容 i386，单独建立 host_linux_i386_compile，至少验证 -m32 工具链、依赖和 ABI；默认不运行产品集成测试。

### 10.2 依赖

- Host 测试不得链接仓库内 32 位 ARM 动态库。
- 优先选择纯源码公共逻辑、标准库或 Host 原生白名单依赖。
- protobuf/zmq 等上层测试先通过窄 adapter + fake 隔离；确需原生依赖时固定兼容版本与许可证。
- 测试运行不得在线下载依赖；依赖准备与测试执行分离。
- Host 产物与 ARM 产物放入不同输出目录，禁止库搜索路径串用。

### 10.3 数据与并发

- 开启 64 位指针审计，禁止 pointer-to-u32。
- 对 wire/persist 格式做 golden vector 和大小端测试。
- 对涉及原子的无锁代码明确 memory order；无法证明时使用 OSAL mutex。
- ASan/UBSan 用于常规 Host 测试；TSan 独立运行，避免与 ASan 混合造成噪声。

## 11. RTOS 兼容策略

定义四种组合 profile：

- linux_full：osal_core + filesystem + process + network + optional dynamic library；
- host_sim：POSIX osal_core + fake time/backend + 测试平台服务；
- rtos_control：osal_core + static config + bounded queue，不含进程、dlopen、ZMQ；
- amp_proxy：RTOS 本地控制 backend + Linux 代理服务。

RTOS 约束前置到公共设计：

- 不要求 malloc 一定存在；支持 caller-owned arena 或静态 pool；
- 队列、线程、buffer 上限可配置且可查询；
- 日志允许 ring buffer/sink 替换；
- 初始化不依赖目录扫描、环境变量和配置文件；
- backend 静态注册；
- 控制面 RPC 有版本、长度、超时、幂等 token；
- 大数据面走共享内存/lease，不复制进控制 RPC；
- 明确 cache clean/invalidate、所有权转移与 peer reset；
- Linux 与 RTOS 时钟域不默认同步，跨核消息保存各自 monotonic 时间和可选映射。
- Diag 使用 static catalog、bounded writer、固定 limits manifest；Linux proxy 终止 JSON，RTOS 侧使用 versioned TLV/CBOR。

如果最终 RTOS 只承担硬实时采集/控制，则 APP 和大部分 API 继续留在 Linux，RTOS 只实现窄 HDI 服务。若确需单芯 RTOS 产品，再根据资源预算拆分 API 子集，而不是复制 linux_full。

## 12. 当前编译规则冻结与 sidecar 路径

### 12.1 冻结边界

在 P0/P1 阶段：

- 不修改根 Makefile；
- 不修改 build/build.mk、build/mi_dep.mk；
- 不修改现有模块 lib.mk；
- 不把 host_fake 放进 modules 下会被递归收集的生产源目录；
- 不执行 make ARCH=x86 all 作为 Host 方案；
- 不改变 SSC305 量产链接库和产物路径。

新增内容仅允许落在 docs/architecture 和未来 tests/host sidecar 下。进入 P2 以后如需改公开头和源码，必须由独立实现任务审批，仍不隐式改变产品构建。

### 12.2 未来 tests/host 形态

建议 sidecar：

    tests/host/
      Makefile
      README.md
      include/
      fakes/
      fixtures/
      contract/
      unit/
      integration/
      scripts/

它显式列出可移植源文件和 fake，不递归吸收 modules 全部源码，也不链接 ARM 库。第一版使用现有 Make 习惯；迁移 GROS 时将相同 source set 映射为 Host target，测试语义不变。

### 12.3 架构边界门禁

从 P2 起，每个迁移域必须配置可自动执行的边界检查：

- public-header gate：API/HDI 公共头禁止 MI、RDK、pthread、Linux syscall 和板级宏；允许项必须登记原因、owner 和失效日期；
- dependency gate：APP 普通业务不得直接包含 HDI，API 不得包含 backend 私有头，HDI core 不得反向依赖 API/APP；
- diag-contract gate：Common diag 禁止 JSON、APP profile、handler、registry/runtime global；HDI/API/OSAL/backend 禁止依赖 diag_runtime；
- diag-policy gate：command manifest 缺 effect/permission/profile/deadline/limits/audit/recovery 即拒绝构建或注册；
- diag-production gate：production catalog/symbol 中 destructive/update/reboot/safety handler 默认不可达；
- diag-maintenance gate：非只读 adapter 不得直接调用 HDI/backend，只能调用批准的领域 maintenance use case；
- source-set gate：Host target 不得收集 vendor backend 源码或 ARM-only 库；
- symbol/dependency audit：Host 产物检查 ELF 架构和动态依赖，目标产物检查误链 Host 库；
- contract-version gate：ops ABI、board manifest、fixture 和 RPC 版本不匹配时 fail closed；
- exception budget：例外只允许 composition root、diag adapter 对 typed 只读 health port 的访问，以及有到期日的兼容 shim。

这些门禁先在 sidecar/CI report-only 运行，消除历史存量后再升级为 blocking，避免一次性阻断当前产品构建。

## 13. 未来源码形态

以下只是目标布局，不在本方案评审通过时自动移动文件：

    modules/
      common/
        include/diag/
      osal/
        include/
        posix/
        rtos/
        fake/
      hdi/
        include/
        core/
        backends/
          ssc305_mi/
          ssu9383cm_mi/
          rdk_x5/
          host_fake/
          rtos/
      api/
        core/
        media/
        storage/
        transport/
      diag/
        include/
        runtime/
        codecs/
        transports/
        adapters/
        compat/v4/
    products/
      pcr02/
      product_profiles/
      product_diag_manifests/
    tests/
      host/
      contract/
      hil/

迁移遵循“先建立 seam，再搬实现”的原则。不得一次性移动全部目录并同时改变接口和构建系统。

## 14. GROS 目标模型

GROS 至少需要表达这些正交维度：

- target_os；
- target_arch；
- soc；
- board；
- profile；
- backend；
- feature_set；
- toolchain；
- sdk_identity；
- output_namespace。
- diag_profile；
- diag_limits_manifest；
- diag_codec；
- command_catalog_version。

建议组合：

| target | 关键选择 |
|---|---|
| host_linux_x86_64 | os=linux, arch=x86_64, profile=host_sim, backend=host_fake, diag=host_sim |
| ssc305_linux | os=linux, arch=armv7, profile=linux_full, backend=ssc305_mi, diag=production/service/factory |
| ssu9383cm_linux | os=linux, arch=目标工具链实际值, profile=linux_full, backend=ssu9383cm_mi, diag=目标产品 profile |
| rdk_x5_linux | os=linux, arch=aarch64, profile=linux_full, backend=rdk_x5, diag=目标产品 profile |
| rtos_control | os=项目 RTOS, arch=目标核, profile=rtos_control, backend=rtos_native/amp_proxy, diag=static bounded |

GROS 迁移门禁：

1. owner 提供并冻结正式规格；
2. 当前 Make 与 GROS 在同一平台生成等价 source/dependency/define/link map；
3. 关键产物做 ABI、功能和包内容对比；
4. 双轨期内量产仍以当前批准路径为准；
5. 单平台验证通过后逐个平台切换；
6. 任何平台失败可退回旧构建，不回退 HDI contract。
7. command catalog、policy/limits manifest、codec 和 compat source set 必须进入等价对比。

## 15. 分阶段迁移计划

Diag 重构不是可选后续项，而是贯穿 P0–P10 的强制轨道：

- P0 对应 D0：现有命令 inventory、effect、owner、profile 和真实调用层冻结；
- P1 对应 D6 基础：Host policy/codec/lifecycle contract 与 Fake 先行；
- P2 对应 D1/D2：旧 dispatcher 前置中央 policy，并建立无 JSON 的 v5 Common ABI；
- P3 对应 D3：独立 diag_runtime、catalog generation、invocation lease、drain/cancel；
- P4/P5 对应 D4/D5：HDI/API/APP adapters、maintenance use case、profile 和 v4 alias；
- P6/P7/P8 对应 D7：各平台与 RTOS contract/HIL；
- P9 把同一 source set、catalog、policy/limits manifest 映射到 GROS；
- P10 对应 D8：在消费者证据完整后移除 v4 compat。

任何平台进入支持状态前，必须同时满足 HDI backend contract 和适用的 Diag DG-01 至 DG-18。

### P0：基线与契约冻结

范围：

- 保存当前平台、SDK、板型、sensor 和构建命令基线；
- 记录公共头泄漏、厂商类型、直接 HDI/OS 调用和 ARM-only 依赖；
- 冻结第一版 error/lifecycle/handle/capability 契约。
- 生成所有现有 Diag command inventory，逐条标记 effect、owner、真实调用层、profile、capability、敏感度和迁移 disposition。

验收：

- 有可复查的基线清单；
- owner 确认首个 SSC305 垂直切片；
- 不存在 unknown effect 的现有命令；
- 不改产品构建。

回滚：纯文档和清单，无运行时影响。

### P1：sidecar Host 纯逻辑测试

范围：

- 新建 tests/host；
- 先纳入无 MI、无 pthread 公开泄漏、无 ARM 库的纯逻辑；
- 引入 sanitizer 和 deterministic fixture。
- 建立 Diag descriptor/policy/codec/lifecycle/Fake principal/confirmation/audit contract 测试骨架。

验收：

- host_linux_x86_64 可独立 clean/build/test；
- 与产品构建输出隔离；
- policy 的 permission × profile × effect 负面矩阵可在 Host 独立运行；
- 当前 SSC305 build 文件无差异。

回滚：移除 sidecar target，不影响产品。

### P2：公共头与 OSAL seam

范围：

- 把 pthread/Linux 类型移出 API/HDI 公共头；
- 建立 osal_core 接口和 POSIX 实现；
- 文件、进程、网络拆为可选平台服务；
- 加 C11/C++17 header compile test。
- 新增无 JSON/handler/runtime global 的 v5 Common Diag ABI；
- 在旧 dispatcher 与 handler 之间加入 descriptor、central policy、limits 和 audit membrane，metadata 缺失 fail closed。

验收：

- 公共头可在 x86_64 无厂商 SDK 编译；
- POSIX 实现对现有 Linux 行为回归；
- Common Diag 头通过 32/64 位布局和 wire golden test；
- 所有旧命令即使保留名称也经过新 policy；
- ABI 变化经过显式清单审批。

回滚：兼容 shim 保留一个发布周期，按域恢复旧入口。

### P3：HDI facade 与 backend ops

范围：

- 先选 system/device 或 audio 的小域建立 facade；
- 把 SSC305 当前实现包入 ssc305_mi backend；
- 实现同契约 host_fake；
- 统一 error、capability、lifecycle。
- 建立独立 diag_runtime、immutable catalog generation、provider invocation lease、drain/cancel 和 bounded writer；
- composition root 注入 runtime/adapters，legacy DIAGPROV_Register/DIAG_Invoke 只保留 compat 转发。

验收：

- fake 与 SSC305 可测子集通过同一 contract suite；
- API 不包含厂商头；
- HDI/API/OSAL/backend 不依赖 diag_runtime；
- unregister/invoke race、迟到结果和 audit failure contract 通过；
- 资源账本在正常和故障路径归零。

回滚：保留旧 HDI adapter，由 feature 控制单域切换。

### P4：视频垂直切片

范围：

- 建立 frame/lease、graph compiler、operation plan；
- SSC305 backend 执行真实节点；
- Host 使用 synthetic frame 和 packet fixture。
- 建立 observe.video health 与受限 selftest adapter；大结果使用 artifact/stream handle。

验收：

- Host 覆盖 graph diff、补偿、背压和迟到事件；
- SSC305 HIL 覆盖 capture/start/stop/release；
- 性能和图像质量只在 HIL 判定。
- selftest 结束恢复原状态且 residue=0。

回滚：视频域独立 feature 回到旧路径。

### P5：API/APP 窄端口

范围：

- 拆 CameraPort、AudioPort、StoragePort、PowerPort、DeviceInfoPort；
- 逐个迁移 DvrCommandHandler 等消费者；
- 建立 API + fake HDI + APP 工作流测试。
- 把现有 hdi/api/app provider 移入 diag adapters；
- 产品控制移出 Diag；format、identity、OTA、reboot、motor 等进入领域 maintenance use case；
- 固化 production/service/factory/product_test/host catalog 与 v4 alias manifest。

验收：

- 迁移组件不依赖大型 HardwareApi；
- 普通 APP 业务无直接 HDI 调用；
- composition root 和 diag adapter typed health port 例外有静态白名单；
- 非只读 adapter 无 direct HDI/backend 调用；
- production 高风险 handler 通过 catalog/symbol audit 证明不可达。

回滚：按消费者保留旧适配器。

### P6：SSU9383CM 后端

范围：

- 冻结 SDK/板型/核间拓扑；
- 复用公共 SigmaStar 辅助代码，但保持 backend 独立；
- 实现能力探测和平台专项 HIL。
- 接入 SSU health/capability adapter；RISC-V/RTOS 通过 versioned proxy，不复制 Linux JSON runtime。

验收：

- 公共 contract suite 通过；
- 不支持项明确返回 UNSUPPORTED；
- RISC-V/RTOS 路径若未验证保持 UNKNOWN。
- Diag peer reset、generation、bounded payload 和 profile catalog 通过验证。

回滚：平台 target 不发布，不影响 SSC305。

### P7：RDK X5 后端

范围：

- 冻结项目 BSP 和批准硬件；
- 映射 X5 camera/media/system API 到 HDI；
- 建立 aarch64 cross build 与实板 HIL。
- 接入 X5 typed health/selftest/maintenance adapter，绑定 BSP/board/sensor identity。

验收：

- contract suite + X5 专项测试通过；
- 不复用 ARMv7 预编译库；
- capability identity 绑定 X5 BSP/板/sensor。
- X5 production catalog 无未经批准的 destructive/update/safety handler。

回滚：X5 target 独立撤回。

### P8：RTOS profile

范围：

- owner 先选择 rtos_control 或 amp_proxy；
- 实现 bounded OSAL、静态 backend、RPC/共享内存契约；
- 实现 static Diag catalog、bounded writer、TLV/CBOR、fixed limits 和 Linux proxy。

验收：

- RTOS 资源预算、超时、peer reset、cache 规则通过实机验证；
- 公共控制面 contract 的可测子集通过；
- Linux/RTOS peer reset 后资源和 generation 能收敛。
- init 后默认无 heap、无动态注册，所有 command limits 可查询。

回滚：RTOS profile 可不随首版发布，不影响各 Linux target。

### P9：GROS 双轨迁移

前置条件：

- P0–P7 的 target/source/dependency 边界已稳定；
- owner 提供并冻结 GROS 正式规格；
- RTOS 是否进入同批迁移由 P8 结果单独决定。

范围：

- 先映射 Host target，再迁移一个已稳定的 Linux target；
- 生成并对比 source/dependency/define/link map；
- 映射 diag profile/catalog/policy/limits/codec/compat source set；
- 按平台逐一双轨验证，不同时改变 HDI contract 或目录布局。

验收：

- GROS 与旧构建的关键产物 ABI、功能和包内容等价；
- 所有 target 使用隔离的 toolchain、SDK identity 和 output namespace；
- 每个平台可独立退回旧构建。

回滚：只回退构建入口，不回退已验证的 HDI contract 和 backend 边界。

### P10：v4 Diag compat 移除

前置条件：

- repo、产测、售后脚本、现场工具和产品 catalog 均有消费者盘点；
- alias deprecation 到达 owner 批准的 remove_after；
- rollback 包和迁移说明已验证。

范围：

- 删除 legacy APP global register/invoke compat；
- 删除 v4 command aliases 和旧 JSON-only Common 头；
- 保留 catalog/audit/迁移验证证据。

验收：

- 无未迁移消费者；
- v5 canonical catalog、Host contract 和所有已支持平台 HIL 通过；
- removal 不恢复任何权限直通或 direct HDI 写路径。

回滚：在批准周期内恢复 compat 包，不回退 central policy、audit 和新 Common ABI。

## 16. 测试与验证矩阵

| 门禁 | Host | SSC305 | SSU9383CM | RDK X5 | RTOS |
|---|---:|---:|---:|---:|---:|
| 公共头 C11/C++17 编译 | 必须 | 交叉编译 | 交叉编译 | 交叉编译 | 目标编译 |
| 纯逻辑 unit | 必须 | 可复用 | 可复用 | 可复用 | 可选子集 |
| ASan/UBSan | 必须 | 非主门禁 | 非主门禁 | 非主门禁 | 不适用 |
| TSan 独立 job | 关键模块 | 非主门禁 | 非主门禁 | 非主门禁 | RTOS 专项 |
| Fake contract | 必须 | 不替代真机 | 不替代真机 | 不替代真机 | 不替代真机 |
| Real backend contract | 不适用 | 必须 | 必须 | 必须 | 可测子集 |
| HIL/性能/质量 | 不适用 | 必须 | 必须 | 必须 | 必须 |
| 包与依赖审计 | Host 白名单 | 必须 | 必须 | 必须 | 必须 |
| Diag policy/codec/lifecycle | 必须 | contract + HIL | contract + HIL | contract + HIL | bounded contract |
| production catalog/symbol audit | 不适用 | 必须 | 必须 | 必须 | static allowlist |

最小负面场景：

- capability 未知时 fail closed；
- 资源耗尽；
- 第 N 步初始化失败；
- stop/release 并发；
- deadline 到期；
- peer/backend reset；
- callback 晚到和 generation 不匹配；
- buffer 双重释放与泄漏；
- 配置版本不兼容；
- Host fixture 与 contract 版本不匹配。
- 未认证 principal、错误 permission/profile、UNKNOWN effect/capability；
- confirmation expiry/replay/args mismatch；
- provider unregister 与 invoke race；
- path traversal、malformed JSON/TLV、result overflow；
- destructive audit sink failure；
- production catalog 意外出现高风险 handler。

## 17. 验收标准

### 17.1 当前方案验收

- AC-D1：明确 HDI、internal HAL、API、APP、OSAL 的职责和依赖方向。
- AC-D2：覆盖 SSC305、SSU9383CM、RDK X5、x86_64 Host 和 future RTOS。
- AC-D3：当前构建冻结与未来 GROS 边界清晰。
- AC-D4：给出 Host 可测范围、不可替代项和 ARM-only 依赖风险。
- AC-D5：给出 lifecycle、ownership、error、capability、handle/ABI 契约。
- AC-D6：每个迁移包有验收与回滚。
- AC-D7：独立 review 后 blocker=0、major=0。
- AC-D8：方案以 reviewing candidate 归档，可检索且不声称 owner 批准。
- AC-D9：Diag 的 Common/runtime/adapter/use-case 边界、安全策略、生命周期、资源预算和兼容策略形成强制 SSOT。
- AC-D10：所有已识别 Diag 问题均映射到 P0–P10、DG 门禁和 owner，不留作无验收的“后续优化”。

### 17.2 后续实现验收

- AC-I1：x86_64 sidecar 在无 ARM SDK/库环境 clean/build/test。
- AC-I2：SSC305 当前量产构建和关键功能无回归。
- AC-I3：同一 HDI contract suite 覆盖 fake 与所有真实 backend 的可测子集。
- AC-I4：公共头无厂商 SDK 和裸 OS 对象。
- AC-I5：Host sanitizer 无新增有效错误，资源账本归零。
- AC-I6：各平台能力绑定真实身份，UNKNOWN 不进入默认量产路径。
- AC-I7：每个平台 HIL 通过后才声明支持。
- AC-I8：GROS 双轨等价验证通过后才切换量产构建。
- AC-I9：Diag DG-01 至 DG-18 全部有 Host/target 对应证据。
- AC-I10：production 高风险命令不可达，maintenance 只经领域 use case，并具备 permission/guard/confirmation/audit/recovery。
- AC-I11：provider drain 无悬空 handler/context，RTOS static/bounded contract 通过。
- AC-I12：v4 compat 仅在有消费者证据的批准周期存在，并按 P10 闭环移除。

## 18. 风险与控制

| 风险 | 级别 | 控制 |
|---|---|---|
| 把厂商 SDK 逐函数包装成公共 HDI | 高 | 用领域语义和私有 backend ops；review 公共头 |
| Host Fake 通过但真机失败 | 高 | 同 contract suite + HIL；明确 L0–L4 证据等级 |
| x86_64 指针截断到 VS_HANDLE | 高 | generation/index 句柄、静态检查、sanitizer |
| ARM 预编译库误链 Host | 高 | 独立输出与依赖白名单、file/ELF 审计 |
| 大规模目录/构建/接口同时迁移 | 高 | P0–P10 小步切换、单域 feature 回滚 |
| RTOS 被迫承载 Linux 全栈 | 高 | profile 化，优先 rtos_control/amp_proxy |
| 能力按 SoC 猜测导致错误默认 | 高 | 三态能力与身份绑定，UNKNOWN fail closed |
| API/APP 继续泄露 pthread/MI 类型 | 中 | header compile test 与依赖规则 |
| GROS 规格不明造成返工 | 中 | 只冻结目标模型，正式 DSL 后双轨迁移 |
| 大型 HardwareApi 成为新 HAL | 中 | 按消费者拆窄端口，不做公开巨型类 |
| Diag 成为无权限产品后门 | 阻断 | central policy、effect/permission/profile、production catalog、audit |
| format/OTA/motor 绕过领域状态机 | 阻断 | maintenance use case、device guard、二阶段确认 |
| provider 注销与 handler 并发造成 UAF | 高 | invocation lease、generation、drain barrier |
| JSON/固定大 buffer 阻断 RTOS | 高 | codec seam、bounded writer、target limits manifest |
| v4 compat 永久保留旧直通 | 高 | alias 同 policy、deprecation evidence、P10 移除 |

## 19. 可恢复执行规则

- goal_statement：在不改变当前编译规则的前提下，形成可审查、可归档、可阶段实施的 HDI/HAL 跨平台与 x86_64 Host 方案。
- completion_claim：方案、独立 review、验证证据和 reviewing archive candidate 均完成；不包含代码实现和 owner 批准。
- claimant：Codex。
- verifier：本轮独立 review loop；team-core owner review 待完成。
- retry_budget：同一失败路径最多重试 2 次，之后重规划。
- evidence_stale_after：24 小时；涉及工作区或 Hub 状态的证据在过期后重跑。
- heartbeat checkpoints：方案初稿、review 修复、验证、归档 dry-run、归档 apply、final coach。
- stop conditions：
  - review blocker/major 未清零时禁止归档；
  - Hub 事务或精确候选检查失败时不得声明归档完成；
  - 需要 owner/BSP/GROS 规格时标记 open item，不伪造结论；
  - 发现需修改产品构建或源码时停止本任务，另开实现任务审批。

## 20. 证据索引

### 20.1 仓库证据

- build/mi_dep.mk：存在 ARCH=x86 本机编译分支，但未形成受控的 x86_64 产品目标。
- build/build.mk：当前产品构建集中包含 MI 依赖，并链接 Linux/POSIX 相关库。
- include/hdi/hdi_os.h：公共头当前暴露 POSIX/Linux。
- include/hdi/hdi_init.h：公开注释/契约包含 SigmaStar MI_SYS。
- include/hdi/hdi_ao.h：存在板级 GPIO 宏。
- include/api/api_video.h：API 公开头包含 HDI 类型。
- include/api/api_zmq.h：API 公开结构包含 pthread 同步对象。
- include/common/vs_type.h：VS_HANDLE/VS_ID 为 VS_U32。
- include/common/diag/diag_types.h：当前 JSON reply limit、layer enum 和 handler 泄漏。
- include/common/diag/diag_provider.h、diag_contract.h：当前 APP runtime global contract。
- modules/hdi/src/hdi_hw/hdi_sys.c：直接包含 mi_sys.h。
- modules/api/src/api_container/api_list.c：直接使用 VSHDIOS_*。
- modules/app/src/app_diag/framework：当前 registry/dispatcher/runtime 实现、裸 handler lookup 和 busy spin。
- modules/app/src/app_diag/provider：当前 observe、产品控制和高风险 maintenance 混合。
- modules/app/src/app_diag/ipc/app_diag_cmd_node.c：当前 JSON/IPC 与 32 KiB 动态 reply。
- modules/sensor/hardware/hardware_api.h：现有大型具体硬件类，适合拆窄端口而非作为 HAL 公共面。
- tests/thread_pool、tests/bridge、tests/transport：已有 sidecar 风格测试和 fake 先例。
- repo 内抽查三方动态库：为 32 位 ARM ELF，不可供 x86_64 Host 链接。

### 20.2 历史知识证据

- project current architecture：hdi-api-app-functional-overview，作为历史来源和分层意图，不作为当前代码已完成解耦的证明。
- embedded architecture：SigmaStar capability matrix 与 internal overview，支持 SSC305/SSU9383CM 的差异化 backend 决策。
- RDK X5 first-boot runbook：支持 X5 ARM64 Linux/Buildroot 基线。
- X5 approved vendor list validation：支持已知板卡/外设线索，但不证明本项目最终选型或当前在线最新版。

### 20.3 被排除的证据

一次通过 wrapper 管道统计 MI/POSIX 命中数得到零值，但与直接 rg 命中相矛盾，因此该计数路径判定为不可靠并从结论中排除。方案只使用可定位到文件/行的直接查询和 ELF 类型检查，不使用该统计数字。

## 21. 数据治理与归档边界

- 文档只记录仓库相对路径、公开平台名、抽象架构和可复用结论。
- 不归档 raw session、完整日志、二进制、媒体原始数据、credential、token 或个人路径。
- 归档状态固定为 reviewing，owner 未签字前不得提升 active。
- Diag 独立 SSOT 与总体方案必须双向关联；command manifest、policy/limits 和测试后续作为机械一致性资产治理。
- 归档 source_from 使用稳定描述，不写临时路径或会话 ID。
- 若平台/BSP 事实更新，先更新 capability identity 和 evidence，再复审本决策。

## 22. 最终决策状态

本方案已通过包含 Diag 平面重构的本轮分离式 review。归档状态仍保持 reviewing，等待 team-core、security、product/platform owner 评审；该 review 不为未实现的 Host、SSU9383CM、RDK X5、RTOS、Diag runtime 或 GROS 功能背书。
