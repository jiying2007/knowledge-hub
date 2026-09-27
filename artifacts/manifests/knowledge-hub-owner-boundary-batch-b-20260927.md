# Knowledge Hub Batch B owner 边界决定

- 决定人：`leiwenjun`
- 决定日期：`2026-09-27`
- 决定来源：本次 Codex 会话中，用户先说明“digital-worker 或 x5-rdk，leiwenjun，确认”，再明确“同时确认两个项目”。
- 执行身份：Codex 按用户上述明确决定机械绑定。
- 待决定事项来源：`https://github.com/jiying2007/knowledge-hub/issues/74#issuecomment-5856311155`
- Batch B 边界指纹：`sha256:dc489ba58eb9f8a1ff00773cc7cb601c281cada8cce2da0a2acab54f4863f1c1`
- 绑定前 owner packet：`sha256:089ecf7606c27f9b0911813fee9b461ed6e773f10013ad27fc43bdaaa140657e`
- 绑定基线：`master@64b9a3704d710c02795b27f605674d1db1df3385`
- 决定范围：仅确认以下两个项目的当前 owner 边界。

## digital-worker

- 项目类型：`git-repository`
- 仓库边界：`control-plane`
- 证据 profile：`software-tool`
- validation item：`digital-worker-readiness-validation-20260713`
- 决定：`leiwenjun` 接受上述 owner 边界。

## x5-rdk

- 项目类型：`product-group`
- 仓库边界：`group`
- 证据 profile：`embedded-target`
- validation item：`x5-rdk-readiness-validation-20260713`
- 决定：`leiwenjun` 接受上述 owner 边界，包含已登记的内部 `integration`、`manifest`、`vendor-docs` 源仓范围。

本决定仅绑定 owner 身份和边界。两份 validation item 继续保持 `reviewing`、`evidence_contract.status=pending`、`promotion=none`。本决定不产生或豁免 source、制品、设备、发布、回滚、provider、生产、采用或 ACL 证据；真实项目证据仍由 #96 跟踪。

## 本地验证快照

- `knowledge-check --dry-run`：通过，0 error；97 条既有复核日期警告。
- `pytest tests/test_owner_qualification_packet.py tests/test_project_readiness.py`：20 项通过。
- 绑定后 owner packet：`owner_declaration_pending=0`、`owner_boundary_pending=0`、`real_evidence_pending_project_count=25`；指纹为 `sha256:47db274e35c07e186ee2ca0a3ea96b6e7454a98c08ee91ffd7cdb6c4771b0087`。
- 本地 Product final gate 为 `needs-fix`：候选当时缺 committed-HEAD restore 证据，真实项目与远端交付证据也未齐。该结果不撤销上述 owner 决定。

#74 的远端状态以经审查的合并结果及 fresh master owner packet 为准；本记录不代替该评估。
