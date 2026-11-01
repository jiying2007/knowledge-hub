---
id: provider-7ded8e7050bf4cb91cf3100ed41a09f61d05daf4cde25317a92868ab3a7bee2c
title: WiFi三仓落地：空配置初始化、持久化确认和缓存复核验证
kind: validation
domain: projects/gros
path: projects/gros/validation/provider-7ded8e7050bf4cb91cf3100ed41a09f61d05daf4cde25317a92868ab3a7bee2c.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:7ded8e7050bf4cb91cf3100ed41a09f61d05daf4cde25317a92868ab3a7bee2c
  source_sha256: fc2fd2b89c905381718ba779b8a956c654e3c83fce912a8e3ec36255819a29b6
  temporary_source_retained: false
review_after: '2027-01-17'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/gros/validation/provider-7ded8e7050bf4cb91cf3100ed41a09f61d05daf4cde25317a92868ab3a7bee2c.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gros/validation/provider-7ded8e7050bf4cb91cf3100ed41a09f61d05daf4cde25317a92868ab3a7bee2c.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-19'
updated_at: '2026-10-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-19'
manual_validation_pending: true
summary_zh: '- last_verified: 2026-10-19 Asia/Hong_Kong - subject: project:gros - 状态：源码实施及定向验证完成，reviewing
  candidate；设备验证未执行。 - 用户授权：按建议优化落地；仅Sensor/API/WiFi三个独立仓。父工程不修改、不提交，不执行设备写入或发布。 - 背景：测试版本1.4.2，有扫码配网；用户确认上传时配置仍为空，/etc与/data/etc配置为同一软链接目标。同版本测试OTA不作为本轮故障处理。
  - 脱敏：无原始日志、凭据、网络标识、设备端点或OTA地址。'
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: gros
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 7ded8e7050bf4cb91cf3100ed41a09f61d05daf4cde25317a92868ab3a7bee2c
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
aliases:
- WiFi三仓落地：空配置初始化、持久化确认和缓存复核验证
related:
- projects/gros/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# WiFi扫码持久化与缓存优化实施验证

- last_verified: 2026-10-19 Asia/Hong_Kong
- subject: project:gros
- 状态：源码实施及定向验证完成，reviewing candidate；设备验证未执行。
- 用户授权：按建议优化落地；仅Sensor/API/WiFi三个独立仓。父工程不修改、不提交，不执行设备写入或发布。
- 背景：测试版本1.4.2，有扫码配网；用户确认上传时配置仍为空，/etc与/data/etc配置为同一软链接目标。同版本测试OTA不作为本轮故障处理。
- 脱敏：无原始日志、凭据、网络标识、设备端点或OTA地址。

## 实施结果

- WiFi新增配置文件准备helper：跟随软链接，不替换入口；open无O_TRUNC，非阻塞文件锁和fstat确认普通文件；只初始化不存在/零字节配置，非空内容保留；空文件权限收紧0600，检查write/fsync/close，失败尽力回滚零长度。
- WiFi配置初始化仍在backend启动前进行，API重复路径兜底移除，避免不同层分别创建配置。
- 新wifi_sta_confirm_network_saved/linux_sta_confirm_network_saved只在STATUS已完成且SSID匹配时执行SAVE_CONFIG，检查返回并同步配置文件及目录；空/缺失文件不确认成功。不执行SELECT、ENABLE、RECONFIGURE，不因保存失败主动断链。
- API原SaveNetwork保留内存语义。新api_wifi_persistence.h提供VSAPIWIFI_ConfirmNetworkSaved，使用已有保存网络锁串行，暂停/关闭时拒绝准入，在途计数纳入API quiet/DeInit检查。
- Sensor不再由连接完成路径重写API内存重连目标，Connect已经拥有该上下文；独立确认持久化，失败仍保持linked。
- Sensor首次保存失败后的待保存标记跨连接完成清理保留，由owner worker驱动重试；最多3次，总计首次+2次重试，失败后退避5秒、10秒；代次变化/停止/低功耗/扫描边界拒绝不合时宜的保存，generation0不写盘。
- 缓存记录local/backend来源、年龄和revision；优先缓存的有效期30秒，稳定联网分支按现有10秒周期直接复核后端且避免在途扫描。查询失败不覆盖原缓存；旧generation/revision结果不提交。
- 日志区分持久化ret/attempt/terminal及cache来源；后台LIST_NETWORKS快照仍标记persistence=unverified，不能当作磁盘证明。
- API/Sensor模块优先引用API源仓头，解决当前父镜像缺CancelConnect声明；新增接口无需复制到父工程公共头。Sensor构建过滤tests，避免Host mocks入产品。

## 源码身份与变更指纹

- WiFi HEAD: 5c3f8bc06a6c73ed8cbbc78319600fefe3cfc8d3
- API HEAD: 53b557b0ae39368653041d299abb18732e5132ee
- Sensor HEAD: 6fb68755c68be8ca0410952d9ebd7b94a16fdb92
- 工作树任务文件清单及逐文件SHA256：/tmp/wifi-persistence-repo-evidence.json，SHA256=660e50b35db49ba25d89bab27f55b1c629c9371213ca36ad9b28b208b1840014。
- 已保留Sensor原有audio两文件dirty、API原有6项暂存音频/测试改动；没有stage、commit或push。
- 新测试位于各模块内部tests/persistence或tests/wifi_persistence。父工程源码、公共头及测试未修改。

## 新鲜验证

1. make -s -C modules/wifi/tests/persistence test：ASAN/UBSAN PASS。
   - 缺失/零文件、软链接保留、非空内容保留、锁冲突；错误目标/未连接拒绝；SAVE失败及空/缺失文件同步失败。
2. make -s -C modules/api/tests/wifi_persistence test：ASAN/UBSAN PASS。
   - 参数/初始化准入、保存失败传播、保存事务锁、后台active计数及暂停拒绝。
3. make -s -C modules/sensor/tests/wifi_persistence test：ASAN/UBSAN PASS。
   - 真实handleConnectedState首次失败仍联网且保留pending，owner retry成功，连续3次失败上限；代次0拒绝、旧代次完成和查询丢弃、缓存TTL复核、stop/低功耗拒绝。
4. make -s -C tests/wifi_recovery_lifecycle test：PASS。
   - recovery、callback、manager teardown、IPv4 snapshot、station parser、control logging、release contract。
5. 原Sensor集成service_test.cpp与当前consumePendingCredential多一项bool参数不匹配，且旧mock缺CancelConnect；父工程禁止改动，因此在/tmp副本中适配该参数、Cancel mock和独立Confirm mock，完整原生命周期ASAN/UBSAN回归PASS。
   - 副本：/tmp/wifi-persistence-service-regression.cpp；可执行：/tmp/wifi-persistence-service-regression。
   - 不宣称父工程原测试未经适配可直接通过。
6. 三仓diff --check PASS；API/Sensor tools/ai.sh doctor和check PASS。check仅为边界/文档/空白检查，不替代编译。
7. 按本源码Makefile dry-run提取真实编译参数，使用平台gcc11.1 glibc ARM工具链，对api_wifi.c、sensor_wifi_service.cpp、linux_common.c、linux_sta.c、wifimg.c定向对象编译全部PASS，输出仅/tmp。
   - API/Sensor头优先顺序与修改后的lib.mk一致；初次Sensor编译暴露父镜像缺CancelConnect，修正模块include顺序后PASS。
   - WiFi仍存在原有unused、隐式声明与格式容量warning；未将warning清零或整库构建作为已完成结论。
8. 锁定clang-format18.1.8用于本轮任务改动格式化；没有使用系统fallback。

## ARM对象指纹

- /tmp/wifi-persist-api.o: ce0632efdfbc0f5f998101ab916f45379f56a59dabcb8c4e24a0f0e874209faa
- /tmp/wifi-persist-sensor.o: e268d69ac66e781c373136d900936e817fed2837cd8301da7cb3f0a41a694b99
- /tmp/wifi-persist-linux_common.o: 83f017bfe7ea7f4bd5207fc747bf19d5f3fed4c5671f3770514592e5da2a6c6e
- /tmp/wifi-persist-linux_sta.o: 4bacbba4613a70a6eaeb9b447fb6dc21d41d7ca980e0a7421c511a4411ab39a8
- /tmp/wifi-persist-wifimg.o: d6a8ec0e3d99f131d84247d5c41009d5bb4191feae4e33b7de44809fc8573040

## 独立审查与边界

- Reviewer: wifi_remediation_review；working-tree whole-diff/相关生命周期审查，独立只读。
- Spec PASS、Quality PASS，无未解决blocker/major。修复了审查发现的连接cleanup误清保存marker、worker缺retry驱动、代次0、过期完成覆盖与假通过测试等问题。
- 最后非阻断errno日志问题已修正：空/非普通文件明确EINVAL；增加空文件失败测试并复验。
- SAVE_CONFIG响应和fsync不等同于设备重启、掉电或OTA验证。fsync没有硬实时上界，不声称端到端硬超时。
- 未重新链接最终APP，未生成/部署image或OTA，未执行板端HIL。三仓配套库必须一起构建；不得将带新API的Sensor/API与缺少对应符号的旧WiFi/API预编译库混用。
- 下一设备验收：空文件启动后扫码→配置保存确认→正常关开机免扫码恢复；写失败时当前链路可用；同版本测试OTA保留网络。设备写入需另有明确设备入口和授权。
- completion_claim: 三仓源码优化和上述定向验证完成；product/HIL未验证。
- open_items: 源码实施0；设备验收及最终制品集成另列，不宣称完成。

## 完成声明与恢复边界

- claimant: 主实现；verifier: 独立wifi_remediation_review及真实编译/测试返回码。
- lifecycle: owner为Sensor worker、API保存事务锁与backend配置owner；连接成功后保存pending独立存活，停止/低功耗关闭准入，已进入的同步保存由worker/API active排空。保存失败不改变link，晚结果核generation/revision。
- retry_budget: 同类编译失败复核后修正；保存业务最多3次，退避不无限重试。实现中的接口与测试适配均有明确负结果记录。
- reusable_pattern: 链路成功、运行时网络与持久化确认分层。
- promotion_candidate: false；do_not_promote_reason: 仍为特定项目源码修复且缺设备证据，不写团队规则或memory。
- next_task_friction_reduced: 可复跑模块内测试和独立持久化结果日志；reduced_by: 配置、API、Sensor三个行为层各有定向用例；reduction_evidence: 上述Host回归。
- owner_review: 未取得产品owner/HIL放行；独立源码复审通过。
- rollback_path: 后续若回退需三仓配套回退本轮任务文件，不覆盖音频dirty，不恢复父工程revert；本次不执行回退。
- verification_evidence: 本报告及repo manifest；浏览器/UI/Runtime配置改动不适用，无设备现场写入。
- breaking_change: 原SaveNetwork语义保留；新增API/WiFi符号要求配套库，源头优先编译；旧预编译库不作为此次集成兼容目标。
