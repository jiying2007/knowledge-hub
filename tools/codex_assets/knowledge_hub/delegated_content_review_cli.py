"""Apply caller-supplied, explicit local AI review authorization transactionally."""

import argparse
import hashlib
import json
import os
import pathlib
import sys

from .common import KnowledgeHubError
from .delegated_content_review import (FIELD, LEDGER, digest, eligible, expected_record,
                                       item_digest, content_digest, load_ledger,
                                       validate_authorization, valid_record_shape)
from .store import RepositoryTransaction, snapshot_inputs


def read_evidence(path):
    if not path.is_file() or path.is_symlink():
        raise KnowledgeHubError("review evidence must be a regular non-symlink file")
    with path.open("rb") as handle:
        raw = handle.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise KnowledgeHubError("review evidence exceeds 2 MiB budget")
    return raw


def verify_user_request(args, auth):
    from .provider_grants import attested_request
    actual_request = read_evidence(args.request_file).decode("utf-8")
    request_sha, attestation = attested_request(actual_request, args.request_file)
    expected = {"state": "verified", "request_sha256": request_sha,
                "intake_attestation_sha256": attestation, "actor_identity_verified": False}
    if auth["request_proof"] != expected or auth["authorization_statement"] not in actual_request:
        raise KnowledgeHubError("authorization is not bound to the attested user request")


def main():
    parser = argparse.ArgumentParser(description="Authorized ordinary AI content review; never writes human or lifecycle fields.")
    parser.add_argument("--root", type=pathlib.Path, required=True)
    parser.add_argument("--authorization", type=pathlib.Path, required=True)
    parser.add_argument("--authorization-sha256", required=True)
    parser.add_argument("--authorization-evidence", type=pathlib.Path, required=True)
    parser.add_argument("--request-file", type=pathlib.Path, required=True)
    parser.add_argument("--independent-review", type=pathlib.Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        inputs = snapshot_inputs(root)
        raw = read_evidence(args.authorization)
        if hashlib.sha256(raw).hexdigest() != args.authorization_sha256:
            raise KnowledgeHubError("authorization file hash mismatch")
        auth = json.loads(raw)
        validate_authorization(root, auth)
        if auth["thread_id"] != os.environ.get("CODEX_THREAD_ID"):
            raise KnowledgeHubError("authorization thread differs from executing thread")
        authorization_raw = read_evidence(args.authorization_evidence)
        if hashlib.sha256(authorization_raw).hexdigest() != auth["authorization_evidence_sha256"]:
            raise KnowledgeHubError("authorization evidence hash mismatch")
        if auth["authorization_statement"] not in authorization_raw.decode("utf-8"):
            raise KnowledgeHubError("authorization statement absent from supplied evidence")
        verify_user_request(args, auth)
        if hashlib.sha256(read_evidence(args.independent_review)).hexdigest() != auth["independent_review_sha256"]:
            raise KnowledgeHubError("independent review hash mismatch")
        path = root / "registry/items.jsonl"
        items = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        by_id = {row["id"]: row for row in items}
        if len(by_id) != len(items):
            raise KnowledgeHubError("duplicate registry item identities")
        ledger = load_ledger(root)
        existing = ledger.get(auth["authorization_id"])
        if existing is not None and existing != auth:
            raise KnowledgeHubError("authorization identity already bound to another scope")
        changed = []
        for entry in auth["entries"]:
            item = by_id.get(entry["id"])
            if not item or not eligible(root, item):
                raise KnowledgeHubError("target is not ordinary unreviewed reviewing content: " + entry["id"])
            if (item.get("owner") != entry["owner"] or item.get("path") != entry["path"]
                    or item_digest(item) != entry["item_sha256"]
                    or content_digest(root, item["path"]) != entry["content_sha256"]):
                raise KnowledgeHubError("target identity/content drift: " + entry["id"])
            record = expected_record(auth, entry)
            if FIELD in item and not valid_record_shape(item[FIELD]):
                raise KnowledgeHubError("malformed existing AI review; repair required")
            if FIELD in item and item[FIELD] != record and item[FIELD].get("authorization_id") == auth["authorization_id"]:
                raise KnowledgeHubError("existing review differs; explicit new review resolution required")
            if item.get(FIELD) != record:
                item[FIELD] = record
                changed.append(item["id"])
        ledger[auth["authorization_id"]] = auth
        transaction = RepositoryTransaction(root, expected_inputs=inputs)
        transaction.add_text("registry/items.jsonl", "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in items) + "\n")
        transaction.add_text(LEDGER, "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in ledger.values()) + "\n")
        # Read-set guards cover target bodies as well as registry/control inputs.
        # Add unchanged bodies so the transactional lock verifies their exact hash.
        for entry in auth["entries"]:
            transaction.add_bytes(entry["path"], (root / entry["path"]).read_bytes(), expected_sha256=entry["content_sha256"])
        plan = transaction.plan()
        result = transaction.apply().to_dict() if args.apply else None
        payload = {"status": "applied" if args.apply else "planned", "applied": args.apply,
                   "authorization_id": auth["authorization_id"], "authorization_sha256": digest(auth),
                   "selected_count": len(auth["entries"]), "updated_count": len(changed),
                   "updated_ids": changed, "transaction_plan": plan, "transaction_result": result,
                   "human_fields_changed": False, "lifecycle_changed": False, "owner_gate_mutation": False,
                   "domain_evidence_bound": False, "authorization_is_cryptographic_signature": False}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except (KnowledgeHubError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "invalid", "applied": False, "reason": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
