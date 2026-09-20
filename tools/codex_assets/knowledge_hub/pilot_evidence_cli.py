"""Project real provider/production observations into strict external evidence."""

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
from .pilot_evidence import build_pilot_evidence, load_pilot_observation
from .schemas import validate_instance

CANONICAL_REGISTRY = "registry/knowledge-platform-p5-p10.json"

OBSERVATION_CONTRACTS = {
    "connector-provider-pilot": "connector-provider-observation-v1",
    "production-retrieval-eval": "production-retrieval-observation-v1",
    "memory-lifecycle-pilot": "production-memory-observation-v1",
    "real-adoption-evidence": "production-adoption-observation-v1",
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--input", required=True)
    parser.add_argument("--expected-gap", required=True)
    parser.add_argument("--output", required=True)
    return parser


def _write_json(root, relative: str, payload: Mapping[str, object]) -> None:
    path = resolve_inside(root, relative)
    canonical = resolve_inside(root, CANONICAL_REGISTRY)
    if path == canonical:
        raise KnowledgeHubError("pilot evidence CLI must never write the canonical registry")
    ensure_private_directory_tree(root, path.parent)
    path.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    ensure_private_file(path)


def main(argv: Sequence[str] = ()) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        source = resolve_inside(root, args.input)
        observation = load_pilot_observation(source)
        contract_id = OBSERVATION_CONTRACTS.get(args.expected_gap, "")
        if not contract_id:
            raise KnowledgeHubError("pilot observation gap is unsupported")
        validation = validate_instance(root, contract_id, observation)
        if validation.get("status") != "pass":
            raise KnowledgeHubError(
                "pilot observation schema validation failed: {}".format(
                    validation.get("errors", [])
                )
            )
        payload = build_pilot_evidence(
            observation,
            expected_gap=args.expected_gap,
        )
        _write_json(root, args.output, payload)
    except (KnowledgeHubError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(
        json.dumps(
            {
                "status": "external-evidence-ready",
                "gap_id": payload["gap_id"],
                "canonical_write_performed": False,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
