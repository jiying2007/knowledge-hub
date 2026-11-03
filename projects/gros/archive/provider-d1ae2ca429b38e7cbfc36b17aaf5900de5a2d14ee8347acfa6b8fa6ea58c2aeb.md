---
id: provider-d1ae2ca429b38e7cbfc36b17aaf5900de5a2d14ee8347acfa6b8fa6ea58c2aeb
title: wifi_loss_lei_2复核报告：同版本定时OTA与关联前33分钟等待
kind: debug-record
domain: projects/gros
path: projects/gros/archive/provider-d1ae2ca429b38e7cbfc36b17aaf5900de5a2d14ee8347acfa6b8fa6ea58c2aeb.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:d1ae2ca429b38e7cbfc36b17aaf5900de5a2d14ee8347acfa6b8fa6ea58c2aeb
  source_sha256: e1fd686be07f89d5575dd9a232b9594062b7984f4535979746f41df995fe4900
  temporary_source_retained: false
review_after: '2027-01-17'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- debug-record
validation_refs:
- projects/gros/archive/provider-d1ae2ca429b38e7cbfc36b17aaf5900de5a2d14ee8347acfa6b8fa6ea58c2aeb.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gros/archive/provider-d1ae2ca429b38e7cbfc36b17aaf5900de5a2d14ee8347acfa6b8fa6ea58c2aeb.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-19'
updated_at: '2026-10-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-19'
manual_validation_pending: true
summary_zh: 分析日期：2026-10-19。范围：本地采集目录 wifi_loss_lei_2，只读离线分析；未修改生产源码、未构建、未连接设备。结论为项目级 reviewing 候选。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: gros
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: d1ae2ca429b38e7cbfc36b17aaf5900de5a2d14ee8347acfa6b8fa6ea58c2aeb
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# wifi_loss_lei_2 分析报告

分析日期：2026-10-19。范围：本地采集目录 wifi_loss_lei_2，只读离线分析；未修改生产源码、未构建、未连接设备。结论为项目级 reviewing 候选。

## 核心结论

本包主要故障链为：凌晨定时任务执行当前同版本 OTA → prog_ota 接管、主应用正常退出 → 后续启动后长时间未主动关联保存网络 → 多次配网/待机往返 → 人工扫码后快速联网并恢复 MQTT。

直接离线触发与后续无法自动恢复应分开处理。前者有 OTA 和应用退出的明确证据；后者定位在首次关联发起之前，尚不能确认是磁盘凭据丢失、配置加载失败，还是自动重连策略没有正确启动。不能将整个中断解释为无线弱信号或 DHCP 超时。

本包主体窗口为 10月17日至18日；此前用户说明的 10月19日关闭 lei 热点再打开属于另一段实验。包内目标网络以 AP-A 代称，不将文件名中的 lei 当作实际 SSID，也不把热点开关动作映射到本包。

## 证据覆盖与身份

- 采集包含 app、Sensor、Task、IoT、Bridge、Navigation、Common、AI 的日志及轮转文件，以及179行 WPA 历史日志。app/WPA 混有多次历史启动，不能整包累计成一次故障。
- Task .1 覆盖 10月17日17:11至18日02:01，当前文件接续至02:40，包含重启后未校时的1970时间段。Sensor .1 覆盖17日19:30至18日00:28，当前文件包含02:04退出和后续启动。这里只报告关键覆盖，不据首尾证明全程无缺口。
- WPA 新包12096字节，旧包 wifi_loss_lei_1 的10979字节为其完整字节前缀。旧事件不能再次计为新增掉线；尤其历史 reason=3、locally_generated=1 不能归为本次主因。
- 后续启动日志：Task版本1.4.2、banner commit f4b5afae；Sensor banner v1.4.0-14-g6935f84；IoT banner 5c269f4。banner仅为日志身份线索，未取得安装ELF、库或OTA包hash，不能与当前源码/本地补丁建立精确对应关系。
- WPA使用数值时间，应用时间先为1970再跳至2026。未校时窗口内部可计算差值；不把1970的16:58解释为设备已运行近9小时，不跨校时直接计算33分钟。
- 包中 data/etc/wpa_supplicant.conf 为0字节。不能排除采集占位、脱敏、路径映射或采集时机影响，不能据此断言设备真实配置被OTA删除。

以下定位以 data/log 为基准；正文不保存密码、二维码内容、设备/用户身份、MAC或私有端点。

## 定时OTA与业务退出

| 时间（2026-10-18） | 事件 | 来源 |
| --- | --- | --- |
| 01:10:51 | 收到1.4.2请求，当前1.4.2、force_update=0，入口明确skip | prog_pcr02/task/task.1.log:3862 |
| 02:00:00.512 | 每日02:00任务触发，从待机退出并处理OTA | task/task.1.log:4207 |
| 02:00:03.265 | OTA版本1.4.2、当前1.4.2、compare result=0，仍进入OTA状态 | task/task.1.log:4237 |
| 02:00:03.273 | 发起下载，随后清除持久化pending请求 | task/task.1.log:4252、4255 |
| 02:04:13.599 | 下载成功，进入升级子状态 | task/task.log:2324、2327 |
| 02:04:17.336 | 启动prog_ota，随后handoff | task/task.log:2376、2391 |
| 02:04:18.512 | 主应用开始有序退出 | app/app.log:797 |
| 02:04:19.694 | MQTT断开 | iot/iot.log:717 |
| 02:04:22.229 | 主应用退出，exit_status=0 | app/app.log:827 |
| 02:06:57.604 | WPA接口deinit；相邻行有TERMINATING | wpa_supplicant/wpa_supplicant.log:164–170 |

02:04:17.876仍记录AP-A、RSSI=-36dBm（task/task.log:2384），随后由OTA路径接管和退出。证据支持这是生命周期导致的业务中断，不支持“先自然掉Wi-Fi、再导致应用退出”。WPA拆除比MQTT退出晚约158秒，业务离线与无线拆除不是同一时刻。

高置信行为缺口：同版本请求在普通入口被skip，但定时执行路径仍启动下载、升级和退出。定时/pending任务的有效性与执行前版本复核需要重点审计。由于没有本次pending创建/恢复的完整来源和force语义证据，不能断言该任务必定来自哪次请求，也不能仅凭compare=0推断所有同版本升级都非法。

后续启动Task读取 /ota/ota_status 为SUCCESS并上报成功（task/task.log:2412–2416、2554）。这证明业务状态文件和上报行为；缺少prog_ota完整执行日志、分区写入记录及升级前后制品hash，不能独立验收升级内容正确或断电恢复能力。

## 启动后约33分钟等待

下表1970时间仅用于同一未校时连续段内计算相对间隔。

| 时间 | 事件 | 来源 |
| --- | --- | --- |
| 16:58:13.156 | 主应用启动入口 | app/app.log:828 |
| 16:58:17.132 | Wi-Fi API初始化；随后首次linked=false、state=2 | sensor/sensor.log:1651–1655 |
| 16:58:28.514 | 返回保存网络缓存count=0，明确without vendor query | sensor/sensor.log:1706 |
| 16:59:18.575 | 首次弱网切换返回error=-4，Task却打印sent successfully | sensor/sensor.log:1757；task/task.log:2662–2664 |
| 16:59:28.581 | 持续LINK_DOWN触发首次NetCfg | task/task.log:2679 |
| 16:59:35.725 | 二维码显示请求成功 | task/task.log:2719 |
| 16:59:39.039 | 待机超时打断NetCfg并关闭扫码 | task/task.log:2721–2725 |
| 17:31:14.491 | 扫码成功并进入凭据处理（内容已脱敏） | sensor/sensor.log:3353–3354 |
| 17:31:19.633 | 真正发起Wi-Fi connect调用 | sensor/sensor.log:3390 |
| 17:31:21.140 | connect返回成功，elapsed_ms=1506 | sensor/sensor.log:3391 |
| 17:31:21.188 | linked=true | sensor/sensor.log:3398 |
| 校时后02:40:15.609 | MQTT连接成功 | iot/iot.log:1626 |
| 02:40:18.814 | 配网业务认证完成并报告成功 | task/task.log:5060–5061 |

可复核耗时：

- 应用启动入口至Sensor linked=true：约33分08.03秒；Wi-Fi API初始化至发起connect：约33分02.50秒。
- WPA最后一次初始化32294.006403至首次关联34279.742372：1985.736秒，即33分05.74秒；首次关联至握手完成34280.014514：0.272秒（WPA:171–179）。两条独立日志都将主要延迟定位在关联前。
- 扫码成功至Sensor linked=true：约6.70秒。其中读取扫描结果约2.553秒，connect调用约1.506秒，其余为扫描准备及消息/资源处理，不把剩余时间全部归为DHCP。
- 首次NetCfg进入至二维码请求成功约7.14秒；其中相机因充电挂起，直到电池回调恢复资源。二维码请求成功至待机触发仅约3.31秒，实际可见时长仍需显示端确认。
- MQTT断开02:04:19.694至恢复02:40:15.609，墙钟可见跨度约35分55.91秒。该跨度包含OTA、启动及人工扫码等待，不能称作自动重连耗时；期间有重启/校时，精确持续时长还需独立单调时间证据。

## 自动恢复路径暴露的问题

1. **保存网络视图和真实凭据混淆。** 升级前缓存count=1；后续启动反复count=0，且日志明确省略vendor query。只能确认上层获得空缓存，不能证明supplicant/磁盘也为空。结合长时间没有关联，候选是保存网络初始化、刷新或重连准入问题；真正磁盘未持久化/未加载也仍未排除。需获取启动时实际配置路径、文件状态及LIST_NETWORKS直接查询终态。
2. **失败ACK被包装成成功。** 后续启动至扫码段有7次弱网切换ACK失败error=-4，同时出现7次sent successfully。Sensor均linked=false；其错误文本称disconnect recovery in progress，但单凭文本不能证明底层确实有恢复任务。需分清发送、受理、完成结果及冷却起点。
3. **LINK_DOWN触发配网与待机往返。** 同窗口统计17次NetCfg进入、16次NetCfg被待机打断。未连接和RSSI=0不能视为实测弱信号。自动恢复未形成终态时，业务仍反复开关扫码/显示资源，影响人工恢复入口的稳定性。
4. **配网资源恢复依赖周期回调。** 首次进入NetCfg时相机挂起，QR enable反复被拒绝；随后电池回调解挂才成功。建议进入NetCfg主动完成资源申请与恢复，并定义等待/失败结果。
5. **超时使用受校时影响的时间。** 联网校时后出现Severe weak network ended after 1792228186s（task/task.log:5042）。该值显然不能作为故障持续时间，应审计持续时间和冷却是否使用单调时钟。

## 不能据此成立的结论

- 不能称为热点关闭触发、密码错误或射频故障。该包没有与10月19日热点实验相符的事件窗口，最后扫码握手与连接快速成功。
- 不能证明配置被OTA覆盖或删除；包内0字节配置与运行时count=0都是待核线索。
- 不能把历史WPA reason=3逐条计为本次自然掉线；本包包含旧包全部WPA前缀。
- 不能把源码中已修复的持久化/缓存策略当作这台设备已经部署；缺最终制品身份。
- 缺少kernel、驱动固件、完整prog_ota和采集脚本证据，不能宣布驱动完全健康或升级保数据已通过。

## 建议处理顺序与验收

优先审计定时/pending OTA执行前复核：当前版本、目标版本、force和请求有效期应在实际执行前确认；已完成或过期pending明确失效。验收覆盖普通入口skip、重启恢复pending、等待期间当前版本变化以及明确允许force的路径。

随后核对Wi-Fi启动恢复：真实配置与known-network查询来源可观测；空缓存不得充当“无凭据”的最终结论，查询unknown需有有界恢复；保留凭据，避免通过清空配置试错。验收分别覆盖保存成功后重启、保存失败但当前连接可用、配置缺失/空白、后端查询失败、目标AP暂时不可用。

同步收敛Task契约：ACK失败不记成功、不错误启动成功冷却；区分LINK_DOWN/恢复中/未知与实测弱网；NetCfg与待机按产品定义互斥或有明确优先级，提供稳定配网窗口。所有超时、冷却和持续时间改用单调时钟并验证校时跳变。

本次交付为分析报告。未执行上述源码修复、构建或板端测试，也未验证设备已恢复自动联网。

## 证据指纹

| 文件（包内相对路径） | SHA256 |
| --- | --- |
| data/log/prog_pcr02/app/app.log | a220020c1d83a776d60655407d9083a66937e264effccdcce11ee74bd5749669 |
| data/log/prog_pcr02/task/task.1.log | 5a8a89c865a422abba7a004da493c8e33b4630e47de0cb1356143ddd9ceca91c |
| data/log/prog_pcr02/task/task.log | 4bd1a36285a331598751955dc1445f5a6d6b0529e85ae22ee9b318147f61dc3d |
| data/log/prog_pcr02/sensor/sensor.log | e50aa8ee8321877dcc990cef80c74ae183485342dc84a12c449ba4a40af89ee8 |
| data/log/prog_pcr02/iot/iot.log | 5fc8b8641ed2ae5d31d37aac3afb752a1489deb8c6123b3c0a0d09f0ae672c45 |
| data/log/wpa_supplicant/wpa_supplicant.log | ed5ad290bfe5e4a6a2f1536864c95531917b9e1ba4dcfde93d06b1ce1747e491 |

知识检索：Provider context路由解析为project:gros，命中同主题reviewing候选；本报告关键结论由本次本地原始材料重新核验。扩展evidence-pack请求返回PROVIDER_RESPONSE_INVALID，未据该调用宣称获得补充证据。
