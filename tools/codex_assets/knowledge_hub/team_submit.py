"""Small-team Git knowledge submission. Only canonical capture writes metadata.

This command is run on an engineer's Linux workstation, never by the MCP server.
GitHub writes use the engineer's own git/gh credentials and a detached worktree.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import pathlib
import re
import subprocess
import tempfile
import uuid

from .common import (
    KnowledgeHubError, encode_jsonl, file_sha256, load_markdown,
    registry_items, render_markdown, resolve_inside, utc_timestamp,
)
from .indexing import CORE_INDEXES, update_core_indexes, update_project_index, update_topic_index
from .lifecycle import capture, _append_event
from .model import merge_frontmatter_mirror, require_valid_item
from .obsidian_view import stage_obsidian_views
from .store import RepositoryTransaction, snapshot_inputs
from .common import route_rows

KINDS = {"debug-record", "runbook", "audit", "validation", "decision", "architecture"}
DIGEST = re.compile(r"^[a-f0-9]{64}$")
PROJECT = re.compile(r"^[a-z0-9][a-z0-9-]{0,80}$")
LEAK = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"\b(?:ghp_|gho_|github_pat_|sk-)[A-Za-z0-9_-]{12,}|"
    r"\bAKIA[0-9A-Z]{16}\b|"
    r"(?i:password|api[_-]?key|access[_-]?token)\s*[:=]\s*[^ \t\n]{8,}|"
    r"(?<!\d)192\.168\.(?:\d{1,3}\.)\d{1,3}|"
    r"(?<!\d)10\.(?:\d{1,3}\.){2}\d{1,3}"
)


def _safe_source(path: pathlib.Path) -> str:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 131072:
        raise KnowledgeHubError("source must be a regular Markdown file <=128KiB")
    text = path.read_text(encoding="utf-8")
    if not text.strip() or LEAK.search(text):
        raise KnowledgeHubError("source is empty or contains restricted material")
    if "\x00" in text:
        raise KnowledgeHubError("source contains a binary marker")
    return text


def _git(cwd: pathlib.Path, *argv: str, timeout: int = 120) -> str:
    process = subprocess.run(["git", "-C", str(cwd), *argv], capture_output=True,
                             text=True, timeout=timeout, check=False)
    if process.returncode:
        # Never echo Git output; it can contain remote addresses or credentials.
        raise KnowledgeHubError("git operation failed: {}".format(argv[0]))
    return process.stdout.rstrip("\n")


def _route(root: pathlib.Path, project: str) -> str:
    if not PROJECT.fullmatch(project):
        raise KnowledgeHubError("invalid project ID")
    rows = [row for row in route_rows(root) if row.get("project_id") == project]
    if len(rows) != 1:
        raise KnowledgeHubError("project must match one registered route")
    target = str(rows[0].get("current_path", ""))
    if target != "projects/{}/current".format(project):
        raise KnowledgeHubError("team submit only supports registered project current paths")
    return target + "/team-knowledge"


def create_candidate(root: pathlib.Path, source: pathlib.Path, project: str, kind: str, today: dt.date, *, apply: bool) -> dict:
    if kind not in KINDS:
        raise KnowledgeHubError("unsupported team knowledge kind")
    base = _route(root, project)
    safe = _safe_source(source)
    # Names never depend on the ASCII-only title slug.
    item_id = "{}-{}-{}-{}".format(
        project, kind, today.strftime("%Y%m%d"), hashlib.sha256(safe.encode("utf-8")).hexdigest()[:12]
    )
    target = "{}/{}.md".format(base, item_id)
    # Temporary source has content provenance without leaking engineer's cwd.
    with tempfile.TemporaryDirectory(prefix="kh-submit-source-") as folder:
        staged = pathlib.Path(folder) / "candidate.md"
        staged.write_text(safe, encoding="utf-8")
        return capture(root, staged, kind, target, today, apply, item_id=item_id,
                       domain="projects/" + project, owner="team-core",
                       visibility="team-internal", status="reviewing",
                       generated_by_ai=False, source_type="ephemeral-file-capture",
                       source_from="ephemeral-content-sha256:" + hashlib.sha256(safe.encode("utf-8")).hexdigest())


def update_candidate(
    root: pathlib.Path, item_id: str, source: pathlib.Path,
    expected_sha256: str, today: dt.date, *, apply: bool,
) -> dict:
    """Reviewing-only CAS edit through the existing journaled transaction store."""
    if not DIGEST.fullmatch(expected_sha256):
        raise KnowledgeHubError("update requires exact expected content SHA256")
    rows = registry_items(root)
    found = [row for row in rows if row.get("id") == item_id]
    if len(found) != 1 or found[0].get("status") != "reviewing":
        raise KnowledgeHubError("only one registered reviewing item may be updated")
    before = found[0]
    relative = str(before["path"])
    domain = str(before.get("domain", ""))
    project = domain.split("/", 1)[1] if domain.startswith("projects/") else ""
    if not relative.startswith(_route(root, project) + "/") or not relative.endswith(".md"):
        raise KnowledgeHubError("ordinary update may only edit team-knowledge/current")
    actual = file_sha256(resolve_inside(root, relative))
    if actual != expected_sha256:
        raise KnowledgeHubError("content SHA conflict")
    raw = _safe_source(source)
    current_meta, old_body = load_markdown(resolve_inside(root, relative))
    if raw.lstrip().startswith("---\n"):
        with tempfile.TemporaryDirectory(prefix="kh-submit-parse-") as folder:
            staged = pathlib.Path(folder) / "note.md"
            staged.write_text(raw, encoding="utf-8")
            _, new_body = load_markdown(staged)
    else:
        new_body = raw
    if not new_body.strip():
        raise KnowledgeHubError("empty updated body")
    after = dict(before)
    after.update(
        updated_at=today.isoformat(),
        manual_validation_pending=True,
        review_status="manual-entry-pending-review",
        content_review_status="pending",
        evidence_validation_status="pending",
        evidence_strength="manual-entry-validation-pending",
        source={"type": "ephemeral-file-capture", "from": "ephemeral-content-sha256:" + hashlib.sha256(raw.encode()).hexdigest(),
                "source_sha256": hashlib.sha256(raw.encode()).hexdigest()},
    )
    for field in ("human_reviewed_by", "human_reviewed_at", "review_attestation_source_ref",
                  "review_content_sha256", "human_review_content_sha256"):
        after.pop(field, None)
    require_valid_item(after)
    rendered = render_markdown(merge_frontmatter_mirror(current_meta, after), new_body)
    if rendered.encode("utf-8") == resolve_inside(root, relative).read_bytes():
        return {"status": "no-change", "id": item_id, "changed_paths": []}
    inputs = snapshot_inputs(root)
    txn = RepositoryTransaction(root, expected_inputs=inputs)
    txn.add_text(relative, rendered)
    next_rows = [after if row.get("id") == item_id else row for row in rows]
    txn.add_text("registry/items.jsonl", encode_jsonl(next_rows))
    indexes = {name: (root / name).read_text(encoding="utf-8") for name in CORE_INDEXES}
    for path, text in update_core_indexes(indexes, after).items():
        txn.add_text(path, text)
    for path, func in (("indexes/by-project.md", update_project_index),
                       ("indexes/by-topic.md", update_topic_index)):
        text = (root / path).read_text(encoding="utf-8")
        txn.add_text(path, func(text, after))
    event = {"event_id": "team-update-{}-{}".format(item_id, uuid.uuid4().hex[:10]),
             "event_type": "team-knowledge-update", "item_id": item_id,
             "before_status": "reviewing", "after_status": "reviewing",
             "authorization_id": "", "executed_by": "knowledge-submit",
             "executed_at": utc_timestamp(), "evidence_refs": [relative]}
    txn.add_text("registry/lifecycle-events.jsonl", _append_event(root, event))
    staged = stage_obsidian_views(root, txn, items=next_rows, document_overrides={relative: rendered})
    if staged["missing_files"] or staged["content_drifts"]:
        raise KnowledgeHubError("derived views inconsistent")
    plan = txn.plan()
    if apply:
        txn.apply()
    return {"status": "applied" if apply else "planned", "id": item_id,
            "changed_paths": [p["path"] for p in plan["writes"] if p["changed"]]}


def _permitted_change(path: str, target_project: str) -> bool:
    return (path in {"registry/items.jsonl", "registry/lifecycle-events.jsonl"}
            or path.startswith("indexes/")
            or path.startswith("projects/{}/current/team-knowledge/".format(target_project))
            or path == "README.md")


def _status_files(cwd: pathlib.Path) -> list:
    raw = _git(cwd, "status", "--porcelain", "-z")
    files = []
    for row in raw.split("\x00"):
        if row:
            if len(row) < 4 or row[:2].strip() not in {"M", "A", "??"}:
                raise KnowledgeHubError("unexpected worktree status")
            files.append(row[3:])
    return files


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Create a governed knowledge PR from an independent worktree")
    parser.add_argument("operation", choices=("create", "update"))
    parser.add_argument("--hub-repo", default=str(pathlib.Path.home() / "knowledge-hub"))
    parser.add_argument("--project", default="")
    parser.add_argument("--kind", default="debug-record")
    parser.add_argument("--item-id", default="")
    parser.add_argument("--expected-sha256", default="")
    parser.add_argument("--source", required=True)
    parser.add_argument("--public-approved", action="store_true")
    parser.add_argument("--create-pr", action="store_true")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--base-remote", default="origin")
    parser.add_argument("--push-remote", default="origin")
    parser.add_argument("--pr-repository", default="jiying2007/knowledge-hub")
    parser.add_argument("--head-owner", default="")
    parser.add_argument("--supersedes-pr", type=int, default=0)
    args = parser.parse_args(argv)
    if not args.public_approved:
        parser.error("confirm that the source may be disclosed in the configured Git remote")
    if (not re.fullmatch(r"[A-Za-z0-9._-]+", args.base_remote)
            or not re.fullmatch(r"[A-Za-z0-9._-]+", args.push_remote)
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.pr_repository)
            or args.head_owner and not re.fullmatch(r"[A-Za-z0-9_.-]+", args.head_owner)
            or args.supersedes_pr < 0):
        parser.error("invalid Git remote/PR identity")
    source = pathlib.Path(args.source).expanduser().resolve()
    hub = pathlib.Path(args.hub_repo).expanduser().resolve()
    today = dt.date.today()
    if not (hub / "registry/items.jsonl").is_file():
        parser.error("--hub-repo must identify a full Knowledge Hub checkout")
    _safe_source(source)
    if not args.offline:
        _git(hub, "fetch", "--no-tags", args.base_remote, "master")
    ref = _git(hub, "rev-parse", "master" if args.offline else "FETCH_HEAD")
    worktree = pathlib.Path(tempfile.mkdtemp(prefix="kh-team-submit-"))
    name = "team/{}-{}".format(today.strftime("%Y%m%d"), uuid.uuid4().hex[:12])
    try:
        _git(hub, "worktree", "add", "--detach", str(worktree), ref)
        _git(worktree, "switch", "-c", name)
        if args.operation == "create":
            if not args.project:
                raise KnowledgeHubError("create requires explicit --project")
            project = args.project
            preview = create_candidate(worktree, source, project, args.kind, today, apply=False)
            if preview.get("status") == "no-change":
                raise KnowledgeHubError("item already exists; choose update with a content digest")
            result = create_candidate(worktree, source, project, args.kind, today, apply=True)
        else:
            if not args.item_id:
                raise KnowledgeHubError("update requires --item-id")
            current = next((v for v in registry_items(worktree) if v.get("id") == args.item_id), None)
            if current is None:
                raise KnowledgeHubError("item not found")
            domain = str(current.get("domain", ""))
            project = domain.split("/", 1)[1] if domain.startswith("projects/") else ""
            preview = update_candidate(worktree, args.item_id, source, args.expected_sha256, today, apply=False)
            result = update_candidate(worktree, args.item_id, source, args.expected_sha256, today, apply=True)
        if result.get("status") == "no-change":
            print("status=no-change item_id={}".format(args.item_id))
            return 0
        paths = _status_files(worktree)
        if not paths or any(not _permitted_change(path, project) for path in paths):
            raise KnowledgeHubError("knowledge PR changed unsupported paths")
        _git(worktree, "add", "--", *paths)
        _git(worktree, "diff", "--cached", "--check")
        _git(worktree, "commit", "-m", "docs(knowledge): submit team {} for {}".format(args.operation, project))
        if args.create_pr and not args.offline:
            _git(worktree, "push", "-u", args.push_remote, name)
            head = args.head_owner + ":" + name if args.head_owner else name
            command = ["gh", "pr", "create", "--repo", args.pr_repository, "--base", "master", "--head", head,
                       "--title", "docs(knowledge): team {} {}".format(args.operation, project),
                       "--body", "Shared reviewing candidate; no active promotion. Review source, version, duplicate and public-sharing boundaries."
                       + (" Supersedes PR #{} (previous proposal requires closure).".format(args.supersedes_pr)
                          if args.supersedes_pr else "")]
            try:
                pr = subprocess.run(command, cwd=str(worktree), capture_output=True, text=True, timeout=60)
            except (OSError, subprocess.TimeoutExpired):
                pr = None
            if pr and pr.returncode == 0 and pr.stdout.strip().startswith("https://"):
                try:
                    _git(hub, "worktree", "remove", "--force", str(worktree))
                except KnowledgeHubError:
                    pass  # Retain diagnostic worktree; remote PR itself has succeeded.
                print("status=pr-created url={} branch={} base_sha={}".format(pr.stdout.strip(), name, ref))
                return 0
            print("status=prepared-local reason=pr-not-created branch={} path={}".format(name, worktree))
            return 2
        print("status=prepared-local branch={} path={} base_sha={}".format(name, worktree, ref))
        return 0
    except (KnowledgeHubError, OSError, subprocess.TimeoutExpired) as exc:
        # Keep the isolated worktree for diagnostics; never claim a PR.
        print("status=blocked kind={} worktree={}".format(type(exc).__name__, worktree))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
