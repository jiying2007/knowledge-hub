"""Recent local health never inherits lifetime qualification from stale samples."""

from __future__ import annotations

import datetime as dt


def finish_metrics(payload, searches, contexts, feedback, today):
    payload['recent_health'] = rolling_health(searches, contexts, feedback, today)
    payload['adoption']['qualification_scope'] = 'lifetime-local-observation'
    return payload


def rolling_health(search_rows, context_rows, feedback_rows, today):
    from . import metrics

    searches = metrics._current_performance_rows(search_rows)
    contexts = metrics._current_performance_rows(context_rows)
    current = {row['interaction_id'] for row in searches + contexts}
    feedback = [row for row in feedback_rows if row['interaction_id'] in current]
    windows = {}
    for days in (7, 30, 90):
        start = today - dt.timedelta(days=days - 1)

        def selected(rows, window_start=start):
            return [row for row in rows if window_start <= metrics._date(row.get('recorded_at')) <= today]

        search, context, responses = selected(searches), selected(contexts), selected(feedback)
        window_ids = {row['interaction_id'] for row in search + context}
        responses = [row for row in responses if row['interaction_id'] in window_ids]
        search_perf, context_perf = metrics._performance_samples(search), metrics._performance_samples(context)
        search_p95 = metrics._percentile(search_perf['warm'], .95)
        context_p95 = metrics._percentile(context_perf['warm'], .95)
        found = sum(row.get('outcome') == 'found' for row in responses)
        found_rate = found / len(responses) if responses else None
        enough = (len(search_perf['warm']) >= metrics.MINIMUM_PERFORMANCE_SAMPLE_COUNT
                  and len(context_perf['warm']) >= metrics.MINIMUM_PERFORMANCE_SAMPLE_COUNT
                  and len(responses) >= 10)
        prep = search_perf['preparation'] + context_perf['preparation']
        ready = (enough and found_rate is not None and found_rate >= .8 and search_p95 <= metrics.SEARCH_WARM_TARGET_MS
                 and context_p95 <= metrics.CONTEXT_WARM_TARGET_MS
                 and metrics._percentile(prep, .95) <= metrics.INDEX_PREPARATION_TARGET_MS)
        dates = sorted({metrics._date(row.get('recorded_at')) for row in search + context})
        windows[str(days)] = {
            'window_start':start.isoformat(), 'window_end':today.isoformat(),
            'status':'pass' if ready else 'needs-fix' if enough else 'insufficient-data',
            'ready':bool(ready), 'search_count':len(search), 'context_count':len(context),
            'feedback_count':len(responses), 'found_rate':found_rate,
            'feedback_coverage':round(len(responses) / max(1, len(search) + len(context)), 4),
            'active_days':len(dates), 'last_sample_at':dates[-1].isoformat() if dates else '',
            'warm_search_samples':len(search_perf['warm']), 'warm_context_samples':len(context_perf['warm']),
            'search_p95_ms':search_p95, 'context_p95_ms':context_p95,
        }
    dates = sorted(metrics._date(row.get('recorded_at')) for row in searches + contexts
                   if dt.date.min < metrics._date(row.get('recorded_at')) <= today)
    return {'scope':'local-only', 'as_of':today.isoformat(), 'windows':windows,
            'last_sample_at':dates[-1].isoformat() if dates else '',
            'sample_age_days':(today - dates[-1]).days if dates else None,
            'current_status':windows['30']['status'],
            'raw_query_stored':False, 'production_qualification':False}
