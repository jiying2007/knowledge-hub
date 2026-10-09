"""Compile a question once and memoize matches only inside one document score."""

from __future__ import annotations

import re
from typing import Callable, Dict, Optional, Sequence, Tuple

from .query_concepts import CJK
from .search_core import _term_variants

Match = Callable[[str, str], bool]


class ConceptMatcher:
    def __init__(self, terms: Sequence[str]) -> None:
        self.patterns: Dict[str, Tuple[Tuple[str, Optional[re.Pattern]], ...]] = {}
        for term in dict.fromkeys(terms):
            self.patterns[term] = tuple((variant, None if CJK.fullmatch(variant) else
                re.compile(r'(?<![a-z0-9])' + re.escape(variant) + r'(?![a-z0-9])'))
                for variant in _term_variants(term))

    def __call__(self, term: str, text: str) -> bool:
        return any(variant in text if pattern is None else pattern.search(text) is not None
                   for variant, pattern in self.patterns[term])


def document_matcher(base: Match) -> Match:
    cache: Dict[Tuple[str, str], bool] = {}
    def match(term: str, text: str) -> bool:
        key = (term, text)
        if key not in cache:
            cache[key] = base(term, text)
        return cache[key]
    return match
