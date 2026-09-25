"""Corrupt cached validation failures rebuild; provider failures still propagate."""

import hashlib
import json

import pytest

from tools.codex_assets.knowledge_hub.retrieval_cache import DerivedCache
from tools.codex_assets.knowledge_hub.retrieval_v4 import _valid_vector


def test_huge_cached_integer_validation_recomputes_current_vector(tmp_path):
    with DerivedCache(tmp_path) as cache:
        def build():
            return [1.0, 0.0]
        def valid(value):
            return _valid_vector(value, 2)
        cache.resolve("vector", "key", "revision", build, valid)
        raw = json.dumps([10 ** 400, 0]).encode("utf-8")
        cache.connection.execute("update entries set payload=?,digest=?",
                                 (raw, hashlib.sha256(raw).hexdigest()))
        assert cache.resolve("vector", "key", "revision", build, valid) == [1.0, 0.0]
        assert cache.stats["invalid_entries"] == 1
        assert cache.stats["hits"] == 0


def test_canonical_builder_errors_are_not_misclassified_as_cache_corruption(tmp_path):
    def broken_provider():
        raise OverflowError("provider overflow")
    with DerivedCache(tmp_path) as cache:
        with pytest.raises(OverflowError, match="provider overflow"):
            cache.resolve("vector", "key", "revision", broken_provider, lambda value: True)
        assert cache.stats["invalid_entries"] == 0
