"""Operation-specific public Provider capabilities; existence is not authorization."""

from __future__ import annotations

from .activity import load_activity_config
from .common import KnowledgeHubError, load_json
from .schemas import validate_instance
from .context_support import TASK_TYPES


def capabilities(root):
    try:
        policy = load_json(root / 'registry/provider-archive-policy.json', {})
        valid = validate_instance(root, 'provider-archive-policy-v1', policy)['status'] == 'pass'
        owners = load_json(root / 'registry/owners.json', {}).get('owners', [])
        valid = valid and policy.get('owner_id') in {row.get('id') for row in owners}
    except (KnowledgeHubError, OSError, TypeError, AttributeError, ValueError):
        policy, valid = {}, False
    try:
        config = load_activity_config(root)
    except (KnowledgeHubError, OSError, ValueError):
        config = {}
    archive_enabled = valid and policy.get('enabled') is True and policy.get('mode') == 'candidate-only'
    activity_enabled = bool(config.get('valid') and config.get('receipt_persistence') and config.get('subject_id'))
    subject_enabled = False
    try:
        from .provider_subjects import policy as subject_policy, principal
        host = subject_policy(root)
        principal(root)
        subject_enabled = True
    except (KnowledgeHubError, OSError, ValueError):
        pass
    return {'schema_version':'knowledge-provider.capabilities/v4', 'status':'READY_FOR_CALL',
            'protocol_version': 4,
            'provider':'knowledge-hub', 'read_only':True,
            'operations':{
                'context':{'mode':'readonly', 'available':True, 'write_allowed':False,
                           'task_types':sorted(TASK_TYPES), 'default_task_type':'general'},
                'evidence-pack':{'mode':'readonly', 'available':True, 'write_allowed':False},
                'action-check':{'mode':'readonly', 'available':True, 'write_allowed':False},
                'proposal-route':{'mode':'shadow', 'write_allowed':False},
                'archive':{'mode':'candidate-only', 'write_allowed':subject_enabled and bool(archive_enabled) and 'archive' in host['actions'],
                           'policy_valid':bool(valid), 'active_promotion_allowed':False,
                           'allowed_kinds':policy.get('allowed_kinds', []) if valid else [],
                           'subject_types':['project', 'domain', 'personal', 'unassigned']},
                'activity-capture':{'mode':'configured-subject-only', 'write_allowed':activity_enabled,
                                    'subject_configured':bool(config.get('subject_id'))},
                'resolve': {'mode':'readonly', 'available':True, 'write_allowed':False},
                'register': {'mode':'exact-authorized-declaration', 'available':True, 'write_allowed':subject_enabled and 'register' in host['actions']},
                'bind': {'mode':'exact-authorized-local-binding', 'available':True, 'write_allowed':subject_enabled and 'bind' in host['actions']},
                'assign': {'mode':'exact-authorized-reassignment', 'available':True, 'write_allowed':subject_enabled and 'assign' in host['actions']},
                'grant': {'mode':'attested-exact-authorization', 'available':True, 'write_allowed':subject_enabled},
                'reconcile': {'mode':'readonly', 'available':True, 'write_allowed':False},
                'capture-source': {'mode':'readonly', 'available':True, 'write_allowed':False}},
            'note':'Each operation still validates its route, inputs and policy at call time.'}
