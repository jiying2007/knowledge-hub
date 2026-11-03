import pathlib

import pytest

from tools.codex_assets.knowledge_hub.check_validation_registry import _registry_rest_4
from tools.codex_assets.knowledge_hub.remote_identity import parse_remote


@pytest.mark.parametrize('groups,valid', [([], True), (['device'], True),
                                         (None, False), ('device', False), (['unknown'], False)])
def test_repository_can_have_no_group_but_must_have_a_valid_list(groups, valid):
    repo = {'repo_id': 'sample', 'project_id': 'sample',
            'remote_key': parse_remote('ssh://git@example.test/team/sample.git'),
            'remote_kind': 'internal-git', 'workspace_ref': 'workspace://sample',
            'groups': groups, 'lifecycle': 'first-party', 'status': 'registered'}
    ctx = {'repository_rows': [repo], 'errors': [], 'repository_ids': set(),
           'route_registry_health': {'invalid_reference_count': 0, 'forbidden_path_hits': []},
           'project_ids': {'sample'}, 'remote_keys': set(), 'ALLOWED_REMOTE_KINDS': {'internal-git'},
           'ALLOWED_REPOSITORY_LIFECYCLES': {'first-party'}, 'ALLOWED_PROJECT_REGISTRY_STATUSES': {'registered'},
           'is_allowed_workspace_ref': lambda value: value.startswith('workspace://'),
           'contains_forbidden_registry_path': lambda value: False, 'project_group_ids': {'device'},
           'load_json': lambda path: {'components': []}, 'root': pathlib.Path('/unused')}
    _registry_rest_4(ctx)
    assert (not ctx['errors']) is valid
