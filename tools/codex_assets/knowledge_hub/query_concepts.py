"""Bounded, corpus-derived concepts for questions; no answer IDs or project aliases."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
import re
import json
import pathlib
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple

from .common import KnowledgeHubError, read_repository_bytes_bounded
from .query_language import strip_grammar, normative_question, chinese_named_constraints, CHINESE_ENTITY_HEADS
from .query_projection import comparison_terms, shared_policy_context

TOKEN = re.compile(r'[a-z0-9_./:+-]+|[\u4e00-\u9fff]+', re.I)
CJK = re.compile(r'[\u4e00-\u9fff]+')
# Closed conversational syntax, not a domain vocabulary or a synonym table.
SCAFFOLD = re.compile('请帮我|请问|为什么|是不是|是否|怎样|怎么|如何|应该|现在|平时|哪些|多少|哪里|什么|'
                      '还没有|还没|还在|先做|要用|用来|能当|就能|放在|算不算|这算|该|吗|呢|的|和|与|而|'
                      '没有|还是')
EN_SCAFFOLD = frozenset(('how', 'what', 'why', 'where', 'can', 'could', 'should', 'would',
                         'is', 'are', 'does', 'do', 'the', 'a', 'an', 'to', 'for', 'of', 'and', 'or',
                         'it', 'please', 'i', 'we', 'you', 'me'))
POLARITY = re.compile(r'\b(?:not|never|without|exclude)\b|不|未|非|无|没有|禁止', re.I)
GOVERNANCE = re.compile(r'\b(?:owner|gate|reviewing|active|authorization|approval)\b|授权|生效|签收|审阅|生命周期', re.I)
COMPARATIVE = re.compile(r'通用|共享|跨项目|分别|区别|区分|比较|对比|分开|分离|\b(?:compare|comparison|versus|vs|shared|general|common|separate|distinguish|difference)\b', re.I)
FIELD_VALUES = frozenset(('active', 'reviewing', 'draft', 'archived', 'superseded', 'rejected',
                          'personal', 'current', 'projects', 'domains', 'decisions', 'validation'))
ANCHOR_CONTEXT = FIELD_VALUES | frozenset(('owner', 'gate', 'ai', 'head', 'repo', 'authorization', 'approval'))
ENTITY_HEADS = frozenset(('project', 'product', 'device', 'board', 'repository', 'entity'))
QUESTION_ACTIONS = frozenset(('configure', 'set', 'setup', 'explain', 'read', 'write', 'build', 'test',
                               'debug', 'compare', 'describe', 'find', 'list', 'show', 'check', 'prepare'))
MAX_ITEMS = 10000
MAX_METADATA_BYTES = 8 * 1024 * 1024
MAX_VOCABULARY = 200000
MAX_TERMS = 64


def project_routes(root: pathlib.Path) -> List[Mapping[str, Any]]:
    if not (root / 'registry/project-routes.json').exists():
        return []
    try:
        payload = json.loads(read_repository_bytes_bounded(root, 'registry/project-routes.json',
                             MAX_METADATA_BYTES, 'concept project routes'))
    except (ValueError, TypeError) as error:
        raise KnowledgeHubError('concept project routes are invalid') from error
    if not isinstance(payload, Mapping) or not isinstance(payload.get('routes'), list) or len(payload['routes']) > 1000:
        raise KnowledgeHubError('concept route budget or shape is invalid')
    return payload['routes']


@dataclass(frozen=True)
class ConceptQuery:
    terms: Tuple[str, ...]
    anchors: Tuple[str, ...] = ()
    unknown: Tuple[str, ...] = ()
    polarity: Tuple[str, ...] = ()
    governance: bool = False
    enabled: bool = False
    weights: Tuple[float, ...] = ()
    subject: str = ''
    project_anchors: Tuple[str, ...] = ()
    project_domains: Tuple[str, ...] = ()
    lexical_constraints: Tuple[str, ...] = ()
    shared_policy_context: bool = False
    shared_terms: Tuple[str, ...] = ()
    project_terms: Tuple[str, ...] = ()
    global_anchors: Tuple[str, ...] = ()
    enforce_constraints: bool = False
    excluded_project_anchors: Tuple[str, ...] = ()
    excluded_project_domains: Tuple[str, ...] = ()


def clean_segments(value: str, vocabulary: Optional[Mapping[str, int]] = None) -> List[str]:
    # Removing a classifier preserves the ordinal, rather than inventing an alias.
    protected: Dict[str, str] = {}
    if vocabulary:
        encoded, offset = [], 0
        maximum = min(256, len(value))
        while offset < len(value):
            word = next((value[offset:offset + width] for width in range(min(maximum, len(value) - offset), 1, -1)
                         if value[offset:offset + width] in vocabulary
                         and (vocabulary[value[offset:offset + width]] == 0
                              or any(char in value[offset:offset + width] for char in '该吗呢就能要已在了的和与而成把过里时'))), '')
            if word:
                marker = '\x00' + str(len(protected)) + '\x00'
                protected[marker] = word
                encoded.append(' ' + marker + ' ')
                offset += len(word)
            else:
                encoded.append(value[offset])
                offset += 1
        value = ''.join(encoded)
    value = re.sub(r'(第[一二三四五六七八九十百\d]+)(?:款|个|代|种)', r'\1', value)
    value = strip_grammar(value)
    # Negation is retained separately; lexical compounds such as 无线 and
    # 非易失性 are never stripped by a single-character stopword rule.
    value = re.sub(r'不(?=是|会|可|允许|暴露|代表|需要|替代|进入|提供|授权|写|修改|开放|使用)', ' ', value)
    return [protected.get(part, part) for part in SCAFFOLD.sub(' ', value).split() if part]


def corpus_lexicon(items: Iterable[Mapping[str, Any]]) -> Tuple[Dict[str, int], int]:
    frequencies: Counter = Counter()
    total_bytes, count = 0, 0
    for item in items:
        count += 1
        if count > MAX_ITEMS:
            raise KnowledgeHubError('concept corpus exceeds item budget')
        if not isinstance(item, Mapping):
            raise KnowledgeHubError('concept metadata item must be an object')
        title, summary, tags = item.get('title', ''), item.get('summary_zh', ''), item.get('tags', [])
        if (not isinstance(title, str) or not isinstance(summary, str) or max(len(title), len(summary)) > 8192
                or not isinstance(tags, list) or len(tags) > 32
                or any(not isinstance(tag, str) or len(tag) > 4096 for tag in tags)):
            raise KnowledgeHubError('concept metadata fields exceed typed budget')
        text = '\n'.join((title, summary, ' '.join(tags)))
        total_bytes += len(text.encode('utf-8'))
        if total_bytes > MAX_METADATA_BYTES:
            raise KnowledgeHubError('concept corpus exceeds metadata budget')
        vocabulary: Set[str] = set()
        vocabulary.update(token.lower() for token in TOKEN.findall(text)
                          if not CJK.fullmatch(token) and len(token) <= 256)
        # Topic nouns in curated titles/tags may contain function characters:
        # stripping 能 from 性能/智能, or 要 from 摘要, destroys their identity.
        for sentence in CJK.findall(title + '\n' + ' '.join(tags)):
            for part in clean_segments(sentence):
                for width in range(2, min(6, len(part)) + 1):
                    vocabulary.update(part[offset:offset + width] for offset in range(len(part) - width + 1))
        for sentence in CJK.findall(text):
            for part in clean_segments(sentence):
                for width in range(2, min(6, len(part)) + 1):
                    vocabulary.update(part[offset:offset + width] for offset in range(len(part) - width + 1))
        frequencies.update(vocabulary)
        if len(frequencies) > MAX_VOCABULARY:
            raise KnowledgeHubError('concept corpus exceeds vocabulary budget')
    return dict(frequencies), count


def _route_alias_domains(routes: Iterable[Mapping[str, Any]]) -> Dict[str, Set[str]]:
    """Validate declared route aliases and retain their explicit family domains."""
    route_rows = list(routes)
    if len(route_rows) > 1000:
        raise KnowledgeHubError('concept route budget exceeded')
    groups: Dict[str, Set[str]] = {}
    aliases: Dict[str, Set[str]] = {}
    for route in route_rows:
        if not isinstance(route, Mapping):
            raise KnowledgeHubError('concept route must be an object')
        domain_refs, route_aliases = route.get('domain_refs', []), route.get('aliases', [])
        if (not isinstance(domain_refs, list) or not isinstance(route_aliases, list)
                or len(domain_refs) > 32 or len(route_aliases) > 64
                or any(not isinstance(value, str) or len(value) > 256 for value in domain_refs + route_aliases)):
            raise KnowledgeHubError('concept route fields exceed typed budget')
        groups.setdefault(str(route.get('group_id', '')), set()).update(domain_refs)
        for alias in route_aliases:
            aliases.setdefault(alias.lower(), set()).update(domain_refs)
    for group, domains in groups.items():
        if group.lower() in aliases:
            aliases[group.lower()].update(domains)
    return aliases


def _named_subject_terms(tokens: List[str], vocabulary: Mapping[str, int], query: str = '', aliases=()) -> List[str]:
    """Keep a leading/unambiguously named unknown entity, not every English modifier."""
    result = _comparison_subject_terms(tokens, vocabulary, query, aliases)
    topic_markers = frozenset(('shared', 'general', 'common', 'team', 'normative'))
    prefix = EN_SCAFFOLD | ANCHOR_CONTEXT | ENTITY_HEADS | QUESTION_ACTIONS | topic_markers | frozenset(('not', 'never', 'without', 'exclude'))
    leading = next((index for index, token in enumerate(tokens)
                    if (bool(clean_segments(token, vocabulary)) if CJK.fullmatch(token)
                        else token.lower() not in prefix)), -1)
    for index, token in enumerate(tokens):
        term = token.lower()
        explicit = index > 0 and tokens[index - 1].lower() in ENTITY_HEADS
        if (CJK.fullmatch(token) or term in EN_SCAFFOLD or term in ANCHOR_CONTEXT
                or term in ENTITY_HEADS or term in ('not', 'never', 'without', 'exclude')
                or (term in topic_markers and not explicit)
                or (vocabulary.get(term, 0) and not explicit)):
            continue
        if explicit or (index == leading and term not in QUESTION_ACTIONS):
            result.append(term)
    return result


def _comparison_subject_terms(tokens: List[str], vocabulary: Mapping[str, int], query: str, aliases) -> List[str]:
    """Treat explicit comparison operands as subjects, including after syntax words."""
    operators = frozenset(('versus', 'vs', 'against', 'compare', 'compared', 'comparison', 'between'))
    syntax = EN_SCAFFOLD | ENTITY_HEADS | ANCHOR_CONTEXT | QUESTION_ACTIONS | operators | frozenset(
        ('with', 'shared', 'general', 'common'))
    lowered = [token.lower() for token in tokens]
    positions = list(TOKEN.finditer(query))
    topic_markers = frozenset(('shared', 'general', 'common', 'team', 'normative'))
    syntax |= topic_markers
    result, comparison_context, entity_context = [], False, False
    for index, term in enumerate(lowered):
        if index and len(positions) == len(tokens) and re.search(
                r'[;；!?！？。]', query[positions[index - 1].end():positions[index].start()]):
            comparison_context = False
            entity_context = False
        begins_comparison = term in operators or bool(CJK.fullmatch(term) and re.search('比较|对比', term))
        comparison_context = comparison_context or begins_comparison
        comma_after = (comparison_context and index + 1 < len(positions)
                       and bool(re.fullmatch(r'\s*[,，]\s*', query[positions[index].end():positions[index + 1].start()])))
        operator = (begins_comparison
                    or (comparison_context and term in ('with', 'to', 'and', 'or'))
                    or (comparison_context and CJK.fullmatch(term)
                        and (term.endswith(('与', '和')) or re.search('比较|对比', term)))
                    or comma_after)
        if not operator:
            continue
        previous = lowered[index - 1] if index else ''
        entity_context = entity_context or previous in aliases
        named_operand, topic_operand = False, False
        for candidate in lowered[index + 1:]:
            named_operand = named_operand or candidate in ENTITY_HEADS
            topic_operand = topic_operand or candidate in topic_markers
            if candidate in syntax:
                continue
            if CJK.fullmatch(candidate):
                if not clean_segments(candidate, vocabulary):
                    continue
                break
            if candidate in aliases:
                entity_context = True
                if (previous and previous not in syntax and not CJK.fullmatch(previous)
                        and not any(term in topic_markers for term in lowered[max(0, index - 3):index])):
                    result.append(previous)
            if named_operand or (entity_context and not topic_operand):
                result.append(candidate)
            break
    return result


def extract_concepts(query: str, vocabulary: Mapping[str, int], document_count: int,
                     routes: Iterable[Mapping[str, Any]] = (), role_vocabulary=None) -> ConceptQuery:
    if not isinstance(query, str) or len(query) > 4096:
        raise KnowledgeHubError('concept query exceeds 4096-character budget')
    routes = list(routes)
    aliases = _route_alias_domains(routes)
    from .query_boundaries import boundaries, without_excluded
    limits = boundaries(query, aliases)
    parsed_query = limits.normalized
    vocabulary = dict(vocabulary)
    vocabulary.update((alias, 0) for alias in aliases if alias not in vocabulary)
    if len(vocabulary) > MAX_VOCABULARY:
        raise KnowledgeHubError('concept query vocabulary exceeds budget')
    tokens = TOKEN.findall(parsed_query)
    natural = bool(re.search(r'[？?]|为什么|怎么|怎样|如何|是否|是不是|\b(?:how|what|why|can|should)\b', query, re.I)
                   or any(len(token) >= 8 and CJK.fullmatch(token) for token in tokens))
    if not natural:
        positive = tuple(name for name in limits.names if name in aliases)
        domains = tuple(sorted({domain for name in positive for domain in aliases[name]}))
        if len(domains) > 64:
            raise KnowledgeHubError('concept project domain budget exceeded')
        return ConceptQuery(without_excluded(tuple(token.lower() for token in tokens), limits.excluded_aliases),
            anchors=limits.names, project_anchors=positive, project_domains=domains,
            global_anchors=tuple(name for name in limits.names if name not in positive),
            enforce_constraints=bool(limits.names or limits.excluded_aliases),
            excluded_project_anchors=limits.excluded_aliases, excluded_project_domains=limits.excluded_domains)
    terms, anchors, unknown = [], [], []
    for token in tokens:
        if not CJK.fullmatch(token):
            term = token.lower()
            if term in EN_SCAFFOLD or term in ('not', 'never', 'without', 'exclude'):
                continue
            terms.append(term)
            if term not in ANCHOR_CONTEXT and (re.search(r'[\d_/:+.-]', term)
                    or (token.isupper() and len(token) >= 3)):
                anchors.append(term)
            continue
        for part in clean_segments(token, vocabulary):
            offset, unmatched = 0, ''
            while offset < len(part):
                word = next((part[offset:offset + width] for width in range(min(6, len(part) - offset), 1, -1)
                             if part[offset:offset + width] in vocabulary), '')
                if word:
                    if len(unmatched) >= 2:
                        terms.append(unmatched)
                        unknown.append(unmatched)
                    unmatched = ''
                    terms.append(word)
                    offset += len(word)
                else:
                    unmatched += part[offset]
                    offset += 1
            if len(unmatched) >= 2:
                terms.append(unmatched)
                unknown.append(unmatched)
    terms = list(dict.fromkeys(terms))
    if len(terms) > MAX_TERMS:
        raise KnowledgeHubError('concept query exceeds 64-term budget')
    if not terms:
        return ConceptQuery((), enabled=True, polarity=tuple(match.group().lower() for match in POLARITY.finditer(query)))
    return _finish_concepts(query, tokens, terms, anchors, unknown, vocabulary, document_count, routes, role_vocabulary, limits)


def _finish_concepts(query, tokens, terms, anchors, unknown, vocabulary, document_count, routes, role_vocabulary, limits):
    from .query_topic_roles import branch_topics
    aliases = _route_alias_domains(routes)
    parsed_query = limits.normalized
    explicit_entities = _named_subject_terms(tokens, vocabulary, parsed_query, aliases) + list(limits.names)
    terms = [term for term in terms if term not in limits.excluded_aliases and term not in limits.descriptors]
    anchors = [term for term in anchors if term not in limits.excluded_aliases]
    explicit_entities = [term for term in explicit_entities if term not in limits.excluded_aliases]
    anchors.extend(term for term in explicit_entities if term not in anchors)
    leading = next((part for token in tokens if CJK.fullmatch(token)
                    for part in clean_segments(token, vocabulary) if len(part) >= 2), '')
    project_anchors: List[str] = []
    project_domains: Set[str] = set()
    for anchor in terms:
        if anchor in aliases:
            if anchor not in anchors:
                anchors.append(anchor)
            project_anchors.append(anchor)
            project_domains.update(aliases[anchor])
    if len(project_domains) > 64:
        raise KnowledgeHubError('concept project domain budget exceeded')
    governance = bool(GOVERNANCE.search(query) or normative_question(query)) and not project_domains and not explicit_entities
    subject = (unknown[0] if unknown and unknown[0] not in project_anchors
               and unknown[0] not in CHINESE_ENTITY_HEADS and leading.startswith(unknown[0])
               and unknown[0] not in limits.descriptors
               and (not anchors or len(unknown[0]) >= 3) else '')
    weights = tuple(1 + math.log(1 + document_count / (1 + vocabulary.get(term, 0))) for term in terms)
    shared_terms, project_terms = comparison_terms(parsed_query, terms, project_anchors)
    named_chinese = chinese_named_constraints(parsed_query, unknown, project_anchors)
    anchors.extend(term for term in named_chinese if term not in anchors)
    local_topics = branch_topics(anchors, explicit_entities + list(named_chinese), project_domains,
                                role_vocabulary or {}, shared_terms) if shared_terms and project_terms else ()
    return ConceptQuery(tuple(terms), tuple(dict.fromkeys(anchors)), tuple(dict.fromkeys(unknown)),
                        tuple(match.group().lower() for match in POLARITY.finditer(query)),
                        governance, True, weights, subject,
                        tuple(dict.fromkeys(project_anchors)), tuple(sorted(project_domains)),
                        tuple(term for term in terms if CJK.fullmatch(term) and term.startswith(('无', '非'))),
                        bool(project_domains and shared_policy_context(query, shared_terms, project_terms)), shared_terms, project_terms,
                        tuple(term for term in anchors if term not in project_anchors and term not in local_topics),
                        bool(limits.names or limits.excluded_aliases), limits.excluded_aliases, limits.excluded_domains)


def exact_concept_match(term: str, text: str, *, normalized: bool = False) -> bool:
    if not normalized:
        text = text.lower()
    if CJK.fullmatch(term):
        return term in text
    return re.search(r'(?<![a-z0-9])' + re.escape(term) + r'(?![a-z0-9])', text) is not None
