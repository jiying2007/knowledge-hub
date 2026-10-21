"""Public versioned Provider operations. Shell wrappers only forward arguments."""

from __future__ import annotations

import argparse
import json
import pathlib
import os
import re
import time
import sys
from typing import Any, Dict, List

from .common import KnowledgeHubError, repository_root, read_bytes_bounded
from .provider_subjects import digest, read_guard
from .provider_operations import response
from .provider_policy import SourceRejected
from .store import WriteConflict
from .context_support import TASK_TYPES


class ProviderArgumentError(KnowledgeHubError):
    def __init__(self, field, issue, allowed_values=()):
        super().__init__("SCHEMA_INVALID")
        self.diagnostic = {"field": field, "issue": issue, "allowed_values": list(allowed_values)}


class ProviderParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse messages can contain private argument values; never echo them.
        raise ProviderArgumentError("arguments", "invalid-arguments")

    def _check_value(self, action, value):
        if action.choices is not None and value not in action.choices:
            raise ProviderArgumentError(action.option_strings[0] if action.option_strings else action.dest,
                                        "invalid-choice", action.choices)

    def _get_value(self, action, arg_string):
        try:
            return super()._get_value(action, arg_string)
        except argparse.ArgumentError:
            raise ProviderArgumentError(action.option_strings[0] if action.option_strings else action.dest,
                                        "invalid-type") from None

    def parse_args(self, args=None, namespace=None):
        supplied = list(sys.argv[1:] if args is None else args)
        self.help_operation = supplied[0] if supplied and supplied[0] in OPERATION_FIELDS else None
        return super().parse_args(supplied, namespace)

    def print_help(self, file=None):
        operation = getattr(self, "help_operation", None)
        allowed = PUBLIC_COMMON_FIELDS | (OPERATION_FIELDS.get(operation, set()) if operation is not None else set())
        options = [{"flags": action.option_strings,
                    "allowed_values": list(action.choices) if action.choices is not None else []}
                   for action in self._actions if action.option_strings
                   and (operation is None or action.dest in allowed) and action.dest != "root"]
        details = {}
        if operation == "archive":
            from .provider_policy import SAFE_METADATA
            details["source_contract"] = {
                "format": "UTF-8 Markdown with optional descriptive YAML frontmatter",
                "allowed_metadata": sorted(SAFE_METADATA),
                "required": ["nonempty body", "--title or frontmatter title or H1", "--sanitized"],
                "ownership": "subject, kind, owner and status are assigned by Provider; do not copy project frontmatter",
                "repair": "create a separate sanitized conclusion; keep the original engineering record unchanged",
            }
        print(json.dumps({"schema_version": "knowledge-provider.help/v4", "status": "HELP",
                          "operation": operation, "read_only": True, "persisted": False,
                          "write_performed": False, "operations": list(OPERATION_FIELDS), "options": options,
                          "context_task_types": sorted(TASK_TYPES),
                          "result_boundaries": {"context": "read-only; inspect authority_lanes separately",
                                                "archive": "only persisted success acknowledges candidate archive"}, **details},
                         ensure_ascii=False), file=file)


def parser():
    p = ProviderParser(description="Knowledge Provider v4: explicit subjects and candidate-only operations.", allow_abbrev=False)
    p.add_argument("operation", choices=("status", "resolve", "grant", "register", "bind", "archive", "assign", "reconcile", "context", "capture-source"))
    p.add_argument("--root", default="")
    p.add_argument("--cwd", default=os.environ.get("KNOWLEDGE_PROVIDER_CALLER_CWD", str(pathlib.Path.cwd())))
    p.add_argument("--project", default="")
    p.add_argument("--name", default="")
    p.add_argument("--workspace", default="")
    p.add_argument("--path", default="")
    p.add_argument("--coverage", choices=("exact-root", "subtree"), default="subtree")
    p.add_argument("--expected-generation", type=int, default=0)
    p.add_argument("--authorization-id", default="")
    p.add_argument("--declaration-file", default="")
    p.add_argument("--grant-action", choices=("register", "bind", "archive", "assign"), default="register")
    p.add_argument("--subject", default="")
    p.add_argument("--from-subject", default="")
    p.add_argument("--source", default="")
    p.add_argument("--provenance-file", default="")
    p.add_argument("--kind", default="audit")
    p.add_argument("--title", default="")
    p.add_argument("--sanitized", action="store_true")
    p.add_argument("--declared-scope", choices=("team-general", "project-specific"), default="")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    p.add_argument("--item-id", default="")
    p.add_argument("--operation-id", default="")
    p.add_argument("--expected-content-sha256", default="")
    p.add_argument("--query", default="")
    p.add_argument("--execution-project", default="")
    p.add_argument("--retrieval-project", action="append", default=[])
    p.add_argument("--retrieval-domain", default="")
    p.add_argument("--archive-subject", default="")
    p.add_argument("--personal", action="store_true")
    p.add_argument("--unassigned", action="store_true")
    p.add_argument("--limit", type=int, default=3)
    p.add_argument("--context-budget", choices=("small", "normal", "deep"), default="small")
    p.add_argument("--task-type", choices=sorted(TASK_TYPES), default="general")
    p.add_argument("--receipt-key", default="")
    output = p.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--summary-json", action="store_true")
    p.add_argument("--file", action="append", default=[])
    return p


def capture_source(args):
    root = pathlib.Path(args.cwd).expanduser().resolve()
    if not args.file or len(args.file) > 64 or len(set(args.file)) != len(args.file):
        raise KnowledgeHubError("SOURCE_BUDGET_EXCEEDED")
    total, unstable, start = 0, False, time.monotonic()
    rows: List[Dict[str, Any]] = []
    denied = {".git", ".aws", ".ssh", ".codex", "build", "dist", "node_modules"}
    if any(part in denied for part in root.parts) or str(root).startswith(("/proc", "/sys", "/dev")):
        raise KnowledgeHubError("SOURCE_REJECTED")
    for relative in sorted(args.file):
        path = pathlib.PurePosixPath(relative)
        if (path.is_absolute() or ".." in path.parts or any(part in denied or part.startswith(".env") for part in path.parts)
                or path.suffix.lower() in {".pem", ".key", ".bin", ".elf", ".core", ".log", ".zip", ".gz", ".jsonl"}):
            raise KnowledgeHubError("SOURCE_REJECTED")
        candidate = root / relative
        try:
            candidate.resolve().relative_to(root)
        except ValueError:
            raise KnowledgeHubError("SOURCE_REJECTED") from None
        if any((root.joinpath(*path.parts[:i])).is_symlink() for i in range(1, len(path.parts) + 1)):
            raise KnowledgeHubError("SOURCE_REJECTED")
        before = candidate.stat()
        raw = read_bytes_bounded(candidate, 4 * 1024 * 1024, "source file")
        from .provider_operations import safe_text
        safe_text(raw.decode("utf-8"))
        after = candidate.stat()
        unstable |= (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns)
        total += len(raw)
        if total > 16 * 1024 * 1024 or time.monotonic() - start > 10:
            return {"status": "PARTIAL", "verification_state": "partial", "file_count": len(rows), "manifest_sha256": None, "read_only": True}
        import hashlib
        rows.append({"path": relative, "size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    return {"status": "UNSTABLE" if unstable else "OBSERVED", "read_only": True, "vcs": "none", "commit": None,
            "consistency": "observed", "verification_state": "unstable" if unstable else "observed",
            "file_count": len(rows), "coverage": "explicit-allowlist", "manifest_sha256": digest(rows), "files": rows}


PUBLIC_COMMON_FIELDS = {"cwd", "json", "summary_json", "operation", "dry_run", "help"}
OPERATION_FIELDS = {
        "status": set(), "resolve": set(),
        "register": {"project", "name", "declaration_file", "authorization_id", "apply"},
        "bind": {"workspace", "path", "coverage", "expected_generation", "authorization_id", "apply"},
        "grant": {"grant_action", "project", "name", "declaration_file", "workspace", "path", "coverage", "expected_generation", "subject", "from_subject", "item_id", "expected_content_sha256", "authorization_id", "declared_scope", "source", "provenance_file", "kind", "title", "sanitized", "apply"},
        "archive": {"subject", "source", "provenance_file", "kind", "title", "sanitized", "declared_scope", "authorization_id", "expected_content_sha256", "apply"},
        "assign": {"subject", "from_subject", "item_id", "expected_content_sha256", "authorization_id", "declared_scope", "apply"},
        "reconcile": {"operation_id", "expected_content_sha256"},
        "capture-source": {"file"},
        "context": {"query", "workspace", "execution_project", "retrieval_project", "retrieval_domain", "archive_subject", "personal", "unassigned", "limit", "context_budget", "task_type", "receipt_key"},
}


def validate_arguments(args):
    common = PUBLIC_COMMON_FIELDS | {"root"}
    defaults = vars(parser().parse_args([args.operation]))
    for key, value in vars(args).items():
        if key not in common | OPERATION_FIELDS[args.operation] and not key.startswith("_") and value != defaults.get(key):
            raise ProviderArgumentError("--" + key.replace("_", "-"), "unsupported-for-operation")
    if len(args.retrieval_project) > 8 or len(set(args.retrieval_project)) != len(args.retrieval_project):
        raise KnowledgeHubError("READ_BUDGET_EXCEEDED")


def run(root, args):
    if (root / "local/provider-maintenance.json").exists():
        raise KnowledgeHubError("PROVIDER_MAINTENANCE")
    validate_arguments(args)
    if args.operation == "archive" and args.project:
        raise KnowledgeHubError("SCHEMA_INVALID")
    if args.operation in {"status", "resolve", "context", "capture-source", "reconcile"} and args.apply:
        raise KnowledgeHubError("SCHEMA_INVALID")
    if args.operation == "status":
        from .provider_capabilities import capabilities
        return capabilities(root)
    if args.operation == "resolve":
        from .provider_onboarding import resolve_workspace
        with read_guard(root):
            value = resolve_workspace(root, args.cwd)
            value.pop("binding", None)
            return {"schema_version": "knowledge-provider.resolve/v1", "read_only": True, **value}
    if args.operation == "register":
        from .provider_onboarding import register_project
        return register_project(root, args.project, args.name, args.declaration_file, args.authorization_id, args.apply)
    if args.operation == "grant":
        from .provider_grants import issue_grant
        return issue_grant(root, args)
    if args.operation == "bind":
        from .provider_onboarding import bind_workspace
        return bind_workspace(root, args.workspace, args.path, args.coverage, args.expected_generation, args.authorization_id, args.apply)
    if args.operation == "archive":
        from .provider_operations import archive
        return archive(root, args)
    if args.operation == "assign":
        from .provider_operations import assign
        return assign(root, args)
    if args.operation == "reconcile":
        from .provider_operations import reconcile
        return reconcile(root, args.operation_id, args.expected_content_sha256)
    if args.operation == "context":
        if not args.query or not 1 <= args.limit <= 16:
            raise KnowledgeHubError("SCHEMA_INVALID")
        from .provider_context import context
        return context(root, args)
    return capture_source(args)


def main(argv=None):
    args = argparse.Namespace(apply=False)
    try:
        args = parser().parse_args(argv)
        root = repository_root(args.root)
        value = run(root, args)
        if value.get("schema_version") == "knowledge-provider.context/v4":
            from .schemas import validate_instance
            if validate_instance(root, "provider-context-v4", value)["status"] != "pass":
                raise KnowledgeHubError("SCHEMA_INVALID")
        if value.get("schema_version") == "knowledge-provider.operation-receipt/v4":
            from .schemas import validate_instance
            if validate_instance(root, "provider-operation-receipt-v4", value)["status"] != "pass":
                raise KnowledgeHubError("SCHEMA_INVALID")
        code = 0 if value.get("status") not in {"CONFLICT", "UNKNOWN", "BLOCKED"} else 2
    except (KnowledgeHubError, OSError, ValueError, TypeError, StopIteration, KeyError) as exc:
        reason = str(exc)
        if re.fullmatch(r"[A-Z][A-Z_]{1,80}", reason) is None:
            reason = "WRITE_CONFLICT" if isinstance(exc, WriteConflict) else "PERSISTENCE_UNCERTAIN" if args.apply and isinstance(exc, OSError) else "SCHEMA_INVALID"
        unknown = bool(getattr(args, "_commit_started", False)) and not isinstance(exc, WriteConflict)
        conflicted = reason == "CONTENT_DRIFT" and bool(getattr(args, "_operation_id", None))
        value = response("UNKNOWN" if unknown else "CONFLICT" if conflicted else "BLOCKED", getattr(args, "_operation_id", None), reason=reason)
        if isinstance(exc, (ProviderArgumentError, SourceRejected)):
            value["diagnostics"] = [exc.diagnostic]
        code = 2
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
