#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import shutil
import sys

root = pathlib.Path(sys.argv[1]).resolve()
parser = argparse.ArgumentParser(description="Apply or verify the Knowledge Hub hard source migration plan.")
parser.add_argument("--as-of", default=dt.date.today().isoformat())
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--apply", action="store_true")
parser.add_argument("--json", action="store_true")
args = parser.parse_args(sys.argv[2:])

if args.dry_run and args.apply:
    print("ERROR --dry-run and --apply are mutually exclusive", file=sys.stderr)
    sys.exit(2)
if not args.apply:
    args.dry_run = True

TEXT_SUFFIXES = {".md", ".txt", ".rst", ".adoc"}
ARTIFACT_SUFFIXES = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".csv",
    ".tsv",
}
SKIP_DIRS = {
    ".git",
    ".cache",
    "__pycache__",
    "build",
    "cmake-build-debug",
    "cmake-build-release",
    "dist",
    "node_modules",
    "out",
    "target",
}

SOURCE_POLICIES = {
    "embedded-knowledge": {
        "kind": "copy-docs",
        "text_target": "domains/embedded/archive/source-docs/embedded-knowledge",
        "artifact_target": "artifacts/vault/embedded-knowledge",
        "decommission": "delete-external-after-verify",
    },
    "engineering-archive": {
        "kind": "copy-docs",
        "text_target": "projects/pcr02/archive/source-docs/engineering-archive",
        "artifact_target": "artifacts/vault/engineering-archive",
        "decommission": "delete-external-after-verify",
    },
    "patent-disclosure": {
        "kind": "copy-docs-and-artifacts",
        "text_target": "domains/patents/archive/patent-disclosure",
        "artifact_target": "artifacts/vault/patent-disclosure",
        "decommission": "delete-external-after-verify",
    },
    "codex-archive": {
        "kind": "copy-docs",
        "text_target": "domains/codex/archive/source-docs/codex-archive",
        "artifact_target": "artifacts/vault/codex-archive",
        "decommission": "delete-external-after-verify",
    },
    "codex-archive-registry": {
        "kind": "copy-docs-and-artifacts",
        "text_target": "domains/codex/archive/source-docs/codex-archive-registry",
        "artifact_target": "artifacts/vault/codex-archive-registry",
        "decommission": "delete-external-after-verify",
    },
    "codex-memories": {"kind": "runtime-input", "decommission": "runtime-not-deleted"},
    "codex-history": {"kind": "runtime-input", "decommission": "runtime-not-deleted"},
    "codex-raw-sessions": {"kind": "runtime-input", "decommission": "runtime-not-deleted"},
    "codex-session-index": {"kind": "runtime-input", "decommission": "runtime-not-deleted"},
    "knowledge-hub-automation-runs": {"kind": "hub-native", "decommission": "not-external"},
    "pcr02-project-docs": {
        "kind": "copy-docs-and-artifacts",
        "text_target": "projects/pcr02/archive/source-docs/pcr02-project-docs",
        "artifact_target": "artifacts/vault/pcr02-project-docs",
        "decommission": "source-project-doc-prune-after-authorization",
    },
    "pcr02-project-tools": {
        "kind": "copy-docs",
        "text_target": "projects/pcr02/archive/source-docs/pcr02-project-tools",
        "artifact_target": "artifacts/vault/pcr02-project-tools",
        "decommission": "source-project-doc-prune-after-authorization",
    },
    "pcr02-project-knowledge": {
        "kind": "copy-docs",
        "text_target": "projects/pcr02/archive/source-docs/pcr02-project-knowledge",
        "artifact_target": "artifacts/vault/pcr02-project-knowledge",
        "decommission": "source-project-doc-prune-after-authorization",
    },
    "pcr02-product-test": {
        "kind": "copy-docs-and-artifacts",
        "text_target": "projects/pcr02/archive/source-docs/pcr02-product-test",
        "artifact_target": "artifacts/vault/pcr02-product-test",
        "decommission": "source-project-doc-prune-after-authorization",
    },
    "pcr02-project-scratch": {
        "kind": "copy-docs",
        "text_target": "projects/pcr02/archive/source-docs/pcr02-project-scratch",
        "artifact_target": "artifacts/vault/pcr02-project-scratch",
        "decommission": "source-project-doc-prune-after-authorization",
    },
    "pcr02-project-root-artifacts": {
        "kind": "project-root-shallow",
        "text_target": "projects/pcr02/archive/source-docs/pcr02-project-root-artifacts",
        "artifact_target": "artifacts/vault/pcr02-project-root-artifacts",
        "decommission": "source-project-root-not-deleted",
    },
    "pcr02-module-agent-rules": {
        "kind": "agent-rules",
        "text_target": "projects/pcr02/archive/source-docs/pcr02-module-agent-rules",
        "artifact_target": "artifacts/vault/pcr02-module-agent-rules",
        "decommission": "source-project-doc-prune-after-authorization",
    },
    "pcr02-project-agent-config": {
        "kind": "agent-config",
        "text_target": "projects/pcr02/archive/source-docs/pcr02-project-agent-config",
        "artifact_target": "artifacts/vault/pcr02-project-agent-config",
        "decommission": "source-project-config-not-deleted",
    },
}


def expand_path(text):
    return pathlib.Path(str(text).replace("~", str(pathlib.Path.home()))).expanduser()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sanitize_text(data):
    replacements = {
        str(pathlib.Path.home()).encode(): b"~",
        f"/vsdata/{pathlib.Path.home().name}".encode(): b"~",
    }
    result = data
    for old, new in replacements.items():
        result = result.replace(old, new)
    result = result.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    result = b"\n".join(line.rstrip(b" \t") for line in result.split(b"\n"))
    return result.rstrip(b"\n") + (b"\n" if result else b"")


def read_text_payload(path):
    return sanitize_text(path.read_bytes())


def safe_target(rel_text):
    rel = pathlib.PurePosixPath(rel_text)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"unsafe target path: {rel_text}")
    return root / pathlib.Path(*rel.parts)


def should_skip(path, source_root):
    rel = path.relative_to(source_root)
    return any(part in SKIP_DIRS for part in rel.parts)


def iter_source_files(source_id, source_root, policy):
    if not source_root.exists():
        return
    if source_root.is_file():
        yield source_root
        return
    kind = policy["kind"]
    if kind == "project-root-shallow":
        for path in sorted(source_root.iterdir()):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                yield path
        return
    if kind == "agent-rules":
        for path in sorted(source_root.rglob("AGENTS.md")):
            if not should_skip(path, source_root):
                yield path
        return
    if kind == "agent-config":
        for dirname in [".codex", ".vscode", ".kilo"]:
            base = source_root / dirname
            if not base.exists():
                continue
            for path in sorted(base.rglob("*")):
                if path.is_file() and not should_skip(path, source_root):
                    yield path
        return
    for path in sorted(source_root.rglob("*")):
        if path.is_file() and not should_skip(path, source_root):
            yield path


def classify_file(path, policy):
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return "copy-body"
    if policy["kind"] == "copy-docs-and-artifacts" and suffix in ARTIFACT_SUFFIXES:
        return "copy-artifact"
    return "drop-non-knowledge"


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + ("\n" if rows else "")
    )


sources_path = root / "registry" / "sources.json"
sources_doc = json.loads(sources_path.read_text())
sources = sources_doc.get("sources", [])
source_ids = [source.get("id", "") for source in sources]

errors = []
warnings = []
migration_rows = []
decommission_rows = []
tombstone_rows = []
copied = 0
existing_verified = 0
planned_copy = 0

for source in sources:
    source_id = source["id"]
    policy = SOURCE_POLICIES.get(source_id)
    if not policy:
        errors.append(f"no hard migration policy for source: {source_id}")
        continue
    origin_path = source.get("origin_path") or source.get("path", "")
    source_root = expand_path(origin_path)
    kind = policy["kind"]
    base_row = {
        "source_id": source_id,
        "origin_path": origin_path,
        "origin_role": source.get("role", ""),
        "origin_authority": source.get("authority", ""),
        "hard_migration_policy": kind,
        "checked_at": args.as_of,
    }
    if kind in {"runtime-input", "hub-native"}:
        migration_rows.append(
            {
                **base_row,
                "id": f"{source_id}-hard-migration-policy",
                "action": kind,
                "status": "covered",
                "target_path": "",
                "reason_zh": "运行态输入或 Hub 原生账本不作为外部知识正文迁移；后续只抽取候选、摘要或 registry 记录。",
            }
        )
        decommission_rows.append(
            {
                **base_row,
                "id": f"{source_id}-decommission-policy",
                "status": policy["decommission"],
                "delete_external": False,
                "reason_zh": "运行态或 Hub 原生输入不由知识硬迁移删除。",
            }
        )
        continue
    if not source_root.exists():
        errors.append(f"{source_id}: source path missing: {source_root}")
        continue
    source_file_count = 0
    copy_count = 0
    drop_count = 0
    artifact_count = 0
    for path in iter_source_files(source_id, source_root, policy):
        source_file_count += 1
        if source_root.is_file():
            rel = pathlib.PurePosixPath(path.name)
        else:
            rel = pathlib.PurePosixPath(path.relative_to(source_root).as_posix())
        action = classify_file(path, policy)
        source_hash = sha256(path)
        row = {
            **base_row,
            "id": f"{source_id}:{rel.as_posix()}",
            "source_path": rel.as_posix(),
            "source_sha256": source_hash,
            "size": path.stat().st_size,
            "action": action,
            "status": "planned",
        }
        if action == "copy-body":
            target_rel = pathlib.PurePosixPath(policy["text_target"]) / rel
            row["target_path"] = target_rel.as_posix()
            target = safe_target(target_rel.as_posix())
            target_payload = read_text_payload(path)
            target_hash = sha256_bytes(target_payload)
            row["target_sha256"] = target_hash
            planned_copy += 1
            copy_count += 1
            if target.exists():
                if target.is_file() and sha256(target) == target_hash:
                    row["status"] = "existing-verified"
                    existing_verified += 1
                elif args.apply:
                    target.write_bytes(target_payload)
                    if sha256(target) != target_hash:
                        row["status"] = "blocked-refresh-hash-mismatch"
                        errors.append(f"{source_id}: refreshed text hash mismatch: {target_rel.as_posix()}")
                    else:
                        row["status"] = "refreshed"
                        copied += 1
                else:
                    row["status"] = "blocked-target-conflict"
                    errors.append(f"{source_id}: target conflict: {target_rel.as_posix()}")
            elif args.apply:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(target_payload)
                shutil.copystat(path, target)
                if sha256(target) != target_hash:
                    row["status"] = "blocked-copy-hash-mismatch"
                    errors.append(f"{source_id}: copied hash mismatch: {target_rel.as_posix()}")
                else:
                    row["status"] = "copied"
                    copied += 1
            else:
                row["status"] = "copy-planned"
        elif action == "copy-artifact":
            target_rel = pathlib.PurePosixPath(policy["artifact_target"]) / rel
            row["target_path"] = target_rel.as_posix()
            target = safe_target(target_rel.as_posix())
            planned_copy += 1
            artifact_count += 1
            if target.exists():
                if target.is_file() and sha256(target) == source_hash:
                    row["status"] = "existing-verified"
                    existing_verified += 1
                else:
                    row["status"] = "blocked-target-conflict"
                    errors.append(f"{source_id}: artifact target conflict: {target_rel.as_posix()}")
            elif args.apply:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                if sha256(target) != source_hash:
                    row["status"] = "blocked-copy-hash-mismatch"
                    errors.append(f"{source_id}: copied artifact hash mismatch: {target_rel.as_posix()}")
                else:
                    row["status"] = "copied"
                    copied += 1
            else:
                row["status"] = "copy-planned"
        else:
            drop_count += 1
            row["target_path"] = ""
            row["status"] = "dropped-by-policy"
            row["reason_zh"] = "非知识正文或非托管附件；硬迁移终态不保留为 Hub 正文。"
        migration_rows.append(row)
    decommission_rows.append(
        {
            **base_row,
            "id": f"{source_id}-decommission-policy",
            "status": policy["decommission"],
            "delete_external": policy["decommission"] == "delete-external-after-verify",
            "source_file_count": source_file_count,
            "copy_body_count": copy_count,
            "copy_artifact_count": artifact_count,
            "drop_count": drop_count,
            "reason_zh": "外部 source 只有在迁移 manifest 校验通过、备份和授权账本齐备后才删除或剪枝。",
        }
    )
    tombstone_rows.append(
        {
            **base_row,
            "id": f"{source_id}-tombstone",
            "status": "planned" if not args.apply else "migration-recorded",
            "canonical_manifest": f"artifacts/manifests/source-hard-migration-{args.as_of.replace('-', '')}.jsonl",
            "decommission_manifest": f"artifacts/manifests/source-hard-decommission-{args.as_of.replace('-', '')}.jsonl",
            "delete_policy": policy["decommission"],
            "notes_zh": "硬迁移完成后，active 面不得再把该 origin 当作 source、authority、SSOT 或 reference-first 入口。",
        }
    )

unknown = sorted(set(SOURCE_POLICIES) - set(source_ids))
if unknown:
    warnings.append(f"hard migration policy has unregistered sources: {', '.join(unknown)}")

date_stamp = args.as_of.replace("-", "")
migration_path = root / "artifacts" / "manifests" / f"source-hard-migration-{date_stamp}.jsonl"
decommission_path = root / "artifacts" / "manifests" / f"source-hard-decommission-{date_stamp}.jsonl"
tombstone_path = root / "registry" / "source-tombstones.jsonl"
summary_path = root / "artifacts" / "manifests" / f"source-hard-migration-{date_stamp}.md"

if args.apply and not errors:
    write_jsonl(migration_path, migration_rows)
    write_jsonl(decommission_path, decommission_rows)
    write_jsonl(tombstone_path, tombstone_rows)
    summary = [
        f"# Source hard migration {args.as_of}",
        "",
        "本报告记录 Knowledge Hub 硬迁移的当前执行结果。长期知识正文以 Hub target 为准，外部 origin 只保留 tombstone/provenance。",
        "",
        f"- registered_sources: {len(sources)}",
        f"- migration_rows: {len(migration_rows)}",
        f"- planned_copy_or_artifact: {planned_copy}",
        f"- copied: {copied}",
        f"- existing_verified: {existing_verified}",
        f"- decommission_rows: {len(decommission_rows)}",
        "",
        "## 验证",
        "",
        "- 后续必须运行 `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics`。",
        "- 删除外部 source 前必须复核 `source-hard-decommission-*.jsonl` 和 `registry/source-tombstones.jsonl`。",
    ]
    summary_path.write_text("\n".join(summary) + "\n")

result = {
    "status": "blocked" if errors else ("applied" if args.apply else "planned"),
    "as_of": args.as_of,
    "registered_sources": len(sources),
    "migration_rows": len(migration_rows),
    "planned_copy_or_artifact": planned_copy,
    "copied": copied,
    "existing_verified": existing_verified,
    "migration_manifest": str(migration_path.relative_to(root)),
    "decommission_manifest": str(decommission_path.relative_to(root)),
    "tombstone_ledger": str(tombstone_path.relative_to(root)),
    "summary": str(summary_path.relative_to(root)),
    "errors": errors,
    "warnings": warnings,
}

if args.json:
    print(json.dumps(result, ensure_ascii=False, indent=2))
else:
    for key in [
        "status",
        "as_of",
        "registered_sources",
        "migration_rows",
        "planned_copy_or_artifact",
        "copied",
        "existing_verified",
        "migration_manifest",
        "decommission_manifest",
        "tombstone_ledger",
        "summary",
    ]:
        print(f"{key}: {result[key]}")
    for item in warnings:
        print(f"WARN {item}")
    for item in errors:
        print(f"ERROR {item}")

sys.exit(3 if errors else 0)
PY
