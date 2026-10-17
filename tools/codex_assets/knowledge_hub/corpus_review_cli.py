"""Emit a complete, redacted, read-only review of every canonical registry item."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import tempfile

from .common import KnowledgeHubError, ensure_private_directory_tree, repository_root
from .corpus_review import build_corpus_review


def _summary(result):
    return {
        key: result[key]
        for key in (
            "schema_version", "as_of", "source_revision", "report_sha256",
            "item_count", "accounted_for_count", "machine_checked_count",
            "private_excluded_count", "total_body_bytes", "status_counts",
            "lane_counts", "signal_counts", "duplicates",
            "report_only", "canonical_write_performed",
            "semantic_review_performed", "owner_approval_performed",
        )
    }


def _save_ignored(root: pathlib.Path, relative: str, data: str) -> str:
    # Never create a second Git-tracked source of knowledge or write outside .tmp.
    path = pathlib.PurePosixPath(relative)
    if (
        not relative.startswith(".tmp/knowledge-hub/")
        or path.is_absolute() or ".." in path.parts
        or any(part.startswith(".") for part in path.parts[1:])
        or not relative.endswith(".json")
    ):
        raise KnowledgeHubError("corpus output must be a JSON file under .tmp/knowledge-hub/")
    parent = root / pathlib.Path(*path.parts[:-1])
    ensure_private_directory_tree(root, parent)
    target = parent / path.name
    if target.is_symlink():
        raise KnowledgeHubError("private report cannot overwrite a symlink")
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", prefix=".review-", suffix=".tmp",
        dir=str(parent), delete=False,
    ) as handle:
        temporary = pathlib.Path(handle.name)
        os.chmod(str(temporary), 0o600)
        handle.write(data)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(str(temporary), str(target))
    return str(target.relative_to(root))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--as-of", default=dt.date.today().isoformat())
    parser.add_argument("--output", default="")
    parser.add_argument("--json", action="store_true", help="Print full redacted per-item report")
    args = parser.parse_args(argv)
    root = repository_root(args.root)
    try:
        today = dt.date.fromisoformat(args.as_of)
        result = build_corpus_review(root, today)
        encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        saved = _save_ignored(root, args.output, encoded) if args.output else ""
        selected = result if args.json else _summary(result)
        if saved:
            selected = dict(selected, report_path=saved)
        print(json.dumps(selected, ensure_ascii=False, sort_keys=True))
        return 0
    except (KnowledgeHubError, ValueError, OSError) as exc:
        print(json.dumps({"status": "invalid", "reason": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
