"""Read raw immutable Git blobs once, without archive export attributes."""

from __future__ import annotations

import os
import pathlib
import re
from typing import Dict, List, Tuple

from .bounded_process import run_bounded
from .common import KnowledgeHubError, run_rtk

PACKAGE_PREFIX = "tools/codex_assets/knowledge_hub/"
MAX_CAPTURE_BYTES = 8 * 1024 * 1024
MAX_MEMBERS = 10000


def _python_objects(root: pathlib.Path, ref: str) -> List[Tuple[str, str]]:
    result = run_rtk(root, ["git", "ls-tree", "-r", "-z", ref, "--", PACKAGE_PREFIX], timeout=20)
    objects: List[Tuple[str, str]] = []
    names = set()
    for row in result["stdout"].split("\0"):
        if not row:
            continue
        metadata, separator, name = row.partition("\t")
        fields = metadata.split()
        path = pathlib.PurePosixPath(name)
        if not separator or len(fields) != 3 or path.is_absolute() or ".." in path.parts:
            raise KnowledgeHubError("complexity baseline has invalid tree metadata")
        if not name.startswith(PACKAGE_PREFIX) or not name.endswith(".py"):
            continue
        if fields[1] != "blob" or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", fields[2]):
            raise KnowledgeHubError("complexity baseline Python object is not a valid blob")
        if name in names or len(objects) >= MAX_MEMBERS:
            raise KnowledgeHubError("complexity baseline has duplicate paths or exceeds member budget")
        names.add(name)
        objects.append((name, fields[2]))
    return objects


def _decode_blobs(data: bytes, objects: List[Tuple[str, str]]) -> Dict[str, str]:
    texts: Dict[str, str] = {}
    position = 0
    for name, object_id in objects:
        end = data.find(b"\n", position)
        if end < position or end - position > 256:
            raise KnowledgeHubError("complexity baseline batch header is incomplete")
        fields = data[position:end].split()
        if (len(fields) != 3 or fields[0] != object_id.encode("ascii")
                or fields[1] != b"blob" or not fields[2].isdigit()):
            raise KnowledgeHubError("complexity baseline batch object identity is invalid")
        size = int(fields[2])
        start = end + 1
        finish = start + size
        if size > MAX_CAPTURE_BYTES or finish >= len(data) or data[finish:finish + 1] != b"\n":
            raise KnowledgeHubError("complexity baseline blob is incomplete or exceeds byte budget")
        texts[name] = data[start:finish].decode("utf-8", errors="replace")
        position = finish + 1
    if position != len(data):
        raise KnowledgeHubError("complexity baseline batch contains trailing data")
    return texts


def baseline_python_texts(root: pathlib.Path, ref: str) -> Dict[str, str]:
    objects = _python_objects(root, ref)
    if not objects:
        return {}
    requests = b"".join(object_id.encode("ascii") + b"\n" for _, object_id in objects)
    result, overflow = run_bounded(
        ["rtk", "git", "cat-file", "--batch"], cwd=str(root), env=os.environ.copy(),
        timeout=20, output_limit=MAX_CAPTURE_BYTES, input_bytes=requests, raw_output=True,
    )
    if result.returncode != 0 or overflow:
        raise KnowledgeHubError("complexity baseline batch failed or exceeded capture budget")
    return _decode_blobs(result.stdout, objects)
