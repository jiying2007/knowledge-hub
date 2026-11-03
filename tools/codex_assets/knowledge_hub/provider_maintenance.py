"""Attested, exact-plan metadata and path maintenance; never content approval.

Only existing Markdown bodies may move; body text is immutable except for
mechanical references to moved paths. Source, owner, status and review dates
cannot be supplied by a maintenance request.

Explicit private-network-address redaction is the only additional body edit.
The original address is never copied into the public maintenance manifest.
The same exact-span privacy cleanup may redact source.from, summary_zh and
evidence/validation reference text; source type and provenance hashes stay intact.
Hash-bound unresolved Markdown source links may also become explicit textual
source pointers. This never creates a target or asserts external availability.
"""
from __future__ import annotations

import copy
import hashlib
import ipaddress
import json
import pathlib
import posixpath
import re
import urllib.parse

from .common import KnowledgeHubError, encode_jsonl, load_json, load_jsonl, load_markdown, render_markdown, pretty_json
from .provider_subjects import authorize, digest, principal, read_guard, item_subject, policy
from .provider_operations import operations, verify_current_item, safe_text
from .store import RepositoryTransaction

FIELDS = {'searchable', 'quality_flags', 'successor_refs', 'evidence_profile', 'related', 'tags', 'summary_zh'}
PRIVATE_NETWORKS = tuple(ipaddress.ip_network(value) for value in
                         ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'))
IPV4_LITERAL = re.compile(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])')


def redact_private_network_addresses(body, occurrences):
    """Redact only reviewed, hash-bound spans; never infer an endpoint from a version."""
    fragments, cursor = [], 0
    for occurrence in occurrences:
        start, end = occurrence['start'], occurrence['end']
        if not cursor <= start < end <= len(body):
            raise KnowledgeHubError('CONTENT_DRIFT')
        literal = body[start:end]
        try:
            address = ipaddress.ip_address(literal)
        except ValueError:
            raise KnowledgeHubError('SOURCE_REJECTED') from None
        if (not IPV4_LITERAL.fullmatch(literal)
                or not any(address in network for network in PRIVATE_NETWORKS)
                or sha(literal.encode()) != occurrence['sha256']):
            raise KnowledgeHubError('CONTENT_DRIFT')
        fragments.extend((body[cursor:start], '<设备地址>'))
        cursor = end
    fragments.append(body[cursor:])
    return ''.join(fragments), len(occurrences)


def validate_redactions(redactions):
    if redactions == []:
        return
    if (not isinstance(redactions, list) or len(redactions) != 1
            or not isinstance(redactions[0], dict)
            or set(redactions[0]) - {'kind', 'occurrences', 'metadata_occurrences'}
            or not {'kind', 'occurrences'} <= set(redactions[0])
            or redactions[0]['kind'] != 'private-network-addresses'):
        raise KnowledgeHubError('POLICY_DENIED')
    occurrences = redactions[0]['occurrences']
    metadata_occurrences = redactions[0].get('metadata_occurrences', [])
    if (not isinstance(occurrences, list) or not isinstance(metadata_occurrences, list)
            or not 1 <= len(occurrences) + len(metadata_occurrences) <= 256):
        raise KnowledgeHubError('POLICY_DENIED')
    for entries, is_metadata in ((occurrences, False), (metadata_occurrences, True)):
        for entry in entries:
            fields = {'start', 'end', 'sha256'} | ({'field'} if is_metadata else set())
            if (not isinstance(entry, dict) or set(entry) != fields
                    or type(entry['start']) is not int or type(entry['end']) is not int
                    or not isinstance(entry['sha256'], str)
                    or re.fullmatch(r'[a-f0-9]{64}', entry['sha256']) is None):
                raise KnowledgeHubError('POLICY_DENIED')
            if is_metadata and (not isinstance(entry['field'], str)
                    or re.fullmatch(r'source\.from|summary_zh|(?:evidence_refs|validation_refs)\.(?:0|[1-9][0-9]*)', entry['field']) is None):
                raise KnowledgeHubError('POLICY_DENIED')


def metadata_slot(container, field):
    """Resolve only validated display/provenance text; never lifecycle/identity fields."""
    try:
        if field == 'summary_zh':
            parent, key = container, field
        elif field == 'source.from':
            parent, key = container['source'], 'from'
        else:
            name, index = field.split('.')
            if name not in {'evidence_refs', 'validation_refs'}:
                raise KnowledgeHubError('POLICY_DENIED')
            parent, key = container[name], int(index)
        if not isinstance(parent, (list, dict)) or not isinstance(parent[key], str):
            raise KnowledgeHubError('CONTENT_DRIFT')
        return parent, key
    except (KeyError, IndexError, ValueError, TypeError):
        raise KnowledgeHubError('CONTENT_DRIFT') from None


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _source_link_container_content(line):
    # Peel arbitrary quote/list interleaving without discarding code indentation.
    marker = re.match(r'^(?: {0,3}>[ \t]?| {0,3}(?:[-+*]|[0-9]+[.)])[ \t])', line)
    while marker:
        line = line[marker.end():]
        marker = re.match(r'^(?: {0,3}>[ \t]?| {0,3}(?:[-+*]|[0-9]+[.)])[ \t])', line)
    return line


def _source_link_fence(line):
    content = _source_link_container_content(line).rstrip('\r\n')
    return re.match(r'^[ \t]*(`{3,}|~{3,})(.*)$', content)


def _source_link_indented(line):
    content = _source_link_container_content(line)
    return re.match(r'^(?: {4}|[ \t]*\t)', content) is not None


def _source_link_block_ranges(body):
    blocked, fence, offset = [], None, 0
    for line in body.splitlines(keepends=True):
        marker = _source_link_fence(line)
        if fence is not None:
            blocked.append((offset, offset + len(line)))
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1] and not marker[2].strip():
                fence = None
        elif marker:
            blocked.append((offset, offset + len(line)))
            fence = (marker[1][0], len(marker[1]))
        elif _source_link_indented(line):
            blocked.append((offset, offset + len(line)))
        offset += len(line)
    return blocked


def _source_link_escaped(body, offset):
    prefix = body[:offset]
    return (len(prefix) - len(prefix.rstrip('\\'))) % 2 == 1


def _source_link_code_ranges(body):
    blocked = _source_link_block_ranges(body)
    # HTML comments and code/raw-text containers do not expose Markdown links.
    html = r'<!--.*?(?:-->|\Z)|<(pre|code|script|style|textarea)\b[^>]*>.*?(?:</\1\s*>|\Z)'
    blocked.extend((match.start(), match.end()) for match in re.finditer(html, body, re.S | re.I))
    pending = None
    for token in re.finditer(r'`+', body):
        if any(start <= token.start() < end for start, end in blocked):
            continue
        if pending is not None:
            if len(token[0]) == pending[1]:
                blocked.append((pending[0], token.end()))
                pending = None
        elif not _source_link_escaped(body, token.start()):
            pending = (token.start(), len(token[0]))
    if pending is not None:
        # Ambiguous/unclosed inline code is never permission to rewrite prose.
        blocked.append((pending[0], len(body)))
    return blocked


def _require_source_link_context(body, start, end, blocked):
    if (_source_link_escaped(body, start) or (start > 0 and body[start - 1] == '!')
            or any(start < stop and end > begin for begin, stop in blocked)):
        raise KnowledgeHubError('POLICY_DENIED')


def repair_unresolved_source_links(root, source, body, repairs):
    """Make exact missing source pointers explicit text, never invent a Hub target."""
    if repairs == []:
        return body
    if not isinstance(repairs, list) or not 1 <= len(repairs) <= 256:
        raise KnowledgeHubError('POLICY_DENIED')
    fragments, cursor = [], 0
    blocked = _source_link_code_ranges(body)
    for entry in repairs:
        if (not isinstance(entry, dict) or set(entry) != {'start', 'end', 'sha256'}
                or type(entry['start']) is not int or type(entry['end']) is not int
                or not isinstance(entry['sha256'], str)):
            raise KnowledgeHubError('POLICY_DENIED')
        start, end = entry['start'], entry['end']
        if not cursor <= start < end <= len(body):
            raise KnowledgeHubError('CONTENT_DRIFT')
        _require_source_link_context(body, start, end, blocked)
        literal = body[start:end]
        match = re.fullmatch(r'\[([^\]\n]+)\]\(([^\s()]+)\)', literal)
        if not match or sha(literal.encode()) != entry['sha256']:
            raise KnowledgeHubError('CONTENT_DRIFT')
        label, target = match.groups()
        if ':' in target or target.startswith(('#', '/')) or '`' in target:
            raise KnowledgeHubError('POLICY_DENIED')
        relative = urllib.parse.unquote(target.split('#', 1)[0])
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source), relative))
        from .common import resolve_inside
        if resolve_inside(root, resolved).exists():
            raise KnowledgeHubError('POLICY_DENIED')
        replacement = label + '（来源内引用：`' + target + '`；尚未映射为 Hub 链接）'
        fragments.extend((body[cursor:start], replacement))
        cursor = end
    fragments.append(body[cursor:])
    return ''.join(fragments)


def _requested_changes(root, request):
    if (set(request) != {'schema_version', 'items'} or request['schema_version'] != 1
            or not isinstance(request['items'], list) or not 1 <= len(request['items']) <= 500):
        raise KnowledgeHubError('SCHEMA_INVALID')
    original_items = load_jsonl(root / 'registry/items.jsonl')
    items = copy.deepcopy(original_items)
    by_id = {item['id']: item for item in items}
    old_by_id = {item['id']: item for item in original_items}
    projects = {row['id'] for row in load_json(root / 'registry/projects.json')['projects']}
    changes, moves, seen = {}, {}, set()
    for entry in request['items']:
        if (not isinstance(entry, dict) or set(entry) - {'item_id', 'expected_sha256', 'target_path', 'metadata', 'redactions', 'link_repairs'}
                or not {'item_id', 'expected_sha256'} <= set(entry) or entry['item_id'] in seen):
            raise KnowledgeHubError('SCHEMA_INVALID')
        seen.add(entry['item_id'])
        validate_redactions(entry.get('redactions', []))
        before = old_by_id.get(entry['item_id'])
        if (not before or before.get('status') == 'active' or before.get('visibility') == 'personal-local'
                or before.get('path', '').startswith('notes/personal/')):
            raise KnowledgeHubError('POLICY_DENIED')
        source = before['path']
        path = pathlib.PurePosixPath(source)
        if not source.startswith('projects/') or path.suffix != '.md':
            raise KnowledgeHubError('POLICY_DENIED')
        from .common import resolve_inside
        resolved = resolve_inside(root, source)
        if any(root.joinpath(*path.parts[:i]).is_symlink() for i in range(1, len(path.parts) + 1)) or sha(resolved.read_bytes()) != entry['expected_sha256']:
            raise KnowledgeHubError('CONTENT_DRIFT')
        target = entry.get('target_path', source)
        target_path = pathlib.PurePosixPath(target)
        if (str(target_path) != target or target_path.is_absolute() or '..' in target_path.parts
                or len(target_path.parts) < 4 or target_path.parts[0] != 'projects'
                or target_path.parts[1] not in projects or target_path.suffix != '.md'):
            if target != source:
                raise KnowledgeHubError('SOURCE_REJECTED')
        if target != source and ((root / target).exists() or target in moves.values()):
            raise KnowledgeHubError('ROUTE_CONFLICT')
        metadata = entry.get('metadata', {})
        if not isinstance(metadata, dict) or set(metadata) - FIELDS:
            raise KnowledgeHubError('POLICY_DENIED')
        safe_text(json.dumps(metadata, ensure_ascii=False))
        item = by_id[entry['item_id']]
        item.update(metadata, path=target, domain='projects/' + target_path.parts[1])
        if 'subject_ref' in item:
            item['subject_ref'] = {'type': 'project', 'id': target_path.parts[1]}
        if target != source:
            moves[source] = target
        changes[item['id']] = entry
    return items, old_by_id, changes, moves


def _replace_refs(value, moves):
    if isinstance(value, str):
        for source, target in moves.items():
            value = value.replace(source, target)
        return value
    if isinstance(value, list):
        return [_replace_refs(v, moves) for v in value]
    if isinstance(value, dict):
        return {k: _replace_refs(v, moves) for k, v in value.items()}
    return value


def _snapshot(root, inputs, name):
    from .common import resolve_inside
    resolve_inside(root, name)
    parts = pathlib.PurePosixPath(name).parts
    if any(root.joinpath(*parts[:i]).is_symlink() for i in range(1, len(parts) + 1)):
        raise KnowledgeHubError('SOURCE_REJECTED')
    raw = (root / name).read_bytes()
    inputs[name] = sha(raw)
    return raw


def _redact_document(item, before, metadata, new_metadata, body, changes, refs, body_redactions):
    redactions = changes.get(item['id'], {}).get('redactions', [])
    if not redactions:
        return body
    redacted_body, redacted_count = redact_private_network_addresses(body, redactions[0]['occurrences'])
    groups = {}
    for occurrence in redactions[0].get('metadata_occurrences', []):
        field = occurrence['field']
        if field.split('.')[0] in changes[item['id']].get('metadata', {}):
            raise KnowledgeHubError('POLICY_DENIED')
        groups.setdefault(field, []).append({key: occurrence[key] for key in ('start', 'end', 'sha256')})
    for field, selected in groups.items():
        before_parent, before_key = metadata_slot(before, field)
        metadata_parent, metadata_key = metadata_slot(metadata, field)
        if before_parent[before_key] != metadata_parent[metadata_key]:
            raise KnowledgeHubError('CONTENT_DRIFT')
        value, count = redact_private_network_addresses(before_parent[before_key], selected)
        for container in (item, new_metadata):
            parent, key = metadata_slot(container, field)
            parent[key] = refs(value)
        redacted_count += count
    body_redactions.append({'item_id': item['id'], 'kind': 'private-network-addresses', 'redacted_count': redacted_count})
    return redacted_body


def _navigation_link(source, target, moves):
    def link(match):
        link_target = match.group(1)
        if ':' in link_target or link_target.startswith(('#', '/')):
            return match.group(0)
        path_part, marker, anchor = link_target.partition('#')
        absolute = posixpath.normpath(posixpath.join(posixpath.dirname(source), path_part))
        if absolute not in moves and source == target:
            return match.group(0)
        destination = moves.get(absolute, absolute)
        relative = posixpath.relpath(destination, posixpath.dirname(target))
        return '](' + relative + (marker + anchor if marker else '') + ')'
    return link


def _active_navigation(before, item, metadata, new_metadata, body, next_body, changes, moves, link):
    from .delegated_content_review import FIELD
    navigation_fields = {'related', 'evidence_refs', 'validation_refs'}
    metadata_changes = {key for key in set(metadata) | set(new_metadata) if metadata.get(key) != new_metadata.get(key)}
    item_changes = {key for key in set(before) | set(item) if before.get(key) != item.get(key)}
    expected_lines, fenced = [], False
    for line in body.splitlines(keepends=True):
        if re.match(r'^\s*(```|~~~)', line):
            fenced = not fenced
        if not fenced:
            line = re.sub(r'\]\(([^)\s]+)\)', link, line)
            for old, new in moves.items():
                line = line.replace('`' + old + '`', '`' + new + '`')
        expected_lines.append(line)
    if (item['id'] in changes or item.get(FIELD) or item.get('human_review_content_sha256')
            or not metadata_changes <= navigation_fields or not item_changes <= navigation_fields
            or next_body != ''.join(expected_lines)):
        raise KnowledgeHubError('ACTIVE_REVIEW_REVALIDATION_REQUIRED')


def _render_document(item, before, raw, new_metadata, next_body, refs, active_navigation, review_history):
    from .delegated_content_review import FIELD
    if item.get(FIELD):
        raise KnowledgeHubError('CONTENT_REVIEW_REVALIDATION_REQUIRED')
    if item.get('human_review_content_sha256'):
        review_history.append({'item_id': item['id'], 'before_sha256': sha(raw),
                               'review': {k: v for k, v in before.items() if k.startswith('human_review')}})
        item.update(human_review_decision='defer', content_review_status='pending', review_status='content-maintenance-pending-review')
        new_metadata.update(human_review_decision='defer', content_review_status='pending', review_status='content-maintenance-pending-review')
    if not active_navigation:
        return render_markdown(new_metadata, next_body).encode()
    rendered = refs(raw.decode()).encode()
    from .common import split_frontmatter
    checked_metadata, checked_body = split_frontmatter(rendered.decode())
    if checked_metadata != new_metadata or checked_body != next_body:
        raise KnowledgeHubError('ACTIVE_REVIEW_REVALIDATION_REQUIRED')
    return rendered


def _rewrite_document(root, item, before, changes, moves, refs, snapshot, outputs, histories, op_rows, latest):
    writes, deletes = outputs
    review_history, navigation_updates, body_redactions = histories
    source, target = before['path'], item['path']
    if before.get('visibility') == 'personal-local' or source.startswith('notes/personal/'):
        return
    if not source.startswith(('projects/', 'domains/embedded/', 'domains/codex/', 'governance/')):
        return
    file = root / source
    if not file.is_file() or file.suffix != '.md':
        return
    current_subject = item_subject(before)
    if not current_subject and before.get('domain') in {'embedded', 'codex'}:
        current_subject = {'type': 'domain', 'id': before['domain']}
    if not current_subject and source.startswith('governance/'):
        current_subject = {'type': 'project', 'id': 'knowledge-hub'}
    if current_subject:
        authorize(root, 'read', current_subject)
    raw = snapshot(source)
    metadata, body = load_markdown(file)
    new_item = refs(item)
    item.clear()
    item.update(new_item)
    new_metadata = refs(metadata)
    redacted = _redact_document(item, before, metadata, new_metadata, body, changes, refs, body_redactions)
    repairs = changes.get(item['id'], {}).get('link_repairs', [])
    if repairs:
        if changes[item['id']].get('redactions'):
            raise KnowledgeHubError('POLICY_DENIED')
        redacted = repair_unresolved_source_links(root, source, redacted, repairs)
        body_redactions.append({'item_id': item['id'], 'kind': 'unresolved-source-links', 'repaired_count': len(repairs)})
    link = _navigation_link(source, target, moves)
    next_body = re.sub(r'\]\(([^)\s]+)\)', link, refs(redacted))
    if item['id'] in changes:
        new_metadata.update(changes[item['id']].get('metadata', {}))
    for field in ('path', 'domain', 'subject_ref'):
        if source != target and (field in new_metadata or field in item):
            new_metadata[field] = item[field]
    if new_metadata == metadata and next_body == body and source == target:
        return
    active_navigation = before.get('status') == 'active'
    if active_navigation:
        _active_navigation(before, item, metadata, new_metadata, body, next_body, changes, moves, link)
        navigation_updates.append({'item_id': item['id'], 'before_sha256': sha(raw), 'kind': 'mechanical-path-reference-only'})
    writes[target] = _render_document(item, before, raw, new_metadata, next_body, refs, active_navigation, review_history)
    if source != target:
        deletes[source] = sha(raw)
    if item['id'] in latest:
        verify_current_item(root, before, op_rows)


def _structural_references(root, snapshot, refs, writes):
    for base in ('indexes', 'registry'):
        for file in sorted((root / base).rglob('*.md')):
            name = str(file.relative_to(root))
            raw = snapshot(name)
            text = refs(raw.decode())
            if text.encode() != raw:
                writes[name] = text.encode()
    name = 'registry/decisions.jsonl'
    if (root / name).is_file():
        raw = snapshot(name)
        text = refs(raw.decode())
        if text.encode() != raw:
            writes[name] = text.encode()


def _validated_public_request(root, request, items):
    from .schemas import _load_contract_schema, _FORMAT_CHECKER
    from jsonschema import Draft202012Validator
    item_schema, schema_errors = _load_contract_schema(root, 'registry-item-v1')
    if schema_errors:
        raise KnowledgeHubError('SCHEMA_INVALID')
    validator = Draft202012Validator(item_schema, format_checker=_FORMAT_CHECKER)
    if any(not validator.is_valid(item) for item in items):
        raise KnowledgeHubError('SCHEMA_INVALID')
    public_request = copy.deepcopy(request)
    for entry in public_request['items']:
        for redaction in entry.get('redactions', []):
            for occurrence in redaction['occurrences'] + redaction.get('metadata_occurrences', []):
                occurrence.pop('sha256')
    return public_request


def _maintenance_proofs(items, old_by_id, latest, op_rows, writes, expected, transaction_id):
    for item in items:
        if item['path'] not in writes or item['id'] not in latest:
            continue
        before = old_by_id[item['id']]
        proof = latest[item['id']]
        after_hash = sha(writes[item['path']])
        op_id = digest([expected, item['id'], proof['content_sha256'], after_hash])
        op_rows.append(dict(proof, operation_id=op_id, request_sha256=op_id,
                            action='metadata' if item_subject(before) == item_subject(item) else 'assign',
                            subject_ref=item_subject(item), content_sha256=after_hash,
                            before_content_sha256=proof['content_sha256'], transaction_id=transaction_id,
                            historical_validation_verified=False,
                            verification_basis={'kind': 'metadata-transaction', 'proof_ref': expected}))
    writes['registry/provider-operations.jsonl'] = encode_jsonl(op_rows).encode()


def build_plan(root, request):
    items, old_by_id, changes, moves = _requested_changes(root, request)
    def refs(value):
        return _replace_refs(value, moves)
    inputs, writes, deletes = {}, {}, {}
    review_history, navigation_updates, body_redactions = [], [], []
    def snapshot(name):
        return _snapshot(root, inputs, name)
    for name in ('registry/items.jsonl', 'registry/projects.json', 'registry/provider-operations.jsonl'):
        snapshot(name)
    op_rows = operations(root)
    latest = {row['item_id']: row for row in op_rows}
    for item in items:
        _rewrite_document(root, item, old_by_id[item['id']], changes, moves, refs, snapshot,
                          (writes, deletes), (review_history, navigation_updates, body_redactions), op_rows, latest)
    _structural_references(root, snapshot, refs, writes)
    writes['registry/items.jsonl'] = encode_jsonl(items).encode()
    public = {'schema_version': 1, 'request': _validated_public_request(root, request, items), 'inputs': inputs,
              'outputs': {p: sha(raw) for p, raw in writes.items()}, 'deletes': deletes,
              'prior_reviews': review_history, 'navigation_updates': navigation_updates, 'body_redactions': body_redactions,
              'active_promoted': False, 'owner_review_performed': False}
    expected = digest(public)
    transaction_id = 'content-maintenance-' + expected[:24]
    _maintenance_proofs(items, old_by_id, latest, op_rows, writes, expected, transaction_id)
    public.update(expected_hash=expected, result_writes={p: sha(raw) for p, raw in writes.items()},
                  write_count=len(writes), delete_count=len(deletes), item_count=len(changes), transaction_id=transaction_id)
    return public, inputs, writes, deletes


def maintain(root, args):
    request = load_json(pathlib.Path(args.source), maximum_bytes=524288)
    if isinstance(request, dict) and request.get('schema_version') == 'knowledge-content-maintenance-authorization/v1':
        from .provider_maintenance_authorization import record
        return record(root, args, request)
    if isinstance(request, dict) and request.get('schema_version') == 'knowledge-owner-cycle-application/v1':
        from .provider_review_schedule import schedule
        return schedule(root, args, request)
    if isinstance(request, dict) and request.get('schema_version') == 'knowledge-owner-cycle-authorization/v1':
        from .provider_review_schedule import record_authorization
        return record_authorization(root, args, request)
    with read_guard(root):
        plan, inputs, writes, deletes = build_plan(root, request)
    scopes = sorted({entry['item_id'] for entry in request['items']})
    for project in {row['path'].split('/')[1] for row in load_jsonl(root / 'registry/items.jsonl') if row['id'] in scopes}:
        authorize(root, 'read', {'type': 'project', 'id': project})
    for entry in request['items']:
        if 'target_path' in entry:
            authorize(root, 'read', {'type': 'project', 'id': entry['target_path'].split('/')[1]})
    receipt = {'schema_version': 'knowledge-provider.content-maintenance/v1', 'status': 'PLANNED',
               'persisted': False, 'read_only': True, 'write_performed': False,
               **{key: plan[key] for key in ('expected_hash', 'item_count', 'write_count', 'delete_count')},
               'active_promoted': False, 'owner_review_performed': False}
    if not args.apply:
        return receipt
    if args.expected_content_sha256 != plan['expected_hash']:
        raise KnowledgeHubError('CONTENT_DRIFT')
    if 'assign' not in policy(root)['actions']:
        raise KnowledgeHubError('POLICY_DENIED')
    from .provider_grants import _require_exact_scope, attested_request
    scope = {'actor': principal(root), 'action': 'maintain-content', 'expected_hash': plan['expected_hash'],
             'item_ids': scopes, 'visibility_change': False}
    _require_exact_scope(root, args.authorization_id, scope)
    declaration = pathlib.Path(args.declaration_file)
    raw = declaration.read_text()
    if not re.search('优化|治理|maintain|cleanup', raw, re.I):
        raise KnowledgeHubError('DECLARATION_MISMATCH')
    renewal = getattr(args, 'renewal_request_file', '')
    request_sha, attestation = attested_request(raw, declaration, renewal) if renewal else attested_request(raw, declaration)
    # Authorization is issued after dry-run, but still bound at commit time.
    inputs['registry/authorizations.jsonl'] = sha((root / 'registry/authorizations.jsonl').read_bytes())
    tx = RepositoryTransaction(root, transaction_id=plan['transaction_id'], expected_inputs=inputs)
    for name, content in writes.items():
        tx.add_bytes(name, content)
    for name, expected in deletes.items():
        tx.add_delete(name, expected)
    manifest_ref = 'artifacts/manifests/content-maintenance-' + plan['expected_hash'] + '.json'
    tx.add_text(manifest_ref, pretty_json(dict(plan, request_sha256=request_sha,
                intake_attestation_sha256=attestation, authorization_ref=args.authorization_id)) + '\n')
    args._commit_started = True
    result = tx.apply()
    if any(sha((root / name).read_bytes()) != sha(content) for name, content in writes.items()):
        raise KnowledgeHubError('CONTENT_DRIFT')
    receipt.update(status='MAINTAINED', persisted=True, read_only=False, write_performed=True,
                   manifest_ref=manifest_ref, transaction_id=result.transaction_id)
    return receipt
