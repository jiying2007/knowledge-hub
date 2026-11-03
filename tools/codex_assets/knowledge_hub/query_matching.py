"""Compile a question once and memoize matches only inside one document score."""

from __future__ import annotations

import re
from typing import Callable, Dict, Optional, Sequence, Tuple

from .query_concepts import CJK
from .search_core import CJK_PATTERN, _cjk_ngrams, _term_variants

Match = Callable[[str, str], bool]


def _half_gram_matches(grams: Tuple[str, ...], text: str) -> bool:
    needed = (len(grams) + 1) // 2
    remaining = len(grams)
    for gram in grams:
        remaining -= 1
        if gram in text:
            needed -= 1
            if needed == 0:
                return True
        if needed > remaining:
            return False
    return False


class TermMatcher:
    """Prepare fuzzy term invariants once, retaining the existing match rules."""

    def __init__(self, terms: Sequence[str]) -> None:
        self.variants: Dict[str, Tuple[str, ...]] = {}
        self.short_grams: Dict[str, Tuple[Tuple[str, ...], ...]] = {}
        for term in dict.fromkeys(terms):
            self._prepare(term)

    def _prepare(self, term: str) -> None:
        variants = _term_variants(term)
        groups = []
        for variant in variants:
            cjk = ''.join(CJK_PATTERN.findall(variant))
            if len(cjk) >= 2:
                groups.append(tuple(sorted(value for value in _cjk_ngrams(cjk) if len(value) == 2)))
        self.variants[term] = variants
        self.short_grams[term] = tuple(groups)

    def __call__(self, term: str, text: str) -> bool:
        if term not in self.variants:
            self._prepare(term)
        variants = self.variants[term]
        if len(variants) == 1:
            if variants[0] in text:
                return True
            if not self.short_grams[term]:
                return False
        elif any(variant in text for variant in variants):
            return True
        return any(_half_gram_matches(grams, text) for grams in self.short_grams[term])


class ConceptMatcher:
    def __init__(self, terms: Sequence[str]) -> None:
        self.patterns: Dict[str, Tuple[Tuple[str, Optional[re.Pattern]], ...]] = {}
        for term in dict.fromkeys(terms):
            self.patterns[term] = tuple((variant, None if CJK.fullmatch(variant) else
                re.compile(r'(?<![a-z0-9])' + re.escape(variant) + r'(?![a-z0-9])'))
                for variant in _term_variants(term))

    def __call__(self, term: str, text: str) -> bool:
        return any(variant in text and (pattern is None or pattern.search(text) is not None)
                   for variant, pattern in self.patterns[term])


def document_matcher(base: Match) -> Match:
    cache: Dict[Tuple[str, str], bool] = {}
    def match(term: str, text: str) -> bool:
        key = (term, text)
        if key not in cache:
            cache[key] = base(term, text)
        return cache[key]
    return match
