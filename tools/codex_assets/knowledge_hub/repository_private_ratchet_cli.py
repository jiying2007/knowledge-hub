"""Emit a review-only repository-private-boundary candidate from hosted metadata."""

from __future__ import annotations

import argparse
import json
from typing import Mapping, Sequence

from .common import (
    KnowledgeHubError,
    ensure_private_directory_tree,
    ensure_private_file,
    repository_root,
    resolve_inside,
)
from .repository_private_ratchet import build_repository_private_candidate

CANONICAL_REGISTRY = "registry/knowledge-platform-p5-p10.json"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--repository-metadata", required=True)
    parser.add_argument("--expected-repository", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--run-attempt", required=True, type=int)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--candidate-output", required=True)
    parser.add_argument("--proposal-output", required=True)
    return parser


def _write(root, relative: str, payload: Mapping[str, object]) -> None:
    path = resolve_inside(root, relative)
    canonical = resolve_inside(root, CANONICAL_REGISTRY)
    if path == canonical:
        raise KnowledgeHubError("repository privacy ratchet must never write the canonical registry")
    ensure_private_directory_tree(root, path.parent)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ensure_private_file(path)


def main(argv: Sequence[str] = ()) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        candidate, proposal = build_repository_private_candidate(
            registry_path=resolve_inside(root, CANONICAL_REGISTRY),
            repository_metadata_path=resolve_inside(root, args.repository_metadata),
            expected_repository=args.expected_repository,
            source_revision=args.source_revision,
            run_id=args.run_id,
            run_attempt=args.run_attempt,
            observed_at=args.observed_at,
        )
        _write(root, args.candidate_output, candidate)
        _write(root, args.proposal_output, proposal)
    except (KnowledgeHubError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(proposal, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
