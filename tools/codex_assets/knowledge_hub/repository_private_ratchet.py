"""Build a review-only closure candidate for the repository privacy boundary.

The builder consumes GitHub repository metadata captured by a hosted workflow. It
never mutates the canonical registry and only produces a candidate when GitHub itself
reports the current repository as private.
"""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import pathlib
import re
from typing import Any, Dict, Mapping, Tuple

from .common import KnowledgeHubError, file_sha256, read_bytes_bounded

GAP_ID = "repository-private-boundary"
PROJECTION = "knowledge-hub-repository-private-ratchet-proposal-v2"
MAX_JSON_BYTES = 1024 * 1024
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _object(value: Any, label: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("{} must be an object".format(label))
    return dict(value)


def _load(path: pathlib.Path, label: str) -> Tuple[Dict[str, Any], str]:
    raw = read_bytes_bounded(path, MAX_JSON_BYTES, label)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("{} must be valid UTF-8 JSON".format(label)) from exc
    return _object(value, label), file_sha256(path)


def _git_sha(value: Any, label: str) -> str:
    result = str(value or "").strip().lower()
    if not GIT_SHA_RE.fullmatch(result):
        raise KnowledgeHubError("{} must be a lowercase 40-character git SHA".format(label))
    return result


def _timestamp(value: Any, label: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise KnowledgeHubError("{} must be a non-empty UTC timestamp".format(label))
    try:
        parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise KnowledgeHubError("{} must be a valid UTC timestamp".format(label)) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise KnowledgeHubError("{} must be UTC".format(label))
    return parsed.astimezone(dt.timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _repository_metadata(metadata: Mapping[str, Any], expected_repository: str) -> Dict[str, Any]:
    repo = _object(metadata, "repository metadata")
    full_name = str(repo.get("full_name") or "").strip()
    if full_name != expected_repository:
        raise KnowledgeHubError("repository metadata does not match the current repository")
    if repo.get("private") is not True:
        raise KnowledgeHubError("repository privacy boundary is not closed: private must be true")
    visibility = str(repo.get("visibility") or "").strip()
    if visibility and visibility != "private":
        raise KnowledgeHubError("repository visibility must be private")
    html_url = str(repo.get("html_url") or "").strip()
    if not html_url.startswith("https://github.com/"):
        raise KnowledgeHubError("repository metadata must retain the canonical GitHub URL")
    return {"full_name": full_name, "html_url": html_url, "visibility": visibility or "private"}


def _open_gap(registry: Mapping[str, Any]) -> Dict[str, Any]:
    target = _object(registry.get("repository_security_target"), "repository security target")
    if target.get("private_required") is not True:
        raise KnowledgeHubError("canonical registry does not require a private repository boundary")
    gaps = registry.get("external_closure_gaps")
    if not isinstance(gaps, list):
        raise KnowledgeHubError("canonical registry external_closure_gaps must be a list")
    matches = [item for item in gaps if isinstance(item, Mapping) and item.get("id") == GAP_ID]
    if len(matches) != 1:
        raise KnowledgeHubError("canonical registry must contain exactly one repository privacy gap")
    gap = dict(matches[0])
    if gap.get("required") is not True or gap.get("status") != "open":
        raise KnowledgeHubError("repository privacy gap must still be required/open")
    if gap.get("evidence_refs") or gap.get("evidence"):
        raise KnowledgeHubError("open repository privacy gap must not contain closure evidence")
    return gap


def build_repository_private_candidate(
    *,
    registry_path: pathlib.Path,
    repository_metadata_path: pathlib.Path,
    expected_repository: str,
    source_revision: str,
    run_id: int,
    run_attempt: int,
    observed_at: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    registry, registry_sha = _load(registry_path, "canonical registry")
    metadata, metadata_sha = _load(repository_metadata_path, "repository metadata")
    repo = _repository_metadata(metadata, expected_repository)
    current_gap = _open_gap(registry)
    revision = _git_sha(source_revision, "source revision")
    timestamp = _timestamp(observed_at, "observed_at")
    if int(run_id) < 1 or int(run_attempt) < 1:
        raise KnowledgeHubError("hosted run id and attempt must be positive")

    candidate = copy.deepcopy(registry)
    gap = next(item for item in candidate["external_closure_gaps"] if item.get("id") == GAP_ID)
    run_url = "https://github.com/{}/actions/runs/{}".format(expected_repository, int(run_id))
    gap["status"] = "closed"
    gap["reason"] = "GitHub hosted metadata reports the canonical repository as private."
    gap["evidence_refs"] = [repo["html_url"], run_url]
    gap["evidence"] = {
        "closure_scope": "repository-private-boundary-only",
        "terminal_claimed": False,
        "previous_open_reason": str(current_gap.get("reason") or ""),
        "repository": repo["full_name"],
        "visibility": repo["visibility"],
        "private": True,
        "source_revision": revision,
        "github_run_id": int(run_id),
        "github_run_attempt": int(run_attempt),
        "repository_metadata_sha256": metadata_sha,
        "canonical_write_performed_by_evidence_chain": False,
    }
    candidate_bytes = (json.dumps(candidate, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    proposal = {
        "schema_version": 1,
        "projection": PROJECTION,
        "status": "ready-for-machine-ratchet",
        "authorization_class": "autonomous-low-risk-ratchet",
        "review_required": False,
        "canonical_write_performed": False,
        "gap_id": GAP_ID,
        "repository": repo["full_name"],
        "visibility": repo["visibility"],
        "private": True,
        "source_revision": revision,
        "github_run_id": int(run_id),
        "github_run_attempt": int(run_attempt),
        "repository_metadata_sha256": metadata_sha,
        "expected_registry_sha256": registry_sha,
        "candidate_registry_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "generated_at": timestamp,
    }
    return candidate, proposal
