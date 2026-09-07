---
id: pcr02-diag-curl-large-download-validation-20260806
title: PCR02 diag 大文件直链下载实现与构建边界验证
kind: validation
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/validation/2026-08-06-diag-curl-large-download.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: Codex source implementation and cross-build validation on 2026-08-06
  source_sha256: e5be0c5e854a7be980237f1c75a46f864f44db22b634478ea6e60180978f19e9
  temporary_source_retained: false
review_after: '2026-11-06'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- diag
- curl
- large-file-download
- build-boundary
validation_refs:
- projects/pcr02-ssc305/validation/2026-08-06-diag-curl-large-download.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/pcr02-ssc305/validation/2026-08-06-diag-curl-large-download.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-06'
updated_at: '2026-08-06'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-06'
manual_validation_pending: true
summary_zh: 记录 PCR02 diag 大文件直链下载的异步命令、续传与校验契约、HTTPS CA 配置、写盘错误诊断，以及 obj/lib/app 构建和 MainAppDiag 启用边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 diag 大文件直链下载实现与构建边界验证
related:
- projects/pcr02-ssc305/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 diag 大文件直链下载实现与构建边界验证

## 来源与时间

- captured_at: 2026-08-06
- source: PCR02 源码仓当前 Codex 实现与本地交叉编译验证
- scope: `modules/api` curl 下载能力、`modules/app` API_CURL diag provider、现有 diag-enabled 应用制品

## 可复用结论

1. 大文件下载不能占用同步 diag 请求直到传输结束。现有兼容命令保留，新增异步 `start/status/cancel` 三命令；provider 仅维护单个 joinable job，curl 层负责进度回调、取消、断点续传与可靠写入。
2. 续传文件固定使用同目录 `<dest>.part`。只有同时提供 `expected_size` 与 SHA256 时允许续传；下载完成后先校验 size/SHA256，再通过同目录 `rename` 发布目标文件。取消和可恢复网络失败保留 `.part`，协议不兼容、size 错误或 checksum 错误不发布错误文件。
3. 续传请求若返回非 HTTP 206（包括服务端忽略 Range 或 416），必须判为协议不兼容并从零重试，不能继续追加。curl 写回调必须处理短写、EINTR，并在成功返回前 `fsync`。
4. 带签名的直链可能在 query 中含凭据；默认日志不得输出 effective URL 全文。
5. 本仓 `modules/<name>_obj_all` 只刷新对象文件，不会自动刷新 `lib<name>.a`。验证最终制品时必须按顺序重建受影响模块对象、静态库，再链接应用；仅执行 `pcr02_app_all` 可能继续使用旧库并产生“链接成功但新命令不在 ELF”的假阳性。
6. `prog_product_test` 默认初始化 `ProductTestDiag`；主应用通过 `SENSOR_DIAG_CMD_NODE_ENABLE=1` 初始化 `MainAppDiag`。只修改 `modules/sensor/lib.mk` 中的编译宏不会使旧对象自动失效，必须先清理 sensor 对象再重建库和主程序。板端从 `no_active_handler` 变为 `accepted`，证明当前运行制品已经注册 `diag.api.curl.download.start.run`，但 `accepted` 仅代表任务入队，不代表下载成功。
7. HTTPS 严格校验应显式绑定随产品发布的 CA bundle。当前 provider 修改默认使用 `/customer/bin/resource/ssl/cacert.pem`，并允许通过 `ca_file` 覆盖；该修改仍需随新版 `libapp.so` 和 resource 一起部署验证。curl error 60 表示证书校验失败，应先检查设备时间、CA 文件存在性和可读性，不能把 `strict_ssl=0` 作为正式修复。
8. curl error 23 在当前下载路径中表示文件写回调的 `write()` 返回 `<= 0`。异步任务写入 `<dest>.part`，成功校验后才 `rename` 到最终路径；单纯存在同名最终普通文件不会在传输阶段触发 error 23。优先检查空间/配额耗尽、只读挂载、目录或 `.part` 权限、文件系统或闪存 I/O 异常。当前写回调未打印 `errno`，板端只能先通过文件系统证据缩小范围。
9. 压测可显式设置 `delete_before_download=1`。任务在空间检查和网络连接前删除最终文件与 `<dest>.part`，默认值为 `0`；该参数与 `resume=1` 互斥。删除功能仅接受 realpath 仍位于 `/data/` 下的普通文件或软链接，目录、越界目标和经父目录软链接逃逸到 `/data` 外的路径会拒绝，避免误删系统分区。

## 使用方式

先确认命令 owner 已注册：

```sh
/customer/bin/prog_cli diag list
```

推荐使用 HTTPS、`/data` 分区、严格证书校验以及同镜像发布的 CA bundle。需要断点续传时，必须把示例中的大小和 SHA-256 替换成服务端文件的真实值：

```sh
/customer/bin/prog_cli diag run diag.api.curl.download.start.run \
'{"url":"https://server/path/file.bin","dest":"/data/file.bin","ca_file":"/customer/bin/resource/ssl/cacert.pem","resume":1,"expected_size":123456789,"sha256":"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef","connection_timeout":30,"retries":2,"retry_sleep":1,"strict_ssl":1}'
```

`start` 返回的 `accepted` 只表示任务已入队，必须用实际 `job_id` 查询终态：

```sh
/customer/bin/prog_cli diag run diag.api.curl.download.status.get.run '{"job_id":"curl-1-1000"}'
/customer/bin/prog_cli diag run diag.api.curl.download.cancel.run '{"job_id":"curl-1-1000"}'
```

重复下载压测时可以在每轮开始前自动删除同名最终文件和 `.part`。这是不可恢复的显式删除操作，只能用于 `/data/` 下已确认可删除的压测目标：

```sh
/customer/bin/prog_cli diag run diag.api.curl.download.start.run \
'{"url":"https://server/path/file.bin","dest":"/data/file.bin","ca_file":"/customer/bin/resource/ssl/cacert.pem","delete_before_download":1,"resume":0,"expected_size":123456789,"sha256":"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef","connection_timeout":30,"retries":2,"retry_sleep":1,"strict_ssl":1}'
```

- `delete_before_download=1` 与 `resume=1` 同时出现会返回 `bad_request`，不会删除文件。
- 删除前会同时预检最终文件和 `.part`；任一目标是目录、不可访问或越过 `/data/` 边界时，本轮失败且不开始下载。
- 异步命令仍可能先返回 `accepted`，删除或下载是否成功以 `status.get` 的终态为准。

## 运行时故障定位

| 现象 | 最小失败范围 | 首要检查 |
| --- | --- | --- |
| `no_active_handler` | cmd_server 没有该命令 owner | `diag list`、`MainAppDiag` 启动日志、sensor 是否清对象后重编译 |
| curl error 60 | TLS peer/CA 校验 | `date`、CA bundle 是否存在可读、`ca_file` 是否随新版 provider 生效 |
| curl error 23 | 下载目标写回调 | `/data` 空间/配额、挂载读写状态、目标目录和 `.part`、内核 I/O 日志 |
| `Channel does not report total download size` | 进度总量未知 | 本身不是下载失败；结合其后的 curl/HTTP 错误判断 |

error 23 板端只读取证命令：

```sh
df -h /data
df -i /data
mount
ls -ld /data /data/file.bin /data/file.bin.part
dmesg | tail -n 100
```

- `resume=0` 时，已有 `.part` 会先删除再重新创建；删除失败会在进入 curl 传输前返回文件写错误，不会表现为 curl error 23。
- `resume=1` 时，仅在同时提供 `expected_size` 和 `sha256` 后复用 `.part`；现有分片大于预期大小会先删除。
- 最终普通文件已存在时，同目录 `rename` 可以替换它；若最终路径是目录或目录权限不允许替换，失败发生在下载完成后的发布阶段，也不是 curl error 23。
- 若 `df`、挂载和权限均正常，需要在 `_Curl_CallbackWriteFile` 的失败分支补充 `errno`/`strerror(errno)` 日志，再复现一次确定是 `ENOSPC`、`EROFS`、`EIO` 或其他写盘错误。

## 验证证据

| Command | Exit Code | Result Summary |
| --- | ---: | --- |
| `rtk make modules/api_obj_all modules/app_obj_all -j20` | 0 | API 与 APP 受影响对象交叉编译通过。 |
| `rtk make modules/api_lib_all modules/app_lib_all -j20` | 0 | 静态/动态模块库刷新通过。 |
| `rtk make app_product_test_app_all -j20` | 0 | diag-enabled 应用链接通过。 |
| `rtk make pcr02_app_all -j20` | 0 | normal PCR02 应用回归链接通过，但不含 command node 新命令。 |
| `rtk python3 -m unittest tests.contracts.test_diag_curl_large_download_contracts -v` | 0 | 当前 15 项源码契约测试通过，包含压测删除开关、resume 互斥、双目标预检、生命周期回收和 `/data/` realpath 边界。 |
| `rtk strings out/arm/app/prog_product_test \| rtk rg 'diag\\.api\\.curl\\.download\\.(start\|status\|cancel)'` | 0 | 三个异步命令均进入 ELF。 |
| 板端 `diag.api.curl.download.start.run` | 0/`accepted` | `MainAppDiag` 路由与命令 owner 已生效；后续分别观察到 curl error 60 和 error 23，尚无成功终态证据。 |

负路径：首次只刷新对象后直接执行 `pcr02_app_all` 虽退出 0，但 ELF 中没有新增命令；复核调用链后确认该制品未初始化 command node，且旧静态库未刷新。该结果用于约束后续验证顺序，不能当作功能通过证据。

## 边界与风险

- 已有板端路由和真实 HTTPS 传输失败路径证据，但尚未取得 `succeeded` 终态；断网续传、取消时延、磁盘耗尽和 soak 仍待 HIL。
- `VSAPICURL_Data_t` 末尾新增字段保持源码兼容，但旧二进制调用方必须与新库一起重编译，不得混用旧对象与新 `libapi`。
- 后编译 app 不会自动进入已有 image/OTA；发布前必须重生制品并逐级核对 size、MD5、BuildID。
- 本记录保持 reviewing，不生成 owner decision，不提升 active，不授权部署或发布。

## 后续验证

在明确设备端点和部署授权后，按单次 smoke、5～10 次短循环、1000 次长循环、soak 逐级验证：正常下载、断点续传、服务端不支持 Range、取消、checksum 失败、空间不足与进程退出回收。
