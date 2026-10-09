import json
from pathlib import Path

from tools.codex_assets.knowledge_hub.natural_query import normalize_question
from tools.codex_assets.knowledge_hub.common import registry_items


def test_holdout_gold_ids_resolve_and_include_negative_classes():
    root = Path(__file__).resolve().parents[1]
    cases = json.loads((root / 'tests/fixtures/retrieval_holdout.json').read_text())['cases']
    known = {row['id'] for row in registry_items(root)}
    assert len({row['id'] for row in cases}) == len(cases)
    assert all(set(row.get('expected_ids', [])) <= known for row in cases)
    assert {'natural-zh', 'mixed', 'authority-conflict', 'no-answer', 'synonym'} <= {row['query_class'] for row in cases}


def test_question_normalization_keeps_identifiers_and_negative_constraints():
    value = '如何在 Obsidian 查看知识的反向链接和关系图？'
    result = normalize_question(value)
    assert 'Obsidian' in result and '反向链接' in result and '关系图' in result
    negative = '不要把 reviewing 候选变成 active 事实？'
    assert normalize_question(negative) == negative
    assert normalize_question('zzholdoutmissingtopicquasar987') == 'zzholdoutmissingtopicquasar987'
