"""Guard linear-time source-line validation for long cached documents."""

from tools.codex_assets.knowledge_hub import retrieval_chunks as chunks_module


def test_cached_line_validation_scans_linear_text_not_repeated_prefixes():
    class CountedText(str):
        scanned = 0
        def __getitem__(self, key):
            value = super().__getitem__(key)
            return CountedText(value) if isinstance(key, slice) else value
        def count(self, *args):
            CountedText.scanned += len(self)
            return super().count(*args)
    body = CountedText("proof words " * 40000)
    rows = chunks_module._split_body("doc", body)
    assert chunks_module._valid_chunks(rows, body, "doc", rows[0]["source_content_sha256"])
    assert CountedText.scanned <= 4 * len(body)
