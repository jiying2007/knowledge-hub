---
doc_type: architecture-decision-candidate
created: 2026-08-13
updated: 2026-08-13
platforms:
- SSC305
- SSU9383CM
- RDK X5
- Linux x86_64 Host
- future RTOS
build_policy: current product build rules remain unchanged
id: pcr02-hdi-hal-cross-platform-host-development-architecture-20260813
title: HDI/HAL 跨平台与 Host 开发测试架构决策候选
kind: decision
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/decisions/hdi-hal-cross-platform-host-development-architecture-20260813.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: design-review
  from: reviewed repository architecture document and local static evidence
  source_sha256: 0ab353276771753fad9ec5d42da3c7b9427557a83e4de5ac9a2d71b01fc9e1bd
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
- decision-candidate
validation_refs:
- projects/xcrz-sigmastar-demo/decisions/hdi-hal-cross-platform-host-development-architecture-20260813.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/decisions/hdi-hal-cross-platform-host-development-architecture-20260813.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-13'
updated_at: '2026-08-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-13'
manual_validation_pending: true
summary_zh: 在保持当前编译规则不变的前提下，定义 SSC305、SSU9383CM、RDK X5、x86_64 Host 与 future RTOS 的 HDI/HAL 分层、能力模型、迁移门禁、验收和回滚。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- HDI/HAL 跨平台与 Host 开发测试架构决策候选
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

该决策目前是 reviewing candidate，只代表架构方案完成自审，不代表平台实现、实板验证、负责人批准或发布完成。

## 2. 目标与非目标

### 2.1 目标

- 在 SSC305、SSU9383CM、RDK X5 和后续 RTOS 之间保持 API/APP 的主体代码稳定。
- 把 SigmaStar MI、RDK X5 SDK、Linux/POSIX、RTOS 和板级差异收敛到明确边界。
- 让 x86_64 PC 能覆盖高频逻辑开发、故障注入、资源泄漏和并发契约测试。
- 保留当前产品构建路径，降低架构迁移对在研版本的扰动。
- 为未来 GROS 提供可直接映射的 target/profile/backend/capability 模型。
- 给每个迁移包配置独立验收、停止条件和回滚点。

### 2.2 非目标

- 不在本阶段实现三个 SoC 后端、RTOS 端或 GROS 构建描述。
- 不承诺 PC 能执行 ARM 专有动态库、真实 ISP 调优、硬编解码性能或硬件在环验证。
- 不把 HAL 设计成公开的“大而全”硬件类，也不要求运行时插件化。
- 不立即重排现有源码目录或改变安装包、量产和 OTA 流程。
- 不把 Host Fake 的通过等价为真机通过。

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

### 3.2 本方案决策

- 公共依赖方向固定为 APP → API → HDI → internal HAL backend → OS/SDK/driver。
- APP 仅允许在 composition root 和只读诊断入口直接访问 HDI；普通业务不得绕过 API。
- OSAL 只覆盖内存、线程、同步、时间、原子和基础日志等最小机制；文件、进程、网络、动态加载归入可选平台服务。
- 后端优先静态链接与启动时注入，不把 dlopen 作为跨 Linux/RTOS 的基础要求。
- 平台选择由构建组合决定，运行时能力由 capability query 决定；不得仅依据 SoC 名称猜能力。
- Host Fake 在 HDI 边界实现同一契约；APP 侧另通过窄业务端口隔离现有大型 HardwareApi 类。

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

### 4.1 Common

Common 层只包含固定宽度类型、无厂商含义的数据结构、序列化、容器和可移植算法：

- 线协议和持久化格式显式定义字节序、版本、长度和校验，不直接写入 C/C++ 原始结构体。
- 不暴露 long、size_t、指针大小和编译器 padding。
- 句柄、对象 ID 和跨进程 ID 不复用指针。
- 公共结构新增字段采用 size/version 或显式 TLV 兼容策略。

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

### 4.3 HDI

HDI 面向“业务需要的硬件语义”，不面向厂商函数的逐项包装：

- 视频域表达 camera stream、frame、encoder channel 和 graph，而不是 MI_SYS/MI_VIF/MI_VPE 的直接镜像。
- 音频域表达 input/output stream、format、buffer 和 clock，而不是厂商设备号的裸露组合。
- 存储、设备信息、电源和看门狗按相同方式形成窄域接口。
- 所有调用都定义前置状态、并发规则、超时、所有权、失败后的可恢复状态。

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

### 4.5 API

API 是跨平台领域服务层：

- 接收 desired state、业务参数和资源策略；
- 把目标状态编译为 HDI 操作计划；
- 管理并发请求、幂等、重试、补偿和状态收敛；
- 不包含 GPIO、sensor bus、MI/RDK SDK 类型或 RTOS task 类型；
- 不公开 OS 线程对象；
- 对不支持能力返回稳定领域错误，而不是静默降级。

### 4.6 APP

APP 只做产品编排、UI/命令映射、业务状态机和策略：

- 普通业务通过 API 使用设备能力；
- composition root 负责选择 profile/backend、构造依赖和注册诊断；
- 只读诊断可直接查询 HDI capability 和 health；
- 现有 HardwareApi 不直接被命名为 HAL，后续拆为 CameraPort、AudioPort、StoragePort、PowerPort、DeviceInfoPort 等窄接口；
- DvrCommandHandler 等消费者逐个改为依赖窄端口或领域 API，而不是依赖整个 HardwareApi。

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
- source-set gate：Host target 不得收集 vendor backend 源码或 ARM-only 库；
- symbol/dependency audit：Host 产物检查 ELF 架构和动态依赖，目标产物检查误链 Host 库；
- contract-version gate：ops ABI、board manifest、fixture 和 RPC 版本不匹配时 fail closed；
- exception budget：例外只允许 composition root、只读诊断和有到期日的兼容 shim。

这些门禁先在 sidecar/CI report-only 运行，消除历史存量后再升级为 blocking，避免一次性阻断当前产品构建。

## 13. 未来源码形态

以下只是目标布局，不在本方案评审通过时自动移动文件：

    modules/
      common/
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
    products/
      pcr02/
      product_profiles/
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

建议组合：

| target | 关键选择 |
|---|---|
| host_linux_x86_64 | os=linux, arch=x86_64, profile=host_sim, backend=host_fake |
| ssc305_linux | os=linux, arch=armv7, profile=linux_full, backend=ssc305_mi |
| ssu9383cm_linux | os=linux, arch=目标工具链实际值, profile=linux_full, backend=ssu9383cm_mi |
| rdk_x5_linux | os=linux, arch=aarch64, profile=linux_full, backend=rdk_x5 |
| rtos_control | os=项目 RTOS, arch=目标核, profile=rtos_control, backend=rtos_native/amp_proxy |

GROS 迁移门禁：

1. owner 提供并冻结正式规格；
2. 当前 Make 与 GROS 在同一平台生成等价 source/dependency/define/link map；
3. 关键产物做 ABI、功能和包内容对比；
4. 双轨期内量产仍以当前批准路径为准；
5. 单平台验证通过后逐个平台切换；
6. 任何平台失败可退回旧构建，不回退 HDI contract。

## 15. 分阶段迁移计划

### P0：基线与契约冻结

范围：

- 保存当前平台、SDK、板型、sensor 和构建命令基线；
- 记录公共头泄漏、厂商类型、直接 HDI/OS 调用和 ARM-only 依赖；
- 冻结第一版 error/lifecycle/handle/capability 契约。

验收：

- 有可复查的基线清单；
- owner 确认首个 SSC305 垂直切片；
- 不改产品构建。

回滚：纯文档和清单，无运行时影响。

### P1：sidecar Host 纯逻辑测试

范围：

- 新建 tests/host；
- 先纳入无 MI、无 pthread 公开泄漏、无 ARM 库的纯逻辑；
- 引入 sanitizer 和 deterministic fixture。

验收：

- host_linux_x86_64 可独立 clean/build/test；
- 与产品构建输出隔离；
- 当前 SSC305 build 文件无差异。

回滚：移除 sidecar target，不影响产品。

### P2：公共头与 OSAL seam

范围：

- 把 pthread/Linux 类型移出 API/HDI 公共头；
- 建立 osal_core 接口和 POSIX 实现；
- 文件、进程、网络拆为可选平台服务；
- 加 C11/C++17 header compile test。

验收：

- 公共头可在 x86_64 无厂商 SDK 编译；
- POSIX 实现对现有 Linux 行为回归；
- ABI 变化经过显式清单审批。

回滚：兼容 shim 保留一个发布周期，按域恢复旧入口。

### P3：HDI facade 与 backend ops

范围：

- 先选 system/device 或 audio 的小域建立 facade；
- 把 SSC305 当前实现包入 ssc305_mi backend；
- 实现同契约 host_fake；
- 统一 error、capability、lifecycle。

验收：

- fake 与 SSC305 可测子集通过同一 contract suite；
- API 不包含厂商头；
- 资源账本在正常和故障路径归零。

回滚：保留旧 HDI adapter，由 feature 控制单域切换。

### P4：视频垂直切片

范围：

- 建立 frame/lease、graph compiler、operation plan；
- SSC305 backend 执行真实节点；
- Host 使用 synthetic frame 和 packet fixture。

验收：

- Host 覆盖 graph diff、补偿、背压和迟到事件；
- SSC305 HIL 覆盖 capture/start/stop/release；
- 性能和图像质量只在 HIL 判定。

回滚：视频域独立 feature 回到旧路径。

### P5：API/APP 窄端口

范围：

- 拆 CameraPort、AudioPort、StoragePort、PowerPort、DeviceInfoPort；
- 逐个迁移 DvrCommandHandler 等消费者；
- 建立 API + fake HDI + APP 工作流测试。

验收：

- 迁移组件不依赖大型 HardwareApi；
- 普通 APP 业务无直接 HDI 调用；
- composition root/只读诊断例外有静态白名单。

回滚：按消费者保留旧适配器。

### P6：SSU9383CM 后端

范围：

- 冻结 SDK/板型/核间拓扑；
- 复用公共 SigmaStar 辅助代码，但保持 backend 独立；
- 实现能力探测和平台专项 HIL。

验收：

- 公共 contract suite 通过；
- 不支持项明确返回 UNSUPPORTED；
- RISC-V/RTOS 路径若未验证保持 UNKNOWN。

回滚：平台 target 不发布，不影响 SSC305。

### P7：RDK X5 后端

范围：

- 冻结项目 BSP 和批准硬件；
- 映射 X5 camera/media/system API 到 HDI；
- 建立 aarch64 cross build 与实板 HIL。

验收：

- contract suite + X5 专项测试通过；
- 不复用 ARMv7 预编译库；
- capability identity 绑定 X5 BSP/板/sensor。

回滚：X5 target 独立撤回。

### P8：RTOS profile

范围：

- owner 先选择 rtos_control 或 amp_proxy；
- 实现 bounded OSAL、静态 backend、RPC/共享内存契约；

验收：

- RTOS 资源预算、超时、peer reset、cache 规则通过实机验证；
- 公共控制面 contract 的可测子集通过；
- Linux/RTOS peer reset 后资源和 generation 能收敛。

回滚：RTOS profile 可不随首版发布，不影响各 Linux target。

### P9：GROS 双轨迁移

前置条件：

- P0–P7 的 target/source/dependency 边界已稳定；
- owner 提供并冻结 GROS 正式规格；
- RTOS 是否进入同批迁移由 P8 结果单独决定。

范围：

- 先映射 Host target，再迁移一个已稳定的 Linux target；
- 生成并对比 source/dependency/define/link map；
- 按平台逐一双轨验证，不同时改变 HDI contract 或目录布局。

验收：

- GROS 与旧构建的关键产物 ABI、功能和包内容等价；
- 所有 target 使用隔离的 toolchain、SDK identity 和 output namespace；
- 每个平台可独立退回旧构建。

回滚：只回退构建入口，不回退已验证的 HDI contract 和 backend 边界。

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

### 17.2 后续实现验收

- AC-I1：x86_64 sidecar 在无 ARM SDK/库环境 clean/build/test。
- AC-I2：SSC305 当前量产构建和关键功能无回归。
- AC-I3：同一 HDI contract suite 覆盖 fake 与所有真实 backend 的可测子集。
- AC-I4：公共头无厂商 SDK 和裸 OS 对象。
- AC-I5：Host sanitizer 无新增有效错误，资源账本归零。
- AC-I6：各平台能力绑定真实身份，UNKNOWN 不进入默认量产路径。
- AC-I7：每个平台 HIL 通过后才声明支持。
- AC-I8：GROS 双轨等价验证通过后才切换量产构建。

## 18. 风险与控制

| 风险 | 级别 | 控制 |
|---|---|---|
| 把厂商 SDK 逐函数包装成公共 HDI | 高 | 用领域语义和私有 backend ops；review 公共头 |
| Host Fake 通过但真机失败 | 高 | 同 contract suite + HIL；明确 L0–L4 证据等级 |
| x86_64 指针截断到 VS_HANDLE | 高 | generation/index 句柄、静态检查、sanitizer |
| ARM 预编译库误链 Host | 高 | 独立输出与依赖白名单、file/ELF 审计 |
| 大规模目录/构建/接口同时迁移 | 高 | P0–P9 小步切换、单域 feature 回滚 |
| RTOS 被迫承载 Linux 全栈 | 高 | profile 化，优先 rtos_control/amp_proxy |
| 能力按 SoC 猜测导致错误默认 | 高 | 三态能力与身份绑定，UNKNOWN fail closed |
| API/APP 继续泄露 pthread/MI 类型 | 中 | header compile test 与依赖规则 |
| GROS 规格不明造成返工 | 中 | 只冻结目标模型，正式 DSL 后双轨迁移 |
| 大型 HardwareApi 成为新 HAL | 中 | 按消费者拆窄端口，不做公开巨型类 |

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
- modules/hdi/src/hdi_hw/hdi_sys.c：直接包含 mi_sys.h。
- modules/api/src/api_container/api_list.c：直接使用 VSHDIOS_*。
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
- 归档 source_from 使用稳定描述，不写临时路径或会话 ID。
- 若平台/BSP 事实更新，先更新 capability identity 和 evidence，再复审本决策。

## 22. 最终决策状态

本方案已通过本轮分离式架构 review，归档状态应保持 reviewing，等待 team-core owner 评审。该 review 仅针对“方案是否足以指导后续实施并安全归档”作出裁决；它不为未实现的 Host、SSU9383CM、RDK X5、RTOS 或 GROS 功能背书。
