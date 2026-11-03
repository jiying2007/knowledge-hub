"""Query-level fuzzy preparation preserves every existing matching decision."""

import copy
import itertools
import random

import pytest

from tools.codex_assets.knowledge_hub import query_matching, search_query
from tools.codex_assets.knowledge_hub.query_matching import TermMatcher
from tools.codex_assets.knowledge_hub.search_query_support import _matched_query_terms, _score, _term_matches, _topic_body
from tools.codex_assets.knowledge_hub.search_core import _metadata_haystack
from tools.codex_assets.knowledge_hub.query_concepts import FIELD_VALUES
from tools.codex_assets.knowledge_hub.search_index import SearchIndex
from test_search import _search_root


def test_prepared_fuzzy_matches_original_for_synonyms_ngrams_and_unicode():
    terms = ['', 'a', 'agent', 'AGENT', '双向链接', '反向链接', '知识图谱', '发布',
             '存储泄漏定位', '内存泄漏', '源码quick', '性能', '路径/SDK:+', '𠀀设备']
    randomizer = random.Random(2107)
    texts = ['', 'backlinks graph release performance', 'agent agents AGENT', '内存',
             '源码 quick gate', '存储泄漏定位', '路径/sdk:+', '𠀀设备']
    texts += [''.join(randomizer.choices('内存泄漏定位源码双向链接 abc/+:', k=24))
              for _ in range(100)]
    prepared = TermMatcher(terms)
    for term in terms:
        for text in texts:
            assert prepared(term, text) == _term_matches(term, text)


def test_early_gram_threshold_matches_every_subset_on_both_sides_of_half():
    for length in range(2, 9):
        term = '中文可读性规范路径'[:length]
        prepared = TermMatcher([term])
        grams = prepared.short_grams[term][0]
        for flags in itertools.product((False, True), repeat=len(grams)):
            text = ' / '.join(gram for gram, present in zip(grams, flags) if present)
            assert prepared(term, text) == _term_matches(term, text)


def test_query_invariants_are_prepared_once_and_lazy_terms_remain_equivalent(monkeypatch):
    original = query_matching._term_variants
    calls = []

    def counted(term):
        calls.append(term)
        return original(term)

    monkeypatch.setattr(query_matching, '_term_variants', counted)
    prepared = TermMatcher(['agent', '性能', 'agent'])
    for _ in range(3):
        for term in ('agent', '性能', 'new-term'):
            for text in ('agent performance', 'missing', 'new-term'):
                assert prepared(term, text) == _term_matches(term, text)
    assert calls == ['agent', '性能', 'new-term']


@pytest.mark.parametrize('body', ['---\ntitle: Hidden CPU\n---\n\nΟΣ Γράφος CPU 内存',
                                  '---\r\ntitle: Hidden\r\n---\r\nΣΥΣΤΗΜΑ memory',
                                  'Plain body performance Σ\u0301'])
@pytest.mark.parametrize('terms', [['cpu', '性能'], ['agent', 'σ'], ['内存', 'missing'],
                                  ['active', 'reviewing'], []])
def test_prepared_body_matching_preserves_original_complete_result(body, terms):
    item = {'title': 'ΟΣ CPU', 'summary_zh': '内存性能', 'tags': ['ΓΡΑΦΟΣ', 'memory']}
    topical_body = _topic_body(body)
    combined = _metadata_haystack(item) + '\n' + topical_body.lower()
    topical = '\n'.join((item['title'], item['summary_zh'], ' '.join(item['tags']), topical_body)).lower()
    expected = [term for term in terms if _term_matches(term, topical if term in FIELD_VALUES else combined)]
    assert _matched_query_terms(terms, body, item) == expected
    assert _matched_query_terms(terms, topical_body, item, body_haystack=topical_body.lower()) == expected


@pytest.mark.parametrize('field', ['id', 'path', 'source', 'title', 'summary_zh', 'tags', 'body'])
def test_field_values_only_match_topical_evidence(field):
    item = {'id': 'fixture', 'path': 'fixture.md', 'title': 'Example',
            'summary_zh': '工程说明', 'tags': [], 'source': {'source_id': 'fixture'}}
    body = 'Technical evidence'
    if field == 'body':
        body = 'active reviewing'
    elif field == 'tags':
        item[field] = ['active', 'reviewing']
    elif field == 'source':
        item[field] = {'source_id': 'active-reviewing'}
    else:
        item[field] = 'active reviewing'
    expected = ['active', 'reviewing'] if field in {'title', 'summary_zh', 'tags', 'body'} else []
    assert _matched_query_terms(['active', 'reviewing'], body, item) == expected
    assert _matched_query_terms(['active', 'reviewing'], body, item, body_haystack=body.lower()) == expected


def test_malformed_tag_error_is_not_hidden_when_topical_body_is_unused():
    for terms in (['active'], ['agent'], []):
        with pytest.raises(TypeError):
            _matched_query_terms(terms, 'body', {'tags': None})


@pytest.mark.parametrize('tags', [None, 42, False])
def test_score_preparation_retains_malformed_tag_error_before_early_rejection(tags):
    with pytest.raises(TypeError):
        _score('example.md', '.md', 'Unrelated evidence', {'tags': tags},
               'Example', ['agent', 'runtime', 'contract'], 'agent runtime contract')


def normalized(payload):
    result = copy.deepcopy(payload)
    result.pop('latency_ms')
    result.pop('timing')
    result['index'] = {key: value for key, value in result['index'].items()
                       if not key.endswith('_ms')}
    return result


@pytest.mark.parametrize('query', ['Obsidian 双向链接', 'Registered body fixture',
                                  'Obsidian Graph', '归档 历史', 'missing-query'])
def test_full_query_payload_and_pagination_equal_legacy_matcher(tmp_path, monkeypatch, query):
    root = _search_root(tmp_path)
    index = SearchIndex(root)
    index.ensure()
    before_factory = search_query.TermMatcher
    monkeypatch.setattr(search_query, 'TermMatcher', lambda terms: _term_matches)
    before = search_query.search(root, query, limit=1, search_index=index)
    monkeypatch.setattr(search_query, 'TermMatcher', before_factory)
    after = search_query.search(root, query, limit=1, search_index=index)
    assert normalized(before) == normalized(after)
    if before['pagination']['next_cursor']:
        cursor = before['pagination']['next_cursor']
        monkeypatch.setattr(search_query, 'TermMatcher', lambda terms: _term_matches)
        before_next = search_query.search(root, query, limit=1, cursor=cursor, search_index=index)
        monkeypatch.setattr(search_query, 'TermMatcher', before_factory)
        after_next = search_query.search(root, query, limit=1, cursor=cursor, search_index=index)
        assert normalized(before_next) == normalized(after_next)
