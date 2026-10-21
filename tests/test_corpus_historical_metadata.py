"""Regression: repairing a historic Markdown mirror cannot certify its claims."""

import pathlib

from tools.codex_assets.knowledge_hub.common import registry_items, split_frontmatter
from tools.codex_assets.knowledge_hub.corpus_review import _document


ITEM_ID = "pcr02-ds2-ai-shm-session-archive-20260710"
BODY_PATH = (
    "projects/xcrz-sigmastar-demo/archive/reports/"
    "2026-07-10-pcr02-ds2-ai-shm-session-archive.md"
)


def test_ds2_session_metadata_matches_canonical_registry_without_promotion():
    root = pathlib.Path(__file__).resolve().parents[1]
    entry = next(item for item in registry_items(root) if item["id"] == ITEM_ID)
    assert entry["path"] == BODY_PATH
    assert entry["status"] == "reviewing"
    metadata, body = split_frontmatter((root / BODY_PATH).read_text(encoding="utf-8"))
    for key in ("id", "path", "kind", "domain", "status", "owner",
                "scope", "visibility", "review_after"):
        assert str(metadata.get(key, "")) == str(entry.get(key, ""))
    assert metadata["maturity"] == "candidate"
    assert "# PCR02 DS2 与 AI 共享内存链路优化会话归档" in body
    assert "未归档长期板端 soak 数据" in body
    observation = _document(root, entry)
    assert observation["status"] == "read"
    assert observation["frontmatter_matches_registry"] is True
    assert observation["body_empty"] is False
    assert entry["content_review_status"] == "pending"
    assert entry["promotion"] == "none"
