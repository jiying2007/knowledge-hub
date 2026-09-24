"""Bound input before parsing; over-budget stdio is terminated, not drained."""

import io
import json

import pytest

from tools.codex_assets.knowledge_hub import mcp_v3_server as server


class BoundedInput(io.BytesIO):
    def __init__(self, value):
        super().__init__(value)
        self.read_sizes = []

    def readline(self, size=-1):
        assert 0 < size <= server.MAX_LINE_BYTES + 1
        self.read_sizes.append(size)
        return super().readline(size)


def _run(payload):
    source = BoundedInput(payload)
    output = io.StringIO()
    code = server._serve(None, source, output, "knowledge-reader")
    return code, source, [json.loads(line) for line in output.getvalue().splitlines()]


@pytest.mark.parametrize("payload", [
    b"x" * (server.MAX_LINE_BYTES + 100),
    b" " * (server.MAX_LINE_BYTES + 100) + b"\n{}\n",
    ("中" * (server.MAX_LINE_BYTES // 3 + 1)).encode("utf-8"),
])
def test_oversized_stream_stops_after_one_bounded_read(payload):
    code, source, responses = _run(payload)
    assert code == 2
    assert source.tell() == server.MAX_LINE_BYTES + 1
    assert source.read_sizes == [server.MAX_LINE_BYTES + 1]
    assert len(responses) == 1
    assert responses[0]["error"]["code"] == -32600
    assert responses[0]["id"] is None


def test_exact_limit_is_not_rejected_as_oversized():
    code, _, responses = _run(b" " * (server.MAX_LINE_BYTES - 1) + b"\n")
    assert code == 0
    assert responses == []


def test_invalid_utf8_is_rejected_without_echo_or_loss_of_next_request():
    code, _, responses = _run(b"\xff\xfe\n[]\n")
    assert code == 0
    assert [row["error"]["code"] for row in responses] == [-32700, -32600]
    assert all(row["id"] is None for row in responses)


def test_whitespace_and_notifications_produce_no_response():
    payload = b'\n  \n{"jsonrpc":"2.0","method":"notifications/progress"}\n'
    assert _run(payload)[2] == []


def test_valid_message_and_final_line_without_newline_reach_handler(monkeypatch):
    calls = []
    def handle(root, request, *, agent_id):
        calls.append((request, agent_id))
        return {"jsonrpc": "2.0", "id": request["id"], "result": {"text": "中文"}}
    monkeypatch.setattr(server, "handle_mcp_stateless_request", handle)
    request = {"jsonrpc": "2.0", "id": 7, "method": "server/discover"}
    code, _, responses = _run(json.dumps(request).encode("utf-8"))
    assert code == 0
    assert calls == [(request, "knowledge-reader")]
    assert responses[0]["result"]["text"] == "中文"


def test_text_stream_fallback_has_the_same_byte_limit():
    source = io.StringIO("中" * (server.MAX_LINE_BYTES // 3 + 1))
    output = io.StringIO()
    assert server._serve(None, source, output, "knowledge-reader") == 2
    assert json.loads(output.getvalue())["error"]["code"] == -32600


def test_one_shot_and_deeply_nested_json_are_bounded(monkeypatch):
    response = server._process(None, "x" * (server.MAX_LINE_BYTES + 1), "knowledge-reader")
    assert response["error"]["code"] == -32600
    response = server._process(None, "[" * 2000 + "0" + "]" * 2000, "knowledge-reader")
    assert response["error"]["code"] in {-32700, -32600}
    def exhausted(raw):
        raise RecursionError("parser recursion exhausted")
    monkeypatch.setattr(server.json, "loads", exhausted)
    assert server._process(None, "{}", "knowledge-reader")["error"]["code"] == -32700
    assert server._process(None, "\ud800", "knowledge-reader")["error"]["code"] == -32700
