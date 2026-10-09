import argparse
import collections
import datetime as dt
import json
import pathlib
import sys

from tools.codex_assets.knowledge_hub.review_triage import _EvidenceReader, _body_evidence, _reference

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(
    prog="knowledge-reviewing-triage.sh",
    description="Summarize reviewing Knowledge Hub items for periodic triage.",
)
parser.add_argument("--json", action="store_true", help="Print JSON output.")
parser.add_argument("--as-of", default=dt.date.today().isoformat(), metavar="YYYY-MM-DD")
parser.add_argument("--window-days", type=int, default=30, help="Near-due review_after window.")
parser.add_argument("--limit", type=int, default=50, help="Maximum reviewing rows to include.")
args = parser.parse_args(argv)

try:
    as_of = dt.date.fromisoformat(args.as_of)
except ValueError:
    parser.error("--as-of must be YYYY-MM-DD")
if args.window_days < 0:
    parser.error("--window-days must be >= 0")
if args.limit < 1:
    parser.error("--limit must be >= 1")


def load_items():
    rows = []
    for line_no, line in enumerate((root / "registry" / "items.jsonl").read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"registry/items.jsonl:{line_no}: invalid JSON: {exc}") from exc
    return rows


def bucket_for(row):
    item_id = row.get("id", "")
    domain = row.get("domain", "")
    kind = row.get("kind", "")
    tags = set(row.get("tags", []) or [])
    if domain == "codex" and ("codex-archive" in tags or "archive" in item_id or "tombstone" in tags):
        return "codex-archive-provenance"
    if domain == "codex":
        return "codex-runtime-governance"
    if domain == "projects/pcr02-ssc305" and kind == "decision":
        return "pcr02-decision-candidate"
    if domain == "projects/pcr02-ssc305":
        return "pcr02-reviewing-record"
    return domain or "uncategorized"


def _current_review(row, reader, as_of):
    decision = row.get('human_review_decision')
    if (reader is None or as_of is None or row.get('content_review_status') != 'accepted'
            or decision not in {'approved-active', 'approved-reviewing', 'accept-as-review-record'}
            or not isinstance(row.get('human_reviewed_by'), str) or not row['human_reviewed_by'].strip()):
        return False
    try:
        if dt.date.fromisoformat(row.get('review_after', '')) <= as_of:
            return False
    except (TypeError, ValueError):
        return False
    body = _body_evidence(reader, row)
    return body['status'] == 'metadata-ready' and body['prior_human_content_hash_matches']


def _verified_evidence(row, reader):
    if reader is None or row.get('evidence_validation_status') != 'verified':
        return False
    evidence, validation = row.get('evidence_refs') or [], row.get('validation_refs') or []
    if not isinstance(evidence, list) or not isinstance(validation, list):
        return False
    refs = evidence + validation
    return bool(refs) and len(refs) <= 16 and all(
        _reference(reader, ref)['status'] == 'local-hash-confirmed' for ref in refs)


def action_for(row, reader=None, as_of=None):
    tags = set(row.get("tags", []) or [])
    has_human_review = _current_review(row, reader, as_of)
    has_evidence = has_human_review and _verified_evidence(row, reader)
    if row.get("decision_status") == "candidate" or "decision-candidate" in tags:
        if has_human_review and has_evidence and row.get('human_review_decision') in {'approved-active', 'approved-reviewing'}:
            return "owner-ready-validation-pending"
        return "owner-review-and-validation"
    if "manual-validation-pending" in tags:
        if has_human_review and has_evidence:
            return "evidence-backed-validation-pending"
        return "evidence-needed"
    if "archive-ready" in tags:
        return "archive-ready-check"
    if row.get("generated_by_ai") and not row.get("human_reviewed_by"):
        return "human-review-needed"
    return "keep-reviewing"


def parse_date(value):
    try:
        return dt.date.fromisoformat(value or "")
    except ValueError:
        return None


items = [row for row in load_items() if row.get("status") == "reviewing"]
window_end = as_of + dt.timedelta(days=args.window_days)
by_bucket = collections.Counter(bucket_for(row) for row in items)
reader = _EvidenceReader(root)
prepared = [(row, action_for(row, reader, as_of)) for row in items]
by_action = collections.Counter(action for _, action in prepared)
near_due = []
for row in items:
    review_after = parse_date(row.get("review_after", ""))
    if review_after and review_after <= window_end:
        near_due.append(row)

rows = []
for row, action in sorted(prepared, key=lambda pair: (pair[0].get("review_after", ""), pair[0].get("domain", ""), pair[0].get("id", ""))):
    rows.append(
        {
            "id": row.get("id", ""),
            "title": row.get("title", ""),
            "domain": row.get("domain", ""),
            "kind": row.get("kind", ""),
            "owner": row.get("owner", ""),
            "review_after": row.get("review_after", ""),
            "bucket": bucket_for(row),
            "recommended_action": action,
            "promotion": row.get("promotion", ""),
            "decision_status": row.get("decision_status", ""),
            "path": row.get("path", ""),
        }
    )

output = {
    "schema_version": 1,
    "read_only": True,
    "report_only": True,
    "as_of": args.as_of,
    "window_days": args.window_days,
    "reviewing_count": len(items),
    "near_due_count": len(near_due),
    "by_bucket": dict(sorted(by_bucket.items())),
    "by_recommended_action": dict(sorted(by_action.items())),
    "items": rows[: args.limit],
    "evidence_bytes_read":reader.total,
    "evidence_byte_overflow":reader.overflow,
    "must_not": [
        "不生成 owner decision",
        "不关闭 owner gate",
        "不提升 active",
        "不写 memory",
        "不修改源项目",
    ],
}

if args.json:
    print(json.dumps(output, ensure_ascii=False, indent=2))
else:
    print("# Knowledge Hub Reviewing Triage")
    print()
    print(f"- as_of: {output['as_of']}")
    print(f"- reviewing: {output['reviewing_count']}")
    print(f"- near_due: {output['near_due_count']}")
    print(f"- by_bucket: {output['by_bucket']}")
    print(f"- by_action: {output['by_recommended_action']}")
    for row in output["items"]:
        print(f"- {row['review_after']}: `{row['id']}` [{row['bucket']}] {row['recommended_action']}")
