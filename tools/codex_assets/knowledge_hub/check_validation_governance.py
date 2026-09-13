def _governance_1(ctx):
    local_path_prefixes = ctx['LOCAL_PATH_PREFIXES']
    manifest_profile_paths = []
    for candidate_path in sorted((ctx['root'] / 'artifacts' / 'manifests').glob('knowledge-hub-*.jsonl')):
        date_match = ctx['re'].search('(20\\d{6})', candidate_path.name)
        if not date_match:
            continue
        try:
            manifest_date = ctx['dt'].datetime.strptime(date_match.group(1), '%Y%m%d').date()
        except Exception:
            continue
        if manifest_date >= ctx['READABILITY_GATE_START']:
            manifest_profile_paths.append(candidate_path)
    manifest_evidence_fields = ['evidence', 'evidence_refs', 'validation_refs', 'verification_commands', 'source_refs']
    manifest_boundary_fields = ['boundaries', 'guardrails', 'must_not', 'non_goals', 'rollback_policy', 'risk']
    for manifest_path in manifest_profile_paths:
        rel_manifest = manifest_path.relative_to(ctx['root'])
        manifest_stem = manifest_path.stem
        filename_has_date = bool(ctx['re'].search('20\\d{6}', manifest_path.name))
        rows = ctx['load_jsonl'](manifest_path)
        for row_index, row in enumerate(rows, 1):
            row_id = str(row.get('id', '')).strip()
            label = row_id or f'{rel_manifest}:{row_index}'
            row_type = str(row.get('row_type', '')).strip()
            if row_id != manifest_stem and row_type != 'summary':
                continue
            if not row_id:
                ctx['errors'].append(f'manifest-profile:{label} missing id')
            if not str(row.get('status', '')).strip():
                ctx['errors'].append(f'manifest-profile:{label} missing status')
            if not (filename_has_date or str(row.get('checked_at', '')).strip() or str(row.get('created_at', '')).strip() or str(row.get('updated_at', '')).strip() or str(row.get('review_after', '')).strip()):
                ctx['errors'].append(f'manifest-profile:{label} missing date field')
            if not (str(row.get('summary_zh', '')).strip() or str(row.get('notes_zh', '')).strip()):
                ctx['errors'].append(f'manifest-profile:{label} missing summary_zh or notes_zh')
            has_evidence = False
            for field in manifest_evidence_fields:
                value = row.get(field)
                if isinstance(value, list) and value:
                    has_evidence = True
                elif isinstance(value, str) and value.strip():
                    has_evidence = True
            if not has_evidence:
                ctx['errors'].append(f'manifest-profile:{label} missing evidence field')
            has_boundary = False
            for field in manifest_boundary_fields:
                value = row.get(field)
                if isinstance(value, list) and value:
                    has_boundary = True
                elif isinstance(value, dict) and value:
                    has_boundary = True
                elif isinstance(value, str) and value.strip():
                    has_boundary = True
            if not has_boundary:
                ctx['errors'].append(f'manifest-profile:{label} missing boundary field')
    template_required_fields = ['id', 'title', 'kind', 'domain', 'path', 'scope', 'visibility', 'status', 'owner', 'source', 'review_after', 'created_at', 'updated_at', 'promotion', 'tags']
    template_readability_fields = ['summary_zh', 'review_status', 'primary_language', 'source_language', 'translation_status', 'terminology_status', 'evidence_strength', 'evidence_refs', 'promotion_decision', 'generated_by_ai', 'ai_role', 'ai_model_or_tool', 'ai_generated_at', 'human_reviewed_by', 'human_reviewed_at', 'review_basis']
    return {key: value for key, value in locals().items() if key != 'ctx'}

def _governance_2(ctx):
    template_skip = {'README.md'}
    for template_path in sorted((ctx['root'] / 'templates').glob('*.md')):
        rel_template = template_path.relative_to(ctx['root'])
        if template_path.name in template_skip:
            continue
        template_text = template_path.read_text()
        for field in ctx['template_required_fields']:
            if not ctx['re'].search(f"^{ctx['re'].escape(field)}:", template_text, ctx['re'].MULTILINE):
                ctx['errors'].append(f'template:{rel_template} missing {field}')
        for field in ctx['template_readability_fields']:
            if not ctx['re'].search(f"^{ctx['re'].escape(field)}:", template_text, ctx['re'].MULTILINE):
                ctx['errors'].append(f'template:{rel_template} missing readability field {field}')
        if template_path.name == 'artifact-ref.md':
            for field in ['uri', 'size', 'sha256']:
                if not ctx['re'].search(f"^{ctx['re'].escape(field)}:", template_text, ctx['re'].MULTILINE):
                    ctx['errors'].append(f'template:{rel_template} artifact-ref missing {field}')
    manual_entry_terms = ['promotion', 'tags', 'validation_refs', 'indexes/by-owner.md', 'indexes/by-review-date.md', 'indexes/by-status.md', '- reviewing:', 'duplicate']
    manual_entry_files = {ctx['root'] / 'tools' / 'knowledge-new.sh': [ctx['root'] / 'tools' / 'knowledge-new.sh', ctx['root'] / 'tools' / 'codex_assets' / 'knowledge_hub' / 'new_cli.py', ctx['root'] / 'tools' / 'codex_assets' / 'knowledge_hub' / 'lifecycle.py'], ctx['root'] / 'templates' / 'README.md': [ctx['root'] / 'templates' / 'README.md']}
    for manual_entry_file, implementation_files in manual_entry_files.items():
        manual_text = '\n'.join((path.read_text() for path in implementation_files))
        rel_manual = manual_entry_file.relative_to(ctx['root'])
        terms = manual_entry_terms
        if manual_entry_file.name == 'knowledge-new.sh':
            terms = ['promotion', 'tags', 'validation_refs', 'indexes/by-owner.md', 'indexes/by-review-date.md', 'indexes/by-status.md', 'choices=("draft", "reviewing", "personal")', 'registry item id already exists']
        for term in terms:
            if term not in manual_text:
                ctx['errors'].append(f'manual-entry:{rel_manual} missing current gate term: {term}')
    manual_entry_file_specific_terms = {ctx['root'] / 'tools' / 'knowledge-new.sh': ['owner_registry_status', 'personal-local', 'recommended_final_disposition', 'recommended_source_strategy', 'recommendation_scope_zh', '--item-source-id', '--check', '--no-check-reason', 'Evidence Index'], ctx['root'] / 'templates' / 'README.md': ['personal-local', 'recommended_final_disposition', 'recommended_source_strategy', '不替代 owner decision', '不关闭 owner gate', 'Evidence Index']}
    for manual_entry_file, terms in manual_entry_file_specific_terms.items():
        implementation_files = manual_entry_files.get(manual_entry_file, [manual_entry_file])
        manual_text = '\n'.join((path.read_text() for path in implementation_files))
        rel_manual = manual_entry_file.relative_to(ctx['root'])
        for term in terms:
            if term not in manual_text:
                ctx['errors'].append(f'manual-entry:{rel_manual} missing terminal manual-entry term: {term}')
    manual_entry_anchor_checks = {'README.md': ['日常入口', '目录边界', 'Source 处置口径', '高风险授权', '中文长期资产', '新会话恢复', 'knowledge-index-plan.sh --section linking --json', 'registry/authorizations.jsonl', 'registry/automation-runs.jsonl'], 'tools/README.md': ['低复杂度入口速查', 'knowledge-owner-gates.sh --owner-inbox', 'owner_inbox_json_command', 'knowledge-index-plan.sh --section linking --json', '离线人工维护', 'personal-local', 'role-aware 推荐终态'], 'indexes/README.md': ['最小同步', 'knowledge-index-plan.sh --section linking --json', 'knowledge-index-plan.sh --section manifest --json', 'manual_validation_pending: true']}
    for relative, terms in manual_entry_anchor_checks.items():
        path = ctx['root'] / relative
        text = path.read_text()
        for term in terms:
            if term not in text:
                ctx['errors'].append(f'manual-entry:{relative} missing maintenance anchor: {term}')
    return {key: value for key, value in locals().items() if key != 'ctx'}

def run_governance(ctx):
    ctx.update(_governance_1(ctx))
    ctx.update(_governance_2(ctx))
