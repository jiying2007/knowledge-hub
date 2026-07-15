# Knowledge Hub Home

本页是 Obsidian 和普通 Markdown 阅读器的首屏导航。状态、owner、review_after 和授权仍以 registry 与 Hub gate 为准。

## 日常入口

- [Knowledge Hub README](../README.md)
- [当前产品状态与证据缺口](../governance/product/validation/project-readiness.md)
- [Obsidian 集成边界](../governance/obsidian-integration.md)
- [全面成熟度治理审计](../artifacts/manifests/knowledge-hub-comprehensive-maturity-remediation-20260713.md)
- [索引维护说明](README.md)
- [按主题浏览](by-topic.md)
- [按项目浏览](by-project.md)
- [按决策浏览](by-decision.md)
- [按状态浏览](by-status.md)
- [按复核日期浏览](by-review-date.md)
- [30 项目成熟度工作台](project-readiness.md)
- [项目成熟度 Base](obsidian/project-readiness.base)
- [Reviewing Base](obsidian/reviewing.base)
- [Active 知识 Base](obsidian/active-knowledge.base)

## PCR02

- [PCR02 项目入口](../projects/pcr02-ssc305/README.md)
- [第三方库编译优化基线](../projects/pcr02-ssc305/current/runbooks/thirdparty-build-optimization-baseline.md)
- [项目构建与部署指导](../projects/xcrz-sigmastar-demo/current/runbooks/project-build-and-deploy-guide.md)
- [终端发布验证记录](../projects/xcrz-sigmastar-demo/validation/reports/2026-05-14-prog-tool-terminal-release-report.md)
- [历史归档入口](../projects/pcr02-ssc305/archive/README.md)
- [ST77912 SPI/FPS 决策候选](../projects/pcr02-ssc305/decisions/st77912-dual-screen-spi-clock-fps-decision-20260711.md)
- [ST77912 framebuffer 边界候选](../projects/pcr02-ssc305/decisions/st77912-fb-mi-fb-boundary-decision-20260711.md)
- [owner-ready 验证路径](../artifacts/manifests/pcr02-owner-ready-validation-paths-20260713.md)

## 跨项目知识

- [嵌入式 ASAN 调试方法论](../domains/embedded/runbooks/asan-debug-guide.md)
- [嵌入式 Linux 性能排查](../domains/embedded/runbooks/embedded-linux-performance-triage-guide.md)
- [知识贡献规范](../domains/embedded/standards/knowledge-contribution-guide.md)
- [Codex archive 边界](../domains/codex/archive/codex-archive.ref.md)
- [专利附件引用边界](../domains/patents/artifacts/patent-disclosure-artifacts.ref.md)

## 捕获与检查

- [Inbox 笔记模板](../templates/inbox-note.md)
- [Knowledge Hub 项目画像](../governance/product/current/project-profile.md)
- [Knowledge Hub 维护入口](../governance/product/current/runbooks/maintenance-entry.md)
- [Knowledge Hub 当前产品状态与证据缺口](../governance/product/validation/project-readiness.md)
- 链接检查：`rtk bash ~/knowledge-hub/tools/knowledge-link-audit.sh --json --strict`
- 产品检查：`rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --as-of 2026-07-13`

## 安全提醒

- `active`、owner decision、promotion 和 release 不能由 Obsidian 页面或 Graph 推断。
- 新附件先进入 [inbox/attachments](../inbox/attachments/README.md)，不要直接写入 `artifacts/vault/`。
- 普通阅读不需要打开 `registry/`、`artifacts/manifests/`、`sources/` 和 `tools/`。
- `.base` 只查询 Markdown properties；视图结果不产生 owner decision、promotion 或 active 状态。

<!-- knowledge-hub-obsidian-views:start -->
## Obsidian MOC 与只读视图

- [项目 MOC](obsidian/projects.md)
- [主题 MOC](obsidian/topics.md)
- [项目成熟度 Base](obsidian/project-readiness.base)
- [Reviewing Base](obsidian/reviewing.base)
- [Active 知识 Base](obsidian/active-knowledge.base)
<!-- knowledge-hub-obsidian-views:end -->
