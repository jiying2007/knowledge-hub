"""Bounded duplicate hints never merge content or authorize lifecycle changes."""

from __future__ import annotations
from typing import Any, Dict, List
import hashlib
import unicodedata
import re
from .common import load_markdown, resolve_inside, KnowledgeHubError

from .search_core import search_tokens


def content_fingerprint(text):
    return hashlib.sha256(re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', text)).strip().encode()).hexdigest()


def duplicate_inventory(root, items):
    result = []
    for item in items[:5000]:
        row = dict(item)
        if row.get('status') in {'active', 'reviewing', 'draft'} and row.get('path'):
            try:
                _, body = load_markdown(resolve_inside(root, row['path']))
                row['content_fingerprint'] = content_fingerprint(body)
            except (OSError, KnowledgeHubError, ValueError):
                pass
        result.append(row)
    return result


def duplicate_hints(rows, title, summary, domain, maximum=3, *, exclude_id="", body="", scope="", version=""):
    if type(maximum) is not int or not 1 <= maximum <= 50:
        raise ValueError("duplicate hint limit must be 1-50")
    query = set(search_tokens(title + ' ' + summary, maximum=256))
    hints: List[Dict[str, Any]] = []
    if not query:
        return hints
    for row in rows[:5000]:
        if row.get('id') == exclude_id:
            continue
        if row.get('domain') != domain or row.get('status') not in {'active', 'reviewing', 'draft'}:
            continue
        tokens = set(search_tokens(str(row.get('title', '')) + ' ' + str(row.get('summary_zh', '')), maximum=256))
        similarity = len(query & tokens) / max(1, len(query | tokens))
        same_title = str(row.get('title', '')).strip().casefold() == title.strip().casefold()
        same_body = bool(body and row.get('content_fingerprint') == content_fingerprint(body)
                         and row.get('scope', '') == scope and row.get('version', '') == version)
        if same_body or same_title or similarity >= .8:
            hints.append({'item_id':row['id'], 'status':row['status'],
                          'similarity':round(similarity, 4), 'reason':'same-content-scope-version' if same_body else 'same-title' if same_title else 'metadata-overlap',
                          'recommended_action':'review-existing-or-supersede', 'automatic_merge':False})
    return sorted(hints, key=lambda row:(-row['similarity'], row['item_id']))[:maximum]
