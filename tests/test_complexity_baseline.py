"""Raw Git baselines ignore export attributes and reject damaged protocols."""

import subprocess

import pytest

from tests.test_complexity_budget import _long_function, _write_budget_policy
from tools.codex_assets.knowledge_hub import complexity_baseline as baseline
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.complexity_budget import evaluate_complexity_budget

OID = "a" * 40
PATH = baseline.PACKAGE_PREFIX + "one.py"


def _git(root, *args):
    return subprocess.run(["rtk", "git", *args], cwd=root, check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()


def _commit(root):
    _git(root, "init", "-q")
    _git(root, "add", ".")
    _git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
         "-c", "commit.gpgsign=false", "commit", "-qm", "baseline fixture")
    return _git(root, "rev-parse", "HEAD")


def _tree(name=PATH, oid=OID, kind="blob"):
    return "100644 {} {}\t{}\0".format(kind, oid, name)


def _metadata(monkeypatch, text):
    monkeypatch.setattr(baseline, "run_rtk", lambda *args, **kwargs: {"stdout": text})


def _blob(data, oid=OID):
    return oid.encode() + b" blob " + str(len(data)).encode() + b"\n" + data + b"\n"


@pytest.mark.parametrize("module_count", [1, 7])
def test_real_raw_git_is_constant_batch_and_preserves_attributes_and_dirty_text(tmp_path, monkeypatch, module_count):
    texts = {}
    for index in range(module_count):
        relative = baseline.PACKAGE_PREFIX + "nested/module_{}.py".format(index)
        texts[relative] = "# 中文基线{}\r\n值 = '证据'\n# $Format:%H$\n\n".format(index)
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(texts[relative].encode("utf-8"))
    attributes = tmp_path / ".gitattributes"
    attributes.write_text(baseline.PACKAGE_PREFIX + "nested/module_0.py export-ignore\n"
                          + baseline.PACKAGE_PREFIX + "nested/*.py export-subst\n", encoding="utf-8")
    ref = _commit(tmp_path)
    working = tmp_path / next(iter(texts))
    working.write_text("# 当前未提交内容\n", encoding="utf-8")
    attributes.write_text("* export-ignore export-subst\n", encoding="utf-8")
    calls, metadata_calls = [], []
    real_batch, real_metadata = baseline.run_bounded, baseline.run_rtk

    def counted(command, **kwargs):
        calls.append((command, kwargs["input_bytes"]))
        return real_batch(command, **kwargs)

    def tree_counted(root, command, **kwargs):
        metadata_calls.append(command)
        return real_metadata(root, command, **kwargs)

    monkeypatch.setattr(baseline, "run_bounded", counted)
    monkeypatch.setattr(baseline, "run_rtk", tree_counted)
    assert baseline.baseline_python_texts(tmp_path, ref) == texts
    assert len(calls) == len(metadata_calls) == 1
    assert calls[0][0] == ["rtk", "git", "cat-file", "--batch"]
    assert len(calls[0][1].splitlines()) == module_count
    assert metadata_calls[0][:4] == ["git", "ls-tree", "-r", "-z"]
    assert working.read_text(encoding="utf-8") == "# 当前未提交内容\n"
    assert attributes.read_text(encoding="utf-8") == "* export-ignore export-subst\n"


@pytest.mark.parametrize("text", [
    _tree("/absolute/escape.py"), _tree(baseline.PACKAGE_PREFIX + "../escape.py"),
    "malformed\0", "100644 blob\t" + PATH + "\0",
    _tree(kind="tree"), _tree(kind="commit"), _tree(oid="g" * 40),
    _tree(oid="a" * 39), _tree(oid="a" * 65),
])
def test_unsafe_or_invalid_tree_metadata_fails_closed(tmp_path, monkeypatch, text):
    _metadata(monkeypatch, text)
    with pytest.raises(KnowledgeHubError):
        baseline._python_objects(tmp_path, "fixture")


def test_duplicate_tree_paths_and_member_budget_fail_closed(tmp_path, monkeypatch):
    _metadata(monkeypatch, _tree() + _tree())
    with pytest.raises(KnowledgeHubError, match="duplicate"):
        baseline._python_objects(tmp_path, "fixture")
    _metadata(monkeypatch, _tree() + _tree(baseline.PACKAGE_PREFIX + "two.py"))
    monkeypatch.setattr(baseline, "MAX_MEMBERS", 1)
    with pytest.raises(KnowledgeHubError, match="member budget"):
        baseline._python_objects(tmp_path, "fixture")


def test_raw_protocol_handles_utf8_byte_sizes_duplicate_oids_and_sha256():
    other = baseline.PACKAGE_PREFIX + "same.py"
    third = baseline.PACKAGE_PREFIX + "sha256.py"
    data = "中文\r\n".encode() + b"\x00\xff\n"
    text = data.decode("utf-8", errors="replace")
    objects = [(PATH, OID), (other, OID), (third, "b" * 64)]
    raw = _blob(data) + _blob(data) + _blob(b"pass\n", "b" * 64)
    assert baseline._decode_blobs(raw, objects) == {PATH: text, other: text, third: "pass\n"}


@pytest.mark.parametrize("raw", [
    b"incomplete", b"x" * 257 + b"\n",
    _blob(b"pass\n", "b" * 40),
    OID.encode() + b" missing\n",
    OID.encode() + b" tree 0\n\n",
    OID.encode() + b" blob -1\n\n",
    OID.encode() + b" blob invalid\n\n",
    OID.encode() + b" blob 10\nshort",
    OID.encode() + b" blob 4\npassX",
    _blob(b"pass\n") + b"trailing",
])
def test_batch_header_identity_size_truncation_delimiter_and_trailing_fail_closed(raw):
    with pytest.raises(KnowledgeHubError):
        baseline._decode_blobs(raw, [(PATH, OID)])


def test_raw_member_capture_limit_is_enforced(monkeypatch):
    monkeypatch.setattr(baseline, "MAX_CAPTURE_BYTES", 4)
    with pytest.raises(KnowledgeHubError, match="byte budget"):
        baseline._decode_blobs(_blob(b"12345"), [(PATH, OID)])


@pytest.mark.parametrize("exit_code,overflow", [(1, False), (0, True)])
def test_failed_or_overflowed_batch_cannot_become_partial_baseline(tmp_path, monkeypatch, exit_code, overflow):
    _metadata(monkeypatch, _tree())
    def failed(command, **kwargs):
        return subprocess.CompletedProcess(command, exit_code, _blob(b"pass\n"), b"error"), overflow
    monkeypatch.setattr(baseline, "run_bounded", failed)
    with pytest.raises(KnowledgeHubError, match="batch failed"):
        baseline.baseline_python_texts(tmp_path, "fixture")


def test_input_budget_rejects_before_starting_batch_process(tmp_path, monkeypatch):
    _metadata(monkeypatch, _tree())
    monkeypatch.setattr(baseline, "MAX_CAPTURE_BYTES", 40)
    def forbidden(*args, **kwargs):
        pytest.fail("oversized batch input must not launch")
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    with pytest.raises(ValueError, match="capture budget"):
        baseline.baseline_python_texts(tmp_path, "fixture")


def test_valid_commit_missing_package_stays_new_module_and_blocks_oversized_function(tmp_path, monkeypatch):
    (tmp_path / "README.md").write_text("仅有其他文件\n", encoding="utf-8")
    ref = _commit(tmp_path)
    def forbidden(*args, **kwargs):
        pytest.fail("empty valid tree must not launch cat-file")
    with monkeypatch.context() as patch:
        patch.setattr(baseline, "run_bounded", forbidden)
        assert baseline.baseline_python_texts(tmp_path, ref) == {}
    package = tmp_path / baseline.PACKAGE_PREFIX
    package.mkdir(parents=True)
    (package / "new.py").write_text(_long_function("new_function", body_lines=90), encoding="utf-8")
    _write_budget_policy(tmp_path, module_limit=200, function_limit=80)
    monkeypatch.setenv("KNOWLEDGE_COMPLEXITY_BASE_REF", ref)
    result = evaluate_complexity_budget(tmp_path)
    assert result["status"] == "fail" and result["baseline_ref_resolved"] is True
    assert any(row["type"] == "new-function-size" and row["function"] == "new_function"
               for row in result["regressions"])
    assert result["modules"][0]["tracked_baseline"] is False


def test_missing_ref_is_not_an_empty_valid_package(tmp_path):
    (tmp_path / "README.md").write_text("baseline\n", encoding="utf-8")
    _commit(tmp_path)
    with pytest.raises(KnowledgeHubError):
        baseline.baseline_python_texts(tmp_path, "missing-ref")
