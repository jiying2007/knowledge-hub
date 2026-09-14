"""Export closure-ready real-adoption evidence from production telemetry."""

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
from .production_evidence import export_real_adoption_evidence

CANONICAL_REGISTRY = "registry/knowledge-platform-p5-p10.json"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--provenance", required=True)
    parser.add_argument("--health", required=True)
    parser.add_argument("--traceability", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--output", required=True)
    return parser


def _write_json(root, relative: str, payload: Mapping[str, object]) -> None:
    path = resolve_inside(root, relative)
    canonical = resolve_inside(root, CANONICAL_REGISTRY)
    if path == canonical:
        raise KnowledgeHubError("production evidence CLI must never write the canonical registry")
    ensure_private_directory_tree(root, path.parent)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ensure_private_file(path)


def main(argv: Sequence[str] = ()) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        payload = export_real_adoption_evidence(
            root=root,
            provenance_path=resolve_inside(root, args.provenance),
            health_path=resolve_inside(root, args.health),
            traceability_path=resolve_inside(root, args.traceability),
            source_revision=args.source_revision,
        )
        _write_json(root, args.output, payload)
    except (KnowledgeHubError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
