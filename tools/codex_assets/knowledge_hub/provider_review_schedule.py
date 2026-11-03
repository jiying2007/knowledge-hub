"""Mechanically apply an explicitly approved owner cycle; never approve content.

This is a separate, hash-bound mode of maintain-content. Generic maintenance
still cannot change review dates or explicitly edit active items. The operator
supplies the real human statements, as with review_attestation; this module
checks bindings, not the real-world identity of the speaker. Runtime request
attestation authenticates only the original execution request, independently.
"""
from __future__ import annotations

import collections
import copy
import datetime as dt
import os
import pathlib
import re

from .common import (KnowledgeHubError, encode_jsonl, load_jsonl, load_markdown,
                     pretty_json, render_markdown, resolve_inside)
from .indexing import CORE_INDEXES, update_core_indexes
from .model import validate_item
from .provider_operations import operations, safe_text, verify_current_item
from .provider_subjects import authorize, digest, item_subject, principal, read_guard, policy
from .provider_maintenance import sha
from .store import RepositoryTransaction

APPLICATION = 'knowledge-owner-cycle-application/v1'
AUTHORIZATION = 'knowledge-owner-cycle-authorization/v1'
PROPOSAL = 'knowledge-owner-review-scheduling-proposal/v1'
FIELDS = {'review_after', 'updated_at', 'manual_validation_pending',
          'content_review_status', 'review_status'}


def checked_confirmation(proposal, confirmation, thread):
    from .review_attestation import _validate_identity
    required = {'schema_version', 'confirmation_token', 'confirmed_by', 'authorized_owners',
                'decision_statement', 'identity_statement', 'source_ref', 'decision_packet_id',
                'decision_packet_sha256', 'execution_authorized', 'content_approval_performed'}
    if (not isinstance(confirmation, dict) or set(confirmation) != required
            or confirmation['schema_version'] != 'knowledge-owner-cycle-confirmation/v1'
            or confirmation['execution_authorized'] is not True
            or confirmation['content_approval_performed'] is not False):
        raise KnowledgeHubError('AUTHORIZATION_REQUIRED')
    who = _validate_identity(confirmation['confirmed_by'])
    owners = confirmation['authorized_owners']
    if (not isinstance(owners, list) or not all(isinstance(v, str) and v for v in owners)
            or len(owners) != len(set(owners)) or set(owners) != set(proposal['owner_counts'])
            or confirmation['confirmation_token'] != proposal['confirmation_token']
            or re.fullmatch(r'[a-f0-9-]{36}', thread or '') is None
            or confirmation['source_ref'] != 'codex-thread:' + thread + '/user-confirmation-and-identity'):
        raise KnowledgeHubError('DECLARATION_MISMATCH')
    decision, identity = confirmation['decision_statement'], confirmation['identity_statement']
    if (not isinstance(decision, str) or not isinstance(identity, str)
            or not 1 <= len(decision) <= 4096 or not 1 <= len(identity) <= 1024
            or not all(fragment in decision for fragment in
                       ('确认周期安排', proposal['confirmation_token'],
                        '批准包中' + str(proposal['item_count']) + '条', 'pending/defer', '保留内容、证据及责任待办'))
            or not all(fragment in identity for fragment in ('负责人身份：' + who, '权限范围：所有周期复核'))):
        raise KnowledgeHubError('DECLARATION_MISMATCH')
    safe_text(decision)
    safe_text(identity)
    return {'kind': 'owner-cycle-decision', 'confirmed_by': who,
            'authorized_owners': owners, 'confirmation_token': proposal['confirmation_token'],
            'source_ref': confirmation['source_ref'], 'identity_basis': 'explicit-human-declaration',
            'human_identity_independently_verified': False, 'executor': 'Codex',
            'statements': [
                {'order': 1, 'source_ref': confirmation['source_ref'] + '/decision',
                 'statement': decision, 'sha256': sha(decision.encode())},
                {'order': 2, 'source_ref': confirmation['source_ref'] + '/identity',
                 'statement': identity, 'sha256': sha(identity.encode())}],
            'content_approval_performed': False, 'human_content_review_performed': False}


def _check_packet(root, by_id, confirmation, proposal_hash, token, snapshot, op_rows):
    packet = by_id.get(confirmation['decision_packet_id'])
    if not packet or packet.get('source', {}).get('type') != 'provider-candidate-archive':
        raise KnowledgeHubError('CONTENT_PROOF_REQUIRED')
    if packet.get('visibility') == 'personal-local' or packet['path'].startswith('notes/'):
        raise KnowledgeHubError('VISIBILITY_DENIED')
    packet_subject = item_subject(packet)
    if not packet_subject:
        packet_subject = ({'type': 'domain', 'id': packet['domain']} if packet.get('domain') in {'embedded', 'codex'}
                          else {'type': 'project', 'id': 'knowledge-hub'})
    authorize(root, 'read', packet_subject)
    packet_raw = snapshot(packet['path'])
    verify_current_item(root, packet, op_rows)
    if (sha(packet_raw) != confirmation['decision_packet_sha256']
            or proposal_hash not in packet_raw.decode()
            or token not in packet_raw.decode()):
        raise KnowledgeHubError('CONTENT_DRIFT')


def _schedule_entry(root, item, before, entry, today, snapshot, op_rows, latest, prior_reviews, writes):
    ident = entry['item_id']
    path = item['path']
    from .delegated_content_review import FIELD
    if (item.get('status') not in {'active', 'reviewing'} or item.get('visibility') == 'personal-local'
            or path.startswith(('notes/', 'sources/', '.'))
            or pathlib.PurePosixPath(path).suffix != '.md'
            or item.get(FIELD)):
        raise KnowledgeHubError('POLICY_DENIED')
    if any(entry[key] != item[field] for key, field in
           (('path', 'path'), ('owner', 'owner'), ('status', 'status'), ('before_review_after', 'review_after'))):
        raise KnowledgeHubError('CONTENT_DRIFT')
    current_subject = item_subject(item)
    if not current_subject:
        current_subject = ({'type': 'domain', 'id': item['domain']} if item.get('domain') in {'embedded', 'codex'}
                           else {'type': 'project', 'id': 'knowledge-hub'})
    authorize(root, 'read', current_subject)
    raw = snapshot(path)
    if sha(raw) != entry['before_sha256']:
        raise KnowledgeHubError('CONTENT_DRIFT')
    if ident in latest:
        verify_current_item(root, before, op_rows)
    metadata, body = load_markdown(root / path)
    next_date = dt.date.fromisoformat(entry['after_review_after'])
    if not today < next_date <= today + dt.timedelta(days=90):
        raise KnowledgeHubError('POLICY_DENIED')
    expected_metadata = {'review_after': next_date.isoformat(), 'updated_at': today.isoformat(),
                         'manual_validation_pending': True,
                         'content_review_status': before['content_review_status'] if before['status'] == 'active' else 'pending',
                         'review_status': 'periodic-review-scheduled-pending-content'}
    if (entry['planned_metadata'] != expected_metadata
            or set(entry['planned_metadata']) != FIELDS
            or entry['body_text_unchanged'] is not True
            or entry['prior_bound_review_will_defer'] is not bool(before.get('human_review_content_sha256'))):
        raise KnowledgeHubError('POLICY_DENIED')
    item.update(expected_metadata)
    metadata.update(expected_metadata)
    if before.get('human_review_content_sha256'):
        prior_reviews.append({'item_id': ident, 'review': {k: v for k, v in before.items() if k.startswith('human_review')}})
        item['human_review_decision'] = metadata['human_review_decision'] = 'defer'
    if validate_item(item):
        raise KnowledgeHubError('SCHEMA_INVALID')
    rendered = render_markdown(metadata, body).encode()
    if sha(rendered) != entry['after_sha256']:
        raise KnowledgeHubError('CONTENT_DRIFT')
    writes[path] = rendered
    return {'item_id': ident, 'path': path, 'owner': before['owner'], 'status': before['status'],
                      'before_sha256': sha(raw), 'after_sha256': sha(rendered),
                      'before_review_after': before['review_after'], 'after_review_after': item['review_after']}


def _cycle_proofs(scheduled, latest, op_rows, writes, expected, txid, authorization_id):
    for row in scheduled:
        if row['item_id'] not in latest:
            continue
        proof = latest[row['item_id']]
        op_id = digest([expected, row['item_id'], proof['content_sha256'], row['after_sha256']])
        op_rows.append(dict(proof, operation_id=op_id, request_sha256=op_id, action='metadata',
                            content_sha256=row['after_sha256'], before_content_sha256=proof['content_sha256'],
                            transaction_id=txid, authorization_ref=authorization_id,
                            historical_validation_verified=False,
                            verification_basis={'kind': 'metadata-transaction', 'proof_ref': expected}))
    writes['registry/provider-operations.jsonl'] = encode_jsonl(op_rows).encode()


def build_plan(root, request, thread):
    if not isinstance(request, dict) or set(request) != {'schema_version', 'proposal', 'owner_confirmation'} or request['schema_version'] != APPLICATION:
        raise KnowledgeHubError('SCHEMA_INVALID')
    proposal, confirmation = request['proposal'], request['owner_confirmation']
    if not isinstance(proposal, dict):
        raise KnowledgeHubError('SCHEMA_INVALID')
    base = {k: v for k, v in proposal.items() if k not in {'proposal_sha256', 'confirmation_token'}}
    proposal_hash = digest(base)
    if (proposal.get('schema_version') != PROPOSAL or proposal.get('proposal_sha256') != proposal_hash
            or proposal.get('confirmation_token') != 'KH-SCHEDULE-' + proposal_hash[:24].upper()
            or proposal.get('execution_state') != 'not-applied'
            or proposal.get('decision_required') != 'owner-review-period-rescheduling-only'
            or proposal.get('content_approval_performed') is not False
            or proposal.get('human_review_performed') is not False):
        raise KnowledgeHubError('DECLARATION_MISMATCH')
    entries = proposal.get('entries')
    if not isinstance(entries, list) or not 1 <= len(entries) <= 500 or proposal.get('item_count') != len(entries):
        raise KnowledgeHubError('SCHEMA_INVALID')
    consent = checked_confirmation(proposal, confirmation, thread)
    today = dt.date.today()
    if proposal['as_of'] != today.isoformat():
        raise KnowledgeHubError('CONTENT_DRIFT')
    if 'assign' not in policy(root)['actions']:
        raise KnowledgeHubError('POLICY_DENIED')
    actor = principal(root)
    inputs, writes = {}, {}

    def snapshot(name):
        path = pathlib.PurePosixPath(name)
        target = resolve_inside(root, name)
        if any(root.joinpath(*path.parts[:i]).is_symlink() for i in range(1, len(path.parts) + 1)):
            raise KnowledgeHubError('SOURCE_REJECTED')
        raw = target.read_bytes()
        inputs[name] = sha(raw)
        return raw

    for name in ('registry/items.jsonl', 'registry/provider-operations.jsonl',
                 'registry/authorizations.jsonl', 'registry/provider-subject-policy.json',
                 'registry/owners.json', 'local/provider-principal.json'):
        snapshot(name)
    originals = load_jsonl(root / 'registry/items.jsonl')
    items = copy.deepcopy(originals)
    by_id = {row['id']: row for row in items}
    old_by_id = {row['id']: row for row in originals}
    op_rows = operations(root)
    latest = {row['item_id']: row for row in op_rows}
    _check_packet(root, by_id, confirmation, proposal_hash, proposal['confirmation_token'], snapshot, op_rows)
    index_texts = {name: snapshot(name).decode() for name in CORE_INDEXES}
    seen, scheduled, prior_reviews = set(), [], []
    for entry in entries:
        ident = entry['item_id']
        if ident in seen or ident not in by_id:
            raise KnowledgeHubError('SCHEMA_INVALID')
        seen.add(ident)
        item, before = by_id[ident], old_by_id[ident]
        scheduled.append(_schedule_entry(root, item, before, entry, today, snapshot, op_rows, latest, prior_reviews, writes))
        index_texts = update_core_indexes(index_texts, item)
    if (dict(collections.Counter(row['owner'] for row in scheduled)) != proposal['owner_counts']
            or dict(collections.Counter(row['after_review_after'] for row in scheduled)) != proposal['date_counts']):
        raise KnowledgeHubError('DECLARATION_MISMATCH')
    writes.update({name: value.encode() for name, value in index_texts.items()})
    writes['registry/items.jsonl'] = encode_jsonl(items).encode()
    scope = {'actor': actor, 'action': 'schedule-review', 'proposal_sha256': proposal_hash,
             'item_ids': sorted(seen), 'confirmation_sha256': digest(consent), 'visibility_change': False}
    public = {'schema_version': 1, 'maintenance_kind': 'owner-review-cycle-only', 'proposal_sha256': proposal_hash,
              'owner_cycle_decision': consent, 'exact_execution_scope': scope,
              'inputs': {name: value for name, value in inputs.items() if name != 'registry/authorizations.jsonl'},
              'outputs': {name: sha(value) for name, value in writes.items()}, 'scheduled_items': scheduled,
              'prior_reviews': prior_reviews, 'active_promoted': False, 'owner_review_performed': False,
              'content_approval_performed': False, 'owner_cycle_decision_recorded': True}
    expected = digest(public)
    txid = 'content-maintenance-' + expected[:24]
    authorization_id = 'owner-cycle-' + expected[:24]
    _cycle_proofs(scheduled, latest, op_rows, writes, expected, txid, authorization_id)
    public.update(expected_hash=expected, transaction_id=txid, authorization_ref=authorization_id,
                  result_writes={name: sha(value) for name, value in writes.items()},
                  item_count=len(seen), write_count=len(writes) + 1, delete_count=0)
    return public, inputs, writes


def record_authorization(root, args, request):
    """Record the explicit execution grant only; cannot update a knowledge item."""
    if request.get('schema_version') != AUTHORIZATION:
        raise KnowledgeHubError('SCHEMA_INVALID')
    application = dict(request, schema_version=APPLICATION)
    with read_guard(root):
        plan, inputs, _ = build_plan(root, application, os.environ.get('CODEX_THREAD_ID', ''))
    scope = dict(plan['exact_execution_scope'], expected_hash=plan['expected_hash'])
    expected = digest({'kind': 'owner-cycle-execution-authorization', 'scope': scope,
                       'before_authorizations_sha256': inputs['registry/authorizations.jsonl']})
    txid = 'content-maintenance-' + expected[:24]
    manifest_ref = 'artifacts/manifests/content-maintenance-' + expected + '.json'
    receipt = {'schema_version': 'knowledge-provider.content-maintenance/v1', 'status': 'PLANNED',
               'maintenance_kind': 'owner-cycle-execution-authorization', 'persisted': False, 'read_only': True,
               'write_performed': False, 'active_promoted': False, 'owner_review_performed': False,
               'expected_hash': expected, 'item_count': 0, 'write_count': 1, 'delete_count': 0,
               'application_expected_hash': plan['expected_hash'], 'authorization_id': plan['authorization_ref']}
    if not args.apply:
        return receipt
    if args.expected_content_sha256 != expected:
        raise KnowledgeHubError('CONTENT_DRIFT')
    from .provider_grants import attested_request
    declaration = pathlib.Path(args.declaration_file)
    renewal = getattr(args, 'renewal_request_file', '')
    request_sha, attestation = attested_request(declaration.read_text(), declaration, renewal) if renewal else attested_request(declaration.read_text(), declaration)
    rows = load_jsonl(root / 'registry/authorizations.jsonl')
    if any(row['authorization_id'] == plan['authorization_ref'] for row in rows):
        raise KnowledgeHubError('AUTHORIZATION_REQUIRED')
    today = dt.date.today().isoformat()
    row = {'authorization_id': plan['authorization_ref'], 'authorized_by': plan['owner_cycle_decision']['confirmed_by'],
           'authorized_at': today, 'expires_at': today, 'scope': pretty_json(scope),
           'allowed_actions': ['automation-apply-with-review'], 'status': 'active',
           'evidence_refs': [manifest_ref, plan['owner_cycle_decision']['source_ref']],
           'rollback_path': '.tmp/transactions/' + plan['transaction_id'] + '/before',
           'validation_commands': ['rtk bash tools/knowledge-check.sh --dry-run --summary-json']}
    tx = RepositoryTransaction(root, transaction_id=txid, expected_inputs=inputs)
    tx.add_text('registry/authorizations.jsonl', encode_jsonl(rows + [row]))
    tx.add_text(manifest_ref, pretty_json({'schema_version': 1, 'maintenance_kind': 'owner-cycle-execution-authorization',
                'exact_execution_scope': scope, 'owner_cycle_decision': plan['owner_cycle_decision'],
                'expected_hash': expected, 'application_expected_hash': plan['expected_hash'],
                'original_execution_request_sha256': request_sha,
                'original_execution_intake_attestation_sha256': attestation,
                'active_promoted': False, 'owner_review_performed': False}) + '\n')
    args._commit_started = True
    tx.apply()
    receipt.update(status='MAINTAINED', persisted=True, read_only=False, write_performed=True,
                   manifest_ref=manifest_ref, transaction_id=txid)
    return receipt


def schedule(root, args, request):
    with read_guard(root):
        plan, inputs, writes = build_plan(root, request, os.environ.get('CODEX_THREAD_ID', ''))
    receipt = {'schema_version': 'knowledge-provider.content-maintenance/v1', 'status': 'PLANNED',
               'maintenance_kind': 'owner-review-cycle-only', 'persisted': False, 'read_only': True,
               'write_performed': False, 'active_promoted': False, 'owner_review_performed': False,
               'owner_cycle_decision_recorded': False,
               **{key: plan[key] for key in ('expected_hash', 'item_count', 'write_count', 'delete_count')}}
    if not args.apply:
        return receipt
    if args.expected_content_sha256 != plan['expected_hash']:
        raise KnowledgeHubError('CONTENT_DRIFT')
    from .provider_grants import attested_request, _require_exact_scope
    if args.authorization_id != plan['authorization_ref']:
        raise KnowledgeHubError('AUTHORIZATION_REQUIRED')
    _require_exact_scope(root, args.authorization_id,
                         dict(plan['exact_execution_scope'], expected_hash=plan['expected_hash']))
    declaration = pathlib.Path(args.declaration_file)
    renewal = getattr(args, 'renewal_request_file', '')
    request_sha, attestation = attested_request(declaration.read_text(), declaration, renewal) if renewal else attested_request(declaration.read_text(), declaration)
    rows = load_jsonl(root / 'registry/authorizations.jsonl')
    for row in rows:
        if row['authorization_id'] == args.authorization_id:
            row['status'] = 'used'
    writes['registry/authorizations.jsonl'] = encode_jsonl(rows).encode()
    plan['result_writes']['registry/authorizations.jsonl'] = sha(writes['registry/authorizations.jsonl'])
    tx = RepositoryTransaction(root, transaction_id=plan['transaction_id'], expected_inputs=inputs)
    for name, raw in writes.items():
        tx.add_bytes(name, raw)
    manifest_ref = 'artifacts/manifests/content-maintenance-' + plan['expected_hash'] + '.json'
    tx.add_text(manifest_ref, pretty_json(dict(plan, original_execution_request_sha256=request_sha,
                original_execution_intake_attestation_sha256=attestation,
                owner_decision_basis='explicit-statements-mechanically-recorded; not-original-intake-attestation')) + '\n')
    args._commit_started = True
    result = tx.apply()
    if any(sha((root / name).read_bytes()) != sha(raw) for name, raw in writes.items()):
        raise KnowledgeHubError('CONTENT_DRIFT')
    receipt.update(status='MAINTAINED', persisted=True, read_only=False, write_performed=True,
                   manifest_ref=manifest_ref, transaction_id=result.transaction_id, owner_cycle_decision_recorded=True)
    return receipt
