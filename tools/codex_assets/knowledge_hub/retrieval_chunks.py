"""Lossless, bounded source spans for derived retrieval chunks."""

from __future__ import annotations

import hashlib
import io
import pathlib
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .common import KnowledgeHubError, read_repository_bytes_bounded
from .retrieval_cache import DerivedCache, fingerprint

MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_CHUNKS_PER_ITEM = 128
MAX_CHUNK_CHARS = 4000
MAX_HEADING_CHARS = 160
CHUNKER_REVISION = "lossless-spans-v3"
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def _chunk_record(
    item_id: str, headings: Sequence[str], text: str,
    line_start: int, line_end: int, char_start: int,
) -> Dict[str, Any]:
    if not text or len(text) > MAX_CHUNK_CHARS:
        raise KnowledgeHubError("chunk text must be non-empty and bounded")
    identity = "{}\0{}\0{}\0{}".format(item_id, "/".join(headings), char_start, text)
    return {
        "chunk_id": "{}:{}".format(item_id, hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]),
        "item_id": item_id, "heading_path": list(headings),
        "line_start": line_start, "line_end": line_end,
        "source_char_start": char_start, "source_char_end": char_start + len(text),
        "text": text, "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


class _ChunkBuilder:
    def __init__(self, item_id: str) -> None:
        self.item_id = item_id
        self.chunks: List[Dict[str, Any]] = []
        self.headings: List[Tuple[int, str]] = []
        self.pieces: List[str] = []
        self.size = self.position = self.char_start = 0
        self.line_start = self.line_end = 1

    def flush(self) -> bool:
        if self.pieces:
            self.chunks.append(_chunk_record(
                self.item_id, [text for _, text in self.headings] or ["document"],
                "".join(self.pieces), self.line_start, self.line_end, self.char_start,
            ))
            self.pieces = []
            self.size = 0
        return len(self.chunks) < MAX_CHUNKS_PER_ITEM

    def append_line(self, line: str, line_number: int) -> bool:
        consumed = 0
        while consumed < len(line):
            if len(self.chunks) >= MAX_CHUNKS_PER_ITEM:
                return False
            if not self.pieces:
                self.line_start, self.char_start = line_number, self.position
            piece = line[consumed:consumed + MAX_CHUNK_CHARS - self.size]
            self.pieces.append(piece)
            self.size += len(piece)
            self.position += len(piece)
            consumed += len(piece)
            self.line_end = line_number
            if self.size == MAX_CHUNK_CHARS:
                self.flush()
        return True


def _split_body(item_id: str, body: str) -> List[Dict[str, Any]]:
    builder = _ChunkBuilder(item_id)
    fence: Tuple[str, int] = ("", 0)
    for line_number, line in enumerate(io.StringIO(body, newline=""), 1):
        heading = HEADING_RE.match(line.rstrip("\r\n")) if not fence[0] else None
        if heading:
            if not builder.flush():
                break
            level = len(heading.group(1))
            builder.headings = [row for row in builder.headings if row[0] < level]
            # This is a bounded display label, not the source span. The full
            # heading remains in body text and is split without loss below.
            builder.headings.append((level, heading.group(2).strip()[:MAX_HEADING_CHARS]))
        marker = FENCE_RE.match(line.rstrip("\r\n"))
        if marker:
            delimiter, tail = marker.groups()
            if not fence[0]:
                fence = (delimiter[0], len(delimiter))
            elif delimiter[0] == fence[0] and len(delimiter) >= fence[1] and not tail.strip():
                fence = ("", 0)
        if not builder.append_line(line, line_number):
            break
    builder.flush()
    source_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    complete = builder.position == len(body)
    for chunk in builder.chunks:
        chunk.update({
            "source_content_sha256": source_hash, "source_char_count": len(body),
            "coverage_complete": complete,
            "next_char_offset": None if complete else builder.position,
            "chunker_revision": CHUNKER_REVISION,
        })
    return builder.chunks


def _line_number(body: str, position: int) -> int:
    prefix = body[:position]
    count = prefix.count("\n") + prefix.count("\r") - prefix.count("\r\n")
    if position and body[position:position + 1] == "\n" and body[position - 1] == "\r":
        count -= 1
    return count + 1


def _valid_chunks(value: Any, body: str, item_id: str, source_hash: str) -> bool:
    if not isinstance(value, list) or len(value) > MAX_CHUNKS_PER_ITEM:
        return False
    end = 0
    for row in value:
        if not isinstance(row, dict):
            return False
        start, stop = row.get("source_char_start"), row.get("source_char_end")
        if type(start) is not int or type(stop) is not int or start != end:
            return False
        if not start < stop <= len(body) or stop - start > MAX_CHUNK_CHARS:
            return False
        text = body[start:stop]
        headings = row.get("heading_path")
        if not isinstance(headings, list) or not 1 <= len(headings) <= 6:
            return False
        if any(not isinstance(h, str) or len(h) > MAX_HEADING_CHARS for h in headings):
            return False
        first, last = row.get("line_start"), row.get("line_end")
        if type(first) is not int or type(last) is not int or not 1 <= first <= last:
            return False
        if first != _line_number(body, start) or last != _line_number(body, stop - 1):
            return False
        if row.get("text") != text or row.get("item_id") != item_id:
            return False
        expected = _chunk_record(item_id, headings, text, first, last, start)
        if any(row.get(key) != val for key, val in expected.items()):
            return False
        if row.get("source_content_sha256") != source_hash or row.get("source_char_count") != len(body):
            return False
        if row.get("chunker_revision") != CHUNKER_REVISION:
            return False
        end = stop
    complete = end == len(body)
    if not complete and len(value) != MAX_CHUNKS_PER_ITEM:
        return False
    return all(
        row.get("coverage_complete") is complete
        and row.get("next_char_offset") == (None if complete else end)
        for row in value
    )


def hierarchical_chunks(
    root: pathlib.Path, item: Mapping[str, Any], *, cache: Optional[DerivedCache] = None,
) -> List[Dict[str, Any]]:
    relative = str(item.get("path", ""))
    source_kind = "body"
    if relative:
        raw = read_repository_bytes_bounded(root, relative, MAX_FILE_BYTES, "retrieval body")
        try:
            body = raw.decode("utf-8")
        except UnicodeError as exc:
            raise KnowledgeHubError("retrieval body must be UTF-8") from exc
    else:
        source_kind = "registry-metadata"
        body = " ".join([
            str(item.get("title", "")), str(item.get("summary_zh", "")),
            " ".join(map(str, item.get("tags", []))),
        ]).strip()
        if len(body.encode("utf-8")) > MAX_FILE_BYTES:
            raise KnowledgeHubError("retrieval metadata exceeds byte budget")
    item_id = str(item.get("id", ""))
    source_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if cache is None:
        chunks = _split_body(item_id, body)
    else:
        revision = fingerprint([source_hash, CHUNKER_REVISION, MAX_CHUNKS_PER_ITEM, MAX_CHUNK_CHARS, MAX_HEADING_CHARS])
        chunks = cache.resolve(
            "chunks", fingerprint([item_id, relative, source_kind]), revision,
            lambda: _split_body(item_id, body),
            lambda value: _valid_chunks(value, body, item_id, source_hash),
        )
    for chunk in chunks:
        chunk["source_kind"] = source_kind
        chunk["source_path"] = relative
    return chunks
