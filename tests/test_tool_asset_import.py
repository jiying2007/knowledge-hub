import hashlib
import json
from pathlib import Path

from tools.codex_assets.knowledge_hub.tool_asset_import_cli import main


def _candidate(path: Path, **overrides):
    values = {
        "source_repo": "xcrz-sigmastar-demo",
        "source_commit": "0123456789abcdef0123456789abcdef01234567",
        "candidate_name": "pcr02-memory-baseline",
        "candidate_source_path": "codex_assets/tools/pcr02_memory_baseline.py",
        "candidate_sha256": hashlib.sha256(b"tool-source").hexdigest(),
        "candidate_score": 88,
        "recommendation": "recommend-promote",
        "recommended_target": "项目 skill 或全局 Codex 候选",
        "summary_zh": "用于复用内存基线采集与比较流程。",
        "risks_zh": "不同固件版本的字段可能变化。",
        "blockers_zh": "需要 owner 确认维护归属。",
        "endpoint_removed": "true",
        "credentials_found": "false",
        "raw_logs_archived": "false",
    }
    values.update(overrides)
    path.write_text(
        """---
schema: knowledge-hub.tool-asset-candidate.v1
source_repo: {source_repo}
source_commit: {source_commit}
source_worktree_dirty: true
source_identity_verified: true
candidate_name: {candidate_name}
candidate_source_path: {candidate_source_path}
candidate_sha256: {candidate_sha256}
candidate_hash_scope: single-file
candidate_file_count: 1
candidate_score: {candidate_score}
recommendation: {recommendation}
recommended_target: {recommended_target}
validation:
  unit_tests: pass
  cli_help: pass
  dry_run: pass
  non_repo_cwd: pass
sanitization:
  endpoint_removed: {endpoint_removed}
  credentials_found: {credentials_found}
  raw_logs_archived: {raw_logs_archived}
status: reviewing
summary_zh: {summary_zh}
risks_zh: {risks_zh}
blockers_zh: {blockers_zh}
---

# ignored input body
""".format(**values),
        encoding="utf-8",
    )


def test_tool_asset_import_plans_metadata_only_candidate(tmp_path, capsys):
    source = tmp_path / "hub-candidate.md"
    _candidate(source)

    assert main(["--source", str(source), "--as-of", "2026-07-31", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["status"] == "planned"
    assert payload["candidate"]["project_id"] == "xcrz-sigmastar-demo"
    assert payload["raw_candidate_body_archived"] is False
    assert payload["source_code_copied"] is False
    assert payload["active_promotion"] is False
    paths = {row["path"] for row in payload["transaction"]["writes"]}
    assert "projects/xcrz-sigmastar-demo/validation/tool-asset-candidate-2026-07-31-pcr02-memory-baseline.md" in paths
    assert "registry/items.jsonl" in paths


def test_tool_asset_import_rejects_secret_and_raw_log_claim(tmp_path, capsys):
    secret = tmp_path / "secret.md"
    _candidate(secret)
    secret.write_text(secret.read_text() + "\npassword=real-secret-value\n", encoding="utf-8")
    assert main(["--source", str(secret), "--json"]) == 3
    assert "secret-like" in json.loads(capsys.readouterr().out)["error"]

    unsafe = tmp_path / "unsafe.md"
    _candidate(unsafe, raw_logs_archived="true")
    assert main(["--source", str(unsafe), "--json"]) == 3
    assert "raw_logs_archived must be false" in json.loads(capsys.readouterr().out)["error"]


def test_tool_asset_import_rejects_live_codex_and_private_endpoint(tmp_path, capsys):
    live = tmp_path / "live.md"
    _candidate(live, candidate_source_path=".codex/tools/example.py")
    assert main(["--source", str(live), "--json"]) == 3
    assert "codex_assets/, tools/ or scripts/" in json.loads(capsys.readouterr().out)["error"]

    endpoint = tmp_path / "endpoint.md"
    _candidate(endpoint, risks_zh="依赖 192.168.1.20 设备。")
    assert main(["--source", str(endpoint), "--json"]) == 3
    assert "private endpoint" in json.loads(capsys.readouterr().out)["error"]
