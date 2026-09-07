---
related:
- projects/xcrz-sigmastar-demo/README.md
- projects/xcrz-sigmastar-demo/decisions/hdi-hal-cross-platform-host-development-architecture-20260813-v4.md
- projects/xcrz-sigmastar-demo/decisions/osal-platform-hdi-final-boundary-20260817.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
decision_status: pending-owner-review
decision_date: null
supersedes_candidate_scope:
- pcr02-hdi-hal-cross-platform-host-development-architecture-20260813-v4/build-policy
- pcr02-hdi-hal-cross-platform-host-development-architecture-20260813-v4/gros-future-boundary
id: pcr02-gros-single-track-cross-platform-build-hard-cut-20260830-v1
title: GROS 单轨跨平台构建硬切换最终方案候选 v1
kind: decision
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/decisions/gros-single-track-cross-platform-build-hard-cut-20260830-v1.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: manual
  from: current user-directed design review plus repository and dev/gros static evidence
  source_sha256: 7ce01cdbf3966fc66fbc75c3898372a31cc330dbd363f561e64b2c16eadeb1ed
review_after: '2026-09-30'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- gros
- hard-cut
- build-system
- ninja
- ssc305
- rdk-x5
- host-test
- thirdparty
- artifact-lifecycle
validation_refs:
- projects/xcrz-sigmastar-demo/decisions/gros-single-track-cross-platform-build-hard-cut-20260830-v1.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/decisions/gros-single-track-cross-platform-build-hard-cut-20260830-v1.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-30'
updated_at: '2026-08-30'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-30'
manual_validation_pending: true
summary_zh: 冻结 xcrz_sigmastar_demo 应用仓内 GROS 单轨构建、Ninja 固定生成器、SSC305/RDK X5/Host 统一 target/source-set、第三方 receipt、原子 bundle
  和 SDK 单向制品交接；不保留应用 Make/GROS 双轨。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- GROS 单轨跨平台构建硬切换最终方案候选 v1
---

# GROS 单轨跨平台构建硬切换最终方案候选 v1

> 2026-09-05 用户纠偏与实施更新：本文后续历史段落中的 Python resolver / JSON source-set 构建权威已废止。当前已落实模块与应用自有 CMakeLists.txt、原生 toolchain/imported targets、CTest；第一方 Make 及 Python/JSON 构建图共153个控制文件已整体移除并通过原生 hard-cut 检查。状态继续 reviewing，不自动转为产品批准。
>
> 新鲜证据：Host 74/74（包含显式启用的SSC305诊断白盒），原20文件coverage为83.13%，三inline头完整计入；原生SSC305产测/Sensor Test/OTA/app_test与RDK X5音视频程序已交叉链接，Host CMD/CLI/Daemon独立链接。PCR02主程序仍缺IoT，完整HIL/许可证/签名认证未完成。当前使用说明与证据为 workspace://xcrz-sigmastar-demo/GROS.md 和 workspace://xcrz-sigmastar-demo/docs/changes/gros-single-track-hard-cut/NATIVE-CMAKE-PLAN.md。历史百分比与contract hash不代表当前身份。

## 1. 决策摘要

`xcrz_sigmastar_demo` 应用仓采用 GROS 单轨构建。应用仓根 `./gros` 是唯一用户入口，GROS/CMake 是唯一应用源码编译和产品链接权威，Ninja 是固定底层生成器。SDK 根目录只负责 SDK、kernel、image、OTA 和发布，不进入应用目录执行编译。

硬切后不保留应用 Make 产品图、Make/GROS 双轨、`crossbuild.py` 产品编译路径、递归源码发现、source 到历史 prebuilt 的自动回退或旧 target alias。现有跨平台 target/source-set、第三方源码构建、ELF 审计、runtime closure 和 receipt 能力迁入 GROS。

本候选只 supersede `hdi-hal-cross-platform-host-development-architecture-20260813-v4` 中“当前 Make 为唯一构建权威”和“GROS 仅作为未来映射模型”的范围。HDI/HAL/API/APP/Diag 的稳定接口、依赖方向、profile 制品隔离、Host 门禁和 HIL 边界继续沿用 v4，不由本候选重写。

当前状态是 `reviewing`：设计已收敛，代码、owner attestation、RDK X5 HIL 和发布认证尚未完成。

## 2. 需求分类与优先级

- 需求类型：架构增强 + 构建系统硬切换 + 配置迁移。
- 优先级：P1。
- 判定依据：它决定 SSC305、RDK X5、Host、HDI/API/APP/Sensor 和第三方的唯一构建权威；若继续多套产品图，跨平台结果、依赖资格和发布回执会持续漂移。
- 需求来源：当前用户明确要求应用目录直接编译、使用 GROS、取消 Make/GROS 双图并归档最终方案。
- 责任 owner：team-core；实现还需要 GROS、平台、产品、发布和 HIL owner 签收。

## 3. 目标

1. 在应用目录直接执行 doctor、configure、build、test、bundle、verify 和 install。
2. 用一套 target/source-set 配置组合 Host、SSC305 和 RDK X5。
3. 保证每个 target 只选择一个 backend、OSAL、board、profile、toolchain 和 third-party profile。
4. HDI、API、APP、Sensor 使用同一公共契约，平台差异只存在于明确 adapter/backend。
5. 第三方从源码或批准供应输入生成 target receipt 和可重定位 sysroot，禁止错误架构回退。
6. 最终产品生成 runtime closure、资源清单、SBOM、checksums 和 identity-bound receipt。
7. GROS bundle 通过单向 artifact contract 交给 SDK image/OTA 流程；SDK 不重新编译应用。
8. 通过内容寻址缓存、构建锁、staging verify 和原子替换支持长期维护和并发构建。

## 4. 非目标

- 不修改 SDK 根 `build.sh` 来支持应用编译。
- 不保留 Make/GROS 双构建图或 Make fallback。
- 不让 GROS 隐式 fetch、pull、reset、checkout、clean 或访问发布凭据。
- 不让 Host 代替 SSC305/RDK X5 HIL。
- 不在 board 静态配置中保存 LINK/HIL/certification 动态状态。
- 不自动删除独立模块仓为其他产品保留的本地构建文件；但 GROS 产品图不得引用它们。
- 不把设计候选自动提升为 active、owner 决策或产品 ready。

## 5. 适用范围

### 5.1 产品与平台

- 产品：PCR02 / `xcrz_sigmastar_demo`。
- SoC/板：SSC305 PCR02、RDK X5 EVB v2.0；后续可扩展 SSU9383CM 和 RTOS。
- OS/runtime：Linux ARMv7、Linux AArch64、Linux x86_64 Host。
- 层级：设备应用、模块、第三方、Host 测试、产品 bundle、诊断/产测制品隔离。
- Boot/image/OTA：只定义应用 artifact import contract，不由 GROS 直接生成系统 image/OTA。

### 5.2 现有入口

- GROS 原型：`origin/dev/gros@78738fc92e34db4d90c05cb453ae1760112f33fb`。
- 当前跨平台实现：`xcrz_sigmastar_demo_rel` 的 target/source-set、RDK X5 media contract、third-party framework 和 receipts。
- 旧 GROS 分支只复用结构思想，不直接合并；它相对当前 `dev/pcr02` 有 1 个独有提交但少 639 个后续提交。

## 6. 领域模型

### 6.1 术语和实体

| 实体 | 定义 | 权威边界 |
|---|---|---|
| Target | 一个可构建产品身份 | `config/targets` |
| Source Set | 显式源码、公开/私有 include、依赖和约束 | `config/source_sets` |
| Feature Set | 功能到 source/dependency/resource/HIL 的选择 | `config/feature_sets` |
| Resource Set | target/profile 可安装的资源和程序集合 | `config/resource_sets` |
| Board Manifest | 静态硬件连接、revision、设备和校准路径 | `config/boards` |
| Module Lock | 聚合仓和独立模块仓 remote/SHA/tree hash | `gros.lock.json` |
| SDK Snapshot | SDK 配置、include、vendor 库和工具链实际身份 | build contract evidence |
| Dependency Receipt | 第三方输入、编译器、flags 和 stage tree hash | `3rdparty/out` |
| Build Contract | target 到全部输入的规范化 hash | `out/gros/.../.gros-build-identity.json` |
| Artifact Bundle | 已安装、已验证、可导入 SDK 的应用制品 | `release/<target>/bundle` |
| Build Receipt | 本次 source/build/link/runtime 观测 | bundle 内 |
| Certification Receipt | HIL、性能、安全、发布和 owner 证据 | 独立认证资产 |

### 6.2 构建状态机

```text
UNRESOLVED
  -> DOCTOR_PASS
  -> RESOLVED
  -> DEPENDENCIES_VERIFIED
  -> CONFIGURED
  -> BUILT
  -> TESTED
  -> STAGED
  -> BUNDLE_VERIFIED
  -> PUBLISHED
```

任一步失败进入 `FAILED`，不得生成完成态 receipt，不得替换旧 bundle。恢复只能从同一 build contract 重跑或创建新 contract。

### 6.3 产品成熟度状态

```text
bootstrap -> source_ready -> link_verified -> hil_verified -> certified -> released
```

状态来自 receipt/certification evidence，不写入 board 静态事实。RDK X5 当前最多只能声明 `link_verified`。

### 6.4 数据流

```text
target/source-set/feature/resource/module-lock
  + SDK/toolchain/dependency receipts
  -> resolved build contract
  -> GROS/CMake/Ninja graph
  -> module libraries + product ELF + tests
  -> runtime/resource/SBOM bundle
  -> build receipt readback
  -> atomic release bundle
  -> SDK image/OTA import
```

## 7. 决策选项

| 选项 | 影响范围 | 成本 | 风险 | 结论 |
|---|---|---|---|---|
| 保留当前 Make/crossbuild | 最小迁移 | 低 | 无法满足 GROS 单轨，长期多权威 | 拒绝 |
| Make 与 GROS 双轨 | 可逐项对照 | 高 | 配置漂移、fallback、发布不确定 | 拒绝 |
| GROS 单轨硬切 | 应用构建全面迁移 | 高 | 一次性迁移风险，需要强门禁 | 选择 |

## 8. 最终构建权威与入口

应用仓根提供 `./gros` 薄入口，逻辑位于 `tools/codex_assets/gros.py`。GROS 固定使用 Ninja，不允许调用者选择 generator，也不允许调用者同时指定与 target 冲突的 toolchain file。

稳定命令：

```text
./gros doctor --target <id>
./gros explain --target <id>
./gros configure --target <id>
./gros build --target <id> --jobs <n>
./gros test --target <id>
./gros bundle --target <id>
./gros verify --target <id>
./gros all --target <id> --jobs <n>
./gros clean --target <id> [--contract <sha>]
```

明确不提供 sync/pull/reset/fallback/use-make/legacy-build 命令。源码同步和 checkout 是构建外的显式治理动作。

## 9. 配置 SSOT

仅保留：

```text
config/targets
config/source_sets
config/feature_sets
config/resource_sets
config/boards
config/diag
config/signing_policies
config/release_policies
```

迁移后删除 `config/cross_build`。声明式配置只生成 build 目录中的 `resolved-target.json` 和安全编码的 `resolved-target.cmake`，不生成 Make 文件，不写回源码仓。

Target 必须声明 product/target/os/arch/soc/board/profile/backend/osal/feature/toolchain/sdk/thirdparty/output/diag/source-set/signing/release/anti-rollback/certification requirements。Production target 不允许环境变量追加 source、feature、library 或 command。

Source-set 必须显式声明 sources、public headers、public/private include、dependencies、definitions、target/feature constraints、expected symbols 和 forbidden dependencies。禁止 GLOB/GLOB_RECURSE、递归 include 和自动 source-to-prebuilt fallback。

## 10. 模块与依赖 DAG

模块 provenance 清单只记录 module id、path、remote、branch、commit、owner 和 required；源码选择只来自 source-set。Production 构建必须校验聚合仓和所有独立模块仓的 remote、SHA、dirty 状态和 source tree hash。

必须源码构建 common、proto、osal、platform、hdi、api、app、sensor。Sensor 不得继续定义为 prebuilt。

依赖方向：

```text
APP composition -> Sensor -> API -> HDI facade -> selected backend -> OSAL/Platform -> Common
```

configure 阶段必须检查依赖环。禁止用 blanket `--start-group` 掩盖 APP/API/HDI/Sensor 环；只有精确 allowlist 的 vendor 静态库组可以使用 linker group。

## 11. 工具链与 SDK 身份

`target_id` 唯一决定 generator、toolchain、SDK identity、board、arch、backend 和 third-party profile。调用者提供的 SDK/toolchain root 只是定位参数，实际内容必须匹配 target。

Build contract 绑定 compiler binary hash/version/sysroot、SDK release config/manifest commit、实际使用 include tree hash、实际链接 vendor 库 hash/BuildID。交叉 toolchain 使用 `CMAKE_FIND_ROOT_PATH_MODE_LIBRARY/INCLUDE/PACKAGE=ONLY`，PROGRAM=NEVER，防止 Host 污染。

## 12. 第三方与不可变缓存

`3rdparty/build` 保留为 GROS dependency producer：source/vendor input -> stage -> ELF/ar audit -> per-library receipt -> relocatable sysroot -> exact imported targets。它不构成第二个产品构建权威。

禁止全局 link directories、`@glob`、整个目录 `.so`、错误架构 fallback。audio DSP、Agora、AISpeech qualification 继续独立 fail-closed。

缓存以完整 dependency contract 为 key，不同 arch/target/flags 不共享可写 stage。相同 contract 的 cache 只读复用，receipt readback 失败立即拒绝。Host/ARMv7/AArch64 输出必须隔离。

## 13. 生成器

Host generator 与 target runtime 分离。Proto receipt 绑定 protoc binary hash/version、proto inputs、generated outputs 和 target protobuf runtime identity。生成物进入 `out/gros/work/<target>/<contract>/generated`，普通构建不覆盖源码仓。

## 14. 路径、配置和命令安全

Target/module/profile ID 只允许安全字符；拒绝分号、换行、NUL 和控制字符。所有 repo/SDK/toolchain/sysroot/output 路径必须 resolve 后重新检查批准 root containment，覆盖 `..` 和 symlink escape 负路径。

生成 CMake 使用专用安全编码器，不拼接原始 CMake expression，不允许配置注入 generator expression。外部命令使用 argv 数组，不拼 shell 字符串。构建不访问发布密钥、NAS 或网络。

## 15. Build contract、并发和原子发布

Build contract 是 target/source-set/feature/resource/module lock/toolchain/SDK/dependency/proto 的规范化 SHA-256。工作目录必须保存 identity 文件；复用目录时 identity 不一致直接拒绝。

输出布局：

```text
out/gros/work/<target>/<contract>
out/gros/cache/<contract>
out/gros/locks/<contract>.lock
out/gros/reports/<target>/<contract>
```

相同 contract 只允许一个 builder，不同 contract 可并行。Release 使用 target lock，先写 staging、完成 bundle verify 和 receipt readback 后原子替换；失败保留旧 bundle。Clean 只删除精确解析的 target/contract 路径。

## 16. 编译和链接规则

GROS 使用 target-scoped `target_sources/include_directories/compile_definitions/compile_options/link_libraries`。禁止全局 include/link/definition、全局 `-fpermissive` 和未批准 RPATH。公共基线是 C11/C++17；警告策略按 source-set 管理，生产 target 禁止 `-fpermissive`。

静态 archive 做确定性规范化。相同输入的 clean build 必须产生一致 contract identity、archive、runtime manifest 和 receipt；使用受控 `SOURCE_DATE_EPOCH`，不把 whoami、当前墙钟或非受控绝对路径编入核心对象。

## 17. 资源、诊断与运行时 bundle

Target 显式选择 resource sets。大型资源目录可以声明目录 root，但必须有 include/exclude、tree hash 和 destination。Production bundle 不得包含 product-test、factory、未批准 cmd server、调试模型或高风险维护工具。

Runtime bundle 只根据最终 ELF 的 DT_NEEDED/SONAME/RPATH/RUNPATH 生成闭包，记录 arch、BuildID、SHA-256、owner 和 parent。检测同 SONAME 不同 hash、SDK/third-party 重复库、Host/ARM 混用、未声明系统库、绝对路径泄漏和 license/notice 缺失。

## 18. 应用到 SDK 的单向制品交接

GROS 原子发布：

```text
release/<target>/bundle/
  bin/
  lib/
  resource/
  artifact-manifest.json
  runtime-manifest.json
  build-receipt.json
  source-lock.json
  sbom.json
  checksums.sha256
```

SDK image/OTA 流程只能导入已验证 bundle，核对 schema、target/product/board/profile、certification state、receipt、checksums 和 layout version。SDK 不进入应用源码目录，不执行应用 CMake/Ninja，不修改 bundle，不用旧 bin 覆盖。

## 19. CI、权限和发布边界

普通 CI 只使用无密钥 target，执行 schema、Host、交叉 build/link 和 receipt verify。Untrusted branch 不接收签名、NAS 或发布凭据。Release job 必须在受信任 ref、owner approval、fresh receipt、HIL/certification gate 后运行，并且只消费已验证 bundle，不重新构建。

构建、认证、签名和发布是四个独立状态，任何 CI 通过都不能自动提升为 certified/released。

## 20. 硬切换迁移

1. 从当前最新产品基线创建新的 GROS 集成分支；不直接 merge 落后 639 提交的旧 dev/gros。
2. 切换前冻结 SSC305 ELF/receipt、RDK X5 contract/runtime/receipt、Host 测试、ABI/symbol/DT_NEEDED 和 HIL 边界；冻结的是证据，不是第二构建图。
3. 分支内完成 `./gros`、Ninja、统一 schema、module lock、Host/SSC/X5 toolchains、third-party、proto、DAG、product link、runtime/resource/SBOM、atomic bundle、artifact import 和 gates。
4. 同时删除应用根 Make 产品入口、聚合仓 build/pcr02 mk、`config/cross_build`、`crossbuild.py` 产品编译逻辑、旧 alias/fallback。独立模块仓服务外部 consumer 的 Make 文件不越权删除，但 GROS 产品图不得调用。
5. 只对比冻结旧证据与 GROS 新结果，不生成 Make/GROS 双图。
6. 全门禁和 owner review 通过后整体合入；失败时整体 revert hard-cut 变更集或使用上一版发布制品，不恢复局部 shim。

## 21. 需求包与 Done-when

| ID | 需求包 | Done-when | Required evidence | Artifact paths | Owner |
|---|---|---|---|---|---|
| RQ-01 | GROS CLI/工具版本 | 应用目录 doctor/explain/configure 可用，固定 Ninja | CLI contract、tool negative tests | `gros`, `tools/codex_assets/gros.py` | GROS owner |
| RQ-02 | Schema/resolution | 一套 target/source-set/feature/resource 通过 schema，错误输入 fail | schema tests、resolved contract hash | `config/*`, `out/gros/.../generated` | team-core |
| RQ-03 | Source/module lock | 所有独立仓 remote/SHA/tree 可读回，production dirty 拒绝 | lock/readback/dirty tests | `gros.lock.json` | module owners |
| RQ-04 | Host target | 无 ARM SDK clean build/test/sanitizer/fuzz 通过 | Host reports、ELF dependency audit | `out/gros/...host...` | team-core |
| RQ-05 | SSC305 target | GROS 产品 ELF、ABI、关键行为不退化 | build receipt、symbol/DT_NEEDED、HIL | `release/ssc305...` | SSC platform owner |
| RQ-06 | RDK X5 target | APP/Sensor/API/HDI video/audio source/link contract 通过 | SDK identity、17 integrations、runtime receipt | `release/rdk_x5...` | X5 platform owner |
| RQ-07 | Third-party | ARMv7/AArch64/Host receipts 和 sysroot 可重定位，无混架构 | per-lib receipts、tree hash、negative audit | `3rdparty/out` | dependency owner |
| RQ-08 | Generators | Host tools和target runtime identity 分离且可复现 | generator/input/output receipts | `out/gros/.../generated` | proto owner |
| RQ-09 | Bundle/runtime/resources | 只打包显式资源和 DT_NEEDED 闭包 | runtime/resource/SBOM/checksums | `release/<target>/bundle` | product owner |
| RQ-10 | Atomic/concurrent/cache | 并发不互相覆盖，失败保留旧 bundle，cache contract 精确 | concurrency/interruption/cache tests | `out/gros/locks/cache`, `release` | GROS owner |
| RQ-11 | SDK import/release | SDK 只导入 verify bundle，release job 不重建 | import contract、release negative tests | bundle artifact manifest | release owner |
| RQ-12 | Hard-cut/zero residue | 应用产品 Make、crossbuild compile、alias/fallback 零命中 | inventory scan、whole-branch review | cutover report/receipt | team-core |

## 22. 验收标准

- AC-01：应用 clean checkout 在应用目录直接构建，不调用 SDK 根 build.sh。
- AC-02：Ninja 是唯一 generator；工具版本不满足时 doctor 失败。
- AC-03：无 GLOB/GLOB_RECURSE/递归 PUBLIC include。
- AC-04：每个 source 来自显式 source-set，每个 target 只有一个 backend/OSAL/profile。
- AC-05：Host 不含 ARM/vendor backend；SSC/X5 不含 fake/错误 backend。
- AC-06：模块依赖 DAG 无环；APP/API/HDI/Sensor 不用 blanket start-group。
- AC-07：路径逃逸、分号/换行注入、错误 toolchain、SDK 内容漂移均 fail-closed。
- AC-08：第三方架构、receipt、sysroot tree 和 runtime closure 全部通过；外部供应缺失不 fallback。
- AC-09：Host 全量门禁、SSC 产品/HIL、X5 media link/HIL 分层有新鲜证据。
- AC-10：相同输入双 clean build contract/archives/runtime/receipt 可复现。
- AC-11：并发、interrupt、cache poisoning 和 atomic replace 负测试通过。
- AC-12：Production program/resource 集合不含 factory/product-test/未批准维护工具。
- AC-13：SDK 只导入 bundle，不重新编译应用；artifact import readback 通过。
- AC-14：Build、certification、signing、release 状态不可相互冒充。
- AC-15：旧应用 Make 产品图、`config/cross_build`、crossbuild compile、alias/shim/fallback 零残留。

## 23. Blocker policy

以下任一情况阻止对应 target 或 release，不产生兼容默认值：schema/target/source-set 缺失；模块 remote/SHA/tree 漂移；production dirty；SDK/toolchain identity 漂移；build dir identity 不匹配；错误 backend/OSAL/arch；依赖 receipt 或 runtime closure 失败；生成器/runtime 不匹配；资源越权；bundle readback 失败；HIL 缺失却申请 certification；UNKNOWN capability 申请 production release；owner/release gate 未签收。

## 24. Required Evidence 与 Artifact Paths

必需证据：schema/negative tests、resolved contract、source lock、compiler/SDK snapshot、third-party receipts、compile/link map、ELF/symbol/DT_NEEDED、Host reports、SSC/X5 receipts、runtime/resource/SBOM/checksums、并发/中断/缓存测试、artifact import、HIL/certification、zero-residue scan、owner review。

规范工件路径：

```text
out/gros/work/<target>/<contract>
out/gros/cache/<contract>
out/gros/locks/<contract>.lock
out/gros/reports/<target>/<contract>
release/<target>/bundle
```

## 25. 证据

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk git fetch origin dev/gros` | 0 | 刷新 GROS 分支引用 | source repo remote ref | Project | `78738fc9` |
| `rtk git rev-list --left-right --count origin/dev/gros...origin/dev/pcr02` | 0 | GROS 分支 1 个独有提交、产品分支 639 个后续提交 | source repo | Project | branch divergence |
| `rtk git diff --check <gros-base>..origin/dev/gros` | 0 | GROS 原型机械 whitespace gate 通过 | source repo | Project | dev/gros diff |
| `rtk bash ./build.sh self-check --app-root <dev-gros-snapshot> --no-source-check --no-sync-sources` | 1 | 旧根编排器只接受 Make 布局；作为负路径证明其不应承担应用编译 | SDK workspace | Project | negative evidence |
| `rtk make host_linux_x86_64-check` | 0 | 当前冻结 Host 基线含 46 architecture tests、sanitizer/fuzz/integration | source validation record | Project | frozen baseline |
| `rtk make cross-build-verify TARGET=ssc305_linux_armv7` | 0 | 当前冻结 SSC305 product receipt 可读回 | source validation record | Project | frozen baseline |
| `rtk make cross-build-verify TARGET=rdk_x5_linux_aarch64 ...` | 0 | 当前冻结 X5 source/link/runtime receipt 可读回 | source validation record | Project | frozen baseline |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --summary-json --diagnostics` | 0 | 归档后 registry、frontmatter、index、source/path 和 artifact 门禁通过；error=0 | Knowledge Hub | Knowledge Hub | archive candidate |

前七项是设计输入和冻结基线，不是 GROS 新实现通过证据。

## 26. 风险与验证

| 风险 | 控制 | 验证 |
|---|---|---|
| 旧分支过时导致功能丢失 | 从当前产品基线重建，不直接 merge dev/gros | source/feature inventory |
| 隐性双构建权威 | 删除应用 Make 和 crossbuild compile，zero-residue | repository scan |
| CMake cache/并发污染 | contract dir、locks、immutable cache、atomic publish | concurrency/cache negative tests |
| Host/目标库混用 | toolchain root-only、ELF audit、imported targets | wrong-arch fixtures |
| 配置/路径注入 | schema、safe encoder、containment | injection/escape tests |
| 资源或诊断越权 | target resource/program allowlist | bundle inventory policy |
| SDK 同版本内容漂移 | include/vendor lib/BuildID hashes | contract drift test |
| 构建成功误作产品 ready | build/certification/release 分离 | release refusal matrix |

## 27. 当前结论与生效条件

当前结论：需求充分，设计层 blocker=0、major=0，Spec Verdict=`pass`，Quality Verdict=`pass for design`；实现和产品 readiness 未完成。

生效条件：GROS、team-core、SSC305、RDK X5、产品、安全/发布 owner 对正文和 SHA 进行真实复核；RQ-01 至 RQ-12、AC-01 至 AC-15 全部有新鲜证据；SSC/X5 HIL 与 release refusal matrix 通过；registry item 才可另走 owner-gated promotion。`reviewing` 本身不授权实现合入或发布。

## 28. 回滚条件

实现未达到门禁、产品功能/ABI/HIL 回归、bundle/import 不可恢复、release refusal 失效或 owner 拒绝时，整体 revert GROS hard-cut 变更集或使用上一版已发布制品。禁止恢复局部 Make shim、alias 或双轨 fallback。本候选若被新 owner-approved ADR 替代，应走 governed supersede，不直接删除。

## 29. 脱敏与归档边界

正文不保存 raw session、日志、二进制、密钥、token、现场设备端点或临时目录。私有 remote URL、个人身份和绝对用户路径不进入复用结论。源码和产物只记录逻辑身份、commit/hash 或 canonical workspace/project reference。

## 30. Review 周期

- owner：team-core。
- review_after：2026-09-30。
- 下一次复核：GROS CLI/schema 草案、owner 列表、工具版本、RQ/AC 测试矩阵、实施分支和首个 Host target evidence。

## 31. 2026-08-30 实施证据增量

本节记录候选形成后的实现状态，不改变本文 `reviewing`、`pending-owner-review` 和 `manual_validation_pending=true` 的治理状态。

### 31.1 已落地

- 应用仓根 `./gros`、`tools/codex_assets/gros.py`、顶层 CMake 与固定 Ninja 已形成单轨实现骨架。
- Host target 已覆盖 source-set/build-unit DAG、static provider/consumer、sanitizer、TSan、fuzz、APP composition、API、MP4 与 Diag；最新完整 contract 为 `1db5ca9a62dad527b8c5ca1a81fe289ff82086027150605d8fefc4ece01a900e`。
- GROS Python 门禁 31/31，第三方 producer 门禁 10/10，Host 123 步编译、16/16 CTest、install、bundle、cache、receipt 与 verify 回读通过。
- 新增独立 `tools/codex_assets/gros_sdk_import.py`。`--verify-only` 允许审计 bootstrap/link probe；真正 SDK import 除要求 `release_eligible=true` 且 certification state 为 `certified` 或 `released`，还必须提供独立 release authorization、detached signature 和可信公钥。
- Signed authorization 绑定 target、contract、artifact/runtime/SBOM hash、HIL receipt hash、owner approval、签名/发布策略和有效期，bundle 不能自证发布资格。Importer 同时校验完整 inventory、文件 mode、checksum、build receipt、verification 和 source lock；以 `<import-root>/<target>/<contract>` 加锁原子落盘，支持幂等重读并拒绝既有导入或授权漂移。
- 跨进程同 contract lock 串行、不同 contract lock 并行、发布 rename 中断后恢复上一份 owned bundle 的负测试通过。
- RDK X5 development-only 探针曾完成 19/19 source sets、70/70 AArch64 compile/link、video/audio required symbols、Proto generator 和 runtime closure；正式 production target 仍按 production dirty lock 拒绝，未执行板端 HIL，不能高于 `link_verified`。
- SSC305 已冻结 Cortex-A32 / ARMv8-A AArch32 hard-float 身份、20 个 SigmaStar static SDK archives、27 个 ARM32 第三方 producer receipts，并建立 product-test static build-unit DAG；FAAC 与 nanopb 已绑定 exact archive、receipt 和 include root。

### 31.2 新鲜验证与已知基线

| Command | Result | Boundary |
|---|---|---|
| `rtk python3 -m unittest discover -s tests/gros -p 'test_*.py'` | 31/31 pass | GROS resolver、bundle、signed SDK import、concurrency/atomic tests |
| `rtk python3 -m unittest discover -s 3rdparty/build/tools/codex_assets/tests -p 'test_*.py'` | 10/10 pass | dependency producer tests |
| `rtk ./gros all --target host_linux_x86_64 --jobs 16` | pass | Host source/build/test/install/bundle only |
| `rtk ./gros verify --target host_linux_x86_64` | pass | Host bundle/readback；`release_eligible=false` |
| `rtk python3 -m tools.codex_assets.gros_sdk_import --bundle release/host_linux_x86_64/bundle --target host_linux_x86_64 --verify-only` | pass | read-only import audit；不授权正式 SDK import |
| `rtk python3 -m unittest discover -s tests/architecture -p 'test_*.py'` | 45/46 | 唯一失败为既有 `app_test_vi_fps_hil.{h,c}` preserved inventory 缺口 |
| `rtk ./gros doctor --target ssc305_linux_product_test` | fail-closed | 当前先由 release-governed 根仓 dirty lock 拒绝 |

### 31.3 仍开放的生效阻塞

- SSC305 product-test 的 Wi-Fi source/ABI owner、完整 third-party exact imports 和 Diag owner 尚未冻结；production/service/factory 仍缺 task/iot/navigation 第一方源码与 profile-bound program policy。
- RDK X5 尚无 fresh production-clean build、license/notice 完成态 SBOM、板端 video/audio HIL 和 owner certification。
- cache poisoning、双 clean reproducibility 和 zero-residue 尚未全部完成。现有双目录 rename 能恢复可捕获 `OSError`，但两次 rename 之间遭遇 SIGKILL/掉电时 canonical release 可能暂时缺失；必须改为不可变 contract release + 原子 `current.json` 后才算 crash-atomic。
- 应用 Make 产品图、`config/cross_build` 和 crossbuild product compile 仍在实施工作树中；在 C6 整体硬切之前，不得声明“唯一产品构建权威已完成”。
- Host、RDK development probe 和静态 SDK 审计都不能替代 SSC305/RDK X5 产品板 HIL、签名或发布资格。

## 32. 2026-08-30 第二次实施增量

本节继续保持 `reviewing/pending-owner-review`，只更新代码与验证事实。

### 32.1 Crash-safe release 与 SDK import

- Release 已从可替换目录改为不可变 `release/<target>/contracts/<contract>/bundle`，以原子、只读 `current.json` 选择当前 contract。
- 发布逐级创建并 fsync `release/target/contracts/contract`，bundle tree 在 rename 前全量 fsync；current 执行 file fsync、`os.replace`、parent fsync。
- 真实子进程故障注入覆盖 current replace 前/后 SIGKILL，以及 contract publish 后、current更新前 SIGKILL；current始终为完整旧值或完整新值。
- Publisher使用排他current lock，SDK importer使用同一文件的共享lock并覆盖current验证、authorization验证、copy和commit；lock通过`O_NOFOLLOW + fstat regular`打开。
- SDK import在rename前完成readonly seal与tree fsync，再执行durable rename和parent fsync；existing destination也必须全树无写位。coherent cache poison即使同步重写二进制、manifest和checksum，仍因build receipt artifact hash不匹配而拒绝。
- Build bundle始终保持`release_eligible=false`；产品资格只来自独立signed authorization。CLI只接受key ID，从只读`/etc/gros/trust`加载target、公钥hash和批准OpenSSL工具hash；trust root、keys目录、config和key逐级lstat、no-symlink、默认UID0且禁group/other写，应用仓不保存private key。
- 当前GROS Python门禁42/42通过，包含managed-key CLI成功、unknown key/hash drift、symlink、并发、SIGKILL、cache poison和durable import负路径。

### 32.2 Host双clean

最新Host contract为`3e9707a1965f60ddf4b59786f37d46cf15c85e673c6a3d379d1a319ad6758b2f`。执行一次完整all、exact clean、第二次完整all后，下列工件hash前后一致：

- Host ELF：`8c338e315485b361c6fc0341c91681fb9998ce1c5a9699c0bd9de9569c6b785b`
- artifact manifest：`a5dcb2c8c23621b7d24117a91c4bab0bf1afac8d6bcba765c06bdb5ca4c32548`
- build receipt：`6306e2313da9a3d1b479882db248ce9b54224d5e4ff4a19156dc58821ee3e07c`
- test receipt：`ce42dce6ca9f175ba3a57ff75ce6afad8167c71b2544e8370f611649bb32e3f2`
- runtime manifest：`466f0b457bc1e94aea6ab725bd67fcba7a63e1e8ef1478e7b57ee26df8417f98`
- SBOM：`1f4a710450a6fd8470bacf6fa9f96747556dcc4e91faf8192f57e6b4f71bc430`
- current：`dab47d7963b6efefaa43e5e72fbf26d69bb7d165b11e57d2dae56356b5b2dc5c`

两次均完成123个Ninja steps、16/16 CTest、install、bundle、verify。仓内证据为`docs/changes/gros-single-track-hard-cut/REPRODUCIBILITY.md`。

### 32.3 SSC305 product-test source/link probe

最新 development-only probe contract `e407b0ee13e5dab4d4275def88c84a58c9e2df1a0fbbf0b22ce9ce54c9cd2bb7` 已完成：

- 285/285 compile/link；
- Wi-Fi 35个显式源码，绑定独立模块commit；
- AISpeech AEC/SEVC、HDI video/audio、API、APP、OSAL、Platform、MP4、Proto C和product-test均从源码构建；
- 29个declared third-party imports（含TLSF）均通过receipt、ELF/ar、EABI5、hard-float和CPU attribute检查，missing=0；
- 自动required-symbol/DT_NEEDED allowlist gate、持久化cross-artifact receipt、install、verify通过；
- 最终ELF为ELF32/ARM、Version5 EABI、hard-float；
- DT_NEEDED不含绝对/相对路径，非系统动态依赖仅`libwpa_client.so`；
- `bundle --no-publish` runtime closure通过：9个DT_NEEDED全部解析，板rootfs系统库只记录，`libwpa_client.so`进入probe runtime，`unresolved=[]`；未写release/current；
- OSAL恢复原TLSF pool语义，不再降级为libc allocator。

Canonical target已恢复`profile_class=product_test`和`diag-product-test-owner` blocker，正式doctor仍由production dirty lock优先拒绝。因此该证据为source/link probe，不是product-ready或HIL通过。

### 32.4 仍开放

- Release owner尚未为SSC305/RDK X5部署真实`/etc/gros/trust` package和签名授权。
- SSC305 product-test尚缺Diag catalog/policy/limits owner与板端HIL；production/service/factory尚未闭环。
- RDK X5需要基于当前GROS代码重新执行production-clean source/link、runtime、SBOM和板端video/audio HIL。
- C6 zero-residue尚未执行，旧应用Make/crossbuild产品图仍存在。

### 32.5 RDK X5当前代码刷新

Development-only probe contract `50a8113843bf2bb3789415d6917d5696f0b7c7a067455dc91be9e7546689fee9` 已完成：

- 19/19 source sets、70-step compile/link；
- ELF64/AArch64；
- 30个required symbols、6个entry calls、19个direct SDK/third-party DT_NEEDED gate；
- 持久化cross-artifact receipt，`board_hil_executed=false`；
- `bundle --no-publish`递归runtime closure为24 libraries、94 edges、`unresolved=[]`；
- 7个批准third-party shared libraries进入probe runtime，SDK/system libraries只记录provider/hash；
- SBOM仍为bootstrap且license validation pending；
- 未写release/current，canonical target已恢复production并由dirty lock拒绝。

这证明当前代码下RDK X5 video/audio source/link/runtime contract成立，不证明板端camera/audio设备行为、性能、HIL或产品发布资格。

### 32.6 SSC305 nanopb源码外生成闭环

SSC305 product-test 已不再由 GROS 消费源码树内历史 `.pb.c/.pb.h`，而是使用受 contract 约束的 Host `protoc` 与 nanopb plugin，在 `out/gros/work/<target>/<contract>/generated` 中生成 Proto C：

- generator snapshot 同时绑定 Host protoc 二进制与 producer receipt、nanopb plugin 二进制与 producer receipt、Python generator tree、4个显式 `.proto` 输入以及8个预期输出；
- generator receipt 记录8个输出的相对路径、mode和SHA-256，输出只进入本 contract 的source/include图；
- 生成环境设置`PYTHONDONTWRITEBYTECODE=1`，避免向受管third-party sysroot写入`pyc/__pycache__`；本轮探针产生的缓存已精确清除，dependency manifest tree重新通过；
- development-only contract `4fb7eae2266c44274ad980a078970a12feb773bba23d16c9641f35fed5d4eade` 完成285/285 compile/link、cross-artifact test、install、verify和`bundle --no-publish`；product-test已移除源码树legacy proto include；
- 8个生成输出与迁移前基线逐文件SHA一致；runtime closure、required-symbol和DT_NEEDED门禁继续通过；未写production release/current；
- 每次消费已有生成缓存时，GROS都会用contract已绑定的工具和输入重新生成到独立staging，并与缓存输出及receipt逐项比较；同步修改生成文件和receipt的coherent poison负测试必须失败。当前GROS门禁43/43通过，同一contract二次configure的fresh regeneration比对通过；
- 独立复审首轮发现上述coherent cache poisoning major；修复后第二轮复审结论为blocker=0、major=0。剩余minor是nanopb producer receipt未把plugin脚本直接列作artifact，但plugin独立SHA与完整Python tree已进入contract，不影响当前内容身份或source/link-ready结论；
- canonical target已恢复`profile_class=product_test`及`diag-product-test-owner` blocker，当前工作树由production dirty lock优先fail-closed。

因此 nanopb generator 可判定为 source/link-ready；Diag owner、clean product contract和板端HIL仍未完成。源码树内旧生成文件和旧Make引用只作为C6整体硬切前的legacy残留，GROS已经不再消费，禁止长期形成双权威。

### 32.7 C6机器门禁与第二构建系统收敛

本轮继续保持`reviewing/pending-owner-review`，完成以下代码侧收敛：

- 新增contract-bound `./gros hardcut-doctor [--summary]`和`config/hardcut/zero_residue.json`；release-governed profile执行正式publish前必须fresh扫描为`pass/finding_count=0`，development probe和no-publish不能绕过发布门禁。
- 策略覆盖根Make/make.sh、应用及模块Make图、`libs/arm`第一方预编译库、源码树Proto/Diag生成物、测试旁路Make、operational文档旧入口和third-party legacy source fallback；历史`docs/changes`仅作provenance，不纳入普通token误判。
- 删除916个未被Git跟踪的`*.user.arm.o/*.d`与`*.arm.o/*.d`中间文件；没有删除源码、配置或库。
- 18个C++ Proto输入现全部由receipt-bound Host protoc在contract work-dir生成36个输出，与历史`.pb.cpp/.pb.h`逐文件一致；RDK实际只编译当前Sensor消费的3组，其余输出等待对应profile/source-set恢复后消费。
- Host Diag catalog改为first-party script + Python identity + catalog/policy/limits/target输入绑定的GROS generator，生成C/H/Markdown/JSON到contract work-dir；Host不再消费`cmd_server/generated`源码树文件。
- 删除`config/generated` Make source map、archcheck render/generated-check CLI和并行manifest validator；Host release policy改由`gros-doctor`验证唯一target/source-set schema。
- 删除`config/cross_build`、crossbuild/productdeps/runtimebundle三套旧产品实现及其专属architecture测试；GROS dependency/runtime/bundle成为唯一产品语义。
- 删除`THIRDPARTY_ALLOW_LEGACY_SOURCE`代码、环境变量和文档；保留`3rdparty/build` producer，缺失源码现在直接fail-closed。
- daemon从读取配置在APP/product-test间运行时切换，改为编译期profile：production仅监督`prog_pcr02`，service仅监督`prog_cmd_server`；两个profile均以`-Werror` Host static compile unit验证。
- operational AGENTS/README不再指导Make；不存在正式target的模块明确标记为migration pending，避免伪造可执行GROS命令。

独立复审补捕`app_sensor_test/tests/Makefile`及其source-gate/ARM alias语义，并增加GNUmakefile/小写makefile/`*.mak/*.make`防回归规则。当前C6基线：`needs-fix`、95项，其中8个forbidden paths、87个forbidden globs、0个forbidden tokens。剩余内容主要是仍承载legacy production/test消费者的根Make/build、`libs/arm`、Proto工具/生成物、`cmd_server/generated`和测试Make图；在Task/IoT/Navigation源码、production/service/factory target及owner Diag contract齐备前不提前删除。

Fresh development-only evidence：

- Host contract `d24e94df95361792c963d45a41af682227552c5ce37cd562dd3b470f7d8fedaa`：绑定最终C6 policy，133-step、daemon双profile compile、16/16 CTest、install、bundle、verify通过。
- SSC305 product-test contract `96685356e9c9121910209b80a0bddcf79806ec2a20601cdeada87028f74e0af6`：绑定最终C6 policy，285/285、test/install/verify/no-publish bundle通过；canonical已恢复product_test和Diag owner blocker。
- RDK X5 contract `c40c68fc6e9025c7dc3f0f8638f0dd82901d18086c47fdf19e968ea35d4cf1fc`：绑定最终C6 policy，36个Proto输出、70/70、test/install/verify/no-publish bundle通过；canonical已恢复production。
- GROS专项48/48、third-party producer 10/10通过；architecture删除旧authority专属测试后为18/19，唯一失败仍是既有`app_test_vi_fps_hil` inventory缺口。

以上仍是source/code readiness证据，不替代SSC305/RDK X5板端HIL、license/notice、owner certification、正式trust package或signed authorization。

## 33. 2026-08-31 深入审查后的最终实施快照

本节是对32.7历史数据的后续修订；发生冲突时以本节为准。决策状态继续保持`reviewing/pending-owner-review`，不自动提升为active或产品ready。

### 33.1 最终方案不变

- 应用仓根`./gros`是唯一用户入口，GROS/CMake/Ninja是唯一应用源码编译和产品链接权威。
- SDK根目录不编译应用，只按target identity提供receipt-bound toolchain、headers、vendor libraries与板级资源，并单向导入已认证bundle。
- 不保留Make/GROS双图、Make map、crossbuild产品图、source/prebuilt fallback或legacy third-party fallback。
- Host、SSC305、RDK X5共用HDI facade、API、APP composition和Sensor contract；平台差异只允许进入backend、SDK import、toolchain和resource set。

### 33.2 新鲜代码证据

- 最新Host contract为`7e62f195aa0006093093223d4cf24c46804ab3b7ee9125531988d547618f7dd8`：479个compile/link steps通过，CTest 58/58通过。
- GROS专项49/49、third-party producer 10/10、`git diff --check`通过。
- app_sensor_test Host矩阵已纳入GROS，覆盖normal、ASan/UBSan和TSan；修复`CAMERABITRATE=27`已进入生产协议/入口但未进入能力manifest、missing-payload matrix和boundary-validation的契约漂移。
- tests/host、bridge、transport、thread_pool的Make入口已移除。app_sensor_test仍有tool/coverage/ARM路径未迁完，因此其Make入口继续保留并由C6报告。
- architecture suite为18/19；唯一失败为既有`app_test_vi_fps_hil.{h,c}`与registry reference缺失。

### 33.3 C6与产品缺口

最新`hardcut-doctor`为`needs-fix`、110项：83个forbidden globs、8个forbidden paths、19个required-present，policy SHA-256为`90195c5318e0002a4024520a0a5268adcff30fb4d9f4b2588f6e1c0accc602ff`。

19个required-present缺口为：`modules/iot`；SSC305 production/service/factory三个target；对应三个resource set；production/service/factory/product_test四套Diag catalog/policy/limits共12个owner合同。Task已恢复并能Host `-Werror`编译，但transport publish绑定仍fail-closed；Navigation已恢复但未形成完整消费闭包；IoT在可见Git refs中缺失。

Canonical SSC305/RDK X5 product doctor当前均因dirty module按设计fail-closed。此前RDK `c40c68fc...`和SSC305 `e407b0ee...` development probes在对应旧contract下可追溯，但当前源码变化后只能作为provenance；必须在C6清零、owner资产补齐和module lock clean后生成新contract，才能形成新鲜cross-platform结论。

### 33.4 最终门槛

完成条件冻结为：C6=0、architecture=19/19、GROS=49/49、Host=58/58、SSC305 production/service/factory/product_test与RDK X5 production五个产品target新鲜构建通过、runtime unresolved=0，并完成video/audio/sensor板端HIL、license/notice、SBOM、owner certification和signed authorization。任一条件缺失都只能声明分层的source/code readiness，不能声明product-ready或released。

仓内对应快照：`workspace://xcrz-sigmastar-demo/docs/changes/gros-single-track-hard-cut/FINAL-SOLUTION-20260831.md`。

## 34. app_sensor_test 工具测试迁移补充（2026-08-31）

Host target 新增受 contract 绑定的 Python unittest suite：解释器 identity、`app_sensor_test/tools/tests` 的测试文件和 import top-level 都进入build contract；`./gros test --target host_linux_x86_64` 先执行58项CTest，再执行25项 machine/HIL evidence validator，统一 receipt 为83项`ctest+python-unittest`。GROS专项随之为50/50通过。

该迁移只消除 app_sensor_test `tool-check` 对 Make 的依赖，不改变产品边界：该 Makefile 仍包含 gcov coverage 和 ARM source-gate，故C6继续报告其为真实legacy authority，finding_count仍为110。不得将工具测试迁移误写为 ARM product build、coverage gate、HIL 或产品发布完成。
