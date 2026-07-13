#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import json
import os
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Search Knowledge Hub and registered sources.")
parser.add_argument("query")
parser.add_argument("--json", action="store_true")
parser.add_argument("--limit", type=int, default=20)
parser.add_argument("--source", action="append", default=[], help="Physical scan source id, for example knowledge-hub or pcr02-project-docs.")
parser.add_argument("--owner", action="append", default=[], help="Filter local registered items by registry owner. Repeatable.")
parser.add_argument("--status", action="append", default=[], help="Filter local registered items by registry status. Repeatable.")
parser.add_argument("--kind", action="append", default=[], help="Filter local registered items by registry kind. Repeatable.")
parser.add_argument("--domain", action="append", default=[], help="Filter local registered items by registry domain prefix. Repeatable.")
parser.add_argument("--source-id", action="append", default=[], help="Filter local registered items by registry source.source_id. Repeatable.")
args = parser.parse_args(argv)

query = args.query.lower()

if args.limit < 1:
    parser.error("--limit must be >= 1")

def user_path_prefixes():
    prefixes = [str(pathlib.Path.home())]
    user_name = os.environ.get("USER", "")
    if user_name:
        prefixes.append("/" + "vsdata" + "/" + user_name)
    return [prefix for prefix in prefixes if prefix and prefix != "/"]

def display_path(value):
    text = str(value)
    for prefix in user_path_prefixes():
        if text == prefix:
            text = "~"
        elif text.startswith(prefix + "/"):
            text = "~" + text[len(prefix):]
        else:
            text = text.replace(prefix, "~")
    return text

allowed_statuses = {"draft", "active", "reviewing", "archived", "superseded", "rejected", "personal"}
allowed_kinds = {
    "standard",
    "runbook",
    "architecture",
    "decision",
    "project-current",
    "project-archive",
    "validation",
    "audit",
    "patent",
    "debug-record",
    "external-source-note",
    "owner-decision-worksheet",
    "patent-disclosure",
    "codex-session",
    "codex-workflow",
    "personal-note",
    "artifact-ref",
}
kind_aliases = {
    "validation-report": "validation",
    "archive-note": "project-archive",
    "external-source": "external-source-note",
    "owner-worksheet": "owner-decision-worksheet",
}
normalized_kinds = [kind_aliases.get(kind, kind) for kind in args.kind]
invalid_statuses = sorted(set(args.status) - allowed_statuses)
invalid_kinds = sorted(kind for kind in set(args.kind) if kind_aliases.get(kind, kind) not in allowed_kinds)
if invalid_statuses:
    parser.error(f"invalid --status value(s): {', '.join(invalid_statuses)}; allowed: {', '.join(sorted(allowed_statuses))}")
if invalid_kinds:
    allowed_kind_values = sorted(allowed_kinds | set(kind_aliases))
    parser.error(f"invalid --kind value(s): {', '.join(invalid_kinds)}; allowed: {', '.join(allowed_kind_values)}")

def load_registry_items():
    path = root / "registry" / "items.jsonl"
    by_path = {}
    rows = []
    if not path.exists():
        return by_path, rows
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except Exception:
            continue
        rows.append(item)
        item_path = item.get("path")
        if not item_path:
            continue
        try:
            full_path = (root / item_path).resolve()
        except Exception:
            continue
        by_path.setdefault(str(full_path), []).append(item)
    return by_path, rows

registry_by_path, registry_items = load_registry_items()

def item_source_id(item):
    source = item.get("source")
    if isinstance(source, dict):
        return source.get("source_id", "")
    return ""

def item_matches_filters(item):
    if args.owner and item.get("owner", "") not in args.owner:
        return False
    if args.status and item.get("status", "") not in args.status:
        return False
    if normalized_kinds and item.get("kind", "") not in normalized_kinds:
        return False
    if args.domain and not any(item.get("domain", "").startswith(prefix) for prefix in args.domain):
        return False
    if args.source_id and item_source_id(item) not in args.source_id:
        return False
    return True

def has_structured_filters():
    return bool(args.owner or args.status or args.kind or args.domain or args.source_id)

def metadata_for_item(item):
    return {
        "item_id": item.get("id", ""),
        "title": item.get("title", ""),
        "kind": item.get("kind", ""),
        "domain": item.get("domain", ""),
        "status": item.get("status", ""),
        "owner": item.get("owner", ""),
        "source_id": item_source_id(item),
        "review_after": item.get("review_after", ""),
        "tags": item.get("tags", []),
    }

def registry_metadata_haystack(item):
    fields = [
        item.get("id", ""),
        item.get("title", ""),
        item.get("path", ""),
        item.get("kind", ""),
        item.get("domain", ""),
        item.get("status", ""),
        item.get("owner", ""),
        item.get("summary_zh", ""),
        item.get("review_status", ""),
        item_source_id(item),
    ]
    tags = item.get("tags", [])
    if isinstance(tags, list):
        fields.extend(str(tag) for tag in tags)
    source = item.get("source")
    if isinstance(source, dict):
        fields.extend(str(value) for value in source.values() if isinstance(value, (str, int, float)))
    return "\n".join(str(value) for value in fields if value).lower()

sources = [
    {"id": "knowledge-hub", "path": str(root)},
]
sources_path = root / "registry" / "sources.json"
if sources_path.exists():
    data = json.loads(sources_path.read_text())
    sources.extend(data.get("sources", []))
retired_sources_path = root / "registry" / "retired-sources.jsonl"
if retired_sources_path.exists():
    for line in retired_sources_path.read_text().splitlines():
        if line.strip():
            sources.append(json.loads(line))

allowed_suffixes = {".md", ".txt", ".json", ".jsonl", ".csv"}
query_terms = re.findall(r"[a-z0-9_./:+-]+|[\u4e00-\u9fff]+", query)
if not query_terms:
    query_terms = [query]

def terms_match(haystack):
    return all(term in haystack for term in query_terms)

def path_priority(relative):
    normalized = relative.replace("\\", "/")
    if normalized == "README.md":
        return 100, "root-entry"
    if normalized.startswith("projects/") and any(
        segment in normalized for segment in ("/current/", "/decisions/", "/validation/")
    ):
        return 120, "project-canonical"
    if normalized.startswith("domains/embedded/") and any(
        segment in normalized for segment in ("/runbooks/", "/standards/", "/architecture/")
    ):
        return 115, "domain-canonical"
    if normalized.startswith("projects/") and "/archive/" in normalized:
        return 70, "project-archive"
    if normalized.startswith("governance/status/"):
        return 80, "governance-status"
    if normalized.startswith("governance/"):
        return 65, "governance"
    if normalized.startswith("indexes/"):
        return 45, "derived-index"
    if normalized.startswith("tools/"):
        return 25, "tooling"
    if normalized.startswith("artifacts/manifests/"):
        return 5, "historical-manifest"
    if normalized.startswith("registry/"):
        return 0, "registry-ledger"
    return 40, "body"

def status_priority(status):
    return {"active": 80, "reviewing": 50, "draft": 25, "archived": 10}.get(status, 0)

def score_candidate(relative, suffix, body_haystack, item):
    metadata_haystack = registry_metadata_haystack(item) if item else ""
    combined = metadata_haystack + "\n" + body_haystack
    if not terms_match(combined):
        return None
    title = str(item.get("title", "")).lower() if item else ""
    item_id = str(item.get("id", "")).lower() if item else ""
    path_text = str(item.get("path", relative)).lower() if item else relative.lower()
    summary = str(item.get("summary_zh", "")).lower() if item else ""
    tags = "\n".join(str(tag).lower() for tag in item.get("tags", [])) if item and isinstance(item.get("tags"), list) else ""
    score, path_reason = path_priority(relative)
    reasons = [path_reason]
    if item:
        score += 300 + status_priority(str(item.get("status", "")))
        reasons.extend(["registry-backed", f"status:{item.get('status', '')}"])
    if query and query in title:
        score += 160
        reasons.append("exact-title")
    elif title and terms_match(title):
        score += 110
        reasons.append("title-tokens")
    if query and query in item_id:
        score += 135
        reasons.append("exact-id")
    elif item_id and terms_match(item_id):
        score += 90
        reasons.append("id-tokens")
    if tags and terms_match(tags):
        score += 90
        reasons.append("tag-tokens")
    if summary and terms_match(summary):
        score += 65
        reasons.append("summary-tokens")
    if path_text and terms_match(path_text):
        score += 55
        reasons.append("path-tokens")
    if query and query in body_haystack:
        score += 40
        reasons.append("exact-body")
    elif terms_match(body_haystack):
        score += 20
        reasons.append("body-tokens")
    if suffix in {".json", ".jsonl"}:
        score -= 45
        reasons.append("structured-ledger-penalty")
    if relative.startswith("artifacts/manifests/"):
        score -= 55
        reasons.append("historical-penalty")
    if relative.startswith("registry/"):
        score -= 100
        reasons.append("registry-noise-penalty")
    return score, reasons

candidates = []
seen = set()
for source in sources:
    sid = source.get("id", "")
    if args.source and sid not in args.source:
        continue
    base = pathlib.Path(str(source.get("path", "")).replace("~", str(pathlib.Path.home()))).expanduser()
    if not base.is_absolute():
        base = root / base
    if not base.exists():
        continue
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in allowed_suffixes:
            continue
        try:
            relative = path.resolve().relative_to(root).as_posix()
        except Exception:
            relative = path.name
        if any(part in {".git", ".tmp", ".cache"} for part in path.parts):
            continue
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        try:
            text = path.read_text(errors="ignore")
        except Exception:
            continue
        items = registry_by_path.get(key, [])
        matching_items = [item for item in items if item_matches_filters(item)]
        if has_structured_filters() and not matching_items:
            continue
        lower = text.lower()
        item_candidates = matching_items if matching_items else (items if items else [{}])
        scored_items = []
        for item in item_candidates:
            scored = score_candidate(relative, path.suffix.lower(), lower, item)
            if scored is not None:
                scored_items.append((scored[0], scored[1], item))
        if not scored_items:
            continue
        score, reasons, item = max(scored_items, key=lambda row: (row[0], str(row[2].get("id", ""))))
        indexes = [lower.find(term) for term in query_terms if lower.find(term) >= 0]
        index = min(indexes) if indexes else -1
        line_no = lower[:index].count("\n") + 1
        lines = text.splitlines()
        line = lines[line_no - 1][:240] if index >= 0 and lines else ""
        if index < 0:
            line_no = 1
            line = f"registry metadata: {item.get('summary_zh') or item.get('title') or item.get('id', '')}"[:240]
        result = {
            "source": sid,
            "path": display_path(path),
            "line": line_no,
            "preview": line,
            "score": score,
            "match": "body-and-metadata" if index >= 0 and item else "body" if index >= 0 else "registry-metadata",
            "match_kind": reasons[0],
            "why_selected": reasons,
        }
        if item:
            result.update(metadata_for_item(item))
        candidates.append(result)

metadata_fallback_enabled = not args.source or "knowledge-hub" in args.source
result_item_ids = {
    str(row.get("item_id", "")) for row in candidates if row.get("item_id")
}
if metadata_fallback_enabled:
    for item in registry_items:
        item_id = str(item.get("id", ""))
        if item_id and item_id in result_item_ids:
            continue
        if not item_matches_filters(item):
            continue
        metadata_haystack = registry_metadata_haystack(item)
        if not terms_match(metadata_haystack):
            continue
        path_text = str(item.get("path", ""))
        relative = path_text or "README.md"
        scored = score_candidate(relative, pathlib.Path(relative).suffix.lower(), "", item)
        if scored is None:
            continue
        score, reasons = scored
        result = {
            "source": "knowledge-hub",
            "path": display_path((root / path_text).resolve()) if path_text else display_path(root),
            "line": 1,
            "preview": f"registry metadata: {item.get('summary_zh') or item.get('title') or item_id}"[:240],
            "match": "registry-metadata",
            "score": score,
            "match_kind": reasons[0],
            "why_selected": reasons,
        }
        result.update(metadata_for_item(item))
        candidates.append(result)

candidates.sort(
    key=lambda row: (
        -int(row.get("score", 0)),
        str(row.get("path", "")),
        str(row.get("item_id", "")),
    )
)
results = candidates[: args.limit]
total_matches = len(candidates)

if args.json:
    filters = {
        "source": args.source,
        "owner": args.owner,
        "status": args.status,
        "kind": args.kind,
        "kind_normalized": normalized_kinds,
        "domain": args.domain,
        "source_id": args.source_id,
    }
    print(json.dumps({
        "query": args.query,
        "query_terms": query_terms,
        "count": len(results),
        "total_matches": total_matches,
        "ranking": "registry-metadata-plus-canonical-path-and-status-v1",
        "filters": filters,
        "results": results,
    }, ensure_ascii=False, indent=2))
else:
    print(f"query: {args.query}")
    print(f"count: {len(results)}")
    for item in results:
        metadata = ""
        if item.get("item_id"):
            metadata = (
                f" [item={item.get('item_id', '')}"
                f" owner={item.get('owner', '')}"
                f" status={item.get('status', '')}"
                f" kind={item.get('kind', '')}"
                f" domain={item.get('domain', '')}"
                f" source_id={item.get('source_id', '')}]"
            )
        print(f"{item['source']}:{item['path']}:{item['line']}{metadata}: {item['preview']}")
sys.exit(0 if results else 1)
PY
