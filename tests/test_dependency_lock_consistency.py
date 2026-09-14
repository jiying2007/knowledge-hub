from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.engineering import evaluate_engineering_contract
from tools.codex_assets.knowledge_hub.engineering_dependencies import (
    lock_health,
    lock_version_mismatches,
)


def test_repository_direct_dependency_versions_match_hash_locks():
    payload = evaluate_engineering_contract(repository_root())

    assert payload["locks"]["requirements-runtime.lock"]["direct_version_mismatches"] == []
    assert payload["locks"]["requirements-dev.lock"]["direct_version_mismatches"] == []


def test_lock_version_contract_accepts_marker_specific_versions():
    hashed = " --hash=sha256:" + "a" * 64 + "\n"
    health = lock_health(
        "demo==1.0 ; python_full_version < '3.9'" + hashed
        + "demo==2.0 ; python_full_version >= '3.9'" + hashed
    )

    assert health["versions"] == {"demo": ["1.0", "2.0"]}
    assert lock_version_mismatches({"demo": "2.0"}, health["versions"]) == []


def test_lock_version_contract_detects_stale_direct_version():
    hashed = " --hash=sha256:" + "a" * 64 + "\n"
    health = lock_health("ruff==0.15.20" + hashed)

    assert lock_version_mismatches({"ruff": "0.16.6"}, health["versions"]) == [
        {"package": "ruff", "expected": "0.16.6", "observed": ["0.15.20"]}
    ]
