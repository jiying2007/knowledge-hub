from pathlib import Path

import pytest
import yaml


WORKFLOWS = Path(".github/workflows")


class _UniqueKeyLoader(yaml.BaseLoader):
    pass


def _construct_unique_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found duplicate key {!r}".format(key),
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


@pytest.mark.parametrize(
    "path",
    sorted(WORKFLOWS.glob("*.yml")),
    ids=lambda path: path.name,
)
def test_workflow_yaml_has_unique_mapping_keys(path):
    text = path.read_text(encoding="utf-8")
    payload = yaml.load(text, Loader=_UniqueKeyLoader)
    assert isinstance(payload, dict)


@pytest.mark.parametrize(
    "path",
    sorted(WORKFLOWS.glob("*.yml")),
    ids=lambda path: path.name,
)
def test_workflow_yaml_uses_spaces_not_tabs(path):
    for number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        1,
    ):
        assert "\t" not in line, "{}:{} contains a tab".format(path, number)
