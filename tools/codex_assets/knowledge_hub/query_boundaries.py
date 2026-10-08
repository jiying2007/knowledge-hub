"""Always-on explicit subject and signed alias boundaries, not a filter DSL."""

import re
from dataclasses import dataclass
from .common import KnowledgeHubError
from .query_language import subject_at, explicit_subjects

NAME = r'[a-z0-9_][a-z0-9_./:+-]{0,255}'
INLINE = re.compile(r'\bproject\s*:\s*(' + NAME + ')', re.I)
NEGATION = re.compile(r'排除|不包括|不要|\b(?:exclude|excluding|except|without)\b', re.I)
CONNECTOR = re.compile(r'\s*(?:(?:和|与|或|以及|、|,)|\b(?:and|or)\b)\s*', re.I)


@dataclass(frozen=True)
class QueryBoundaries:
    names: tuple = ()
    excluded_aliases: tuple = ()
    excluded_domains: tuple = ()
    normalized: str = ''
    descriptors: tuple = ()


def boundaries(query, aliases):
    negative, spans = [], []
    ordered_aliases = sorted(aliases, key=len, reverse=True)
    for marker in NEGATION.finditer(query):
        position, end = marker.end(), marker.end()
        while position < len(query):
            value = subject_at(query, position, ordered_aliases)
            if value is None or value.name not in aliases:
                break
            negative.append(value.name)
            end = value.end
            connector = CONNECTOR.match(query, end)
            if not connector:
                break
            position = connector.end()
        if end > marker.end():
            spans.append((marker.start(), end))
    visible = ''.join(' ' if any(start <= index < end for start, end in spans) else char
                      for index, char in enumerate(query))
    named = explicit_subjects(visible, ordered_aliases)
    selected_names = tuple(dict.fromkeys(value.name for value in named))
    excluded = tuple(dict.fromkeys(negative))
    domains = tuple(sorted({domain for name in excluded for domain in aliases[name]}))
    if max(len(selected_names), len(excluded), len(domains)) > 64:
        raise KnowledgeHubError('query subject boundaries exceed budget')
    normalized = INLINE.sub(lambda match:match.group(1).rstrip('.'), visible)
    descriptors = tuple(dict.fromkeys(value.descriptor for value in named if value.descriptor))
    return QueryBoundaries(selected_names, excluded, domains, normalized, descriptors)


def without_excluded(terms, excluded):
    return tuple(term for term in terms if term not in excluded)
