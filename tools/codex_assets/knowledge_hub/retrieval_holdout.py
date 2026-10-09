"""Report per-class held-out retrieval and lexical/hash shadow quality separately."""

from __future__ import annotations

from collections import defaultdict
import json
import pathlib
import tempfile
import hashlib

from .common import read_utf8_bounded, file_sha256, KnowledgeHubError, working_tree_signature
from .retrieval import run_retrieval_benchmark_serialized, retrieval_benchmark_summary
from .retrieval_metrics import validate_cases, ranking_summary


def evaluate_holdout(root, path, *, diagnose=False, **benchmark_options):
    before_signature = working_tree_signature(root)
    raw = read_utf8_bounded(path, 4 * 1024 * 1024, 'holdout dataset')
    dataset = json.loads(raw)
    validate_cases(dataset)
    dataset_digest = hashlib.sha256(raw.encode()).hexdigest()
    role = dataset.get('dataset_role', 'development-regression')
    case_digest = hashlib.sha256(json.dumps(dataset['cases'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    unseen = role == 'frozen-validation' and dataset.get('used_for_tuning') is False
    if role == 'frozen-validation' and (not unseen or dataset.get('frozen_cases_sha256') != case_digest):
        raise KnowledgeHubError('frozen validation dataset integrity or tuning isolation failed')
    if diagnose and role == 'frozen-validation':
        raise KnowledgeHubError('frozen validation cannot be used for development diagnostics')
    if diagnose and (not isinstance(dataset.get('cases'), list) or len(dataset['cases']) > 200):
        raise KnowledgeHubError('development diagnosis exceeds 200-case budget')
    if diagnose:
        from .retrieval_diagnostics import _validate_development
        _validate_development(dataset, {'cases':dataset['cases']})
    with tempfile.TemporaryDirectory(prefix='kh-holdout-raw-') as directory:
        frozen_path = pathlib.Path(directory) / 'cases.json'
        frozen_path.write_text(raw, encoding='utf-8')
        measured = run_retrieval_benchmark_serialized(root, cases_path=frozen_path, enable_extended_probes=False, **benchmark_options)
    classes = {row['id']:row.get('query_class', 'unclassified') for row in dataset['cases']}
    grouped = defaultdict(list)
    for row in measured['cases']:
        grouped[classes[row['id']]].append(row)
    breakdown = {}
    for name, rows in sorted(grouped.items()):
        breakdown[name] = {'case_count':len(rows), 'hit_rate':sum(row['hit'] for row in rows) / len(rows),
                           **ranking_summary(rows),
                           'forbidden_hit_count':sum(len(row['forbidden_hits']) for row in rows)}
    from .natural_query import normalize_question
    shadow_dataset = dict(dataset, cases=[dict(case, query=normalize_question(case['query'])) for case in dataset['cases']])
    with tempfile.TemporaryDirectory(prefix='kh-holdout-shadow-') as directory:
        shadow_path = pathlib.Path(directory) / 'cases.json'
        shadow_path.write_text(json.dumps(shadow_dataset, ensure_ascii=False), encoding='utf-8')
        shadow = run_retrieval_benchmark_serialized(root, cases_path=shadow_path, enable_extended_probes=False, **benchmark_options)
    diagnostics = None
    if diagnose:
        from .retrieval_diagnostics import development_diagnostics
        diagnostics = development_diagnostics(dataset, measured, root=root)
    after_signature = working_tree_signature(root)
    unchanged = before_signature == after_signature
    output = {'schema_version':'knowledge-hub.holdout-report/v1', 'status':measured['status'] if unchanged else 'fail',
            'production_derived':False, 'report_only':True, 'default_policy_changed':False,
            'evaluation_scope':'unseen-engineering-validation' if unseen else 'development-regression',
            'independent_of_tuning':unseen, 'production_qualification':False,
            'dataset_sha256':dataset_digest, 'cases_sha256':case_digest, 'dataset_input_frozen':True,
            'source_signature':before_signature,
            'candidate_integrity':{'unchanged':unchanged, 'before_signature':before_signature, 'after_signature':after_signature},
            'evaluator_sha256':file_sha256(pathlib.Path(__file__)),
            'benchmark':retrieval_benchmark_summary(measured), 'by_query_class':breakdown,
            'shadow':{'method':'natural-question-normalization-v2-boundary-only', 'status':shadow['status'],
                      'hit_rate':shadow['hit_rate'], 'mrr':shadow['mrr'], 'ndcg_at_10':shadow['ndcg_at_10'],
                      'authority_recall_at_3':shadow['authority_recall_at_3'],
                      'failed_ids':[row['id'] for row in shadow['cases'] if not row['hit']],
                      'integrity':shadow['integrity']},
            'failed_ids':[row['id'] for row in measured['cases'] if not row['hit']]}
    if diagnose:
        output['development_diagnostics'] = diagnostics
    return output


def holdout_summary(payload):
    benchmark = payload['benchmark']
    result = {key:payload[key] for key in ('schema_version', 'status', 'evaluation_scope', 'dataset_sha256',
            'cases_sha256', 'source_signature', 'candidate_integrity', 'production_qualification')}
    result.update({
            'projection':'holdout-summary-v1',
            'quality':{key:benchmark.get(key) for key in (
                'case_count', 'top_k', 'hit_rate', 'mrr', 'ndcg_at_10', 'thresholds',
                'metric_scope', 'ranking_case_count', 'ranking_metrics_applicable',
                'zero_hit_case_count', 'zero_hit_accuracy', 'zero_hit_failure_count',
            )},
            'failed_ids':payload['failed_ids'][:20],
            'shadow_status':payload['shadow']['status']})
    return result
