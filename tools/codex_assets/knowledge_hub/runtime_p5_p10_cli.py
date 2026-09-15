"""P5-P10 Knowledge Platform runtime CLI."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any, Dict, Mapping, Sequence

from .attestation import verify_quality_attestation
from .common import KnowledgeHubError, repository_root
from .memory_runtime import (
    MAX_SUMMARY_CHARS,
    MEMORY_LEVELS,
    active_memories,
    append_memory_event,
    consolidation_candidates,
    forget_memory,
    forget_scope,
    memory_event,
    supersede_memory,
)
from .protocol_conformance import protocol_conformance_report
from .retrieval_v4 import retrieve_v4
from .runtime_p5_security import repository_posture
from .temporal_graph import temporal_context_graph


def _json_object(value: str, label: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise KnowledgeHubError("{} must be valid JSON".format(label)) from exc
    if not isinstance(parsed, Mapping):
        raise KnowledgeHubError("{} must be a JSON object".format(label))
    return dict(parsed)


def _load_object(path: str, label: str) -> Dict[str, Any]:
    file_path = pathlib.Path(path)
    if not file_path.exists() or file_path.is_symlink() or not file_path.is_file():
        raise KnowledgeHubError("{} file is unavailable".format(label))
    if file_path.stat().st_size > 4 * 1024 * 1024:
        raise KnowledgeHubError("{} file exceeds byte budget".format(label))
    return _json_object(file_path.read_text(encoding="utf-8"), label)


def _load_summary(path: str) -> str:
    file_path = pathlib.Path(path)
    if not file_path.exists() or file_path.is_symlink() or not file_path.is_file():
        raise KnowledgeHubError("memory summary file is unavailable")
    if file_path.stat().st_size > MAX_SUMMARY_CHARS * 4:
        raise KnowledgeHubError("memory summary file exceeds byte budget")
    try:
        value = file_path.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError as exc:
        raise KnowledgeHubError("memory summary file must be UTF-8 text") from exc
    if not value or len(value) > MAX_SUMMARY_CHARS:
        raise KnowledgeHubError("memory summary must be non-empty and bounded")
    return value


def _memory_identity(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--principal-id", required=True)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--scope-ref", required=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    sub = parser.add_subparsers(dest="operation", required=True)

    protocols = sub.add_parser("protocols")
    protocols.add_argument("--agent-id", default="knowledge-reader")

    posture = sub.add_parser("repository-posture")
    posture.add_argument("--observed-json", required=True)
    posture.add_argument(
        "--target",
        default="registry/knowledge-platform-p5-p10.json",
    )

    retrieval = sub.add_parser("retrieve")
    retrieval.add_argument("query")
    retrieval.add_argument("--principal-json", required=True)
    retrieval.add_argument("--agent-id", default="knowledge-reader")
    retrieval.add_argument("--limit", type=int, default=10)
    retrieval.add_argument("--as-of", default="")

    memory = sub.add_parser("memory-list")
    memory.add_argument("--principal-id", required=True)
    memory.add_argument("--agent-id", required=True)
    memory.add_argument("--scope-ref", default="")

    record = sub.add_parser("memory-record")
    _memory_identity(record)
    record.add_argument("--level", required=True, choices=sorted(MEMORY_LEVELS))
    record.add_argument("--summary-file", required=True)
    record.add_argument("--source-ref", action="append", default=[])
    record.add_argument("--ttl-seconds", type=int, default=0)

    forget = sub.add_parser("memory-forget")
    _memory_identity(forget)
    forget.add_argument("--memory-id", required=True)

    supersede = sub.add_parser("memory-supersede")
    _memory_identity(supersede)
    supersede.add_argument("--memory-id", required=True)

    forget_scope_parser = sub.add_parser("memory-forget-scope")
    _memory_identity(forget_scope_parser)

    consolidate = sub.add_parser("memory-consolidate")
    consolidate.add_argument("--principal-id", required=True)
    consolidate.add_argument("--agent-id", required=True)
    consolidate.add_argument("--scope-ref", default="")

    graph = sub.add_parser("temporal-graph")
    graph.add_argument("--seed-id", action="append", default=[])
    graph.add_argument("--as-of", default="")

    attest = sub.add_parser("attestation-verify")
    attest.add_argument("--statement", required=True)
    attest.add_argument("--subject-sha256", default="")
    return parser


def _target_policy(root: pathlib.Path, relative: str) -> Dict[str, Any]:
    path = root / relative
    if not path.exists() or path.is_symlink() or not path.is_file():
        raise KnowledgeHubError("platform policy is unavailable")
    value = _json_object(path.read_text(encoding="utf-8"), "platform policy")
    target = value.get("repository_security_target", {})
    if not isinstance(target, Mapping):
        raise KnowledgeHubError("platform policy repository target must be an object")
    return dict(target)


def _memory_record(root: pathlib.Path, args: argparse.Namespace) -> Dict[str, Any]:
    event = memory_event(
        agent_id=args.agent_id,
        principal_id=args.principal_id,
        level=args.level,
        summary=_load_summary(args.summary_file),
        scope_ref=args.scope_ref,
        source_refs=args.source_ref,
        ttl_seconds=args.ttl_seconds,
    )
    return append_memory_event(root, event)


def _memory_forget_scope(root: pathlib.Path, args: argparse.Namespace) -> Dict[str, Any]:
    result = forget_scope(
        root,
        principal_id=args.principal_id,
        agent_id=args.agent_id,
        scope_ref=args.scope_ref,
    )
    return {"status": "pass", **result}


def _dispatch(root: pathlib.Path, args: argparse.Namespace) -> Dict[str, Any]:
    if args.operation == "protocols":
        return protocol_conformance_report(root, agent_id=args.agent_id)
    if args.operation == "repository-posture":
        observed = _json_object(args.observed_json, "observed repository posture")
        return repository_posture(observed, _target_policy(root, args.target))
    if args.operation == "retrieve":
        principal = _json_object(args.principal_json, "principal")
        return retrieve_v4(
            root,
            args.query,
            principal,
            agent_id=args.agent_id,
            limit=args.limit,
            as_of=args.as_of,
        )
    if args.operation == "memory-list":
        rows = active_memories(
            root,
            principal_id=args.principal_id,
            agent_id=args.agent_id,
            scope_ref=args.scope_ref,
        )
        return {
            "schema_version": "knowledge-hub.memory-list.v1",
            "status": "pass",
            "memories": rows,
        }
    if args.operation == "memory-record":
        return _memory_record(root, args)
    if args.operation == "memory-forget":
        return forget_memory(
            root,
            memory_id=args.memory_id,
            principal_id=args.principal_id,
            agent_id=args.agent_id,
            scope_ref=args.scope_ref,
        )
    if args.operation == "memory-supersede":
        return supersede_memory(
            root,
            memory_id=args.memory_id,
            principal_id=args.principal_id,
            agent_id=args.agent_id,
            scope_ref=args.scope_ref,
        )
    if args.operation == "memory-forget-scope":
        return _memory_forget_scope(root, args)
    if args.operation == "memory-consolidate":
        return consolidation_candidates(
            root,
            principal_id=args.principal_id,
            agent_id=args.agent_id,
            scope_ref=args.scope_ref,
        )
    if args.operation == "temporal-graph":
        return temporal_context_graph(
            root,
            seed_ids=args.seed_id,
            as_of=args.as_of,
        )
    if args.operation == "attestation-verify":
        statement = _load_object(args.statement, "attestation")
        return verify_quality_attestation(
            statement,
            expected_subject_sha256=args.subject_sha256,
        )
    raise KnowledgeHubError("unsupported platform operation")


def main(argv: Sequence[str] = ()) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        result = _dispatch(root, args)
    except KnowledgeHubError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result.get("status") in {"pass", "ready", "recorded"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
