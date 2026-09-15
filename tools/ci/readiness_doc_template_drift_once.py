from __future__ import annotations

import json
import re
from pathlib import Path


PROJECTS_PATH = Path("registry/projects.json")
READINESS_PATH = Path("tools/codex_assets/knowledge_hub/project_readiness.py")
TESTS_PATH = Path("tests/test_project_readiness.py")

PROFILE_EXPECTATIONS = {
    "embedded-target": (
        "工程验证：在源项目运行适用的构建、单元/集成测试并保留命令、版本和日志摘要。",
        "设备验证：需要硬件行为的结论必须补 HIL/实机、环境条件和可复现实验记录。",
        "发布验证：记录制品身份、版本、回滚路径和端到端验收，不以 Hub 文档替代发布签收。",
    ),
    "software-tool": (
        "工具验证：覆盖 CLI help、错误码、输入边界、制品 hash 和目标平台 smoke test。",
        "发布验证：覆盖可安装/可运行制品、版本信息、回滚和消费者兼容性。",
    ),
    "runtime-assets": (
        "运行态验证：执行声明式 build/doctor/plan/dry-run/apply/check 链路并保留回滚证据。",
    ),
    "control-plane": (
        "控制面验证：执行 check、unit、retrieval、route、link、export 和 restore drill。",
    ),
    "aggregate-group": (
        "项目组验证：每个成员项目分别补齐所需真实证据，组级结论不得替代成员项目 readiness。",
    ),
}

OLD_GROUP_LINE = "项目组验证：每个成员仓分别补源码、设备/平台和发布证据，不能用组级结论替代。"
OLD_EXPECTATIONS = {row for rows in PROFILE_EXPECTATIONS.values() for row in rows}
OLD_EXPECTATIONS.add(OLD_GROUP_LINE)


def replace_section(text: str, start: str, end: str, replacement: str, label: str) -> str:
    start_index = text.find(start)
    end_index = text.find(end, start_index + len(start))
    if start_index < 0 or end_index < 0:
        raise SystemExit(f"unable to locate {label}")
    if text.find(start, start_index + len(start)) >= 0:
        raise SystemExit(f"duplicate {label} start")
    return text[:start_index] + replacement.rstrip() + "\n\n\n" + text[end_index:]


def expectation_marker(text: str) -> str:
    return text.split("：", 1)[0] + "："


projects = json.loads(PROJECTS_PATH.read_text(encoding="utf-8"))["projects"]
project_by_id = {row["id"]: row for row in projects}
if len(project_by_id) != 32:
    raise SystemExit(f"unexpected project count: {len(project_by_id)}")

route_pattern = re.compile(
    r"^- \[x\] \d+ 项目 route matrix 能将 `([^`]+)` 稳定解析为本项目。$",
    re.M,
)
route_migrated = []
for project in projects:
    project_id = project["id"]
    path = Path(str(project["validation"]).rstrip("/")) / "project-readiness.md"
    text = path.read_text(encoding="utf-8")
    matches = route_pattern.findall(text)
    if matches != [project_id]:
        raise SystemExit(f"unexpected route line for {project_id}: {matches!r}")
    replacement = f"- [x] 项目 route matrix 能将 `{project_id}` 稳定解析为本项目。"
    text, count = route_pattern.subn(replacement, text, count=1)
    if count != 1:
        raise SystemExit(f"route migration count mismatch for {project_id}")
    path.write_text(text, encoding="utf-8")
    route_migrated.append(project_id)

# Only unchecked, exact machine-template lines are replaced. Manual/completed evidence is preserved.
semantic_targets = {
    "llm-agent": "software-tool",
    "agent-dev-kit": "software-tool",
    "digital-worker": "software-tool",
    "x5-rdk": "embedded-target",
}
for project_id, expected_profile in semantic_targets.items():
    project = project_by_id[project_id]
    if project.get("evidence_profile") != expected_profile:
        raise SystemExit(f"unexpected evidence profile for {project_id}")
    path = Path(str(project["validation"]).rstrip("/")) / "project-readiness.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    generated_indexes = [
        index
        for index, line in enumerate(lines)
        if line.startswith("- [ ] ") and line[6:] in OLD_EXPECTATIONS
    ]
    if not generated_indexes:
        raise SystemExit(f"no exact generated expectation lines for {project_id}")

    insert_at = generated_indexes[0]
    generated_set = set(generated_indexes)
    kept = [line for index, line in enumerate(lines) if index not in generated_set]
    insert_at -= sum(1 for index in generated_indexes if index < insert_at)

    expected_lines = []
    for expectation in PROFILE_EXPECTATIONS[expected_profile]:
        marker = expectation_marker(expectation)
        if any(
            line.startswith(("- [ ] ", "- [x] ")) and marker in line
            for line in kept
        ):
            continue
        expected_lines.append(f"- [ ] {expectation}")
    kept[insert_at:insert_at] = expected_lines
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")

source = READINESS_PATH.read_text(encoding="utf-8")
new_expectations = '''PROFILE_VALIDATION_EXPECTATIONS = {
    "embedded-target": (
        "工程验证：在源项目运行适用的构建、单元/集成测试并保留命令、版本和日志摘要。",
        "设备验证：需要硬件行为的结论必须补 HIL/实机、环境条件和可复现实验记录。",
        "发布验证：记录制品身份、版本、回滚路径和端到端验收，不以 Hub 文档替代发布签收。",
    ),
    "software-tool": (
        "工具验证：覆盖 CLI help、错误码、输入边界、制品 hash 和目标平台 smoke test。",
        "发布验证：覆盖可安装/可运行制品、版本信息、回滚和消费者兼容性。",
    ),
    "runtime-assets": (
        "运行态验证：执行声明式 build/doctor/plan/dry-run/apply/check 链路并保留回滚证据。",
    ),
    "control-plane": (
        "控制面验证：执行 check、unit、retrieval、route、link、export 和 restore drill。",
    ),
    "aggregate-group": (
        "项目组验证：每个成员项目分别补齐所需真实证据，组级结论不得替代成员项目 readiness。",
    ),
}


def _expectation_marker(text: str) -> str:
    return text.split("：", 1)[0] + "："


def _validation_expectations(
    project: Mapping[str, Any], extension: Mapping[str, Any]
) -> List[str]:
    profile = project_evidence_profile(project)
    rows = [
        "Hub 结构验证：registry、route、正文镜像、链接和检索矩阵通过。",
        "来源验证：确认 Git remote key、当前分支/版本和源码事实，Hub 不代替源仓事实。",
        "责任验证：由真实 decision owner 明确接受、修改或拒绝边界候选。",
    ]
    rows.extend(PROFILE_VALIDATION_EXPECTATIONS[profile])
    rows.extend(str(value) for value in extension.get("validation_expectations_zh", []))
    return rows


def _validate_existing_validation_body(
    project: Mapping[str, Any], text: str
) -> None:
    project_id = str(project["id"])
    expected_route = "- [x] 项目 route matrix 能将 `{}` 稳定解析为本项目。".format(
        project_id
    )
    if expected_route not in text:
        raise KnowledgeHubError(
            "existing readiness route statement drift: {}".format(project_id)
        )

    profile = project_evidence_profile(project)
    expected_rows = set(PROFILE_VALIDATION_EXPECTATIONS[profile])
    all_rows = {
        row
        for rows in PROFILE_VALIDATION_EXPECTATIONS.values()
        for row in rows
    }
    all_markers = {_expectation_marker(row) for row in all_rows}
    expected_markers = {_expectation_marker(row) for row in expected_rows}
    actual_markers = {
        _expectation_marker(line[6:])
        for line in text.splitlines()
        if line.startswith(("- [ ] ", "- [x] "))
        and "：" in line[6:]
        and _expectation_marker(line[6:]) in all_markers
    }
    missing_markers = expected_markers - actual_markers
    stale_generated = sorted(
        row
        for row in all_rows - expected_rows
        if "- [ ] {}".format(row) in text
    )
    if missing_markers or stale_generated:
        raise KnowledgeHubError(
            "existing readiness evidence-profile statement drift: {} missing={} stale_generated={}".format(
                project_id,
                sorted(missing_markers),
                stale_generated,
            )
        )
'''
source = replace_section(
    source,
    "def _validation_expectations(\n",
    "def _base_item(\n",
    new_expectations,
    "validation expectation section",
)

new_body = '''def _validation_body(
    project: Mapping[str, Any],
    path: str,
    paths: Mapping[str, str],
    extension: Mapping[str, Any],
) -> str:
    expectations = "\\n".join(
        "- [ ] {}".format(value)
        for value in _validation_expectations(project, extension)
    )
    related_extension = "".join(
        "\\n- {}".format(
            _link(path, str(row["path"]), str(row["label_zh"]))
        )
        for row in extension.get("related_links", [])
    )
    return """# {name} readiness validation

## 结论

结构性工作台已建立；本机 source 定位由未跟踪 local mapping 动态报告，真实 owner、工程验证、实机/目标平台和发布证据尚未由本页完成。当前结论是 `structurally-ready / evidence-pending`，不是 release-ready。

## 自动结构检查

- [x] registry item 与正文 frontmatter 镜像一致。
- [x] 项目 route matrix 能将 `{project_id}` 稳定解析为本项目。
- [x] 单一 evidence contract 已登记，统一 dashboard 可从项目入口访问。
- [x] search known-answer 与 link audit 通过。
- [ ] 本机 source 定位：运行 `knowledge-workspace-discover.sh --plan --json`，由 project gate 动态读取；结果不得复制到 tracked Markdown。

## 人工/真实环境门禁

{expectations}

## 证据记录模板

| 字段 | 待填写 |
|---|---|
| decision owner | `unassigned` |
| source repo / commit / version | pending |
| 执行环境与设备 | pending |
| 命令与返回码 | pending |
| 日志/截图/制品 hash | pending |
| 回滚验证 | pending |
| 结论和适用边界 | pending |

## Related

- {dashboard_link}{related_extension}
- {project_entry_link}
""".format(
        name=project["name"],
        project_id=project["id"],
        expectations=expectations,
        dashboard_link=_link(path, "indexes/project-readiness.md", "统一 readiness dashboard"),
        related_extension=related_extension,
        project_entry_link=_link(path, str(project["entry"]), "项目入口"),
    )
'''
source = replace_section(
    source,
    "def _validation_body(\n",
    "def _managed_readme(\n",
    new_body,
    "validation body section",
)

old_call = '''                _validation_body(
                    project,
                    paths["validation"],
                    paths,
                    len(projects),
                    readiness_extension,
                ),'''
new_call = '''                _validation_body(
                    project,
                    paths["validation"],
                    paths,
                    readiness_extension,
                ),'''
if source.count(old_call) != 1:
    raise SystemExit("unexpected validation body call")
source = source.replace(old_call, new_call, 1)

old_existing = '''            if existing_item:
                if not target_exists:
                    raise KnowledgeHubError(
                        "existing readiness body is missing: {}".format(existing_item.get("id", ""))
                    )
                item = _preserve_existing_readiness_item('''
new_existing = '''            if existing_item:
                if not target_exists:
                    raise KnowledgeHubError(
                        "existing readiness body is missing: {}".format(existing_item.get("id", ""))
                    )
                if slot == "validation":
                    _validate_existing_validation_body(
                        project,
                        (root / paths[slot]).read_text(encoding="utf-8"),
                    )
                item = _preserve_existing_readiness_item('''
if source.count(old_existing) != 1:
    raise SystemExit("unexpected existing readiness branch")
source = source.replace(old_existing, new_existing, 1)
READINESS_PATH.write_text(source, encoding="utf-8")

tests = TESTS_PATH.read_text(encoding="utf-8")
old_import = '''from tools.codex_assets.knowledge_hub.project_readiness import (
    RETIRED_PROJECTION_SLOTS,
    SLOT_NAMES,
    _preserve_existing_readiness_item,
    _project_paths,
    generate_project_readiness,
)'''
new_import = '''from tools.codex_assets.knowledge_hub.project_readiness import (
    PROFILE_VALIDATION_EXPECTATIONS,
    RETIRED_PROJECTION_SLOTS,
    SLOT_NAMES,
    _preserve_existing_readiness_item,
    _project_paths,
    _validate_existing_validation_body,
    generate_project_readiness,
)'''
if tests.count(old_import) != 1:
    raise SystemExit("unexpected project readiness test import")
tests = tests.replace(old_import, new_import, 1)

old_assert = '''    assert "{} 项目 route matrix".format(expected_project_count) in validation.read_text()'''
new_assert = '''    assert (
        "- [x] 项目 route matrix 能将 `scalable-project-31` 稳定解析为本项目。"
        in validation.read_text()
    )'''
if tests.count(old_assert) != 1:
    raise SystemExit("unexpected scalable route count assertion")
tests = tests.replace(old_assert, new_assert, 1)

addition = r'''


def test_readiness_documents_are_count_neutral_and_profile_aligned():
    root = repository_root()
    numeric_route = re.compile(r"^- \[x\] \d+ 项目 route matrix", re.M)
    for project in project_rows(root):
        path = root / _project_paths(project)["validation"]
        text = path.read_text(encoding="utf-8")
        assert not numeric_route.search(text), project["id"]
        _validate_existing_validation_body(project, text)


def test_validation_expectations_follow_evidence_profile_not_repo_topology():
    root = repository_root()
    projects = {row["id"]: row for row in project_rows(root)}
    for project_id in ("llm-agent", "agent-dev-kit", "digital-worker"):
        project = projects[project_id]
        assert project["evidence_profile"] == "software-tool"
        text = (root / _project_paths(project)["validation"]).read_text(encoding="utf-8")
        for expected in PROFILE_VALIDATION_EXPECTATIONS["software-tool"]:
            assert expected.split("：", 1)[0] + "：" in text
    x5 = projects["x5-rdk"]
    assert x5["repo_boundary"] == "group"
    assert x5["evidence_profile"] == "embedded-target"
    x5_text = (root / _project_paths(x5)["validation"]).read_text(encoding="utf-8")
    for expected in PROFILE_VALIDATION_EXPECTATIONS["embedded-target"]:
        assert expected.split("：", 1)[0] + "：" in x5_text


def test_existing_manual_readiness_evidence_is_preserved():
    root = repository_root()
    project = next(row for row in project_rows(root) if row["id"] == "llm-agent")
    text = (root / _project_paths(project)["validation"]).read_text(encoding="utf-8")
    assert "check-all.sh --full` 均为 62/62" in text
    assert "313 篇 corpus" in text
    assert "- [x] 工程验证：" in text
    _validate_existing_validation_body(project, text)


def test_existing_readiness_body_profile_drift_fails_closed():
    root = repository_root()
    project = dict(next(row for row in project_rows(root) if row["id"] == "x5-rdk"))
    text = (root / _project_paths(project)["validation"]).read_text(encoding="utf-8")
    project["evidence_profile"] = "software-tool"
    with pytest.raises(
        KnowledgeHubError,
        match="existing readiness evidence-profile statement drift: x5-rdk",
    ):
        _validate_existing_validation_body(project, text)
'''
if "test_readiness_documents_are_count_neutral_and_profile_aligned" in tests:
    raise SystemExit("readiness drift tests already present")
if "import re\n" not in tests:
    tests = tests.replace("import json\n", "import json\nimport re\n", 1)
tests = tests.rstrip() + addition + "\n"
TESTS_PATH.write_text(tests, encoding="utf-8")

print(
    json.dumps(
        {
            "route_documents_migrated": len(route_migrated),
            "semantic_documents_migrated": sorted(semantic_targets),
            "generator_semantics": "evidence-profile",
            "route_statement": "count-neutral",
            "manual_evidence_policy": "preserve",
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
