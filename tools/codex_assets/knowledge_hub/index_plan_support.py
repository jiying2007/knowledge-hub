"""Shared helpers for the index-plan CLI."""

import datetime as dt
import hashlib
import json
import os
import pathlib
import re

SOURCE_COVERAGE_RE = re.compile(r"^knowledge-hub-source-coverage-closeout-(\d{8})\.jsonl$")

def emit_json(payload, *, budget_bytes, sort_keys=False):
    output = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=sort_keys)
    output_bytes = len(output.encode("utf-8"))
    if output_bytes > budget_bytes:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "error": "output-budget-exceeded",
                    "projected_bytes": output_bytes,
                    "budget_bytes": budget_bytes,
                    "next_action": "use --summary-json, a narrower --section, or a smaller queue page",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return False
    print(output)
    return True

def user_path_prefixes():
    prefixes = [str(pathlib.Path.home())]
    user_name = os.environ.get("USER", "")
    if user_name:
        prefixes.append("/" + "vsdata" + "/" + user_name)
    return [prefix for prefix in prefixes if prefix and prefix != "/"]

def display_path(value):
    text = str(value)
    for prefix in user_path_prefixes():
        if text == prefix:
            text = "~"
        elif text.startswith(prefix + "/"):
            text = "~" + text[len(prefix):]
        else:
            text = text.replace(prefix, "~")
    return text

def is_local_manifest_draft(path):
    return path.suffix == ".jsonl" and path.name.endswith(".local.jsonl")

def repository_file_sha256(root, relative_path):
    path_text = str(relative_path or "")
    if not path_text:
        return ""
    candidate = pathlib.Path(path_text)
    if candidate.is_absolute():
        return ""
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return ""
    if not resolved.is_file():
        return ""
    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def select_source_coverage_closeout(root):
    paths = sorted((root / "artifacts" / "manifests").glob("knowledge-hub-source-coverage-closeout-*.jsonl"))
    dated = []
    ignored = []
    for path in paths:
        relative = str(path.relative_to(root))
        match = SOURCE_COVERAGE_RE.match(path.name)
        if not match:
            ignored.append(relative)
            continue
        date_text = match.group(1)
        try:
            dt.datetime.strptime(date_text, "%Y%m%d").date()
        except Exception:
            ignored.append(relative)
            continue
        dated.append((date_text, relative, path))
    dated.sort(key=lambda row: (row[0], row[1]))
    selection = {
        "pattern": "artifacts/manifests/knowledge-hub-source-coverage-closeout-*.jsonl",
        "required_filename": "knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl",
        "strategy": "filename-yyyymmdd-sort-last",
        "candidate_count": len(paths),
        "candidates": [str(path.relative_to(root)) for path in paths],
        "dated_candidate_count": len(dated),
        "dated_candidates": [row[1] for row in dated],
        "ignored_non_date_candidates": ignored,
        "selected": dated[-1][1] if dated else "",
        "reason_zh": "只按 knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl 的日期字段选择最新 closeout；非日期候选会被忽略并作为 warning 暴露，避免 future/latest 等文件名被静默选中。",
    }
    return selection, dated[-1][2] if dated else None

def read_json_array(root, errors, path, key):
    try:
        data = json.loads(path.read_text())
        value = data.get(key, [])
        if not isinstance(value, list):
            errors.append(f"{path.relative_to(root)} field {key} is not a list")
            return []
        return value
    except Exception as exc:
        errors.append(f"cannot read {path.relative_to(root)}: {exc}")
        return []

def read_jsonl(root, errors, path, label):
    rows = []
    try:
        for line_no, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                errors.append(f"{label}:{line_no}: {exc}")
    except Exception as exc:
        errors.append(f"cannot read {label}: {exc}")
    return rows

