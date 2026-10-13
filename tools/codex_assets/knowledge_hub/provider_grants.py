"""Host-issued exact grants, backed by the current thread's real request intake."""

from __future__ import annotations

import datetime as dt
import hashlib
import os
import pathlib
import re

from .common import KnowledgeHubError, read_utf8_bounded, load_jsonl, encode_jsonl
from .provider_subjects import policy, principal, subject, digest, GRANTS_PATH, read_guard
from .store import RepositoryTransaction, snapshot_inputs


def attested_request(raw, request_file):
    thread = os.environ.get("CODEX_THREAD_ID", "")
    if re.fullmatch(r"[a-f0-9-]{36}", thread) is None:
        raise KnowledgeHubError("DECLARATION_UNATTESTED")
    sha = hashlib.sha256(raw.encode()).hexdigest()
    import subprocess
    import json
    runtime_env = dict(os.environ)
    runtime_env.pop("PYTHONPATH", None)
    try:
        call = subprocess.run(["rtk", "python3", "-m", "tools.codex_assets", "execution-policy", "--thread-id", thread,
                               "verify-request", "--request-file", str(pathlib.Path(request_file).absolute())],
                              cwd=str(pathlib.Path.home() / "codex"), text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=10, env=runtime_env)
        receipt = json.loads(call.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        raise KnowledgeHubError("DECLARATION_UNATTESTED") from None
    if (call.returncode == 0 and receipt.get("schema_version") == "codex-request-verification/v1"
            and receipt.get("status") == "VERIFIED" and receipt.get("read_only") is True
            and receipt.get("user_message_verified") is True
            and receipt.get("thread_id") == thread and receipt.get("request_sha256") == sha
            and re.fullmatch(r"[a-f0-9]{64}", str(receipt.get("attestation_sha256", "")))):
        return sha, receipt["attestation_sha256"]
    raise KnowledgeHubError("DECLARATION_UNATTESTED")


def issue_grant(root, args):
    host, actor = policy(root), principal(root)
    raw = read_utf8_bounded(pathlib.Path(args.declaration_file), 131072, "actual user request")
    request_sha, attestation = attested_request(raw, args.declaration_file)
    action = args.grant_action
    if action not in host["actions"]:
        raise KnowledgeHubError("POLICY_DENIED")
    if action == "register":
        from .provider_onboarding import register_project
        planned = register_project(root, args.project, args.name, args.declaration_file)
        target, expected = planned["subject_ref"], planned["expected_hash"]
        extra = {"declaration_sha256": planned["declaration_sha256"]}
        widening = False
    elif action == "bind":
        from .provider_onboarding import bind_workspace
        planned = bind_workspace(root, args.workspace, args.path, args.coverage, args.expected_generation)
        target, expected = planned["subject_ref"], planned["expected_hash"]
        # A mention of another path is never a binding authorization.
        tokens = [args.path, str(pathlib.Path(args.path).expanduser())]
        exact_path = any(re.search(r"(?<![A-Za-z0-9/_~.-])" + re.escape(p) + r"(?![A-Za-z0-9/_~.-])", raw) for p in tokens)
        if target["id"].lower() not in raw.lower() or not exact_path:
            raise KnowledgeHubError("DECLARATION_MISMATCH")
        extra = {"binding_path_sha256": planned["binding_path_sha256"]}
        widening = False
    else:
        from .provider_subjects import route_subject, verify_item
        from .common import registry_items
        target = subject(args.subject)
        with read_guard(root):
            item = next((r for r in registry_items(root) if r["id"] == args.item_id), None)
            if not item or args.item_id not in raw or target["id"] not in raw:
                raise KnowledgeHubError("DECLARATION_MISMATCH")
            verify_item(root, item, args.expected_content_sha256)
            route = route_subject(root, target, item["kind"])
            widening = route["visibility"] != item["visibility"]
        expected = digest({"action": "assign", "item_id": args.item_id, "subject_ref": target,
                           "expected_content_sha256": args.expected_content_sha256})
        # Intake proves request provenance, not approval of an arbitrary transfer.
        # Assignment also requires an exact reviewed host authorization scope.
        from .authorization import require_authorization
        import json
        approval = require_authorization(root, args.authorization_id, ["automation-apply-with-review"], dt.date.today(), [])
        exact_scope = {"actor": actor, "action": "assign", "subject_ref": target, "item_id": args.item_id,
                       "expected_hash": expected, "visibility_change": widening}
        try:
            approved_scope = json.loads(approval["scope"])
        except ValueError:
            raise KnowledgeHubError("AUTHORIZATION_REQUIRED") from None
        if approved_scope != exact_scope:
            raise KnowledgeHubError("POLICY_DENIED")
        extra = {}
    ident = "grant-" + digest([actor, action, expected, request_sha, dt.date.today().isoformat()])
    with read_guard(root):
        inputs = snapshot_inputs(root)
        rows = load_jsonl(root / GRANTS_PATH)
        existing = next((r for r in rows if r["id"] == ident), None)
    if existing:
        if existing.get("status") != "active":
            raise KnowledgeHubError("AUTHORIZATION_REQUIRED")
        return {"status": "ALREADY_GRANTED", "persisted": True, "authorization_id": ident, "expected_hash": expected}
    row = {"id": ident, "actor": actor, "action": action, "subject_ref": target, "expected_hash": expected,
           "status": "active", "expires_at": dt.date.today().isoformat(),
           "visibility_change": widening, "request_sha256": request_sha, "intake_attestation_sha256": attestation, **extra}
    transaction = RepositoryTransaction(root, expected_inputs=inputs)
    transaction.add_text(GRANTS_PATH, encode_jsonl(rows + [row]))
    result = transaction.apply().to_dict() if args.apply else transaction.plan()
    return {"status": "GRANTED" if args.apply else "PLANNED", "persisted": args.apply,
            "authorization_id": ident, "expected_hash": expected, "transaction": result}
