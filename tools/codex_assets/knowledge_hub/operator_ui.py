"""Local read-only Operator UI for Knowledge Hub."""

from __future__ import annotations

import argparse
import html
import json
import pathlib
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, Mapping, Sequence, Tuple

from .common import KnowledgeHubError, repository_root
from .operator_state import build_operator_state

LOOPBACK_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
_MACHINE_CLASSES = {
    "machine-discovery",
    "machine-after-prerequisite",
    "dependency-gate",
}

_CSS = """
:root { color-scheme: light dark; font-family: ui-sans-serif, system-ui, sans-serif; }
body { margin: 0; background: Canvas; color: CanvasText; }
main { max-width: 1440px; margin: 0 auto; padding: 24px; }
header { display:flex; justify-content:space-between; gap:16px; align-items:flex-start; }
h1 { margin:0; font-size:26px; }
small,.muted { opacity:.7; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin:20px 0; }
.card,section { border:1px solid color-mix(in srgb, CanvasText 18%, transparent); border-radius:12px; padding:14px; }
.card strong { display:block; font-size:24px; margin-top:6px; }
section { margin:16px 0; overflow:auto; }
table { width:100%; border-collapse:collapse; font-size:14px; }
th,td { text-align:left; padding:9px 8px; border-bottom:1px solid color-mix(in srgb, CanvasText 12%, transparent); vertical-align:top; }
code { font-family:ui-monospace, SFMono-Regular, Consolas, monospace; font-size:12px; }
.badge { display:inline-block; border:1px solid currentColor; border-radius:999px; padding:2px 7px; margin:1px 3px 1px 0; font-size:12px; }
ul { padding-left:20px; }
.ok { opacity:.75; }
.attention { font-weight:600; }
footer { margin:24px 0 8px; opacity:.7; font-size:13px; }
"""


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _card(label: str, value: Any) -> str:
    return '<div class="card"><span>{}</span><strong>{}</strong></div>'.format(
        _escape(label), _escape(value)
    )


def _badges(values: Sequence[Any]) -> str:
    if not values:
        return '<span class="muted">—</span>'
    return "".join(
        '<span class="badge">{}</span>'.format(_escape(value)) for value in values
    )


def _project_rows(readiness: Mapping[str, Any]) -> str:
    rendered = []
    for row in readiness.get("projects", []):
        if not isinstance(row, Mapping):
            continue
        rendered.append(
            "<tr>"
            "<td><code>{}</code><br><span class=\"muted\">{}</span></td>"
            "<td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td>"
            "</tr>".format(
                _escape(row.get("project_id", "")),
                _escape(row.get("name", "")),
                _escape(row.get("evidence_profile", "")),
                _escape(row.get("owner_boundary_status", "")),
                _escape(row.get("evidence_field_status", "")),
                _badges(row.get("action_classes", [])),
                _badges(row.get("attention", [])),
            )
        )
    return "".join(rendered)


def _status_actions(state: Mapping[str, Any]) -> str:
    rows = [
        str(value) for value in state.get("next_actions_zh", []) if str(value)
    ]
    if not rows:
        return '<p class="ok">当前 status projection 没有给出下一步动作。</p>'
    return "<ul>{}</ul>".format(
        "".join("<li>{}</li>".format(_escape(row)) for row in rows)
    )


def _external_rows(external: Mapping[str, Any]) -> str:
    rows = external.get("open_gaps", [])
    if not rows:
        return '<p class="ok">没有开放的 external closure gap。</p>'
    items = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        owner = (
            " · owner={}".format(_escape(row.get("owner", "")))
            if row.get("owner")
            else ""
        )
        items.append(
            "<li><code>{}</code> — {}{}</li>".format(
                _escape(row.get("id", "")),
                _escape(row.get("status", "")),
                owner,
            )
        )
    return "<ul>{}</ul>".format("".join(items))


def _queue_rows(queue: Mapping[str, Any], *, machine: bool) -> str:
    rows = []
    for row in queue.get("actions", []):
        if not isinstance(row, Mapping):
            continue
        execution_class = str(row.get("execution_class", ""))
        if (execution_class in _MACHINE_CLASSES) != machine:
            continue
        target = str(row.get("project_id", "")) or str(row.get("field", ""))
        rows.append(
            "<tr><td>{}</td><td><code>{}</code></td><td>{}</td><td>{}</td>"
            "</tr>".format(
                _escape(execution_class),
                _escape(target),
                _escape(row.get("field", "")),
                _escape(row.get("summary_zh", "")),
            )
        )
    if not rows:
        return '<p class="ok">当前没有此类 action。</p>'
    return (
        "<table><thead><tr><th>Execution class</th><th>Target</th>"
        "<th>Field</th><th>Next step</th></tr></thead>"
        "<tbody>{}</tbody></table>".format("".join(rows))
    )


def _candidate_refs(row: Mapping[str, Any]) -> str:
    refs = []
    for candidate in row.get("candidates", []):
        if not isinstance(candidate, Mapping):
            continue
        refs.append(str(candidate.get("ref", "")))
    return _badges(refs)


def _provider_query_refs(row: Mapping[str, Any]) -> str:
    refs = []
    for query in row.get("provider_queries", []):
        if not isinstance(query, Mapping):
            continue
        refs.append(
            "{}:{}:{}".format(
                query.get("provider", ""),
                query.get("operation", ""),
                query.get("target", ""),
            )
        )
    return _badges(refs)


def _discovery_rows(discovery: Mapping[str, Any]) -> str:
    rows = []
    for row in discovery.get("rows", []):
        if not isinstance(row, Mapping):
            continue
        rows.append(
            "<tr><td><code>{}</code></td><td>{}</td><td>{}</td>"
            "<td>{}</td><td>{}</td></tr>".format(
                _escape(row.get("project_id", "")),
                _escape(row.get("field", "")),
                _escape(row.get("status", "")),
                _candidate_refs(row),
                _provider_query_refs(row),
            )
        )
    if not rows:
        return '<p class="ok">当前没有 machine-discovery action。</p>'
    return (
        "<table><thead><tr><th>Project</th><th>Field</th><th>Status</th>"
        "<th>Local candidates</th><th>Provider queries</th></tr></thead>"
        "<tbody>{}</tbody></table>".format("".join(rows))
    )


def _cards(
    state: Mapping[str, Any],
    readiness: Mapping[str, Any],
    external: Mapping[str, Any],
    terminal: Mapping[str, Any],
    queue: Mapping[str, Any],
    discovery: Mapping[str, Any],
) -> str:
    return "".join(
        (
            _card("Control plane", state.get("status", "")),
            _card("Projects", readiness.get("project_count", 0)),
            _card(
                "Source mapped",
                "{}/{}".format(
                    readiness.get("source_mapping_ready_count", 0),
                    readiness.get("project_count", 0),
                ),
            ),
            _card(
                "Field complete",
                "{}/{}".format(
                    readiness.get("evidence_field_complete_count", 0),
                    readiness.get("project_count", 0),
                ),
            ),
            _card(
                "Evidence ready",
                "{}/{}".format(
                    readiness.get("evidence_ready_count", 0),
                    readiness.get("project_count", 0),
                ),
            ),
            _card("Machine discovery", queue.get("machine_candidate_count", 0)),
            _card("Candidates found", discovery.get("candidate_found_count", 0)),
            _card("Provider needed", discovery.get("provider_required_count", 0)),
            _card("Machine blocked", queue.get("machine_blocked_count", 0)),
            _card("Human projects", queue.get("human_project_count", 0)),
            _card("External open", external.get("open_count", 0)),
            _card(
                "Terminal",
                "true"
                if terminal.get("terminal")
                else terminal.get("status", "false"),
            ),
        )
    )


def render_dashboard(state: Mapping[str, Any]) -> str:
    readiness = state.get("readiness", {})
    external = state.get("external_closure", {})
    terminal = state.get("terminal_closure", {})
    queue = state.get("action_queue", {})
    discovery = state.get("discovery", {})
    readiness_map = readiness if isinstance(readiness, Mapping) else {}
    external_map = external if isinstance(external, Mapping) else {}
    terminal_map = terminal if isinstance(terminal, Mapping) else {}
    queue_map = queue if isinstance(queue, Mapping) else {}
    discovery_map = discovery if isinstance(discovery, Mapping) else {}
    cards = _cards(
        state,
        readiness_map,
        external_map,
        terminal_map,
        queue_map,
        discovery_map,
    )
    return """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>Knowledge Hub Operator UI</title><style>{css}</style></head>
<body><main>
<header><div><h1>Knowledge Hub Operator UI</h1>
<p class="muted">Machine-first · Human-on-exception · Read-only</p></div>
<div><a href="/api/state">JSON API</a></div></header>
<div class="grid">{cards}</div>
<section><h2>Discovery Queue</h2>
<p class="muted">自动执行本地 registry discovery；远端只生成 provider query，
不在 Hub core 内发起网络或写入。</p>{discovery}</section>
<section><h2>Machine Queue</h2>
<p class="muted">先由机器发现候选或等待前置；当前不会自动写仓库。</p>{machine}</section>
<section><h2>Human / External Queue</h2>{human}</section>
<section><h2>Status Next Actions</h2>{actions}</section>
<section><h2>External Closure</h2>{external}</section>
<section><h2>Projects</h2>
<table><thead><tr><th>Project</th><th>Profile</th><th>Owner boundary</th>
<th>Evidence fields</th><th>Action class</th><th>Raw attention</th></tr></thead>
<tbody>{projects}</tbody></table></section>
<footer>只读界面；事实源仍是 registry / status / readiness / terminal closure。
Discovery candidate 永远是 candidate-only；provider query 只描述应由 provider 执行的
只读查询，不代表查询已经执行，也不代表 evidence 可以绑定。</footer>
</main></body></html>""".format(
        css=_CSS,
        cards=cards,
        discovery=_discovery_rows(discovery_map),
        machine=_queue_rows(queue_map, machine=True),
        human=_queue_rows(queue_map, machine=False),
        actions=_status_actions(state),
        external=_external_rows(external_map),
        projects=_project_rows(readiness_map),
    )


class OperatorHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        server_address: Tuple[str, int],
        root: pathlib.Path,
        state_builder: Callable[[pathlib.Path], Dict[str, Any]] = build_operator_state,
    ) -> None:
        self.root = root
        self.state_builder = state_builder
        super().__init__(server_address, OperatorRequestHandler)


class OperatorRequestHandler(BaseHTTPRequestHandler):
    server_version = "KnowledgeHubOperatorUI/1"

    def _headers(self, content_type: str, length: int) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'unsafe-inline'; script-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'",
        )

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self._headers(content_type, len(body))
        self.end_headers()
        self.wfile.write(body)

    def _state(self) -> Dict[str, Any]:
        server = self.server
        return server.state_builder(server.root)  # type: ignore[attr-defined]

    def do_GET(self) -> None:
        if self.path == "/healthz":
            body = json.dumps({"status": "ok", "read_only": True}).encode("utf-8")
            self._send(HTTPStatus.OK, body, "application/json; charset=utf-8")
            return
        try:
            state = self._state()
        except Exception as exc:
            body = json.dumps(
                {"status": "error", "read_only": True, "error": str(exc)}
            ).encode("utf-8")
            self._send(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                body,
                "application/json; charset=utf-8",
            )
            return
        if self.path == "/api/state":
            body = json.dumps(state, ensure_ascii=False, indent=2).encode("utf-8")
            self._send(HTTPStatus.OK, body, "application/json; charset=utf-8")
            return
        if self.path == "/":
            body = render_dashboard(state).encode("utf-8")
            self._send(HTTPStatus.OK, body, "text/html; charset=utf-8")
            return
        self._send(
            HTTPStatus.NOT_FOUND,
            b'{"status":"not-found"}',
            "application/json; charset=utf-8",
        )

    def do_POST(self) -> None:
        self._send(
            HTTPStatus.METHOD_NOT_ALLOWED,
            b'{"status":"read-only","error":"write methods are disabled"}',
            "application/json; charset=utf-8",
        )

    def log_message(self, format: str, *args: Any) -> None:
        return


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default="")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--json", action="store_true", help="Print operator state and exit.")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    try:
        root = repository_root(args.root)
    except KnowledgeHubError as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(build_operator_state(root), ensure_ascii=False, indent=2))
        return 0
    server = OperatorHTTPServer((LOOPBACK_HOST, args.port), root)
    print(
        "Knowledge Hub Operator UI: http://{}:{}/".format(LOOPBACK_HOST, args.port),
        flush=True,
    )
    print("Read-only; press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
