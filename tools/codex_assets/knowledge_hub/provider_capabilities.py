"""Operation-specific public Provider capabilities; existence is not authorization."""

from __future__ import annotations

from .activity import load_activity_config
from .common import KnowledgeHubError, load_json
from .schemas import validate_instance


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
    archive_enabled = valid and policy.get('enabled') is True
    activity_enabled = bool(config.get('valid') and config.get('receipt_persistence') and config.get('subject_id'))
    return {'schema_version':'knowledge-provider.capabilities/v1', 'status':'READY_FOR_CALL',
            'provider':'knowledge-hub', 'read_only':True,
            'operations':{
                'context':{'mode':'readonly', 'available':True, 'write_allowed':False},
                'evidence-pack':{'mode':'readonly', 'available':True, 'write_allowed':False},
                'action-check':{'mode':'readonly', 'available':True, 'write_allowed':False},
                'proposal-route':{'mode':'shadow', 'write_allowed':False},
                'archive':{'mode':'candidate-only', 'write_allowed':bool(archive_enabled),
                           'policy_valid':bool(valid), 'active_promotion_allowed':False,
                           'allowed_kinds':policy.get('allowed_kinds', []) if valid else []},
                'activity-capture':{'mode':'configured-subject-only', 'write_allowed':activity_enabled,
                                    'subject_configured':bool(config.get('subject_id'))}},
            'note':'Each operation still validates its route, inputs and policy at call time.'}
