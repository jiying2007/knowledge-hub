import argparse
import datetime as dt
import json
import pathlib
import sys
from .owner_form_rules import owner_decision_target_mismatch
from .owner_gates_support import _display_path, compute_source_identity, configure_owner_gates_support, effective_verification_commands, is_filled, is_resolved, load_json, load_jsonl, owner_route_for, path_from_arg, source_execution_root, source_path_values
from .owner_gates_evidence import configure_owner_gates_evidence, make_evidence_readiness, make_owner_inbox, make_owner_ready_blocking_context, make_owner_ready_coverage, owner_ready_items, owner_ready_state
from .owner_gates_forms import make_decision_form, make_landing_audit, make_landing_plan, make_owner_checklist, owner_ready_landing_errors
from .owner_gates_dispatch import make_owner_handoff_packets, make_owner_summary
root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]
parser = argparse.ArgumentParser(description='Print a read-only owner-gate board from owner decision worksheets.')
parser.add_argument('--json', action='store_true')
parser.add_argument('--summary', action='store_true', help='Print a concise owner-facing summary for open rows.')
parser.add_argument('--forms', action='store_true', help='Print copyable owner decision JSONL skeletons for open rows.')
parser.add_argument('--forms-jsonl', action='store_true', help='Print only owner decision JSONL skeleton lines for open rows.')
parser.add_argument('--checklist', action='store_true', help='Print owner-facing closure checklists with intake questions and hard gates.')
parser.add_argument('--evidence-readiness', action='store_true', help='Print read-only evidence readiness and prefill candidates for open rows.')
parser.add_argument('--owner-inbox', action='store_true', help='Print a compact owner-facing inbox with grouped fields, routing and validation commands.')
parser.add_argument('--handoff-packet', action='store_true', help='Print one read-only owner handoff packet with inbox, evidence readiness, forms JSONL and command sequence.')
parser.add_argument('--validate-forms', default='', help='Validate a filled owner decision JSONL file without applying it.')
parser.add_argument('--landing-plan', action='store_true', help='With --validate-forms, print a read-only manual landing plan for valid forms.')
parser.add_argument('--landing-audit', action='store_true', help='With --validate-forms, print a read-only manual landing audit for worksheet/registry/index deltas.')
parser.add_argument('--source-id', default='')
parser.add_argument('--owner', default='', help='Limit output to one exact owner value.')
parser.add_argument('--worksheet-id', default='', help='Limit output to one owner decision worksheet id.')
parser.add_argument('--next-open', action='store_true', help='Limit output to the next open owner gate by review_after and worksheet id.')
parser.add_argument('--status', choices=['all', 'open', 'resolved'], default='open')
args = parser.parse_args(argv)
errors = []
configure_owner_gates_support(root, errors)
configure_owner_gates_evidence(root)
if args.forms_jsonl:
    conflicts = []
    if args.json:
        conflicts.append('--json')
    if args.summary:
        conflicts.append('--summary')
    if args.forms:
        conflicts.append('--forms')
    if args.checklist:
        conflicts.append('--checklist')
    if args.evidence_readiness:
        conflicts.append('--evidence-readiness')
    if args.owner_inbox:
        conflicts.append('--owner-inbox')
    if args.handoff_packet:
        conflicts.append('--handoff-packet')
    if args.validate_forms:
        conflicts.append('--validate-forms')
    if args.landing_plan:
        conflicts.append('--landing-plan')
    if args.landing_audit:
        conflicts.append('--landing-audit')
    if conflicts:
        parser.error(f"cannot combine --forms-jsonl with {', '.join(conflicts)}")
if args.next_open and args.worksheet_id:
    errors.append('--next-open cannot be combined with --worksheet-id')
if args.handoff_packet and (not args.json):
    parser.error('--handoff-packet requires --json')

def validate_forms_file(path, rows):
    form_errors = []
    diagnostics = []
    warnings = []
    forms = []

    def add_form_error(code, message, worksheet_id='', field='', actual='', expected='', action_zh='', line_no=None):
        form_errors.append(message)
        diagnostics.append({'code': code, 'severity': 'error', 'worksheet_id': worksheet_id, 'field': field, 'actual': actual, 'expected': expected, 'line_no': line_no, 'message_zh': message, 'action_zh': action_zh or '请按 owner worksheet 重新填写该字段后再运行 validate-forms。'})

    def date_error_message(prefix, field, value):
        return f'{prefix}: {field} invalid date: {value}'

    def add_invalid_date(prefix, worksheet_id, field, value, line_no):
        add_form_error('invalid-date', date_error_message(prefix, field, value), worksheet_id=worksheet_id, field=field, actual=str(value), expected='YYYY-MM-DD', line_no=line_no, action_zh='请使用 YYYY-MM-DD 格式填写日期字段。')

    def is_valid_date(value):
        try:
            parts = str(value).split('-')
            if len(parts) != 3 or any((not part.isdigit() for part in parts)):
                raise ValueError('not YYYY-MM-DD')
            year, month, day = (int(part) for part in parts)
            dt.date(year, month, day)
            return True
        except Exception:
            return False
    if not path.exists():
        add_form_error('forms-file-missing', f'{path}: missing owner decision forms file', field='path', expected='existing-jsonl-file', action_zh='请先由人工 owner 提供 owner decision JSONL 文件。')
    else:
        try:
            lines = path.read_text().splitlines()
        except Exception as exc:
            add_form_error('forms-file-unreadable', f'{path}: cannot read owner decision forms file: {exc}', field='path', actual=str(path), expected='readable-jsonl-file')
            lines = []
        for line_no, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                forms.append(json.loads(line))
            except Exception as exc:
                add_form_error('invalid-jsonl', f'{path}:{line_no}: invalid jsonl: {exc}', field='jsonl', actual=line[:200], expected='valid-json-object', line_no=line_no, action_zh='请修复该行 JSON 语法后再运行 validate-forms。')
    if not forms:
        add_form_error('forms-empty', f'{path}: no owner decision forms found', field='jsonl', expected='at-least-one-owner-decision-form')
    open_by_id = {row['id']: row for row in rows if row['status'] == 'open'}
    seen = set()
    for index, form in enumerate(forms, 1):
        prefix = f'{path}:{index}'
        worksheet_id = str(form.get('worksheet_id', ''))
        if not worksheet_id:
            add_form_error('missing-worksheet-id', f'{prefix}: missing worksheet_id', field='worksheet_id', expected='open-owner-gate-worksheet-id', line_no=index)
            continue
        if worksheet_id in seen:
            add_form_error('duplicate-worksheet-id', f'{prefix}: duplicate worksheet_id {worksheet_id}', worksheet_id=worksheet_id, field='worksheet_id', actual=worksheet_id, expected='unique-owner-gate-worksheet-id', line_no=index)
            continue
        seen.add(worksheet_id)
        row = open_by_id.get(worksheet_id)
        if not row:
            add_form_error('worksheet-not-open', f'{prefix}: worksheet_id {worksheet_id} does not match an open owner gate row', worksheet_id=worksheet_id, field='worksheet_id', actual=worksheet_id, expected='open-owner-gate-row', line_no=index)
            continue
        if form.get('source_id') != row['source_id']:
            add_form_error('source-id-mismatch', f'{prefix}: source_id mismatch for {worksheet_id}', worksheet_id=worksheet_id, field='source_id', actual=str(form.get('source_id', '')), expected=row['source_id'], line_no=index)
        if form.get('source_path') != row['source_path']:
            add_form_error('source-path-mismatch', f'{prefix}: source_path mismatch for {worksheet_id}', worksheet_id=worksheet_id, field='source_path', actual=str(form.get('source_path', '')), expected=row['source_path'], line_no=index)
        owner_decision = form.get('owner_decision', '')
        if not is_filled(owner_decision):
            add_form_error('missing-owner-decision', f'{prefix}: missing owner_decision', worksheet_id=worksheet_id, field='owner_decision', expected='one-of-decision_options', line_no=index)
        elif row['decision_options'] and owner_decision not in row['decision_options']:
            add_form_error('owner-decision-not-allowed', f"{prefix}: owner_decision {owner_decision!r} is not in allowed decisions {row['decision_options']}", worksheet_id=worksheet_id, field='owner_decision', actual=str(owner_decision), expected=row['decision_options'], line_no=index)
        target_decision = form.get('target_decision', '')
        if is_filled(target_decision) and row.get('target_candidates') and (target_decision not in row['target_candidates']):
            add_form_error('target-decision-not-candidate', f"{prefix}: target_decision {target_decision!r} is not in target candidates {row['target_candidates']}", worksheet_id=worksheet_id, field='target_decision', actual=str(target_decision), expected=row['target_candidates'], line_no=index)
        if is_filled(owner_decision) and is_filled(target_decision):
            mismatch = owner_decision_target_mismatch(owner_decision, target_decision)
            if mismatch:
                add_form_error('owner-decision-target-mismatch', f"{prefix}: owner_decision {owner_decision!r} does not form a valid pair with target_decision {target_decision!r}: {mismatch['reason_zh']}", worksheet_id=worksheet_id, field='target_decision', actual={'owner_decision': owner_decision, 'target_decision': target_decision}, expected=mismatch['expected'], line_no=index, action_zh='请保持 owner_decision 与 target_decision 成对一致；不要使用旧 domains/projects/domains/personal 入口，也不要把 reference-only/no-migration 与项目落地路径混用。')
        for field in row['required_owner_fields']:
            if not is_filled(form.get(field)):
                add_form_error('missing-required-owner-field', f'{prefix}: missing required field {field}', worksheet_id=worksheet_id, field=field, expected='filled-owner-field', line_no=index)
        for field in ['target_decision', 'reviewed_by', 'reviewed_at', 'review_after', 'source_status', 'evidence_refs', 'status_reason']:
            if not is_filled(form.get(field)):
                add_form_error('missing-required-review-field', f'{prefix}: missing required review field {field}', worksheet_id=worksheet_id, field=field, expected='filled-review-field', line_no=index)
        owner_route = row.get('owner_route', {})
        routing_status = str(owner_route.get('routing_status', ''))
        routing_owner = str(owner_route.get('routing_owner', ''))
        reviewed_by = str(form.get('reviewed_by', ''))
        if routing_status == 'needs-human-assignment' and routing_owner and (reviewed_by == routing_owner):
            add_form_error('reviewed-by-routing-owner', f'{prefix}: reviewed_by must be a real owner, not routing_owner {routing_owner!r} for {worksheet_id}', worksheet_id=worksheet_id, field='reviewed_by', actual=reviewed_by, expected='real-human-owner', line_no=index, action_zh='reviewed_by 必须由真实人工 owner 填写，不能使用路由占位 owner。')
        if is_filled(form.get('reviewed_at')):
            if not is_valid_date(form.get('reviewed_at')):
                add_invalid_date(prefix, worksheet_id, 'reviewed_at', form.get('reviewed_at'), index)
        if is_filled(form.get('review_after')):
            if not is_valid_date(form.get('review_after')):
                add_invalid_date(prefix, worksheet_id, 'review_after', form.get('review_after'), index)
        identity = row.get('observed_source_identity', {})
        identity_status = str(identity.get('identity_status', 'unavailable'))
        if identity_status != 'match':
            add_form_error('source-identity-not-match', f'{prefix}: observed source identity is {identity_status}, expected match before owner landing', worksheet_id=worksheet_id, field='observed_source_identity', actual=identity_status, expected='match', line_no=index)
        else:
            observed_sha256 = str(identity.get('observed_sha256', ''))
            observed_size = str(identity.get('observed_size', ''))
            if observed_sha256 and str(form.get('source_sha256', '')) != observed_sha256:
                add_form_error('source-sha256-mismatch', f'{prefix}: source_sha256 does not match observed source identity for {worksheet_id}', worksheet_id=worksheet_id, field='source_sha256', actual=str(form.get('source_sha256', '')), expected=observed_sha256, line_no=index)
            if observed_size and str(form.get('source_size', '')) != observed_size:
                add_form_error('source-size-mismatch', f'{prefix}: source_size does not match observed source identity for {worksheet_id}', worksheet_id=worksheet_id, field='source_size', actual=str(form.get('source_size', '')), expected=observed_size, line_no=index)
        if 'must_not' in form and form.get('must_not') != row['must_not']:
            add_form_error('must-not-tampered', f'{prefix}: must_not differs from worksheet guardrails', worksheet_id=worksheet_id, field='must_not', actual=form.get('must_not', ''), expected=row['must_not'], line_no=index, action_zh='请恢复 worksheet 原始 guardrails；owner 表单不得修改 must_not。')
        if 'allowed_owner_decisions' in form and form.get('allowed_owner_decisions') != row['decision_options']:
            add_form_error('allowed-decisions-tampered', f'{prefix}: allowed_owner_decisions differs from worksheet decision options', worksheet_id=worksheet_id, field='allowed_owner_decisions', actual=form.get('allowed_owner_decisions', ''), expected=row['decision_options'], line_no=index, action_zh='请恢复 worksheet 原始 decision options；owner 表单不得修改 allowed_owner_decisions。')
        if 'target_candidates' in form and form.get('target_candidates') != row['target_candidates']:
            add_form_error('target-candidates-tampered', f'{prefix}: target_candidates differs from worksheet target candidates', worksheet_id=worksheet_id, field='target_candidates', actual=form.get('target_candidates', ''), expected=row['target_candidates'], line_no=index, action_zh='请恢复 worksheet 原始 target candidates；owner 表单不得修改 target_candidates。')
    submitted_open_ids = sorted((worksheet_id for worksheet_id in seen if worksheet_id in open_by_id))
    missing_open_ids = sorted((worksheet_id for worksheet_id in open_by_id if worksheet_id not in seen))
    if len(open_by_id) <= 1:
        coverage_status = 'single-worksheet'
    elif missing_open_ids:
        coverage_status = 'partial'
    else:
        coverage_status = 'complete'
    coverage = {'filtered_open_count': len(open_by_id), 'submitted_form_count': len(forms), 'submitted_open_count': len(submitted_open_ids), 'submitted_worksheet_ids': submitted_open_ids, 'missing_open_worksheet_ids': missing_open_ids, 'coverage_status': coverage_status, 'notes_zh': '本字段只说明 validate-forms 覆盖了当前过滤范围内哪些 open worksheet；partial 不阻断分批签收，但 landing 后仍需继续处理 missing_open_worksheet_ids。'}
    if missing_open_ids:
        warnings.append('validate-forms covers a subset of current open owner gates; remaining open worksheets: ' + ', '.join(missing_open_ids))
    status = 'pass' if not form_errors else 'fail'
    return {'status': status, 'path': str(path), 'form_count': len(forms), 'checked_count': len(seen), 'coverage': coverage, 'filtered_open_count': coverage['filtered_open_count'], 'submitted_form_count': coverage['submitted_form_count'], 'submitted_worksheet_ids': coverage['submitted_worksheet_ids'], 'missing_open_worksheet_ids': coverage['missing_open_worksheet_ids'], 'coverage_status': coverage['coverage_status'], 'forms': forms, 'error_count': len(form_errors), 'warning_count': len(warnings), 'errors': form_errors, 'warnings': warnings, 'diagnostics': diagnostics}
sources_payload = load_json(root / 'registry' / 'sources.json')
sources_rows = list(sources_payload.get('sources', [])) + load_jsonl(root / 'registry' / 'retired-sources.jsonl')
source_roots = {str(source.get('id', '')): str(source.get('path', '')) for source in sources_rows if isinstance(source, dict)}
owner_routing_payload = load_json(root / 'registry' / 'owner-routing.json')
owner_route_map = {}
for route in owner_routing_payload.get('routes', []):
    key = (str(route.get('source_id', '')), str(route.get('decision_owner_role', '')))
    if key == ('', ''):
        continue
    owner_route_map[key] = {'decision_owner_role': str(route.get('decision_owner_role', '')), 'source_id': str(route.get('source_id', '')), 'routing_status': str(route.get('routing_status', '')), 'routing_owner': str(route.get('routing_owner', '')), 'candidate_registry_owners': route.get('candidate_registry_owners', []), 'required_real_owner_zh': str(route.get('required_real_owner_zh', '')), 'escalation_zh': str(route.get('escalation_zh', '')), 'must_not': route.get('must_not', []), 'notes_zh': str(route.get('notes_zh', '')), 'no_owner_decision_generated': True}
configure_owner_gates_support(root, errors, source_roots_value=source_roots, owner_route_map_value=owner_route_map)
items = load_jsonl(root / 'registry' / 'items.jsonl')
items_by_source_path = {}
active_by_source_path = {}
for item in items:
    source = item.get('source') if isinstance(item.get('source'), dict) else {}
    source_id = source.get('source_id')
    source_paths = source_path_values(source.get('source_path'))
    if not source_id or not source_paths:
        continue
    item_ref = {'id': item.get('id', ''), 'kind': item.get('kind', ''), 'status': item.get('status', ''), 'path': item.get('path', ''), 'review_status': item.get('review_status', ''), 'tags': item.get('tags', []), 'source': source}
    for source_path in source_paths:
        key = (source_id, source_path)
        items_by_source_path.setdefault(key, []).append(item_ref)
        if item.get('status') == 'active':
            active_by_source_path.setdefault(key, []).append(item_ref)
worksheet_paths = sorted((root / 'artifacts' / 'manifests').glob('*owner-decision-worksheets-*.jsonl'))
if not worksheet_paths:
    errors.append('missing artifacts/manifests/*owner-decision-worksheets-*.jsonl')
intake_paths = sorted((root / 'artifacts' / 'manifests').glob('*owner-intake-package-*.jsonl'))
intake_by_worksheet = {}
intake_by_source_path = {}
for intake_path in intake_paths:
    for intake in load_jsonl(intake_path):
        worksheet_id = str(intake.get('next_worksheet', ''))
        if worksheet_id:
            intake_by_worksheet[worksheet_id] = intake
        for source_path in source_path_values(intake.get('source_path', '')):
            intake_by_source_path[source_path] = intake
rows = []
for worksheet_path in worksheet_paths:
    for row in load_jsonl(worksheet_path):
        row_id = str(row.get('id', ''))
        if args.worksheet_id and row_id != args.worksheet_id:
            continue
        source_id = str(row.get('source_id', ''))
        source_path = str(row.get('source_path', ''))
        if args.source_id and source_id != args.source_id:
            continue
        owner = row.get('owner_required') or row.get('owner_candidate') or ''
        if args.owner and owner != args.owner:
            continue
        key = (source_id, source_path)
        resolved = is_resolved(row)
        row_status = 'resolved' if resolved else 'open'
        if args.status != 'all' and row_status != args.status:
            continue
        intake = intake_by_worksheet.get(row_id) or intake_by_source_path.get(source_path, {})
        execution_root = source_execution_root(source_id)
        row_entry = {'id': row_id, 'source_id': source_id, 'source_path': source_path, 'owner': owner, 'owner_route': owner_route_for(source_id, owner), 'status': row_status, 'worksheet_status': row.get('worksheet_status') or row.get('status') or row.get('default_state') or '', 'decision_options': row.get('decision_options', []), 'target_candidates': row.get('target_candidates', []), 'required_owner_fields': row.get('required_owner_fields', []), 'must_not': row.get('must_not', []), 'review_after': row.get('review_after', ''), 'worksheet': str(worksheet_path.relative_to(root)), 'registry_items': items_by_source_path.get(key, []), 'active_registry_items': active_by_source_path.get(key, []), 'source_execution_root': execution_root, 'verification_cwd': execution_root, 'verification_commands': effective_verification_commands(row, source_id), 'owner_question_zh': intake.get('owner_question_zh', ''), 'default_state': intake.get('default_state', ''), 'allowed_next_status': intake.get('allowed_next_status', []), 'hard_gate_summary': intake.get('hard_gate_summary', ''), 'hard_gate': intake.get('hard_gate', ''), 'observed_source_identity': compute_source_identity(row)}
        ready_status, ready_packages = owner_ready_state(row_entry)
        row_entry['owner_ready_package_status'] = ready_status
        row_entry['owner_ready_package_status_source'] = 'knowledge-owner-gates.owner_ready_state'
        row_entry['owner_ready_strong_validation'] = True
        row_entry['owner_ready_package_count'] = len(ready_packages)
        row_entry['owner_ready_packages'] = ready_packages
        row_entry['owner_ready_package_ids'] = [str(item.get('id', '')) for item in ready_packages if isinstance(item, dict) and item.get('id')]
        row_entry['owner_ready_package_paths'] = [str(item.get('path', '')) for item in ready_packages if isinstance(item, dict) and item.get('path')]
        rows.append(row_entry)
if args.next_open and (not errors):
    rows = sorted([row for row in rows if row['status'] == 'open'], key=lambda row: (str(row.get('review_after', '') or '9999-12-31'), str(row.get('id', ''))))[:1]
open_count = sum((1 for row in rows if row['status'] == 'open'))
resolved_count = sum((1 for row in rows if row['status'] == 'resolved'))
active_exposure_count = sum((len(row['active_registry_items']) for row in rows))
owner_ready_coverage = make_owner_ready_coverage(rows)
owner_ready_blocking_context = make_owner_ready_blocking_context(rows)
owner_review_status = 'needs-owner-review' if open_count else 'complete'
owner_gate_status = 'owner-gates-open' if open_count else 'owner-gates-complete'
result_status = 'blocked' if errors else 'needs-fix' if active_exposure_count else 'ok'
exit_status = 1 if errors or active_exposure_count else 0
result = {'status': result_status, 'status_scope': 'tool-health', 'owner_review_status': owner_review_status, 'owner_gate_status': owner_gate_status, 'root': _display_path(root), 'read_only': True, 'source_id': args.source_id, 'owner': args.owner, 'worksheet_id': args.worksheet_id, 'next_open': args.next_open, 'filter_status': args.status, 'source_identity_read_policy': {'source_identity_read_mode': 'read-bytes-for-hash', 'source_body_read_for_hash': True, 'source_body_copied': False, 'source_project_written': False, 'owner_gate_mutation': False, 'notes_zh': 'owner-gates 为 source identity/hash 匹配会只读读取 source 文件字节；不会复制 source 正文、不会写源项目、不会生成 owner decision、不会关闭 gate。'}, 'worksheet_count': len(worksheet_paths), 'row_count': len(rows), 'open_count': open_count, 'resolved_count': resolved_count, 'active_exposure_count': active_exposure_count, **owner_ready_coverage, **owner_ready_blocking_context, 'errors': errors, 'rows': rows}
if args.summary:
    result['owner_summary'] = make_owner_summary(rows)
if args.forms:
    result['decision_forms'] = [make_decision_form(row) for row in rows if row['status'] == 'open']
if args.evidence_readiness:
    result['evidence_readiness'] = make_evidence_readiness([row for row in rows if row['status'] == 'open'])
if args.owner_inbox:
    result['owner_inbox'] = make_owner_inbox([row for row in rows if row['status'] == 'open'])
if args.handoff_packet:
    result['owner_handoff_packets'] = make_owner_handoff_packets(rows)
if args.checklist:
    result['owner_checklists'] = [make_owner_checklist(row) for row in rows if row['status'] == 'open']
form_validation = None
if args.validate_forms:
    form_validation = validate_forms_file(path_from_arg(args.validate_forms), rows)
    result['form_validation'] = form_validation
    if form_validation['status'] != 'pass':
        result_status = 'needs-fix'
        result['status'] = result_status
        exit_status = 1
landing_plan = None
if args.landing_plan:
    if not args.validate_forms:
        landing_plan = {'status': 'blocked', 'read_only': True, 'reason': '--landing-plan requires --validate-forms <jsonl>', 'steps': []}
        result['landing_plan'] = landing_plan
        result_status = 'needs-fix'
        result['status'] = result_status
        exit_status = 1
    else:
        landing_plan = make_landing_plan(form_validation, rows)
        result['landing_plan'] = landing_plan
landing_audit = None
if args.landing_audit:
    if not args.validate_forms:
        landing_audit = {'status': 'blocked', 'read_only': True, 'reason': '--landing-audit requires --validate-forms <jsonl>', 'rows': []}
        result['landing_audit'] = landing_audit
        result_status = 'needs-fix'
        result['status'] = result_status
        exit_status = 1
    else:
        audit_blocked = form_validation is None or form_validation.get('status') != 'pass'
        owner_ready_errors = owner_ready_landing_errors(form_validation, rows)
        if owner_ready_errors:
            audit_blocked = True
        landing_audit = make_landing_audit(form_validation, rows, audit_blocked, owner_ready_errors)
        result['landing_audit'] = landing_audit
        if landing_audit.get('status') == 'blocked':
            result_status = 'needs-fix'
            result['status'] = result_status
            exit_status = 1
if args.forms_jsonl:
    if errors:
        for error in errors:
            print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(exit_status)
    if active_exposure_count:
        print('ERROR: active exposure exists; owner-gated rows must stay out of active until owner decisions are closed.', file=sys.stderr)
        sys.exit(exit_status)
    forms_jsonl_rows = [row for row in rows if row['status'] == 'open']
    if not forms_jsonl_rows and (args.source_id or args.owner or args.worksheet_id):
        hint_source_id = args.source_id or '<source-id>'
        print('WARNING: no open owner decision forms matched the current filters.', file=sys.stderr)
        print(f'WARNING: matched_row_count={len(rows)} matched_open_count=0', file=sys.stderr)
        print(f'WARNING: hint_command=rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id {hint_source_id} --summary --json', file=sys.stderr)
    for form in [make_decision_form(row) for row in forms_jsonl_rows]:
        print(json.dumps(form, ensure_ascii=False, separators=(',', ':')))
    sys.exit(exit_status)
if args.json:
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(exit_status)
print('# Knowledge Owner Gates')
print()
print('本命令只读汇总 owner decision worksheets，不创建、不修改、不提交、不提升任何文件。')
print()
print(f"- status: {result['status']}")
print(f'- worksheets: {len(worksheet_paths)}')
print(f'- rows: {len(rows)}')
print(f'- open: {open_count}')
print(f'- resolved: {resolved_count}')
print(f'- active exposure: {active_exposure_count}')
print(f"- owner-ready packages: {owner_ready_coverage['owner_ready_package_coverage']}")
print(f"- owner-ready missing: {owner_ready_coverage['owner_ready_missing_count']}")
print(f"- owner-ready invalid: {owner_ready_coverage['owner_ready_invalid_count']}")
print(f"- owner-ready duplicate: {owner_ready_coverage['owner_ready_duplicate_count']}")
print(f"- owner-ready blocking status: {owner_ready_blocking_context['owner_ready_blocking_status']}")
print(f"- owner-ready note: {owner_ready_blocking_context['owner_ready_status_note_zh']}")
if args.source_id:
    print(f'- source_id: {args.source_id}')
if args.owner:
    print(f'- owner: {args.owner}')
print(f'- filter: {args.status}')
for error in errors:
    print(f'- ERROR: {error}')
if active_exposure_count:
    print('- ERROR: active exposure exists; run knowledge-check and keep owner-gated rows out of active until owner decisions are closed.')
if args.summary:
    summary = make_owner_summary(rows)
    print()
    print('## Owner Gate Summary')
    print()
    print('本摘要只读输出 owner gate 总览，供人工分派、排期和收口；不生成 owner decision，不写文件、不关闭门禁、不提升 active。')
    print(f"- summary_status: {summary['status']}")
    print(f"- rows: {summary['row_count']}")
    print(f"- open: {summary['open_count']}")
    print(f"- resolved: {summary['resolved_count']}")
    print(f"- active_exposure: {summary['active_exposure_count']}")
    print(f"- owner_ready_packages: {summary['owner_ready_package_count']}/{summary['row_count']}")
    print(f"- owner_ready_missing: {summary['owner_ready_missing_count']}")
    if summary['source_identity_counts']:
        identity_parts = [f'{key}={value}' for key, value in summary['source_identity_counts'].items()]
        print(f"- source_identity: {', '.join(identity_parts)}")
    if summary['owner_counts']:
        owner_parts = [f'{key}={value}' for key, value in summary['owner_counts'].items()]
        print(f"- owners: {', '.join(owner_parts)}")
    routed = [f"{item['owner']}=>{item.get('owner_route', {}).get('routing_owner', '<unmapped>') or '<unmapped>'}" for item in summary['owner_dispatch']]
    if routed:
        print(f"- owner_routes: {', '.join(routed)}")
    print()
    print('### Owner Dispatch')
    print()
    print('| owner | route | open | evidence readiness | forms-jsonl | validate | landing plan | landing audit | next focus |')
    print('|---|---|---:|---|---|---|---|---|---|')
    for item in summary['owner_dispatch']:
        route = item.get('owner_route', {})
        route_text = route.get('routing_owner') or route.get('routing_status') or '<unmapped>'
        print(f"| {item['owner']} | {route_text} | {item['open_count']} | `{item['evidence_readiness_command']}` | `{item['forms_jsonl_command']}` | `{item['validate_forms_command_template']}` | `{item['landing_plan_command_template']}` | `{item['landing_audit_command_template']}` | `{item['next_focus_command']}` |")
    print()
    print('| worksheet | source path | owner | identity | owner-ready | required fields | focus command |')
    print('|---|---|---|---|---|---:|---|')
    for item in summary['rows']:
        print(f"| `{item['worksheet_id']}` | `{item['source_path']}` | {item['owner'] or '<missing-owner>'} | {item['source_identity_status']} | {item['owner_ready_package_status']} | {item['required_owner_field_count']} | `{item['focus_command']}` |")
if args.owner_inbox:
    inbox = make_owner_inbox([row for row in rows if row['status'] == 'open'])
    print()
    print('## Owner Inbox')
    print()
    print('本视图只读汇总 owner 待办，不生成 owner decision，不写文件，不关闭 gate。')
    print(f"- inbox_status: {inbox['status']}")
    print(f"- rows: {inbox['row_count']}")
    if inbox['owner_counts']:
        owner_parts = [f'{key}={value}' for key, value in inbox['owner_counts'].items()]
        print(f"- owners: {', '.join(owner_parts)}")
    print()
    print('| worksheet | owner | route | source path | fields | owner-ready | focus |')
    print('|---|---|---|---|---:|---|---|')
    for item in inbox['rows']:
        route = item.get('owner_route', {})
        route_text = route.get('routing_owner') or route.get('routing_status') or '<unmapped>'
        fields = item.get('required_field_groups', {}).get('field_count', 0)
        print(f"| `{item['worksheet_id']}` | {item['owner']} | {route_text} | `{item['source_path']}` | {fields} | {item['owner_ready_package_status']} | `{item['commands']['focus_command']}` |")
    print()
    print('### 字段分组和只读候选')
    print()
    for item in inbox['rows']:
        groups = item.get('required_field_groups', {})
        prefill = item.get('read_only_prefill_candidates', {})
        manual = ', '.join(groups.get('manual_decision_fields', [])[:8]) or '-'
        candidates = ', '.join(groups.get('copyable_candidate_fields', [])[:8]) or '-'
        evidence = ', '.join(groups.get('evidence_fields', [])[:8]) or '-'
        candidate_keys = [key for key in ['source_sha256_candidate', 'source_size_candidate', 'review_after_candidate'] if prefill.get(key)]
        candidate_text = ', '.join(candidate_keys) or '-'
        print(f"- `{item['worksheet_id']}`: manual=`{manual}`; candidates=`{candidates}`; evidence=`{evidence}`; read_only_prefill=`{candidate_text}`")
        print(f"  - forms-jsonl: `{item['commands']['forms_jsonl_command']}`")
        print(f"  - evidence-readiness: `{item['commands']['evidence_readiness_command']}`")
        print(f"  - validate template: `{item['commands']['validate_forms_command_template']}`")
    print()
    print('### 使用边界')
    print()
    print('- routing_owner 只是分派提示，不能填入 reviewed_by。')
    print('- source_sha256/source_size/review_after 只是候选值，必须由真实 owner 人工签收。')
    print('- validate / landing plan / landing audit 都是只读命令；人工落地前不得关闭 owner gate。')
if form_validation:
    print()
    print('## Owner Decision Form Validation')
    print()
    print('本校验只读检查 owner 回填 JSONL，不写文件、不关闭门禁、不提升 active。')
    print(f"- status: {form_validation['status']}")
    print(f"- forms: {form_validation['form_count']}")
    print(f"- checked: {form_validation['checked_count']}")
    print(f"- coverage_status: {form_validation['coverage_status']}")
    print(f"- filtered_open_count: {form_validation['filtered_open_count']}")
    print(f"- missing_open_worksheet_ids: {', '.join(form_validation['missing_open_worksheet_ids']) or '-'}")
    print(f"- errors: {form_validation['error_count']}")
    print(f"- warnings: {form_validation['warning_count']}")
    for item in form_validation['errors'][:20]:
        print(f'- ERROR: {item}')
    for item in form_validation['warnings'][:20]:
        print(f'- WARNING: {item}')
if landing_plan:
    print()
    print('## Owner Decision Landing Plan')
    print()
    print('本计划只读输出人工落地步骤，不写文件、不关闭门禁、不提升 active。')
    print(f"- status: {landing_plan['status']}")
    if landing_plan.get('reason'):
        print(f"- reason: {landing_plan['reason']}")
    if landing_plan.get('landing_scope'):
        scope = landing_plan['landing_scope']
        print(f"- landing_scope: {scope.get('coverage_status', '<missing>')} submitted={scope.get('submitted_open_count', 0)}/{scope.get('filtered_open_count', 0)}")
        print(f"- remaining_open_after_this_batch: {', '.join(landing_plan.get('remaining_open_after_this_batch', [])) or '-'}")
    owner_ready_gate = landing_plan.get('owner_ready_gate', {})
    if owner_ready_gate:
        print(f"- owner_ready_gate: {owner_ready_gate.get('status', '<missing-status>')}")
        print(f"- owner_ready_gate_errors: {owner_ready_gate.get('error_count', 0)}")
    if landing_plan.get('required_manual_files'):
        print('- required_manual_files:')
        for item in landing_plan['required_manual_files']:
            print(f'  - `{item}`')
    if landing_plan.get('verification_commands'):
        print('- verification_commands:')
        for item in landing_plan['verification_commands']:
            print(f'  - `{item}`')
    for step in landing_plan.get('steps', []):
        print()
        print(f"### {step['worksheet_id']}")
        print(f"- source_path: `{step['source_path']}`")
        print(f"- owner_decision: `{step['owner_decision']}`")
        print(f"- target_decision: `{step['target_decision']}`")
        print('- manual_actions:')
        for action in step['manual_actions_zh']:
            print(f'  - {action}')
        if step.get('worksheet_verification_commands'):
            print('- worksheet_verification_commands:')
            for command in step['worksheet_verification_commands']:
                print(f'  - `{command}`')
if landing_audit:
    print()
    print('## Owner Decision Landing Audit')
    print()
    print('本审计只读列出人工落地后必须核对的 worksheet、registry、source policy 和 index 变化；不写文件、不关闭门禁。')
    print(f"- status: {landing_audit['status']}")
    print(f"- rows: {landing_audit['row_count']}")
    if landing_audit.get('landing_scope'):
        scope = landing_audit['landing_scope']
        print(f"- landing_scope: {scope.get('coverage_status', '<missing>')} submitted={scope.get('submitted_open_count', 0)}/{scope.get('filtered_open_count', 0)}")
        print(f"- remaining_open_after_this_batch: {', '.join(landing_audit.get('remaining_open_after_this_batch', [])) or '-'}")
    print(f"- owner_ready_errors: {landing_audit['owner_ready_error_count']}")
    if landing_audit.get('required_manual_files'):
        print('- required_manual_files:')
        for item in landing_audit['required_manual_files']:
            print(f'  - `{item}`')
    for row in landing_audit.get('rows', []):
        print()
        print(f"### {row['worksheet_id']}")
        print(f"- source_path: `{row['source_path']}`")
        print(f"- audit_status: {row['status']}")
        worksheet_resolution = row.get('worksheet_resolution_status', {})
        print(f"- worksheet_file: `{worksheet_resolution.get('worksheet_file', '')}`")
        print(f"- must_update_worksheet_row: {worksheet_resolution.get('must_update_worksheet_row', False)}")
        if worksheet_resolution.get('missing_fields_in_form'):
            print(f"- missing_fields_in_form: {', '.join(worksheet_resolution['missing_fields_in_form'])}")
        deltas = row.get('expected_manual_deltas', {})
        if deltas:
            print('- expected_manual_deltas:')
            for key, value in deltas.items():
                if isinstance(value, list):
                    print(f"  - {key}: {', '.join(value)}")
                else:
                    print(f'  - {key}: {value}')
        if row.get('post_landing_commands'):
            print('- post_landing_commands:')
            for command in row['post_landing_commands']:
                print(f'  - `{command}`')
if args.evidence_readiness:
    readiness = make_evidence_readiness([row for row in rows if row['status'] == 'open'])
    print()
    print('## Owner Evidence Readiness')
    print()
    print('本视图只读展示 owner 签收前的候选证据和值，不写正式字段、不关闭门禁。')
    print(f"- status: {readiness['status']}")
    print(f"- rows: {readiness['row_count']}")
    if readiness['status_counts']:
        parts = [f'{key}={value}' for key, value in readiness['status_counts'].items()]
        print(f"- status_counts: {', '.join(parts)}")
    for item in readiness['rows']:
        print()
        print(f"### {item['worksheet_id']}")
        print(f"- source_path: `{item['source_path']}`")
        print(f"- owner: {item['owner'] or '<missing-owner>'}")
        print(f"- readiness_status: {item['readiness_status']}")
        print(f"- source_identity_status: {item['source_identity_status']}")
        print(f"- owner_ready_package_status: {item['owner_ready_package_status']}")
        if item['mechanical_known_fields']:
            print(f"- mechanical_known_fields: {', '.join(item['mechanical_known_fields'])}")
        if item['owner_answer_required_fields']:
            print(f"- owner_answer_required_fields: {', '.join(item['owner_answer_required_fields'])}")
        if item['command_evidence_required_fields']:
            print(f"- command_evidence_required_fields: {', '.join(item['command_evidence_required_fields'])}")
        if item['owner_ready_evidence_refs']:
            print('- owner_ready_evidence_refs:')
            for ref in item['owner_ready_evidence_refs']:
                print(f'  - `{ref}`')
        if item['safe_command_candidates']:
            print('- safe_command_candidates:')
            for command in item['safe_command_candidates']:
                print(f"  - `{command['command']}`")
        if item['project_command_candidates']:
            print('- project_command_candidates:')
            for command in item['project_command_candidates']:
                print(f"  - `{command['command']}`")
if args.forms:
    print()
    print('## Owner Decision JSONL Skeletons')
    print()
    print('以下骨架只供 owner 人工复制、填写和复核；本命令不写文件、不关闭门禁、不提升 active。')
    print('写入任何 owner decision 前，必须补齐证据引用、reviewed_by、reviewed_at、source hash/size 和 status_reason。')
    for form in [make_decision_form(row) for row in rows if row['status'] == 'open']:
        print(json.dumps(form, ensure_ascii=False, separators=(',', ':')))
if args.checklist:
    print()
    print('## Owner Closure Checklists')
    print()
    print('以下清单把 owner intake 与 worksheet 合并到一个只读视图；不能替代 owner 决策，不能关闭门禁。')
    for checklist in [make_owner_checklist(row) for row in rows if row['status'] == 'open']:
        print()
        print(f"### {checklist['worksheet_id']}")
        print(f"- source_path: `{checklist['source_path']}`")
        print(f"- owner: {checklist['owner'] or '<missing-owner>'}")
        if checklist['owner_question_zh']:
            print(f"- owner_question: {checklist['owner_question_zh']}")
        if checklist['default_state']:
            print(f"- default_state: {checklist['default_state']}")
        if checklist['hard_gate_summary']:
            print(f"- hard_gate_summary: {checklist['hard_gate_summary']}")
        if checklist['hard_gate']:
            print(f"- hard_gate: {checklist['hard_gate']}")
        owner_route = checklist.get('owner_route', {})
        if owner_route:
            print(f"- owner_route: {owner_route.get('routing_status', '<missing-status>')} via {owner_route.get('routing_owner', '<missing-routing-owner>')}")
            if owner_route.get('required_real_owner_zh'):
                print(f"- required_real_owner: {owner_route['required_real_owner_zh']}")
            if owner_route.get('escalation_zh'):
                print(f"- escalation: {owner_route['escalation_zh']}")
        source_identity = checklist.get('observed_source_identity', {})
        if source_identity:
            print(f"- observed_source_identity: {source_identity.get('identity_status', '<missing-status>')} sha256={source_identity.get('observed_sha256', '<missing-sha256>')} size={source_identity.get('observed_size', '<missing-size>')}")
        if checklist['allowed_owner_decisions']:
            print(f"- allowed_owner_decisions: {', '.join((str(item) for item in checklist['allowed_owner_decisions']))}")
        if checklist['required_owner_fields']:
            print(f"- required_owner_fields: {', '.join((str(item) for item in checklist['required_owner_fields']))}")
        if checklist['must_not']:
            print(f"- must_not: {', '.join((str(item) for item in checklist['must_not']))}")
detail_rows = [] if args.summary or args.forms else rows
for row in detail_rows:
    active_marker = 'YES' if row['active_registry_items'] else 'no'
    print()
    print(f"## {row['source_path'] or row['id']}")
    print()
    print(f"- id: `{row['id']}`")
    print(f"- source_id: `{row['source_id']}`")
    print(f"- owner: {row['owner'] or '<missing-owner>'}")
    owner_route = row.get('owner_route', {})
    if owner_route:
        print(f"- owner_route: {owner_route.get('routing_status', '<missing-status>')} via {owner_route.get('routing_owner', '<missing-routing-owner>')}")
    print(f"- status: {row['status']} ({row['worksheet_status'] or '<missing-worksheet-status>'})")
    print(f"- review_after: {row['review_after'] or '<missing-review_after>'}")
    print(f'- active exposure: {active_marker}')
    ready_items = owner_ready_items(row)
    ready_status, _ = owner_ready_state(row)
    print(f'- owner-ready package: {ready_status}')
    if row['decision_options']:
        print(f"- decision_options: {', '.join((str(item) for item in row['decision_options']))}")
    if row['required_owner_fields']:
        print(f"- required_owner_fields: {', '.join((str(item) for item in row['required_owner_fields'][:8]))}")
    if row['must_not']:
        print(f"- must_not: {', '.join((str(item) for item in row['must_not'][:5]))}")
    source_identity = row.get('observed_source_identity', {})
    if source_identity:
        print(f"- observed_source_identity: {source_identity.get('identity_status', '<missing-status>')} sha256={source_identity.get('observed_sha256', '<missing-sha256>')} size={source_identity.get('observed_size', '<missing-size>')}")
    if row['registry_items']:
        print('- registry_items:')
        for item in row['registry_items']:
            print(f"  - `{item['id']}` status={item['status'] or '<missing-status>'} review_status={item['review_status'] or '<missing-review-status>'} path={item['path'] or '<missing-path>'}")
    if args.forms and row['status'] == 'open':
        print()
        print('```json')
        print(json.dumps(make_decision_form(row), ensure_ascii=False, sort_keys=True))
        print('```')
print()
print('## 验证')
print()
print('```bash')
print('rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics')
print('```')
sys.exit(exit_status)
