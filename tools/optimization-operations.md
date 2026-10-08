# 写入、验证与复核运营契约

这些入口维护本地工具与证据，不代替 owner approval、active 提升、生产采用或设备验收。

## 写入一致性

准备派生内容前调用 `snapshot_inputs`，将原始读取身份传入 `RepositoryTransaction(expected_inputs=...)`。已有读取快照优先于内容生成后取得的 hash；新目标必须在快照中确实不存在。并发冲突需重新读取和生成，不重复提交旧内容。operator apply/rollback 使用其已审阅计划的准确 before hash，不能用较晚 hash 替代。

活动回执默认使用规范化内容的完整 SHA256 生成身份，文件 basename 不再是唯一身份。同一内容重试不重复写入；不同内容保留独立记录。调用方可提供明确 `receipt_id` 或 `session_id`，同身份不同内容返回冲突。需要修订时使用明确 `receipt_id` 和 `--expected-sha256`，并发修订通过比较当前 hash 防止覆盖。活动 item 和快速 record 也拒绝静默覆盖。

dry-run 与 apply 都校验修订 CAS；旧回执按原 hash 保存在私有 revision history。相同 subject/project/item 的不同事实默认返回 needs-review 冲突，不能用文件名顺序决定状态。明确修订须提供 `revision`、后继 `supersedes_sha256` 和带时区的 `observed_at`。汇总支持 `--knowledge-as-of`，按观察时间重放；没有观察时间的事实不混入历史视图。receipt 的 `item_fingerprints` 可作为下一版本的前驱身份。

输出目录为 0700、文件为 0600；原子写后同步目录并回读 hash。新增目录的权限由创建者负责。恢复审计对错误结构只报告 `invalid-journal` / `needs-recovery-review`，不删除或执行修复。

## Provider 受控执行

活动修订先解析全部可见事实链，再按业务日期投影到报告期间；跨天前驱不会因日期过滤而丢失。孤立后继返回 `lineage-unknown`，缺前驱、多头、无合法观察时间等冲突继续进入 needs-review，不将唯一剩余记录误当完整链。

本仓的受控入口仅调用公开 Provider Adapter；默认只生成计划。

```bash
rtk bash ~/knowledge-hub/tools/knowledge-capture.sh --governed-provider --source /tmp/sanitized-conclusion.md --project knowledge-hub
rtk bash ~/knowledge-hub/tools/knowledge-capture.sh --governed-provider --provider-operation activity-capture --source /tmp/activity-receipt.json
```

明确需要持久化时添加 `--apply`。该入口冻结输入、调用 Provider dry-run、登记真实 plan/dry-run 身份、检查当前线程 apply gate，然后执行并核对输出 hash。任何门禁非零都短路；中途源码输入变化需重新计划。门禁仍要求已有 repo/build 等证据，入口不会伪造它们。Provider 成功与 Runtime final 仍是不同验收线。

阶段日志记录 planned/gated/applied/verified/unknown，并绑定 plan hash 和 operation identity。apply 已调用但超时、JSON 无效或回读失败时返回 needs-recovery-review，applied 为 null，自动尝试只读对账，禁止盲目重试。对账可独立复跑：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-capture.sh --governed-provider --reconcile-plan PLAN_SHA256
rtk bash ~/codex/scripts/knowledge-provider.sh archive --project knowledge-hub --reconcile-operation OPERATION_SHA256 --expected-content-sha256 CONTENT_SHA256 --json
rtk bash ~/codex/scripts/knowledge-provider.sh activity-capture --reconcile-receipt RECEIPT_ID --receipt-date YYYY-MM-DD --expected-content-sha256 CONTENT_SHA256 --json
```

VERIFIED 表示可见内容与准确身份一致；对账不会补造耐久成功回执，也不会关闭 owner gate。Provider 已明确成功而附加阶段日志失败时，保留真实成功并单列 journal_status=needs-review。

阶段状态机要求 `planned → gated → applied → verified`，从 gated/applied 可进入 unknown。相同当前阶段重复登记幂等；不得跳阶段、倒退或从 unknown 继续 apply。每份计划固定 `attempt_generation=1`；新尝试必须重新计划，不复用未知结果日志冒充新 generation。只读对账不自动重试写入。

命令执行创建独立进程 session，超时只回收自有进程组。stdout/stderr 各保留最多 8 MiB，超预算返回失败而非截断后假装 JSON 完整。

执行 deadline 同时覆盖父进程退出与输出管道 EOF。父进程正常退出后，后代仍持有输出管道也不能视为采集成功；未设置 timeout 时，退出后最多等待 1 秒排空。非阻塞采集不创建 drain 线程，失败关闭调用方持有的管道并保留有界部分输出。TimeoutExpired 的 output_incomplete=true 表示采集未完成；只清理自有进程组，不声明已终止另建 session 的后代。

进程回收由执行器独占，依赖 Linux waitid/WNOWAIT 保留父进程身份；不支持外部 reaper 并发回收同一子进程。检测到 ChildProcessError 时显式失败并关闭自身管道，不再向已失去身份保证的进程组发信号。

## 检查依赖和测试委托

engineering 输出 kernel/content/views/retrieval/delivery 指纹。仅 ruff、mypy、bandit 使用输入完全匹配且不超过 24 小时的成功缓存；测试、coverage、full regression 依赖实际仓库内容，继续按 exact delivery 验证。build 和依赖漏洞审计每次执行。最终结果仍验证整个工作区在运行前后未变化，不以组件缓存刷新旧终态证据。

kernel 包含根目录及子目录 Python/stub 文件和根配置。mypy 配置插件、mypy_path 或环境 MYPYPATH 时禁用缓存，直到依赖闭包可证明。错误 timestamp 或缓存结构视为 miss。

full 默认在短持锁阶段捕获 Git 可见文件的完整 dirty overlay、HEAD、逐文件 hash，然后在私有临时快照运行检查；测试期间不占用 Provider 写锁。声明的 local/workspaces.json、local/activity-report.json 作为独立 host input，不是发布源码。结果分别显示 captured source 与当前 live source；live 变化时，快照通过不代表 live 已验证。`--in-place` 仅用于明确选择原树诊断。snapshot manifest 保存在私有 `.tmp/engineering/`。

本地clone的origin默认指向源目录，不能用它替代源仓的已注册路由。快照只恢复源仓经registry匹配的origin，拒绝credential/query/fragment，并在Git忽略的host配置加入绑定HEAD的snapshot view；原始host输入hash和effective workspace hash分别记录，不授予owner身份或批准。未注册源仓不猜测路由。

`KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1` 只表示递归调度，不能证明外层测试通过。没有新鲜父测试证据时返回 delegated-unverified/exit 77，产品 shared_unit_tests 不通过，不写正式快照。engineering 在完整 pytest 成功后记录真实父 run、准确源码/测试集身份与结果 hash；消费时复验这些字段及24小时有效期，作为 passed-reused 使用。临时夹具不能复制父运行缓存或把源树不匹配的证据升级为通过。

## 检索评估

第三轮 full 先执行低成本 contract/schema/真实 CI transport 预检，再捕获独立 Git 对象与完整 dirty overlay；`--no-hardlinks` 不依赖源仓对象库。CI 委托通过固定 `rtk bash -lc` 环境语法执行，标志仍不构成父测试证据。失败报告保留阶段、退出码、超时与分类；契约错误不得自动重跑完整工程。

失败快照保存在私有 `.tmp/engineering/failure-snapshots/`，保留建议为30天且 report-only。manifest 绑定版本、HEAD、源码签名、逐文件 hash/size、host 原始身份与路由身份；host 配置正文不进入保留副本。回放须提供原始 host hash，在私有临时副本运行，结束后不会在保留副本留下 host 正文或新测试结果；回放不能认证 live source。

```bash
rtk bash ~/knowledge-hub/tools/knowledge-engineering-check.sh --mode full --replay .tmp/engineering/failure-snapshots/EXACT_DIRECTORY --summary-json
```

`retrieval_holdout.json` 已用于规则选择，身份为 development-regression。新增 `retrieval_unseen.json` 在评估前冻结，作为跨项目与问题类型的工程验证集，不能在失败后改 gold 或用它调参。它仍为人工构造案例，production_derived=false，不用于补足真实生产案例数量。

```bash
rtk bash ~/knowledge-hub/tools/knowledge-retrieval-benchmark.sh --holdout --cases ~/knowledge-hub/tests/fixtures/retrieval_unseen.json
```

报告绑定 dataset/cases/source/evaluator 身份，并分别报告原始查询与边界规范化的 shadow 结果。规范化仅移除明确问句前后缀，名词内部的“的/和/与”、技术标识和否定保持原样。工程评估失败是待优化项，不自动改变默认检索策略。

holdout 尊重 top-k 和全部阈值；默认 report-only 退出0，显式 `--quality-gate` 时质量失败退出1。`--summary-json` 只输出有界摘要。开发集可加 `--diagnose` 输出脱敏问题 hash、匹配 term 数量、返回身份、失败类别和下一步，不持久化原始问题 token 或正文；冻结验证集拒绝开发诊断。开发失败项转为回归后，新的独立评估者须在策略冻结后收集和审查新的问题，冻结案例 hash；禁止将已用于调优的案例再声明 unseen。

## 复核消费与观测

owner packet 按 current-validity/candidate-decision/historical-integrity 轮流选择，默认批量和 owner WIP 上限均为10，每轮有内容的 lane 都获得名额。逾期30天候选标为 cold，并在候选 lane 内提高优先级；每行明确负责 owner 和下一步。记录 accepted/deferred/changes-requested 后，只有 body 与 cycle hash 均匹配、且未到期的记录会暂时排除；正文、owner、状态、review_after、证据或风险政策变化自动重开。accepted 最多30天有效，也受下一复审日期约束。deferred 必须提供未来日期。legacy 或损坏消费记录不阻断重新审查，并单列 needs-review。accepted 仅代表 packet 消费，不改变 registry 状态或 owner gate。

```bash
rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --consume-item ITEM --decision deferred --reviewer REVIEWER --evidence-ref EVIDENCE --body-sha256 SHA256 --next-review-at YYYY-MM-DD
```

真实复核完成后添加 `--apply`，可提供 `--review-seconds`。准备耗时与真实审阅耗时分别统计；未实际复核不得自动填 accepted 或 reviewer 身份。

去重先排除自身，再进行 top-k；相同标题与 metadata overlap 仅作提示，正文指纹相同仍需 scope/version 匹配，永不自动合并。trace ledger 上限4 MiB，超过时返回非阻断 budget-exceeded；保留30天的清理建议为 report-only。operation/item/transaction 身份只用于 trace关联，SLO 按固定类型、状态与阶段汇总，不以每个条目生成指标标签。

archive 和 review packet 均使用真实正文生成去重指纹。runtime-maintenance 的 artifact_catalog 覆盖活动回执及修订、消费状态、工程证据、受控计划和查询 trace；有文件/字节上限与 overflow 提示。unknown/pending 操作和权威事实保持保护。新增类别的保留建议全部 report-only，既有清理 apply 也不会删除这些新类别。

目录预算优先枚举受控操作，再按类别轮流分配名额；类别状态保留 examined/files/bytes/unknown/scan_complete，其中 unknown 统计不可读条目或无法解析的操作状态。合法 stage=unknown 的操作在 rows 中标为 pending-or-unknown-operation，不计入该读取异常计数。预算不足时明确 overflow，摘要也暴露该状态。预算小于类别数量时不能声称所有类别已扫描。

复核消费除当前库存外追加 metadata-only 事件，调用方可使用 `--review-event-id` 重试同一事件；同身份不同内容冲突。期间指标仅统计 recorded events 的决定次数、独立条目和实际审阅时长；重开是当前库存统计，真实复用需独立证据，二者不冒充期间吞吐。未真实审阅不得自动生成 accepted、reviewer 或时长。

未显式指定 event ID 时，默认身份包含日期，跨天操作会形成新事件。跨天恢复须继续使用原先传入 CLI 的 `--review-event-id`，不得将返回的事件 hash 当成原始 CLI ID。消费状态保留 pending outbox；重试先恢复同一待发布事件，旧事件回放不覆盖较新消费状态。`PrivateWriteUncertain` 表示写入结果待核验，CLI 返回 `applied:null`、`needs-recovery-review` 和退出码3，不将它当作未写入而另造新事件。

## 第四轮验收与恢复契约

受控 Provider apply 使用本机同 plan 非阻塞执行锁，锁覆盖阶段日志、Runtime gate、实际调用及最终回读；竞争者返回 `blocked/applied=false`，不进入实际 apply。锁不授予新权限，也不提供跨主机 exactly-once。unknown 阶段仍须先只读对账，不能因锁已释放就重新写入。同阶段幂等登记会再次确认 fsync/readback，未确认耐久性继续报告不确定。

复核 packet 和写入使用相同 stock/pending outbox 校验。损坏文档或待发布事件显式返回 needs-review 与 pending 计数，不能当成正常库存或期间吞吐 PASS；合法 legacy 文档仍可读取。

子进程超时先回收自有进程组并排空输出，再保留有界 stdout/stderr、timeout 和截断标识。工程报告仅保留尾部，超时仍 FAIL 且不默认重试。该诊断不证明此前失败的根因，也不构成成功回执。

评估样本的身份必须唯一，字段类型和数量有界；同一相关文档按 ID/path 标注时按 canonical 身份归并。禁止结果命中和无答案负例错误返回单独阻断质量门禁，不能被总体命中率稀释。排序指标仅统计可回答的正例，负例拒绝率及其分母另行报告；既有阈值不降低，旧新口径不能直接视为同一指标比较。

评分保留 title/summary 等字段区别，对完整且具有区分度的摘要匹配增加受限相关性信号；泛词和仅正文匹配不获得该信号。候选入口、authority 过滤和生命周期资格保持原契约，摘要匹配不能授权原本不可见的内容。

coverage 恢复只在覆盖数据错误被明确分类、且本轮 pytest 与完整回归都已真实通过时执行一次有界重采。低于覆盖门槛、超时、信号终止或未知错误直接失败，不重复昂贵测试。分类优先检查所有尝试的结构化超时及负返回码，不因尾部“无数据”文字覆盖这些事实。嵌套回归因递归保护而跳过的案例单列 skipped/delegated，不能计为真实 PASS；没有相应执行证据时不能宣称完整回归已执行。

## 第五轮概念检索与证据准备

自然问题使用受控 title/summary 与正式 project route 别名生成有界概念计划，同一计划用于召回、评分和开发诊断。保留原句、否定、技术标识及未知实体约束；字段镜像不能冒充主题内容。原权限、生命周期过滤和质量/性能阈值仍生效，budget失败不会升级为无界fallback扫描。

默认策略 generation 为 `knowledge-retrieval-implementation-20261008-v5`。旧 generation 的交互保留历史usage，但不计入新策略的性能或生产资格；不重标旧事件。开发集可以复用已曝光问题并明确标记 used_for_tuning=true；独立新冻结集首次结果必须分列，不能据开发PASS宣称泛化。

复核报告包含有界 `evidence_triage`：将正文hash/元数据准备、current与retired来源、引用类型、缓存年龄/身份和真实owner/语义阻塞分开。`metadata-ready`不代表完成复核；指令和provenance说明不自动执行，也不应作为不存在的文件处理。retired只作历史provenance，不恢复active路由。报告保留warning-equivalent集合与更大的历史/近期队列区别。

```bash
rtk bash tools/knowledge-review-after.sh --json --triage-limit 100
rtk bash tools/knowledge-engineering-check.sh --preflight --summary-json
```

能力预检在普通full、in-place及replay进入昂贵检查前验证实际解释器、临时loopback socket权限及PyPI DNS。probe子进程最多8秒；不启动HTTP服务、不发依赖HTTP请求，不保存DNS地址。DNS成功不证明HTTPS、漏洞审计或完整测试通过。blocked时返回明确环境原因和expensive_checks_started=false；须按执行权限规则在可用环境验证，不能关闭测试或修改门槛。`--preflight`不写完整工程成功缓存。

## 第六轮比较检索与复核建议

已登记项目的通用比较或共享规范问句可同时召回项目材料与团队通用的 standard/architecture/runbook。共享评分去除该项目 anchor 的贡献，保留技术标识与未知主体约束；明确的 domain/owner/status/source 等过滤先执行。纯项目问题、其他项目、个人材料与不可检索内容保持原有约束。该能力依赖有界词法意图识别，不能承诺任意语义问法覆盖。

每次查询一次编译词变体与匹配规则，匹配结果仅在当前文档中复用。两条候选通道共享 SQLite 读取快照，各自保持原 cutoff/顺序及预算；唯一正文按批读取一次，不引入跨查询正文缓存。诊断和预览使用实际候选概念，原始与有效词数分别可见。

复核建议中的 owner-ready 需要明确正向审阅、内容 accepted、经验证证据及与当前正文相符的审阅 hash；拒绝、未知、陈旧或未验证的声明不能获得此建议。建议不执行 owner 决定。正文确认读取也计入共享字节预算，预算耗尽时报告 overflow，不能把未确认内容列为 metadata-ready。

产品门禁的实际命令任务超时仍判为失败，并输出有界部分诊断和明确的超时状态；保持原命令 deadline，不将不完整输出或超时测试计为通过。该处理仅覆盖已知命令超时，其他编程异常继续暴露。回归的最终门禁调用保留有界 stderr，方便区分协议中断、环境失败与业务阻断。缺少原始 stderr 时保留未知根因，不因一次复跑通过而回写旧失败为成功。

## 第七轮中文问句与比较投影

普通中文语法、数词量词和谓语描述与主题概念分别处理；登记 alias 在语法处理前保护，明确项目、设备、产品和技术主体继续作为约束。名词中的歧义单字不被任意删除，原句否定信息保留。概念与主体分类不生成答案词，不以普通 corpus topic 证明项目存在；无有效主题继续零结果。

明确的团队通用规范与项目资料比较按原句子句生成两侧有效计划，未知主体和技术约束跨投影保留，显式过滤仍先执行。技术“共享内存”不表示团队共享规范。规范性意图与实操步骤仅对已经通过准入和评分的结果调整顺序，选择理由可见；这不能证明文档已获 Owner 审阅。

有限语法不保证嵌套引语、复杂指代或任意同义表达。开发回归、冻结首测与真实使用指标分开记录；语义改善可能增加实际候选评分成本，不能仅据一次离线 P95 宣称性能全面改善。

复核报告的可选 `evidence_triage.owner_preparation` 使用 `knowledge-hub.review-preparation/v1` 版本标识，复用已有证据读取结果，按登记 Owner 路由同时准备条目与来源事项。每包大小复用 `--batch-size`，总量复用 `--triage-limit`；同一 Owner 可有多个包。使用 `--triage-limit 500` 请求较大有界批次，实际 `selected`、`remaining` 和 `overflow` 决定覆盖程度。

交接投影的 canonical JSON UTF-8 上限为 48KiB，Owner/包数量及每包条目数均有上限；pretty-print 的缩进不计入 canonical 预算。只含实体身份、既有日期、仓库内安全路径、hash、准备状态和引用类别计数，不复制正文、raw URL、命令或原始 origin 路径。超预算如实保留剩余数。声明路由不代表分派或实际签收，`real_signer_confirmed=false`；retired 来源仅准备历史 provenance 决定，不能启用原源探查或恢复 active。summary 同样受此元数据预算约束。

## 第八轮已准入信息覆盖

明确主体与已登记项目的排除约束先于自然问句识别执行，句末标点不决定是否保留边界。正向与否定列表共用有界主体语法，支持明确的英文/中文命名 head 及 inline `project:` 主体提示；后者不是新增结构化过滤 DSL。被否定的项目 alias 不再进入正向项目域，候选在评分前排除相应域。中文名称与 head 之间只接受闭合描述符，不将任意动作词当作实体修饰。普通关键词及已登记项目的正向请求仍需独立回归验证。

发现量词、把字处置、整段/整篇及前后条件等闭合语法与真实命名分开；明确规范子句不依赖固定“团队”前缀。已验证 metadata 语料中的域内主题关联仅用于成功双层投影的各侧主题划分，不能证明 alias 登记或解除明确实体约束。

literal 标题/版本焦点和规范文档形态仅参与已准入结果排序，使用该候选实际有效通道的主题；枚举多个组件不能把末项当唯一焦点，通用规范意图也不能污染项目侧排序。按多份相关信息覆盖评价，不用首个 hit 冒充完整回答。

章节替换声明需要独立、有界、经校验的关系索引与 companion 准入契约。当前检索不能仅凭 frontmatter 关联放松技术 literal 或主体约束；该缺口保留，不以文档目标 ID 或相关性打分特判。
