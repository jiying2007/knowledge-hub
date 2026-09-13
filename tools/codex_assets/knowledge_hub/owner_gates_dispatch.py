import json

from .owner_gates_evidence import (
    make_evidence_readiness,
    make_owner_inbox,
    make_owner_ready_blocking_context,
    make_owner_ready_coverage,
    owner_ready_state,
)
from .owner_gates_forms import make_decision_form, make_owner_checklist
from .owner_gates_support import shlex_quote

def _safe_slug(value):
    text = str(value).strip().lower()
    chars = []
    for char in text:
        if char.isalnum() or char in {'-', '_'}:
            chars.append(char)
        else:
            chars.append('-')
    slug = ''.join(chars).strip('-')
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug or 'owner'

def make_owner_handoff_packet(owner, source_id, owner_open_rows, next_row, commands):
    owner_ready_statuses = {}
    required_fields = []
    must_not = []
    for row in owner_open_rows:
        status, _packages = owner_ready_state(row)
        owner_ready_statuses[status] = owner_ready_statuses.get(status, 0) + 1
        for field in row.get('required_owner_fields', []):
            if field not in required_fields:
                required_fields.append(field)
        for rule in row.get('must_not', []):
            if rule not in must_not:
                must_not.append(rule)
    local_path = f'artifacts/manifests/{source_id}-{_safe_slug(owner)}-owner-decisions-YYYYMMDD.local.jsonl' if source_id else 'artifacts/manifests/<source-id>-<owner>-owner-decisions-YYYYMMDD.local.jsonl'
    return {'status': 'ready-for-owner-review' if owner_open_rows else 'empty', 'read_only': True, 'owner': owner, 'source_id': source_id, 'open_count': len(owner_open_rows), 'worksheet_ids': [row['id'] for row in owner_open_rows], 'next_worksheet_id': next_row.get('id', '') if next_row else '', 'suggested_local_owner_decisions_path': local_path, 'owner_ready_status_counts': dict(sorted(owner_ready_statuses.items())), 'manual_owner_fields': required_fields, 'recommended_sequence': [{'step': '1-open-owner-inbox', 'command': commands.get('owner_inbox_json_command', ''), 'notes_zh': '先用单屏 owner inbox 查看问题、字段分组、候选证据和后续命令；这一步不生成 owner decision。'}, {'step': '2-review-summary', 'command': commands.get('summary_command', ''), 'notes_zh': '先确认 owner 角色、open worksheet、source path 和 owner_route；这一步不生成 owner decision。'}, {'step': '3-check-evidence-readiness', 'command': commands.get('evidence_readiness_command', ''), 'notes_zh': '只读查看 source identity、owner-ready evidence ref 候选和仍需人工回答的字段。'}, {'step': '4-export-forms', 'command': commands.get('forms_jsonl_command', ''), 'output_path_hint': local_path, 'notes_zh': 'owner 可把骨架复制到本地临时 JSONL 后手工填写；工具不写该文件。'}, {'step': '5-validate-filled-forms', 'command_template': commands.get('validate_forms_command_template', ''), 'replace_placeholder_with': local_path, 'notes_zh': '只读校验 owner 填写结果；不通过时不得进入 landing plan。'}, {'step': '6-plan-manual-landing', 'command_template': commands.get('landing_plan_command_template', ''), 'replace_placeholder_with': local_path, 'notes_zh': '生成 no-write 人工落地计划；仍不写 registry、worksheet、migration 或 index。'}, {'step': '7-audit-manual-landing', 'command_template': commands.get('landing_audit_command_template', ''), 'replace_placeholder_with': local_path, 'notes_zh': '人工落地后复核 worksheet、registry、source policy 和 index 是否同步；不能把 audit 当 owner approval。'}], 'must_not': ['不得把 routing_owner 当 reviewed_by', '不得由工具或 AI 代签 owner decision', '不得关闭未签收 owner gate', '不得把 owner-ready package 当作已批准决策'] + [rule for rule in must_not if rule not in {'不得把 routing_owner 当 reviewed_by', '不得由工具或 AI 代签 owner decision', '不得关闭未签收 owner gate', '不得把 owner-ready package 当作已批准决策'}], 'notes_zh': '只读 owner handoff 包；把已有命令排成可交给 owner 的顺序，不生成、不保存、不应用 owner decision。'}

def make_owner_dispatch(rows):
    dispatch_rows = []
    rows_by_scope = {}
    for row in rows:
        owner = row.get('owner', '') or '<missing-owner>'
        source_id = row.get('source_id', '') or ''
        rows_by_scope.setdefault((source_id, owner), []).append(row)
    for (source_id, owner), owner_rows in sorted(rows_by_scope.items()):
        owner_open_rows = [row for row in owner_rows if row['status'] == 'open']
        next_row = sorted(owner_open_rows, key=lambda row: (str(row.get('review_after', '') or '9999-12-31'), str(row.get('id', ''))))[0] if owner_open_rows else {}
        owner_arg = shlex_quote(owner)
        owner_routes = [row.get('owner_route', {}) for row in owner_open_rows if row.get('owner_route')]
        unique_owner_routes = []
        seen_routes = set()
        for route in owner_routes:
            key = (route.get('decision_owner_role', ''), route.get('source_id', ''))
            if key in seen_routes:
                continue
            seen_routes.add(key)
            unique_owner_routes.append(route)
        commands = {'owner_inbox_json_command': f'rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id {source_id} --owner {owner_arg} --owner-inbox --json' if source_id else '', 'summary_command': f'rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id {source_id} --owner {owner_arg} --summary' if source_id else '', 'forms_jsonl_command': f'rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id {source_id} --owner {owner_arg} --forms-jsonl' if source_id else '', 'evidence_readiness_command': f'rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id {source_id} --owner {owner_arg} --evidence-readiness --json' if source_id else '', 'validate_forms_command_template': f"rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id {source_id} --owner {owner_arg} --validate-forms '<owner-decisions.jsonl>' --json" if source_id else '', 'landing_plan_command_template': f"rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id {source_id} --owner {owner_arg} --validate-forms '<owner-decisions.jsonl>' --landing-plan --json" if source_id else '', 'landing_audit_command_template': f"rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id {source_id} --owner {owner_arg} --validate-forms '<owner-decisions.jsonl>' --landing-audit --json" if source_id else ''}
        dispatch_rows.append({'owner': owner, 'source_id': source_id, 'source_ids': [source_id] if source_id else [], 'dispatch_scope_id': f"{source_id or '<missing-source>'}:{owner}", 'mixed_source_owner': False, 'owner_route': unique_owner_routes[0] if len(unique_owner_routes) == 1 else {}, 'owner_routes': unique_owner_routes, 'row_count': len(owner_rows), 'open_count': len(owner_open_rows), 'resolved_count': sum((1 for row in owner_rows if row['status'] == 'resolved')), 'worksheet_ids': [row['id'] for row in owner_open_rows], 'source_paths': [row['source_path'] for row in owner_open_rows], **commands, 'next_focus_command': f"rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id {next_row['source_id']} --owner {owner_arg} --worksheet-id {next_row['id']} --checklist --forms" if next_row else '', 'suggested_owner_packet': make_owner_handoff_packet(owner, source_id, owner_open_rows, next_row, commands), 'notes_zh': '只读 owner 分派包；按 source_id + owner 分派，避免同一 owner 跨 source 时丢失 source scope。用于人工领取、导出骨架、校验和生成 no-write landing plan。owner_route 只说明分派路由，不生成 owner decision，不关闭 gate。'})
    return dispatch_rows

def make_owner_handoff_packets(rows):
    packets = []
    dispatch_rows = make_owner_dispatch(rows)
    for dispatch in dispatch_rows:
        owner = dispatch.get('owner', '')
        source_id = dispatch.get('source_id', '')
        owner_open_rows = [row for row in rows if row.get('status') == 'open' and (row.get('owner', '') or '<missing-owner>') == owner and ((row.get('source_id', '') or '') == source_id)]
        base_packet = dict(dispatch.get('suggested_owner_packet', {}))
        command_fields = ['owner_inbox_json_command', 'summary_command', 'forms_jsonl_command', 'evidence_readiness_command', 'validate_forms_command_template', 'landing_plan_command_template', 'landing_audit_command_template', 'next_focus_command']
        base_packet.update({'packet_type': 'owner-handoff', 'dispatch_scope_id': dispatch.get('dispatch_scope_id', ''), 'source_ids': dispatch.get('source_ids', []), 'mixed_source_owner': dispatch.get('mixed_source_owner', False), 'owner_route': dispatch.get('owner_route', {}), 'owner_routes': dispatch.get('owner_routes', []), 'source_paths': dispatch.get('source_paths', []), 'commands': {field: dispatch.get(field, '') for field in command_fields}, 'owner_inbox': make_owner_inbox(owner_open_rows), 'evidence_readiness': make_evidence_readiness(owner_open_rows), 'forms_jsonl_lines': [json.dumps(make_decision_form(row), ensure_ascii=False, separators=(',', ':')) for row in owner_open_rows], 'owner_checklists': [make_owner_checklist(row) for row in owner_open_rows], 'no_owner_decision_generated': True, 'no_owner_gate_closed': True, 'routing_owner_is_not_reviewed_by': True, 'report_only': True, 'notes_zh': '只读 owner handoff packet；一次性聚合 inbox、证据准备度、JSONL 骨架和命令序列，方便人工 owner 离线签收。不写文件、不代签、不关闭 gate。'})
        packets.append(base_packet)
    return packets

def make_owner_summary(rows):
    summary_rows = []
    source_identity_counts = {}
    owner_counts = {}
    owner_ready_coverage = make_owner_ready_coverage(rows)
    owner_ready_blocking_context = make_owner_ready_blocking_context(rows)
    for row in rows:
        identity_status = row.get('observed_source_identity', {}).get('identity_status', 'unavailable')
        source_identity_counts[identity_status] = source_identity_counts.get(identity_status, 0) + 1
        owner = row.get('owner', '') or '<missing-owner>'
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
        ready_status, ready_items = owner_ready_state(row)
        summary_rows.append({'worksheet_id': row['id'], 'source_id': row['source_id'], 'source_path': row['source_path'], 'owner': row['owner'], 'owner_route': row.get('owner_route', {}), 'status': row['status'], 'worksheet_status': row['worksheet_status'], 'review_after': row['review_after'], 'source_identity_status': identity_status, 'required_owner_field_count': len(row['required_owner_fields']), 'allowed_owner_decisions': row['decision_options'], 'active_exposure_count': len(row['active_registry_items']), 'owner_ready_package_status': ready_status, 'owner_ready_package_count': len(ready_items), 'owner_ready_packages': ready_items, 'focus_command': f"rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id {row['source_id']} --owner {shlex_quote(row['owner'])} --worksheet-id {row['id']} --checklist --forms"})
    return {'status': 'needs-owner-review' if any((row['status'] == 'open' for row in rows)) else 'ok', 'read_only': True, 'row_count': len(rows), 'open_count': sum((1 for row in rows if row['status'] == 'open')), 'resolved_count': sum((1 for row in rows if row['status'] == 'resolved')), 'active_exposure_count': sum((len(row['active_registry_items']) for row in rows)), **owner_ready_coverage, **owner_ready_blocking_context, 'source_identity_counts': dict(sorted(source_identity_counts.items())), 'owner_counts': dict(sorted(owner_counts.items())), 'owner_dispatch': make_owner_dispatch(rows), 'rows': summary_rows, 'notes_zh': '只读 owner gate 总览；用于人工分派和收口，不生成 owner decision，不写文件，不关闭门禁，不提升 active。'}
