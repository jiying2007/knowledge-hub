---
id: aispeech-devpath-port-review-20260921
title: 音频候选迁回开发路径与验证边界
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-devpath-port-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo
  source_sha256: b17d4ee4ddac0b9a8b4d6fda89678e7d1420bef35626f2d85d770af74f6c49e8
  temporary_source_retained: false
review_after: '2026-10-21'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- aispeech
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-devpath-port-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-devpath-port-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 61个候选文件迁回或核对一致，API回归及音频定向构建通过，整机链接受独立ToF改动阻塞
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# 音频候选迁回开发路径

2026-09-21，用户要求将隔离工作树中的音频集成结果迁回当前开发路径。

- 父仓本轮起点为 1b721ec8；API master 50831f6，HDI master 5d14ea2，APP master 4b2a317，与候选模块基线一致。AISpeech仍在 dev/audio_process 9ce7a7f，其既有算法修改完整保留；本轮未切换分支。
- 已迁入 API 6 个文件、HDI 5 个文件、APP 3 个文件，并核对 AISpeech 47 个文件。共 61 个相关文件与候选一致（比较时统一CRLF/LF和末尾换行）。
- 根 Makefile 补齐 API 公共头同步和产品直接构建依赖，其他已有音频构建增量保留。hdi/api/app/aispeech 公共头全量检查通过。
- API全套Host测试通过，包含新speech_profile_test。API/APP静态及动态库构建通过；HDI的hdi_ai、hdi_ao、ssplat_file三个音频对象验证通过。
- 三模块doctor/check通过。历史环境曾使用 `EMBEDDED_KNOWLEDGE_HOME`；此处仅保留 provenance，现行知识库路由以 `workspace://embedded-knowledge` 为准。
- 第一次产品构建被旧ToF .d文件引用已删除头文件阻塞。备份137个生成物后重新生成HDI对象和API/APP库。
- 第二次产品构建被期间新出现的ToF源文件修改阻塞：vl53l8x/vl53l8cx_api.c 新增78行、删除2行，引用未定义的VL53L8CX_GLARE_FILTER和Dev等标识。该文件不属于迁移补丁，未覆盖或修复；ToF两个未跟踪参考文件同样保留。
- 开发路径本轮没有完成新的prog_pcr02链接，不复用隔离工作树成功结果作当前构建结论。原HDI库已从备份恢复，仍是旧制品，不是本轮验证的新库。
- 生成物备份保留在会话临时目录，隔离工作树保留。本轮未commit/push/merge/rebase，未替换设备、未生成image/OTA。
- 后续：当前ToF改动自洽后重跑 `rtk make NC=1 pcr02_app_all -j4`，核对新产品身份再执行设备验证。

结论：源码迁回完成且定向验证通过，当前完整产品构建有独立ToF阻塞。
