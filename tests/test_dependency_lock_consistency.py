import pathlib
import re

from tools.codex_assets.knowledge_hub.common import repository_root


_PIN = re.compile(r"^([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?==([^\s;\\]+)")


def _normalized_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _manifest_pins(path: pathlib.Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("-r "):
            continue
        match = _PIN.match(line)
        assert match is not None, "{} contains a non-exact dependency pin: {}".format(path, line)
        pins[_normalized_name(match.group(1))] = match.group(2)
    return pins


def _lock_versions(path: pathlib.Path) -> dict[str, set[str]]:
    versions: dict[str, set[str]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("--"):
            continue
        match = _PIN.match(line)
        if match is None:
            continue
        versions.setdefault(_normalized_name(match.group(1)), set()).add(match.group(2))
    return versions


def _mismatches(pins: dict[str, str], lock_versions: dict[str, set[str]]) -> list[str]:
    result = []
    for name, expected in sorted(pins.items()):
        observed = sorted(lock_versions.get(name, set()))
        if expected not in observed:
            result.append(
                "{}: manifest={} lock={}".format(
                    name,
                    expected,
                    ",".join(observed) if observed else "<missing>",
                )
            )
    return result


def test_repository_direct_dependency_versions_match_hash_locks():
    root = repository_root()
    runtime = _manifest_pins(root / "requirements-runtime.txt")
    development = _manifest_pins(root / "requirements-dev.txt")
    runtime_lock = _lock_versions(root / "requirements-runtime.lock")
    development_lock = _lock_versions(root / "requirements-dev.lock")

    runtime_mismatches = _mismatches(runtime, runtime_lock)
    development_mismatches = _mismatches({**runtime, **development}, development_lock)

    assert runtime_mismatches == [], "runtime manifest/lock version drift: {}".format(
        "; ".join(runtime_mismatches)
    )
    assert development_mismatches == [], "development manifest/lock version drift: {}".format(
        "; ".join(development_mismatches)
    )


def test_dependency_lock_contract_detects_stale_direct_version(tmp_path):
    manifest = tmp_path / "requirements-dev.txt"
    lock = tmp_path / "requirements-dev.lock"
    manifest.write_text("ruff==0.16.6\n", encoding="utf-8")
    lock.write_text(
        "ruff==0.15.20 \\\n    --hash=sha256:" + "a" * 64 + "\n",
        encoding="utf-8",
    )

    mismatches = _mismatches(_manifest_pins(manifest), _lock_versions(lock))

    assert mismatches == ["ruff: manifest=0.16.6 lock=0.15.20"]
