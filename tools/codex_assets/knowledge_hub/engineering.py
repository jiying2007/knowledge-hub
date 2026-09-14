"""Engineering, runtime-support and supply-chain quality contracts."""

from __future__ import annotations

import os
import pathlib
import re
import sys
import uuid
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - exercised by the system Python compatibility lane
    import tomli as tomllib

from .common import (
    KnowledgeHubError,
    ensure_private_directory_tree,
    ensure_private_file,
    pretty_json,
    read_utf8_bounded,
    run_rtk,
    utc_timestamp,
    working_tree_signature,
)
from .artifact_governance import evaluate_artifact_governance
from .command_surface import evaluate_command_surface
from .complexity_budget import evaluate_complexity_budget
from .engineering_dependencies import (
    direct_pins as _direct_pins,
    lock_health as _lock_health,
    lock_version_mismatches as _lock_version_mismatches,
)


CONTRACT_MAX_BYTES = 4 * 1024 * 1024
ENGINEERING_SNAPSHOT_RELATIVE = ".cache/knowledge-hub/engineering-quality.json"
RUNTIME_COMPATIBILITY_VERSIONS = (
    "3.8",
    "3.9",
    "3.10",
    "3.11",
    "3.12",
    "3.13",
    "3.14",
)
ENGINEERING_PYTHON_VERSIONS = ("3.10", "3.11", "3.12", "3.13", "3.14")
EXPECTED_RUNTIME_DIRECT = {
    "jsonschema": "4.23.0",
    "pyyaml": "6.0.3",
    "tomli": "2.4.1",
}
EXPECTED_BUILD_BACKEND = {"setuptools": "83.0.0"}
REQUIRED_FILES = (
    "pyproject.toml",
    "requirements-runtime.txt",
    "requirements-dev.txt",
    "requirements-runtime.lock",
    "requirements-dev.lock",
    ".github/workflows/quality.yml",
    ".github/workflows/recovery-drill.yml",
    ".github/dependabot.yml",
    "tools/ci/rtk",
    "tools/ci/bootstrap-path.sh",
    "tools/ci/python-runtime.sh",
)
ACTION_PATTERN = re.compile(r"\buses:\s*([^\s#]+)")
FULL_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def _read(root: pathlib.Path, relative: str) -> str:
    return read_utf8_bounded(
        root / relative,
        CONTRACT_MAX_BYTES,
        "engineering contract file",
    )



def _python_contract(pyproject: Mapping[str, Any], workflow_text: str) -> Dict[str, Any]:
    project = pyproject.get("project", {}) if isinstance(pyproject, Mapping) else {}
    requires_python = str(project.get("requires-python", "")) if isinstance(project, Mapping) else ""
    minimum_match = re.search(r">=\s*(\d+\.\d+)", requires_python)
    minimum = minimum_match.group(1) if minimum_match else ""
    ci_versions = [
        version
        for version in RUNTIME_COMPATIBILITY_VERSIONS
        if '"{}"'.format(version) in workflow_text
        or "'{}'".format(version) in workflow_text
    ]
    current = "{}.{}".format(sys.version_info.major, sys.version_info.minor)
    return {
        "minimum": minimum,
        "requires_python": requires_python,
        "selection_policy": "capability-based",
        "ci_versions": ci_versions,
        "current": current,
        "current_supported": current in ENGINEERING_PYTHON_VERSIONS,
    }


def _ci_contract(workflow_text: str) -> Dict[str, Any]:
    actions = []
    mutable_actions = []
    for value in ACTION_PATTERN.findall(workflow_text):
        if value.startswith("./"):
            continue
        if "@" not in value:
            mutable_actions.append(value)
            continue
        action, reference = value.rsplit("@", 1)
        actions.append({"action": action, "reference": reference})
        if FULL_SHA_PATTERN.fullmatch(reference) is None:
            mutable_actions.append(value)
    permissions_read = bool(
        re.search(
            r"(?ms)^permissions:\s*$.*?^\s+contents:\s+read\s*$",
            workflow_text,
        )
    )
    no_write_permissions = re.search(r"(?m)^\s+[A-Za-z-]+:\s+write\s*$", workflow_text) is None
    quality_entry = "engineering_cli --mode full" in workflow_text
    direct_quality = all(
        token in workflow_text
        for token in (
            "pytest",
            "knowledge-check.sh",
            "knowledge-retrieval-benchmark.sh",
            "knowledge-regression.sh",
            "pip_audit",
        )
    )
    run_steps = re.findall(r"(?m)^\s*run:\s*(.+?)\s*$", workflow_text)
    governed_run_steps = all(
        value.startswith("rtk ") or value.startswith("tools/ci/rtk ")
        for value in run_steps
    )
    return {
        "actions": actions,
        "mutable_actions": mutable_actions,
        "all_actions_sha_pinned": bool(actions) and not mutable_actions,
        "least_privilege_permissions": permissions_read and no_write_permissions,
        "dangerous_pull_request_target": bool(
            re.search(r"(?m)^\s*pull_request_target\s*:", workflow_text)
        ),
        "checkout_credentials_persisted": "persist-credentials: false" not in workflow_text,
        "hash_locked_install": "--require-hashes" in workflow_text,
        "quality_gate_present": quality_entry or direct_quality,
        "job_timeout_present": "timeout-minutes:" in workflow_text,
        "governed_transport_bootstrap": (
            "tools/ci/rtk bash tools/ci/bootstrap-path.sh" in workflow_text
        ),
        "all_run_steps_governed": bool(run_steps) and governed_run_steps,
    }


def _recovery_workflow_contract(workflow_text: str) -> Dict[str, Any]:
    actions = ACTION_PATTERN.findall(workflow_text)
    pinned = bool(actions) and all(
        "@" in value
        and FULL_SHA_PATTERN.fullmatch(value.rsplit("@", 1)[1]) is not None
        for value in actions
        if not value.startswith("./")
    )
    run_steps = re.findall(r"(?m)^\s*run:\s*(.+?)\s*$", workflow_text)
    return {
        "quarterly_schedule": bool(
            re.search(r'(?m)^\s*-\s*cron:\s*["\']23 3 1 \*/3 \*["\']\s*$', workflow_text)
        ),
        "manual_dispatch": bool(
            re.search(r"(?m)^\s*workflow_dispatch\s*:\s*$", workflow_text)
        ),
        "github_hosted": "runs-on: ubuntu-latest" in workflow_text,
        "least_privilege": (
            "contents: read" in workflow_text
            and re.search(r"(?m)^\s+[A-Za-z-]+:\s+write\s*$", workflow_text)
            is None
        ),
        "all_actions_sha_pinned": pinned,
        "checkout_credentials_disabled": "persist-credentials: false" in workflow_text,
        "hash_locked_install": "--require-hashes" in workflow_text,
        "head_restore": "knowledge-restore-drill.sh --source-mode head" in workflow_text,
        "same_run_product_gate": (
            "knowledge-final-gate.sh --final-profile product" in workflow_text
        ),
        "evidence_retention_days": 90 if "retention-days: 90" in workflow_text else 0,
        "all_run_steps_governed": bool(run_steps)
        and all(
            value.startswith("rtk ") or value.startswith("tools/ci/rtk ")
            for value in run_steps
        ),
    }


def _ci_transport_contract(rtk_text: str, bootstrap_text: str) -> Dict[str, Any]:
    required_wrappers = (
        "tools/ci/bootstrap-path.sh",
        "tools/knowledge-check.sh",
        "tools/knowledge-regression.sh",
        "tools/knowledge-retrieval-benchmark.sh",
    )
    unsafe_shell_dispatch = bool(
        re.search(r"(?m)^\s*(?:eval|source)\b", rtk_text)
        or "bash -c" in rtk_text
        or "tools/*.sh" in rtk_text
    )
    return {
        "required_wrappers": list(required_wrappers),
        "exact_wrapper_allowlist": all(value in rtk_text for value in required_wrappers)
        and not unsafe_shell_dispatch,
        "runner_path_boundary": all(
            value in bootstrap_text
            for value in (
                '"$RUNNER_TEMP"/_runner_file_commands/*',
                '! -f "$GITHUB_PATH"',
                '-L "$GITHUB_PATH"',
                '"$GITHUB_WORKSPACE/tools/ci"',
            )
        ),
    }


def _dependabot_contract(text: str) -> Dict[str, Any]:
    ecosystems = sorted(
        set(
            re.findall(
                r"(?m)^\s*-?\s*package-ecosystem:\s*[\"']?([^\s\"']+)",
                text,
            )
        )
    )
    return {
        "ecosystems": ecosystems,
        "monthly_schedule_count": len(
            re.findall(r"(?m)^\s*interval:\s*[\"']?monthly[\"']?\s*$", text)
        ),
    }


def evaluate_engineering_contract(root: pathlib.Path) -> Dict[str, Any]:
    root = pathlib.Path(root).resolve()
    errors: List[str] = []
    missing = [relative for relative in REQUIRED_FILES if not (root / relative).is_file()]
    for relative in missing:
        errors.append("missing required engineering file: {}".format(relative))

    def read_or_empty(relative: str) -> str:
        if relative in missing:
            return ""
        try:
            return _read(root, relative)
        except KnowledgeHubError as exc:
            errors.append("{}: {}".format(relative, exc))
            return ""

    pyproject_text = read_or_empty("pyproject.toml")
    try:
        pyproject = tomllib.loads(pyproject_text) if pyproject_text else {}
    except (ValueError, tomllib.TOMLDecodeError) as exc:
        errors.append("pyproject.toml is invalid TOML: {}".format(exc))
        pyproject = {}
    workflow_text = read_or_empty(".github/workflows/quality.yml")
    recovery_workflow_text = read_or_empty(".github/workflows/recovery-drill.yml")
    python_support = _python_contract(pyproject, workflow_text)
    if python_support["requires_python"]:
        errors.append("pyproject.toml must leave runtime selection capability-based")
    if python_support["ci_versions"] != list(RUNTIME_COMPATIBILITY_VERSIONS):
        errors.append("CI must cover capability-based runtime compatibility from Python 3.8 through 3.14")

    runtime_text = read_or_empty("requirements-runtime.txt")
    runtime_direct, runtime_errors = _direct_pins(runtime_text)
    errors.extend("requirements-runtime.txt: {}".format(value) for value in runtime_errors)
    if runtime_direct != EXPECTED_RUNTIME_DIRECT:
        errors.append("runtime direct dependency pins do not match the governed baseline")
    project = pyproject.get("project", {}) if isinstance(pyproject, Mapping) else {}
    project_dependencies = project.get("dependencies", []) if isinstance(project, Mapping) else []
    pyproject_direct, pyproject_errors = _direct_pins(
        "\n".join(str(value) for value in project_dependencies)
    )
    errors.extend("pyproject.toml: {}".format(value) for value in pyproject_errors)
    if pyproject_direct != runtime_direct:
        errors.append("pyproject and requirements-runtime direct dependencies differ")
    dev_direct, dev_errors = _direct_pins(
        read_or_empty("requirements-dev.txt"),
        allow_include=True,
    )
    errors.extend("requirements-dev.txt: {}".format(value) for value in dev_errors)
    build_system = pyproject.get("build-system", {}) if isinstance(pyproject, Mapping) else {}
    build_requirements = build_system.get("requires", []) if isinstance(build_system, Mapping) else []
    build_direct, build_errors = _direct_pins(
        "\n".join(str(value) for value in build_requirements)
    )
    errors.extend("pyproject.toml build-system: {}".format(value) for value in build_errors)
    if build_direct != EXPECTED_BUILD_BACKEND:
        errors.append("build backend dependency pin does not match the governed baseline")
    if not set(build_direct).issubset(dev_direct):
        errors.append("development dependencies must include the pinned build backend")

    locks: Dict[str, Dict[str, Any]] = {}
    for relative in ("requirements-runtime.lock", "requirements-dev.lock"):
        health = _lock_health(read_or_empty(relative))
        locks[relative] = health
        if not health["hash_complete"]:
            errors.append("{} must contain only exact pins with SHA-256 hashes".format(relative))
        if health["unsupported_global_options"]:
            errors.append("{} contains unsupported global index options".format(relative))
    runtime_lock_packages = set(locks["requirements-runtime.lock"]["packages"])
    if not set(runtime_direct).issubset(runtime_lock_packages):
        errors.append("runtime lock does not cover every direct runtime dependency")
    dev_lock_packages = set(locks["requirements-dev.lock"]["packages"])
    if not (set(runtime_direct) | set(dev_direct)).issubset(dev_lock_packages):
        errors.append("dev lock does not cover every direct runtime and development dependency")

    runtime_version_mismatches = _lock_version_mismatches(
        runtime_direct,
        locks["requirements-runtime.lock"]["versions"],
    )
    locks["requirements-runtime.lock"]["direct_version_mismatches"] = runtime_version_mismatches
    for mismatch in runtime_version_mismatches:
        errors.append(
            "runtime lock direct dependency version mismatch for {}: expected {}, observed {}".format(
                mismatch["package"],
                mismatch["expected"],
                ",".join(mismatch["observed"]) if mismatch["observed"] else "<missing>",
            )
        )
    dev_expected = dict(runtime_direct)
    dev_expected.update(dev_direct)
    dev_version_mismatches = _lock_version_mismatches(
        dev_expected,
        locks["requirements-dev.lock"]["versions"],
    )
    locks["requirements-dev.lock"]["direct_version_mismatches"] = dev_version_mismatches
    for mismatch in dev_version_mismatches:
        errors.append(
            "dev lock direct dependency version mismatch for {}: expected {}, observed {}".format(
                mismatch["package"],
                mismatch["expected"],
                ",".join(mismatch["observed"]) if mismatch["observed"] else "<missing>",
            )
        )

    ci = _ci_contract(workflow_text)
    if not ci["all_actions_sha_pinned"]:
        errors.append("every third-party GitHub Action must use a full commit SHA")
    if not ci["least_privilege_permissions"]:
        errors.append("CI permissions must be contents: read with no write permission")
    if ci["dangerous_pull_request_target"]:
        errors.append("pull_request_target is forbidden for executable repository CI")
    if ci["checkout_credentials_persisted"]:
        errors.append("checkout must set persist-credentials: false")
    if not ci["hash_locked_install"]:
        errors.append("CI dependency installation must use --require-hashes")
    if not ci["quality_gate_present"] or not ci["job_timeout_present"]:
        errors.append("CI must run the governed quality gate with explicit timeouts")
    if not ci["governed_transport_bootstrap"] or not ci["all_run_steps_governed"]:
        errors.append("every CI run step must use the governed RTK transport")
    recovery_workflow = _recovery_workflow_contract(recovery_workflow_text)
    if not all(recovery_workflow.values()):
        errors.append("quarterly recovery workflow contract failed")

    transport = _ci_transport_contract(
        read_or_empty("tools/ci/rtk"),
        read_or_empty("tools/ci/bootstrap-path.sh"),
    )
    if not transport["exact_wrapper_allowlist"]:
        errors.append("CI RTK transport must use the exact wrapper allowlist")
    if not transport["runner_path_boundary"]:
        errors.append("CI PATH bootstrap must validate the GitHub runner boundary")

    dependabot = _dependabot_contract(read_or_empty(".github/dependabot.yml"))
    if dependabot["ecosystems"] != ["github-actions", "pip"]:
        errors.append("Dependabot must cover pip and github-actions")
    if dependabot["monthly_schedule_count"] < 2:
        errors.append("Dependabot updates must use an explicit monthly schedule")

    command_surface = evaluate_command_surface(root)
    complexity_budget = evaluate_complexity_budget(root)
    artifact_governance = evaluate_artifact_governance(root)
    if command_surface["status"] != "pass":
        errors.append("command surface contract failed")
    if complexity_budget["status"] != "pass":
        errors.append("complexity budget regression detected")
    if artifact_governance["status"] != "pass":
        errors.append("artifact governance contract failed")

    return {
        "schema_version": 1,
        "generated_at": utc_timestamp(),
        "status": "pass" if not errors else "fail",
        "read_only": True,
        "python_support": python_support,
        "dependencies": {
            "runtime_direct": runtime_direct,
            "development_direct": dev_direct,
            "build_backend": build_direct,
            "pyproject_matches_runtime": pyproject_direct == runtime_direct,
        },
        "locks": locks,
        "ci": ci,
        "recovery_workflow": recovery_workflow,
        "ci_transport": transport,
        "dependabot": dependabot,
        "command_surface": command_surface,
        "complexity_budget": complexity_budget,
        "artifact_governance": artifact_governance,
        "missing_files": missing,
        "errors": errors,
    }


def _tail(value: str, limit: int = 20) -> List[str]:
    return value.splitlines()[-limit:]


def _run_quality_command(
    root: pathlib.Path,
    command: Sequence[str],
    timeout: int,
    *,
    max_attempts: int = 1,
    retry_exit_codes: Sequence[int] = (),
) -> Dict[str, Any]:
    """Run one quality command and retain bounded evidence for every attempt."""

    attempts: List[Dict[str, Any]] = []
    accepted_exit_codes = tuple(sorted({0, *retry_exit_codes}))
    for attempt_number in range(1, max_attempts + 1):
        try:
            result = run_rtk(
                root,
                command,
                timeout=timeout,
                accepted_exit_codes=accepted_exit_codes,
            )
        except (KnowledgeHubError, OSError) as exc:
            attempts.append(
                {
                    "attempt": attempt_number,
                    "status": "fail",
                    "error": str(exc),
                }
            )
            if attempt_number < max_attempts:
                continue
            return {
                "status": "fail",
                "attempt_count": len(attempts),
                "recovered_after_retry": False,
                "attempts": attempts,
                "error": str(exc),
            }

        attempt_status = "pass" if result["exit_code"] == 0 else "fail"
        attempt = {
            "attempt": attempt_number,
            "status": attempt_status,
            "exit_code": result["exit_code"],
            "command": result["command"],
            "duration_sec": result["duration_sec"],
            "stdout_tail": _tail(result["stdout"]),
            "stderr_tail": _tail(result["stderr"]),
        }
        attempts.append(attempt)
        if attempt_status == "pass":
            return {
                "status": "pass",
                "command": result["command"],
                "duration_sec": result["duration_sec"],
                "stdout_tail": attempt["stdout_tail"],
                "stderr_tail": attempt["stderr_tail"],
                "attempt_count": len(attempts),
                "recovered_after_retry": len(attempts) > 1,
                "attempts": attempts,
            }

    return {
        "status": "fail",
        "attempt_count": len(attempts),
        "recovered_after_retry": False,
        "attempts": attempts,
        "error": "command failed after {} attempt(s)".format(len(attempts)),
    }


def _coverage_recollection_commands(
    python: str,
) -> Sequence[Tuple[str, Sequence[str], int]]:
    return (
        ("coverage_erase", (python, "-m", "coverage", "erase"), 60),
        (
            "coverage",
            (python, "-m", "coverage", "run", "--parallel-mode", "-m", "pytest", "-q"),
            300,
        ),
        (
            "full_regression",
            (
                python,
                "-m",
                "coverage",
                "run",
                "--parallel-mode",
                "-m",
                "tools.codex_assets.knowledge_hub.regression_cli",
                ".",
                "--suite",
                "full",
                "--summary-json",
            ),
            600,
        ),
        ("coverage_combine", (python, "-m", "coverage", "combine"), 120),
        ("coverage_report", (python, "-m", "coverage", "report"), 120),
    )


def _recover_coverage_report(
    root: pathlib.Path,
    python: str,
    initial: Mapping[str, Any],
) -> Dict[str, Any]:
    """Recollect coverage once after a report failure, preserving first-failure evidence."""

    diagnostic = _run_quality_command(
        root,
        (python, "-m", "coverage", "report", "--fail-under=0"),
        120,
    )
    recollection: Dict[str, Dict[str, Any]] = {}
    for name, command, timeout in _coverage_recollection_commands(python):
        if name == "full_regression":
            result = _run_quality_command(
                root,
                command,
                timeout,
                max_attempts=2,
                retry_exit_codes=(1,),
            )
        else:
            result = _run_quality_command(root, command, timeout)
        recollection[name] = result
        if result["status"] != "pass":
            break
    report = recollection.get("coverage_report", {})
    recovered = report.get("status") == "pass"
    payload: Dict[str, Any] = {
        "status": "pass" if recovered else "fail",
        "initial": dict(initial),
        "diagnostic": diagnostic,
        "recollection": recollection,
        "recovered_after_recollection": recovered,
    }
    if recovered:
        for field in ("command", "duration_sec", "stdout_tail", "stderr_tail"):
            if field in report:
                payload[field] = report[field]
    else:
        payload["error"] = "coverage report failed after one full recollection"
    return payload


def _current_python_executable() -> str:
    """Return the active interpreter path without resolving a venv symlink."""

    executable = pathlib.Path(sys.executable)
    if not executable.is_absolute():
        executable = pathlib.Path.cwd() / executable
    return os.path.abspath(os.fspath(executable))


def engineering_snapshot_path(root: pathlib.Path) -> pathlib.Path:
    return root / ENGINEERING_SNAPSHOT_RELATIVE


def _write_engineering_snapshot(root: pathlib.Path, payload: Mapping[str, Any]) -> str:
    path = engineering_snapshot_path(root)
    ensure_private_directory_tree(root, path.parent)
    temporary = path.with_name("{}.tmp-{}".format(path.name, uuid.uuid4().hex))
    temporary.write_text(pretty_json(dict(payload)) + "\n", encoding="utf-8")
    ensure_private_file(temporary)
    os.replace(str(temporary), str(path))
    ensure_private_file(path)
    return str(path.relative_to(root))


def run_engineering_quality(
    root: pathlib.Path,
    sbom_output: Optional[pathlib.Path] = None,
) -> Dict[str, Any]:
    root = pathlib.Path(root).resolve()
    candidate_signature = working_tree_signature(root)
    contract = evaluate_engineering_contract(root)
    output_root = root / ".tmp" / "engineering"
    ensure_private_directory_tree(root, output_root)
    sbom_path = (sbom_output or output_root / "knowledge-hub.cdx.json").resolve()
    try:
        sbom_path.relative_to(root)
    except ValueError as exc:
        raise KnowledgeHubError("SBOM output must stay inside the repository") from exc
    checks: Dict[str, Dict[str, Any]] = {}
    if contract["status"] != "pass" or not contract["python_support"]["current_supported"]:
        blocking_errors = list(contract["errors"])
        if not contract["python_support"]["current_supported"]:
            blocking_errors.append("full engineering quality requires a supported Python >=3.10")
        return {
            "schema_version": 1,
            "generated_at": utc_timestamp(),
            "status": "fail",
            "mode": "full",
            "contract": contract,
            "checks": checks,
            "sbom": {"path": str(sbom_path.relative_to(root)), "generated": False},
            "errors": blocking_errors,
        }

    python = _current_python_executable()
    dist_dir = ".tmp/engineering/dist"
    commands: Sequence[Tuple[str, Sequence[str], int]] = (
        (
            "ruff_correctness",
            (python, "-m", "ruff", "check", "tools/codex_assets/knowledge_hub", "tests"),
            120,
        ),
        ("mypy", (python, "-m", "mypy"), 180),
        (
            "bandit",
            (python, "-m", "bandit", "-q", "-r", "tools/codex_assets/knowledge_hub", "-ll", "-ii"),
            180,
        ),
        (
            "coverage_erase",
            (python, "-m", "coverage", "erase"),
            60,
        ),
        (
            "coverage",
            (python, "-m", "coverage", "run", "--parallel-mode", "-m", "pytest", "-q"),
            300,
        ),
        ("build", (python, "-m", "build", "--no-isolation", "--outdir", dist_dir), 180),
        ("knowledge_check", ("bash", "tools/knowledge-check.sh", "--dry-run", "--json"), 120),
        (
            "retrieval_benchmark",
            ("bash", "tools/knowledge-retrieval-benchmark.sh", "--summary-json"),
            120,
        ),
        (
            "full_regression",
            (
                python,
                "-m",
                "coverage",
                "run",
                "--parallel-mode",
                "-m",
                "tools.codex_assets.knowledge_hub.regression_cli",
                ".",
                "--suite",
                "full",
                "--summary-json",
            ),
            600,
        ),
        ("coverage_combine", (python, "-m", "coverage", "combine"), 120),
        ("coverage_report", (python, "-m", "coverage", "report"), 120),
        (
            "dependency_audit",
            (
                python,
                "-m",
                "pip_audit",
                "--require-hashes",
                "--disable-pip",
                "-r",
                "requirements-runtime.lock",
            ),
            180,
        ),
        (
            "sbom",
            (
                python,
                "-m",
                "pip_audit",
                "--require-hashes",
                "--disable-pip",
                "-r",
                "requirements-runtime.lock",
                "--format",
                "cyclonedx-json",
                "--output",
                str(sbom_path),
            ),
            180,
        ),
    )
    quality_errors: List[str] = []
    for name, command, timeout in commands:
        if name == "full_regression":
            checks[name] = _run_quality_command(
                root,
                command,
                timeout,
                max_attempts=2,
                retry_exit_codes=(1,),
            )
        else:
            checks[name] = _run_quality_command(root, command, timeout)
        if checks[name]["status"] != "pass" and name != "coverage_report":
            quality_errors.append("{} failed".format(name))
    if checks.get("coverage_report", {}).get("status") != "pass":
        checks["coverage_report"] = _recover_coverage_report(
            root,
            python,
            checks["coverage_report"],
        )
        if checks["coverage_report"]["status"] != "pass":
            quality_errors.append("coverage_report failed")

    if sbom_path.exists():
        ensure_private_file(sbom_path)
    candidate_signature_after = working_tree_signature(root)
    candidate_unchanged = candidate_signature_after == candidate_signature
    if not candidate_unchanged:
        quality_errors.append("candidate changed during engineering quality gate")
    payload = {
        "schema_version": 1,
        "generated_at": utc_timestamp(),
        "status": "pass" if not quality_errors else "fail",
        "mode": "full",
        "contract": contract,
        "checks": checks,
        "sbom": {
            "path": str(sbom_path.relative_to(root)),
            "generated": sbom_path.is_file(),
        },
        "candidate_integrity": {
            "status": "pass" if candidate_unchanged else "fail",
            "unchanged": candidate_unchanged,
            "before_signature": candidate_signature,
            "after_signature": candidate_signature_after,
        },
        "errors": quality_errors,
    }
    payload["snapshot"] = {
        "path": ENGINEERING_SNAPSHOT_RELATIVE,
        "written": True,
    }
    _write_engineering_snapshot(root, payload)
    return payload
