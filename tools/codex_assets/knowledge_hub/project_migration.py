"""Exact-plan project consolidation with content preservation and recoverable writes.

This is identity maintenance, never owner approval or lifecycle promotion.
Runtime code is maintained separately: a Provider call must not replace its own
executable source set. The operation refuses any such remaining references.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess

from .common import KnowledgeHubError, encode_jsonl, load_json, load_jsonl, load_markdown, pretty_json, render_markdown
from .provider_subjects import authorize, digest, principal, read_guard, subject
from .remote_identity import parse_remote
from .store import RepositoryTransaction


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _paths(root):
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others',
                             '--exclude-standard', '-z'], capture_output=True, check=True)
    paths = set(filter(None, result.stdout.decode().split('\0')))
    for name in ('local/provider-bindings.json', 'local/provider-principal.json'):
        if (root / name).is_file():
            paths.add(name)
    return sorted(paths)


def _dedupe(value):
    if isinstance(value, dict):
        return {key: _dedupe(v) for key, v in value.items()}
    if isinstance(value, list):
        result = []
        for entry in value:
            entry = _dedupe(entry)
            if entry not in result:
                result.append(entry)
        return result
    return value



def _migration_inputs(root, source, target, remote_url):
    source, target = subject(source), subject('project:' + target)
    if source['type'] != 'project' or source == target:
        raise KnowledgeHubError('SCHEMA_INVALID')
    old, new = source['id'], target['id']
    old_prefix, new_prefix = 'projects/' + old + '/', 'projects/' + new + '/'
    projects = load_json(root / 'registry/projects.json')
    source_rows = [r for r in projects['projects'] if r['id'] == old]
    target_rows = [r for r in projects['projects'] if r['id'] == new]
    if len(source_rows) != 1 or len(target_rows) != 1:
        raise KnowledgeHubError('PROJECT_UNREGISTERED')
    source_project, target_project = source_rows[0], target_rows[0]
    remote = parse_remote(remote_url)
    if not remote:
        raise KnowledgeHubError('SOURCE_REJECTED')
    original_items = load_jsonl(root / 'registry/items.jsonl')
    source_items = [r for r in original_items if r['path'].startswith(old_prefix)]
    # The repository contract becomes canonical. Preserve the target's earlier
    # knowledge-project contract separately, retaining both evidence histories.
    readiness = next((r for r in source_items if r['path'] == old_prefix + 'validation/project-readiness.md'), None)
    replacements = []
    if readiness and (root / (new_prefix + 'validation/project-readiness.md')).is_file():
        replacements += [(new_prefix + 'validation/project-readiness.md', new_prefix + 'validation/knowledge-project-readiness.md')]
        if readiness['id'].replace(old, new) in {r['id'] for r in original_items if r['path'].startswith(new_prefix)}:
            replacements.append((readiness['id'], new + '-repository-readiness'))
    replacements += [('robot/' + old.replace('-', '_'), remote['repository_path']),
                     (old.replace('-', '_') + '_rel', new),
                     (old.replace('-', '_') + '_dev', new),
                     (old.replace('-', '_').upper(), new.replace('-', '_').upper()),
                     (old.upper(), new.upper()),
                     (old, new), (old.replace('-', '_'), new),
                     (source_project['name'], target_project['name'])]

    return source, target, source_project, target_project, remote, original_items, source_items, readiness, replacements


def _convert_value(value, convert):
    if isinstance(value, str):
        return convert(value)
    if isinstance(value, dict):
        return {_convert_value(key, convert): _convert_value(entry, convert) for key, entry in value.items()}
    if isinstance(value, list):
        return [_convert_value(entry, convert) for entry in value]
    return value


def _virtual_files(root, old, old_prefix, new_prefix, convert):
    original, virtual, moves = {}, {}, []
    names = _paths(root)
    for path in (root / 'projects' / old).rglob('*'):
        if path.is_symlink() or (path.is_file() and str(path.relative_to(root)) not in names):
            raise KnowledgeHubError('SOURCE_INVENTORY_INCOMPLETE')
    runtime_files = set(load_json(root / 'registry/provider-runtime-files.json', {}).get('files', {}))
    for name in names:
        path = root / name
        if not path.exists():
            continue  # Preserve pre-existing user deletions.
        if path.is_symlink():
            if old in name:
                raise KnowledgeHubError('SOURCE_REJECTED') from None
            continue
        if not path.is_file():
            continue
        raw = path.read_bytes()
        original[name] = raw
        try:
            text = raw.decode('utf-8')
        except UnicodeError:
            if name.startswith(old_prefix):
                raise KnowledgeHubError('SOURCE_REJECTED') from None
            virtual[name] = raw
            continue
        transformed = convert(text)
        destination = convert(name)
        if (name.startswith('tools/') or name in runtime_files) and (transformed != text or destination != name):
            raise KnowledgeHubError('RUNTIME_MAINTENANCE_REQUIRED')
        if destination in virtual:
            if destination == new_prefix + 'README.md' and name in {old_prefix + 'README.md', new_prefix + 'README.md'}:
                if name.startswith(old_prefix):
                    moves.append({'source': name, 'target': destination, 'before_sha256': _sha(raw),
                                  'normalized_sha256': _sha(transformed.encode())})
                continue
            raise KnowledgeHubError('ROUTE_CONFLICT')
        virtual[destination] = transformed.encode()
        if destination != name:
            moves.append({'source': name, 'target': destination, 'before_sha256': _sha(raw),
                          'normalized_sha256': _sha(transformed.encode())})

    return original, virtual, moves


def _merge_entry_documents(original, virtual, old_prefix, new_prefix, readiness, convert):
    # Handle only the declared entry collision. Other duplicate destinations
    # are rejected before any write, including byte-identical documents.
    entry = new_prefix + 'README.md'
    old_entry = old_prefix + 'README.md'
    if old_entry in original and entry in original:
        source_body = convert(original[old_entry].decode())
        if source_body.startswith('---\n'):
            source_body = source_body.split('\n---\n', 1)[1]
        # Duplicate managed navigation contains no unique knowledge; retain one
        # canonical block and an explicit link to the preserved prior contract.
        source_body = re.sub(r'<!-- knowledge-hub-project-readiness:start -->.*?<!-- knowledge-hub-project-readiness:end -->', '', source_body, flags=re.S)
        virtual[entry] = (convert(original[entry].decode()).rstrip() +
                          '\n\n## 仓库知识与历史适用范围\n\n' + source_body.strip() + '\n').encode()
    if readiness:
        entry_text = virtual[entry].decode()
        contract_path = convert(readiness['path'])[len(new_prefix):]
        entry_text += '\n- [仓库工程 evidence contract](' + contract_path + ')\n'
        if new_prefix + 'validation/knowledge-project-readiness.md' in virtual:
            entry_text += '- [知识项目阶段 evidence contract](validation/knowledge-project-readiness.md)\n'
        virtual[entry] = entry_text.encode()



def _merge_identity_catalogs(root, original, virtual, source, source_project, target_project, old, new, remote, convert):
    def get(name):
        return json.loads(virtual[name])

    def put(name, value):
        virtual[name] = (pretty_json(value) + '\n').encode()

    catalog = get('registry/projects.json')
    merged = next(r for r in catalog['projects'] if r['id'] == new)
    # Source row precedes target in some registries. Retain target entry metadata
    # while adopting the actual repository boundary and source evidence profile.
    merged = json.loads(convert(json.dumps(target_project)))
    merged.update(type='git-repository', repo_boundary='primary',
                  evidence_profile=source_project.get('evidence_profile', 'embedded-target'),
                  groups=sorted(set(source_project.get('groups', []) + target_project.get('groups', []))))
    catalog['projects'] = [r for r in catalog['projects'] if r['id'] != new] + [merged]
    put('registry/projects.json', catalog)
    routes = get('registry/project-routes.json')
    original_routes = load_json(root / 'registry/project-routes.json')['routes']
    src_route = next(r for r in original_routes if r['project_id'] == old)
    dst_route = next(r for r in original_routes if r['project_id'] == new)
    route = json.loads(convert(json.dumps(dst_route)))
    route.update(repo_refs=[new], workspace_refs=['workspace://' + new], aliases=[new],
                 route_key_policy='git-remote-first', group_id=src_route.get('group_id', ''),
                 default_source_ids=sorted(set(src_route.get('default_source_ids', []) + dst_route.get('default_source_ids', []))))
    routes['routes'] = [r for r in routes['routes'] if r['project_id'] != new] + [route]
    put('registry/project-routes.json', routes)
    repositories = get('registry/repositories.json')
    repo_rows = [r for r in repositories['repositories'] if r.get('repo_id') == new]
    if len(repo_rows) != 1:
        raise KnowledgeHubError('ROUTE_CONFLICT')
    repo_rows[0].update(project_id=new, remote_key=remote, workspace_ref='workspace://' + new,
                        aliases=[], groups=merged['groups'])
    project_groups = {r['id']: r.get('groups', []) for r in catalog['projects']}
    for row in repositories['repositories']:
        if 'groups' not in row:
            row['groups'] = project_groups.get(row.get('project_id'), [])
    put('registry/repositories.json', repositories)
    # Never transfer an old project's active write grants to the new identity.
    grant_path = 'registry/provider-grants.jsonl'
    if grant_path in original:
        grants = []
        for raw in original[grant_path].decode().splitlines():
            if not raw.strip():
                continue
            before = json.loads(raw)
            after = json.loads(convert(raw))
            if before.get('subject_ref') == source:
                after['status'] = 'revoked'
            grants.append(after)
        virtual[grant_path] = encode_jsonl(grants).encode()



def _normalize_review_authorities(original, virtual, convert):
    from .delegated_content_review import LEDGER
    review_history, invalid_authorities = [], set()
    if LEDGER in original:
        remaining = []
        for line in original[LEDGER].decode().splitlines():
            if not line.strip():
                continue
            authority = json.loads(line)
            if convert(line) != line:
                invalid_authorities.add(authority['authorization_id'])
                review_history.append({'kind': 'prior-delegated-authority', 'original_sha256': _sha(line.encode()),
                                       'normalized_record': json.loads(convert(line)), 'historical_validation_verified': False})
            else:
                remaining.append(authority)
        virtual[LEDGER] = encode_jsonl(remaining).encode()
    return review_history, invalid_authorities


def _invalidate_changed_reviews(root, original_items, items, original, virtual, convert, review_history, invalid_authorities):
    from .delegated_content_review import FIELD
    from .model import merge_frontmatter_mirror
    original_by_normalized_id = {convert(r['id']): r for r in original_items}
    for item in items:
        before_item = original_by_normalized_id[item['id']]
        raw_before = original.get(before_item['path'])
        raw_after = virtual.get(item['path'])
        changed = raw_before != raw_after or before_item != item
        credential = item.get(FIELD)
        invalid_credential = credential and (changed or credential.get('authorization_id') in invalid_authorities)
        stale_human = changed and bool(item.get('human_review_content_sha256'))
        if not invalid_credential and not stale_human:
            continue
        if item.get('status') == 'active':
            raise KnowledgeHubError('ACTIVE_REVIEW_REVALIDATION_REQUIRED')
        review_history.append({'kind': 'prior-content-review', 'item_id': item['id'],
                               'original_content_sha256': _sha(raw_before) if raw_before else None,
                               'normalized_review': {key: value for key, value in item.items()
                                                     if key.startswith('human_review') or key == FIELD},
                               'historical_validation_verified': False})
        item.pop(FIELD, None)
        if stale_human:
            item['human_review_decision'] = 'defer'
        item['content_review_status'] = 'pending'
        item['review_status'] = 'identity-migration-pending-review'
        metadata, body = load_markdown(root / before_item['path'])
        # Normalize the parsed metadata and body without inventing any review.
        metadata = _convert_value(metadata, convert)
        metadata.pop(FIELD, None)
        metadata = merge_frontmatter_mirror(metadata, item)
        if stale_human:
            metadata['human_review_decision'] = 'defer'
        metadata['review_status'] = item['review_status']
        virtual[item['path']] = render_markdown(metadata, convert(body)).encode()


def _plan_bytes(name, raw):
    # The exact approval is issued after dry-run. Exclude only migration
    # approval records from the proposal identity to avoid a recursive hash;
    # the transaction still snapshots and verifies their actual bytes.
    if name == 'registry/authorizations.jsonl':
        rows = []
        for line in raw.decode().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            try:
                scope = json.loads(row.get('scope', ''))
            except (ValueError, TypeError):
                scope = {}
            if isinstance(scope, dict) and scope.get('action') == 'migrate-project':
                continue
            rows.append(row)
        return encode_jsonl(rows).encode()
    return raw


def _append_current_proofs(items, original_items, original, virtual, writes, convert, expected):
    op_path = 'registry/provider-operations.jsonl'
    op_rows = [json.loads(line) for line in virtual.get(op_path, b'').decode().splitlines() if line.strip()]
    latest = {r['item_id']: r for r in op_rows}
    proof_count = 0
    for item in items:
        if item['id'] not in latest or item['path'] not in writes:
            continue
        before_item = next((r for r in original_items if convert(r['id']) == item['id']), None)
        if not before_item or before_item['path'] not in original:
            raise KnowledgeHubError('CONTENT_DRIFT')
        proof = latest[item['id']]
        before_hash, after_hash = _sha(original[before_item['path']]), _sha(virtual[item['path']])
        if proof['content_sha256'] != before_hash:
            raise KnowledgeHubError('CONTENT_DRIFT')
        op_id = digest([expected, item['id'], before_hash, after_hash])
        op_rows.append(dict(proof, operation_id=op_id, request_sha256=op_id, action='metadata',
                            before_content_sha256=before_hash, content_sha256=after_hash,
                            transaction_id='project-migration-' + expected[:24],
                            historical_validation_verified=False,
                            verification_basis={'kind': 'metadata-transaction', 'proof_ref': expected}))
        proof_count += 1
    if proof_count:
        writes[op_path] = encode_jsonl(op_rows).encode()
        virtual[op_path] = writes[op_path]
    return proof_count


def build_plan(root, source, target, remote_url):
    """Return virtual final bytes, complete input hashes, and a content-bound plan."""
    (source, target, source_project, target_project, remote, original_items,
     source_items, readiness, replacements) = _migration_inputs(root, source, target, remote_url)
    old, new = source['id'], target['id']
    old_prefix, new_prefix = 'projects/' + old + '/', 'projects/' + new + '/'
    def convert(text):
        for before, after in replacements:
            if before:
                text = text.replace(before, after)
        return text

    original, virtual, moves = _virtual_files(root, old, old_prefix, new_prefix, convert)
    _merge_entry_documents(original, virtual, old_prefix, new_prefix, readiness, convert)
    _merge_identity_catalogs(root, original, virtual, source, source_project, target_project, old, new, remote, convert)
    item_path = 'registry/items.jsonl'
    items = [json.loads(line) for line in virtual[item_path].decode().splitlines() if line.strip()]
    if len({r['id'] for r in items}) != len(items) or len({r['path'] for r in items}) != len(items):
        raise KnowledgeHubError('ROUTE_CONFLICT')
    if any(r['path'] not in virtual for r in items if r['path'].startswith(new_prefix)):
        raise KnowledgeHubError('CONTENT_DRIFT')
    # Content-bound review is not transferable approval. Seal changed review
    # authority records as provenance and detach their current credentials.
    review_history, invalid_authorities = _normalize_review_authorities(original, virtual, convert)
    _invalidate_changed_reviews(root, original_items, items, original, virtual, convert, review_history, invalid_authorities)
    virtual[item_path] = encode_jsonl(items).encode()
    # Normalize duplicate memberships without combining unrelated objects.
    for name in ('registry/project-groups.json', 'registry/provider-workspaces.json', 'local/provider-bindings.json'):
        if name in virtual:
            virtual[name] = (pretty_json(_dedupe(json.loads(virtual[name]))) + '\n').encode()
    # A manifest binds all initial files, deletions and exact output bytes.
    inputs = {name: _sha(raw) for name, raw in original.items()}
    writes = {name: raw for name, raw in virtual.items() if original.get(name) != raw}
    deletes = {name: _sha(raw) for name, raw in original.items() if name not in virtual}
    public = {'protocol': 'project-migration/v1', 'source_subject_sha256': digest(source),
              'subject_ref': target, 'remote_key': remote,
              'inputs_sha256': digest({p: _sha(_plan_bytes(p, raw)) for p, raw in original.items()}),
              'writes': {p: _sha(_plan_bytes(p, raw)) for p, raw in writes.items()},
              'deletes_sha256': digest(deletes), 'source_file_count': sum(p.startswith(old_prefix) for p in original),
              'source_item_count': len(source_items), 'moves': [dict(source_path_sha256=_sha(r['source'].encode()),
                    target=r['target'], before_sha256=r['before_sha256'], normalized_sha256=r['normalized_sha256']) for r in moves]}
    expected = digest(public)
    # Append fresh current-byte proofs; old hashes remain historical hashes.
    proof_count = _append_current_proofs(items, original_items, original, virtual, writes, convert, expected)
    remnants = [name for name, raw in virtual.items()
                if old.encode() in raw.lower() or old.replace('-', '_').encode() in raw.lower() or old in name.lower()]
    if remnants:
        raise KnowledgeHubError('CONTENT_DRIFT')
    public.update(expected_hash=expected, write_count=len(writes), delete_count=len(deletes), provider_proofs=proof_count,
                  prior_review_evidence=review_history,
                  before_writes={p: inputs[p] for p in writes if p in inputs},
                  result_writes={p: _sha(raw) for p, raw in writes.items()})
    return public, inputs, writes, deletes, virtual


def migrate(root, args):
    source = subject(args.from_subject)
    target = subject('project:' + args.project)
    actor = principal(root)
    authorize(root, 'read', source)
    authorize(root, 'read', target)
    if re.fullmatch(r'[a-f0-9]{64}', args.expected_content_sha256 or ''):
        report_path = root / ('artifacts/manifests/project-migration-' + args.expected_content_sha256 + '.json')
        if report_path.is_file():
            with read_guard(root):
                recorded = load_json(report_path)
                if (recorded.get('source_subject_sha256') != digest(source)
                        or recorded.get('subject_ref') != target
                        or recorded.get('remote_key') != parse_remote(args.remote_url)
                        or (root / 'projects' / source['id']).exists()
                        or any(not (root / p).is_file() or _sha((root / p).read_bytes()) != value
                               for p, value in recorded.get('result_writes', {}).items())):
                    raise KnowledgeHubError('CONTENT_DRIFT')
            return {'schema_version': 'knowledge-provider.project-migration/v1', 'status': 'ALREADY_MIGRATED',
                    'persisted': True, 'write_performed': False, 'read_only': True, 'subject_ref': target,
                    'expected_hash': args.expected_content_sha256,
                    **{key: recorded[key] for key in ('source_file_count', 'source_item_count', 'write_count', 'delete_count', 'provider_proofs')},
                    'active_promoted': False, 'owner_review_performed': False,
                    'manifest_ref': str(report_path.relative_to(root))}
    with read_guard(root):
        plan, inputs, writes, deletes, virtual = build_plan(root, args.from_subject, args.project, args.remote_url)
    receipt = {'schema_version': 'knowledge-provider.project-migration/v1', 'status': 'PLANNED',
               'persisted': False, 'write_performed': False, 'read_only': True,
               'subject_ref': target, 'expected_hash': plan['expected_hash'],
               'source_file_count': plan['source_file_count'], 'source_item_count': plan['source_item_count'],
               'write_count': len(writes), 'delete_count': len(deletes), 'provider_proofs': plan['provider_proofs'],
               'active_promoted': False, 'owner_review_performed': False}
    if not args.apply:
        return receipt
    if args.expected_content_sha256 != plan['expected_hash']:
        raise KnowledgeHubError('CONTENT_DRIFT')
    from .provider_subjects import policy
    from .provider_grants import _require_exact_scope
    if 'assign' not in policy(root)['actions']:
        raise KnowledgeHubError('POLICY_DENIED')
    exact_scope = {'actor': actor, 'action': 'migrate-project',
                   'source_subject_sha256': digest(source), 'subject_ref': target,
                   'remote_key': plan['remote_key'], 'expected_hash': plan['expected_hash'],
                   'visibility_change': False}
    _require_exact_scope(root, args.authorization_id, exact_scope)
    from .provider_grants import attested_request
    request_path = pathlib.Path(args.declaration_file)
    raw = request_path.read_text()
    if not re.search(r'迁移|migrat', raw, re.I):
        raise KnowledgeHubError('DECLARATION_MISMATCH')
    request_sha, attestation = attested_request(raw, request_path)
    tx = RepositoryTransaction(root, transaction_id='project-migration-' + plan['expected_hash'][:24], expected_inputs=inputs)
    for name, content in writes.items():
        tx.add_bytes(name, content)
    for name, before in deletes.items():
        tx.add_delete(name, before)
    report = dict(plan, principal_id=actor, request_sha256=request_sha, intake_attestation_sha256=attestation,
                  authorization_ref=args.authorization_id,
                  historical_validation_verified=False, active_promoted=False, owner_review_performed=False)
    report_name = 'artifacts/manifests/project-migration-' + plan['expected_hash'] + '.json'
    tx.add_text(report_name, pretty_json(report) + '\n')
    args._commit_started = True
    result = tx.apply()
    for name, content in writes.items():
        if (root / name).read_bytes() != content:
            raise KnowledgeHubError('CONTENT_DRIFT')
    if any((root / name).exists() for name in deletes):
        raise KnowledgeHubError('CONTENT_DRIFT')
    # Empty legacy directories carry no content and are removed only after all
    # file proofs pass. An unexpected file prevents rmdir rather than being lost.
    old_root = root / 'projects' / source['id']
    if old_root.exists():
        for path in sorted(old_root.rglob('*'), key=lambda p: len(p.parts), reverse=True):
            if path.is_dir():
                path.rmdir()
        old_root.rmdir()
    receipt.update(status='MIGRATED', persisted=True, write_performed=True, read_only=False,
                   transaction_id=result.transaction_id, manifest_ref=report_name)
    return receipt
