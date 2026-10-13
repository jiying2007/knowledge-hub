"""Hash-bound, explicitly authorized AI review of ordinary reviewing records.

Authorization is a local audit record, not a cryptographic human signature.
Human review and owner/promotion authority remain separate.
"""

import datetime as dt
import hashlib
import json
import pathlib
import re

from .common import KnowledgeHubError
from .review_risk import classify_review_risk, load_review_risk_policy
from .review_semantic import OWNER_BLOCKED

LEDGER = "registry/ai-content-review-authorizations.jsonl"
FIELD = "ai_delegated_content_review"
SHA = re.compile(r"[0-9a-f]{64}")
SCHEMA = "knowledge-ai-content-review-authorization/v1"


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def item_digest(item):
    return digest({key: value for key, value in item.items() if key != FIELD})


def content_digest(root, path):
    if not isinstance(path, str) or not path or pathlib.Path(path).is_absolute():
        raise KnowledgeHubError("invalid review content path")
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise KnowledgeHubError("review content outside repository") from exc
    if not resolved.is_file():
        raise KnowledgeHubError("review content missing or outside repository")
    return hashlib.sha256(resolved.read_bytes()).hexdigest()


def load_ledger(root):
    path = root / LEDGER
    if not path.exists():
        return {}
    if path.is_symlink():
        raise KnowledgeHubError("authorization ledger must not be a symlink")
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        validate_authorization(root, row)
        key = row["authorization_id"]
        if key in result:
            raise KnowledgeHubError("duplicate authorization identity")
        result[key] = row
    return result


def _string(value):
    return isinstance(value, str) and bool(value.strip())


def validate_authorization(root, auth):
    if not isinstance(auth, dict) or auth.get("schema_version") != SCHEMA:
        raise KnowledgeHubError("invalid AI content review authorization schema")
    required = {"schema_version", "authorization_id", "authorized_by", "authorized_at",
                "thread_id", "authorization_statement", "authorization_evidence_sha256",
                "executor", "scope", "independent_review_sha256", "entries", "request_proof"}
    if set(auth) != required:
        raise KnowledgeHubError("authorization fields incomplete or unsupported")
    for key in required - {"entries", "request_proof"}:
        if not _string(auth.get(key)):
            raise KnowledgeHubError("blank authorization field: " + key)
    proof = auth["request_proof"]
    if (not isinstance(proof, dict) or set(proof) != {"state", "request_sha256", "intake_attestation_sha256", "actor_identity_verified"}
            or proof.get("state") not in {"verified", "unverified"} or proof.get("actor_identity_verified") is not False):
        raise KnowledgeHubError("invalid request proof")
    attestation = proof["intake_attestation_sha256"]
    if (proof["state"] == "verified" and (not SHA.fullmatch(str(attestation)) or not SHA.fullmatch(str(proof["request_sha256"])))
            or proof["state"] == "unverified" and (attestation is not None or proof["request_sha256"] is not None)):
        raise KnowledgeHubError("invalid request attestation")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,159}", auth["authorization_id"]):
        raise KnowledgeHubError("invalid authorization identity")
    if auth["executor"] != "Codex" or auth["scope"] != "ordinary-reviewing-content-only":
        raise KnowledgeHubError("unsupported executor or authorization scope")
    if not re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", auth["thread_id"]):
        raise KnowledgeHubError("invalid authorization thread")
    date = dt.date.fromisoformat(auth["authorized_at"])
    if date > dt.datetime.now(dt.timezone.utc).date():
        raise KnowledgeHubError("authorization date is in future")
    for key in ("authorization_evidence_sha256", "independent_review_sha256"):
        if not SHA.fullmatch(auth[key]):
            raise KnowledgeHubError("invalid authorization evidence hash")
    owners = json.loads((root / "registry/owners.json").read_text())
    rows = owners if isinstance(owners, list) else owners.get("owners", [])
    if auth["authorized_by"] not in {row["id"] for row in rows}:
        raise KnowledgeHubError("authorization owner is not registered")
    entries = auth["entries"]
    if not isinstance(entries, list) or not entries:
        raise KnowledgeHubError("empty authorized review scope")
    seen = set()
    fields = {"id", "path", "owner", "item_sha256", "content_sha256", "decision", "basis"}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != fields:
            raise KnowledgeHubError("invalid review entry fields")
        if any(not _string(entry[key]) for key in fields):
            raise KnowledgeHubError("blank review entry field")
        if entry["id"] in seen or entry["owner"] != auth["authorized_by"]:
            raise KnowledgeHubError("duplicate target or unauthorized owner")
        seen.add(entry["id"])
        if entry["decision"] not in {"accept-as-review-record", "needs-edits", "defer"}:
            raise KnowledgeHubError("AI content review cannot change lifecycle")
        for key in ("item_sha256", "content_sha256"):
            if not SHA.fullmatch(entry[key]):
                raise KnowledgeHubError("invalid review entry hash")


def expected_record(auth, entry):
    return {"schema_version": 1, "authorization_id": auth["authorization_id"],
            "authorization_sha256": digest(auth), "executor": auth["executor"],
            "reviewed_at": auth["authorized_at"], "decision": entry["decision"],
            "basis": entry["basis"], "content_sha256": entry["content_sha256"],
            "item_sha256": entry["item_sha256"]}


def valid_record_shape(record):
    fields = {"schema_version", "authorization_id", "authorization_sha256", "executor",
              "reviewed_at", "decision", "basis", "content_sha256", "item_sha256"}
    if not isinstance(record, dict) or set(record) != fields or type(record.get("schema_version")) is not int or record["schema_version"] != 1:
        return False
    if any(not _string(record[key]) for key in fields - {"schema_version"}):
        return False
    if record["executor"] != "Codex" or record["decision"] not in {"accept-as-review-record", "needs-edits", "defer"}:
        return False
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,159}", record["authorization_id"]):
        return False
    if any(not SHA.fullmatch(record[key]) for key in ("authorization_sha256", "content_sha256", "item_sha256")):
        return False
    try:
        return dt.date.fromisoformat(record["reviewed_at"]).isoformat() == record["reviewed_at"]
    except ValueError:
        return False


def eligible(root, item, policy=None):
    path = str(item.get("path", ""))
    risk = classify_review_risk(policy or load_review_risk_policy(root), path)
    tags = item.get("tags", [])
    review = str(item.get("review_status", ""))
    return (item.get("generated_by_ai") is True and item.get("status") == "reviewing"
            and item.get("visibility") == "team-internal"
            and risk["review_class"] == "ordinary"
            and item.get("kind") in {"validation", "debug-record", "runbook"}
            and not item.get("owner_gate_verified")
            and not item.get("owner_decision") and not item.get("agent_contract")
            and not item.get("evidence_contract")
            and review not in OWNER_BLOCKED
            and not any(marker in review for marker in ("pending-owner", "needs-owner", "blocked-", "owner-intake", "owner-review", "owner-gate"))
            and item.get("promotion", "none") == "none"
            and item.get("promotion_decision", "none") in {"none", "", "none; capture does not authorize active promotion or owner decision"}
            and not any(tag in tags for tag in ("promoted", "team-standard", "owner-gated"))
            and not path.endswith("project-readiness.md")
            and not any(item.get(key) for key in ("human_reviewed_by", "human_reviewed_at",
                                                  "review_basis", "human_review_decision")))


def review_state(root, item, ledger=None, policy=None):
    """Return absent, valid closed/open, or invalid; all invalid states fail closed."""
    if FIELD not in item:
        return {"status": "absent", "closed": False}
    try:
        record = item[FIELD]
        if not valid_record_shape(record):
            raise KnowledgeHubError("invalid review record")
        ledger = load_ledger(root) if ledger is None else ledger
        auth = ledger.get(record.get("authorization_id", ""))
        if not auth:
            raise KnowledgeHubError("authorization absent or revoked")
        entry = next((row for row in auth["entries"] if row["id"] == item.get("id")), None)
        if not entry or record != expected_record(auth, entry):
            raise KnowledgeHubError("review credential mismatch or target outside scope")
        if auth["request_proof"]["state"] != "verified":
            return {"status": "needs-review", "closed": False, "reason": "historical-user-request-unverified"}
        if not eligible(root, item, policy) or item.get("owner") != auth["authorized_by"]:
            raise KnowledgeHubError("review target no longer eligible")
        if item.get("path") != entry["path"] or item_digest(item) != entry["item_sha256"]:
            raise KnowledgeHubError("review object identity drift")
        if content_digest(root, item["path"]) != entry["content_sha256"]:
            raise KnowledgeHubError("review content hash drift")
        return {"status": "valid", "closed": entry["decision"] == "accept-as-review-record",
                "decision": entry["decision"], "executor": "Codex"}
    except (KnowledgeHubError, ValueError, OSError, KeyError, TypeError) as exc:
        return {"status": "invalid", "closed": False, "reason": str(exc)}


def review_counts(root, items):
    closed = 0
    human = 0
    for item in items:
        if review_state(root, item)["closed"]:
            closed += 1
        try:
            human_hash_valid = (not item.get("human_review_content_sha256")
                                or item["human_review_content_sha256"] == content_digest(root, item.get("path")))
        except (KnowledgeHubError, OSError):
            human_hash_valid = False
        if (item.get("generated_by_ai") is True
                and all(_string(item.get(key)) for key in ("human_reviewed_by", "human_reviewed_at", "review_basis"))
                and item.get("human_review_decision") not in {"needs-edits", "defer"}
                and human_hash_valid):
            human += 1
    return {"ai_delegated_closed_count": closed, "human_reviewed_count": human}
