"""Opt-in question normalization for shadow evaluation; negation stays exact."""

from __future__ import annotations

import re


def normalize_question(query):
    if len(query) > 4096 or re.search(r'\b(?:not|never|without|exclude)\b|[不未非无]|禁止', query, re.I):
        return query
    value = re.sub(r'^(?:如何在|如何|怎样|怎么)\s*', '', query.strip())
    # Only complete interrogative boundaries are removable. Nouns, conjunctions
    # and technical identifiers inside the phrase remain byte-for-byte intact.
    value = re.sub(r'^(?:请问|请帮我)\s*', '', value)
    value = re.sub(r'(?:在哪里|应该如何处理|有什么建议)$', '', value.rstrip('？?'))
    return ' '.join(value.rstrip('？?').split()) or query
