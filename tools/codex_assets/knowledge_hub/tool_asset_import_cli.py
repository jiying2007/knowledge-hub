"""Validate and import metadata-only tool asset candidates."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import tempfile
from typing import Any, Dict, Mapping, Sequence, Tuple

from .common import (
    KnowledgeHubError,
    load_json,
    load_markdown,
    normalize_relpath,
    read_utf8_bounded,
    repository_root,
    resolve_today,
    slugify,
)
from .lifecycle import capture
from .search_ranking import redact_internal_endpoints
from .security import scan_secret_text


SCHEMA = "knowledge-hub.tool-asset-candidate.v1"
MAX_CANDIDATE_BYTES = 128 * 1024
REQUIRED_VALIDATIONS = ("unit_tests", "cli_help", "dry_run", "non_repo_cwd")
VALIDATION_RESULTS = {"pass", "fail", "not-run", "not-applicable"}
RECOMMENDATIONS = {
    "keep-project-tool",
    "recommend-project-skill",
    "recommend-global-codex",
    "recommend-promote",
    "reject",
}
SOURCE_PREFIXES = ("codex_assets/", "tools/", "scripts/")
PROHIBITED_SOURCE_PARTS = {".git", ".codex", "tmp", ".tmp", "logs", "core", "cores"}
PROHIBITED_SOURCE_SUFFIXES = {".bin", ".core", ".dump", ".elf", ".log", ".o", ".so", ".zip"}
HEX_RE = re.compile(r"^[0-9a-f]+$")
CANONICAL_TEMPLATE = """---
schema: {schema}
id: {item_id}
title: {title_json}
kind: validation
domain: {target_domain}
path: {target}
scope: project-specific
visibility: team-internal
status: reviewing
owner: {owner_json}
review_after: {review_after}
created_at: {today}
updated_at: {today}
promotion: none
promotion_decision: {recommendation}
tags: [tool-asset, candidate, validation]
source_repo: {source_repo}
source_commit: {source_commit}
source_worktree_dirty: {source_worktree_dirty}
source_identity_verified: {source_identity_verified}
candidate_name: {candidate_name}
candidate_source_path: {candidate_source_path}
candidate_sha256: {candidate_sha256}
candidate_hash_scope: {candidate_hash_scope}
candidate_file_count: {candidate_file_count}
candidate_score: {candidate_score}
recommendation: {recommendation}
recommended_target: {recommended_target_json}
summary_zh: {summary_zh_json}
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
review_status: automated-candidate-pending-human-review
evidence_strength: source-identity-and-offline-validation-summary
generated_by_ai: false
---

# {title}

## 结论

{summary_zh}

- 当前状态：`reviewing`
- 候选评分：`{candidate_score}/100`
- 推荐动作：`{recommendation}`
- 推荐目标：{recommended_target}
- 本记录不复制源码、raw log、core、二进制或现场信息，也不代表已批准提升。

## 源码身份

- source_repo：`{source_repo}`
- source_commit：`{source_commit}`
- source_worktree_dirty：`{source_worktree_dirty}`
- source_identity_verified：`{source_identity_verified}`
- candidate_source_path：`{candidate_source_path}`
- candidate_sha256：`{candidate_sha256}`
- candidate_hash_scope：`{candidate_hash_scope}`
- candidate_file_count：`{candidate_file_count}`

源码仍由源仓管理；Knowledge Hub 只保存路径、commit、hash、验证摘要和治理结论。

## 验证矩阵

| 检查 | 结果 |
| --- | --- |
| unit_tests | `{unit_tests}` |
| cli_help | `{cli_help}` |
| dry_run | `{dry_run}` |
| non_repo_cwd | `{non_repo_cwd}` |

## 脱敏门禁

| 检查 | 结果 |
| --- | --- |
| endpoint_removed | `{endpoint_removed}` |
| credentials_found | `{credentials_found}` |
| raw_logs_archived | `{raw_logs_archived}` |

## 风险与阻塞

- 风险：{risks_zh}
- blockers：{blockers_zh}

## Promotion Gate

1. 人工复核源码用途、维护 owner、兼容边界和验证证据。
2. 项目专用资产继续留在源仓；跨项目通用资产只能作为 `~/codex` 源码候选，另走 source-to-live 流程。
3. 需要正式提升时另建 decision；本 validation 不关闭 owner gate，不授权自动调用、外部写入、commit、push、merge 或 memory write。

## 验证

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "{item_id}" --json
```
"""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="校验并规划导入脱敏的工具资产候选；默认只生成事务计划。",
        epilog=(
            "Example:\n"
            "  rtk bash ~/knowledge-hub/tools/knowledge-capture.sh "
            "--tool-asset-candidate /tmp/tool-asset-candidates/hub-candidate.md --json\n"
            "  rtk bash ~/knowledge-hub/tools/knowledge-capture.sh "
            "--tool-asset-candidate /tmp/hub-candidate.md --apply --json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--root", default="")
    parser.add_argument("--source", required=True)
    parser.add_argument("--owner", default="leiwenjun")
    parser.add_argument("--review-after", default="")
    parser.add_argument("--as-of", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def _required_text(metadata: Mapping[str, Any], field: str) -> str:
    value = metadata.get(field)
    if not isinstance(value, str) or not value.strip():
        raise KnowledgeHubError("candidate field must be a non-empty string: {}".format(field))
    return value.strip()


def _required_bool(metadata: Mapping[str, Any], field: str, expected: bool) -> bool:
    value = metadata.get(field)
    if not isinstance(value, bool):
        raise KnowledgeHubError("candidate field must be boolean: {}".format(field))
    if value is not expected:
        raise KnowledgeHubError(
            "candidate sanitization gate failed: {} must be {}".format(field, str(expected).lower())
        )
    return value


def _candidate_bool(metadata: Mapping[str, Any], field: str, default: bool) -> bool:
    value = metadata.get(field, default)
    if not isinstance(value, bool):
        raise KnowledgeHubError("candidate field must be boolean: {}".format(field))
    return value


def _repository_route(root: pathlib.Path, source_repo: str) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    data = load_json(root / "registry/repositories.json", {}) or {}
    matches = []
    for row in data.get("repositories", []):
        if not isinstance(row, dict) or row.get("status") != "registered":
            continue
        identities = {str(row.get("repo_id", "")), str(row.get("remote_key", ""))}
        identities.update(str(value) for value in row.get("aliases", []) if isinstance(value, str))
        if source_repo in identities:
            matches.append(row)
    if len(matches) != 1:
        raise KnowledgeHubError("source_repo must resolve to exactly one registered repository: {}".format(source_repo))
    project_id = str(matches[0].get("project_id", ""))
    projects = load_json(root / "registry/projects.json", {}) or {}
    project_matches = [row for row in projects.get("projects", []) if isinstance(row, dict) and row.get("id") == project_id]
    if len(project_matches) != 1:
        raise KnowledgeHubError("registered repository has no usable project route: {}".format(source_repo))
    project = dict(project_matches[0])
    entry = str(project.get("entry", ""))
    validation = str(project.get("validation", ""))
    if not entry or not validation or not (root / entry).exists():
        raise KnowledgeHubError("registered repository has incomplete project paths: {}".format(source_repo))
    return project_id, dict(matches[0]), project


def _target_domain(validation_root: str, project_id: str) -> str:
    if validation_root.startswith("projects/{}/".format(project_id)):
        return "projects/{}".format(project_id)
    if validation_root.startswith("governance/"):
        return "governance"
    if validation_root.startswith("domains/codex/"):
        return "codex"
    if validation_root.startswith("domains/embedded/"):
        return "embedded"
    if validation_root.startswith("domains/patents/"):
        return "patents"
    raise KnowledgeHubError("project validation path has no supported item domain: {}".format(validation_root))


def _validate_commit(value: str) -> str:
    if not 7 <= len(value) <= 64 or not HEX_RE.fullmatch(value):
        raise KnowledgeHubError("source_commit must be 7-64 lowercase hexadecimal characters")
    return value


def _validate_sha256(value: str) -> str:
    if len(value) != 64 or not HEX_RE.fullmatch(value):
        raise KnowledgeHubError("candidate_sha256 must be a lowercase SHA256 value")
    return value


def _validate_source_path(value: str) -> str:
    normalized = normalize_relpath(value)
    path = pathlib.PurePosixPath(normalized)
    if not normalized.startswith(SOURCE_PREFIXES):
        raise KnowledgeHubError("candidate_source_path must live under codex_assets/, tools/ or scripts/")
    if any(part.lower() in PROHIBITED_SOURCE_PARTS for part in path.parts):
        raise KnowledgeHubError("candidate_source_path points to a prohibited runtime/raw directory")
    if path.suffix.lower() in PROHIBITED_SOURCE_SUFFIXES:
        raise KnowledgeHubError("candidate_source_path points to a binary, raw log or runtime artifact")
    return normalized


def _validation_matrix(metadata: Mapping[str, Any]) -> Dict[str, str]:
    value = metadata.get("validation")
    if not isinstance(value, dict):
        raise KnowledgeHubError("candidate validation must be a mapping")
    result: Dict[str, str] = {}
    for field in REQUIRED_VALIDATIONS:
        status = value.get(field)
        if not isinstance(status, str) or status not in VALIDATION_RESULTS:
            raise KnowledgeHubError(
                "validation.{} must be one of {}".format(field, ", ".join(sorted(VALIDATION_RESULTS)))
            )
        result[field] = status
    return result


def _sanitization(metadata: Mapping[str, Any]) -> Dict[str, bool]:
    value = metadata.get("sanitization")
    if not isinstance(value, dict):
        raise KnowledgeHubError("candidate sanitization must be a mapping")
    return {
        "endpoint_removed": _required_bool(value, "endpoint_removed", True),
        "credentials_found": _required_bool(value, "credentials_found", False),
        "raw_logs_archived": _required_bool(value, "raw_logs_archived", False),
    }


def _short_text(metadata: Mapping[str, Any], field: str, default: str = "无") -> str:
    value = metadata.get(field, default)
    if isinstance(value, list):
        value = "；".join(str(item).strip() for item in value if str(item).strip()) or default
    if not isinstance(value, str):
        raise KnowledgeHubError("candidate field must be text or a text list: {}".format(field))
    value = " ".join(value.split())
    if len(value) > 1000:
        raise KnowledgeHubError("candidate field exceeds 1000 characters: {}".format(field))
    return value or default


def _validate_candidate(root: pathlib.Path, source: pathlib.Path) -> Dict[str, Any]:
    raw_text = read_utf8_bounded(source, MAX_CANDIDATE_BYTES, "tool asset candidate")
    findings = scan_secret_text(raw_text)
    if findings:
        rules = sorted({str(row.get("rule", "unknown")) for row in findings})
        raise KnowledgeHubError("candidate contains secret-like material; rules={}".format(",".join(rules)))
    _, endpoint_redacted = redact_internal_endpoints(raw_text)
    if endpoint_redacted:
        raise KnowledgeHubError("candidate contains an internal/private endpoint; provide a redacted candidate")

    metadata, _body = load_markdown(source)
    if metadata.get("schema") != SCHEMA:
        raise KnowledgeHubError("candidate schema must be {}".format(SCHEMA))
    if metadata.get("status") != "reviewing":
        raise KnowledgeHubError("candidate status must be reviewing")
    source_repo = _required_text(metadata, "source_repo")
    project_id, repository, project = _repository_route(root, source_repo)
    candidate_name = slugify(_required_text(metadata, "candidate_name"))
    if not candidate_name:
        raise KnowledgeHubError("candidate_name must contain a usable slug")
    recommendation = _required_text(metadata, "recommendation")
    if recommendation not in RECOMMENDATIONS:
        raise KnowledgeHubError("unsupported recommendation: {}".format(recommendation))
    score = metadata.get("candidate_score")
    if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
        raise KnowledgeHubError("candidate_score must be an integer between 0 and 100")
    identity_verified = _candidate_bool(metadata, "source_identity_verified", False)
    if not identity_verified:
        raise KnowledgeHubError("source_identity_verified must be true")
    hash_scope = _short_text(metadata, "candidate_hash_scope", "single-file")
    if hash_scope not in {"single-file", "file-set"}:
        raise KnowledgeHubError("candidate_hash_scope must be single-file or file-set")
    file_count = metadata.get("candidate_file_count", 1)
    if not isinstance(file_count, int) or isinstance(file_count, bool) or file_count < 1:
        raise KnowledgeHubError("candidate_file_count must be a positive integer")
    return {
        "source_repo": source_repo,
        "project_id": project_id,
        "repository": repository,
        "project": project,
        "target_domain": _target_domain(str(project["validation"]), project_id),
        "validation_root": str(project["validation"]),
        "source_commit": _validate_commit(_required_text(metadata, "source_commit")),
        "source_worktree_dirty": _candidate_bool(metadata, "source_worktree_dirty", True),
        "source_identity_verified": identity_verified,
        "candidate_name": candidate_name,
        "candidate_source_path": _validate_source_path(_required_text(metadata, "candidate_source_path")),
        "candidate_sha256": _validate_sha256(_required_text(metadata, "candidate_sha256")),
        "candidate_hash_scope": hash_scope,
        "candidate_file_count": file_count,
        "candidate_score": score,
        "recommendation": recommendation,
        "recommended_target": _short_text(metadata, "recommended_target", "待人工评审"),
        "validation": _validation_matrix(metadata),
        "sanitization": _sanitization(metadata),
        "summary_zh": _short_text(metadata, "summary_zh"),
        "risks_zh": _short_text(metadata, "risks_zh"),
        "blockers_zh": _short_text(metadata, "blockers_zh"),
    }


def _canonical_markdown(
    candidate: Mapping[str, Any], today: str, target: str, owner: str, review_after: str, item_id: str
) -> str:
    validation = candidate["validation"]
    sanitization = candidate["sanitization"]
    title = "工具资产候选：{}".format(candidate["candidate_name"])
    values = dict(candidate)
    values.update(
        {
            "schema": SCHEMA,
            "item_id": item_id,
            "title": title,
            "target": target,
            "owner": owner,
            "review_after": review_after,
            "today": today,
            "unit_tests": validation["unit_tests"],
            "cli_help": validation["cli_help"],
            "dry_run": validation["dry_run"],
            "non_repo_cwd": validation["non_repo_cwd"],
            "endpoint_removed": str(sanitization["endpoint_removed"]).lower(),
            "credentials_found": str(sanitization["credentials_found"]).lower(),
            "raw_logs_archived": str(sanitization["raw_logs_archived"]).lower(),
            "source_worktree_dirty": str(candidate["source_worktree_dirty"]).lower(),
            "source_identity_verified": str(candidate["source_identity_verified"]).lower(),
            "title_json": json.dumps(title, ensure_ascii=False),
            "owner_json": json.dumps(owner, ensure_ascii=False),
            "recommended_target_json": json.dumps(str(candidate["recommended_target"]), ensure_ascii=False),
            "summary_zh_json": json.dumps(str(candidate["summary_zh"]), ensure_ascii=False),
        }
    )
    return CANONICAL_TEMPLATE.format(**values)


def _emit(payload: Mapping[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(dict(payload), ensure_ascii=False, indent=2))
        return
    for key, value in payload.items():
        rendered = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
        print("{}: {}".format(key, rendered))


def import_candidate(
    root: pathlib.Path,
    source: pathlib.Path,
    today: dt.date,
    apply: bool,
    owner: str = "leiwenjun",
    review_after: str = "",
) -> Dict[str, Any]:
    candidate = _validate_candidate(root, source.expanduser().resolve())
    review_after = review_after or (today + dt.timedelta(days=90)).isoformat()
    item_id = "{}-tool-asset-candidate-{}-{}".format(
        candidate["project_id"], candidate["candidate_name"], today.strftime("%Y%m%d")
    )
    target = "{}/tool-asset-candidate-{}-{}.md".format(
        candidate["validation_root"], today.isoformat(), candidate["candidate_name"]
    )
    canonical = _canonical_markdown(candidate, today.isoformat(), target, owner, review_after, item_id)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md") as stream:
        stream.write(canonical)
        stream.flush()
        result = capture(
            root,
            pathlib.Path(stream.name),
            "validation",
            target,
            today,
            apply,
            item_id=item_id,
            title="工具资产候选：{}".format(candidate["candidate_name"]),
            domain=str(candidate["target_domain"]),
            owner=owner,
            status="reviewing",
            review_after=review_after,
            tags=("tool-asset", "candidate", "validation"),
            summary_zh=str(candidate["summary_zh"]),
            source_type="tool-asset-candidate",
            source_from="{}@{}:{}#{}".format(
                candidate["source_repo"],
                candidate["source_commit"],
                candidate["candidate_source_path"],
                candidate["candidate_sha256"],
            ),
        )
    result.update(
        {
            "schema": SCHEMA,
            "candidate": candidate,
            "security_gate": "pass",
            "raw_candidate_body_archived": False,
            "source_code_copied": False,
            "active_promotion": False,
            "owner_decision_generated": False,
        }
    )
    return result


def main(argv: Sequence[str] = ()) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv else None)
    if args.apply and args.dry_run:
        parser.error("--apply and --dry-run are mutually exclusive")
    try:
        root = repository_root(args.root)
        today, date_source = resolve_today(args.as_of)
        result = import_candidate(
            root,
            pathlib.Path(args.source),
            today,
            args.apply,
            owner=args.owner,
            review_after=args.review_after,
        )
        result.update({"as_of": today.isoformat(), "date_source": date_source, "dry_run": not args.apply})
        _emit(result, args.json)
        return 0
    except (KnowledgeHubError, OSError, ValueError) as exc:
        _emit({"status": "error", "error": str(exc), "schema": SCHEMA}, args.json)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
