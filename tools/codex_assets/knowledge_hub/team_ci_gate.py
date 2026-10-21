"""Check exact GitHub-hosted push Quality and Signed runs before LAN deployment.

This is not a substitute for repository-administrator inspection of branch rules.
A network/API failure keeps the existing serving revision untouched.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.request

from .common import KnowledgeHubError


def check_runs(payload: dict, sha: str) -> dict:
    runs = payload.get("workflow_runs", [])
    if not isinstance(runs, list):
        raise KnowledgeHubError("invalid GitHub workflow run data")
    matching = {}
    for run in runs:
        if not isinstance(run, dict) or run.get("head_sha") != sha:
            continue
        name = str(run.get("name", ""))
        expected_events = {"quality": "push", "signed-quality-attestation": "workflow_run"}
        if (name not in expected_events or run.get("event") != expected_events[name]
                or run.get("head_branch") != "master"
                or run.get("status") != "completed"):
            continue
        matching[name] = run.get("conclusion") == "success" or matching.get(name, False)
    if not all(matching.get(name, False) for name in ("quality", "signed-quality-attestation")):
        raise KnowledgeHubError("exact-head Quality/Signed success is missing")
    return {"status": "pass", "sha": sha, "quality": "success", "signed": "success"}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--sha", required=True)
    parser.add_argument("--repository", default="jiying2007/knowledge-hub")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[a-f0-9]{40}", args.sha):
        raise KnowledgeHubError("invalid serving SHA")
    if not re.fullmatch(r"[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+", args.repository):
        raise KnowledgeHubError("invalid repository identity")
    url = "https://api.github.com/repos/{}/actions/runs?head_sha={}&per_page=100".format(
        args.repository, args.sha
    )
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json", "User-Agent": "knowledge-hub-lan-deploy/1",
    })
    # Fixed api.github.com HTTPS host; repository/sha are bounded and validated.
    with urllib.request.urlopen(req, timeout=15) as response:  # nosec B310
        body = response.read(1048576)
    result = check_runs(json.loads(body.decode("utf-8")), args.sha)
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
