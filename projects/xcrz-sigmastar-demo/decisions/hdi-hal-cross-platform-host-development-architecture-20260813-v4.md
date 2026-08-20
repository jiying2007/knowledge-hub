---
doc_type: architecture-decision-baseline
decision_id: pcr02-hdi-hal-cross-platform-host-development-architecture-20260813-v4
supersedes_candidate: pcr02-hdi-hal-cross-platform-host-development-architecture-20260813-v3
related_review: pcr02-hdi-hal-diag-final-architecture-determination-20260813
created: 2026-08-13
updated: 2026-08-13
platforms:
- SSC305
- SSU9383CM
- RDK X5
- Linux x86_64 Host
- future RTOS
build_policy: current Make remains the sole build authority; no dual build path
id: pcr02-hdi-hal-cross-platform-host-development-architecture-20260813-v4
title: HDI/HAL/Diag 跨平台硬切换与 Host 自动化最终架构基线 v4
kind: decision
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/decisions/hdi-hal-cross-platform-host-development-architecture-20260813-v4.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: final-design-review
  from: final architecture determination with repository static evidence
  source_sha256: a25a31b8d778fd4cd0c9f9441add7a89c18ee9ca3b4cf2c256a903e27e23dbec
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
- diag
- hard-cut
- host-test
- artifact-lifecycle
- release-gates
validation_refs:
- projects/xcrz-sigmastar-demo/decisions/hdi-hal-cross-platform-host-development-architecture-20260813-v4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/decisions/hdi-hal-cross-platform-host-development-architecture-20260813-v4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-13'
updated_at: '2026-08-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-13'
manual_validation_pending: true
summary_zh: 冻结 HDI/HAL/API/APP/Diag 跨平台硬切换最终架构、x86_64 Host、唯一兼容政策、profile 制品生命周期与三层自动化门禁。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- HDI/HAL/Diag 跨平台硬切换与 Host 自动化最终架构基线 v4
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# HDI/HAL 跨平台与 Host 开发测试完整方案

## 1. 结论

本项目采用“稳定语义接口 + 可替换平台后端 + 能力驱动组合”的唯一目标态，并以一次产品分支硬切换交付：

1. HDI 是面向 API 的稳定硬件语义接口；HAL 是 HDI 内部的平台适配机制，不向 API、APP 泄露厂商 SDK 类型、板级引脚和操作系统对象。
2. 本次重构继续使用当前 Make 体系作为唯一构建权威；允许为新目录更新显式 source/dependency list，但不改变根构建入口、工具链、打包和量产产物语义，不引入第二套构建规则。
3. Linux x86_64 是第一优先级 Host 平台。Host 只承诺纯逻辑、协议、状态机、资源生命周期、API 编排和 APP 部分业务的开发测试；不模拟真实图像质量、硬编解码性能、驱动时序和板级电气行为。
4. SSC305 保持参考实现地位；SSU9383CM 与 RDK X5 分别落成独立后端，不通过大量条件编译把三套 SDK 混入公共层。
5. RTOS 先支持 rtos_control 或 amp_proxy 受限配置，不默认搬迁完整 Linux APP；所有公共接口不得假设文件系统、进程、动态加载、ZMQ 或 POSIX 线程存在。
6. 未来 GROS 只负责目标、源码、依赖与 feature 组合。其语法、包管理、锁文件和缓存规则尚无可信规格，本方案只定义 GROS 需要表达的目标模型，不臆造具体 DSL。
7. 唯一 Host 目标名是 host_linux_x86_64；旧 ARCH=x86 条件不作为别名继续承载 Host 语义，i386 不在支持范围。
8. Diag、Observability 与 Maintenance 是一条正交平面：Common 只保留无 OS/JSON/runtime 的 ABI；独立 diag_runtime 承担 policy、registry、dispatcher、audit、codec 和 transport；非只读操作必须通过领域 maintenance use case；旧命令、旧全局符号和旧目录不进入目标产物。
9. 重构阶段只允许存在于隔离分支/工作区，阶段 checkpoint 不是可发布混合态；合入产品分支时新旧实现、compat shim、feature fallback、alias 和过期测试必须全部清零。
10. production、service、factory、product_test 不只是不同 catalog，而是受 target identity、独立签名策略、设备生命周期和启动/升级策略共同约束的不同制品；量产设备不能通过普通 OTA 或运行时配置切换到 factory/product_test。

该决策是本次重构的最终设计基线，已通过硬切换、零残留和最终定案 review；不代表平台实现、实板验证、正式 owner attestation 或发布完成。实现若改变任一冻结边界，必须提交新 ADR 并重跑受影响的完整门禁，不建立“临时兼容”例外。

## 2. 目标与非目标

### 2.1 目标

- 在 SSC305、SSU9383CM、RDK X5 和后续 RTOS 之间保持 API/APP 的主体代码稳定。
- 把 SigmaStar MI、RDK X5 SDK、Linux/POSIX、RTOS 和板级差异收敛到明确边界。
- 让 x86_64 PC 能覆盖高频逻辑开发、故障注入、资源泄漏和并发契约测试。
- 保持当前 Make 构建入口、工具链和产物契约，同时让新 source set 成为唯一实现。
- 为未来 GROS 提供可直接映射的 target/profile/backend/capability 模型。
- 给每个重构 checkpoint 配置独立验收和停止条件，但只允许整体硬切换进入产品分支。
- 一次性冻结 Diag 的分层、安全策略、生命周期、资源预算、Host/RTOS contract 和长期治理，不留作非约束性后续优化。

### 2.2 非目标

- 不把本设计评审冒充三个 SoC backend、RTOS 或 GROS 已实现。
- 不承诺 PC 能执行 ARM 专有动态库、真实 ISP 调优、硬编解码性能或硬件在环验证。
- 不把 HAL 设计成公开的“大而全”硬件类，也不要求运行时插件化。
- 不保留旧目录、旧符号或旧调用链作为运行时回退；安装包、量产和 OTA 的外部行为变化必须由切换清单显式声明。
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
- 已部署持久化数据或外部 wire consumer 的精确清单；清单为空时按破坏性硬切换处理，非空时只允许边界一次性迁移工具，不允许核心双实现。
- Host 允许的本机三方依赖白名单。
- 各产品设备生命周期状态、factory/service 签名根、service 授权票据签发方和 recovery boot 能力。

这些事项不改变最终架构方向，但会阻塞对应 target 的实现或支持声明；任何未回答项均 fail closed，不产生兼容默认值、共享签名根或可绕过的启动路径。

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
- 公共结构在当前 major 内布局冻结；任何布局变化提升 major、全仓消费者同一变更迁移，wire/persist schema major 不匹配明确拒绝。
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
- composition root 读取编译内置 target identity 绑定唯一 backend/OSAL/diag profile，并构造 runtime 和 adapters；运行时参数不能切换 profile；
- APP 不直接查询 HDI；只读 hdi adapter 只调用 typed HDI capability/health port；
- transport/auth adapter 将已认证 principal 交给 diag_runtime，不能把“本机 IPC”视为天然可信；
- 现有 HardwareApi 不直接被命名为 HAL，目标态拆为 CameraPort、AudioPort、StoragePort、PowerPort、DeviceInfoPort 等窄接口；
- DvrCommandHandler 等全部消费者在硬切换变更中改为依赖窄端口或领域 API，旧大接口删除。

### 4.7 Diag、Observability 与 Maintenance 平面

完整 SSOT 见 docs/architecture/diag-observability-maintenance-plane.md，以下为不可删减的总体约束：

- Common contract 无 OS、JSON、runtime global 和 handler；
- diag_runtime 独立承载 immutable catalog、policy、dispatcher、provider lifecycle、audit、codec 和 transport ports；
- command manifest 强制包含 effect、required_permissions、build_profiles、capability/state guard、deadline、limits、audit、concurrency、idempotency、confirmation 和 recovery；build_profiles 只在生成期过滤，runtime descriptor 不携带 profile；
- 命令分 observe/selftest/maint/admin；名称不能替代 effect policy；
- production 默认只注册 observe 和批准的轻量 selftest，高风险 handler 必须经 catalog/symbol audit 证明不可达；
- destructive/update/reboot/safety critical 使用二阶段确认和独立安全 guard；
- provider invoke 使用 lease/generation/drain barrier，registry lock 内禁止执行 handler；
- JSON 是 Linux codec，RTOS 使用 static catalog、bounded writer、TLV/CBOR 或 Linux proxy；
- 大型 media/dump/firmware 使用 artifact/stream handle，不进入 inline reply；
- 旧命令名只进入 tombstone/cutover inventory，调用方同包迁移，目标 runtime 不生成 alias 或旧 handler。

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

- VS_HANDLE/VS_ID 保持固定宽度整数语义并编码 index + generation，禁止承载地址或 native handle。
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

- request context 包含 correlation、principal hash、granted permissions、authentication strength、source、target identity hash、deadline、idempotency key 和 request generation；role 只在认证 adapter 映射期存在，不保存 credential 明文且不接受调用方覆盖 target identity。
- stable diag status 与 VS_ERROR/errno/vendor/RTOS native code 分离；provider 不把 native code 暴露给业务决策。
- 调用顺序固定为 validate/admission → immutable catalog lookup → permission/effect/authentication-strength/capability → rate budget → atomic READY invocation lease → device guard → confirmation/idempotency/deadline → high-risk intent audit → handler → redaction/completion audit → release lease/budget；profile 已在生成期裁剪，不进入运行时分支。
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

能力键按以下域命名：

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

| 平台 | OS/架构基线 | backend | 目标 profile | 支持职责 | 必须补证 |
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
- diag fixture：提供 fake principal、permission/profile/effect matrix、virtual audit、confirmation token、operation journal 和 fixed catalog/provider bind-unbind 场景。

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

## 10. Linux x86_64 Host target

### 10.1 目标命名

- 正式 Host 目标名使用 host_linux_x86_64。
- 现有 ARCH=x86 是待清理条件名；硬切换后 Host source set、脚本和 CI 对该名称零命中。
- 不建立 host_linux_i386、-m32 或 x86/x64 双目标；需要 32 位 wire/ABI 证据时使用交叉编译布局测试，不形成可发布 i386 target。

### 10.2 依赖

- Host 测试不得链接仓库内 32 位 ARM 动态库。
- 优先选择纯源码公共逻辑、标准库或 Host 原生白名单依赖。
- protobuf/zmq 等上层测试通过窄 adapter + fake 隔离；批准进入 Host target 的原生依赖必须锁定版本、哈希和许可证。
- 测试运行不得在线下载依赖；依赖准备与测试执行分离。
- Host 产物与 ARM 产物放入不同输出目录，禁止库搜索路径串用。

### 10.3 数据与并发

- 开启 64 位指针审计，禁止 pointer-to-u32。
- 对 wire/persist 格式做 golden vector 和大小端测试。
- 对涉及原子的无锁代码明确 memory order；无法证明时使用 OSAL mutex。
- ASan/UBSan 用于常规 Host 测试；TSan 独立运行，避免与 ASan 混合造成噪声。

## 11. RTOS target contract

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

## 12. 当前 Make 唯一构建与永久 Host 门禁

### 12.1 构建权威边界

- 本次重构期间 Make 是唯一构建入口，不引入 CMake/GROS/第二套产品构建描述。
- 根构建入口、toolchain 选择、打包、量产产物名称和发布流程保持不变；新目录通过显式 source/dependency list 接入，不使用递归发现。
- config/targets 下的 target/source-set manifest 是组合 SSOT，生成的 Make source fragment 禁止手改并携带 manifest hash。
- 同一 target 只能选择一个 backend、一个 OSAL 实现和一个 Diag profile；旧/新实现同时入链直接构建失败。
- 每个 target manifest 必须声明 product_id、board_id、soc_id、target_id、profile_id、lifecycle_class、signing_policy_id、release_policy_id、catalog/policy/limits hash 和 anti_rollback_epoch；缺失或不一致时禁止打包。
- host_fake 只进入 host_linux_x86_64，任何生产 target 命中 fake 源码或 Host 原生库都构建失败。
- SSC305 量产 target 在硬切换前后保持产品入口与产物契约；内部源布局和依赖边可以改变。

### 12.2 永久 Host 形态

    tests/host/
      Makefile
      README.md
      fakes/
      fixtures/
      contract/
      unit/
      integration/
      fuzz/

host_linux_x86_64 是长期一等测试 target，不是迁移完成后可删除的 sidecar。它与产品 target 读取同一 contract/schema/source-set manifest，只替换 OSAL、backend、clock、security 和 artifact ports；不得复制 production core 形成 Host 专用实现。

### 12.3 Blocking 架构门禁

以下门禁从硬切换变更的第一次 CI 起即为 blocking，不存在 report-only、exception budget 或到期 shim：

- public-header：API/HDI/Common 公开头禁止 MI、RDK、pthread、Linux syscall、板级宏和 backend 私有类型；
- dependency：APP 普通业务不得直接依赖 HDI，API 不得依赖 backend 私有头，HDI/core/OSAL 不得反向依赖 API/APP/diag_runtime；composition root 和只读 health adapter 是规则中的明确边，不是例外；
- diag-contract：Common diag 禁止 JSON、APP profile、handler pointer、registry/runtime global；
- diag-policy：command manifest 缺 effect/permission/profile/deadline/limits/audit/recovery 即生成失败；
- production-catalog：未逐项批准的 destructive/update/reboot/safety handler 不得出现在 production source set、symbol 或 catalog；
- maintenance-route：非只读 adapter 只能调用批准的领域 use case，不得调用 HDI/backend 写接口；
- source-set：Host 不得收集 vendor backend/ARM 库，生产 target 不得收集 fake、fuzz 或 Host native test 库；
- retired-residue：retired_identifiers.json 中的旧头、目录、宏、命令、全局符号和 target 名在 source/build/runtime script/test/product-test/service-tool 必须零命中；只允许 architecture review、cutover inventory 和 tombstone 的精确 evidence path 命中；
- symbol/dependency：检查 ELF 架构、导出符号、动态依赖、重复 backend 和未声明 native dependency；
- generated-clean：manifest 生成 C catalog、Make fragment、文档和 vectors 后工作区必须 clean，生成物 hash 必须匹配；
- contract-version：ABI、board manifest、fixture、RPC 和 catalog major 不匹配直接拒绝，不做运行时降级。

### 12.4 自动化命令契约

实现必须提供以下稳定入口，CI 与开发机使用同一命令：

    make architecture-check
    make generated-check
    make host_linux_x86_64-check
    make product-contract-check TARGET=ssc305_linux
    make product-contract-check TARGET=ssu9383cm_linux
    make product-contract-check TARGET=rdk_x5_linux
    make rtos-contract-check TARGET=rtos_control

architecture-check 执行 header/dependency/source-set/retired-residue/symbol 规则；generated-check 校验 schema、确定性生成和 source hash；Host check 执行 unit/contract/integration、ASan/UBSan、独立 TSan 和 fuzz smoke；target contract check 执行交叉编译、产物审计和可移植 contract suite。命令缺失、skip 或 unsupported 均不是 pass。

### 12.5 制品身份、签名与设备生命周期

- production、service、factory、product_test 使用不同 signing_policy_id；密钥材料、签发权限和允许的设备生命周期不可共用“全能”默认策略。
- manufacturing 生命周期只允许 factory/product_test 制品；设备完成不可逆量产转换后，boot chain、recovery 和 updater 必须拒绝 factory/product_test key、profile 或 target identity。
- production OTA 只能安装同 product/board、production profile、允许 anti-rollback epoch 的制品，禁止借 OTA 改 profile；校验必须在写入与启动两个阶段执行。
- service 制品不得替换 production A/B 正常槽，也不得进入普通 OTA 渠道；只能由受验证 recovery/临时启动路径加载，并同时要求物理或本地授权、设备 nonce 绑定、短期/单次 service ticket、到期失效和全量审计。
- service 会话结束、超时或异常重启后必须回到 production；service 对量产秘密、永久身份和安全熔丝的访问遵循独立最小权限 allowlist，不能因 profile 身份自动获得写权限。
- binary identity 覆盖 source、toolchain、target manifest、profile、catalog/policy/limits、签名策略和版本；boot/update/runtime audit 与发布 receipt 必须能关联到同一 identity。
- Host 只验证策略、签名元数据和拒绝矩阵；secure boot、recovery、生命周期熔断和 anti-rollback 必须由目标 boot chain/updater HIL 证明。无法证明时不得发布非 production 制品。

### 12.6 唯一兼容政策

| 边界 | 最终政策 | 允许的迁移机制 |
|---|---|---|
| 仓内 C/C++ 源码 API、HDI、HAL、OSAL、Diag runtime/provider | 同一变更全仓硬切，旧头、符号、wrapper、alias、feature fallback 零残留 | 无 |
| Common/backend/runtime 二进制 ABI | 仅当前 major 与精确 size/build identity，旧 major 明确拒绝 | 整体固件/制品回退，不在新 binary 内协商 |
| wire/RPC/Diag schema | 仅当前 major，旧 client 返回 UNSUPPORTED 且 handler 不执行 | 客户端、产测、售后工具与固件同发布包切换 |
| 持久化数据 | 只接受 supported_upgrade_floor 内有真实部署证据的来源 | 升级包一次性离线 migrator；不链接核心，floor 提升即删除 |
| CLI、脚本、服务和产测工具 | canonical name/id 同包切换，旧名只留 tombstone | 无运行时 alias/转发 |
| target/profile 制品 | product/board/profile/lifecycle/signing/epoch 精确匹配 | 受控 service 临时启动；不是 compatibility path |

cutover_inventory.json 必须覆盖表中全部 consumer；未登记的外部 consumer 不构成保留兼容层的理由，而是阻断切换并补齐 inventory。目标分支只存在一个当前 contract，跨版本共存只能发生在完整发布制品之间。

## 13. 目标源码形态

实现完成时仓库必须收敛到以下唯一布局；旧目录不得作为转发层保留：

    include/
      common/
        diag/
      osal/
      hdi/
      api/
    modules/
      osal/
        core/
        posix/
        rtos/
        fake/
      hdi/
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
        include/private/
        runtime/
        codecs/
        transports/
        adapters/
        manifests/
    products/
      pcr02/
      product_profiles/
      product_diag_manifests/
    config/
      targets/
      architecture/
        dependency_rules.json
        retired_identifiers.json
    tests/
      host/
      contract/
      hil/
    tools/
      archcheck/

实施、合并与回滚只以第 15 节 C0–C6 为准，本节不建立第二套迁移规则。

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

规范组合：

| target | 关键选择 |
|---|---|
| host_linux_x86_64 | os=linux, arch=x86_64, profile=host_sim, backend=host_fake, diag=host_sim |
| ssc305_linux_production | os=linux, arch=armv7, profile=linux_full, backend=ssc305_mi, diag=production |
| ssc305_linux_service | 同 production 平台身份，diag=service，独立受签名制品 |
| ssc305_linux_factory | 同 production 平台身份，diag=factory，独立受签名制品 |
| ssc305_linux_product_test | 同 production 平台身份，diag=product_test，独立受签名制品 |
| ssu9383cm_linux_<diag_profile> | os=linux, arch=目标工具链实际值, backend=ssu9383cm_mi；每个 target 只选一个批准 profile |
| rdk_x5_linux_<diag_profile> | os=linux, arch=aarch64, backend=rdk_x5；每个 target 只选一个批准 profile |
| rtos_control | os=项目 RTOS, arch=目标核, profile=rtos_control, backend=rtos_native/amp_proxy, diag=rtos_control |

上表每个非 Host target 还必须绑定第 12.5 节的 lifecycle_class、signing_policy_id 和 anti_rollback_epoch；相同 SoC、board 或 backend 不表示 profile 制品可以互换。

GROS 是未来独立硬切换项目，不与本次 HDI/HAL/Diag 重构混合：

1. owner 先冻结正式规格、toolchain、依赖锁定和产物模型；
2. 在隔离验证工作区用同一 target/source-set manifest 生成 Make 与 GROS 的 source/dependency/define/link map，只用于差异验证；
3. 所有已支持 target 的 ABI、功能、catalog/policy/limits hash、产物内容和 HIL 同时达到等价；
4. 切换提交把 GROS 设为唯一构建权威并删除 Make 产品规则和临时对比资产，不在产品分支长期双轨；
5. 失败时回退整个 GROS 切换提交或上一版发布制品，不恢复 HDI/HAL/Diag 旧 contract；
6. 未取得正式 GROS 规格前，不创建伪 DSL、占位 package 或第二份依赖清单。

## 15. 重构检查点与硬切换

C0–C6 只用于隔离重构分支内的执行和恢复，不是可发布阶段。C6 未通过前不得把任一新旧混合态合入产品分支。

### C0：现状清单与删除契约

- 固化平台、SDK、板型、sensor、构建、公共头、依赖边、Diag 命令和外部消费者清单；
- 每个旧文件、目录、宏、符号、命令和脚本只有 migrate、replace、delete 三种 disposition，不允许 keep-legacy/unknown；
- 生成 config/architecture/retired_identifiers.json 和 command_id tombstone；
- 完成条件：清单闭合、owner 明确、自动扫描可运行，不修改产品行为。

### C1：自动化基座先行

- 落地 target/source-set manifest、archcheck、generated-check 和永久 host_linux_x86_64 target；
- 建立 C11/C++17 header compile、dependency graph、ELF/symbol、manifest schema、deterministic generation、unit/contract/integration、sanitizer 和 fuzz smoke；
- 完成条件：所有新门禁 blocking，能对当前残留给出确定失败清单，禁止 skip 伪通过。

### C2：Common 与 OSAL 破坏性切换

- 公共头一次移除 pthread/Linux/vendor/board 类型；
- 建立 osal_core 与 POSIX/RTOS/fake 私有实现；
- 建立新的 Diag ABI major 1，Common 无 JSON、handler 和 runtime global；
- 同一变更迁移全部仓内消费者并删除旧头，不保留 wrapper；
- 完成条件：公开头独立编译、布局/wire vectors 通过、旧头和旧符号零命中。

### C3：HDI facade 与 internal HAL 唯一化

- 按 video/audio/storage/power/device 等窄域定义 facade、ops、error、lifecycle、capability 和 generation handle；
- SSC305 实现收敛到 ssc305_mi，Host 实现收敛到 host_fake；
- 删除旧 backend 入口、重复 helper 和平台条件分支；
- 完成条件：Fake 与 SSC305 可测子集通过同一 contract suite，单 target 只链接一个 backend，资源账本归零。

### C4：API/APP 边界硬切换

- APP 业务只依赖 API/窄 product port，composition root 是唯一装配点；
- API 消费 HDI facade，不包含 backend 私有头，不暴露 OS 对象；
- 视频 graph、frame/lease、补偿、背压和迟到事件进入 Host 自动测试；
- 全部消费者同一变更迁移，删除大型直通 HardwareApi 和 direct APP→HDI 路径；
- 完成条件：dependency gate 零违规，SSC305 核心业务回归与 HIL 通过。

### C5：Diag 单实现切换

- 按 Diag 规范 D0–D7 完成 manifest、runtime、policy、provider lease、adapters、maintenance journal、Host/RTOS contract；
- 产品功能命令移回领域 API，维护命令只调用领域 use case；
- 旧 DIAGPROV_Register/Unregister、DIAG_Invoke、旧 layer enum、旧 JSON Common 头、旧命令名和 app_diag runtime 同一变更删除；
- 完成条件：DG-01 至 DG-22、production catalog/symbol audit、profile 制品生命周期拒绝矩阵、Host negative matrix 和 SSC305 HIL 全部通过。

### C6：零残留与产品硬切换

- architecture-check、generated-check、host_linux_x86_64-check 和 SSC305 product-contract-check 全绿；
- retired identifiers、旧目录、旧 target、compat/alias/shim/fallback/duplicate test 在受管范围零命中；
- source tree、Make source fragment、文档、测试、产测和售后工具只引用新 contract；
- 生成切换 receipt，绑定源码、manifest、生成物、构建、Host、HIL、target identity、签名策略、生命周期验证和发布制品 hash；
- 只在 C6 完整通过后一次合入产品分支。回滚为整体 revert 或上一版发布制品，不在新代码中恢复旧路径。

### Target certification

- T-SSC305：C6 的首个量产证明，contract + 产品回归 + HIL + catalog/symbol/包审计 + profile 签名/启动/升级拒绝矩阵必须通过；
- T-SSU9383CM：冻结 SDK/板型/核间拓扑后新增独立 backend，不复制 SSC305 条件分支；Linux/RTOS peer reset、generation 和 bounded payload 必测；
- T-RDK-X5：冻结 BSP/板/sensor 后新增 aarch64 backend，不复用 ARMv7 库或 SigmaStar device path；
- T-RTOS：明确 rtos_control 或 amp_proxy，使用 bounded OSAL、static catalog、固定 limits、TLV/CBOR 和 shared-memory lease；init 后默认无 heap/动态注册。

每个 target 独立通过其 certification 后才进入支持清单；未通过只是不发布该 target，不影响已完成 target，也不引入通用代码 fallback。

## 16. 测试与验证矩阵

| 门禁 | Host | SSC305 | SSU9383CM | RDK X5 | RTOS |
|---|---:|---:|---:|---:|---:|
| 公共头 C11/C++17 编译 | 必须 | 交叉编译 | 交叉编译 | 交叉编译 | 目标编译 |
| 纯逻辑 unit | 必须 | 可复用 | 可复用 | 可复用 | 适用子集必须 |
| ASan/UBSan | 必须 | 非主门禁 | 非主门禁 | 非主门禁 | 不适用 |
| TSan 独立 job | 关键模块 | 非主门禁 | 非主门禁 | 非主门禁 | RTOS 专项 |
| Fake contract | 必须 | 不替代真机 | 不替代真机 | 不替代真机 | 不替代真机 |
| Real backend contract | 不适用 | 必须 | 必须 | 必须 | 可测子集 |
| HIL/性能/质量 | 不适用 | 必须 | 必须 | 必须 | 必须 |
| 包与依赖审计 | Host 白名单 | 必须 | 必须 | 必须 | 必须 |
| Diag policy/codec/lifecycle | 必须 | contract + HIL | contract + HIL | contract + HIL | bounded contract |
| production catalog/symbol audit | 不适用 | 必须 | 必须 | 必须 | static allowlist |
| retired residue 零命中 | 必须 | 必须 | 必须 | 必须 | 必须 |
| deterministic generation | 必须 | 必须 | 必须 | 必须 | 必须 |
| profile 签名/启动/升级拒绝矩阵 | 元数据模型 | 必须 | 必须 | 必须 | 适用 target 必须 |

### 16.1 阻断层级与证据新鲜度

| 层级 | 每次执行的最小集合 | 通过规则 |
|---|---|---|
| Presubmit | architecture/generated、Host unit/contract/integration、ASan/UBSan、独立 TSan、fuzz smoke、覆盖率差异 | 全部 blocking；缺 job、skip、unsupported、coverage 回退均失败 |
| Target integration | 对受影响 target 交叉构建、ELF/符号/依赖/包审计、portable contract、profile identity 拒绝矩阵 | target 与源码/manifest/toolchain identity 精确绑定 |
| Release certification | 完整产品回归、HIL、性能/质量、secure boot/update/lifecycle/anti-rollback、nightly fuzz corpus、发布包审计 | 全部证据未过期且 receipt 完整后才能发布 |

- HIL unavailable、runner/设备/网络基础设施错误和未执行不等于通过；固定重试预算耗尽后状态为 BLOCKED/FAIL，不允许绿色降级。
- 测试隔离必须包含 owner、缺陷链接、创建日期和最长 14 天 expiry；安全、契约、零残留、生成确定性和 profile 生命周期测试禁止隔离；过期隔离直接阻断。
- coverage 只统计受管手写源码，排除生成物和批准的 third_party/vendor；阈值与 changed-line/branch 不回退同时满足，不能通过扩大排除列表获得通过。
- receipt 记录 test_id、输入 identity、工具版本、时间、结果、重试/隔离状态和产物 hash；源码/manifest/toolchain/binary identity 任一变化立即失效，各证据最大时效由受审查的 target release_policy 显式声明，缺失或过期必须重跑。

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
- provider unbind 与 invoke race；
- path traversal、malformed JSON/TLV、result overflow；
- destructive audit sink failure；
- production catalog 意外出现高风险 handler。
- 旧头、旧符号、旧命令、旧 target、shim/alias/fallback 任一残留；
- target 同时链接两个 backend/OSAL/Diag runtime；
- 自动化 job 缺失、skip 或把 unsupported 计为 pass。
- 量产设备接受 factory/product_test 制品，或普通 OTA 能改变 profile；
- HIL/基础设施失败、过期隔离或旧 receipt 被计为通过。

## 17. 验收标准

### 17.1 当前方案验收

- AC-D1：明确 HDI、internal HAL、API、APP、OSAL 的职责和依赖方向。
- AC-D2：覆盖 SSC305、SSU9383CM、RDK X5、x86_64 Host 和 future RTOS。
- AC-D3：当前构建冻结与未来 GROS 边界清晰。
- AC-D4：给出 Host 可测范围、不可替代项和 ARM-only 依赖风险。
- AC-D5：给出 lifecycle、ownership、error、capability、handle/ABI 契约。
- AC-D6：C0–C6 每个检查点有验收，只有 C6 完成态可合入，回滚为整体提交/制品回退。
- AC-D7：独立 review 后 blocker=0、major=0。
- AC-D8：方案作为最终设计基线以 reviewing 治理状态归档，可检索且不声称正式 owner attestation。
- AC-D9：Diag 的 Common/runtime/adapter/use-case 边界、安全策略、生命周期、资源预算和硬切换清理形成强制 SSOT。
- AC-D10：所有已识别问题均映射到 C0–C6、target certification、DG 门禁和 owner，不存在未验收过渡态。
- AC-D11：源码 ABI、wire、persist、工具和 target/profile 制品只有一份兼容政策，除受控持久化 migrator 外无兼容实现。
- AC-D12：profile 制品受 signing policy、设备生命周期、boot/update、anti-rollback 和 release receipt 共同约束。

### 17.2 实现验收

- AC-I1：永久 host_linux_x86_64 target 在无 ARM SDK/库环境 clean/build/test。
- AC-I2：SSC305 当前量产构建和关键功能无回归。
- AC-I3：同一 HDI contract suite 覆盖 fake 与所有真实 backend 的可测子集。
- AC-I4：公共头无厂商 SDK 和裸 OS 对象。
- AC-I5：Host sanitizer 无新增有效错误，资源账本归零。
- AC-I6：各平台能力绑定真实身份，UNKNOWN 不进入默认量产路径。
- AC-I7：每个平台 HIL 通过后才声明支持。
- AC-I8：未来 GROS 隔离验证达到全 target 等价后一次硬切换，切换提交不保留 Make 产品规则或对比资产。
- AC-I9：Diag DG-01 至 DG-22 全部有 Host/target 对应证据。
- AC-I10：production 高风险命令不可达，maintenance 只经领域 use case，并具备 permission/guard/confirmation/audit/recovery。
- AC-I11：provider drain 无悬空 handler/context，RTOS static/bounded contract 通过。
- AC-I12：旧 Diag 头、符号、命令、目录、target、alias、shim 和 fallback 在受管范围零命中，只有 tombstone manifest 可记录退役身份。
- AC-I13：architecture/generated/Host/product/RTOS 稳定命令均存在且禁止 skip/unsupported 伪通过。
- AC-I14：production OTA 不能改变 profile，量产生命周期拒绝 factory/product_test，service 仅能受控临时启动并自动回到 production。
- AC-I15：Presubmit、target integration、release certification 三层门禁均生成 identity-bound receipt，基础设施失败和过期隔离不能变绿。

## 18. 风险与控制

| 风险 | 级别 | 控制 |
|---|---|---|
| 把厂商 SDK 逐函数包装成公共 HDI | 高 | 用领域语义和私有 backend ops；review 公共头 |
| Host Fake 通过但真机失败 | 高 | 同 contract suite + HIL；明确 L0–L4 证据等级 |
| x86_64 指针截断到 VS_HANDLE | 高 | generation/index 句柄、静态检查、sanitizer |
| ARM 预编译库误链 Host | 高 | 独立输出与依赖白名单、file/ELF 审计 |
| 硬切换范围大导致集成失败 | 高 | C0–C6 隔离分支 checkpoint、自动门禁、整体提交/制品回滚；不保留运行时双路 |
| RTOS 被迫承载 Linux 全栈 | 高 | profile 化，优先 rtos_control/amp_proxy |
| 能力按 SoC 猜测导致错误默认 | 高 | 三态能力与身份绑定，UNKNOWN fail closed |
| API/APP 继续泄露 pthread/MI 类型 | 中 | header compile test 与依赖规则 |
| GROS 规格不明造成返工 | 中 | 当前只冻结目标模型；正式规格后隔离等价验证并一次硬切换 |
| 大型 HardwareApi 成为新 HAL | 中 | 按消费者拆窄端口，不做公开巨型类 |
| Diag 成为无权限产品后门 | 阻断 | central policy、effect/permission/profile、production catalog、audit |
| format/OTA/motor 绕过领域状态机 | 阻断 | maintenance use case、device guard、二阶段确认 |
| provider 注销与 handler 并发造成 UAF | 高 | invocation lease、generation、drain barrier |
| JSON/固定大 buffer 阻断 RTOS | 高 | codec seam、bounded writer、target limits manifest |
| compat/alias/shim 形成第二调用链 | 阻断 | 目标产物禁止兼容层，retired-residue blocking gate，整体制品回滚 |
| 量产设备装载 factory/product_test 或普通 OTA 改 profile | 阻断 | 独立签名策略、设备生命周期、双阶段 update/boot 校验、anti-rollback HIL |
| HIL/基础设施错误或隔离测试被当作通过 | 阻断 | 三层门禁、固定重试、隔离 expiry、identity-bound receipt |

## 19. 可恢复执行规则

- goal_statement：保持当前 Make 构建权威，形成可审查、可归档、可硬切换实施且无旧路径残留的 HDI/HAL/Diag 跨平台与 x86_64 Host 方案。
- completion_claim：最终设计基线、独立 review、验证证据和 reviewing archive candidate 均完成；不包含代码实现、实板 certification 和正式 owner attestation。
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
- Diag 独立 SSOT 与总体方案必须双向关联；command、policy、limits、target/source-set、retired identifiers 和测试均作为机械一致性资产治理。
- 归档 source_from 使用稳定描述，不写临时路径或会话 ID。
- 若平台/BSP 事实更新，先更新 capability identity 和 evidence，再复审本决策。

## 22. 最终决策状态

本方案已通过硬切换与零残留独立 review。归档状态仍保持 reviewing，等待 team-core、security、product/platform/release/build owner 评审；该 review 不为未实现的 Host、SSU9383CM、RDK X5、RTOS、Diag runtime 或 GROS 功能背书。
