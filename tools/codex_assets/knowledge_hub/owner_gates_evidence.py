import pathlib

from .owner_gates_support import _display_path, _read_jsonl_local, _row_ref, shlex_quote, source_path_matches

root = pathlib.Path(".")

def configure_owner_gates_evidence(root_value):
    global root
    root = root_value

def inspect_owner_ready_item(row, item):
    tags = item.get('tags', [])
    source = item.get('source', {}) if isinstance(item.get('source'), dict) else {}
    path_value = str(item.get('path', '') or '')
    md_path = root / path_value if path_value else root / '__missing_owner_ready_path__'
    jsonl_path = root / str(pathlib.Path(path_value).with_suffix('.jsonl')) if path_value else root / '__missing_owner_ready_path__.jsonl'
    checks = {}
    errors_local = []

    def check(name, condition, message):
        checks[name] = bool(condition)
        if not condition:
            errors_local.append(message)
    check('registry_kind_audit', item.get('kind') == 'audit', 'registry kind must be audit')
    check('registry_status_reviewing', item.get('status') == 'reviewing', 'registry status must be reviewing')
    check('registry_review_status_owner_ready', item.get('review_status') == 'owner-ready-no-decision', 'registry review_status must be owner-ready-no-decision')
    check('registry_tags_owner_gate_ready', 'owner-gate' in tags and 'owner-ready' in tags, 'registry tags must include owner-gate and owner-ready')
    check('registry_source_type_generated', source.get('type') == 'generated', 'registry source.type must be generated')
    check('registry_source_id_match', source.get('source_id') == row['source_id'], 'registry source_id must match worksheet')
    check('registry_source_path_match', source_path_matches(source.get('source_path'), row['source_path']), 'registry source_path must match worksheet')
    check('artifact_path_owner_ready_package', path_value.startswith('artifacts/manifests/') and 'owner-ready-package' in pathlib.Path(path_value).name, 'artifact path must point to an owner-ready package manifest')
    check('artifact_markdown_exists', md_path.is_file(), 'owner-ready package markdown must exist')
    check('artifact_jsonl_exists', jsonl_path.is_file(), 'owner-ready package jsonl must exist')
    md_text = ''
    if md_path.is_file():
        try:
            md_text = md_path.read_text()
        except Exception as exc:
            errors_local.append(f'cannot read {_display_path(md_path)}: {exc}')
    check('package_markdown_commands_cwd_stable', 'rtk bash tools/' not in md_text, 'owner-ready package markdown must use ~/knowledge-hub/tools commands instead of rtk bash tools/...')
    package_rows, package_errors = _read_jsonl_local(jsonl_path)
    errors_local.extend(package_errors)
    check('package_jsonl_single_row', len(package_rows) == 1, 'owner-ready package jsonl must contain exactly one row')
    package = package_rows[0] if len(package_rows) == 1 else {}
    identity = package.get('observed_source_identity', {}) if isinstance(package.get('observed_source_identity'), dict) else {}
    evidence_refs = package.get('evidence_refs', [])
    evidence_ref_commands_are_stable = True
    if not isinstance(evidence_refs, list):
        evidence_ref_commands_are_stable = False
    else:
        for ref in evidence_refs:
            if not isinstance(ref, str):
                evidence_ref_commands_are_stable = False
                break
            stripped = ref.strip()
            if stripped.startswith('tools/') or 'rtk bash tools/' in stripped:
                evidence_ref_commands_are_stable = False
                break
    check('package_classification_match', package.get('classification') == 'single-owner-ready-package', 'package classification must be single-owner-ready-package')
    check('package_worksheet_id_match', package.get('worksheet_id') == row['id'], 'package worksheet_id must match worksheet')
    check('package_source_id_match', package.get('source_id') == row['source_id'], 'package source_id must match worksheet')
    check('package_source_path_match', source_path_matches(package.get('source_path'), row['source_path']), 'package source_path must match worksheet')
    check('package_decision_owner_ready', package.get('decision') == 'owner-ready-no-decision', 'package decision must be owner-ready-no-decision')
    check('package_status_reviewing', package.get('status') == 'reviewing', 'package status must be reviewing')
    check('package_open_gate_remains', package.get('open_gate_remains') is True, 'package open_gate_remains must be true')
    check('package_identity_match', identity.get('status') == 'match', 'package observed_source_identity.status must be match')
    check('package_evidence_refs_cwd_stable', evidence_ref_commands_are_stable, 'owner-ready package evidence_refs must use stable rtk bash ~/knowledge-hub/tools commands or non-command artifact refs')
    return {'id': item.get('id', ''), 'path': path_value, 'jsonl_path': _display_path(jsonl_path), 'review_status': item.get('review_status', ''), 'decision': package.get('decision', ''), 'open_gate_remains': package.get('open_gate_remains', None), 'identity_status': identity.get('status', ''), 'package_evidence_refs': evidence_refs if isinstance(evidence_refs, list) else [], 'status': 'valid' if not errors_local else 'invalid', 'coverage_checks': checks, 'errors': errors_local}

def owner_ready_items(row):
    candidates = [item for item in row.get('registry_items', []) if item.get('review_status') == 'owner-ready-no-decision' or 'owner-ready' in item.get('tags', [])]
    return [inspect_owner_ready_item(row, item) for item in candidates]

def owner_ready_state(row):
    packages = owner_ready_items(row)
    valid_packages = [item for item in packages if item['status'] == 'valid']
    if not packages:
        return ('missing', packages)
    if len(packages) > 1:
        return ('duplicate', packages)
    if len(valid_packages) == 1:
        return ('covered', packages)
    return ('invalid', packages)

def owner_ready_evidence_refs(row):
    refs = []
    for item in owner_ready_items(row):
        for ref in item.get('package_evidence_refs', []):
            if ref not in refs:
                refs.append(ref)
    return refs

def _is_evidence_field(field):
    field_text = str(field)
    return field_text == 'evidence_refs' or field_text == 'gate_evidence' or field_text.endswith('_evidence') or field_text.endswith('_evidence_refs') or ('evidence' in field_text)

def _classify_evidence_command(command):
    text = str(command).strip()
    if not text:
        return {'command': text, 'bucket': 'empty', 'notes_zh': '空命令不能作为证据候选。'}
    stable_prefixes = ['rtk bash ~/knowledge-hub/tools/', 'rtk git -C ~/knowledge-hub ', 'rtk git -C ~/knowledge-hub ']
    if any((text.startswith(prefix) for prefix in stable_prefixes)):
        return {'command': text, 'bucket': 'safe-command-candidate', 'notes_zh': 'Knowledge Hub 只读或本仓状态命令；仍需人工运行并引用输出，不自动写入表单。'}
    return {'command': text, 'bucket': 'project-command-needs-owner-or-lab-run', 'notes_zh': '项目侧、构建、硬件、分支状态或上下文相关命令；需要 owner 或实验环境人工运行后再引用。'}

def _field_readiness(field, row, evidence_refs):
    identity = row.get('observed_source_identity', {}) if isinstance(row.get('observed_source_identity'), dict) else {}
    identity_matches = identity.get('identity_status') == 'match'
    if field == 'source_sha256':
        return {'field': field, 'readiness': 'copy-from-source-identity' if identity_matches else 'source-identity-not-ready', 'candidate': identity.get('observed_sha256', '') if identity_matches else '', 'notes_zh': '候选值只来自 observed_source_identity；正式 source_sha256 字段仍必须由 owner 人工复制和签收。'}
    if field == 'source_size':
        return {'field': field, 'readiness': 'copy-from-source-identity' if identity_matches else 'source-identity-not-ready', 'candidate': identity.get('observed_size', '') if identity_matches else '', 'notes_zh': '候选值只来自 observed_source_identity；正式 source_size 字段仍必须由 owner 人工复制和签收。'}
    if field == 'review_after':
        return {'field': field, 'readiness': 'copy-from-worksheet', 'candidate': row.get('review_after', ''), 'notes_zh': '候选值来自 worksheet 排期；owner 可按实际复核周期调整。'}
    if field == 'owner_decision':
        return {'field': field, 'readiness': 'enum-choice-required', 'candidate': row.get('decision_options', []), 'notes_zh': '必须由真实 owner 从 allowed_owner_decisions 中选择，工具不代选。'}
    if field == 'target_decision':
        return {'field': field, 'readiness': 'enum-choice-required', 'candidate': row.get('target_candidates', []), 'notes_zh': '必须由真实 owner 从 target_candidates 中选择，不能写到候选目标之外。'}
    if _is_evidence_field(field):
        return {'field': field, 'readiness': 'owner-ready-evidence-ref-candidate' if evidence_refs else 'command-evidence-required', 'candidate': evidence_refs, 'notes_zh': 'owner-ready package 的 evidence_refs 只是引用候选；owner 仍需确认是否足以支撑该字段。'}
    return {'field': field, 'readiness': 'owner-input-required', 'candidate': '', 'notes_zh': '需要真实 owner 填写或确认；工具不自动推断。'}

def make_read_only_prefill_candidates(row):
    evidence_refs = owner_ready_evidence_refs(row)
    identity = row.get('observed_source_identity', {}) if isinstance(row.get('observed_source_identity'), dict) else {}
    identity_matches = identity.get('identity_status') == 'match'
    field_readiness = [_field_readiness(field, row, evidence_refs) for field in row.get('required_owner_fields', [])]
    return {'read_only': True, 'no_owner_decision_generated': True, 'formal_owner_fields_remain_manual': ['owner_decision', 'target_decision', 'reviewed_by', 'reviewed_at', 'source_sha256', 'source_size', 'evidence_refs', 'status_reason'], 'source_sha256_candidate': identity.get('observed_sha256', '') if identity_matches else '', 'source_size_candidate': identity.get('observed_size', '') if identity_matches else '', 'review_after_candidate': row.get('review_after', ''), 'evidence_ref_candidates': evidence_refs, 'field_readiness': field_readiness, 'notes_zh': '这些值只用于减少 owner 查找成本，不写入正式字段、不代表签收、不关闭 owner gate。'}

def make_evidence_readiness(rows):
    readiness_rows = []
    status_counts = {}
    for row in rows:
        evidence_refs = owner_ready_evidence_refs(row)
        field_readiness = [_field_readiness(field, row, evidence_refs) for field in row.get('required_owner_fields', [])]
        mechanical_known_fields = [item['field'] for item in field_readiness if item['readiness'] in {'copy-from-source-identity', 'copy-from-worksheet'}]
        owner_answer_required_fields = [item['field'] for item in field_readiness if item['readiness'] in {'owner-input-required', 'enum-choice-required'}]
        command_evidence_required_fields = [item['field'] for item in field_readiness if item['readiness'] == 'command-evidence-required']
        command_candidates = [_classify_evidence_command(command) for command in row.get('verification_commands', [])]
        safe_command_candidates = [item for item in command_candidates if item['bucket'] == 'safe-command-candidate']
        project_command_candidates = [item for item in command_candidates if item['bucket'] == 'project-command-needs-owner-or-lab-run']
        source_identity_status = row.get('observed_source_identity', {}).get('identity_status', 'unavailable')
        owner_ready_status, owner_ready_packages = owner_ready_state(row)
        if row.get('active_registry_items'):
            readiness_status = 'blocked-active-exposure'
        elif source_identity_status != 'match':
            readiness_status = 'blocked-source-identity'
        elif owner_ready_status != 'covered':
            readiness_status = 'blocked-owner-ready-package'
        else:
            readiness_status = 'ready-for-owner-review-owner-input-required'
        status_counts[readiness_status] = status_counts.get(readiness_status, 0) + 1
        readiness_rows.append({'worksheet_id': row['id'], 'source_id': row['source_id'], 'source_path': row['source_path'], 'owner': row['owner'], 'owner_route': row.get('owner_route', {}), 'status': row['status'], 'readiness_status': readiness_status, 'source_identity_status': source_identity_status, 'owner_ready_package_status': owner_ready_status, 'owner_ready_packages': owner_ready_packages, 'mechanical_known_fields': mechanical_known_fields, 'owner_answer_required_fields': owner_answer_required_fields, 'command_evidence_required_fields': command_evidence_required_fields, 'owner_ready_evidence_refs': evidence_refs, 'safe_command_candidates': safe_command_candidates, 'project_command_candidates': project_command_candidates, 'field_readiness': field_readiness, 'read_only_prefill_candidates': make_read_only_prefill_candidates(row), 'notes_zh': '只读证据准备度；帮助 owner 找候选值和命令，不生成 owner decision，不写文件，不关闭 gate。'})
    return {'status': 'ready-for-owner-review' if rows and all((row['readiness_status'] == 'ready-for-owner-review-owner-input-required' for row in readiness_rows)) else 'needs-attention' if rows else 'empty', 'read_only': True, 'row_count': len(readiness_rows), 'status_counts': dict(sorted(status_counts.items())), 'rows': readiness_rows, 'notes_zh': 'evidence readiness 只汇总候选证据和人工动作，不自动填 owner 字段、不关闭 gate、不提升 active。'}

def group_owner_required_fields(row):
    manual_fields = []
    copyable_candidate_fields = []
    evidence_fields = []
    verification_fields = []
    automation_boundary_fields = []
    other_manual_fields = []
    copyable_names = {'source_sha256', 'source_size', 'review_after'}
    automation_names = {'automation_enabled', 'writes_memory', 'writes_team_active_index', 'no_memory_write_gate', 'not_active_source', 'contains_memory_candidates'}
    verification_markers = ('verification', 'test', 'validation', 'command', 'branch', 'commit', 'tag')
    core_manual = {'owner_decision', 'target_decision', 'reviewed_by', 'reviewed_at', 'source_status', 'status_reason'}
    for field in row.get('required_owner_fields', []):
        field_text = str(field)
        if field_text in core_manual:
            manual_fields.append(field_text)
        elif field_text in copyable_names:
            copyable_candidate_fields.append(field_text)
        elif _is_evidence_field(field_text):
            evidence_fields.append(field_text)
        elif field_text in automation_names:
            automation_boundary_fields.append(field_text)
        elif any((marker in field_text for marker in verification_markers)):
            verification_fields.append(field_text)
        else:
            other_manual_fields.append(field_text)
    return {'manual_decision_fields': manual_fields, 'other_manual_owner_fields': other_manual_fields, 'copyable_candidate_fields': copyable_candidate_fields, 'evidence_fields': evidence_fields, 'verification_context_fields': verification_fields, 'automation_boundary_fields': automation_boundary_fields, 'field_count': len(row.get('required_owner_fields', [])), 'notes_zh': '字段分组只降低 owner 复核成本；manual 字段必须由真实 owner 填写，copyable 候选也必须人工签收后才可落地。'}

def make_owner_inbox(rows):
    inbox_rows = []
    owner_counts = {}
    for row in rows:
        if row['status'] != 'open':
            continue
        owner = row.get('owner', '') or '<missing-owner>'
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
        ready_status, ready_packages = owner_ready_state(row)
        owner_arg = shlex_quote(owner)
        source_id = row['source_id']
        worksheet_id = row['id']
        inbox_rows.append({'worksheet_id': worksheet_id, 'source_id': source_id, 'source_path': row['source_path'], 'owner': owner, 'review_after': row.get('review_after', ''), 'owner_question_zh': row.get('owner_question_zh', ''), 'allowed_owner_decisions': row.get('decision_options', []), 'target_candidates': row.get('target_candidates', []), 'owner_route': row.get('owner_route', {}), 'required_field_groups': group_owner_required_fields(row), 'read_only_prefill_candidates': make_read_only_prefill_candidates(row), 'observed_source_identity': row.get('observed_source_identity', {}), 'owner_ready_package_status': ready_status, 'owner_ready_package_ids': [item.get('id', '') for item in ready_packages if item.get('id')], 'owner_ready_package_paths': [item.get('path', '') for item in ready_packages if item.get('path')], 'verification_cwd': row.get('verification_cwd', ''), 'verification_commands': row.get('verification_commands', []), 'commands': {'focus_command': f'rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id {source_id} --owner {owner_arg} --worksheet-id {worksheet_id} --checklist --forms', 'forms_jsonl_command': f'rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id {source_id} --owner {owner_arg} --worksheet-id {worksheet_id} --forms-jsonl', 'evidence_readiness_command': f'rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id {source_id} --owner {owner_arg} --worksheet-id {worksheet_id} --evidence-readiness --json', 'validate_forms_command_template': f"rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id {source_id} --owner {owner_arg} --worksheet-id {worksheet_id} --validate-forms '<owner-decisions.jsonl>' --json", 'landing_plan_command_template': f"rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id {source_id} --owner {owner_arg} --worksheet-id {worksheet_id} --validate-forms '<owner-decisions.jsonl>' --landing-plan --json", 'landing_audit_command_template': f"rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id {source_id} --owner {owner_arg} --worksheet-id {worksheet_id} --validate-forms '<owner-decisions.jsonl>' --landing-audit --json"}, 'must_not': ['不得把 routing_owner 当 reviewed_by', '不得由工具或 AI 代签 owner decision', '不得把 owner-ready package 当成已批准决策', '不得关闭未签收 owner gate', '不得把 project-specific 内容提升到 domains/embedded/standards/', '不得修改 PCR02 源项目 docs', '不得写 ~/.codex/memories'], 'notes_zh': '单条 owner inbox 只做人工复核入口；命令和候选字段均为只读上下文，不生成、不保存、不应用 owner decision。'})
    return {'status': 'ready-for-owner-review' if inbox_rows else 'empty', 'read_only': True, 'report_only': True, 'no_owner_decision_generated': True, 'no_owner_gate_closed': True, 'routing_owner_is_not_reviewed_by': True, 'row_count': len(inbox_rows), 'owner_counts': dict(sorted(owner_counts.items())), 'rows': inbox_rows, 'notes_zh': 'owner inbox 是单屏人工复核队列；只汇总 owner 问题、路由、字段分组、候选证据和校验命令，不写文件、不关闭 gate、不提升 active。'}

def make_owner_ready_coverage(rows):
    coverage = {'owner_ready_package_count': 0, 'owner_ready_missing_count': 0, 'owner_ready_invalid_count': 0, 'owner_ready_duplicate_count': 0, 'owner_ready_missing': [], 'owner_ready_invalid': [], 'owner_ready_duplicate': []}
    for row in rows:
        status, packages = owner_ready_state(row)
        if status == 'covered':
            coverage['owner_ready_package_count'] += 1
        elif status == 'missing':
            coverage['owner_ready_missing_count'] += 1
            coverage['owner_ready_missing'].append(_row_ref(row))
        elif status == 'invalid':
            coverage['owner_ready_invalid_count'] += 1
            entry = _row_ref(row)
            entry['owner_ready_packages'] = packages
            coverage['owner_ready_invalid'].append(entry)
        elif status == 'duplicate':
            coverage['owner_ready_duplicate_count'] += 1
            entry = _row_ref(row)
            entry['owner_ready_packages'] = packages
            coverage['owner_ready_duplicate'].append(entry)
    coverage['owner_ready_package_coverage'] = f"{coverage['owner_ready_package_count']}/{len(rows)}"
    return coverage

def make_owner_ready_blocking_context(rows):
    open_rows = [row for row in rows if row.get('status') == 'open']
    open_coverage = make_owner_ready_coverage(open_rows)
    blocking_missing = open_coverage['owner_ready_missing_count']
    blocking_invalid = open_coverage['owner_ready_invalid_count']
    blocking_duplicate = open_coverage['owner_ready_duplicate_count']
    has_blocking = bool(blocking_missing or blocking_invalid or blocking_duplicate)
    if not open_rows:
        status = 'not-applicable-no-open-owner-gates'
        note = 'owner-ready package 覆盖只阻断 open owner gate；当前没有 open owner gate，历史 owner-ready package 缺失或被 owner decision landing 取代不再阻断。'
    elif has_blocking:
        status = 'blocked-open-owner-gates'
        note = 'owner-ready package 覆盖只阻断 open owner gate；当前仍有 open owner gate 缺少、无效或重复 owner-ready package，landing 前必须先修复。'
    else:
        status = 'pass-open-owner-gates'
        note = 'owner-ready package 覆盖只阻断 open owner gate；当前 open owner gate 的 owner-ready package 覆盖有效。'
    return {'owner_ready_blocking_scope': 'open-owner-gates-only', 'owner_ready_blocking_status': status, 'owner_ready_missing_blocking': bool(blocking_missing), 'owner_ready_invalid_blocking': bool(blocking_invalid), 'owner_ready_duplicate_blocking': bool(blocking_duplicate), 'owner_ready_blocking_counts': {'open_row_count': len(open_rows), 'missing': blocking_missing, 'invalid': blocking_invalid, 'duplicate': blocking_duplicate, 'coverage': open_coverage['owner_ready_package_coverage']}, 'owner_ready_status_note_zh': note}
