# Knowledge Hub 30 项 Owner 绑定落地审计（2026-07-16）

## 结论

Owner attestation 已按授权机械落地：120/120 个 readiness registry/frontmatter 镜像为 `decision_owner=leiwenjun`，30/30 个 validation contract 的 `owner_ref` 指向同一 attestation。30 个候选继续保持 `reviewing`，30 个 evidence contract 继续保持 `pending`；本次没有 active promotion，也没有生成任何工程、设备、发布、回滚或采用证明。

- Audit ID：`knowledge-hub-terminal-owner-binding-audit-20260716`
- Attestation JSONL SHA256：`4592cac185ae29602fe062e356c70fa49a62b0fe8507e0b23b19301a27ac3392`
- Packet JSONL SHA256：`39c1f84c084d4e37527732ff35216e26f83e1fc5b6527c09cb2c1974a0598975`
- Owner：`leiwenjun`
- 机器可读审计：`artifacts/manifests/knowledge-hub-terminal-owner-binding-audit-20260716.jsonl`

## 落地结果

| 检查项 | 结果 | 边界 |
| --- | ---: | --- |
| readiness `decision_owner` 镜像 | 120/120 | 4 个槽位保持一致 |
| validation `owner_ref` | 30/30 | 统一指向 owner attestation |
| `status=reviewing` | 120/120 | 未提升 active |
| `promotion=none` | 120/120 | 无 lifecycle promotion |
| `manual_validation_pending=true` | 120/120 | 真实验证仍待补 |
| `evidence_contract.status=pending` | 30/30 | ready 仍为 0/30 |

## 逐项正文绑定

| Project | Decision Item | Before SHA256 | After SHA256 | Result |
| --- | --- | --- | --- | --- |
| `pcr02-ssc305` | `pcr02-ssc305-readiness-decision-20260713` | `ed6b5b673c7dbbcf25d3ec30674e50edfdfca24fe49d251259c5df1d85e7dc4d` | `01822bdc20f2db918a85eb1b3238110e67988b7d8b28ebdf66ca97cc7d45afee` | pass |
| `xcrz-sigmastar-demo` | `xcrz-sigmastar-demo-readiness-decision-20260713` | `4982e690875369d31879232a15f1ee9e3e0bf3b2125f49cab6695c809269947c` | `141fe4686a75026425509716926ce88df542e5d5809609f9ad4f184114f98a17` | pass |
| `pcr02-api` | `pcr02-api-readiness-decision-20260713` | `66133b9d154af7258c730262f34940128c02c8ad9d81943a1707e4d7301d9025` | `c13c8388ef8d9d1d1894939e262b75c80776a9ec994a0348f7671622a3292882` | pass |
| `pcr02-app` | `pcr02-app-readiness-decision-20260713` | `143e0770f34f0adf5699b0331832ee40f0fffb05d8191d68ede986039dbc9350` | `84a28efee7ce993989b22ab642c368fcae4be9d8bb5556b6adf52a2804162cb1` | pass |
| `pcr02-hdi` | `pcr02-hdi-readiness-decision-20260713` | `cf42467112974c885a64f1558dc22fd344bc1b82a47d4f37ded94d27a76d89b7` | `890423886f8d64ba3d756b9495b613041aa081c260eac046f648280bf496864a` | pass |
| `pcr02-sensor` | `pcr02-sensor-readiness-decision-20260713` | `b9cab44e2e4dcb57a8d5831f99296dd913a3756d133f42784323cde1b378182a` | `998352cfaab8b5318a5178569049ae93e47e1a2f2814b9005c658af7263181bc` | pass |
| `pcr02-daemon` | `pcr02-daemon-readiness-decision-20260713` | `3c02c12ee2d0d8da1aad5bbb54ceef5ff0709239b9454c4e09fcc5b8be1cda2a` | `c00aa391aade2e35ae1d0df2f951d35ed27c5cf60244e4964f69d49c55169e3e` | pass |
| `pcr02-cli` | `pcr02-cli-readiness-decision-20260713` | `bb1b50587e73370ea7a40bcd0bac79369d5b478107529fb8e60a678da3ac560b` | `5aa87a99436a0ed9b1437a2cb6ae8e3115a3364920e7ab42a039a6461081dffd` | pass |
| `pcr02-cmd-server` | `pcr02-cmd-server-readiness-decision-20260713` | `fa735413a6a9a5d0595baf96b8b03886979b554bebbaaf03110dd8e44550eb1d` | `58b4d4ac57061cce53cec4c17246b0ed3409ed8616b1d16581e8c976329fae9b` | pass |
| `pcr02-proto-c` | `pcr02-proto-c-readiness-decision-20260713` | `107aa1bf693d7e8afa65df8dc927ab9214ac3340bffe278f5ef08c8a0a57a628` | `dc4ec7414fa1c7dab2cfd069d2ab5ddcd537ab9e2e92ba26e0b9ff504a52d5ef` | pass |
| `pcr02-wifi` | `pcr02-wifi-readiness-decision-20260713` | `4c8c6c6b95fe1b36967b4117d7c21457f5a1928a3c310f9bedd2aaf4d214af11` | `7fbde1007a1f54cf8c1b6112a62fd2af8c43bc943be2066350a9037c8c2f89fd` | pass |
| `pcr02-mp4` | `pcr02-mp4-readiness-decision-20260713` | `78f6a31e308168a2c8539d868602d16cc37da2f8bfebd3edd4683d9e74b33463` | `3ca3dbb3b49307b8d69138be2035c7e079adce008fd67a310a22ca51004ed7b6` | pass |
| `app-ota` | `app-ota-readiness-decision-20260713` | `c493f84aa837057e91436f019b7ecb49bd868defe218cf6144e1aa73613e5f9b` | `b15f8d739f5f04fba29b16fd998036a42b3173bb0f249ebb041b49569bbc54bd` | pass |
| `app-product-test` | `app-product-test-readiness-decision-20260713` | `3a426cbab2788b442e2234219ec1b1dab0627a928dc841f903bbc7e089b10873` | `0d54b8b0bb90c65eff145beb0fa6c33050c3ef81bf6e148c7d449509e7d705a4` | pass |
| `app-tool` | `app-tool-readiness-decision-20260713` | `fc13ceb377238665d6285fdde0547b8ef8750a84fee1d2e8c673b9fa2b685408` | `91a13ba92319673c43bad3da729c43b8911c6c9659ea615d432589808fb1030a` | pass |
| `app-main` | `app-main-readiness-decision-20260713` | `bb3a5ba3cadc2eb125949aedd32010d4544052907b03bac95d7ba1d15e4dd3bf` | `06d41c020cf025944c06724d4a843fa1bbc59647142bdfedf74addb6aacf6f34` | pass |
| `mcu` | `mcu-readiness-decision-20260713` | `9b68542519577c764f5e68be7e2dce02be0ff36c4cb9888874496251fceb462e` | `70c8f9cfcef151c7cf3fc41b4a7c88d69cdaf2517b3d235f57de40068cb07068` | pass |
| `gd32l235` | `gd32l235-readiness-decision-20260713` | `976adba40665e40bfb69fdfb8cf485c3fd218dc2f77b80acf993f5e8c7429866` | `227030a3c4e64442b5cb94e682d1ec2a2c4e348e105a95bcab6a11d9d6a17741` | pass |
| `hc32f072` | `hc32f072-readiness-decision-20260713` | `5fcb1cec68970b98a6ff5cd0abcb92fbe1762d5c0e90ac429038a459e2fa205e` | `417aa30ccea71aa94d78dfea924d3df0375d71d782fff7ab817bbaf2c78358aa` | pass |
| `mm32spin023c` | `mm32spin023c-readiness-decision-20260713` | `99edbc582d737c04630b7f6b31ad3a53783b5d7fc97b713bd45769c153caa7a2` | `582746df9532e56e615248b15a5a3c51106fe3072e1ce1293201be4158b56859` | pass |
| `firmware-release-tools` | `firmware-release-tools-readiness-decision-20260713` | `abc1489dbe8f50960cb8a6750fa571a507ae903c30a6efec4f017c294266a399` | `de1ce25ae82be446f914e0110b72a2ed1c00bf799abda5e31e174aacd9404cf3` | pass |
| `firmware-toolchains` | `firmware-toolchains-readiness-decision-20260713` | `9ad9ee02778acfa73b7961082a6d33b156af8558b77116e92b657ee5b912601f` | `56048e2c02ee324dda2214cf6ecaed77e79435e33f48911b73b79887ca67e77e` | pass |
| `codex` | `codex-readiness-decision-20260713` | `84eb3115a3ee04d08627f4e715481ae2114caea48fa48b0a49b669db72f992a2` | `51ffbad0adf63f1540c6c2ed302a62285de08a386da88a848ad76dcc10921443` | pass |
| `llm-agent` | `llm-agent-readiness-decision-20260713` | `e8bce7bbe40a440bd6f1e939e6b1edd86e2100f3cfc9e0c836d63d96d8dc5fff` | `934acf188cc7889a800c2a8ab65f5d20570d193db4414cb30e012077f2a0c38b` | pass |
| `agent-dev-kit` | `agent-dev-kit-readiness-decision-20260713` | `042725caf674985d56ee314fddf95f21c9649728d1b2a50d5b82dd1c96387c95` | `0ee51371762762387821a1a60f2aa7d8ea907ba17056d3b0e4a8ca9a698dae44` | pass |
| `llm-tools` | `llm-tools-readiness-decision-20260713` | `e5bf73da39ac43088d770028769efaaef43f37309f945fc4dc9fc100860c47ed` | `4feea7e0e91b51bd4d1fbe7ae080a58737edd6c3f7935db63f030a0bd8f0e5e1` | pass |
| `sigmastar-flasher` | `sigmastar-flasher-readiness-decision-20260713` | `66ec01edac779f6bcf7047296086188d93769dc51dfb0addd9a2a9b3410e923d` | `de96bd346cdd77d0c1788db2ae724eaf417fb0821228a6b03359f0cb8f1580f4` | pass |
| `mm32spin-validator` | `mm32spin-validator-readiness-decision-20260713` | `345c8c40ed05e513534364b4cc645d135ccc9e7f9df03feb184b89643b7bf3aa` | `f7743513d30219343f0dbca99989736a100ea0d11700414ad225b72aab2a90ea` | pass |
| `ota-packager` | `ota-packager-readiness-decision-20260713` | `c8874b86c16bb96c5c2746ba98d7f057268572b1dc7d817894c792d1ab1fa544` | `0995663ee65a03b5f3e1fe4f4649838d59cf595d10de3e2a9dbc02e73d793e6f` | pass |
| `knowledge-hub` | `knowledge-hub-readiness-decision-20260713` | `f5c8ffd8043585ec55105040ec139e7f855d7dcda245b318a174c7d9d2936bcf` | `4e4116039e35c9f8e1eee3c77badc2314e25aad0c6122502f45fe6ef5a85589b` | pass |

正文 after hash 变化来自受授权的 owner 字段、attestation 决定和禁止边界说明落地；before hash 继续绑定 owner 已复核的 Packet 原文，二者均保留以便审计。

## 验证与限制

- `knowledge-project-readiness --check`：30 projects / 120 slots / changed 0。
- `knowledge-obsidian-view-build --check`：150 个受管文档、`content_mirror_drift_count=0`、transaction changed 0。
- registry 精确审计：120 个 readiness slot 的 owner/status/promotion/manual 字段一致；30 个 validation owner_ref 一致。
- full regression：140/140 结果通过，包含 product gate 对“authority-boundary owner 已完成、专项 owner/evidence 仍待办”的语义回归。
- 执行记录：`registry/automation-runs.jsonl#knowledge-hub-terminal-owner-boundary-binding-20260716`。
- 本审计只证明 authority-boundary owner 绑定落地，不证明 Packet 外 PCR02 专项决定、artifact/device/release/rollback、evidence-ready 或真实采用。
