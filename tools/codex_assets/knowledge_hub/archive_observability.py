"""Optional archive correlation; trace storage can never invalidate persistence."""

from __future__ import annotations

import os

from .common import KnowledgeHubError
from .observability_runtime import append_optional_span, propagation_context, span_record


def attach_trace(root, receipt, latency_ms):
    if not receipt.get('write_performed'):
        return receipt
    try:
        context = propagation_context(traceparent=os.environ.get('KNOWLEDGE_TRACEPARENT', ''))
        span = span_record(name='provider.archive', trace_id=context['trace_id'], span_id=context['span_id'],
                           parent_span_id=context['parent_span_id'], latency_ms=latency_ms,
                           attributes={'operation_id':receipt['operation_id'], 'item_id':receipt['item_id'],
                                       'transaction_id':receipt.get('transaction_id', ''),
                                       'content_sha256':receipt['content_sha256'], 'persisted':True})
        receipt['observability'] = append_optional_span(root, span)
        receipt['trace_id'] = context['trace_id']
    except (KnowledgeHubError, OSError, ValueError):
        receipt['observability'] = {'status':'degraded', 'non_blocking':True, 'raw_query_stored':False}
    return receipt
