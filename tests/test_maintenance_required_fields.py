"""A missing review collection is not an empty completed collection."""

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.maintenance_triage import build_maintenance_triage


@pytest.mark.parametrize("field", ["status", "today", "rows", "errors"])
def test_missing_required_report_fields_cannot_make_a_no_change_packet(field):
    review = {"status": "report-only", "today": "2026-09-25", "rows": [], "errors": []}
    del review[field]
    with pytest.raises(KnowledgeHubError):
        build_maintenance_triage(review, {"status": "pass"}, {"status": "pass"})
