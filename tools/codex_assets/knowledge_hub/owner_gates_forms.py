from .owner_gates_evidence import make_read_only_prefill_candidates, owner_ready_state
from .owner_gates_support import default_field_value, is_filled

def make_decision_form(row):
    form = {'worksheet_id': row['id'], 'source_id': row['source_id'], 'source_path': row['source_path'], 'worksheet': row['worksheet'], 'owner': row['owner'], 'status': row.get('status', ''), 'worksheet_status': row.get('worksheet_status', ''), 'owner_question_zh': row.get('owner_question_zh', ''), 'default_state': row.get('default_state', ''), 'allowed_next_status': row.get('allowed_next_status', []), 'hard_gate_summary': row.get('hard_gate_summary', ''), 'hard_gate': row.get('hard_gate', ''), 'owner_route': row.get('owner_route', {}), 'observed_source_identity': row.get('observed_source_identity', {}), 'read_only_prefill_candidates': make_read_only_prefill_candidates(row), 'source_execution_root': row.get('source_execution_root', ''), 'verification_cwd': row.get('verification_cwd', ''), 'verification_commands': row.get('verification_commands', []), 'allowed_owner_decisions': row['decision_options'], 'target_candidates': row.get('target_candidates', []), 'required_owner_fields': row['required_owner_fields'], 'must_not': row['must_not'], 'notes_zh': '本骨架只供 owner 人工填写和复核；status、worksheet_status、owner_question_zh、default_state、allowed_next_status、hard_gate_summary、hard_gate、observed_source_identity、allowed_owner_decisions、target_candidates、required_owner_fields 和 must_not 是只读上下文；脚本不写文件、不关闭门禁、不提升 active。'}
    for field in row['required_owner_fields']:
        form.setdefault(field, default_field_value(field, row))
    for field in ['owner_decision', 'target_decision', 'reviewed_by', 'reviewed_at', 'review_after', 'source_status', 'evidence_refs', 'status_reason']:
        form.setdefault(field, default_field_value(field, row))
    return form

def make_owner_checklist(row):
    return {'worksheet_id': row['id'], 'source_id': row['source_id'], 'source_path': row['source_path'], 'owner': row['owner'], 'owner_question_zh': row.get('owner_question_zh', ''), 'default_state': row.get('default_state', ''), 'allowed_owner_decisions': row['decision_options'], 'target_candidates': row.get('target_candidates', []), 'allowed_next_status': row.get('allowed_next_status', []), 'required_owner_fields': row['required_owner_fields'], 'hard_gate_summary': row.get('hard_gate_summary', ''), 'hard_gate': row.get('hard_gate', ''), 'owner_route': row.get('owner_route', {}), 'observed_source_identity': row.get('observed_source_identity', {}), 'source_execution_root': row.get('source_execution_root', ''), 'verification_cwd': row.get('verification_cwd', ''), 'verification_commands': row.get('verification_commands', []), 'must_not': row['must_not'], 'notes_zh': '本清单只把 owner intake、worksheet 和执行目录提示合并到一个只读视图；不能替代 owner 决策，不能关闭门禁。'}

def owner_ready_landing_errors(form_validation, rows):
    open_by_id = {row['id']: row for row in rows if row['status'] == 'open'}
    owner_ready_errors = []
    if form_validation and form_validation.get('status') == 'pass':
        for form in form_validation.get('forms', []):
            worksheet_id = str(form.get('worksheet_id', ''))
            row = open_by_id.get(worksheet_id)
            if not row:
                continue
            ready_status, ready_packages = owner_ready_state(row)
            if ready_status != 'covered':
                owner_ready_errors.append({'worksheet_id': worksheet_id, 'source_id': row.get('source_id', ''), 'source_path': row.get('source_path', ''), 'owner_ready_package_status': ready_status, 'owner_ready_packages': ready_packages})
    return owner_ready_errors

def required_manual_files_for_forms(form_validation, rows):
    open_by_id = {row['id']: row for row in rows if row['status'] == 'open'}
    worksheet_files = []
    if form_validation:
        for form in form_validation.get('forms', []):
            row = open_by_id.get(str(form.get('worksheet_id', '')))
            worksheet = str(row.get('worksheet', '')) if row else ''
            if worksheet and worksheet not in worksheet_files:
                worksheet_files.append(worksheet)
    if not worksheet_files:
        worksheet_files = ['artifacts/manifests/*owner-decision-worksheets-*.jsonl']
    return ['artifacts/manifests/<owner-decision-landing-YYYYMMDD>.jsonl', *sorted(worksheet_files), 'registry/items.jsonl', 'indexes/by-owner.md', 'indexes/by-project.md', 'indexes/by-review-date.md', 'indexes/by-source.md', 'indexes/by-status.md', 'indexes/by-topic.md', 'indexes/by-decision.md']

def make_landing_plan(form_validation, rows):
    open_by_id = {row['id']: row for row in rows if row['status'] == 'open'}
    blocked = form_validation is None or form_validation.get('status') != 'pass'
    owner_ready_errors = owner_ready_landing_errors(form_validation, rows)
    if owner_ready_errors:
        blocked = True
    reason = ''
    if form_validation is None or form_validation.get('status') != 'pass':
        reason = 'form validation must pass before landing plan is usable'
    elif owner_ready_errors:
        reason = 'owner-ready package strong validation must be covered before landing plan is usable'
    plan = {'status': 'blocked' if blocked else 'planned', 'read_only': True, 'source_form': form_validation.get('path', '') if form_validation else '', 'reason': reason, 'landing_scope': form_validation.get('coverage', {}) if form_validation else {}, 'remaining_open_after_this_batch': form_validation.get('coverage', {}).get('missing_open_worksheet_ids', []) if form_validation else [], 'owner_ready_gate': {'status': 'blocked' if owner_ready_errors else 'pass', 'error_count': len(owner_ready_errors), 'errors': owner_ready_errors, 'notes_zh': 'owner-ready package 只表示可交给 owner 签收；landing plan 仍不生成 owner decision、不关闭 gate、不写文件。'}, 'steps': [], 'required_manual_files': required_manual_files_for_forms(form_validation, rows), 'verification_commands': ['rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics', 'rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --status all --json', 'rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict --json'], 'must_not': ['do not treat this plan as owner approval', 'do not auto-edit registry/index', 'do not promote project-specific content to domains/embedded/standards', 'do not write ~/.codex/memories', 'do not modify source project docs']}
    if blocked:
        return plan
    for form in form_validation.get('forms', []):
        worksheet_id = form.get('worksheet_id', '')
        row = open_by_id.get(worksheet_id, {})
        plan['steps'].append({'worksheet_id': worksheet_id, 'source_id': form.get('source_id', ''), 'source_path': form.get('source_path', ''), 'owner_decision': form.get('owner_decision', ''), 'target_decision': form.get('target_decision', ''), 'reviewed_by': form.get('reviewed_by', ''), 'reviewed_at': form.get('reviewed_at', ''), 'owner_ready_package_status': owner_ready_state(row)[0] if row else '', 'owner_ready_packages': owner_ready_state(row)[1] if row else [], 'worksheet_verification_cwd': row.get('verification_cwd', ''), 'worksheet_verification_commands': row.get('verification_commands', []), 'manual_actions_zh': ['把已审 owner decision 追加到 owner decision landing JSONL 制品。', '按 target_decision 更新或新增对应 registry item，状态不得越过 owner 决策允许范围。', '同步 by-project、by-status、by-owner、by-review-date、by-topic、by-source 和 by-decision 索引。', '按 worksheet_verification_commands 复核项目侧或 Knowledge Hub 侧证据；无法运行的命令必须记录原因。', '运行 verification_commands 中的命令；strict gate 只有所有 owner gates 闭环后才会返回 0。'], 'guardrails': row.get('must_not', [])})
    return plan

def make_landing_audit(form_validation, rows, blocked, owner_ready_errors):
    open_by_id = {row['id']: row for row in rows if row['status'] == 'open'}
    forms = form_validation.get('forms', []) if form_validation else []
    audit_rows = []
    for form in forms:
        worksheet_id = str(form.get('worksheet_id', ''))
        row = open_by_id.get(worksheet_id, {})
        worksheet_file = row.get('worksheet', 'artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl')
        required_fields = []
        for field in list(row.get('required_owner_fields', [])) + ['owner_decision', 'target_decision', 'reviewed_by', 'reviewed_at', 'review_after', 'source_status', 'evidence_refs', 'status_reason']:
            if field not in required_fields:
                required_fields.append(field)
        missing_fields = [field for field in required_fields if not is_filled(form.get(field))]
        row_status = 'blocked' if blocked or missing_fields or (not row) else 'ready-for-manual-landing'
        audit_rows.append({'worksheet_id': worksheet_id, 'source_id': form.get('source_id', ''), 'source_path': form.get('source_path', ''), 'status': row_status, 'worksheet_resolution_status': {'current_status': row.get('status', 'missing-open-row'), 'worksheet_file': worksheet_file, 'must_update_worksheet_row': bool(row), 'required_resolution_state_hint': '设置 worksheet_status/row_status/status/default_state 中至少一个为 resolved、owner-approved、approved 或 closed，并保留完整 owner 字段。', 'required_fields': required_fields, 'missing_fields_in_form': missing_fields, 'notes_zh': 'worksheet 是否关闭由 worksheet 行和必填 owner 字段共同决定；landing plan 不会自动改 worksheet 或关闭 gate。'}, 'expected_manual_deltas': {'landing_jsonl': '追加已人工签收的 owner decision JSONL；保留 reviewed_by、reviewed_at、source_sha256/source_size、evidence_refs 和 status_reason。', 'worksheet_jsonl': '把对应 worksheet 行更新为已签收状态，并写入同一组 owner decision 字段；不得由工具代签。', 'registry_items': '按 target_decision 更新或新增 registry item，状态不得越过 owner 决策允许范围。', 'registry_source_policy': '记录 owner-gated 到目标状态的人工迁移/引用/归档决策。', 'indexes': ['indexes/by-owner.md', 'indexes/by-project.md', 'indexes/by-review-date.md', 'indexes/by-source.md', 'indexes/by-status.md', 'indexes/by-topic.md', 'indexes/by-decision.md']}, 'post_landing_commands': ['rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --status all --json', 'rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics', 'rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict --json', 'rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json'], 'must_not': ['不得把本 audit 当作 owner approval', '不得自动写 worksheet、registry、source policy 或 index', '不得关闭未签收 owner gate', '不得把 project-specific 内容提升为团队标准']})
    return {'status': 'blocked' if blocked else 'ready-for-manual-landing' if audit_rows else 'empty', 'read_only': True, 'row_count': len(audit_rows), 'landing_scope': form_validation.get('coverage', {}) if form_validation else {}, 'remaining_open_after_this_batch': form_validation.get('coverage', {}).get('missing_open_worksheet_ids', []) if form_validation else [], 'owner_ready_error_count': len(owner_ready_errors), 'required_manual_files': required_manual_files_for_forms(form_validation, rows), 'rows': audit_rows, 'notes_zh': 'landing_audit 只描述人工落点和复核命令，避免 owner JSONL 合法但 worksheet 仍 open；不写文件、不生成 owner decision、不关闭 gate。'}
