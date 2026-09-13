import datetime as dt
import json
import os
import pathlib
import shlex
import subprocess
from typing import Any, Dict, List, Sequence, Tuple

DISPLAY_TOOL_ROOT = "~/knowledge-hub/tools"


def resolve_today(args: Any, parser: Any) -> Tuple[dt.date, str]:
    if args.as_of:
        raw_value = args.as_of
        source = "arg:--as-of"
    else:
        raw_value = os.environ.get("KNOWLEDGE_TODAY", "")
        source = "env:KNOWLEDGE_TODAY" if raw_value else "system-date"
    if raw_value:
        try:
            return dt.date.fromisoformat(raw_value), source
        except Exception:
            parser.error("invalid date for {}: {}".format(source, raw_value))
    return dt.date.today(), source


def user_path_prefixes() -> List[str]:
    prefixes = [str(pathlib.Path.home())]
    user_name = os.environ.get("USER", "")
    if user_name:
        prefixes.append("/" + "vsdata" + "/" + user_name)
    return [prefix for prefix in prefixes if prefix and prefix != "/"]


def display_path(value: Any) -> str:
    text = str(value)
    for prefix in user_path_prefixes():
        if text == prefix:
            text = "~"
        elif text.startswith(prefix + "/"):
            text = "~" + text[len(prefix):]
        else:
            text = text.replace(prefix, "~")
    return text


def display_tool(script_name: str) -> str:
    return "{}/{}".format(DISPLAY_TOOL_ROOT, script_name)


def shell_command(parts: Sequence[Any]) -> str:
    quoted = []
    for part in parts:
        text = str(part)
        if text.startswith("~/"):
            quoted.append(text)
        else:
            quoted.append(shlex.quote(text))
    return " ".join(quoted)


def load_json(root: pathlib.Path, errors: List[str], path: pathlib.Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        errors.append("cannot load {}: {}".format(path.relative_to(root), exc))
        return {}


def load_jsonl(root: pathlib.Path, errors: List[str], path: pathlib.Path) -> List[Dict[str, Any]]:
    rows = []
    try:
        lines = path.read_text().splitlines()
    except Exception as exc:
        errors.append("cannot read {}: {}".format(path.relative_to(root), exc))
        return rows
    for line_no, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception as exc:
            errors.append("{}:{}: invalid jsonl: {}".format(path.relative_to(root), line_no, exc))
    return rows


def run_json(root: pathlib.Path, errors: List[str], command: Sequence[str]) -> Dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    payload: Dict[str, Any] = {}
    parse_error = ""
    if completed.stdout.strip():
        try:
            payload = json.loads(completed.stdout)
        except Exception as exc:
            parse_error = str(exc)
            errors.append("cannot parse {} output: {}".format(" ".join(command), exc))
    else:
        parse_error = "empty JSON output"
        errors.append("{} returned no JSON output".format(" ".join(command)))
    return {
        "command": list(command),
        "exit_code": completed.returncode,
        "payload": payload,
        "parse_error": parse_error,
        "stderr": completed.stderr.strip(),
    }


def count_by(rows: Sequence[Dict[str, Any]], field: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(field, "") or "<missing>")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def parse_date(value: Any) -> Any:
    try:
        return dt.date.fromisoformat(str(value))
    except Exception:
        return None
