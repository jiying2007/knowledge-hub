"""P5-P10 Knowledge Platform runtime CLI."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any, Dict, Mapping, Sequence

from .attestation import verify_quality_attestation
from .common import KnowledgeHubError, repository_root
from .memory_runtime import active_memories, consolidation_candidates
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
