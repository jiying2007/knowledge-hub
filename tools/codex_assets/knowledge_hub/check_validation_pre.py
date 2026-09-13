def _pre_before_1(ctx):
    sources_path = ctx['root'] / 'registry' / 'sources.json'
    sources_payload = ctx['load_json'](sources_path)
    current_sources = sources_payload.get('sources', [])
    retired_sources = ctx['load_jsonl'](ctx['root'] / 'registry' / 'retired-sources.jsonl')
    if not isinstance(current_sources, list):
        ctx['errors'].append('sources: sources must be a list')
        current_sources = []
    for source in current_sources:
        if isinstance(source, dict) and source.get('status') != 'registered':
            ctx['errors'].append(f"sources:{source.get('id', '<unknown>')} current registry requires status=registered")
    for source in retired_sources:
        if isinstance(source, dict) and source.get('status') != 'retired':
            ctx['errors'].append(f"retired-sources:{source.get('id', '<unknown>')} retired ledger requires status=retired")
    sources = current_sources + retired_sources
    current_source_ids = {str(source.get('id', '')) for source in current_sources if isinstance(source, dict) and source.get('id') and (source.get('status') == 'registered')}
    owner_ids_for_sources = {owner.get('id', '') for owner in ctx['load_json'](ctx['root'] / 'registry' / 'owners.json').get('owners', []) if owner.get('id')}
    source_check_health = {'mode': 'static-registry-only', 'executed': False, 'registered_source_count': len(sources), 'with_check_count': 0, 'with_no_check_reason_count': 0, 'check_command_count': 0, 'no_check_reason_count': 0, 'path_exists_count': 0, 'missing_check_or_reason_ids': [], 'both_check_and_no_check_reason_ids': [], 'non_rtk_check_ids': [], 'missing_source_path_ids': [], 'stale_review_after_ids': [], 'missing_check_or_reason_source_ids': [], 'both_check_and_no_check_reason_source_ids': [], 'non_rtk_check_command_source_ids': [], 'check_command_source_ids': [], 'no_check_reason_source_ids': [], 'path_missing_source_ids': [], 'stale_review_after_source_ids': [], 'rows': [], 'report_only_findings': ['source check commands are inspected but not executed by knowledge-check']}
    source_control_health = {'mode': 'hub-source-control-directories', 'registered_source_count': len(sources), 'required_file_count': len(sources) * len(ctx['SOURCE_CONTROL_REQUIRED_FILES']), 'present_file_count': 0, 'missing_source_ids': [], 'missing_files': [], 'inventory_row_count': 0, 'invalid_inventory_rows': [], 'unsafe_raw_copy_rows': [], 'rows_by_source': {}, 'status': 'pass'}
    owner_target_health = {'mode': 'owner-decision-landing-target-existence', 'landing_manifest': 'artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.jsonl', 'checked_count': 0, 'present_count': 0, 'skipped_count': 0, 'missing_targets': [], 'rows': [], 'status': 'pass'}
    source_ids = set()
    return {key: value for key, value in locals().items() if key != 'ctx'}

def _pre_before_2(ctx):
    for source in ctx['sources']:
        for field in ['id', 'path', 'role', 'authority', 'status', 'write_policy', 'source_strategy', 'owner', 'review_after', 'final_disposition']:
            if not source.get(field):
                ctx['errors'].append(f"sources:{source.get('id', '<unknown>')} missing {field}")
        source_id = source.get('id', '<unknown>')
        if source.get('id'):
            if source_id in ctx['source_ids']:
                ctx['errors'].append(f'sources:{source_id} duplicate id')
            ctx['source_ids'].add(source_id)
        if source.get('role') and source.get('role') not in ctx['ALLOWED_SOURCE_ROLES']:
            ctx['errors'].append(f"sources:{source_id} invalid role: {source.get('role')}")
        if source.get('authority') and source.get('authority') not in ctx['ALLOWED_SOURCE_AUTHORITIES']:
            ctx['errors'].append(f"sources:{source_id} invalid authority: {source.get('authority')}")
        if source.get('status') and source.get('status') not in ctx['ALLOWED_SOURCE_STATUSES']:
            ctx['errors'].append(f"sources:{source_id} invalid status: {source.get('status')}")
        if source.get('write_policy') and source.get('write_policy') not in ctx['ALLOWED_SOURCE_WRITE_POLICIES']:
            ctx['errors'].append(f"sources:{source_id} invalid write_policy: {source.get('write_policy')}")
        if source.get('owner') and source.get('owner') not in ctx['owner_ids_for_sources']:
            ctx['errors'].append(f"sources:{source_id} unknown owner: {source.get('owner')}")
        if source.get('review_after'):
            try:
                source_review_after = ctx['dt'].date.fromisoformat(str(source.get('review_after')))
                if source_review_after < ctx['today']:
                    ctx['source_check_health']['stale_review_after_ids'].append(source_id)
                    ctx['source_check_health']['stale_review_after_source_ids'].append(source_id)
                    ctx['warnings'].append(f"sources:{source_id} review_after is stale: {source.get('review_after')}")
            except Exception:
                ctx['errors'].append(f"sources:{source_id} invalid review_after: {source.get('review_after')}")
        if source.get('final_disposition') and source.get('final_disposition') not in ctx['ALLOWED_SOURCE_FINAL_DISPOSITIONS']:
            ctx['errors'].append(f"sources:{source_id} invalid final_disposition: {source.get('final_disposition')}")
        check_command = str(source.get('check', '')).strip()
        no_check_reason = str(source.get('no_check_reason', '')).strip()
        source_path_text = str(source.get('path', ''))
        if source_path_text.startswith('~/') or source_path_text.startswith('/') or source_path_text.startswith('../') or source_path_text.startswith('./') or (not source_path_text.startswith('sources/')):
            ctx['errors'].append(f'sources:{source_id} path must point to Hub source control directory: {source_path_text}')
        if any((token in check_command for token in ['~/embedded', '~/codex/docs/archive', '~/work/', '~/.codex', '/vsdata/'])):
            ctx['errors'].append(f'sources:{source_id} check must not depend on retired external source path')
        path = ctx['pathlib'].Path(source_path_text.replace('~', str(ctx['pathlib'].Path.home()))).expanduser()
        if not path.is_absolute():
            path = ctx['root'] / path
        path_exists = path.exists()
        if check_command:
            ctx['source_check_health']['with_check_count'] += 1
            ctx['source_check_health']['check_command_count'] += 1
            ctx['source_check_health']['check_command_source_ids'].append(source_id)
            if not check_command.startswith('rtk '):
                ctx['source_check_health']['non_rtk_check_ids'].append(source_id)
                ctx['source_check_health']['non_rtk_check_command_source_ids'].append(source_id)
                ctx['errors'].append(f'sources:{source_id} check must start with rtk')
        if no_check_reason:
            ctx['source_check_health']['with_no_check_reason_count'] += 1
            ctx['source_check_health']['no_check_reason_count'] += 1
            ctx['source_check_health']['no_check_reason_source_ids'].append(source_id)
        if not check_command and (not no_check_reason):
            ctx['source_check_health']['missing_check_or_reason_ids'].append(source_id)
            ctx['source_check_health']['missing_check_or_reason_source_ids'].append(source_id)
            ctx['errors'].append(f'sources:{source_id} missing no_check_reason for empty check')
        if check_command and no_check_reason:
            ctx['source_check_health']['both_check_and_no_check_reason_ids'].append(source_id)
            ctx['source_check_health']['both_check_and_no_check_reason_source_ids'].append(source_id)
            ctx['errors'].append(f'sources:{source_id} has both check and no_check_reason')
        if path_exists:
            ctx['source_check_health']['path_exists_count'] += 1
        else:
            ctx['source_check_health']['missing_source_path_ids'].append(source_id)
            ctx['source_check_health']['path_missing_source_ids'].append(source_id)
            ctx['warnings'].append(f"sources:{source.get('id')} path missing: {path}")
        ctx['source_check_health']['rows'].append({'source_id': source_id, 'has_check': bool(check_command), 'has_no_check_reason': bool(no_check_reason), 'check_contract_status': 'ok' if check_command or no_check_reason else 'missing-check-or-no-check-reason', 'execution_status': 'not-run', 'path_exists': path_exists, 'check_command': check_command, 'no_check_reason': no_check_reason, 'review_after': str(source.get('review_after', '')), 'review_after_stale': source_id in ctx['source_check_health']['stale_review_after_ids']})
    return {key: value for key, value in locals().items() if key != 'ctx'}

def _pre_before_3(ctx):
    ctx['source_check_health']['check_command_source_ids'] = sorted(ctx['source_check_health']['check_command_source_ids'])
    ctx['source_check_health']['no_check_reason_source_ids'] = sorted(ctx['source_check_health']['no_check_reason_source_ids'])
    ctx['source_check_health']['missing_check_or_reason_source_ids'] = sorted(ctx['source_check_health']['missing_check_or_reason_source_ids'])
    ctx['source_check_health']['both_check_and_no_check_reason_source_ids'] = sorted(ctx['source_check_health']['both_check_and_no_check_reason_source_ids'])
    ctx['source_check_health']['non_rtk_check_command_source_ids'] = sorted(ctx['source_check_health']['non_rtk_check_command_source_ids'])
    ctx['source_check_health']['path_missing_source_ids'] = sorted(ctx['source_check_health']['path_missing_source_ids'])
    ctx['source_check_health']['missing_check_or_reason_ids'] = sorted(ctx['source_check_health']['missing_check_or_reason_ids'])
    ctx['source_check_health']['both_check_and_no_check_reason_ids'] = sorted(ctx['source_check_health']['both_check_and_no_check_reason_ids'])
    ctx['source_check_health']['non_rtk_check_ids'] = sorted(ctx['source_check_health']['non_rtk_check_ids'])
    ctx['source_check_health']['missing_source_path_ids'] = sorted(ctx['source_check_health']['missing_source_path_ids'])
    ctx['source_check_health']['stale_review_after_ids'] = sorted(ctx['source_check_health']['stale_review_after_ids'])
    ctx['source_check_health']['stale_review_after_source_ids'] = sorted(ctx['source_check_health']['stale_review_after_source_ids'])
    ctx['source_check_health']['rows'] = sorted(ctx['source_check_health']['rows'], key=lambda row: row['source_id'])
    return {key: value for key, value in locals().items() if key != 'ctx'}

def run_pre_before(ctx):
    ctx.update(_pre_before_1(ctx))
    ctx.update(_pre_before_2(ctx))
    ctx.update(_pre_before_3(ctx))

def _pre_after_1(ctx):
    for source_id in sorted(ctx['source_ids']):
        source_dir = ctx['root'] / 'sources' / source_id
        missing_for_source = []
        for filename in ctx['SOURCE_CONTROL_REQUIRED_FILES']:
            required_path = source_dir / filename
            if required_path.exists():
                ctx['source_control_health']['present_file_count'] += 1
            else:
                rel_missing = str(required_path.relative_to(ctx['root']))
                missing_for_source.append(rel_missing)
                ctx['source_control_health']['missing_files'].append(rel_missing)
                ctx['errors'].append(f'source-control:{source_id} missing {rel_missing}')
        if missing_for_source:
            ctx['source_control_health']['missing_source_ids'].append(source_id)
        inventory_path = source_dir / 'inventory.jsonl'
        ctx['source_control_health']['rows_by_source'][source_id] = 0
        if not inventory_path.exists():
            continue
        for line_no, row in enumerate(ctx['load_jsonl'](inventory_path), 1):
            row_id = str(row.get('id', f'{source_id}:{line_no}'))
            ctx['source_control_health']['inventory_row_count'] += 1
            ctx['source_control_health']['rows_by_source'][source_id] += 1
            row_errors = []
            for field in ctx['SOURCE_CONTROL_REQUIRED_ROW_FIELDS']:
                if field not in row or row.get(field) in (None, ''):
                    row_errors.append(f'missing {field}')
            row_source_id = str(row.get('source_id', ''))
            if row_source_id and row_source_id != source_id:
                row_errors.append(f'source_id mismatch: {row_source_id}')
            object_type = str(row.get('object_type', ''))
            hub_disposition = str(row.get('hub_disposition', ''))
            status = str(row.get('status', ''))
            if object_type and object_type not in ctx['ALLOWED_SOURCE_CONTROL_OBJECT_TYPES']:
                row_errors.append(f'invalid object_type: {object_type}')
            if hub_disposition and hub_disposition not in ctx['ALLOWED_SOURCE_CONTROL_DISPOSITIONS']:
                row_errors.append(f'invalid hub_disposition: {hub_disposition}')
            if status and status not in ctx['ALLOWED_SOURCE_CONTROL_STATUSES']:
                row_errors.append(f'invalid status: {status}')
            checked_at = str(row.get('checked_at', ''))
            if checked_at:
                try:
                    ctx['dt'].date.fromisoformat(checked_at)
                except Exception:
                    row_errors.append(f'invalid checked_at: {checked_at}')
            target_path_text = str(row.get('target_path', '')).strip()
            if target_path_text:
                if ctx['pathlib'].Path(target_path_text).is_absolute() or target_path_text.startswith(('./', '../')):
                    row_errors.append(f'target_path must be repo-relative or source-local reference: {target_path_text}')
                elif not ctx['local_inventory_target_exists'](target_path_text):
                    row_errors.append(f'target_path missing: {target_path_text}')
            if object_type in ctx['SOURCE_CONTROL_RAW_OBJECT_TYPES'] and hub_disposition == 'copy-body':
                raw_row = {'source_id': source_id, 'row_id': row_id, 'object_type': object_type, 'hub_disposition': hub_disposition, 'target_path': target_path_text}
                ctx['source_control_health']['unsafe_raw_copy_rows'].append(raw_row)
                row_errors.append('raw/session/source-code/log/binary must not use copy-body')
            if row_errors:
                invalid = {'source_id': source_id, 'row_id': row_id, 'line': line_no, 'errors': row_errors}
                ctx['source_control_health']['invalid_inventory_rows'].append(invalid)
                for row_error in row_errors:
                    ctx['errors'].append(f'source-control:{source_id} inventory row {row_id} {row_error}')
    return {key: value for key, value in locals().items() if key != 'ctx'}

def _pre_after_2(ctx):
    owner_target_landing_path = ctx['root'] / ctx['owner_target_health']['landing_manifest']
    for row in ctx['load_jsonl'](owner_target_landing_path):
        worksheet_id = str(row.get('worksheet_id', '<unknown>'))
        owner_decision = str(row.get('owner_decision', ''))
        target_decision = str(row.get('target_decision', ''))
        target_status = 'skipped'
        target_path = ''
        skip_decisions = {'reference-only', 'no-migration', 'report-only-governance-candidate'}
        if owner_decision in {'reference-only', 'teamized-report-only'} or target_decision in skip_decisions:
            ctx['owner_target_health']['skipped_count'] += 1
        elif target_decision.startswith('domains/projects/') or target_decision.startswith('domains/personal/'):
            target_status = 'noncanonical-target-rejected'
            missing = {'worksheet_id': worksheet_id, 'target_decision': target_decision, 'mapped_target_path': '', 'reason': 'domains/projects and domains/personal are not canonical owner targets in the current contract'}
            ctx['owner_target_health']['missing_targets'].append(missing)
            ctx['errors'].append(f'owner-target:{worksheet_id} noncanonical target path rejected: {target_decision}')
        elif target_decision.startswith('projects/'):
            target_path = target_decision
        if target_path:
            ctx['owner_target_health']['checked_count'] += 1
            if (ctx['root'] / target_path).exists():
                ctx['owner_target_health']['present_count'] += 1
                target_status = 'present'
            else:
                target_status = 'missing'
                missing = {'worksheet_id': worksheet_id, 'target_decision': target_decision, 'mapped_target_path': target_path}
                ctx['owner_target_health']['missing_targets'].append(missing)
                ctx['errors'].append(f'owner-target:{worksheet_id} target path missing: {target_path}')
        ctx['owner_target_health']['rows'].append({'worksheet_id': worksheet_id, 'owner_decision': owner_decision, 'target_decision': target_decision, 'mapped_target_path': target_path, 'status': target_status})
    ctx['source_control_health']['missing_source_ids'] = sorted(set(ctx['source_control_health']['missing_source_ids']))
    ctx['source_control_health']['missing_files'] = sorted(ctx['source_control_health']['missing_files'])
    ctx['source_control_health']['status'] = 'fail' if ctx['source_control_health']['missing_files'] or ctx['source_control_health']['invalid_inventory_rows'] or ctx['source_control_health']['unsafe_raw_copy_rows'] else 'pass'
    ctx['owner_target_health']['status'] = 'fail' if ctx['owner_target_health']['missing_targets'] else 'pass'
    automation_safety_health = {'mode': 'registry-maintenance-runs', 'record_count': 0, 'checked_count': 0, 'unsafe_run_ids': [], 'missing_guard_run_ids': [], 'authorization_required_run_ids': [], 'rows': []}
    authorization_rows = ctx['load_jsonl'](ctx['root'] / 'registry' / 'authorizations.jsonl')
    authorization_ids = {str(row.get('authorization_id', '')) for row in authorization_rows if isinstance(row, dict) and str(row.get('authorization_id', '')).strip()}
    return {key: value for key, value in locals().items() if key != 'ctx'}

def _pre_after_3(ctx):
    for run in ctx['load_jsonl'](ctx['root'] / 'registry' / 'maintenance-runs.jsonl'):
        run_id = str(run.get('run_id', '<unknown>'))
        ctx['automation_safety_health']['record_count'] += 1
        if 'automation_id' not in run:
            ctx['automation_safety_health']['rows'].append({'run_id': run_id, 'automation_id': '', 'check_status': 'not-automation-record'})
            continue
        ctx['automation_safety_health']['checked_count'] += 1
        enabled = run.get('enabled')
        mode = str(run.get('mode', ''))
        authorization_id = str(run.get('authorization_id', '')).strip()
        writes_memory = run.get('writes_memory')
        writes_team_active_index = run.get('writes_team_active_index')
        no_memory_write_gate = str(run.get('no_memory_write_gate', '')).strip()
        row_errors = []
        if enabled is not False:
            row_errors.append('enabled must be false')
        if mode not in {'read-only', 'report-only', 'plan-only', 'local-commit', 'apply-with-review', 'forbidden'}:
            row_errors.append('mode must be read-only/report-only/plan-only/local-commit/apply-with-review/forbidden')
        if mode == 'apply-with-review' and authorization_id not in ctx['authorization_ids']:
            row_errors.append('apply-with-review requires registered authorization_id')
        if mode in {'read-only', 'report-only', 'plan-only', 'local-commit'}:
            if writes_memory is not False:
                row_errors.append('writes_memory must be false without authorization')
            if writes_team_active_index is not False:
                row_errors.append('writes_team_active_index must be false without authorization')
        if mode == 'apply-with-review' and (writes_memory is not False or writes_team_active_index is not False) and (authorization_id not in ctx['authorization_ids']):
            row_errors.append('write actions require registered authorization_id')
        if not no_memory_write_gate:
            row_errors.append('no_memory_write_gate is required')
        if row_errors:
            ctx['automation_safety_health']['unsafe_run_ids'].append(run_id)
            if 'no_memory_write_gate is required' in row_errors:
                ctx['automation_safety_health']['missing_guard_run_ids'].append(run_id)
            if any(('authorization_id' in row_error for row_error in row_errors)):
                ctx['automation_safety_health']['authorization_required_run_ids'].append(run_id)
            for row_error in row_errors:
                ctx['errors'].append(f'maintenance-runs:{run_id} {row_error}')
        ctx['automation_safety_health']['rows'].append({'run_id': run_id, 'automation_id': str(run.get('automation_id', '')), 'enabled': enabled, 'mode': mode, 'authorization_id': authorization_id, 'writes_memory': writes_memory, 'writes_team_active_index': writes_team_active_index, 'has_no_memory_write_gate': bool(no_memory_write_gate), 'check_status': 'pass' if not row_errors else 'fail', 'errors': row_errors})
    ctx['automation_safety_health']['unsafe_run_ids'] = sorted(ctx['automation_safety_health']['unsafe_run_ids'])
    ctx['automation_safety_health']['missing_guard_run_ids'] = sorted(ctx['automation_safety_health']['missing_guard_run_ids'])
    ctx['automation_safety_health']['authorization_required_run_ids'] = sorted(ctx['automation_safety_health']['authorization_required_run_ids'])
    authorization_health = {'record_count': len(ctx['authorization_rows']), 'active_count': 0, 'invalid_authorization_ids': [], 'rows': []}
    allowed_authorization_actions = {'owner-decision-landing', 'active-promotion', 'memory-write', 'source-project-write', 'automation-apply-with-review', 'external-publish', 'delete-or-prune', 'remote-git-write'}
    allowed_authorization_statuses = {'active', 'expired', 'revoked', 'used', 'superseded'}
    return {key: value for key, value in locals().items() if key != 'ctx'}

def _pre_after_4(ctx):
    for row in ctx['authorization_rows']:
        auth_id = str(row.get('authorization_id', '<unknown>'))
        row_errors = []
        for field in ['authorization_id', 'authorized_by', 'authorized_at', 'scope', 'allowed_actions', 'expires_at', 'evidence_refs', 'rollback_path', 'validation_commands', 'status']:
            if row.get(field) in ('', None, []):
                row_errors.append(f'missing {field}')
        for field in ['authorized_at', 'expires_at']:
            value = str(row.get(field, ''))
            if value:
                try:
                    ctx['dt'].date.fromisoformat(value)
                except Exception:
                    row_errors.append(f'invalid {field}')
        actions = row.get('allowed_actions', [])
        if not isinstance(actions, list) or not actions:
            row_errors.append('allowed_actions must be non-empty list')
        else:
            for action in actions:
                if action not in ctx['allowed_authorization_actions']:
                    row_errors.append(f'invalid allowed_action {action}')
        status = str(row.get('status', ''))
        if status and status not in ctx['allowed_authorization_statuses']:
            row_errors.append(f'invalid status {status}')
        if status == 'active':
            ctx['authorization_health']['active_count'] += 1
        if row_errors:
            ctx['authorization_health']['invalid_authorization_ids'].append(auth_id)
            for row_error in row_errors:
                ctx['errors'].append(f'authorizations:{auth_id} {row_error}')
        ctx['authorization_health']['rows'].append({'authorization_id': auth_id, 'status': status, 'allowed_actions': actions if isinstance(actions, list) else [], 'check_status': 'pass' if not row_errors else 'fail', 'errors': row_errors})
    ctx['authorization_health']['invalid_authorization_ids'] = sorted(ctx['authorization_health']['invalid_authorization_ids'])
    source_coverage_selection = {'pattern': 'artifacts/manifests/knowledge-hub-source-coverage-closeout-*.jsonl', 'required_filename': 'knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl', 'strategy': 'filename-yyyymmdd-sort-last', 'candidate_count': 0, 'candidates': [], 'dated_candidate_count': 0, 'dated_candidates': [], 'ignored_non_date_candidates': [], 'selected': '', 'reason_zh': '只按 knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl 的日期字段选择最新 closeout；非日期候选会被忽略并作为 warning 暴露，避免 future/latest 等文件名被静默选中。'}
    source_coverage_health = {'registered_source_count': len(ctx['source_ids']), 'row_count': 0, 'unique_source_count': 0, 'missing_source_ids': [], 'stale_source_ids': [], 'duplicate_source_ids': [], 'missing_required_field_rows': [], 'invalid_checked_at_rows': []}
    route_registry_health = {'schema_version': 1, 'status': 'not-run', 'mode': 'git-remote-first-route-registry', 'project_count': 0, 'group_count': 0, 'repository_count': 0, 'component_count': 0, 'route_count': 0, 'workspace_example_count': 0, 'forbidden_path_hits': [], 'missing_entry_paths': [], 'invalid_reference_count': 0, 'report_only_findings': ['workspace:// refs are logical adapters; local machine paths belong in untracked local/workspaces.json', '~/knowledge-hub, ~/codex and ~/.codex are the only allowed long-term local path conventions']}
    frontmatter_status_health = {'status': 'not-run', 'checked_item_count': 0, 'declared_status_count': 0, 'mismatch_count': 0, 'invalid_status_count': 0, 'owner_mismatch_count': 0, 'review_after_mismatch_count': 0, 'rows': [], 'notes_zh': 'registry/items.jsonl 是 status、owner、review_after 权威；正文 frontmatter 声明这些字段时只能镜像同一值。'}
    body_coverage_health = {'status': 'not-run', 'mode': 'exact-item-or-frozen-collection', 'coverage_registry': 'registry/body-coverage.json', 'checked_count': 0, 'exact_registered_count': 0, 'collection_covered_count': 0, 'missing_registry_count': 0, 'coverage_contract_status': 'not-run', 'coverage_errors': [], 'missing_registry': []}
    artifact_vault_health = {'status': 'not-run', 'manifest': 'artifacts/manifests/patent-disclosure-artifact-ref-20260619.jsonl', 'vault_root': 'artifacts/vault/patent-disclosure', 'row_count': 0, 'expected_row_count': 181, 'required_present_count': 0, 'external_reference_only_count': 0, 'missing_required_count': 0, 'hash_mismatch_count': 0, 'size_mismatch_count': 0, 'extra_file_count': 0, 'duplicate_id_count': 0, 'duplicate_path_count': 0, 'invalid_identity_count': 0, 'symlink_count': 0, 'errors': []}
    return {key: value for key, value in locals().items() if key != 'ctx'}

def run_pre_after(ctx):
    ctx.update(_pre_after_1(ctx))
    ctx.update(_pre_after_2(ctx))
    ctx.update(_pre_after_3(ctx))
    ctx.update(_pre_after_4(ctx))
