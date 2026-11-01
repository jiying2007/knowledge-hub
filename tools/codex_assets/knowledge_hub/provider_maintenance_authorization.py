"""Record an exact execution grant separately from maintenance application."""
import datetime as dt
import pathlib
import re

from .common import KnowledgeHubError, encode_jsonl, load_jsonl, pretty_json
from .provider_grants import attested_request
from .provider_subjects import digest, policy, principal, read_guard
from .store import RepositoryTransaction

SCHEMA = 'knowledge-content-maintenance-authorization/v1'


def record(root, args, request):
    from .provider_maintenance import build_plan, sha
    if not isinstance(request, dict) or set(request) != {'schema_version', 'request'} or request['schema_version'] != SCHEMA:
        raise KnowledgeHubError('SCHEMA_INVALID')
    with read_guard(root):
        plan, inputs, _, _ = build_plan(root, request['request'])
        actor = principal(root)
        if 'assign' not in policy(root)['actions']:
            raise KnowledgeHubError('POLICY_DENIED')
        for name in ('registry/provider-subject-policy.json', 'local/provider-principal.json'):
            inputs[name] = sha((root / name).read_bytes())
        inputs['registry/authorizations.jsonl'] = sha((root / 'registry/authorizations.jsonl').read_bytes())
        rows = load_jsonl(root / 'registry/authorizations.jsonl')
    scope = {'actor': actor, 'action': 'maintain-content', 'expected_hash': plan['expected_hash'],
             'item_ids': sorted(entry['item_id'] for entry in request['request']['items']), 'visibility_change': False}
    expected = digest({'kind': SCHEMA, 'scope': scope, 'authorizations_before_sha256': inputs['registry/authorizations.jsonl']})
    ident = 'maintenance-' + expected[:24]
    txid = 'content-maintenance-' + expected[:24]
    manifest_ref = 'artifacts/manifests/content-maintenance-' + expected + '.json'
    receipt = {'schema_version': 'knowledge-provider.content-maintenance/v1', 'status': 'PLANNED',
               'maintenance_kind': 'execution-authorization-only', 'persisted': False, 'read_only': True,
               'write_performed': False, 'expected_hash': expected, 'application_expected_hash': plan['expected_hash'],
               'authorization_id': ident, 'item_count': 0, 'write_count': 1, 'delete_count': 0,
               'active_promoted': False, 'owner_review_performed': False}
    if not args.apply:
        return receipt
    if args.expected_content_sha256 != expected or any(row['authorization_id'] == ident for row in rows):
        raise KnowledgeHubError('AUTHORIZATION_REQUIRED')
    declaration = pathlib.Path(args.declaration_file)
    raw = declaration.read_text()
    if not re.search('优化|治理|maintain|cleanup', raw, re.I):
        raise KnowledgeHubError('DECLARATION_MISMATCH')
    renewal = getattr(args, 'renewal_request_file', '')
    request_sha, attestation = attested_request(raw, declaration, renewal) if renewal else attested_request(raw, declaration)
    today = dt.date.today().isoformat()
    authorization = {'authorization_id': ident, 'authorized_by': actor, 'authorized_at': today, 'expires_at': today,
                     'scope': pretty_json(scope), 'allowed_actions': ['automation-apply-with-review'], 'status': 'active',
                     'evidence_refs': [manifest_ref], 'rollback_path': '.tmp/transactions/' + plan['transaction_id'] + '/before',
                     'validation_commands': ['rtk bash tools/knowledge-check.sh --dry-run --summary-json']}
    tx = RepositoryTransaction(root, transaction_id=txid, expected_inputs=inputs)
    tx.add_text('registry/authorizations.jsonl', encode_jsonl(rows + [authorization]))
    tx.add_text(manifest_ref, pretty_json({'schema_version': 1, 'maintenance_kind': 'execution-authorization-only',
                'exact_execution_scope': scope, 'expected_hash': expected, 'request_sha256': request_sha,
                'intake_attestation_sha256': attestation, 'active_promoted': False, 'owner_review_performed': False}) + '\n')
    args._commit_started = True
    tx.apply()
    receipt.update(status='MAINTAINED', persisted=True, read_only=False, write_performed=True,
                   manifest_ref=manifest_ref, transaction_id=txid)
    return receipt
