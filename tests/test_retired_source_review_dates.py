import datetime as dt
import json
import pathlib

import pytest

from tools.codex_assets.knowledge_hub.check_validation_pre import run_pre_before
from tools.codex_assets.knowledge_hub.common import load_json, load_jsonl


@pytest.mark.parametrize('retired_date,expect_error', [('2020-01-01', False), ('bad-date', True)])
def test_only_registered_sources_require_current_review_cycles(tmp_path, retired_date, expect_error):
    (tmp_path / 'registry').mkdir()
    common = {'role': 'input', 'authority': 'reference', 'write_policy': 'read-only', 'owner': 'owner',
              'source_strategy': 'reference-only', 'final_disposition': 'reference-only'}
    current = dict(common, id='current', path='sources/current', status='registered',
                   check='rtk test -d sources/current', review_after='2020-01-01')
    retired = dict(common, id='retired', path='sources/retired', status='retired',
                   check='rtk test -d sources/retired', review_after=retired_date)
    for source in (current, retired):
        (tmp_path / source['path']).mkdir(parents=True)
    (tmp_path / 'registry/sources.json').write_text(json.dumps({'sources': [current]}))
    (tmp_path / 'registry/retired-sources.jsonl').write_text(json.dumps(retired) + '\n')
    (tmp_path / 'registry/owners.json').write_text(json.dumps({'owners': [{'id': 'owner'}]}))
    ctx = {'root': tmp_path, 'load_json': load_json, 'load_jsonl': load_jsonl,
           'SOURCE_CONTROL_REQUIRED_FILES': [], 'ALLOWED_SOURCE_FINAL_DISPOSITIONS': {'reference-only'},
           'ALLOWED_SOURCE_ROLES': {'input'}, 'ALLOWED_SOURCE_AUTHORITIES': {'reference'},
           'ALLOWED_SOURCE_STATUSES': {'registered', 'retired'}, 'ALLOWED_SOURCE_WRITE_POLICIES': {'read-only'},
           'today': dt.date(2026, 10, 31), 'dt': dt, 'pathlib': pathlib, 'errors': [], 'warnings': []}
    run_pre_before(ctx)
    assert ctx['source_check_health']['stale_review_after_ids'] == ['current']
    assert ctx['warnings'] == ['sources:current review_after is stale: 2020-01-01']
    assert bool(ctx['errors']) is expect_error
