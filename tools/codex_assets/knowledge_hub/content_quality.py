"""Content quality checks shared by intake, maintenance and repository gates."""
from __future__ import annotations

import datetime as dt
import hashlib
from .common import (
    DEFAULT_MARKDOWN_MAX_BYTES, KnowledgeHubError, load_markdown,
    read_utf8_bounded, split_frontmatter,
)


class ValidatedBodyBatch:
    """Reuse only validated bodies; every access still reads bounded fresh text.

    The byte budget charges full source UTF-8 bytes (at least the retained body
    size); the entry budget also bounds path/digest bookkeeping. No metadata is
    retained, and exhausted budgets transparently use the original parser.
    """

    def __init__(self, max_bytes=8 * 1024 * 1024, max_entries=2048):
        self._max_bytes = max_bytes
        self._max_entries = max_entries
        self._bytes = 0
        self._bodies = {}

    def _read(self, path):
        try:
            return read_utf8_bounded(path, DEFAULT_MARKDOWN_MAX_BYTES, 'Markdown file')
        except OSError as exc:
            raise KnowledgeHubError('unable to read Markdown {}: {}'.format(path, exc)) from exc

    def _remember(self, path, raw, body):
        previous = self._bodies.pop(path, None)
        if previous is not None:
            self._bytes -= previous[2]
        size = len(raw)
        if len(self._bodies) < self._max_entries and self._bytes + size <= self._max_bytes:
            self._bodies[path] = (hashlib.sha256(raw).digest(), body, size)
            self._bytes += size

    def load(self, path, *, retain_body=True):
        text = self._read(path)
        metadata, body = split_frontmatter(text)
        if retain_body:
            self._remember(path, text.encode('utf-8'), body)
        return metadata, body

    def body(self, path):
        text = self._read(path)
        raw = text.encode('utf-8')
        previous = self._bodies.get(path)
        if previous is not None and previous[0] == hashlib.sha256(raw).digest():
            return previous[1]
        _, body = split_frontmatter(text)
        self._remember(path, raw, body)
        return body


def template_body(root, body):
    """An exact unfilled template is not an engineering record."""
    return _template_body(root, body, {})


def _template_body(root, body, template_bodies):
    normalized = body.strip()
    for path in (root / 'templates').glob('*.md'):
        if path.name == 'README.md':
            continue
        if path not in template_bodies:
            template_bodies[path] = load_markdown(path)[1].strip()
        if normalized == template_bodies[path]:
            return True
    return False


def overdue(item, today=None):
    today = today or dt.date.today()
    value = item.get('review_after')
    if not value or item.get('status') in {'archived', 'superseded', 'rejected'}:
        return False
    try:
        return dt.date.fromisoformat(str(value)) < today
    except ValueError:
        return True  # Invalid temporal evidence never grants current authority.


def findings(root, items, *, body_reader=None):
    result = []
    template_bodies = {}
    for item in items:
        path = root / item.get('path', '')
        if not str(item.get('path', '')).startswith('projects/') or not path.is_file() or path.suffix != '.md':
            continue
        body = body_reader(path) if body_reader is not None else load_markdown(path)[1]
        if _template_body(root, body, template_bodies) and item.get('searchable') is not False:
            result.append('template-body:' + item['path'])
        if '/current/' in item['path'] and item.get('status') in {'archived', 'superseded', 'rejected'}:
            result.append('terminal-in-current:' + item['path'])
    return result
