def _body_coverage_1(ctx):
    body_coverage_command = ['rtk', 'bash', 'tools/knowledge-orphan-files.sh', '--all', '--strict', '--json', '--limit', '50']
    body_coverage_run = ctx['subprocess'].run(body_coverage_command, cwd=ctx['root'], text=True, stdout=ctx['subprocess'].PIPE, stderr=ctx['subprocess'].PIPE)
    try:
        body_coverage_payload = ctx['json'].loads(body_coverage_run.stdout)
    except Exception:
        body_coverage_payload = {}
        ctx['errors'].append(f"body-coverage:unable to parse orphan helper JSON: {ctx['exc']}")
    if body_coverage_payload:
        ctx['body_coverage_health'].update(body_coverage_payload)
    if body_coverage_run.returncode != 0:
        if body_coverage_payload.get('coverage_errors'):
            for message in body_coverage_payload.get('coverage_errors', [])[:10]:
                ctx['errors'].append(f'body-coverage:{message}')
        if body_coverage_payload.get('missing_registry'):
            for path in body_coverage_payload.get('missing_registry', [])[:10]:
                ctx['errors'].append(f'body-coverage:missing exact or collection coverage: {path}')
        if not body_coverage_payload.get('coverage_errors') and (not body_coverage_payload.get('missing_registry')):
            ctx['errors'].append('body-coverage:strict helper failed without structured findings: ' + body_coverage_run.stderr.strip()[:300])
    return {key: value for key, value in locals().items() if key != 'ctx'}

def run_body_coverage(ctx):
    ctx.update(_body_coverage_1(ctx))

def _index_security_1(ctx):
    decision_rows = ctx['load_jsonl'](ctx['root'] / 'registry' / 'decisions.jsonl')
    registry_decision_ids = set()
    for decision in decision_rows:
        decision_id = str(decision.get('decision_id', '')).strip()
        if not decision_id:
            ctx['errors'].append('decisions: missing decision_id')
            continue
        if decision_id in registry_decision_ids:
            ctx['errors'].append(f'decisions:{decision_id} duplicate decision_id')
        registry_decision_ids.add(decision_id)
    by_decision_path = ctx['root'] / 'indexes' / 'by-decision.md'
    by_decision_counts = {}
    if not by_decision_path.exists():
        ctx['errors'].append('index missing: indexes/by-decision.md')
    else:
        for ref in ctx['re'].findall('`([^`]+)`', by_decision_path.read_text()):
            if ref in registry_decision_ids:
                by_decision_counts[ref] = by_decision_counts.get(ref, 0) + 1
    for decision_id in sorted(registry_decision_ids):
        count = by_decision_counts.get(decision_id, 0)
        if count == 0:
            ctx['errors'].append(f'index:indexes/by-decision.md missing registry decision {decision_id}')
        elif count > 1:
            ctx['errors'].append(f'index:indexes/by-decision.md duplicate registry decision {decision_id} ({count}x)')
    index_requirements = {'indexes/by-owner.md': 'owner', 'indexes/by-review-date.md': 'review_after', 'indexes/by-status.md': 'status'}
    for rel_index, field in index_requirements.items():
        index_path = ctx['root'] / rel_index
        if rel_index == 'indexes/by-status.md':
            status_seen = {status: ctx['status_bucket_ids'](index_path, status) for status in ['draft', 'active', 'reviewing', 'archived', 'superseded', 'rejected', 'personal']}
            seen = set().union(*status_seen.values())
        else:
            status_seen = {}
            seen = ctx['indexed_ids'](index_path)
        for item in ctx['items']:
            item_id = item.get('id')
            if item_id and item_id not in seen:
                ctx['errors'].append(f"index:{rel_index} missing item {item_id} ({field}={item.get(field, '<missing>')})")
            if rel_index == 'indexes/by-status.md' and item_id:
                expected_status = item.get('status', '')
                if expected_status in status_seen and item_id in seen and (item_id not in status_seen[expected_status]):
                    found_buckets = [status for status, bucket_ids in status_seen.items() if item_id in bucket_ids]
                    ctx['errors'].append(f"index:{rel_index} item {item_id} in wrong status bucket (registry status={expected_status}, buckets={','.join(found_buckets) or '<none>'})")
        stale_seen = seen if rel_index == 'indexes/by-status.md' else seen
        for indexed_id in sorted(stale_seen):
            if indexed_id not in ctx['ids']:
                ctx['errors'].append(f'index:{rel_index} stale item reference {indexed_id}')
        duplicate_counts = ctx['item_ref_counts'](ctx['root'] / rel_index, canonical_status_only=rel_index == 'indexes/by-status.md')
        for indexed_id, count in sorted(duplicate_counts.items()):
            if count > 1:
                ctx['errors'].append(f'index:{rel_index} duplicate item reference {indexed_id} ({count}x)')
    items_by_id = {item.get('id'): item for item in ctx['items'] if item.get('id')}
    return {key: value for key, value in locals().items() if key != 'ctx'}

def _index_security_2(ctx):
    if ctx['args'].explain:
        explain_id = ctx['args'].explain
        explained_item = ctx['items_by_id'].get(explain_id)
        explain = {'id': explain_id, 'found': bool(explained_item), 'registry': {}, 'indexes': {}, 'maintenance_hints': []}
        if not explained_item:
            ctx['errors'].append(f'explain:{explain_id} item not found')
        else:
            explained_path = ctx['pathlib'].Path(str(explained_item.get('path', '')))
            explained_path_exists = bool(str(explained_item.get('path', ''))) and (not explained_path.is_absolute()) and (ctx['root'] / explained_path).exists()
            validation_refs = explained_item.get('validation_refs', [])
            if not isinstance(validation_refs, list):
                validation_refs = []
            explain['registry'] = {'title': explained_item.get('title', ''), 'kind': explained_item.get('kind', ''), 'domain': explained_item.get('domain', ''), 'path': explained_item.get('path', ''), 'path_exists': explained_path_exists, 'scope': explained_item.get('scope', ''), 'visibility': explained_item.get('visibility', ''), 'status': explained_item.get('status', ''), 'owner': explained_item.get('owner', ''), 'review_after': explained_item.get('review_after', ''), 'promotion': explained_item.get('promotion', ''), 'tags_count': len(explained_item.get('tags', [])) if isinstance(explained_item.get('tags'), list) else 0, 'validation_refs_count': len(validation_refs)}
            for rel_index in ['indexes/by-owner.md', 'indexes/by-review-date.md', 'indexes/by-status.md']:
                canonical_only = rel_index == 'indexes/by-status.md'
                ref_count = ctx['item_ref_counts'](ctx['root'] / rel_index, canonical_status_only=canonical_only).get(explain_id, 0)
                if ref_count == 0:
                    index_status = 'missing'
                    explain['maintenance_hints'].append(f'{rel_index}: add `{explain_id}` to the appropriate section')
                elif ref_count == 1:
                    index_status = 'ok'
                else:
                    index_status = 'duplicate'
                    explain['maintenance_hints'].append(f'{rel_index}: keep exactly one canonical `{explain_id}` reference')
                explain['indexes'][rel_index] = {'reference_count': ref_count, 'status': index_status}
            status_index_path = ctx['root'] / 'indexes' / 'by-status.md'
            for bucket in ['active', 'reviewing', 'archived']:
                if explain_id in ctx['status_bucket_ids'](status_index_path, bucket):
                    explain['indexes']['indexes/by-status.md']['bucket'] = bucket
                    break
            if not explained_path_exists:
                explain['maintenance_hints'].append('registry path is missing or absolute; keep item path repo-relative and existing')
            if explained_item.get('status') in {'active', 'reviewing'} and (not validation_refs):
                explain['maintenance_hints'].append('active/reviewing item needs non-empty validation_refs')
            if not explain['maintenance_hints']:
                explain['maintenance_hints'].append('no immediate manual maintenance action detected for this item')
    active_index_ids = ctx['status_bucket_ids'](ctx['root'] / 'indexes' / 'by-status.md', 'active')
    for indexed_id in sorted(active_index_ids):
        item = ctx['items_by_id'].get(indexed_id)
        if not item:
            continue
        if item.get('visibility') == 'personal-local' or str(item.get('path', '')).startswith('notes/personal/'):
            ctx['errors'].append(f'index:indexes/by-status.md active bucket references personal-local item {indexed_id}')
    for index_path in sorted((ctx['root'] / 'indexes').glob('*.md')):
        text = index_path.read_text()
        for ref in sorted(set(ctx['re'].findall('`([^`]+)`', text))):
            if not (ref.startswith(ctx['local_path_prefixes']) or ref in {'README.md', 'AGENTS.md'}):
                continue
            if '*' in ref:
                if not list(ctx['root'].glob(ref)):
                    ctx['errors'].append(f"index:{index_path.relative_to(ctx['root'])} missing local glob reference {ref}")
            elif not (ctx['root'] / ref).exists():
                ctx['errors'].append(f"index:{index_path.relative_to(ctx['root'])} missing local path reference {ref}")
    scan_roots = [ctx['root'] / 'domains', ctx['root'] / 'notes', ctx['root'] / 'projects', ctx['root'] / 'sources', ctx['root'] / 'registry', ctx['root'] / 'governance', ctx['root'] / 'templates', ctx['root'] / 'indexes', ctx['root'] / 'tools', ctx['root'] / 'docs', ctx['root'] / 'README.md', ctx['root'] / 'AGENTS.md', ctx['root'] / 'artifacts' / 'manifests']
    forbidden_path_prefixes = ctx['user_path_prefixes']()
    return {key: value for key, value in locals().items() if key != 'ctx'}

def _index_security_3(ctx):
    for path in ctx['iter_text_files'](ctx['scan_roots']):
        try:
            text = path.read_text(errors='ignore')
        except Exception:
            ctx['warnings'].append(f"{ctx['display_path'](path)}: unreadable: {ctx['exc']}")
            continue
        for prefix in ctx['forbidden_path_prefixes']:
            if prefix in text:
                ctx['errors'].append(f"user-path-boundary:{path.relative_to(ctx['root'])}")
                break
        if ctx['scan_secret_text'](text):
            ctx['errors'].append(f"secret-pattern:{path.relative_to(ctx['root'])}")
    return {key: value for key, value in locals().items() if key != 'ctx'}

def run_index_security(ctx):
    ctx.update(_index_security_1(ctx))
    ctx.update(_index_security_2(ctx))
    ctx.update(_index_security_3(ctx))
