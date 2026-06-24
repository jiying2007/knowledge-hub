---
title: PCR02 Diag V4 Hybrid RefCount + 发现先行 实现计划
doc_type: plan
knowledge_type: decision
maturity: verified
status: archived
owner: team-core
created: 2026-05-10
last_updated: 2026-05-12
tags: [diag, v4, refcount]
related: []
validation_refs: []
---

# PCR02 Diag V4 Hybrid RefCount + 发现先行 实现计划

> 归档说明：本文为历史计划，未勾选步骤不代表当前待办；重新执行前必须重新核对源码、构建脚本和验证命令。

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 落地 `Hybrid + RefCount` 生命周期、`discover-first` CLI、自发现命令目录与分层版本清单，并修复 `VSAPIDVR_RecordInit` 重复初始化风险。

**架构：** 以 `app_diag registry` 为状态中心，新增 provider 运行态与 `owner_ref/ext_ref`；`cmd_node` 新增 `catalog/help/version/provider-state` 命令；API 通用 provider 与 DVR owner 同时实现内部 RefCount 防重。`cmd_server` 仍保持纯转发与路由。

**技术栈：** C（VS_* 类型与 VSHDIOS 并发原语）、ZMQ IPC、Python 静态门禁脚本（ripgrep）

---

## 文件结构（先锁定）

### 创建
- `tools/diag/checks/check_diag_contract_symbols.py`：契约符号门禁（公共头）。
- `tools/diag/checks/check_diag_registry_refcount.py`：registry 状态机/refcount 门禁。
- `build/check_api_dvr_refcount.py`：DVR Init/DeInit RefCount 门禁。
- `docs/reports/2026-05-10-diag-v4-hybrid-refcount-execution-notes-report.md`：执行归档。

### 修改
- `include/common/diag/diag_types.h`
- `include/common/diag/diag_provider.h`
- `include/app/app_diag_registry.h`
- `modules/app/include/app_diag_registry.h`
- `modules/app/src/app_diag/framework/app_diag_registry.c`
- `modules/app/src/app_diag/framework/app_diag_dispatcher.c`
- `modules/app/src/app_diag/ipc/app_diag_cmd_node.c`
- `cli/cli.c`
- `modules/app/src/app_diag/provider/api/app_diag_api_event_provider.c`
- `modules/app/src/app_diag/provider/api/app_diag_api_msg_provider.c`
- `modules/app/src/app_diag/provider/api/app_diag_api_wifi_provider.c`
- `modules/app/src/app_diag/provider/api/app_diag_api_ws_provider.c`
- `modules/app/src/app_diag/provider/api/app_diag_api_tick_provider.c`
- `modules/api/src/api_dvr/api_dvr_record.c`
- `tools/diag/checks/check_diag_phase6_static.py`

### 测试/门禁入口
- `python3 tools/diag/checks/check_diag_contract_symbols.py`
- `python3 tools/diag/checks/check_diag_registry_refcount.py`
- `python3 build/check_api_dvr_refcount.py`
- `python3 tools/diag/checks/check_diag_naming.py`
- `python3 tools/diag/checks/check_diag_layer_deps.py`
- `python3 tools/diag/checks/check_diag_phase6_static.py`

---

### 任务 1：扩展公共契约并同步双轨头文件

**文件：**
- 创建：`tools/diag/checks/check_diag_contract_symbols.py`
- 修改：`include/common/diag/diag_types.h`
- 修改：`include/common/diag/diag_provider.h`
- 修改：`include/app/app_diag_registry.h`
- 修改：`modules/app/include/app_diag_registry.h`
- 测试：`tools/diag/checks/check_diag_contract_symbols.py`

- [ ] **步骤 1：编写失败门禁**

```python
required = {
    "include/common/diag/diag_types.h": ["DIAG_ProviderState_e", "DIAG_CommandMeta_t"],
    "include/common/diag/diag_provider.h": ["pfnCollectMeta"],
    "include/app/app_diag_registry.h": ["VSAPPDIAG_RegistryProviderOwnerUp"],
    "modules/app/include/app_diag_registry.h": ["VSAPPDIAG_RegistryProviderOwnerUp"],
}
```

- [ ] **步骤 2：运行门禁验证失败**

运行：`rtk bash -lc 'python3 tools/diag/checks/check_diag_contract_symbols.py'`
预期：`[FAIL] diag contract symbols gate`

- [ ] **步骤 3：补最小契约定义**

```c
typedef enum _DiagProviderState_e
{
    DIAG_PROVIDER_STATE_DOWN = 0,
    DIAG_PROVIDER_STATE_STARTING,
    DIAG_PROVIDER_STATE_UP,
    DIAG_PROVIDER_STATE_STOPPING,
    DIAG_PROVIDER_STATE_ERROR
} DIAG_ProviderState_e;

typedef struct _DiagCommandMeta_t
{
    const VS_CHAR *pcCommand;
    const VS_CHAR *pcOwner;
    DIAG_Layer_e enLayer;
    const VS_CHAR *pcSummary;
    const VS_CHAR *pcArgsSchemaJson;
    const VS_CHAR *pcExampleJson;
} DIAG_CommandMeta_t;
```

- [ ] **步骤 4：运行门禁验证通过**

运行：`rtk bash -lc 'python3 tools/diag/checks/check_diag_contract_symbols.py'`
预期：`[PASS] diag contract symbols gate`

- [ ] **步骤 5：Commit**

```bash
rtk bash -lc 'git add tools/diag/checks/check_diag_contract_symbols.py include/common/diag/diag_types.h include/common/diag/diag_provider.h include/app/app_diag_registry.h modules/app/include/app_diag_registry.h && git commit -m "feat(diag):扩展混合生命周期公共契约"'
```

---

### 任务 2：registry 落地 provider 状态机与双引用计数

**文件：**
- 创建：`tools/diag/checks/check_diag_registry_refcount.py`
- 修改：`modules/app/src/app_diag/framework/app_diag_registry.c`
- 修改：`include/app/app_diag_registry.h`
- 修改：`modules/app/include/app_diag_registry.h`
- 测试：`tools/diag/checks/check_diag_registry_refcount.py`

- [ ] **步骤 1：编写失败门禁**

```python
required = [
    "owner_ref", "ext_ref", "VSAPPDIAG_RegistryProviderOwnerUp",
    "VSAPPDIAG_RegistryProviderExternalUp", "VSAPPDIAG_RegistryProviderStateList"
]
```

- [ ] **步骤 2：运行门禁验证失败**

运行：`rtk bash -lc 'python3 tools/diag/checks/check_diag_registry_refcount.py'`
预期：`[FAIL] diag registry refcount gate`

- [ ] **步骤 3：实现状态表与迁移规则**

```c
typedef struct _AppDiagProviderRuntime_t
{
    VS_BOOL bInUse;
    VS_CHAR acProviderName[DIAG_MODULE_KEY_MAX_LEN];
    DIAG_ProviderState_e enState;
    VS_U32 u32OwnerRef;
    VS_U32 u32ExtRef;
    VS_S32 s32LastError;
} AppDiagProviderRuntime_t;
```

- [ ] **步骤 4：实现 API**

```c
VS_S32 VSAPPDIAG_RegistryProviderOwnerUp(const VS_CHAR *pcProviderName, const VS_CHAR *pcActor);
VS_S32 VSAPPDIAG_RegistryProviderOwnerDown(const VS_CHAR *pcProviderName, const VS_CHAR *pcActor);
VS_S32 VSAPPDIAG_RegistryProviderExternalUp(const VS_CHAR *pcProviderName, const VS_CHAR *pcActor);
VS_S32 VSAPPDIAG_RegistryProviderExternalDown(const VS_CHAR *pcProviderName, const VS_CHAR *pcActor);
VS_S32 VSAPPDIAG_RegistryProviderStateList(VS_CHAR *pcJson, VS_U32 u32Len);
```

- [ ] **步骤 5：运行门禁验证通过**

运行：`rtk bash -lc 'python3 tools/diag/checks/check_diag_registry_refcount.py'`
预期：`[PASS] diag registry refcount gate`

- [ ] **步骤 6：Commit**

```bash
rtk bash -lc 'git add tools/diag/checks/check_diag_registry_refcount.py modules/app/src/app_diag/framework/app_diag_registry.c include/app/app_diag_registry.h modules/app/include/app_diag_registry.h && git commit -m "feat(diag):registry落地provider状态机与双引用计数"'
```

---

### 任务 3：cmd_node 增加 catalog/help/version/provider-state 系统命令

**文件：**
- 修改：`modules/app/src/app_diag/ipc/app_diag_cmd_node.c`
- 修改：`modules/app/src/app_diag/framework/app_diag_dispatcher.c`
- 测试：`modules/app/src/app_diag/ipc/app_diag_cmd_node.c`（`rg` 静态断言）

- [ ] **步骤 1：编写失败断言**

```bash
rtk bash -lc 'rg -n "diag\\.sys\\.catalog\\.run|diag\\.sys\\.help\\.run|diag\\.sys\\.version\\.matrix\\.run|diag\\.provider\\.state\\.list\\.run" modules/app/src/app_diag/ipc/app_diag_cmd_node.c'
```

预期：改造前命中不足或无命中。

- [ ] **步骤 2：新增 handler 与命令表注册**

```c
{"SYS", "diag.sys.catalog.run", _DIAGCMD_SysCatalog},
{"SYS", "diag.sys.help.run", _DIAGCMD_SysHelp},
{"SYS", "diag.sys.version.matrix.run", _DIAGCMD_SysVersionMatrix},
{"SYS", "diag.provider.registry.state.list.run", _DIAGCMD_ProviderRegistryStateList},
{"SYS", "diag.provider.manager.state.list.run", _DIAGCMD_ProviderManagerStateList},
```

- [ ] **步骤 3：provider up/down 改走 registry external ref**

```c
s32Ret = VSAPPDIAG_RegistryProviderExternalUp(pstProvider->pcName, g_acDiagCmdIdentity);
s32Ret = VSAPPDIAG_RegistryProviderExternalDown(pstProvider->pcName, g_acDiagCmdIdentity);
```

- [ ] **步骤 4：重新断言命令命中**

运行：同步骤 1。
预期：4 个命令全部命中。

- [ ] **步骤 5：Commit**

```bash
rtk bash -lc 'git add modules/app/src/app_diag/ipc/app_diag_cmd_node.c modules/app/src/app_diag/framework/app_diag_dispatcher.c && git commit -m "feat(diag):新增catalog/help/version/provider-state系统命令"'
```

---

### 任务 4：API 通用 provider 改造为 Hybrid RefCount 幂等

**文件：**
- 修改：`modules/app/src/app_diag/provider/api/app_diag_api_event_provider.c`
- 修改：`modules/app/src/app_diag/provider/api/app_diag_api_msg_provider.c`
- 修改：`modules/app/src/app_diag/provider/api/app_diag_api_wifi_provider.c`
- 修改：`modules/app/src/app_diag/provider/api/app_diag_api_ws_provider.c`
- 修改：`modules/app/src/app_diag/provider/api/app_diag_api_tick_provider.c`
- 测试：`tools/diag/checks/check_diag_layer_deps.py`

- [ ] **步骤 1：写失败断言（refcount 字段不存在）**

```bash
rtk bash -lc 'rg -n "OwnerRef|ExtRef|RefCount" modules/app/src/app_diag/provider/api/app_diag_api_{event,msg,wifi,ws,tick}_provider.c'
```

- [ ] **步骤 2：补 provider 内部字段与锁**

```c
static VSHDIOS_MutexId_t g_u32DiagEventMutex = VS_INVALID_ID;
static VS_U32 g_u32DiagEventOwnerRef = 0U;
static VS_U32 g_u32DiagEventExtRef = 0U;
```

- [ ] **步骤 3：按 0->1 / 1->0 执行真实注册与清理**

```c
if (0U == (g_u32DiagEventOwnerRef + g_u32DiagEventExtRef)) { /* register */ }
if (0U == (g_u32DiagEventOwnerRef + g_u32DiagEventExtRef)) { /* unregister */ }
```

- [ ] **步骤 4：运行分层门禁**

运行：`rtk bash -lc 'python3 tools/diag/checks/check_diag_layer_deps.py'`
预期：`[PASS] diag layer dependency gate`

- [ ] **步骤 5：Commit**

```bash
rtk bash -lc 'git add modules/app/src/app_diag/provider/api/app_diag_api_event_provider.c modules/app/src/app_diag/provider/api/app_diag_api_msg_provider.c modules/app/src/app_diag/provider/api/app_diag_api_wifi_provider.c modules/app/src/app_diag/provider/api/app_diag_api_ws_provider.c modules/app/src/app_diag/provider/api/app_diag_api_tick_provider.c && git commit -m "refactor(diag):通用API provider改造为Hybrid RefCount"'
```

---

### 任务 5：修复 DVR owner 模块重复初始化（模块内 RefCount）

**文件：**
- 创建：`build/check_api_dvr_refcount.py`
- 修改：`modules/api/src/api_dvr/api_dvr_record.c`
- 测试：`build/check_api_dvr_refcount.py`

- [ ] **步骤 1：编写失败门禁**

```python
required = ["g_u32DvrInitRef", "g_u32DvrInitMutexId", "VSAPIDVR_RecordInit(", "VSAPIDVR_RecordDeInit("]
```

- [ ] **步骤 2：运行门禁验证失败**

运行：`rtk bash -lc 'python3 build/check_api_dvr_refcount.py'`
预期：`[FAIL] api dvr refcount gate`

- [ ] **步骤 3：在 `VSAPIDVR_RecordInit/DeInit` 增加 refcount 保护**

```c
static VSHDIOS_MutexId_t g_u32DvrInitMutexId = VS_INVALID_ID;
static VS_U32 g_u32DvrInitRef = 0U;
```

```c
/* Init: ref>0 仅++并成功返回；真实初始化仅在 0->1 */
/* DeInit: ref>1 仅--；1->0 执行真实反初始化；0 返回 VS_ERROR_INVALID_STATE */
```

- [ ] **步骤 4：运行门禁验证通过**

运行：`rtk bash -lc 'python3 build/check_api_dvr_refcount.py'`
预期：`[PASS] api dvr refcount gate`

- [ ] **步骤 5：Commit**

```bash
rtk bash -lc 'git add build/check_api_dvr_refcount.py modules/api/src/api_dvr/api_dvr_record.c && git commit -m "fix(dvr):RecordInit与DeInit引入模块内RefCount防重"'
```

---

### 任务 6：CLI 收敛为 discover-first（薄入口）

**文件：**
- 修改：`cli/cli.c`
- 测试：`cli/cli.c`（`rg` 静态断言）

- [ ] **步骤 1：新增失败断言**

```bash
rtk bash -lc 'rg -n "diag help|diag\\.sys\\.catalog\\.run|diag\\.sys\\.help\\.run" cli/cli.c'
```

- [ ] **步骤 2：增加帮助与目录入口**

```c
/* diag help */
"diag.sys.catalog.run {}"
/* diag help <command> */
"diag.sys.help.run {\"command\":\"...\"}"
```

- [ ] **步骤 3：更新 usage，弱化硬编码业务子命令说明**

```c
DBG_INFO("  %s diag help [diag.command]", pcProgName);
DBG_INFO("  %s diag run <diag.command> [json]", pcProgName);
```

- [ ] **步骤 4：断言新增入口已生效**

运行：同步骤 1。
预期：关键字符串全部命中。

- [ ] **步骤 5：Commit**

```bash
rtk bash -lc 'git add cli/cli.c && git commit -m "refactor(cli):收敛为discover-first薄入口"'
```

---

### 任务 7：汇总门禁接入与执行归档

**文件：**
- 修改：`tools/diag/checks/check_diag_phase6_static.py`
- 创建：`docs/reports/2026-05-10-diag-v4-hybrid-refcount-execution-notes-report.md`
- 测试：`tools/diag/checks/check_diag_phase6_static.py`

- [ ] **步骤 1：把新增门禁纳入 phase6 脚本**

```python
{"name": "diag_contract_symbols_gate", "cmd": [PY, "tools/diag/checks/check_diag_contract_symbols.py"]},
{"name": "diag_registry_refcount_gate", "cmd": [PY, "tools/diag/checks/check_diag_registry_refcount.py"]},
{"name": "api_dvr_refcount_gate", "cmd": [PY, "build/check_api_dvr_refcount.py"]},
```

- [ ] **步骤 2：执行总静态门禁**

运行：`rtk bash -lc 'python3 tools/diag/checks/check_diag_phase6_static.py'`
预期：`[Phase6] static verification passed`

- [ ] **步骤 3：写执行归档文档**

```markdown
# Diag V4 Hybrid RefCount 实施归档
- 完成：契约、registry、cmd_node、provider、DVR、CLI
- 门禁：phase6 static pass
- 待做：APP/PT 联调运行验证
```

- [ ] **步骤 4：Commit**

```bash
rtk bash -lc 'git add tools/diag/checks/check_diag_phase6_static.py docs/reports/2026-05-10-diag-v4-hybrid-refcount-execution-notes-report.md && git commit -m "docs(diag):归档V4混合生命周期实施结果"'
```

---

## 自检

### 1. 规格覆盖度
- `Hybrid + RefCount`：任务 2、4、5 覆盖。
- Event/Msg/WiFi 类可外控且防重复：任务 4 覆盖。
- CLI 膨胀与自发现：任务 3、6 覆盖。
- 分层版本清单：任务 3（命令入口）+ 任务 2（registry 输出）覆盖。
- 代码规范与门禁：任务 1、7 覆盖，且全程受 `$EMBEDDED_KNOWLEDGE_HOME/docs/standards/c-coding-standards.md` 约束。

### 2. 占位符扫描
- 无 `TODO`、`待定`、`后续实现` 作为执行步骤占位。

### 3. 类型一致性
- 统一术语：`owner_ref/ext_ref/init_ref`。
- 统一命名前缀：`VSAPPDIAG_Registry*`、`VSAPPDIAG_Api*Provider*`、`VSAPPDIAG_Hdi*Provider*`。
- 统一响应结构：`{"code","msg","data"}`。
