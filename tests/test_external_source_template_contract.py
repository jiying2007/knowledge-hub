"""Explicit source-note template kind matches the registry and CLI contract."""

import json
from pathlib import Path

import yaml

from tools.codex_assets.knowledge_hub.new_cli import TEMPLATES

ROOT = Path(__file__).resolve().parents[1]


def _template_metadata(path):
    data = (ROOT / path).read_text(encoding="utf-8")
    assert data.startswith("---\n")
    return yaml.safe_load(data.split("---", 2)[1])


def test_external_source_template_kind_matches_schema_and_cli():
    path = "templates/external-source-note.md"
    kind = _template_metadata(path)["kind"]
    item_schema = json.loads((ROOT / "schemas/item.schema.json").read_text(encoding="utf-8"))
    assert kind == "external-source-note"
    assert kind in item_schema["properties"]["kind"]["enum"]
    assert TEMPLATES["external-source-note"] == (path, kind)
    assert TEMPLATES["external-source"] == (path, kind)


def test_patent_template_alias_is_intentionally_shared():
    path = "templates/patent-disclosure.md"
    kind = _template_metadata(path)["kind"]
    assert kind == "patent"
    assert TEMPLATES["patent"] == (path, "patent")
    assert TEMPLATES["patent-disclosure"] == (path, "patent-disclosure")
