# patent-disclosure-skill 归一化对比与改动点

## 读取依据

本轮已拉取并读取 `https://github.com/handsomestWei/patent-disclosure-skill`，版本入口显示为 `patent-disclosure-skill`，`version: "1.8.9"`。重点对照文件包括：

1. `SKILL.md`
2. `prompts/disclosure_builder.md`
3. `prompts/template_reference.md`
4. `prompts/disclosure_self_check.md`
5. `prompts/iteration_context.md`
6. `prompts/merger.md`
7. `prompts/prior_art_search.md`
8. `tools/README.md`

## 供应链与执行边界

1. 仓库为公开 GitHub 仓库，README 标注 MIT license。
2. 本轮只将其作为模板与流程参考读取，未安装到 `~/.codex/skills`，未修改 Codex live skill。
3. 已在 `/tmp/patent_skill_venv` 中补齐 Playwright/Chromium，重新执行国知局公布公告检索脚本；三个关键词均在约 120 秒处超时，因此 1.1 仍按该 skill 的降级规则使用公开 Web/Google Patents/Linux MTD/AOSP 资料。
4. 已在 `/tmp/patent_skill_venv` 中补齐 `python-docx`、`matplotlib==3.7.5`、Playwright 等 Python 临时依赖；未写入仓库依赖或全局 Python 环境。
5. 已在 `/tmp/patent-disclosure-skill/tools` 执行 `npm install`，本地 `mmdc` 极简图示测试通过；`npm audit` 提示 6 个 moderate 和 1 个 high 漏洞，本轮仅作为临时转换工具使用，未引入项目依赖。

## 与上一版相比的主要改动

1. **按 skill 六章结构重排交底书**：三篇交底书均调整为“注意事项、一、现有技术、二、技术问题、三、技术方案、四、优点、五、保护点、六、其它”。
2. **补齐 1.1 公开源 URL**：每篇交底书均新增检索说明和公开源表格，列出可访问链接、技术方案概括和局限性。
3. **补齐 mermaid 图示要求**：每篇交底书均保留 3.2 系统框图和 3.4 系统流程图，使用 fenced `mermaid`，未使用 ASCII 框图。
4. **补齐 3.4.1 符号与公式**：三篇均增加符号表和关键公式，且 3.5 参数表的符号列与 3.4.1 保持同形。
5. **补齐 3.5 关键技术参数**：三篇均新增参数表，支撑代理人理解公式和实施例。
6. **正文去除内部流程元信息**：交底书正文未写入 `patent-disclosure-skill`、脚本名、WebSearch 降级等内部执行细节。
7. **保留新时间戳交付并清理旧稿**：本轮规范化产物统一使用 `20260530204854` 时间戳；`20260530190555` 三篇旧交底书、三篇旧权利要求草案和早期共享图片目录已按用户要求清理，仅在修订记录中保留过程说明。
8. **移除 OTA 成案并保留三件组合**：按用户最新要求，已从当前交付组合移除“只读客户区与可写数据区安全 OTA”相关 Markdown、Word 和 `figures_ota/` 图示目录。
9. **权利要求书单独规范化**：保留三份当前权利要求草案，均采用 `权利要求书_案件名_时间戳.md`，仍保持 1 项主权利要求 + 10 项从属权利要求。
9. **补充修订记录**：按 `iteration_context.md` 要求新增 `交底书修订对话记录.md`，记录本轮合并迭代。
10. **生成 Word 并补齐图示/公式渲染**：本轮已用 `mermaid_render.py` 为保留交底书生成同名 `.docx`；保留交底书的 mermaid 图示均已转为 PNG，公式已转为 PNG。为避免多篇共用 `fig_001.png`、`inline_001.png` 被后续文件覆盖，当前保留三件分别使用 `figures_eye/`、`figures_multisensor/`、`figures_behavior/` 独立图片目录。

## 本轮交付文件

### 技术交底书

1. `一种多源创作输入驱动的端侧轻量化眼神动画生成显示方法及系统_20260530154742.md`
2. `一种宠物机器人多传感器产测标定与诊断命令闭环方法及系统_20260530204854.md`
3. `一种宠物机器人端侧多模态陪伴行为自动编排方法及系统_20260530204854.md`

### 权利要求书

1. `权利要求书_一种多源创作输入驱动的端侧轻量化眼神动画生成显示方法及系统_20260530154742.md`
2. `权利要求书_一种宠物机器人多传感器产测标定与诊断命令闭环方法及系统_20260530204854.md`
3. `权利要求书_一种宠物机器人端侧多模态陪伴行为自动编排方法及系统_20260530204854.md`

## 未完全等同 skill 的事项

1. 国知局公布公告检索依赖已补齐，但站点/脚本访问三次均超时；已按该 skill 的降级规则使用公开 Web 和 Google Patents 等可核验来源。
2. 本轮未把第三方 skill 安装为 Codex live skill，仅作为参考仓库读取并执行其流程约束。
3. Node 侧 `npm install` 存在审计漏洞提示，因其只位于 `/tmp/patent-disclosure-skill/tools` 并仅用于本轮本地渲染，未纳入项目依赖；若未来要长期纳入工具链，应单独做供应链修复。
