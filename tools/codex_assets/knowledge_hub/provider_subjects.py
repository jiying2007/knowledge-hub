"""Host-owned subject routing and exact, operation-specific authorization."""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import re

from .common import KnowledgeHubError, load_json, load_jsonl, route_rows, file_sha256, resolve_inside
from .store import incomplete_transactions, WriteConflict

POLICY_PATH = "registry/provider-subject-policy.json"
GRANTS_PATH = "registry/provider-grants.jsonl"
OPERATIONS_PATH = "registry/provider-operations.jsonl"
BINDINGS_PATH = "local/provider-bindings.json"
PRINCIPAL_PATH = "local/provider-principal.json"
WORKSPACES_PATH = "registry/provider-workspaces.json"
SUBJECT_TYPES = {"project", "domain", "personal", "unassigned"}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def subject(value):
    if isinstance(value, str):
        parts = value.split(":")
        value = {"type": parts[0], "id": parts[1]} if len(parts) == 2 else {}
    if not isinstance(value, dict) or set(value) != {"type", "id"}:
        raise KnowledgeHubError("SCHEMA_INVALID")
    if value["type"] not in SUBJECT_TYPES or not isinstance(value["id"], str):
        raise KnowledgeHubError("SCHEMA_INVALID")
    pattern = r"[a-z0-9][a-z0-9-]{0,80}" if value["type"] in {"project", "domain"} else r"[A-Za-z0-9][A-Za-z0-9._+-]{0,159}"
    if re.fullmatch(pattern, value["id"]) is None:
        raise KnowledgeHubError("SCHEMA_INVALID")
    return dict(value)


def policy(root):
    value = load_json(root / POLICY_PATH, {})
    from .schemas import validate_instance
    if validate_instance(root, "provider-subject-policy-v1", value)["status"] != "pass":
        raise KnowledgeHubError("POLICY_DENIED")
    required = {"schema_version", "enabled", "owner_id", "actions", "domains", "configured_principal", "authorization_basis"}
    if (not isinstance(value, dict) or set(value) != required or value.get("schema_version") != 1
            or value.get("enabled") is not True or type(value.get("configured_principal")) is not bool
            or not isinstance(value.get("actions"), list) or not isinstance(value.get("domains"), list)):
        raise KnowledgeHubError("POLICY_DENIED")
    owners = load_json(root / "registry/owners.json", {}).get("owners", [])
    if value["owner_id"] not in {row.get("id") for row in owners}:
        raise KnowledgeHubError("POLICY_DENIED")
    return value


def principal(root):
    config = load_json(root / PRINCIPAL_PATH, {})
    from .schemas import validate_instance
    if validate_instance(root, "provider-principal-v1", config)["status"] != "pass" or config.get("enabled") is not True:
        raise KnowledgeHubError("PRINCIPAL_UNCONFIGURED")
    value = config["principal_id"]
    subject({"type": "personal", "id": value})
    return value


def authorize(root, action, target, authorization_id="", visibility_change=False, expected_hash="", require_exact=False):
    target = subject(target)
    host = policy(root)
    try:
        actor = principal(root)
    except KnowledgeHubError:
        if action != "read" or target["type"] in {"personal", "unassigned"}:
            raise
        actor = ""
    if action not in host["actions"]:
        raise KnowledgeHubError("POLICY_DENIED")
    if target["type"] in {"personal", "unassigned"} and target["id"] != actor:
        raise KnowledgeHubError("VISIBILITY_DENIED")
    if target["type"] == "domain" and target["id"] not in host["domains"]:
        raise KnowledgeHubError("POLICY_DENIED")
    # Standing candidate grants never authorize reassignment, visibility widening,
    # or a client-authored assertion that a new project was declared by a user.
    if action in {"register", "bind", "assign"} or visibility_change or require_exact:
        matches = [row for row in load_jsonl(root / GRANTS_PATH) if row.get("id") == authorization_id]
        if len(matches) != 1:
            raise KnowledgeHubError("AUTHORIZATION_REQUIRED")
        row = matches[0]
        from .schemas import validate_instance
        if validate_instance(root, "provider-grant-v1", row)["status"] != "pass":
            raise KnowledgeHubError("POLICY_DENIED")
        allowed = {"id", "actor", "action", "subject_ref", "expected_hash", "status", "expires_at", "declaration_sha256", "binding_path_sha256", "visibility_change", "intake_attestation_sha256", "request_sha256"}
        import datetime as dt
        if (set(row) - allowed or row.get("status") != "active" or row.get("actor") != actor
                or row.get("action") != action or row.get("subject_ref") != target
                or not expected_hash or row.get("expected_hash") != expected_hash
                or bool(row.get("visibility_change")) != visibility_change
                or dt.date.fromisoformat(row.get("expires_at", "")) < dt.date.today()):
            raise KnowledgeHubError("POLICY_DENIED")
    return host, actor


def route_subject(root, value, kind="audit"):
    value = subject(value)
    typ, ident = value["type"], value["id"]
    if typ == "project":
        matches = [r for r in route_rows(root) if r.get("project_id") == ident]
        if len(matches) != 1:
            raise KnowledgeHubError("PROJECT_UNREGISTERED")
        base = matches[0].get("validation_path" if kind == "validation" else "archive_path", "")
        if not base.startswith(("projects/", "governance/product/", "domains/codex/")):
            raise KnowledgeHubError("POLICY_DENIED")
        domain = "projects/" + ident if base.startswith("projects/") else "codex" if base.startswith("domains/codex/") else "governance"
        return {"base": base, "domain": domain, "scope": "project-specific" if domain.startswith("projects/") else "team-general", "visibility": "team-internal"}
    if typ == "domain":
        if ident not in {"embedded", "codex"}:
            raise KnowledgeHubError("POLICY_DENIED")
        return {"base": "domains/" + ident + "/archive/provider-candidates", "domain": ident, "scope": "team-general", "visibility": "team-internal"}
    lane = "unassigned" if typ == "unassigned" else "archive"
    return {"base": "notes/personal/" + ident + "/" + lane, "domain": "notes", "scope": "team-general", "visibility": "personal-local"}


def item_subject(item):
    value = item.get("subject_ref")
    if value:
        return subject(value)
    domain = item.get("domain", "")
    return {"type": "project", "id": domain.split("/", 1)[1]} if domain.startswith("projects/") else None


def signatures(root):
    paths = (POLICY_PATH, GRANTS_PATH, BINDINGS_PATH, WORKSPACES_PATH, OPERATIONS_PATH, PRINCIPAL_PATH, "registry/provider-archive-policy.json")
    return {path: file_sha256(root / path) if (root / path).is_file() else "absent" for path in paths}


@contextlib.contextmanager
def read_guard(root):
    """Readers refuse an in-flight or interrupted transaction; never repair it."""
    lock = root / ".tmp/locks/knowledge-hub.lock"
    if lock.is_symlink():
        raise KnowledgeHubError("STORAGE_RECOVERY_REQUIRED")
    from .common import ensure_private_directory, ensure_private_file
    ensure_private_directory(root / ".tmp")
    ensure_private_directory(lock.parent)
    handle = lock.open("a+")
    ensure_private_file(lock)
    try:
        if handle:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise WriteConflict("STORAGE_BUSY") from exc
        if incomplete_transactions(root):
            raise KnowledgeHubError("STORAGE_RECOVERY_REQUIRED")
        yield
    finally:
        if handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()


def verify_item(root, row, expected=""):
    from .common import load_markdown
    from .model import FRONTMATTER_MIRROR_FIELDS
    path = resolve_inside(root, row["path"])
    if not path.is_file():
        raise KnowledgeHubError("CONTENT_DRIFT")
    actual = file_sha256(path)
    metadata, body = load_markdown(path)
    fields = set(FRONTMATTER_MIRROR_FIELDS) | {"subject_ref", "principal_id", "provider_operation_id"}
    if (expected and actual != expected) or any(metadata.get(k) != row[k] for k in fields if k in row):
        raise KnowledgeHubError("CONTENT_DRIFT")
    return actual, metadata, body
