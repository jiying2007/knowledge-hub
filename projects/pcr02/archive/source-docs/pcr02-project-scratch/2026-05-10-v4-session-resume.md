# V4 终态会话接力摘要（2026-05-10）

## 当前目标
推进 V4 终态：去聚合、按 owner 生命周期管理 provider，清理直接 Init/DeInit 共享资源行为，文档与实现闭环一致。

## 已完成（关键）
1. cmd_node provider 策略收紧：owner 管理 provider 禁止外部 `diag.provider.up/down` 控制（返回 `provider_owner_managed`）。
2. APP_UART 生命周期 owner 化：`VSAPPUART_Init/DeInit` 自动挂接 `VSAPPDIAG_UartProviderModuleUp/Down`。
3. `hdi.vi` 已拆分为独立 owner provider：新增 `hdi_diag_vi_provider.[h/c]`，命令从 `HDI_TEST` 聚合 provider 移出。
4. `hdi.vi` 生命周期挂接：`VSHDIVI_Init/DeInit` 成功路径调用 `VSHDIDIAGVI_ModuleUp/Down`。
5. `api.dvr` owner 生命周期已确认：`VSAPIDVR_RecordInit/DeInit` 调用 `VSAPIDIAGDVR_ModuleUp/Down`。
6. 文档同步：07/08/10 及 phase6 验证文档已补充 phase-7 进展与 owner 管理策略。
7. 静态检查通过：
   - `python3 build/check_diag_naming.py`
   - `python3 build/check_diag_layer_deps.py`

## 仍需推进（V4 终态缺口）
1. 继续拆分 `HDI_TEST/API_TEST` 聚合 provider 余项（如 `hdi.ai`、`hdi.ao`、API 聚合残留）。
2. 清理聚合 provider 中“直接 Init/DeInit 共享资源”路径，改为只调用 owner 已就绪能力。
3. 聚合 provider 彻底下线后，从 cmd_node provider 表移除 `HDI_TEST/API_TEST`。
4. 同步更新 07/08/10 与 phase6 文档为“终态完成”。

## 本轮关键文件（供快速定位）
- `modules/app/src/app_diag/ipc/app_diag_cmd_node.c`
- `modules/app/src/app_uart/app_uart.c`
- `modules/hdi/src/hdi_video/hdi_vi.c`
- `modules/hdi/src/hdi_video/hdi_diag_vi_provider.c`
- `modules/hdi/src/hdi_debug/hdi_diag_test_provider.c`
- `modules/api/src/api_dvr/api_dvr_record.c`
- `docs/project/07_diag_command_architecture_v4.md`
- `docs/project/08_diag_command_architecture_v4_development_plan.md`
- `docs/project/10_app_tool_function_migration_checklist.md`
- `docs/project/10_diag_command_architecture_v4_phase6_verification_release.md`

## 下一步建议（按顺序）
1. 拆 `hdi.ai` 为 owner provider 并挂接 owner 生命周期。
2. 拆 API 聚合残留模块（优先 dvr 以外仍在 `API_TEST` 的分支）。
3. 删除 `HDI_TEST/API_TEST` 在 cmd_node 的注册项，完成聚合 provider 退场。
4. 跑静态门禁并更新文档归档为 V4 终态完成。

## Resume Prompt
继续推进 V4 终态：先拆 `hdi.ai` 与 API 聚合残留为 owner provider，并清除聚合 provider 直接 Init/DeInit 行为；完成后下线 `HDI_TEST/API_TEST` 并同步 07/08/10 + phase6 文档。
