"""Curated project-topic association is separate from alias/entity registration."""

from collections import defaultdict
from .query_concepts import TOKEN, CJK
from .search_core import _item_is_default_searchable, _domain_matches


def scoped_topics(items):
    result = defaultdict(set)
    for item in items:
        if (not _item_is_default_searchable(item) or item.get('status') not in ('active', 'reviewing')):
            continue
        domain = item.get('domain', '')
        if item.get('scope') == 'team-general':
            if item.get('status') != 'active' or item.get('kind') not in ('standard', 'architecture', 'runbook'):
                continue
            domain = 'team-general'
        elif item.get('scope') != 'project-specific':
            continue
        text = '\n'.join((item.get('title', ''), item.get('summary_zh', ''), ' '.join(item.get('tags', []))))
        for token in TOKEN.findall(text):
            if not CJK.fullmatch(token):
                result[token.lower()].add(domain)
    return dict(result)


def branch_topics(anchors, explicit_entities, domains, role_vocabulary, shared_terms):
    return tuple(term for term in anchors if term not in explicit_entities
                 and ((term in shared_terms and 'team-general' in role_vocabulary.get(term, ()))
                      or any(_domain_matches(domain, project) for domain in role_vocabulary.get(term, ())
                             for project in domains)))
