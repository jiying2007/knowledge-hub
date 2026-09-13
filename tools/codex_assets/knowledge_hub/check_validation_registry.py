def _registry_head_1(ctx):
    for registry_json_path in sorted((ctx['root'] / 'registry').glob('*.json')):
        try:
            ctx['json'].loads(registry_json_path.read_text())
        except Exception:
            ctx['errors'].append(f"registry:{registry_json_path.relative_to(ctx['root'])} invalid json: {ctx['exc']}")
    for registry_jsonl_path in sorted((ctx['root'] / 'registry').glob('*.jsonl')):
        for lineno, line in enumerate(registry_jsonl_path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            try:
                ctx['json'].loads(line)
            except Exception:
                ctx['errors'].append(f"registry:{registry_jsonl_path.relative_to(ctx['root'])}:{lineno} invalid jsonl: {ctx['exc']}")
    by_source_path = ctx['root'] / 'indexes' / 'by-source.md'
    if not by_source_path.exists():
        ctx['errors'].append('index missing: indexes/by-source.md')
    else:
        by_source_ids = set()
        in_sources_section = False
        in_source_table = False
        for line in by_source_path.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith('# '):
                in_sources_section = stripped == '# Knowledge Sources'
                in_source_table = False
                continue
            if in_sources_section and stripped.startswith('#'):
                break
            if not in_sources_section:
                continue
            if not stripped:
                if in_source_table:
                    break
                continue
            if not stripped.startswith('|'):
                if in_source_table:
                    break
                continue
            in_source_table = True
            cells = [cell.strip().strip('`') for cell in stripped.strip('|').split('|')]
            if len(cells) < 3 or cells[0] in {'Source', '---'}:
                continue
            by_source_ids.add(cells[0])
        for source_id in sorted(ctx['source_ids']):
            if source_id not in by_source_ids:
                ctx['errors'].append(f'index:indexes/by-source.md missing source {source_id}')
        for indexed_source_id in sorted(by_source_ids):
            if indexed_source_id not in ctx['source_ids']:
                ctx['errors'].append(f'index:indexes/by-source.md stale source {indexed_source_id}')
    source_coverage_selection, source_coverage_path = ctx['select_source_coverage_closeout'](ctx['root'])
    if source_coverage_selection.get('ignored_non_date_candidates'):
        ctx['warnings'].append('source-coverage: ignored non-date closeout candidates: ' + ', '.join(source_coverage_selection.get('ignored_non_date_candidates', [])))
    source_coverage_ids = set()
    return {key: value for key, value in locals().items() if key != 'ctx'}

def _registry_head_2(ctx):
    if not ctx['source_coverage_selection'].get('candidates'):
        ctx['errors'].append('source-coverage: missing knowledge-hub-source-coverage-closeout manifest')
    elif ctx['source_coverage_path'] is None:
        ctx['errors'].append('source-coverage: missing dated knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl manifest')
    else:
        source_coverage_rows = ctx['load_jsonl'](ctx['source_coverage_path'])
        ctx['source_coverage_health']['row_count'] = len(source_coverage_rows)
        duplicate_source_ids = set()
        missing_required_field_rows = []
        invalid_checked_at_rows = []
        for row in source_coverage_rows:
            row_source_id = row.get('source_id')
            row_id = row.get('id', row_source_id or '<unknown>')
            if not row_source_id:
                ctx['errors'].append(f"source-coverage:{ctx['source_coverage_path'].relative_to(ctx['root'])} row {row_id} missing source_id")
                continue
            if row_source_id in ctx['source_coverage_ids']:
                duplicate_source_ids.add(row_source_id)
                ctx['errors'].append(f"source-coverage:{ctx['source_coverage_path'].relative_to(ctx['root'])} duplicate source {row_source_id}")
            ctx['source_coverage_ids'].add(row_source_id)
            for field in ['status', 'classification', 'decision', 'risk', 'owner', 'checked_at']:
                if not row.get(field):
                    missing_required_field_rows.append({'source_id': row_source_id, 'field': field})
                    ctx['errors'].append(f"source-coverage:{ctx['source_coverage_path'].relative_to(ctx['root'])} source {row_source_id} missing {field}")
            checked_at = str(row.get('checked_at', ''))
            if checked_at:
                try:
                    ctx['dt'].date.fromisoformat(checked_at)
                except Exception:
                    invalid_checked_at_rows.append({'source_id': row_source_id, 'checked_at': checked_at})
                    ctx['errors'].append(f"source-coverage:{ctx['source_coverage_path'].relative_to(ctx['root'])} source {row_source_id} invalid checked_at: {checked_at}")
        ctx['source_coverage_health']['unique_source_count'] = len(ctx['source_coverage_ids'])
        ctx['source_coverage_health']['missing_source_ids'] = sorted(ctx['source_ids'] - ctx['source_coverage_ids'])
        ctx['source_coverage_health']['stale_source_ids'] = sorted(ctx['source_coverage_ids'] - ctx['source_ids'])
        ctx['source_coverage_health']['duplicate_source_ids'] = sorted(duplicate_source_ids)
        ctx['source_coverage_health']['missing_required_field_rows'] = missing_required_field_rows
        ctx['source_coverage_health']['invalid_checked_at_rows'] = invalid_checked_at_rows
        for source_id in sorted(ctx['source_ids']):
            if source_id not in ctx['source_coverage_ids']:
                ctx['errors'].append(f"source-coverage:{ctx['source_coverage_path'].relative_to(ctx['root'])} missing source {source_id}")
        for covered_source_id in sorted(ctx['source_coverage_ids']):
            if covered_source_id not in ctx['source_ids']:
                ctx['errors'].append(f"source-coverage:{ctx['source_coverage_path'].relative_to(ctx['root'])} stale source {covered_source_id}")
    return {key: value for key, value in locals().items() if key != 'ctx'}

def run_registry_head(ctx):
    ctx.update(_registry_head_1(ctx))
    ctx.update(_registry_head_2(ctx))

def _registry_rest_1(ctx):
    owner_gated_source_paths = {}
    owner_gate_roles = set()
    owner_gate_paths = sorted((ctx['root'] / 'artifacts' / 'manifests').glob('*owner-decision-worksheets-*.jsonl'))
    for owner_gate_path in owner_gate_paths:
        for row in ctx['load_jsonl'](owner_gate_path):
            row_source_id = row.get('source_id')
            row_source_path = row.get('source_path')
            row_owner_role = row.get('owner_required') or row.get('owner_candidate') or ''
            if not row_source_id or not row_source_path:
                continue
            if row_owner_role:
                owner_gate_roles.add((str(row_source_id), str(row_owner_role)))
            if ctx['owner_gate_row_resolved'](row):
                continue
            owner_gated_source_paths[row_source_id, row_source_path] = owner_gate_path.relative_to(ctx['root'])
    owner_ids = set()
    owners_doc = ctx['load_json'](ctx['root'] / 'registry' / 'owners.json')
    for owner in owners_doc.get('owners', []):
        owner_id = owner.get('id')
        if not owner_id:
            ctx['errors'].append('owners: missing id')
            continue
        if owner_id in owner_ids:
            ctx['errors'].append(f'owners:{owner_id} duplicate id')
        owner_ids.add(owner_id)
    owner_routing_doc = ctx['load_json'](ctx['root'] / 'registry' / 'owner-routing.json')
    owner_route_keys = set()
    allowed_owner_route_statuses = {'mapped-to-registry-owner', 'needs-human-assignment', 'unmapped', 'retired'}
    for route in owner_routing_doc.get('routes', []):
        role = str(route.get('decision_owner_role', ''))
        source_id = str(route.get('source_id', ''))
        route_id = f'{source_id}:{role}' if source_id or role else '<unknown>'
        for field in ['decision_owner_role', 'source_id', 'routing_status', 'routing_owner', 'required_real_owner_zh', 'escalation_zh', 'notes_zh']:
            if not route.get(field):
                ctx['errors'].append(f'owner-routing:{route_id} missing {field}')
        key = (source_id, role)
        if key in owner_route_keys:
            ctx['errors'].append(f'owner-routing:{route_id} duplicate route')
        owner_route_keys.add(key)
        if source_id and source_id not in ctx['source_ids']:
            ctx['errors'].append(f'owner-routing:{route_id} unknown source_id: {source_id}')
        if route.get('routing_status') and route.get('routing_status') not in allowed_owner_route_statuses:
            ctx['errors'].append(f"owner-routing:{route_id} invalid routing_status: {route.get('routing_status')}")
        routing_owner = route.get('routing_owner')
        if routing_owner and routing_owner not in owner_ids:
            ctx['errors'].append(f'owner-routing:{route_id} unknown routing_owner: {routing_owner}')
        candidate_registry_owners = route.get('candidate_registry_owners', [])
        if not isinstance(candidate_registry_owners, list):
            ctx['errors'].append(f'owner-routing:{route_id} candidate_registry_owners must be list')
        else:
            for candidate_owner in candidate_registry_owners:
                if candidate_owner not in owner_ids:
                    ctx['errors'].append(f'owner-routing:{route_id} unknown candidate_registry_owner: {candidate_owner}')
        if not isinstance(route.get('must_not', []), list) or not route.get('must_not', []):
            ctx['errors'].append(f'owner-routing:{route_id} missing must_not')
    return {key: value for key, value in locals().items() if key != 'ctx'}

def _registry_rest_2(ctx):
    for source_id, role in sorted(ctx['owner_gate_roles']):
        if (source_id, role) not in ctx['owner_route_keys']:
            ctx['errors'].append(f'owner-routing:{source_id}:{role} missing route for owner worksheet role')
    project_ids = set()
    project_group_ids = set()
    repository_ids = set()
    remote_keys = set()
    projects_doc = ctx['load_json'](ctx['root'] / 'registry' / 'projects.json')
    project_rows = projects_doc.get('projects', [])
    ctx['route_registry_health']['project_count'] = len(project_rows)
    for project in project_rows:
        project_id = project.get('id')
        if not project_id:
            ctx['errors'].append('projects: missing id')
            ctx['route_registry_health']['invalid_reference_count'] += 1
            continue
        if project_id in project_ids:
            ctx['errors'].append(f'projects:{project_id} duplicate id')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        project_ids.add(project_id)
        for field in ['name', 'type', 'domain', 'entry', 'current', 'archive', 'decisions', 'validation', 'groups', 'repo_boundary', 'status']:
            if project.get(field) in ('', None, []):
                ctx['errors'].append(f'projects:{project_id} missing {field}')
                ctx['route_registry_health']['invalid_reference_count'] += 1
        status = project.get('status')
        if status and status not in ctx['ALLOWED_PROJECT_REGISTRY_STATUSES']:
            ctx['errors'].append(f'projects:{project_id} invalid status: {status}')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        for field in ['domain', 'entry', 'current', 'archive', 'decisions', 'validation']:
            value = str(project.get(field, ''))
            if value and ctx['contains_forbidden_registry_path'](value):
                ctx['route_registry_health']['forbidden_path_hits'].append(f'projects:{project_id}:{field}')
                ctx['errors'].append(f'projects:{project_id} {field} must not use machine path: {value}')
            if value and (not ctx['registry_relpath_ok'](value)):
                ctx['errors'].append(f'projects:{project_id} {field} must be repo-relative: {value}')
                ctx['route_registry_health']['invalid_reference_count'] += 1
        entry = str(project.get('entry', ''))
        if entry and ctx['registry_relpath_ok'](entry) and (not (ctx['root'] / entry).exists()):
            ctx['route_registry_health']['missing_entry_paths'].append(entry)
            ctx['errors'].append(f'projects:{project_id} entry path missing: {entry}')
        groups_value = project.get('groups', [])
        if not isinstance(groups_value, list) or not groups_value:
            ctx['errors'].append(f'projects:{project_id} groups must be non-empty list')
            ctx['route_registry_health']['invalid_reference_count'] += 1
    project_groups_doc = ctx['load_json'](ctx['root'] / 'registry' / 'project-groups.json')
    group_rows = project_groups_doc.get('groups', [])
    ctx['route_registry_health']['group_count'] = len(group_rows)
    return {key: value for key, value in locals().items() if key != 'ctx'}

def _registry_rest_3(ctx):
    for group in ctx['group_rows']:
        group_id = group.get('id')
        if not group_id:
            ctx['errors'].append('project-groups: missing id')
            ctx['route_registry_health']['invalid_reference_count'] += 1
            continue
        if group_id in ctx['project_group_ids']:
            ctx['errors'].append(f'project-groups:{group_id} duplicate id')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        ctx['project_group_ids'].add(group_id)
        for field in ['name', 'type', 'entry', 'member_project_ids', 'status']:
            if group.get(field) in ('', None, []):
                ctx['errors'].append(f'project-groups:{group_id} missing {field}')
                ctx['route_registry_health']['invalid_reference_count'] += 1
        if group.get('status') and group.get('status') not in ctx['ALLOWED_PROJECT_REGISTRY_STATUSES']:
            ctx['errors'].append(f"project-groups:{group_id} invalid status: {group.get('status')}")
            ctx['route_registry_health']['invalid_reference_count'] += 1
        entry = str(group.get('entry', ''))
        if entry and ctx['contains_forbidden_registry_path'](entry):
            ctx['route_registry_health']['forbidden_path_hits'].append(f'project-groups:{group_id}:entry')
            ctx['errors'].append(f'project-groups:{group_id} entry must not use machine path: {entry}')
        if entry and ctx['registry_relpath_ok'](entry) and (not (ctx['root'] / entry).exists()):
            ctx['route_registry_health']['missing_entry_paths'].append(entry)
            ctx['errors'].append(f'project-groups:{group_id} entry path missing: {entry}')
        for member_project_id in group.get('member_project_ids', []):
            if member_project_id not in ctx['project_ids']:
                ctx['errors'].append(f'project-groups:{group_id} unknown member_project_id: {member_project_id}')
                ctx['route_registry_health']['invalid_reference_count'] += 1
    for project in ctx['project_rows']:
        project_id = project.get('id', '<unknown>')
        for group_id in project.get('groups', []) if isinstance(project.get('groups', []), list) else []:
            if group_id not in ctx['project_group_ids']:
                ctx['errors'].append(f'projects:{project_id} unknown group: {group_id}')
                ctx['route_registry_health']['invalid_reference_count'] += 1
    repositories_doc = ctx['load_json'](ctx['root'] / 'registry' / 'repositories.json')
    repository_rows = repositories_doc.get('repositories', [])
    ctx['route_registry_health']['repository_count'] = len(repository_rows)
    return {key: value for key, value in locals().items() if key != 'ctx'}

def _registry_rest_4(ctx):
    for repo in ctx['repository_rows']:
        repo_id = repo.get('repo_id')
        if not repo_id:
            ctx['errors'].append('repositories: missing repo_id')
            ctx['route_registry_health']['invalid_reference_count'] += 1
            continue
        if repo_id in ctx['repository_ids']:
            ctx['errors'].append(f'repositories:{repo_id} duplicate repo_id')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        ctx['repository_ids'].add(repo_id)
        for field in ['remote_key', 'remote_kind', 'workspace_ref', 'groups', 'lifecycle', 'status']:
            if repo.get(field) in ('', None, []):
                ctx['errors'].append(f'repositories:{repo_id} missing {field}')
                ctx['route_registry_health']['invalid_reference_count'] += 1
        project_id = str(repo.get('project_id', ''))
        lifecycle = str(repo.get('lifecycle', ''))
        if project_id and project_id not in ctx['project_ids']:
            ctx['errors'].append(f'repositories:{repo_id} unknown project_id: {project_id}')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        if not project_id and lifecycle != 'external-reference':
            ctx['errors'].append(f'repositories:{repo_id} empty project_id only allowed for external-reference')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        remote_key = str(repo.get('remote_key', ''))
        if remote_key:
            if remote_key in ctx['remote_keys']:
                ctx['errors'].append(f'repositories:{repo_id} duplicate remote_key: {remote_key}')
                ctx['route_registry_health']['invalid_reference_count'] += 1
            ctx['remote_keys'].add(remote_key)
            if any((token in remote_key for token in ('://', '@', '/home/', '/vsdata/'))) or remote_key.endswith('.git') or remote_key.startswith('/'):
                ctx['errors'].append(f'repositories:{repo_id} remote_key must be normalized logical key: {remote_key}')
                ctx['route_registry_health']['invalid_reference_count'] += 1
        if repo.get('remote_kind') and repo.get('remote_kind') not in ctx['ALLOWED_REMOTE_KINDS']:
            ctx['errors'].append(f"repositories:{repo_id} invalid remote_kind: {repo.get('remote_kind')}")
            ctx['route_registry_health']['invalid_reference_count'] += 1
        if lifecycle and lifecycle not in ctx['ALLOWED_REPOSITORY_LIFECYCLES']:
            ctx['errors'].append(f'repositories:{repo_id} invalid lifecycle: {lifecycle}')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        if repo.get('status') and repo.get('status') not in ctx['ALLOWED_PROJECT_REGISTRY_STATUSES']:
            ctx['errors'].append(f"repositories:{repo_id} invalid status: {repo.get('status')}")
            ctx['route_registry_health']['invalid_reference_count'] += 1
        workspace_ref = str(repo.get('workspace_ref', ''))
        if workspace_ref and (not ctx['is_allowed_workspace_ref'](workspace_ref)):
            ctx['errors'].append(f'repositories:{repo_id} workspace_ref must be logical or allowed local convention: {workspace_ref}')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        if workspace_ref and ctx['contains_forbidden_registry_path'](workspace_ref):
            ctx['route_registry_health']['forbidden_path_hits'].append(f'repositories:{repo_id}:workspace_ref')
            ctx['errors'].append(f'repositories:{repo_id} workspace_ref must not use machine path: {workspace_ref}')
        for group_id in repo.get('groups', []) if isinstance(repo.get('groups', []), list) else []:
            if group_id not in ctx['project_group_ids']:
                ctx['errors'].append(f'repositories:{repo_id} unknown group: {group_id}')
                ctx['route_registry_health']['invalid_reference_count'] += 1
    components_doc = ctx['load_json'](ctx['root'] / 'registry' / 'components.json')
    component_rows = components_doc.get('components', [])
    ctx['route_registry_health']['component_count'] = len(component_rows)
    component_ids = set()
    return {key: value for key, value in locals().items() if key != 'ctx'}

def _registry_rest_5(ctx):
    for component in ctx['component_rows']:
        component_id = component.get('component_id')
        if not component_id:
            ctx['errors'].append('components: missing component_id')
            ctx['route_registry_health']['invalid_reference_count'] += 1
            continue
        if component_id in ctx['component_ids']:
            ctx['errors'].append(f'components:{component_id} duplicate component_id')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        ctx['component_ids'].add(component_id)
        for field in ['parent_project_id', 'component_uri', 'kind', 'relative_path', 'status']:
            if field not in component or component.get(field) is None:
                ctx['errors'].append(f'components:{component_id} missing {field}')
                ctx['route_registry_health']['invalid_reference_count'] += 1
        parent_project_id = str(component.get('parent_project_id', ''))
        if parent_project_id and parent_project_id not in ctx['project_ids']:
            ctx['errors'].append(f'components:{component_id} unknown parent_project_id: {parent_project_id}')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        component_uri = str(component.get('component_uri', ''))
        if component_uri and (not component_uri.startswith('component://')):
            ctx['errors'].append(f'components:{component_id} component_uri must start with component://')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        relative_path = str(component.get('relative_path', ''))
        if relative_path and (ctx['pathlib'].Path(relative_path).is_absolute() or relative_path.startswith(('./', '../', '~')) or ctx['contains_forbidden_registry_path'](relative_path)):
            ctx['errors'].append(f'components:{component_id} relative_path must be source-relative logical path: {relative_path}')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        if component.get('status') and component.get('status') not in ctx['ALLOWED_COMPONENT_STATUSES']:
            ctx['errors'].append(f"components:{component_id} invalid status: {component.get('status')}")
            ctx['route_registry_health']['invalid_reference_count'] += 1
    project_routes_doc = ctx['load_json'](ctx['root'] / 'registry' / 'project-routes.json')
    route_rows = project_routes_doc.get('routes', [])
    ctx['route_registry_health']['route_count'] = len(route_rows)
    route_keys = set()
    return {key: value for key, value in locals().items() if key != 'ctx'}

def _registry_rest_6(ctx):
    for route in ctx['route_rows']:
        project_id = str(route.get('project_id', ''))
        route_key = project_id or str(route.get('group_id', '<unknown>'))
        if route_key in ctx['route_keys']:
            ctx['errors'].append(f'project-routes:{route_key} duplicate route')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        ctx['route_keys'].add(route_key)
        for field in ['project_id', 'name', 'type', 'aliases', 'repo_refs', 'workspace_refs', 'hub_entry', 'current_path', 'archive_path', 'decisions_path', 'validation_path', 'route_key_policy']:
            if route.get(field) in ('', None, []):
                ctx['errors'].append(f'project-routes:{route_key} missing {field}')
                ctx['route_registry_health']['invalid_reference_count'] += 1
        if project_id and project_id not in ctx['project_ids']:
            ctx['errors'].append(f'project-routes:{route_key} unknown project_id: {project_id}')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        group_id = str(route.get('group_id', ''))
        if group_id and group_id not in ctx['project_group_ids']:
            ctx['errors'].append(f'project-routes:{route_key} unknown group_id: {group_id}')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        if 'cwd_patterns' in route:
            ctx['errors'].append(f'project-routes:{route_key} cwd_patterns is not part of the current route contract')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        if str(route.get('engineering_archive_path', '')):
            ctx['errors'].append(f'project-routes:{route_key} engineering_archive_path is unsupported; use archive_path')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        if 'retired_route_ids' in route:
            ctx['errors'].append(f'project-routes:{route_key} retired_route_ids is not part of the current route contract')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        default_source_ids = route.get('default_source_ids', [])
        if not isinstance(default_source_ids, list):
            ctx['errors'].append(f'project-routes:{route_key} default_source_ids must be a list')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        else:
            for default_source_id in default_source_ids:
                if default_source_id not in ctx['current_source_ids']:
                    ctx['errors'].append(f'project-routes:{route_key} default_source_id is not a current registered source: {default_source_id}')
                    ctx['route_registry_health']['invalid_reference_count'] += 1
        for repo_id in route.get('repo_refs', []) if isinstance(route.get('repo_refs', []), list) else []:
            if repo_id not in ctx['repository_ids']:
                ctx['errors'].append(f'project-routes:{route_key} unknown repo_ref: {repo_id}')
                ctx['route_registry_health']['invalid_reference_count'] += 1
        for workspace_ref in route.get('workspace_refs', []) if isinstance(route.get('workspace_refs', []), list) else []:
            if not ctx['is_allowed_workspace_ref'](workspace_ref):
                ctx['errors'].append(f'project-routes:{route_key} invalid workspace_ref: {workspace_ref}')
                ctx['route_registry_health']['invalid_reference_count'] += 1
            if ctx['contains_forbidden_registry_path'](workspace_ref):
                ctx['route_registry_health']['forbidden_path_hits'].append(f'project-routes:{route_key}:workspace_ref')
                ctx['errors'].append(f'project-routes:{route_key} workspace_ref must not use machine path: {workspace_ref}')
        for field in ['hub_entry', 'current_path', 'archive_path', 'decisions_path', 'validation_path']:
            value = str(route.get(field, ''))
            if value and ctx['contains_forbidden_registry_path'](value):
                ctx['route_registry_health']['forbidden_path_hits'].append(f'project-routes:{route_key}:{field}')
                ctx['errors'].append(f'project-routes:{route_key} {field} must not use machine path: {value}')
            if value and (not ctx['registry_relpath_ok'](value)):
                ctx['errors'].append(f'project-routes:{route_key} {field} must be repo-relative: {value}')
                ctx['route_registry_health']['invalid_reference_count'] += 1
        hub_entry = str(route.get('hub_entry', ''))
        if hub_entry and ctx['registry_relpath_ok'](hub_entry) and (not (ctx['root'] / hub_entry).exists()):
            ctx['route_registry_health']['missing_entry_paths'].append(hub_entry)
            ctx['errors'].append(f'project-routes:{route_key} hub_entry path missing: {hub_entry}')
    return {key: value for key, value in locals().items() if key != 'ctx'}

def _registry_rest_7(ctx):
    workspaces_example_doc = ctx['load_json'](ctx['root'] / 'registry' / 'workspaces.example.json')
    workspace_rows = workspaces_example_doc.get('workspaces', [])
    ctx['route_registry_health']['workspace_example_count'] = len(workspace_rows)
    for index, workspace in enumerate(workspace_rows, 1):
        workspace_ref = str(workspace.get('workspace_ref', ''))
        label = workspace_ref or f'row-{index}'
        if not workspace_ref:
            ctx['errors'].append(f'workspaces:{label} missing workspace_ref')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        elif not ctx['is_allowed_workspace_ref'](workspace_ref):
            ctx['errors'].append(f'workspaces:{label} invalid workspace_ref: {workspace_ref}')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        for field in ['path', 'path_example']:
            value = str(workspace.get(field, ''))
            if value and ctx['contains_forbidden_registry_path'](value):
                ctx['route_registry_health']['forbidden_path_hits'].append(f'workspaces:{label}:{field}')
                ctx['errors'].append(f'workspaces:{label} {field} must not use machine path: {value}')
        repo_id = str(workspace.get('repo_id', ''))
        group_id = str(workspace.get('project_group_id', ''))
        if repo_id and repo_id not in ctx['repository_ids']:
            ctx['errors'].append(f'workspaces:{label} unknown repo_id: {repo_id}')
            ctx['route_registry_health']['invalid_reference_count'] += 1
        if group_id and group_id not in ctx['project_group_ids']:
            ctx['errors'].append(f'workspaces:{label} unknown project_group_id: {group_id}')
            ctx['route_registry_health']['invalid_reference_count'] += 1
    ctx['route_registry_health']['forbidden_path_hits'] = sorted(set(ctx['route_registry_health']['forbidden_path_hits']))
    ctx['route_registry_health']['missing_entry_paths'] = sorted(set(ctx['route_registry_health']['missing_entry_paths']))
    ctx['route_registry_health']['status'] = 'fail' if ctx['route_registry_health']['invalid_reference_count'] or ctx['route_registry_health']['forbidden_path_hits'] or ctx['route_registry_health']['missing_entry_paths'] else 'pass'
    topic_ids = set()
    topics_doc = ctx['load_json'](ctx['root'] / 'registry' / 'topics.json')
    return {key: value for key, value in locals().items() if key != 'ctx'}

def _registry_rest_8(ctx):
    for topic in ctx['topics_doc'].get('topics', []):
        topic_id = topic.get('id')
        if not topic_id:
            ctx['errors'].append('topics: missing id')
            continue
        if topic_id in ctx['topic_ids']:
            ctx['errors'].append(f'topics:{topic_id} duplicate id')
        ctx['topic_ids'].add(topic_id)
        topic_domain = topic.get('domain')
        if not topic_domain:
            ctx['errors'].append(f'topics:{topic_id} missing domain')
        else:
            if str(topic_domain).startswith(('domains/projects', 'domains/personal')):
                ctx['errors'].append(f'topics:{topic_id} domain uses a noncanonical path: {topic_domain}')
            topic_path = ctx['pathlib'].Path(str(topic_domain))
            if topic_path.is_absolute():
                ctx['errors'].append(f'topics:{topic_id} domain must be relative: {topic_domain}')
            elif not (ctx['root'] / topic_path).exists():
                ctx['errors'].append(f'topics:{topic_id} domain path missing: {topic_domain}')
        allowed_kinds = topic.get('allowed_kinds')
        if not isinstance(allowed_kinds, list) or not allowed_kinds:
            ctx['errors'].append(f'topics:{topic_id} missing allowed_kinds')
        else:
            for allowed_kind in allowed_kinds:
                if allowed_kind not in ctx['ALLOWED_ITEM_KINDS']:
                    ctx['errors'].append(f'topics:{topic_id} invalid allowed_kind: {allowed_kind}')
    retention_path = ctx['root'] / 'registry' / 'retention.json'
    if retention_path.exists():
        retention_doc = ctx['load_json'](retention_path)
        rules = retention_doc.get('rules', [])
        if not isinstance(rules, list):
            ctx['errors'].append('retention: rules must be list')
        else:
            for index, rule in enumerate(rules):
                if not isinstance(rule, dict):
                    ctx['errors'].append(f'retention:{index} rule must be object')
                    continue
                rule_domain = str(rule.get('domain', ''))
                if rule_domain.startswith(('domains/projects', 'domains/personal')):
                    ctx['errors'].append(f'retention:{index} domain uses a noncanonical path: {rule_domain}')
    return {key: value for key, value in locals().items() if key != 'ctx'}

def run_registry_rest(ctx):
    ctx.update(_registry_rest_1(ctx))
    ctx.update(_registry_rest_2(ctx))
    ctx.update(_registry_rest_3(ctx))
    ctx.update(_registry_rest_4(ctx))
    ctx.update(_registry_rest_5(ctx))
    ctx.update(_registry_rest_6(ctx))
    ctx.update(_registry_rest_7(ctx))
    ctx.update(_registry_rest_8(ctx))
