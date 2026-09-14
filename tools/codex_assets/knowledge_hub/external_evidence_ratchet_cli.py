"""Generate a review-only external evidence canonical ratchet candidate."""

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
from .external_evidence_ratchet import build_external_gap_ratchet_candidate

DEFAULT_REGISTRY = "registry/knowledge-platform-p5-p10.json"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--registry", default=DEFAULT_REGISTRY)
    parser.add_argument("--closure-receipt", required=True)
    parser.add_argument("--intake-receipt", required=True)
    parser.add_argument("--host-binding", required=True)
    parser.add_argument("--candidate-registry", required=True)
    parser.add_argument("--proposal", required=True)
    return parser


def _write_json(root, relative: str, payload: Mapping[str, object]) -> None:
    path = resolve_inside(root, relative)
    canonical = resolve_inside(root, DEFAULT_REGISTRY)
    if path == canonical:
        raise KnowledgeHubError("ratchet candidate CLI must never write the canonical registry")
    ensure_private_directory_tree(root, path.parent)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ensure_private_file(path)


def main(argv: Sequence[str] = ()) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        registry = resolve_inside(root, args.registry)
        closure_receipt = resolve_inside(root, args.closure_receipt)
        intake_receipt = resolve_inside(root, args.intake_receipt)
        host_binding = resolve_inside(root, args.host_binding)
        candidate_relative = args.candidate_registry
        proposal_relative = args.proposal
        candidate, proposal = build_external_gap_ratchet_candidate(
            registry_path=registry,
            closure_receipt_path=closure_receipt,
            intake_receipt_path=intake_receipt,
            host_binding_path=host_binding,
        )
        _write_json(root, candidate_relative, candidate)
        _write_json(root, proposal_relative, proposal)
    except (KnowledgeHubError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(proposal, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
